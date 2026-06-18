"""
Tests unitaires pour le module FNE - Facture Normalisée Électronique
"""
import pytest
from datetime import datetime, timezone
from fne_module import (
    FNEStatus,
    InvoiceType,
    FNEInvoiceItem,
    FNEInvoice,
    FNEMetadata,
    FNEConfig,
    FNEService,
    FNEQueue,
    FNEResponse
)


class TestFNEEnums:
    """Tests des enums FNE"""
    
    def test_fne_status_values(self):
        """Test des valeurs de statut FNE"""
        assert FNEStatus.PENDING == "pending"
        assert FNEStatus.SUBMITTED == "submitted"
        assert FNEStatus.ACCEPTED == "accepted"
        assert FNEStatus.REJECTED == "rejected"
        assert FNEStatus.ERROR == "error"
    
    def test_invoice_type_values(self):
        """Test des types de facture"""
        assert InvoiceType.FACTURE == "facture"
        assert InvoiceType.AVOIR == "avoir"
        assert InvoiceType.PROFORMA == "proforma"


class TestInvoiceModels:
    """Tests des modèles de facture"""
    
    def test_invoice_item_validation(self):
        """Test validation des articles de facture"""
        item = FNEInvoiceItem(
            code_article="LIV001",
            designation="Livre Mathématiques CM1",
            quantite=10,
            prix_unitaire=5000,
            taux_tva=18.0,
            montant_ht=50000,
            montant_tva=9000,
            montant_ttc=59000
        )
        assert item.code_article == "LIV001"
        assert item.quantite == 10
        assert item.prix_unitaire == 5000
    
    def test_invoice_item_negative_quantity(self):
        """Test que la quantité négative est rejetée"""
        with pytest.raises(Exception):
            FNEInvoiceItem(
                code_article="LIV001",
                designation="Livre",
                quantite=-5,
                prix_unitaire=5000,
                taux_tva=18.0,
                montant_ht=0,
                montant_tva=0,
                montant_ttc=0
            )
    
    def test_invoice_validation(self):
        """Test validation de la facture"""
        item = FNEInvoiceItem(
            code_article="LIV001",
            designation="Livre",
            quantite=10,
            prix_unitaire=5000,
            taux_tva=18.0,
            montant_ht=50000,
            montant_tva=9000,
            montant_ttc=59000
        )
        
        invoice = FNEInvoice(
            reference="FAC-2024-001",
            client_nom="École Primaire Bingerville",
            client_tin="CI123456789",
            client_adresse="Bingerville",
            client_telephone="+2250707070707",
            client_email="ecole@example.com",
            date_facture="2024-01-15",
            date_echeance="2024-02-15",
            type_facture=InvoiceType.FACTURE,
            articles=[item],
            montant_ht=50000,
            montant_tva=9000,
            montant_ttc=59000,
            remise_globale=0
        )
        
        assert invoice.reference == "FAC-2024-001"
        assert invoice.client_nom == "École Primaire Bingerville"
        assert invoice.montant_ttc == 59000


class TestFNEMetadata:
    """Tests des métadonnées FNE"""
    
    def test_fne_metadata_creation(self):
        """Test création des métadonnées FNE"""
        metadata = FNEMetadata(
            invoice_id="FAC-2024-001",
            status=FNEStatus.PENDING
        )
        
        assert metadata.invoice_id == "FAC-2024-001"
        assert metadata.status == FNEStatus.PENDING
        assert metadata.fne_id is None
        assert metadata.qr_code is None
        assert metadata.id is not None  # UUID généré automatiquement
    
    def test_fne_metadata_default_values(self):
        """Test valeurs par défaut des métadonnées"""
        metadata = FNEMetadata(invoice_id="FAC-2024-001")
        
        assert metadata.status == FNEStatus.PENDING
        assert metadata.response_payload is None
        assert metadata.error_message is None
        assert metadata.created_at is not None
        assert metadata.updated_at is not None


class TestFNEConfig:
    """Tests de la configuration FNE"""
    
    def test_fne_config_creation(self):
        """Test création de la configuration FNE"""
        config = FNEConfig(
            dgi_api_url="https://api.dgi.ci/fne/v1",
            dgi_api_key="test_key",
            dgi_username="test_user",
            dgi_password="test_pass",
            company_tin="CI123456789"
        )
        
        assert config.dgi_api_url == "https://api.dgi.ci/fne/v1"
        assert config.dgi_api_key == "test_key"
        assert config.company_tin == "CI123456789"
    
    def test_fne_config_default_retry(self):
        """Test valeurs par défaut de retry"""
        config = FNEConfig(
            dgi_api_url="https://api.dgi.ci/fne/v1",
            dgi_api_key="test_key",
            dgi_username="test_user",
            dgi_password="test_pass",
            company_tin="CI123456789"
        )
        
        assert config.retry_max_attempts == 3
        assert config.retry_delay_seconds == 2


class TestFNEResponse:
    """Tests des réponses FNE"""
    
    def test_fne_response_success(self):
        """Test réponse FNE succès"""
        response = FNEResponse(
            success=True,
            message="Facture acceptée",
            data={"fne_id": "FNE-123456"}
        )
        
        assert response.success is True
        assert response.message == "Facture acceptée"
        assert response.data is not None
    
    def test_fne_response_failure(self):
        """Test réponse FNE échec"""
        response = FNEResponse(
            success=False,
            message="Facture rejetée",
            data={"error": "Invalid data"}
        )
        
        assert response.success is False
        assert response.message == "Facture rejetée"


class TestFNEQueue:
    """Tests de la queue FNE"""
    
    @pytest.mark.asyncio
    async def test_queue_enqueue_dequeue(self):
        """Test enqueue et dequeue"""
        # Note: Ce test nécessite une instance Redis
        # À adapter avec un mock Redis pour les tests unitaires
        pass
    
    @pytest.mark.asyncio
    async def test_queue_task_status(self):
        """Test mise à jour du statut de tâche"""
        # Note: Ce test nécessite une instance Redis
        # À adapter avec un mock Redis pour les tests unitaires
        pass


class TestFNEService:
    """Tests du service FNE"""
    
    def test_transform_invoice_to_fne_structure(self):
        """Test structure de transformation facture vers FNE"""
        # Note: Ce test nécessite une instance de base de données
        # À adapter avec un mock MongoDB pour les tests unitaires
        pass
    
    def test_generate_qr_code(self):
        """Test génération QR code"""
        # Note: Ce test nécessite une instance de service
        # À adapter avec un mock pour les tests unitaires
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
