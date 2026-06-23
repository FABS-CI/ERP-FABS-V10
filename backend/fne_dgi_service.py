"""
Service FNE DGI - Intégration API Direction Générale des Impôts Côte d'Ivoire

Ce module gère l'intégration avec l'API FNE de la DGI pour la certification
électronique des factures conformément à la loi de finances 2025.
"""

import httpx
import logging
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

logger = logging.getLogger("fabsci.fne_dgi")

load_dotenv()


# ============================================================================
# ENUMS
# ============================================================================

class FNEStatus(str, Enum):
    """Statut de certification FNE"""
    PENDING = "pending"
    CERTIFIED = "certified"
    REJECTED = "rejected"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    """Méthodes de paiement acceptées par la DGI"""
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    MOBILE_MONEY = "mobile-money"
    TRANSFER = "transfer"
    DEFERRED = "deferred"


class InvoiceTemplate(str, Enum):
    """Templates de facture acceptés par la DGI"""
    B2B = "B2B"  # Client entreprise/professionnel avec NCC
    B2C = "B2C"  # Client particulier
    B2G = "B2G"  # Institution gouvernementale
    B2F = "B2F"  # Client international


class TaxType(str, Enum):
    """Types de taxes acceptés par la DGI"""
    TVA = "TVA"      # TVA normale 18%
    TVAB = "TVAB"    # TVA réduite 9%
    TVAC = "TVAC"    # TVA exonérée convention 0%
    TVAD = "TVAD"    # TVA exonérée légale 0%


# ============================================================================
# PYDANTIC MODELS - REQUÊTES API DGI
# ============================================================================

class FNEInvoiceItem(BaseModel):
    """Ligne d'article pour l'API DGI [C4: taxes MUST have default]"""
    reference: str
    description: str
    quantity: float = Field(gt=0)
    amount: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    measurementUnit: str = "pcs"
    taxes: List[str] = Field(default=["TVA"])  # [C4] DEFAULT REQUIRED
    customTaxes: List[Dict[str, Any]] = Field(default_factory=list)


class FNESignRequest(BaseModel):
    """Requête de certification de facture (endpoint /sign)"""
    invoiceType: str = Field(default="sale")  # "sale" ou "purchase"
    paymentMethod: str = Field(default="cash")
    template: str = Field(default="B2B")
    clientNcc: Optional[str] = None
    clientCompanyName: str
    clientPhone: str
    clientEmail: Optional[str] = None
    clientSellerName: str
    pointOfSale: str
    establishment: str
    isRne: bool = False
    rne: Optional[str] = None
    foreignCurrency: Optional[str] = None
    foreignCurrencyRate: float = 0
    items: List[FNEInvoiceItem]
    customTaxes: List[Dict[str, Any]] = Field(default_factory=list)
    discount: float = Field(default=0, ge=0)
    commercialMessage: Optional[str] = None
    footer: Optional[str] = None


class FNERefundRequest(BaseModel):
    """Requête de certification d'avoir (endpoint /refund)"""
    items: List[Dict[str, Any]]  # [{"id": "uuid", "quantity": 10}]


# ============================================================================
# PYDANTIC MODELS - RÉPONSES API DGI
# ============================================================================

class DGIInvoiceItem(BaseModel):
    """Ligne d'article dans la réponse DGI"""
    id: str
    quantity: float
    reference: str
    description: str
    amount: float
    discount: float


class DGIInvoice(BaseModel):
    """Facture dans la réponse DGI"""
    id: str
    parentId: Optional[str] = None
    parentReference: Optional[str] = None
    token: str
    reference: str
    type: str
    subtype: str
    date: str
    paymentMethod: str
    amount: float
    vatAmount: float
    status: str
    template: str
    items: List[DGIInvoiceItem]


class DGISignResponse(BaseModel):
    """Réponse de certification de facture"""
    ncc: str
    reference: str
    token: str
    warning: bool
    balance_sticker: int
    invoice: DGIInvoice


class DGIRefundResponse(BaseModel):
    """Réponse de certification d'avoir"""
    ncc: str
    reference: str
    token: str
    warning: bool
    balance_sticker: int


# ============================================================================
# SERVICE FNE
# ============================================================================

