"""
Tests unitaires pour le module Document Settings
"""
import pytest
from datetime import datetime, timezone
from document_settings_module import (
    DocumentSettings,
    WatermarkSettings,
    CompanyInfo,
    determine_watermark,
    InvoiceTemplate
)


class TestWatermarkDetermination:
    """Tests de la fonction determine_watermark"""
    
    def test_proforma_watermark(self):
        """Test filigrane PROFORMA"""
        result = determine_watermark("proforma", "emise", 0, 10000)
        assert result == "PROFORMA"
    
    def test_brouillon_watermark(self):
        """Test filigrane BROUILLON"""
        result = determine_watermark("facture", "brouillon", 0, 10000)
        assert result == "BROUILLON"
    
    def test_paye_watermark(self):
        """Test filigrane PAYÉ"""
        result = determine_watermark("facture", "payee", 10000, 10000)
        assert result == "PAYÉ"
    
    def test_paiement_partiel_watermark(self):
        """Test filigrane PAIEMENT_PARTIEL"""
        result = determine_watermark("facture", "partiellement_payee", 5000, 10000)
        assert result == "PAIEMENT_PARTIEL"
    
    def test_impaye_watermark(self):
        """Test filigrane IMPAYÉ"""
        result = determine_watermark("facture", "emise", 0, 10000)
        assert result == "IMPAYÉ"
    
    def test_annule_watermark(self):
        """Test filigrane ANNULÉ"""
        result = determine_watermark("facture", "annulee", 0, 10000)
        assert result == "ANNULÉ"
    
    def test_avoir_watermark(self):
        """Test filigrane AVOIR"""
        result = determine_watermark("avoir", "emise", 0, 10000)
        assert result == "AVOIR"
    
    def test_no_watermark(self):
        """Test aucun filigrane"""
        result = determine_watermark("facture", "emise", 10000, 10000)
        assert result is None


class TestDocumentSettings:
    """Tests du schéma DocumentSettings"""
    
    def test_default_settings(self):
        """Test création des paramètres par défaut"""
        settings = DocumentSettings()
        assert settings.selected_template == "classique_professionnel"
        assert settings.watermark_settings.enabled == True
        assert settings.watermark_settings.opacity == 0.3
        assert settings.watermark_settings.size == 48
        assert settings.watermark_settings.position == "center"
        assert settings.watermark_settings.rotation == 45
        assert settings.company_info.nom == "EDITIONS FABS-CI"
    
    def test_watermark_settings_validation(self):
        """Test validation des paramètres de filigrane"""
        # Opacité valide
        settings = WatermarkSettings(opacity=0.5)
        assert settings.opacity == 0.5
        
        # Taille valide
        settings = WatermarkSettings(size=36)
        assert settings.size == 36
    
    def test_company_info_default(self):
        """Test informations entreprise par défaut"""
        company = CompanyInfo()
        assert company.nom == "EDITIONS FABS-CI"
        assert company.adresse == "BP 693"
        assert company.telephone == "+225 07 59 73 71 23"
        assert company.email == "edition693fabs@gmail.com"
        assert "CORIS BANK" in company.banques
        assert "SGBCI" in company.banques


class TestInvoiceTemplates:
    """Tests des modèles de facture"""
    
    def test_valid_templates(self):
        """Test que tous les modèles sont valides"""
        valid_templates = [
            "classique_professionnel",
            "moderne_bleu",
            "premium",
            "corporate_orange",
            "elegant_administratif"
        ]
        
        for template in valid_templates:
            assert template in InvoiceTemplate.__args__
    
    def test_template_selection(self):
        """Test sélection de modèle"""
        settings = DocumentSettings(selected_template="moderne_bleu")
        assert settings.selected_template == "moderne_bleu"


class TestDocumentSettingsAPI:
    """Tests des endpoints API (simulation)"""
    
    def test_get_settings_response_structure(self):
        """Test structure de réponse GET settings"""
        settings = DocumentSettings()
        response_dict = settings.model_dump()
        
        assert "selected_template" in response_dict
        assert "watermark_settings" in response_dict
        assert "company_info" in response_dict
        assert "logo_url" in response_dict
        assert "updated_at" in response_dict
    
    def test_update_settings(self):
        """Test mise à jour des paramètres"""
        settings = DocumentSettings()
        settings.selected_template = "premium"
        settings.watermark_settings.enabled = False
        
        assert settings.selected_template == "premium"
        assert settings.watermark_settings.enabled == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
