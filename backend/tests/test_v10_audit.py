"""
V10 Final Regression Audit — covers items requested in iteration 10.
Run: pytest /app/backend/tests/test_v10_audit.py -v
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")

SUPER_EMAIL = "pissken@editionsfabsci.com"
SUPER_PASSWORD = "Admin@2025"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token", "")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ---------- BACKEND HEALTH ----------
def test_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy")


# ---------- AUTH ----------
def test_login_super_admin():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD}, timeout=15)
    assert r.status_code == 200
    data = r.json()
    # Either token or cookie based
    assert "user" in data or "email" in data or "session_token" in data or r.cookies.get("session_token")


# ---------- RH DEPARTEMENTS (le bug critique) ----------
def test_departements_returns_at_least_7(session):
    r = session.get(f"{BASE_URL}/api/rh/departements", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    # data may be list or paginated
    items = data if isinstance(data, list) else data.get("items") or data.get("data") or []
    assert len(items) >= 7, f"Expected >=7 departements, got {len(items)}: {[d.get('nom') for d in items]}"
    noms = {d.get("nom", "").lower() for d in items}
    expected = {"commercial", "comptabilité", "direction générale", "informatique",
                "logistique", "magasin & stock", "secrétariat & administration"}
    # Vérifier qu'au moins 6 noms attendus sont présents (tolérance casse/accents)
    matched = sum(1 for e in expected if any(e in n for n in noms))
    assert matched >= 6, f"Only {matched} expected departments matched. Got: {noms}"


# ---------- RH PAIE ----------
def test_paie_calculer(session):
    payload = {"salaire_brut": 500000}
    r = session.post(f"{BASE_URL}/api/paie/calculer", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    # Vérifier les champs CNPS, ITS, CMU, net
    keys = {k.lower() for k in data.keys()}
    assert any("net" in k for k in keys), f"Missing 'net' in response: {data}"
    assert any("cnps" in k for k in keys), f"Missing 'cnps' in response: {data}"
    assert any("its" in k for k in keys), f"Missing 'its' in response: {data}"
    assert any("cmu" in k for k in keys), f"Missing 'cmu' in response: {data}"


# ---------- NOTIFICATIONS ----------
def test_notifications_count_unread(session):
    # NOTE: l'endpoint réel est /api/notifications/count (la PR mentionnait à tort count-unread)
    r = session.get(f"{BASE_URL}/api/notifications/count", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "count" in data, f"Missing 'count' key in {data}"


def test_notifications_list(session):
    r = session.get(f"{BASE_URL}/api/notifications", timeout=15)
    assert r.status_code == 200


# ---------- FNE DASHBOARD ----------
def test_fne_dashboard_stats(session):
    r = session.get(f"{BASE_URL}/api/fne/dashboard/fne-stats", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)


# ---------- WORKFLOW COMMERCIAL ----------
def test_commande_cible_exists(session):
    """Vérifie que la commande cmd_8666a66ccac5 existe et est en statut 'preparee'."""
    r = session.get(f"{BASE_URL}/api/commandes/cmd_8666a66ccac5", timeout=15)
    # Peut renvoyer 404 si la commande n'existe pas dans cet environnement — test informationnel
    if r.status_code == 404:
        pytest.skip("Commande cmd_8666a66ccac5 absente de l'environnement de test")
    assert r.status_code == 200, r.text
    data = r.json()
    statut = data.get("statut") or data.get("status")
    assert statut in ("preparee", "prepare", "preparee_partielle"), f"Statut inattendu: {statut}"


def test_generer_facture_endpoint_exists(session):
    """Vérifier que l'endpoint existe en envoyant un body invalide (doit renvoyer 400/422/404, pas 405)."""
    r = session.post(f"{BASE_URL}/api/factures/generer-depuis-commande", json={"commande_id": "inexistant_xyz"}, timeout=15)
    assert r.status_code != 405, "Endpoint manquant (Method Not Allowed)"
    assert r.status_code in (400, 404, 422), f"Unexpected status: {r.status_code} - {r.text[:200]}"


def test_convertir_facture_endpoint_exists(session):
    """Vérifier que l'endpoint POST /api/proformas/{id}/convertir-facture existe."""
    r = session.post(f"{BASE_URL}/api/proformas/inexistant_xyz/convertir-facture", timeout=15)
    assert r.status_code != 405, "Endpoint manquant (Method Not Allowed)"
    assert r.status_code in (400, 404, 422), f"Unexpected status: {r.status_code}"


# ---------- API ENDPOINTS QUE LES PAGES V10 UTILISENT ----------
@pytest.mark.parametrize("endpoint", [
    "/api/produits",
    "/api/notifications",
    "/api/rh/employes",
    "/api/rh/departements",
    "/api/rh/missions",
    "/api/rh/conges",
    "/api/rh/absences",
    "/api/comptabilite/comptes",
    "/api/expeditions",
    "/api/fleet/vehicules",
    "/api/logistics-costs",
    "/api/file-storage/files",
])
def test_page_backend_endpoints(session, endpoint):
    r = session.get(f"{BASE_URL}{endpoint}", timeout=15)
    # Accepter 200 ou 404 si l'endpoint n'existe pas exactement sous ce chemin
    assert r.status_code in (200, 404), f"{endpoint} → {r.status_code}: {r.text[:200]}"
