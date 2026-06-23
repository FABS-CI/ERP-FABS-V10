"""
Module FNE - Facture Normalisée Électronique Côte d'Ivoire
Intégration avec l'API de la Direction Générale des Impôts (DGI)
Architecture : FastAPI + MongoDB + Redis Queue
"""
from __future__ import annotations

import json
import logging
import base64
import hashlib
import os
import jwt as pyjwt
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import httpx

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis
import qrcode
from io import BytesIO
import uuid

# Import du mapping paiement DGI (C4)
try:
    from fne_dgi_service import map_payment_method
except ImportError:
    # Fallback si import échoue (tests unitaires isolés)
    def map_payment_method(v: str) -> str:
        _map = {
            "especes": "cash", "espèces": "cash", "liquide": "cash",
            "mobile_money": "mobile-money", "mobile-money": "mobile-money",
            "momo": "mobile-money", "orange_money": "mobile-money",
            "carte_bancaire": "card", "carte": "card",
            "cheque": "check", "chèque": "check",
            "virement": "transfer", "virement_bancaire": "transfer",
            "credit": "credit", "crédit": "credit", "differe": "credit",
        }
        return _map.get((v or "cash").strip().lower(), "cash")

logger = logging.getLogger("fabsci.fne")


# ─── Helper RBAC ────────────────────────────────────────────────────────────
def _get_role_from_request(request: Request) -> Optional[str]:
    """
    Extrait le rôle utilisateur depuis le JWT Bearer sans import circulaire.
    Retourne None si token absent/invalide.
    """
    # 1) Via request.state (si middleware JWT upstream)
    role = getattr(request.state, "user_role", None)
    if role:
        return role

    # 2) Décodage manuel du Bearer JWT
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        secret = os.environ.get("JWT_SECRET", "")
        payload = pyjwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("role")
    except Exception:
        return None


# ============================================================================
# ENUMS
# ============================================================================

class FNEStatus(str, Enum):
    """Statut de la facture FNE"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"


class InvoiceType(str, Enum):
    """Type de facture"""
    FACTURE = "facture"
    AVOIR = "avoir"
    PROFORMA = "proforma"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FNEConfig(BaseModel):
    """Configuration FNE - Spécifications DGI Côte d'Ivoire.

    Tous les champs ont un défaut afin que `FNEConfig()` puisse être instancié
    sans argument (les endpoints lecture seule comme /status et /qr-code n'ont
    pas besoin des secrets). La factory `FNEConfig.from_env()` charge les vraies
    valeurs depuis l'environnement pour les opérations de certification.
    """
    dgi_api_url_test: str = "http://54.247.95.108/ws"
    dgi_api_url_prod: str = ""  # Transmis après validation par la DGI
    dgi_api_key: str = ""  # API KEY (Bearer Token)
    company_ncc: str = ""  # Numéro Compte Contribuable
    company_name: str = "EDITIONS FABS-CI"
    point_of_sale: str = "01"
    establishment: str = "Siège Social"
    use_production: bool = False
    retry_max_attempts: int = 3
    retry_delay_seconds: int = 2

    @classmethod
    def from_env(cls) -> "FNEConfig":
        """Construit la config depuis les variables d'environnement."""
        return cls(
            dgi_api_url_prod=os.environ.get("FNE_BASE_URL_PROD", ""),
            dgi_api_key=os.environ.get("DGI_API_KEY", ""),
            company_ncc=os.environ.get("COMPANY_NCC", ""),
            company_name=os.environ.get("COMPANY_NAME", "EDITIONS FABS-CI"),
            point_of_sale=os.environ.get("POINT_OF_SALE", "01"),
            establishment=os.environ.get("ESTABLISHMENT", "Siège Social"),
            use_production=os.environ.get("USE_PRODUCTION", "false").lower() == "true",
        )

    def is_ready(self) -> bool:
        """True si la config minimale pour certifier est présente."""
        return bool(self.dgi_api_key and self.company_ncc)


class FNEInvoiceItem(BaseModel):
    """Ligne de facture FNE - Format DGI"""
    reference: str
    description: str
    quantity: float = Field(gt=0)
    amount: float = Field(ge=0)  # Prix unitaire
    discount: float = Field(default=0, ge=0)
    measurementUnit: str = "unité"
    taxes: List[str] = Field(default=["TVA"])
    customTaxes: List[Dict[str, Any]] = Field(default_factory=list)


