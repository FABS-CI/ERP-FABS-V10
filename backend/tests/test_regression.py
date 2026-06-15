"""
ERP FABS-CI - Regression Tests
Tests to ensure no regressions are introduced in existing functionality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8001')
API = f"{BASE_URL}/api"

SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'pissken@editionsfabsci.com')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="class")
def super_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }, timeout=10)
    return r.json()["access_token"]


class TestRegressionAuth:
    """Regression tests for authentication"""
    
    def test_login_still_works(self):
        """Ensure login still works after changes"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        assert r.status_code == 200
        assert "access_token" in r.json()
    
    def test_refresh_token_still_works(self):
        """Ensure refresh token still works"""
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        refresh_token = r.json()["refresh_token"]
        
        r = requests.post(f"{API}/auth/refresh", json={
            "refresh_token": refresh_token
        }, timeout=10)
        assert r.status_code == 200
        assert "access_token" in r.json()


class TestRegressionClients:
    """Regression tests for clients module"""
    
    def test_clients_list_still_works(self, super_token):
        """Ensure clients list still works"""
        r = requests.get(f"{API}/clients", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert "items" in r.json()
    
    def test_client_creation_still_works(self, super_token):
        """Ensure client creation still works"""
        import uuid
        payload = {
            "nom": f"Regression_{uuid.uuid4().hex[:8]}",
            "type_client": "particulier",
            "telephone": "+225 07 01 02 03 04",
            "email": f"reg_{uuid.uuid4().hex[:8]}@example.com",
            "ville": "Abidjan"
        }
        r = requests.post(f"{API}/clients", json=payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201


class TestRegressionProduits:
    """Regression tests for products module"""
    
    def test_products_list_still_works(self, super_token):
        """Ensure products list still works"""
        r = requests.get(f"{API}/produits", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert "items" in r.json()
    
    def test_stock_alerts_still_works(self, super_token):
        """Ensure stock alerts still work"""
        r = requests.get(f"{API}/produits/alertes-stock", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestRegressionCommandes:
    """Regression tests for commandes module"""
    
    def test_commandes_list_still_works(self, super_token):
        """Ensure commandes list still works"""
        r = requests.get(f"{API}/commandes", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestRegressionFactures:
    """Regression tests for factures module"""
    
    def test_factures_list_still_works(self, super_token):
        """Ensure factures list still works"""
        r = requests.get(f"{API}/factures", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestRegressionRBAC:
    """Regression tests for RBAC"""
    
    def test_super_admin_access_still_works(self, super_token):
        """Ensure super admin still has access to all modules"""
        endpoints = ["/clients", "/produits", "/utilisateurs"]
        for endpoint in endpoints:
            r = requests.get(f"{API}{endpoint}", headers=bearer(super_token), timeout=10)
            assert r.status_code != 403, f"Super admin should access {endpoint}"


class TestRegressionSecurity:
    """Regression tests for security features"""
    
    def test_security_headers_present(self):
        """Ensure security headers are still present"""
        r = requests.get(f"{BASE_URL}/", timeout=10)
        assert r.status_code == 200
        assert "X-Content-Type-Options" in r.headers
        assert "X-Frame-Options" in r.headers
        assert "X-XSS-Protection" in r.headers
    
    def test_unauthorized_access_blocked(self):
        """Ensure unauthorized access is still blocked"""
        r = requests.get(f"{API}/clients", timeout=10)
        assert r.status_code == 401


class TestRegressionDataIntegrity:
    """Regression tests for data integrity"""
    
    def test_client_data_structure(self, super_token):
        """Ensure client data structure hasn't changed"""
        r = requests.get(f"{API}/clients", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        if len(data["items"]) > 0:
            client = data["items"][0]
            required_fields = ["client_id", "nom", "type_client", "actif"]
            for field in required_fields:
                assert field in client, f"Missing field: {field}"
    
    def test_product_data_structure(self, super_token):
        """Ensure product data structure hasn't changed"""
        r = requests.get(f"{API}/produits", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        if len(data["items"]) > 0:
            product = data["items"][0]
            required_fields = ["product_id", "reference", "titre", "categorie", "stock_actuel"]
            for field in required_fields:
                assert field in product, f"Missing field: {field}"


class TestRegressionAPIResponseTimes:
    """Regression tests for API response times"""
    
    def test_health_check_response_time(self):
        """Ensure health check is still fast"""
        import time
        start = time.time()
        r = requests.get(f"{API}/health", timeout=10)
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 2.0, f"Health check too slow: {elapsed}s"
    
    def test_dashboard_response_time(self, super_token):
        """Ensure dashboard is still fast"""
        import time
        start = time.time()
        r = requests.get(f"{API}/dashboard/stats", headers=bearer(super_token), timeout=10)
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 3.0, f"Dashboard too slow: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