# ============================================================================
# MAPPING MÉTHODES DE PAIEMENT ERP → DGI (C4)
# ============================================================================
# Valeurs ERP internes → valeurs attendues par l'API DGI
PAYMENT_METHOD_MAP: Dict[str, str] = {
    # espèces
    "especes":          "cash",
    "espèces":          "cash",
    "cash":             "cash",
    "liquide":          "cash",
    # mobile money
    "mobile_money":     "mobile-money",
    "mobile-money":     "mobile-money",
    "mobilemoney":      "mobile-money",
    "momo":             "mobile-money",
    "orange_money":     "mobile-money",
    "mtn_money":        "mobile-money",
    "wave":             "mobile-money",
    # carte bancaire
    "carte_bancaire":   "card",
    "carte":            "card",
    "card":             "card",
    "visa":             "card",
    "mastercard":       "card",
    # chèque
    "cheque":           "check",
    "chèque":           "check",
    "check":            "check",
    # virement bancaire
    "virement":         "transfer",
    "virement_bancaire":"transfer",
    "transfer":         "transfer",
    "bank_transfer":    "transfer",
    # crédit / différé
    "credit":           "credit",
    "crédit":           "credit",
    "a_credit":         "credit",
    "differe":          "credit",
    "différé":          "credit",
    "deferred":         "credit",
}


def map_payment_method(erp_value: str) -> str:
    """
    Convertit une méthode de paiement ERP interne en valeur DGI.

    Args:
        erp_value: valeur stockée dans la facture ERP (ex: "especes", "mobile_money")

    Returns:
        Valeur DGI valide (ex: "cash", "mobile-money") — défaut "cash" si inconnu.
    """
    normalized = (erp_value or "cash").strip().lower().replace(" ", "_")
    dgi_value = PAYMENT_METHOD_MAP.get(normalized)
    if dgi_value is None:
        logger.warning("map_payment_method: valeur inconnue '%s' → défaut 'cash'", erp_value)
        return "cash"
    return dgi_value


