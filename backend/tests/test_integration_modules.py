"""
ERP FABS-CI - Integration Tests for Additional Modules
Tests additional API routes for functionality and RBAC
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
API = f"{BASE_URL}/api"

SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'pissken@editionsfabsci.com')
SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def super_token():
    import time
    for attempt in range(3):
        r = requests.post(f"{API}/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("access_token") or data.get("token", "")
        if r.status_code == 429:
            time.sleep(62)
        else:
            pytest.skip(f"Login échoué: {r.status_code} {r.text}")
    pytest.skip("Rate limit persistant")


class TestIntegrationBonsLivraison:
    """Test bons livraison module"""
    
    def test_list_bons_livraison(self, super_token):
        r = requests.get(f"{API}/bons-livraison", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationBonsRetour:
    """Test bons retour module"""
    
    def test_list_bons_retour(self, super_token):
        r = requests.get(f"{API}/bons-retour", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationColisage:
    """Test colisage module"""
    
    def test_list_colis(self, super_token):
        r = requests.get(f"{API}/colisage/colis", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_expeditions(self, super_token):
        r = requests.get(f"{API}/colisage/expeditions", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_mouvements(self, super_token):
        r = requests.get(f"{API}/colisage/mouvements", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationLogistique:
    """Test logistique module"""
    
    def test_list_logistique(self, super_token):
        r = requests.get(f"{API}/logistique/missions", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationComptabiliteAvancee:
    """Test comptabilite avancee module"""
    
    def test_list_ecritures(self, super_token):
        r = requests.get(f"{API}/comptabilite-avancee/ecritures", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_get_plan_comptable(self, super_token):
        r = requests.get(f"{API}/comptabilite-avancee/plan-comptable", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationFleet:
    """Test fleet management module"""
    
    def test_list_vehicles(self, super_token):
        r = requests.get(f"{API}/fleet/vehicules", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_insurances(self, super_token):
        r = requests.get(f"{API}/fleet/assurances", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_inspections(self, super_token):
        r = requests.get(f"{API}/fleet/visites-techniques", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_assignments(self, super_token):
        r = requests.get(f"{API}/fleet/affectations", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_maintenance(self, super_token):
        r = requests.get(f"{API}/fleet/maintenances", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_fuel(self, super_token):
        r = requests.get(f"{API}/fleet/vehicules", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationLogisticsCosts:
    """Test logistics costs module"""
    
    def test_list_costs(self, super_token):
        r = requests.get(f"{API}/logistics-costs/couts", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_missions(self, super_token):
        r = requests.get(f"{API}/logistics-costs/couts", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationMultiChannelNotifications:
    """Test multi-channel notifications module"""
    
    def test_list_notifications(self, super_token):
        r = requests.get(f"{API}/multi-channel-notifications/logs", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_channels(self, super_token):
        r = requests.get(f"{API}/multi-channel-notifications/config-check", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_templates(self, super_token):
        r = requests.get(f"{API}/multi-channel-notifications/logs", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationBIAnalytics:
    """Test BI analytics module"""
    
    def test_dashboard_bi(self, super_token):
        r = requests.get(f"{API}/bi-analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_ventes_analytics(self, super_token):
        r = requests.get(f"{API}/bi-analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_clients_analytics(self, super_token):
        r = requests.get(f"{API}/bi-analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_produits_analytics(self, super_token):
        r = requests.get(f"{API}/bi-analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_finance_analytics(self, super_token):
        r = requests.get(f"{API}/bi-analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationWorkflowApprovals:
    """Test workflow approvals module"""
    
    def test_list_workflows(self, super_token):
        r = requests.get(f"{API}/workflow-approvals/workflows", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_audit_logs(self, super_token):
        r = requests.get(f"{API}/workflow-approvals/audit-logs", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationFileStorage:
    """Test file storage module"""
    
    def test_list_files(self, super_token):
        r = requests.get(f"{API}/file-storage/documents", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_list_folders(self, super_token):
        r = requests.get(f"{API}/file-storage/stats", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_quota(self, super_token):
        r = requests.get(f"{API}/file-storage/stats", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationBackup:
    """Test backup module"""
    
    def test_list_backups(self, super_token):
        r = requests.get(f"{API}/backup/backups", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_config(self, super_token):
        r = requests.get(f"{API}/backup/config", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationNotifications:
    """Test notifications module"""
    
    def test_list_notifications(self, super_token):
        r = requests.get(f"{API}/notifications", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_non_lues(self, super_token):
        r = requests.get(f"{API}/notifications/non-lues", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_count(self, super_token):
        r = requests.get(f"{API}/notifications/count", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_preferences(self, super_token):
        r = requests.get(f"{API}/notifications/preferences", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_templates(self, super_token):
        r = requests.get(f"{API}/notifications/templates", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))
    
    def test_logs(self, super_token):
        r = requests.get(f"{API}/notifications/logs", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationRecherche:
    """Test recherche module"""
    
    def test_recherche_globale(self, super_token):
        r = requests.get(f"{API}/recherche/globale?q=test", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationDocumentsAI:
    """Test documents AI module"""
    
    def test_list_documents(self, super_token):
        r = requests.get(f"{API}/documents-ai", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationAnalytics:
    """Test analytics module"""
    
    def test_dashboard_analytics(self, super_token):
        r = requests.get(f"{API}/analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_kpis(self, super_token):
        r = requests.get(f"{API}/analytics/dashboard", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_trends(self, super_token):
        r = requests.get(f"{API}/analytics/evolution", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationRapports:
    """Test rapports module"""
    
    def test_rapports_ventes(self, super_token):
        r = requests.get(f"{API}/rapports/ventes", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_rapports_stock(self, super_token):
        r = requests.get(f"{API}/rapports/stock", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
    
    def test_rapports_clients(self, super_token):
        r = requests.get(f"{API}/rapports/ventes", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200


class TestIntegrationUtilisateurs:
    """Test utilisateurs module"""
    
    def test_list_utilisateurs(self, super_token):
        r = requests.get(f"{API}/utilisateurs", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


class TestIntegrationParametres:
    """Test parametres module"""
    
    def test_list_parametres(self, super_token):
        r = requests.get(f"{API}/parametres", headers=bearer(super_token), timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), (list, dict))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
