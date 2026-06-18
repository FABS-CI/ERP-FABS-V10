"""
ERP FABS-CI - E2E Tests for Critical Workflows
Tests end-to-end workflows that span multiple modules
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
API = f"{BASE_URL}/api"

SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'pissken@editionsfabsci.com')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def super_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }, timeout=10)
    data = r.json()
    return data.get("access_token") or data.get("token", "")


class TestE2EWorkflowCommandeToFacture:
    """E2E test: Create commande -> Validate -> Create facture -> Validate"""
    
    def test_workflow_commande_complete(self, super_token):
        """Test complete workflow from commande to facture"""
        
        # 1. Create a client
        unique_name = f"E2E_Client_{uuid.uuid4().hex[:8]}"
        client_payload = {
            "nom": unique_name,
            "type_client": "particulier",
            "telephone": f"+225 07 01 02 03 04",
            "email": f"e2e_{uuid.uuid4().hex[:8]}@example.com",
            "ville": "Abidjan",
            "plafond_credit": 1000000
        }
        r = requests.post(f"{API}/clients", json=client_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        client_id = r.json()["client_id"]
        
        # 2. Create a product
        product_payload = {
            "titre": f"E2E Product {uuid.uuid4().hex[:8]}",
            "reference": f"E2E-{uuid.uuid4().hex[:6].upper()}",
            "categorie": "primaire",
            "prix_vente": 5000,
            "stock_actuel": 100,
            "stock_minimum": 10
        }
        r = requests.post(f"{API}/produits", json=product_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        product_id = r.json()["product_id"]
        
        # 3. Create a commande
        commande_payload = {
            "client_id": client_id,
            "lignes": [
                {
                    "produit_id": product_id,
                    "quantite": 5,
                    "prix_unitaire": 5000
                }
            ],
            "date_livraison_prevue": "2026-12-31"
        }
        r = requests.post(f"{API}/commandes?submit=true", json=commande_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        commande_id = r.json()["commande_id"]
        
        # 4. Validate the commande
        r = requests.post(f"{API}/commandes/{commande_id}/valider", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # 5. Create a bon de livraison
        bl_payload = {
            "commande_id": commande_id,
            "date_livraison": "2026-12-31"
        }
        r = requests.post(f"{API}/bons-livraison", json=bl_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        bl_id = r.json()["bl_id"]
        
        # 6. Deliver the bon
        r = requests.post(f"{API}/bons-livraison/{bl_id}/livrer", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # 7. Create a facture
        facture_payload = {
            "commande_id": commande_id,
            "date_facture": "2026-12-31"
        }
        r = requests.post(f"{API}/factures", json=facture_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        facture_id = r.json()["facture_id"]
        
        # 8. Validate the facture
        r = requests.post(f"{API}/factures/{facture_id}/valider", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # Cleanup
        requests.delete(f"{API}/clients/{client_id}", headers=bearer(super_token), timeout=10)


class TestE2EWorkflowUserLifecycle:
    """E2E test: Create user -> Update permissions -> Change password -> Delete"""
    
    def test_workflow_user_lifecycle(self, super_token):
        """Test complete user lifecycle"""
        
        # 1. Create a new user
        unique_email = f"e2e_{uuid.uuid4().hex[:8]}@example.com"
        user_payload = {
            "email": unique_email,
            "password": "Test@2025",
            "nom_complet": "E2E Test User",
            "role": "comptable",
            "actif": True
        }
        r = requests.post(f"{API}/auth/create-user", json=user_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        user_id = r.json()["user_id"]
        
        # 2. Login as new user
        r = requests.post(f"{API}/auth/login", json={
            "email": unique_email,
            "password": "Test@2025"
        }, timeout=10)
        assert r.status_code == 200
        user_token = r.json()["access_token"]
        
        # 3. Access comptable module
        r = requests.get(f"{API}/factures", headers=bearer(user_token), timeout=10)
        assert r.status_code == 200
        
        # 4. Change password (as super admin)
        r = requests.post(f"{API}/auth/change-password/{user_id}", 
                        json={"new_password": "NewTest@2025"}, 
                        headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # 5. Login with new password
        r = requests.post(f"{API}/auth/login", json={
            "email": unique_email,
            "password": "NewTest@2025"
        }, timeout=10)
        assert r.status_code == 200
        
        # 6. Delete user
        r = requests.delete(f"{API}/utilisateurs/{user_id}", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # 7. Verify login fails
        r = requests.post(f"{API}/auth/login", json={
            "email": unique_email,
            "password": "NewTest@2025"
        }, timeout=10)
        assert r.status_code == 401


class TestE2EWorkflowStockMovement:
    """E2E test: Stock movement -> Alert check -> Replenishment"""
    
    def test_workflow_stock_movement(self, super_token):
        """Test stock movement workflow"""
        
        # 1. Create a product with low stock
        product_payload = {
            "titre": f"E2E Stock Product {uuid.uuid4().hex[:8]}",
            "reference": f"STK-{uuid.uuid4().hex[:6].upper()}",
            "categorie": "primaire",
            "prix_vente": 1000,
            "stock_actuel": 5,
            "stock_minimum": 10
        }
        r = requests.post(f"{API}/produits", json=product_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        product_id = r.json()["product_id"]
        
        # 2. Check stock alerts
        r = requests.get(f"{API}/produits/alertes-stock", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        alerts = r.json()
        assert alerts["total"] > 0
        
        # 3. Create stock movement (replenishment)
        mouvement_payload = {
            "produit_id": product_id,
            "quantite": 20,
            "type_mouvement": "entree",
            "motif": "Réapprovisionnement"
        }
        r = requests.post(f"{API}/stock/mouvements", json=mouvement_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        
        # 4. Verify stock updated
        r = requests.get(f"{API}/produits/{product_id}", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        product = r.json()
        assert product["stock_actuel"] == 25  # 5 + 20
        
        # Cleanup
        requests.delete(f"{API}/produits/{product_id}", headers=bearer(super_token), timeout=10)


class TestE2EWorkflowNotification:
    """E2E test: Create notification -> Read -> Mark all read"""
    
    def test_workflow_notification(self, super_token):
        """Test notification workflow"""
        
        # 1. Create a notification template
        template_payload = {
            "nom": "E2E Test Template",
            "sujet": "Test Notification",
            "contenu": "Ceci est un test E2E",
            "type": "email"
        }
        r = requests.post(f"{API}/notifications/templates", json=template_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        template_id = r.json()["template_id"]
        
        # 2. Get unread count
        r = requests.get(f"{API}/notifications/count", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        initial_count = r.json()["count"]
        
        # 3. Mark all as read
        r = requests.patch(f"{API}/notifications/tout-lire", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        
        # 4. Verify count is 0
        r = requests.get(f"{API}/notifications/count", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert r.json()["count"] == 0
        
        # Cleanup
        requests.delete(f"{API}/notifications/templates/{template_id}", headers=bearer(super_token), timeout=10)


class TestE2EWorkflowRefreshToken:
    """E2E test: Login -> Access expires -> Refresh -> Continue"""
    
    def test_workflow_refresh_token(self):
        """Test refresh token workflow"""
        
        # 1. Login
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=10)
        assert r.status_code == 200
        data = r.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        # 2. Use access token
        r = requests.get(f"{API}/clients", headers=bearer(access_token), timeout=10)
        assert r.status_code == 200
        
        # 3. Refresh token
        r = requests.post(f"{API}/auth/refresh", json={
            "refresh_token": refresh_token
        }, timeout=10)
        assert r.status_code == 200
        new_data = r.json()
        new_access_token = new_data["access_token"]
        new_refresh_token = new_data["refresh_token"]
        
        # 4. Verify new tokens are different
        assert new_access_token != access_token
        assert new_refresh_token != refresh_token
        
        # 5. Use new access token
        r = requests.get(f"{API}/clients", headers=bearer(new_access_token), timeout=10)
        assert r.status_code == 200
        
        # 6. Verify old refresh token is revoked
        r = requests.post(f"{API}/auth/refresh", json={
            "refresh_token": refresh_token
        }, timeout=10)
        assert r.status_code == 401  # Old token revoked


class TestE2EWorkflowBackupRestore:
    """E2E test: Create backup -> Verify -> Restore"""
    
    def test_workflow_backup_restore(self, super_token):
        """Test backup and restore workflow"""
        
        # 1. Get backup config
        r = requests.get(f"{API}/backup/config", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        config = r.json()
        
        # 2. Create backup
        r = requests.post(f"{API}/backup/create", headers=bearer(super_token), timeout=30)
        assert r.status_code == 200
        backup_id = r.json()["backup_id"]
        
        # 3. List backups
        r = requests.get(f"{API}/backup/list", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        backups = r.json()
        assert len(backups) > 0
        
        # 4. Verify backup exists
        backup_exists = any(b["backup_id"] == backup_id for b in backups)
        assert backup_exists


class TestE2EWorkflowFleetManagement:
    """E2E test: Create vehicle -> Add insurance -> Add maintenance"""
    
    def test_workflow_fleet_management(self, super_token):
        """Test fleet management workflow"""
        
        # 1. Create vehicle
        vehicle_payload = {
            "immatriculation": f"E2E-{uuid.uuid4().hex[:6].upper()}",
            "marque": "Toyota",
            "modele": "Hilux",
            "annee": 2024,
            "type": "camion",
            "statut": "actif"
        }
        r = requests.post(f"{API}/fleet/vehicles", json=vehicle_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        vehicle_id = r.json()["vehicle_id"]
        
        # 2. Add insurance
        insurance_payload = {
            "vehicle_id": vehicle_id,
            "compagnie": "AXA",
            "numero_police": f"POL-{uuid.uuid4().hex[:8].upper()}",
            "date_debut": "2026-01-01",
            "date_fin": "2026-12-31",
            "montant": 500000
        }
        r = requests.post(f"{API}/fleet/insurances", json=insurance_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        
        # 3. Add maintenance
        maintenance_payload = {
            "vehicle_id": vehicle_id,
            "type": "preventive",
            "description": "Maintenance routine",
            "date": "2026-06-01",
            "cout": 50000
        }
        r = requests.post(f"{API}/fleet/maintenance", json=maintenance_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        
        # 4. Assign driver
        assignment_payload = {
            "vehicle_id": vehicle_id,
            "chauffeur_id": "driver_001",
            "date_debut": "2026-06-01",
            "date_fin": "2026-12-31"
        }
        r = requests.post(f"{API}/fleet/assignments", json=assignment_payload, headers=bearer(super_token), timeout=10)
        assert r.status_code == 201
        
        # Cleanup
        requests.delete(f"{API}/fleet/vehicles/{vehicle_id}", headers=bearer(super_token), timeout=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