class FNEDGIService:
    """Service pour l'intégration avec l'API FNE de la DGI"""
    
    def __init__(self):
        self.base_url = os.getenv("FNE_BASE_URL", "http://54.247.95.108/ws")
        # Support DGI_API_KEY (clé principale) ET FNE_API_KEY (alias legacy)
        self.api_key = os.getenv("DGI_API_KEY") or os.getenv("FNE_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key:
            raise ValueError("DGI_API_KEY non définie dans les variables d'environnement")
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.http_client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Génère les headers pour les requêtes API DGI"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def sign_invoice(self, request: FNESignRequest) -> DGISignResponse:
        """
        Certifie une facture via l'API DGI (endpoint /sign)
        
        Args:
            request: Données de la facture à certifier
            
        Returns:
            DGISignResponse: Réponse de la DGI
            
        Raises:
            httpx.HTTPStatusError: Erreur HTTP (400, 401, 500)
            httpx.RequestError: Erreur de connexion
        """
        endpoint = f"{self.base_url}/external/invoices/sign"
        headers = self._get_headers()
        
        response = await self.http_client.post(
            endpoint,
            json=request.model_dump(),
            headers=headers
        )
        response.raise_for_status()
        
        return DGISignResponse(**response.json())
    
    async def refund_invoice(self, invoice_id: str, request: FNERefundRequest) -> DGIRefundResponse:
        """
        Certifie un avoir via l'API DGI (endpoint /refund)
        
        Args:
            invoice_id: ID de la facture d'origine (invoice.id de la réponse DGI)
            request: Données de l'avoir à certifier
            
        Returns:
            DGIRefundResponse: Réponse de la DGI
            
        Raises:
            httpx.HTTPStatusError: Erreur HTTP (400, 401, 500)
            httpx.RequestError: Erreur de connexion
        """
        endpoint = f"{self.base_url}/external/invoices/{invoice_id}/refund"
        headers = self._get_headers()
        
        response = await self.http_client.post(
            endpoint,
            json=request.model_dump(),
            headers=headers
        )
        response.raise_for_status()
        
        return DGIRefundResponse(**response.json())
    
    async def generate_qr_code(self, token_url: str) -> str:
        """
        Génère un QR code à partir de l'URL de vérification DGI
        
        Args:
            token_url: URL complète de vérification (token)
            
        Returns:
            str: QR code encodé en base64
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def should_retry(self, http_status: int, retry_count: int) -> bool:
        """
        Détermine si une requête doit être retentée
        
        Args:
            http_status: Code HTTP de la réponse
            retry_count: Nombre de tentatives déjà effectuées
            
        Returns:
            bool: True si retry, False sinon
        """
        # Ne retry que pour les erreurs 500 (erreur serveur DGI)
        if http_status != 500:
            return False
        
        # Maximum 5 tentatives
        if retry_count >= 5:
            return False
        
        return True
    
    def get_retry_delay(self, retry_count: int) -> int:
        """
        Calcule le délai avant retry avec exponential backoff
        
        Args:
            retry_count: Numéro de la tentative (1-indexed)
            
        Returns:
            int: Délai en secondes
        """
        delays = {
            1: 0,      # Immédiat
            2: 30,     # 30 secondes
            3: 120,    # 2 minutes
            4: 600,    # 10 minutes
            5: 3600    # 1 heure
        }
        return delays.get(retry_count, 3600)
    
    def map_invoice_to_fne_request(
        self,
        invoice_data: Dict[str, Any],
        items_data: List[Dict[str, Any]]
    ) -> FNESignRequest:
        """
        Transforme une facture interne en requête FNE
        
        Args:
            invoice_data: Données de la facture interne
            items_data: Liste des articles de la facture
            
        Returns:
            FNESignRequest: Requête formatée pour l'API DGI
        """
        # Déterminer le template selon le type de client
        template = InvoiceTemplate.B2B
        if invoice_data.get("client_type") == "particulier":
            template = InvoiceTemplate.B2C
        elif invoice_data.get("client_type") == "gouvernement":
            template = InvoiceTemplate.B2G
        elif invoice_data.get("client_type") == "international":
            template = InvoiceTemplate.B2F
        
        # Mapper les articles
        fne_items = []
        for item in items_data:
            fne_item = FNEInvoiceItem(
                reference=item.get("reference", ""),
                description=item.get("description", ""),
                quantity=item.get("quantity", 0),
                amount=item.get("prix_unitaire", 0),
                discount=item.get("remise", 0),
                measurementUnit=item.get("unite", "pcs"),
                taxes=item.get("taxes", ["TVA"]),
                customTaxes=item.get("custom_taxes", [])
            )
            fne_items.append(fne_item)
        
        return FNESignRequest(
            invoiceType="sale",
            paymentMethod=map_payment_method(invoice_data.get("payment_method") or invoice_data.get("mode_paiement") or "cash"),
            template=template.value,
            clientNcc=invoice_data.get("client_ncc"),
            clientCompanyName=invoice_data.get("client_nom", ""),
            clientPhone=invoice_data.get("client_telephone", ""),
            clientEmail=invoice_data.get("client_email"),
            clientSellerName=invoice_data.get("vendeur", ""),
            pointOfSale=invoice_data.get("point_of_vente", "SIEGE FABS-CI"),
            establishment=invoice_data.get("etablissement", "EDITIONS FABS-CI"),
            items=fne_items,
            customTaxes=invoice_data.get("custom_taxes", []),
            discount=invoice_data.get("remise_globale", 0),
            commercialMessage=invoice_data.get("message_commercial"),
            footer=invoice_data.get("footer")
        )
    
    def map_refund_to_fne_request(
        self,
        refund_items: List[Dict[str, Any]]
    ) -> FNERefundRequest:
        """
        Transforme un avoir interne en requête FNE
        
        Args:
            refund_items: Liste des articles retournés avec leurs IDs DGI
            
        Returns:
            FNERefundRequest: Requête formatée pour l'API DGI
        """
        fne_items = []
        for item in refund_items:
            fne_items.append({
                "id": item["fne_item_id"],  # ID DGI de la ligne article
                "quantity": item["quantity_retournee"]
            })
        
        return FNERefundRequest(items=fne_items)


# ============================================================================
# FABRICATION
# ============================================================================

def get_fne_service() -> FNEDGIService:
    """Factory pour créer une instance du service FNE"""
    return FNEDGIService()
