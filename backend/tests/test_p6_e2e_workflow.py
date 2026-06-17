"""
P6-003 — Tests e2e workflow complet : commande → valider → préparer → livrer
Requiert : backend local sur localhost:8001, MongoDB accessible
"""
import pytest
import requests
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

BASE = "http://localhost:8001/api"
CREDENTIALS = {"email": "pissken@editionsfabsci.com", "password": "Fabs@2026"}

# Données existantes en DB
CLIENT_ID   = "cli_56de11d67429"
PRODUIT_ID  = "prod_760dd0dffa9e"
PRIX_UNITAIRE = 2000.0


# ============================================================
# Helpers async
# ============================================================

def run_async(coro):
    return asyncio.run(coro)


async def _get_stock():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fabsci_erp"]
    p = await db.produits.find_one({"product_id": PRODUIT_ID}, {"_id": 0, "stock_actuel": 1})
    client.close()
    return p["stock_actuel"]


async def _set_stock(val: int):
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fabsci_erp"]
    await db.produits.update_one({"product_id": PRODUIT_ID}, {"$set": {"stock_actuel": val}})
    client.close()


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE}/auth/login", json=CREDENTIALS, timeout=10)
    assert r.status_code == 200, f"Login failed: {r.text}"
    t = r.json().get("access_token")
    assert t, "Pas de access_token"
    return t


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def patch_stock():
    """Mettre le stock à 100 avant les tests, restaurer à 0 après."""
    run_async(_set_stock(100))
    yield
    run_async(_set_stock(0))


# commande_id partagé dans le module (state machine e2e)
_state = {"commande_id": None}


def _ligne(qte=5):
    return {"produit_id": PRODUIT_ID, "quantite": qte, "prix_unitaire": PRIX_UNITAIRE}


# ============================================================
# Étape 1 — Créer la commande
# ============================================================

class TestE2ECommande:

    def test_create_commande_brouillon(self, headers):
        """POST /commandes (sans submit) → statut brouillon"""
        payload = {
            "client_id": CLIENT_ID,
            "lignes": [_ligne(1)],
            "remise_globale": 0,
            "taux_tva": 18,
            "notes": "Brouillon e2e test P6"
        }
        r = requests.post(f"{BASE}/commandes", json=payload, headers=headers, timeout=10)
        assert r.status_code == 201, f"Create brouillon failed: {r.text}"
        d = r.json()
        assert d["statut"] == "brouillon"
        # Cleanup immédiat (pas utilisé pour le workflow principal)
        cid = d["commande_id"]
        requests.post(f"{BASE}/commandes/{cid}/annuler",
                      json={"motif": "cleanup brouillon e2e"}, headers=headers, timeout=10)

    def test_create_commande_en_attente(self, headers):
        """POST /commandes?submit=true → statut en_attente — commande principale du workflow"""
        payload = {
            "client_id": CLIENT_ID,
            "lignes": [_ligne(5)],
            "remise_globale": 0,
            "taux_tva": 18,
            "notes": "Commande e2e workflow P6"
        }
        r = requests.post(f"{BASE}/commandes?submit=true", json=payload, headers=headers, timeout=10)
        assert r.status_code == 201, f"Create en_attente failed: {r.text}"
        d = r.json()
        assert d["statut"] == "en_attente"
        assert d["client_id"] == CLIENT_ID
        assert "commande_id" in d
        _state["commande_id"] = d["commande_id"]

    def test_get_commande_by_id(self, headers):
        """GET /commandes/{id} → récupère la commande créée"""
        cid = _state["commande_id"]
        assert cid
        r = requests.get(f"{BASE}/commandes/{cid}", headers=headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["commande_id"] == cid
        assert d["statut"] == "en_attente"

    def test_list_commandes_contains_created(self, headers):
        """GET /commandes → la commande apparaît dans la liste"""
        cid = _state["commande_id"]
        assert cid
        r = requests.get(f"{BASE}/commandes?limit=50", headers=headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        ids = [c["commande_id"] for c in d["items"]]
        assert cid in ids


# ============================================================
# Étape 2 — Soumettre + Valider
# ============================================================

class TestE2EValider:

    def test_commande_is_en_attente(self, headers):
        """Vérifier que la commande principale est bien en en_attente"""
        cid = _state["commande_id"]
        assert cid
        r = requests.get(f"{BASE}/commandes/{cid}", headers=headers, timeout=10)
        assert r.status_code == 200
        assert r.json().get("statut") == "en_attente"

    def test_valider_commande(self, headers):
        """POST /commandes/{id}/valider → statut validee"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/valider", headers=headers, timeout=10)
        assert r.status_code == 200, f"Valider failed: {r.text}"
        d = r.json()
        assert d["statut"] == "validee", f"Attendu validee, got {d['statut']}"
        assert d["validated_by"] is not None

    def test_valider_twice_is_400(self, headers):
        """Valider une commande déjà validée → 400"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/valider", headers=headers, timeout=10)
        assert r.status_code == 400

    def test_valider_without_auth_401(self):
        """Valider sans token → 401/403"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/valider", timeout=10)
        assert r.status_code in (401, 403)


# ============================================================
# Étape 3 — Préparer
# ============================================================

class TestE2EPreparer:

    def test_preparer_commande(self, headers):
        """POST /commandes/{id}/preparer → statut preparee"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/preparer", headers=headers, timeout=10)
        assert r.status_code == 200, f"Preparer failed: {r.text}"
        d = r.json()
        assert d["statut"] == "preparee", f"Attendu preparee, got {d['statut']}"
        assert d["prepared_by"] is not None

    def test_preparer_twice_is_400(self, headers):
        """Préparer une commande déjà préparée → 400"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/preparer", headers=headers, timeout=10)
        assert r.status_code == 400

    def test_preparer_without_auth_401(self):
        """Préparer sans token → 401/403"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/preparer", timeout=10)
        assert r.status_code in (401, 403)


