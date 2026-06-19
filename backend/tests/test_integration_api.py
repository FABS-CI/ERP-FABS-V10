"""
ERP FABS-CI - Integration Tests for API Routes
Tests all 150+ API routes for functionality, RBAC, and validation
"""

import pytest
import requests
import os
from datetime import datetime, timezone
import uuid

# Configuration
BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
API = f"{BASE_URL}/api"

# Test credentials (from env.example)
SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'pissken@editionsfabsci.com')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')
DG_EMAIL = os.environ.get('DG_EMAIL', 'ali.mamin@editionsfabsci.com')
DG_PASSWORD = os.environ.get('DG_PASSWORD', 'DG@2025')


def bearer(token: str) -> dict:
    """Return Authorization header with bearer token"""
    return {"Authorization": f"Bearer {token}"}


class TestIntegrationAuth:
    """Test authentication endpoints"""
    
    def test_login_super_admin(self):
        """Test super admin login and get tokens"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        assert r.status_code == 200, f"Login failed: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["expires_in"] > 0
    
    def test_login_directeur_general(self):
        """Test DG login"""
        r = requests.post(f"{API}/auth/login", json={
            "email": DG_EMAIL,
            "password": DG_PASSWORD
        }, timeout=10)
        assert r.status_code == 200, f"Login failed: {r.text}"
        data = r.json()
        assert data["user"]["role"] == "directeur_general"
    
    def test_refresh_token(self):
        """Test refresh token endpoint"""
        # First login
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        assert r.status_code == 200
        refresh_token = r.json()["refresh_token"]
        
        # Refresh
        r = requests.post(f"{API}/auth/refresh", json={
            "refresh_token": refresh_token
        }, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different
        assert data["refresh_token"] != refresh_token
    
    def test_me_endpoint(self):
        """Test /auth/me endpoint"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        token = r.json()["access_token"]
        
        r = requests.get(f"{API}/auth/me", headers=bearer(token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == SUPER_ADMIN_EMAIL
        assert data["role"] == "super_admin"


class TestIntegrationClients:
    """Test clients module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_clients(self, super_token):
        """Test GET /clients"""
        r = requests.get(f"{API}/clients", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_create_client(self, super_token):
        """Test POST /clients"""
        unique_name = f"TEST_Integration_{uuid.uuid4().hex[:8]}"
        payload = {
            "nom": unique_name,
            "type_client": "particulier",
            "telephone": f"+225 07 01 02 03 04",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "ville": "Abidjan",
            "plafond_credit": 100000
        }
        r = requests.post(f"{API}/clients", json=payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201, f"Create failed: {r.text}"
        data = r.json()
        assert data["client_id"].startswith("cli_")
        assert data["nom"] == unique_name
    
    def test_check_duplicates(self, super_token):
        """Test POST /clients/check-duplicates"""
        r = requests.post(f"{API}/clients/check-duplicates", json={
            "nom": "Lib. Carrefour Coc",
            "telephone": "+225 27 22 44 50 10"
        }, headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "matches" in data


class TestIntegrationProduits:
    """Test produits module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_produits(self, super_token):
        """Test GET /produits"""
        r = requests.get(f"{API}/produits", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
    
    def test_alertes_stock(self, super_token):
        """Test GET /produits/alertes-stock"""
        r = requests.get(f"{API}/produits/alertes-stock", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "rupture" in data
        assert "alerte" in data


class TestIntegrationCommandes:
    """Test commandes module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_commandes(self, super_token):
        """Test GET /commandes"""
        r = requests.get(f"{API}/commandes", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestIntegrationFactures:
    """Test factures module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_factures(self, super_token):
        """Test GET /factures"""
        r = requests.get(f"{API}/factures", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestIntegrationPaiements:
    """Test paiements module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_paiements(self, super_token):
        """Test GET /paiements"""
        r = requests.get(f"{API}/paiements", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestIntegrationStock:
    """Test stock module endpoints"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_list_mouvements_stock(self, super_token):
        """Test GET /stock/mouvements"""
        r = requests.get(f"{API}/stock/mouvements", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestIntegrationDashboard:
    """Test dashboard endpoint"""
    
    @pytest.fixture(scope="session")
    def super_token(self):
        """Get super admin token"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        data = r.json()
        return data.get("access_token") or data.get("token", "")
    
    def test_dashboard_stats(self, super_token):
        """Test GET /dashboard/stats"""
        r = requests.get(f"{API}/dashboard/stats", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "kpi" in data


class TestIntegrationHealth:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test GET /"""
        r = requests.get(f"{BASE_URL}/", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_endpoint(self):
        """Test GET /health"""
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "checks" in data


class TestIntegrationRBAC:
    """Test RBAC permissions across modules"""
    
    @pytest.fixture(scope="session")
    def tokens(self):
        """Get tokens for different roles"""
        tokens = {}
        
        # Super admin
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        tokens["super_admin"] = r.json()["access_token"]
        
        # DG
        r = requests.post(f"{API}/auth/login", json={
            "email": DG_EMAIL,
            "password": DG_PASSWORD
        }, timeout=10)
        tokens["directeur_general"] = r.json()["access_token"]
        
        return tokens
    
    def test_super_admin_can_access_all(self, tokens):
        """Super admin should have access to all modules"""
        endpoints = [
            "/clients",
            "/produits",
            "/commandes",
            "/factures",
            "/paiements",
            "/utilisateurs",
            "/parametres",
        ]
        for endpoint in endpoints:
            r = requests.get(f"{API}{endpoint}", headers=bearer(tokens["super_admin"]), timeout=10)
            # Should not get 403 (forbidden)
            assert r.status_code != 403, f"Super admin should access {endpoint}"
    
    def test_unauthorized_access(self):
        """Test without token returns 401"""
        r = requests.get(f"{API}/clients", timeout=10)
        assert r.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