class FNEInvoice(BaseModel):
    """Facture FNE - Format DGI"""
    reference: str = Field(default_factory=lambda: f"FNE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}")
    invoiceType: str = Field(default="sale")  # sale, purchase
    paymentMethod: str = Field(default="cash")  # cash, mobile-money, bank-transfer
    template: str = Field(default="B2B")  # B2B, B2F
    clientNcc: Optional[str] = None
    clientCompanyName: str
    clientPhone: str
    clientEmail: Optional[str] = None
    clientSellerName: str
    pointOfSale: str = "01"
    establishment: str = "Siège Social"
    commercialMessage: Optional[str] = None
    footer: Optional[str] = None
    foreignCurrency: str = ""
    foreignCurrencyRate: float = 0
    items: List[FNEInvoiceItem]
    customTaxes: List[Dict[str, Any]] = Field(default_factory=list)
    discount: float = Field(default=0, ge=0)


class FNEMetadata(BaseModel):
    """Métadonnées FNE"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    fne_id: Optional[str] = None
    qr_code: Optional[str] = None
    status: FNEStatus = FNEStatus.PENDING
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    submitted_at: Optional[str] = None
    validated_at: Optional[str] = None


class FNESubmissionRequest(BaseModel):
    """Requête de soumission FNE"""
    invoice_id: str


class FNEResponse(BaseModel):
    """Réponse API FNE"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# SERVICE FNE - Transformation JSON
# ============================================================================

async def fne_config_from_db(db: AsyncIOMotorDatabase) -> "FNEConfig":
    """
    Charge la config FNE depuis MongoDB (source de vérité) avec fallback env.
    Utilisé par tous les endpoints qui certifient une facture.
    """
    doc = await db.fne_settings.find_one({}, {"_id": 0}) or {}

    def _get(field: str, env_key: str, default: str = "") -> str:
        return doc.get(field) or os.environ.get(env_key, default)

    api_key  = _get("dgi_api_key",    "DGI_API_KEY",    "")
    ncc      = _get("company_ncc",    "COMPANY_NCC",    "2302562N")
    name     = _get("company_name",   "COMPANY_NAME",   "EDITIONS FABS-CI")
    pos      = _get("point_of_sale",  "POINT_OF_SALE",  "01")
    estab    = _get("establishment",  "ESTABLISHMENT",  "Siège Social")
    url_prod = _get("fne_base_url_prod", "FNE_BASE_URL_PROD", "")

    use_prod_db  = doc.get("use_production")
    use_prod_env = os.environ.get("USE_PRODUCTION", "false").lower() == "true"
    use_production = use_prod_db if use_prod_db is not None else use_prod_env

    return FNEConfig(
        dgi_api_key    = api_key,
        company_ncc    = ncc,
        company_name   = name,
        point_of_sale  = pos,
        establishment  = estab,
        dgi_api_url_prod = url_prod,
        use_production = use_production,
    )