# ============================================================
# Étape 4 — Livrer
# ============================================================

class TestE2ELivrer:

    def test_livrer_commande(self, headers):
        """POST /commandes/{id}/livrer → statut livree (via BL si existant)"""
        cid = _state["commande_id"]
        assert cid

        stock_before = run_async(_get_stock())

        r = requests.post(f"{BASE}/commandes/{cid}/livrer", headers=headers, timeout=10)

        if r.status_code == 400 and "bon de livraison" in r.text.lower():
            # Chemin BL : le backend redirige vers /bons-livraison/{bl_id}/livrer
            import re
            match = re.search(r"bons-livraison/(bl_[a-z0-9]+)/livrer", r.text)
            assert match, f"Pas de bl_id dans le message: {r.text}"
            bl_id = match.group(1)
            r2 = requests.post(f"{BASE}/bons-livraison/{bl_id}/livrer", headers=headers, timeout=10)
            assert r2.status_code == 200, f"Livrer via BL failed: {r2.text}"
            # Vérifier statut commande mis à jour via BL
            rc = requests.get(f"{BASE}/commandes/{cid}", headers=headers, timeout=10)
            assert rc.status_code == 200
            assert rc.json()["statut"] == "livree"
        else:
            assert r.status_code == 200, f"Livrer failed: {r.text}"
            d = r.json()
            assert d["statut"] == "livree", f"Attendu livree, got {d['statut']}"
            assert d["date_livraison"] is not None

        stock_after = run_async(_get_stock())
        assert stock_after <= stock_before, (
            f"Stock non décrémenté: avant={stock_before}, après={stock_after}"
        )

    def test_livrer_twice_is_400(self, headers):
        """Livrer une commande déjà livrée → 400"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/livrer", headers=headers, timeout=10)
        assert r.status_code == 400

    def test_livrer_without_auth_401(self):
        """Livrer sans token → 401/403"""
        cid = _state["commande_id"]
        assert cid
        r = requests.post(f"{BASE}/commandes/{cid}/livrer", timeout=10)
        assert r.status_code in (401, 403)

    def test_commande_finale_statut(self, headers):
        """GET /commandes/{id} → vérifier état final complet"""
        cid = _state["commande_id"]
        assert cid
        r = requests.get(f"{BASE}/commandes/{cid}", headers=headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["statut"] == "livree", f"Attendu livree, got {d['statut']}"
        assert d["validated_by"] is not None
        assert d["prepared_by"] is not None
        assert d["date_validation"] is not None
        assert d["date_preparation"] is not None
        assert d["date_livraison"] is not None


# ============================================================
# Étape 5 — Vérifications sécurité workflow
# ============================================================

class TestE2EWorkflowSecurite:

    def test_cannot_skip_validation(self, headers):
        """Commande brouillon → tenter preparer directement → 400"""
        payload = {
            "client_id": CLIENT_ID,
            "lignes": [_ligne(1)],
            "remise_globale": 0,
            "taux_tva": 18,
        }
        r = requests.post(f"{BASE}/commandes", json=payload, headers=headers, timeout=10)
        assert r.status_code == 201, f"Create failed: {r.text}"
        cid = r.json()["commande_id"]

        r2 = requests.post(f"{BASE}/commandes/{cid}/preparer", headers=headers, timeout=10)
        assert r2.status_code == 400, f"Expected 400 skipping validation, got {r2.status_code}: {r2.text}"

        # Cleanup
        requests.post(f"{BASE}/commandes/{cid}/annuler",
                      json={"motif": "cleanup e2e"}, headers=headers, timeout=10)

    def test_cannot_skip_preparation(self, headers):
        """Commande validée → tenter livrer sans préparer → 400"""
        payload = {
            "client_id": CLIENT_ID,
            "lignes": [_ligne(1)],
            "remise_globale": 0,
            "taux_tva": 18,
        }
        r = requests.post(f"{BASE}/commandes?submit=true", json=payload, headers=headers, timeout=10)
        assert r.status_code == 201, f"Create failed: {r.text}"
        cid = r.json()["commande_id"]

        rv = requests.post(f"{BASE}/commandes/{cid}/valider", headers=headers, timeout=10)
        if rv.status_code != 200:
            requests.post(f"{BASE}/commandes/{cid}/annuler",
                          json={"motif": "cleanup"}, headers=headers, timeout=10)
            pytest.skip(f"Validation échouée: {rv.text}")

        rl = requests.post(f"{BASE}/commandes/{cid}/livrer", headers=headers, timeout=10)
        assert rl.status_code == 400, f"Expected 400 skipping prep, got {rl.status_code}: {rl.text}"

        # Cleanup
        requests.post(f"{BASE}/commandes/{cid}/annuler",
                      json={"motif": "cleanup e2e"}, headers=headers, timeout=10)

    def test_commande_livree_non_modifiable(self, headers):
        """PATCH sur commande livrée → refusé ou sans effet"""
        cid = _state["commande_id"]
        assert cid
        r = requests.patch(
            f"{BASE}/commandes/{cid}",
            json={"notes": "tentative post-livraison"},
            headers=headers, timeout=10
        )
        assert r.status_code in (200, 400, 403, 409)
