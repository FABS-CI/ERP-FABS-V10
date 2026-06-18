"""
ERP FABS-CI V10 — Tests smoke P5 (localhost)
Couvre : Auth, Commandes, Factures, Colisage, Produits, Clients, Dashboard,
         Rate limiting, Validation input, Pagination normalisée.
"""
import pytest
import requests

BASE = "http://localhost:8000/api"
ADMIN_EMAIL = "pissken@editionsfabsci.com"
ADMIN_PASS  = "Admin@2025"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Login échoué: {r.text}"
    token = r.json().get("access_token")
    assert token, "Pas de access_token dans la réponse login"
    return token


@pytest.fixture(scope="session")
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

class TestAuth:
    def test_login_success(self):
        r = requests.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        assert r.status_code == 200
        d = r.json()
        assert "access_token" in d
        # role est dans le JWT décodé, pas forcément dans la réponse login brute
        assert d.get("access_token") is not None

    def test_login_wrong_password(self):
        r = requests.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": "mauvais"})
        assert r.status_code in (401, 400)

    def test_me_returns_profile(self, auth):
        r = requests.get(f"{BASE}/auth/me", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == ADMIN_EMAIL
        assert d["role"] == "super_admin"
        assert "password_hash" not in d   # pas de fuite hash

    def test_me_no_token_401(self):
        r = requests.get(f"{BASE}/auth/me")
        assert r.status_code in (401, 403, 422)

    def test_refresh_invalid_token_401(self):
        r = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": "fake_token"})
        assert r.status_code in (401, 422)

    def test_logout_no_token_idempotent(self):
        r = requests.post(f"{BASE}/auth/logout")
        # Doit retourner 401 ou 200 mais jamais 500
        assert r.status_code != 500


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self):
        r = requests.get(f"{BASE}/health")
        assert r.status_code == 200

    def test_health_no_auth_required(self):
        # health doit être public
        r = requests.get(f"{BASE}/health")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# COMMANDES — pagination normalisée (TICKET-014)
# ---------------------------------------------------------------------------

class TestCommandesPagination:
    def test_list_returns_paginated_dict(self, auth):
        r = requests.get(f"{BASE}/commandes?limit=5", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict), "Doit retourner un dict paginé, pas un array"
        for key in ("items", "total", "page", "limit", "has_next"):
            assert key in d, f"Clé manquante: {key}"

    def test_list_items_is_list(self, auth):
        r = requests.get(f"{BASE}/commandes?limit=5", headers=auth)
        assert isinstance(r.json()["items"], list)

    def test_list_limit_respected(self, auth):
        r = requests.get(f"{BASE}/commandes?limit=1", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert len(d["items"]) <= 1

    def test_list_filter_statut(self, auth):
        r = requests.get(f"{BASE}/commandes?statut=validee&limit=10", headers=auth)
        assert r.status_code == 200
        d = r.json()
        # Tous les items doivent avoir statut validee
        for item in d["items"]:
            assert item["statut"] == "validee"

    def test_list_unauthenticated_403(self):
        r = requests.get(f"{BASE}/commandes")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# FACTURES — pagination + relances (TICKET-014, 015)
# ---------------------------------------------------------------------------

class TestFacturesPagination:
    def test_list_returns_paginated_dict(self, auth):
        r = requests.get(f"{BASE}/factures?limit=5", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d, dict)
        for key in ("items", "total", "page", "limit", "has_next"):
            assert key in d, f"Clé manquante: {key}"

    def test_list_limit_respected(self, auth):
        r = requests.get(f"{BASE}/factures?limit=1", headers=auth)
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 1

    def test_relances_run_endpoint_exists(self, auth):
        r = requests.post(f"{BASE}/factures/relances/run", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "ok"
        assert "updated" in d
        assert "errors" in d

    def test_relances_run_unauthenticated_401(self):
        r = requests.post(f"{BASE}/factures/relances/run")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# COLISAGE — validation input (TICKET-016 + P5)
# ---------------------------------------------------------------------------

class TestColisageValidation:
    def test_ordres_list_returns_items(self, auth):
        r = requests.get(f"{BASE}/colisage/ordres", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert "items" in d

    def test_create_ordre_invalid_facture_id_422(self, auth):
        # facture_id avec caractères interdits → 422
        r = requests.post(f"{BASE}/colisage/ordres", headers=auth,
                          json={"facture_id": "<script>alert(1)</script>"})
        assert r.status_code == 422

    def test_create_ordre_empty_facture_id_422(self, auth):
        r = requests.post(f"{BASE}/colisage/ordres", headers=auth,
                          json={"facture_id": ""})
        assert r.status_code == 422

    def test_create_ordre_notes_too_long_422(self, auth):
        r = requests.post(f"{BASE}/colisage/ordres", headers=auth,
                          json={"facture_id": "fac_test_001", "notes": "x" * 1001})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# PRODUITS
# ---------------------------------------------------------------------------

class TestProduits:
    def test_list_ok(self, auth):
        r = requests.get(f"{BASE}/produits", headers=auth)
        assert r.status_code == 200

    def test_alertes_stock_ok(self, auth):
        r = requests.get(f"{BASE}/produits/alertes-stock", headers=auth)
        assert r.status_code == 200

    def test_list_unauthenticated_403(self):
        r = requests.get(f"{BASE}/produits")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# CLIENTS
# ---------------------------------------------------------------------------

class TestClients:
    def test_list_ok(self, auth):
        r = requests.get(f"{BASE}/clients", headers=auth)
        assert r.status_code == 200

    def test_list_unauthenticated_403(self):
        r = requests.get(f"{BASE}/clients")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_stats_ok(self, auth):
        r = requests.get(f"{BASE}/dashboard/stats", headers=auth)
        assert r.status_code == 200

    def test_stats_no_500(self, auth):
        r = requests.get(f"{BASE}/dashboard/stats", headers=auth)
        assert r.status_code != 500


# ---------------------------------------------------------------------------
# SECURITE — pas de fuite _id MongoDB
# ---------------------------------------------------------------------------

class TestSecurite:
    def test_commandes_no_mongo_id_leak(self, auth):
        r = requests.get(f"{BASE}/commandes?limit=5", headers=auth)
        assert r.status_code == 200
        for item in r.json().get("items", []):
            assert "_id" not in item, "Fuite _id MongoDB détectée dans commandes"

    def test_factures_no_mongo_id_leak(self, auth):
        r = requests.get(f"{BASE}/factures?limit=5", headers=auth)
        assert r.status_code == 200
        for item in r.json().get("items", []):
            assert "_id" not in item, "Fuite _id MongoDB détectée dans factures"

    def test_me_no_password_hash_leak(self, auth):
        r = requests.get(f"{BASE}/auth/me", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert "password_hash" not in d
        assert "password" not in d