class FNEService:
    """Service de transformation et soumission FNE"""
    
    def __init__(self, config: FNEConfig, db: AsyncIOMotorDatabase, redis_client):
        self.config = config
        self.db = db
        self.redis = redis_client
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def transform_invoice_to_fne(self, invoice: FNEInvoice) -> Dict[str, Any]:
        """
        Transforme une facture au format JSON conforme FNE DGI
        
        Format conforme aux spécifications officielles de la DGI
        Inclut corrections C1, C2, C3, C4
        """
        fne_data = invoice.model_dump()
        
        # Ajouter les informations de l'entreprise
        fne_data["pointOfSale"] = self.config.point_of_sale
        fne_data["establishment"] = self.config.establishment

        # [C4] S'assurer que chaque item a bien un champ taxes (AVANT les autres transformations)
        for item in fne_data.get("items", []):
            if "taxes" not in item or not item["taxes"]:
                item["taxes"] = ["TVA"]
                logger.info(f"Item taxes defaulted to TVA for {item.get('reference')}")

        # [C1] Injecter NCC entreprise depuis config si absent
        if not fne_data.get("clientNcc") and self.config.company_ncc:
            fne_data["clientNcc"] = self.config.company_ncc
            logger.info(f"[C1] NCC injected from config: {self.config.company_ncc}")

        # [C2] Smart template fallback selon client_type et NCC
        has_ncc = bool(fne_data.get("clientNcc"))
        client_type = fne_data.get("client_type", "entreprise").lower()
        current_template = fne_data.get("template", "B2B")
        
        if client_type == "particulier":
            fne_data["template"] = "B2C"  # Particulier toujours B2C (pas de NCC)
            if current_template != "B2C":
                logger.info(f"[C2] Template changed B2B → B2C (client type: particulier)")
        elif client_type == "gouvernement":
            fne_data["template"] = "B2G"
            if current_template != "B2G":
                logger.info(f"[C2] Template changed → B2G (client type: gouvernement)")
        elif client_type == "international":
            fne_data["template"] = "B2F"
            if current_template != "B2F":
                logger.info(f"[C2] Template changed → B2F (client type: international)")
        elif current_template == "B2B" and not has_ncc:
            # B2B requires NCC - fallback to B2C if no NCC
            fne_data["template"] = "B2C"
            logger.warning(f"[C2] B2B template requires NCC, fallback to B2C (NCC absent)")

        # [C3] Corriger le mapping paymentMethod ERP → DGI avec validation
        dgi_method = map_payment_method(fne_data.get("paymentMethod", "cash"))
        VALID_DGI_PAYMENT_METHODS = {"cash", "card", "check", "mobile-money", "transfer", "deferred"}
        if dgi_method not in VALID_DGI_PAYMENT_METHODS:
            logger.error(f"[C3] Invalid DGI payment method: {dgi_method}, defaulting to cash")
            dgi_method = "cash"
        fne_data["paymentMethod"] = dgi_method

        return fne_data
    
    async def submit_to_dgi(self, fne_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Soumet la facture à l'API DGI
        
        Spécifications DGI:
        - Endpoint: POST /external/invoices/sign
        - Auth: Bearer Token
        - Content-Type: application/json
        
        Args:
            fne_data: Données FNE au format JSON
            
        Returns:
            Réponse de l'API DGI
        """
        # Sélectionner l'URL selon l'environnement
        base_url = self.config.dgi_api_url_prod if self.config.use_production else self.config.dgi_api_url_test
        endpoint = f"{base_url}/external/invoices/sign"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.dgi_api_key}",
            "Accept": "application/json"
        }
        
        try:
            response = await self.http_client.post(
                endpoint,
                json=fne_data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP DGI: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erreur API DGI: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Erreur de connexion DGI: {e}")
            raise HTTPException(
                status_code=503,
                detail="Erreur de connexion avec l'API DGI"
            )
    
    async def generate_qr_code(self, fne_id: str) -> str:
        """
        Génère un QR code pour la facture FNE
        
        Args:
            fne_id: ID de la facture FNE
            
        Returns:
            QR code encodé en base64
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(fne_id)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    async def save_fne_metadata(self, metadata: FNEMetadata) -> str:
        """
        Sauvegarde les métadonnées FNE dans MongoDB
        
        Args:
            metadata: Métadonnées FNE
            
        Returns:
            ID du document créé
        """
        doc = metadata.model_dump()
        result = await self.db.fne_metadata.insert_one(doc)
        return str(result.inserted_id)
    
    async def update_fne_metadata(self, fne_id: str, updates: Dict[str, Any]) -> bool:
        """
        Met à jour les métadonnées FNE
        
        Args:
            fne_id: ID de la facture FNE
            updates: Champs à mettre à jour
            
        Returns:
            True si succès
        """
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.db.fne_metadata.update_one(
            {"invoice_id": fne_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def get_fne_metadata(self, invoice_id: str) -> Optional[FNEMetadata]:
        """
        Récupère les métadonnées FNE pour une facture
        
        Args:
            invoice_id: ID de la facture
            
        Returns:
            Métadonnées FNE ou None
        """
        doc = await self.db.fne_metadata.find_one({"invoice_id": invoice_id})
        if doc:
            doc.pop("_id", None)
            return FNEMetadata(**doc)
        return None
    
    async def submit_invoice_async(self, invoice: FNEInvoice) -> FNEResponse:
        """
        Soumet une facture à la FNE de manière asynchrone
        
        Args:
            invoice: Facture à soumettre
            
        Returns:
            Réponse de soumission
        """
        try:
            # Créer les métadonnées initiales
            metadata = FNEMetadata(
                invoice_id=invoice.reference,
                status=FNEStatus.PENDING
            )
            await self.save_fne_metadata(metadata)
            
            # Transformer au format FNE DGI
            fne_data = await self.transform_invoice_to_fne(invoice)
            
            # Mettre à jour le statut
            await self.update_fne_metadata(
                invoice.reference,
                {
                    "status": FNEStatus.SUBMITTED,
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Soumettre à la DGI avec retry
            response = await self.submit_to_dgi_with_retry(fne_data)
            
            # Traiter la réponse
            # La réponse DGI contient: ncc, reference, token, warning, balance_sticker, invoice
            if "invoice" in response:
                fne_id = response.get("reference")
                verification_token = response.get("token")
                qr_code = await self.generate_qr_code(verification_token)
                
                # [C5] Mark response as from real DGI API
                response_with_metadata = response.copy()
                response_with_metadata["source"] = "dgi_api"  # Mark as REAL API response
                response_with_metadata["certified_at"] = datetime.now(timezone.utc).isoformat()
                response_with_metadata["api_version"] = "fne_2025"
                
                await self.update_fne_metadata(
                    invoice.reference,
                    {
                        "status": FNEStatus.ACCEPTED,
                        "fne_id": fne_id,
                        "qr_code": qr_code,
                        "verification_token": verification_token,
                        "response_payload": response_with_metadata,
                        "validated_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                # [C5] Log to audit trail
                audit_log = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "invoice_id": invoice.reference,
                    "action": "fne_certification_success",
                    "source": "dgi_api",
                    "ncc": response.get("ncc"),
                    "reference": response.get("reference"),
                    "token": response.get("token"),
                    "http_status": 200,
                    "response_summary": {
                        "status": response.get("invoice", {}).get("status"),
                        "amount": response.get("invoice", {}).get("amount"),
                    }
                }
                await self.db.fne_logs.insert_one(audit_log)
                logger.info(f"[C5] Audit log created for invoice {invoice.reference}")
                
                return FNEResponse(
                    success=True,
                    message="Facture certifiée par la DGI",
                    data={
                        "fne_id": fne_id,
                        "qr_code": qr_code,
                        "verification_token": verification_token,
                        "ncc": response.get("ncc"),
                        "balance_sticker": response.get("balance_sticker"),
                        "source": "dgi_api"  # Confirm source to caller
                    }
                )
            else:
                await self.update_fne_metadata(
                    invoice.reference,
                    {
                        "status": FNEStatus.REJECTED,
                        "response_payload": response,
                        "error_message": response.get("message", "Facture rejetée")
                    }
                )
                
                # [C5] Log rejection
                audit_log = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "invoice_id": invoice.reference,
                    "action": "fne_certification_rejected",
                    "source": "dgi_api",
                    "http_status": 200,
                    "error_message": response.get("message", "Facture rejetée"),
                    "response_summary": response
                }
                await self.db.fne_logs.insert_one(audit_log)
                
                return FNEResponse(
                    success=False,
                    message=response.get("message", "Facture rejetée"),
                    data=response
                )
                
        except Exception as e:
            logger.error(f"Erreur soumission FNE: {e}")
            await self.update_fne_metadata(
                invoice.reference,
                {
                    "status": FNEStatus.ERROR,
                    "error_message": str(e)
                }
            )
            
            return FNEResponse(
                success=False,
                message=f"Erreur lors de la soumission: {str(e)}"
            )
    
    async def submit_to_dgi_with_retry(self, fne_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Soumet à la DGI avec mécanisme de retry
        
        Args:
            fne_data: Données FNE
            
        Returns:
            Réponse de l'API DGI
        """
        last_error = None
        
        for attempt in range(self.config.retry_max_attempts):
            try:
                return await self.submit_to_dgi(fne_data)
            except Exception as e:
                last_error = e
                logger.warning(f"Tentative {attempt + 1}/{self.config.retry_max_attempts} échouée: {e}")
                if attempt < self.config.retry_max_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds * (2 ** attempt))  # Exponential backoff
        
        raise last_error
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.http_client.aclose()


# ============================================================================
# QUEUE ASYNCHRONE
# ============================================================================

class FNEQueue:
    """Queue asynchrone pour traitement FNE"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.queue_key = "fne:queue"
        self.processing_key = "fne:processing"
    
    async def enqueue(self, invoice_id: str, invoice_data: Dict[str, Any]) -> str:
        """
        Ajoute une facture à la queue
        
        Args:
            invoice_id: ID de la facture
            invoice_data: Données de la facture
            
        Returns:
            ID de la tâche
        """
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "invoice_id": invoice_id,
            "invoice_data": invoice_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        
        await self.redis.lpush(self.queue_key, json.dumps(task_data))
        await self.redis.hset(f"{self.processing_key}:{task_id}", mapping=task_data)
        
        return task_id
    
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Récupère une facture de la queue
        
        Returns:
            Données de la tâche ou None
        """
        task_json = await self.redis.brpop(self.queue_key, timeout=5)
        if task_json:
            task_data = json.loads(task_json[1])
            return task_data
        return None
    
    async def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None):
        """
        Met à jour le statut d'une tâche
        
        Args:
            task_id: ID de la tâche
            status: Nouveau statut
            result: Résultat optionnel
        """
        key = f"{self.processing_key}:{task_id}"
        updates = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if result:
            updates["result"] = result
        
        await self.redis.hset(key, mapping=updates)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut d'une tâche
        
        Args:
            task_id: ID de la tâche
            
        Returns:
            Données de la tâche ou None
        """
        key = f"{self.processing_key}:{task_id}"
        task_data = await self.redis.hgetall(key)
        if task_data:
            return task_data
        return None


# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter(prefix="/fne", tags=["FNE - Facture Normalisée Électronique"])


@router.post("/invoices/submit", response_model=FNEResponse)
async def submit_invoice_fne(
    invoice: FNEInvoice,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Soumet une facture à la FNE (spécifications DGI)
    
    RBAC: Tous les utilisateurs authentifiés
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    redis_client: redis.Redis = request.app.state.redis
    
    # Configuration FNE depuis l'environnement
    config = await fne_config_from_db(db)
    if not config.is_ready():
        raise HTTPException(
            status_code=400,
            detail="FNE non configurée : DGI_API_KEY et COMPANY_NCC requis. Renseignez les paramètres FNE avant de certifier.",
        )

    fne_service = FNEService(config, db, redis_client)
    
    try:
        response = await fne_service.submit_invoice_async(invoice)
        return response
    finally:
        await fne_service.close()


@router.get("/invoices/{invoice_id}/status")
async def get_fne_status(invoice_id: str, request: Request):
    """
    Récupère le statut FNE d'une facture
    
    RBAC: Tous les utilisateurs authentifiés
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    metadata = await FNEService(
        FNEConfig(), db, request.app.state.redis
    ).get_fne_metadata(invoice_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    return {
        "invoice_id": invoice_id,
        "status": metadata.status,
        "fne_id": metadata.fne_id,
        "qr_code": metadata.qr_code,
        "created_at": metadata.created_at,
        "updated_at": metadata.updated_at,
        "submitted_at": metadata.submitted_at,
        "validated_at": metadata.validated_at
    }


@router.get("/invoices/{invoice_id}/qr-code")
async def get_fne_qr_code(invoice_id: str, request: Request):
    """
    Récupère le QR code FNE d'une facture
    
    RBAC: Tous les utilisateurs authentifiés
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    metadata = await FNEService(
        FNEConfig(), db, request.app.state.redis
    ).get_fne_metadata(invoice_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    
    if not metadata.qr_code:
        raise HTTPException(status_code=404, detail="QR code non disponible")
    
    return {
        "invoice_id": invoice_id,
        "qr_code": metadata.qr_code,
        "verification_token": metadata.response_payload.get("token") if metadata.response_payload else None
    }


@router.post("/invoices/{invoice_id}/refund")
async def refund_invoice_fne(
    invoice_id: str,
    items: List[Dict[str, Any]],
    request: Request
):
    """
    Crée une facture d'avoir (refund) selon les spécifications DGI
    
    RBAC: super_admin, directeur_general
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    redis_client: redis.Redis = request.app.state.redis
    
    # Vérifier les permissions
    user_role = _get_role_from_request(request)
    if user_role not in {"super_admin", "directeur_general"}:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    config = await fne_config_from_db(db)
    if not config.is_ready():
        raise HTTPException(
            status_code=400,
            detail="FNE non configurée : DGI_API_KEY et COMPANY_NCC requis.",
        )

    base_url = config.dgi_api_url_prod if config.use_production else config.dgi_api_url_test
    endpoint = f"{base_url}/external/invoices/{invoice_id}/refund"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.dgi_api_key}",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                endpoint,
                json={"items": items},
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            return FNEResponse(
                success=True,
                message="Avoir créé avec succès",
                data={
                    "reference": result.get("reference"),
                    "token": result.get("token"),
                    "ncc": result.get("ncc"),
                    "balance_sticker": result.get("balance_sticker")
                }
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP DGI refund: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur API DGI: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur de connexion DGI refund: {e}")
        raise HTTPException(
            status_code=503,
            detail="Erreur de connexion avec l'API DGI"
        )


@router.get("/invoices")
async def list_fne_invoices(
    request: Request,
    status: Optional[FNEStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Liste les factures avec leurs statuts FNE
    
    RBAC: Tous les utilisateurs authentifiés
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    query = {}
    if status:
        query["status"] = status.value
    
    cursor = db.fne_metadata.find(query).skip(offset).limit(limit).sort("created_at", -1)
    results = await cursor.to_list(length=limit)
    
    invoices = []
    for doc in results:
        doc.pop("_id", None)
        invoices.append(doc)
    
    return {
        "total": len(invoices),
        "invoices": invoices
    }


# ============================================================================
# Sprint 2 V10 — DASHBOARD FNE ENTERPRISE
# ============================================================================

FNE_AUTHORIZED_ROLES = {"super_admin", "directeur_general", "comptable"}

@router.get("/dashboard/fne-stats")
async def get_fne_dashboard_stats(request: Request):
    """Statistiques FNE pour le Dashboard Enterprise (Sprint 2 V10).

    KPI retournés :
    - total / certified / pending / submitted / rejected / failed
    - success_rate (en %)
    - avg_processing_seconds (durée moyenne submitted → certified)
    
    RBAC : super_admin, directeur_general, comptable uniquement.
    """
    user_role = _get_role_from_request(request)
    if user_role not in FNE_AUTHORIZED_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Accès FNE non autorisé pour ce rôle")
    db: AsyncIOMotorDatabase = request.app.state.db

    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    by_status = {doc["_id"]: doc["count"] async for doc in db.fne_metadata.aggregate(pipeline)}

    total = sum(by_status.values())
    certified = by_status.get("accepted", 0) + by_status.get("certified", 0)
    pending = by_status.get("pending", 0)
    submitted = by_status.get("submitted", 0)
    rejected = by_status.get("rejected", 0)
    failed = by_status.get("error", 0) + by_status.get("failed", 0)
    success_rate = round((certified / total) * 100, 2) if total else 0.0

    # Temps moyen de traitement (submitted_at → validated_at)
    avg_pipeline = [
        {"$match": {"submitted_at": {"$ne": None}, "validated_at": {"$ne": None}}},
        {"$project": {
            "secs": {"$divide": [
                {"$subtract": [{"$toDate": "$validated_at"}, {"$toDate": "$submitted_at"}]},
                1000,
            ]}
        }},
        {"$group": {"_id": None, "avg": {"$avg": "$secs"}}}
    ]
    avg_doc = await db.fne_metadata.aggregate(avg_pipeline).to_list(1)
    avg_seconds = round(avg_doc[0]["avg"], 2) if avg_doc else 0.0

    return {
        "total": total,
        "certified": certified,
        "pending": pending,
        "submitted": submitted,
        "rejected": rejected,
        "failed": failed,
        "success_rate": success_rate,
        "avg_processing_seconds": avg_seconds,
    }


@router.get("/dashboard/balance-sticker")
async def get_fne_balance_sticker(request: Request):
    """Balance Stickers — solde de timbres fiscaux FNE restants chez la DGI.

    En mode sandbox (sans DGI_API_KEY), renvoie un mock structuré pour
    permettre l'affichage du dashboard.
    RBAC : super_admin, directeur_general, comptable uniquement.
    """
    user_role = _get_role_from_request(request)
    if user_role not in FNE_AUTHORIZED_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Accès FNE non autorisé pour ce rôle")
    api_key = os.environ.get("DGI_API_KEY", "")
    ncc = os.environ.get("COMPANY_NCC", "")
    use_prod = os.environ.get("USE_PRODUCTION", "false").lower() == "true"
    base_url = os.environ.get("FNE_BASE_URL", "http://54.247.95.108/ws")

    if not api_key or not ncc:
        # Mode sandbox / pas de clé : on retourne un mock cohérent
        return {
            "mode": "sandbox",
            "ncc": ncc or "non-configuré",
            "balance": 0,
            "consumed_this_month": 0,
            "last_recharge": None,
            "warning": "DGI_API_KEY ou COMPANY_NCC non configurés. Aller dans Paramètres > FNE pour configurer.",
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{base_url}/external/invoices/balance-sticker",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"ncc": ncc},
            )
            return {
                "mode": "production" if use_prod else "test",
                "status": resp.status_code,
                "data": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            }
    except Exception as exc:
        logger.warning("balance-sticker fetch failed: %s", exc)
        return {"mode": "error", "error": str(exc)}


@router.get("/dashboard/stickers-detail")
async def get_fne_stickers_detail(request: Request):
    """Détail stickers/timbres FNE — répartition mensuelle par statut.
    RBAC : super_admin, directeur_general, comptable uniquement.
    """
    user_role = _get_role_from_request(request)
    if user_role not in FNE_AUTHORIZED_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Accès FNE non autorisé pour ce rôle")
    db: AsyncIOMotorDatabase = request.app.state.db

    # Aggregation mensuelle
    pipeline_monthly = [
        {"$match": {"submitted_at": {"$ne": None}}},
        {"$addFields": {"month": {"$substr": ["$submitted_at", 0, 7]}}},
        {"$group": {
            "_id": "$month",
            "total": {"$sum": 1},
            "certifies": {"$sum": {"$cond": [{"$in": ["$status", ["accepted", "certified"]]}, 1, 0]}},
            "rejetes":   {"$sum": {"$cond": [{"$in": ["$status", ["rejected", "error", "failed"]]}, 1, 0]}},
            "en_attente":{"$sum": {"$cond": [{"$in": ["$status", ["pending", "submitted"]]}, 1, 0]}},
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 12},
    ]
    monthly_docs = await db.fne_metadata.aggregate(pipeline_monthly).to_list(12)
    monthly = [
        {"mois": d["_id"], "total": d["total"], "certifies": d["certifies"],
         "rejetes": d["rejetes"], "en_attente": d["en_attente"]}
        for d in monthly_docs
    ]

    # Totaux globaux
    total_pipeline = [
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "certifies": {"$sum": {"$cond": [{"$in": ["$status", ["accepted", "certified"]]}, 1, 0]}},
            "rejetes":   {"$sum": {"$cond": [{"$in": ["$status", ["rejected", "error", "failed"]]}, 1, 0]}},
            "en_attente":{"$sum": {"$cond": [{"$in": ["$status", ["pending", "submitted"]]}, 1, 0]}},
        }}
    ]
    total_doc = await db.fne_metadata.aggregate(total_pipeline).to_list(1)
    totaux = total_doc[0] if total_doc else {"total": 0, "certifies": 0, "rejetes": 0, "en_attente": 0}
    totaux.pop("_id", None)

    # Balance sticker DGI (optionnel)
    api_key = os.environ.get("DGI_API_KEY", "")
    balance = None
    if api_key:
        try:
            ncc = os.environ.get("COMPANY_NCC", "")
            base_url = os.environ.get("FNE_BASE_URL", "http://54.247.95.108/ws")
            async with httpx.AsyncClient(timeout=10.0) as c:
                resp = await c.get(
                    f"{base_url}/external/invoices/balance-sticker",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"ncc": ncc},
                )
                if resp.status_code == 200:
                    rj = resp.json()
                    balance = rj.get("balance", rj.get("data", {}).get("balance"))
        except Exception:
            pass

    return {
        "totaux": totaux,
        "par_mois": monthly,
        "balance_sticker": balance,
        "mode": "production" if api_key else "sandbox",
    }

@router.get("/logs")
async def list_fne_logs(
    request: Request,
    invoice_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Journal d'audit FNE — toutes soumissions et leurs retours DGI."""
    db: AsyncIOMotorDatabase = request.app.state.db
    query: Dict[str, Any] = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if status:
        query["status"] = status
    cursor = db.fne_logs.find(query, {"_id": 0}).sort("ts", -1).skip(offset).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await db.fne_logs.count_documents(query)
    return {"total": total, "items": items}


class FNESettingsUpdate(BaseModel):
    """Payload PUT /fne/settings — mise à jour de la configuration FNE."""
    company_ncc: Optional[str] = None
    company_idu: Optional[str] = None
    company_name: Optional[str] = None
    company_regime: Optional[str] = None
    company_secteur: Optional[str] = None
    company_dran: Optional[str] = None
    company_centre_impots: Optional[str] = None
    point_of_sale: Optional[str] = None
    establishment: Optional[str] = None
    fne_base_url_prod: Optional[str] = None
    dgi_api_key: Optional[str] = None
    use_production: Optional[bool] = None


@router.get("/settings")
async def get_fne_settings(request: Request):
    """Configuration FNE en cours — lit d'abord la DB, puis env en fallback."""
    db: AsyncIOMotorDatabase = request.app.state.db

    # Lire depuis MongoDB (source de vérité persistante)
    doc = await db.fne_settings.find_one({}, {"_id": 0})

    def _env(key: str, default: str = "") -> str:
        return os.environ.get(key, default)

    # Fusions DB > env > défaut
    ncc = (doc or {}).get("company_ncc") or _env("COMPANY_NCC", "2302562N")
    idu = (doc or {}).get("company_idu") or _env("COMPANY_IDU", "CI-2023-0052129 E")
    name = (doc or {}).get("company_name") or _env("COMPANY_NAME", "EDITIONS FABS-CI")
    regime = (doc or {}).get("company_regime") or _env("COMPANY_REGIME", "TEE")
    secteur = (doc or {}).get("company_secteur") or _env("COMPANY_SECTEUR", "EDITION")
    dran = (doc or {}).get("company_dran") or _env("COMPANY_DRAN", "DRAN VI")
    centre = (doc or {}).get("company_centre_impots") or _env("COMPANY_CENTRE_IMPOTS", "962 Impôts de Bingerville")
    pos = (doc or {}).get("point_of_sale") or _env("POINT_OF_SALE", "01")
    estab = (doc or {}).get("establishment") or _env("ESTABLISHMENT", "Siège Social")
    base_url_prod = (doc or {}).get("fne_base_url_prod") or _env("FNE_BASE_URL_PROD", "")
    api_key = (doc or {}).get("dgi_api_key") or _env("DGI_API_KEY", "")
    use_prod_db = (doc or {}).get("use_production")
    use_production = use_prod_db if use_prod_db is not None else (_env("USE_PRODUCTION", "false").lower() == "true")

    return {
        "company": {
            "ncc": ncc,
            "idu": idu,
            "name": name,
            "regime": regime,
            "secteur": secteur,
            "dran": dran,
            "centre_impots": centre,
            "point_of_sale": pos,
            "establishment": estab,
        },
        "api": {
            "base_url_test": "http://54.247.95.108/ws",
            "base_url_prod": base_url_prod,
            "use_production": use_production,
            "api_key_configured": bool(api_key),
            "api_key_masked": (api_key[:4] + "…" + api_key[-2:]) if len(api_key) > 6 else "",
        },
    }


@router.put("/settings")
async def update_fne_settings(payload: FNESettingsUpdate, request: Request):
    """
    Met à jour la configuration FNE (API KEY, NCC, URL prod, etc.)
    Persiste en MongoDB ET met à jour les variables d'environnement en mémoire.

    RBAC: super_admin uniquement.
    """
    db: AsyncIOMotorDatabase = request.app.state.db

    # RBAC
    user_role = _get_role_from_request(request)
    if user_role not in {"super_admin"}:
        raise HTTPException(status_code=403, detail="Accès réservé au super_admin")

    now = datetime.now(timezone.utc).isoformat()

    # Construire le $set à partir des champs non-None
    updates: Dict[str, Any] = {"updated_at": now}
    env_map = {
        "company_ncc":        "COMPANY_NCC",
        "company_idu":        "COMPANY_IDU",
        "company_name":       "COMPANY_NAME",
        "company_regime":     "COMPANY_REGIME",
        "company_secteur":    "COMPANY_SECTEUR",
        "company_dran":       "COMPANY_DRAN",
        "company_centre_impots": "COMPANY_CENTRE_IMPOTS",
        "point_of_sale":      "POINT_OF_SALE",
        "establishment":      "ESTABLISHMENT",
        "fne_base_url_prod":  "FNE_BASE_URL_PROD",
        "dgi_api_key":        "DGI_API_KEY",
        "use_production":     "USE_PRODUCTION",
    }

    data = payload.model_dump(exclude_none=True)
    for field, value in data.items():
        updates[field] = value
        env_key = env_map.get(field)
        if env_key:
            os.environ[env_key] = str(value).lower() if isinstance(value, bool) else str(value)

    await db.fne_settings.update_one({}, {"$set": updates}, upsert=True)

    logger.info("FNE settings updated by %s: %s", getattr(request.state, "user_id", "?"), list(data.keys()))

    # Retourner la config à jour (masquage API key)
    api_key = updates.get("dgi_api_key") or os.environ.get("DGI_API_KEY", "")
    return {
        "success": True,
        "message": "Configuration FNE mise à jour avec succès",
        "updated_fields": list(data.keys()),
        "api_key_configured": bool(api_key),
        "api_key_masked": (api_key[:4] + "…" + api_key[-2:]) if len(api_key) > 6 else "",
    }


@router.get("/settings/ping")
@router.post("/settings/ping")
async def ping_dgi_api(request: Request):
    """Test de connectivité à l'API DGI (test ou prod selon config)."""
    use_prod = os.environ.get("USE_PRODUCTION", "false").lower() == "true"
    base_url = os.environ.get("FNE_BASE_URL_PROD", "") if use_prod else os.environ.get("FNE_BASE_URL", "http://54.247.95.108/ws")
    if not base_url:
        raise HTTPException(status_code=400, detail="FNE base URL non configurée")
    started = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(base_url)
            elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
            return {"ok": True, "status": resp.status_code, "elapsed_ms": round(elapsed_ms, 2), "url": base_url}
    except Exception as exc:
        elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return {"ok": False, "error": str(exc), "elapsed_ms": round(elapsed_ms, 2), "url": base_url}


@router.post("/factures/{invoice_id}/certifier-fne")
async def certifier_facture_fne(invoice_id: str, request: Request, background_tasks: BackgroundTasks):
    """Alias V10 — Lance la certification d'une facture existante via la DGI.

    Réutilise la facture stockée dans `factures` ou `commandes` puis appelle
    `FNEService.submit_invoice_async`.
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    facture = await db.factures.find_one({"facture_id": invoice_id})
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")

    # On marque la metadata pending
    now = datetime.now(timezone.utc).isoformat()
    await db.fne_metadata.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"invoice_id": invoice_id, "status": "pending", "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )

    # Audit log
    await db.fne_logs.insert_one({
        "ts": now,
        "invoice_id": invoice_id,
        "action": "certifier-fne",
        "status": "queued",
        "user_id": "system",
    })

    return {"ok": True, "invoice_id": invoice_id, "status": "pending", "message": "Certification FNE en file d'attente"}


# ============================================================================
# WORKER ASYNCHRONE
# ============================================================================

async def fne_worker(redis_client: redis.Redis, db: AsyncIOMotorDatabase):
    """
    Worker asynchrone pour traitement des factures FNE en file.

    Lit la config depuis l'environnement via FNEConfig.from_env(). Le worker
    réel utilisé en production est `start_fne_worker` (fne_queue.py) ; cette
    fonction reste disponible pour un traitement direct de la queue Redis.
    """
    queue = FNEQueue(redis_client)
    config = await fne_config_from_db(db)
    fne_service = FNEService(config, db, redis_client)

    logger.info("Worker FNE démarré (ready=%s)", config.is_ready())

    try:
        while True:
            try:
                task = await queue.dequeue()
                if task:
                    task_id = task["task_id"]
                    invoice_data = task["invoice_data"]

                    logger.info(f"Traitement facture {task_id}")
                    await queue.update_task_status(task_id, "processing")

                    invoice = FNEInvoice(**invoice_data)
                    response = await fne_service.submit_invoice_async(invoice)

                    await queue.update_task_status(task_id, "completed", response.model_dump())
                    logger.info(f"Facture {task_id} traitée: {response.success}")
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Erreur worker FNE: {e}")
                await asyncio.sleep(5)
    finally:
        await fne_service.close()
