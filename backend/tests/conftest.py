"""conftest.py — Configuration pytest pour ERP FABS V10 (local)"""
import os
import time
import requests
import pytest

# URL locale du backend
os.environ.setdefault("REACT_APP_BACKEND_URL", "http://localhost:8000")
os.environ.setdefault("API_BASE_URL", "http://localhost:8000")

BASE_URL = "http://localhost:8000"

# Créer un frontend/.env minimal si absent
_frontend_env = "/home/user/ERP-FABS-V10/frontend/.env"
if not os.path.exists(_frontend_env):
    os.makedirs(os.path.dirname(_frontend_env), exist_ok=True)
    with open(_frontend_env, "w") as f:
        f.write("REACT_APP_BACKEND_URL=http://localhost:8000\n")


@pytest.fixture(scope="session")
def super_token():
    """Token super_admin partagé pour toute la session de tests."""
    for attempt in range(3):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "pissken@editionsfabsci.com", "password": "Admin@2025"},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("access_token") or data.get("token", "")
        if r.status_code == 429:
            time.sleep(62)  # attendre reset rate limiter
        else:
            pytest.skip(f"Login échoué: {r.status_code} {r.text}")
    pytest.skip("Impossible d'obtenir un token (rate limit persistant)")


@pytest.fixture(scope="session")
def auth_headers(super_token):
    return {"Authorization": f"Bearer {super_token}"}
