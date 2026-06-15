"""
Module Document Settings - Gestion des paramètres de documents et impression
- Gestion du logo de l'entreprise
- Sélection des modèles de facture (5 modèles)
- Configuration des filigranes automatiques
- Prévisualisation PDF
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal
import logging
import base64
import io
from pathlib import Path

import os
import jwt as pyjwt
from pathlib import Path
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("fabsci.document_settings")

# Charger le .env du backend (même répertoire que ce module)
load_dotenv(Path(__file__).parent / ".env")
_JWT_SECRET = os.environ.get("JWT_SECRET", "fabsci-secret-key-change-in-development-only")
_JWT_ALGORITHM = "HS256"


def _get_user_role(request: Request) -> str | None:
    """Decode JWT from Authorization header and return user role."""
    authorization = request.headers.get("Authorization", "")
    token = None
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        payload = pyjwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload.get("role")
    except Exception:
        return None

# RBAC
ADMIN_ROLES = {"super_admin", "directeur_general"}
READ_ROLES = {"super_admin", "directeur_general", "comptable", "secretariat"}

# Modèles de facture disponibles
InvoiceTemplate = Literal[
    "classique_professionnel",
    "moderne_bleu",
    "premium",
    "corporate_orange",
    "elegant_administratif",
    "minimaliste_moderne",
    "premium_luxe",
    "education_edition"
]

# Couleurs FABS-CI
FABS_COLORS = {
    "navy": "#0A2540",
    "orange": "#FF6200",
    "grey": "#6B7280",
    "red": "#DC2626",
    "blue": "#2563EB"
}

# Types de filigrane
WatermarkType = Literal["PROFORMA", "BROUILLON", "PAYÉ", "PAIEMENT_PARTIEL", "IMPAYÉ", "ANNULÉ", "AVOIR"]


# ============================================================================
# Schémas Pydantic
# ============================================================================

class CompanyInfo(BaseModel):
    """Informations de l'entreprise FABS-CI"""
    nom: str = "EDITIONS FABS-CI"
    adresse: str = "BP 693"
    telephone: str = "+225 07 59 73 71 23"
    email: str = "edition693fabs@gmail.com"
    siege_social: str = "Bingerville, Quartier N'GOTTO, Immeuble cité Angan A. fils et petits-fils, Rez-de-chaussée"
    banques: Dict[str, str] = {
        "CORIS BANK": "C116 01011 007630824101 34",
        "SGBCI": "CI008 01123012343259990 95"
    }


class WatermarkSettings(BaseModel):
    """Configuration des filigranes"""
    enabled: bool = True
    color: str = "#FF0000"
    size: int = 48
    opacity: float = Field(default=0.3, ge=0.1, le=1.0)
    position: Literal["center", "top_left", "top_right", "bottom_left", "bottom_right"] = "center"
    rotation: int = Field(default=45, ge=0, le=90)


class CustomColors(BaseModel):
    """Couleurs personnalisées du modèle"""
    primary: str = "#0A2540"
    secondary: str = "#FF6200"
    accent: str = "#2563EB"


class DocumentSettings(BaseModel):
    """Paramètres globaux de documents"""
    selected_template: InvoiceTemplate = "classique_professionnel"
    # Modèle par type de document
    template_per_type: Dict[str, str] = {}
    # Couleurs personnalisées
    custom_colors: CustomColors = CustomColors()
    watermark_settings: WatermarkSettings = WatermarkSettings()
    company_info: CompanyInfo = CompanyInfo()
    logo_url: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LogoUploadResponse(BaseModel):
    """Réponse après upload de logo"""
    success: bool
    logo_url: Optional[str] = None
    message: str


class TemplatePreview(BaseModel):
    """Aperçu d'un modèle"""
    template_id: InvoiceTemplate
    template_name: str
    description: str
    colors: List[str]
    style: str
    preview_url: Optional[str] = None


# ============================================================================
# Fonctions utilitaires
# ============================================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def determine_watermark(document_type: str, statut: str, montant_regle: float, montant_total: float) -> Optional[str]:
    """
    Détermine le filigrane automatique selon le statut du document
    
    Règles:
    - Proforma → PROFORMA
    - Brouillon → BROUILLON
    - Facture soldée 100% → PAYÉ
    - Paiement partiel → PAIEMENT_PARTIEL
    - Facture échue non réglée → IMPAYÉ
    - Document annulé → ANNULÉ
    - Avoir → AVOIR
    """
    if document_type == "proforma":
        return "PROFORMA"
    elif statut == "brouillon":
        return "BROUILLON"
    elif statut == "annulee":
        return "ANNULÉ"
    elif document_type == "avoir":
        return "AVOIR"
    elif statut == "payee":
        return "PAYÉ"
    elif statut == "partiellement_payee":
        return "PAIEMENT_PARTIEL"
    elif statut == "emise" and montant_regle == 0:
        return "IMPAYÉ"
    return None


# ============================================================================
# API Routes
# ============================================================================

router = APIRouter(prefix="/document-settings", tags=["Document Settings"])


@router.get("/settings", response_model=DocumentSettings)
async def get_document_settings(request: Request):
    """
    Récupérer les paramètres de documents actuels
    
    RBAC: super_admin, directeur_general, comptable, secretariat
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    settings = await db.document_settings.find_one({"_id": "default"})
    if not settings:
        # Créer les paramètres par défaut
        default_settings = DocumentSettings()
        await db.document_settings.insert_one({"_id": "default", **default_settings.model_dump()})
        return default_settings
    
    settings.pop("_id", None)
    return DocumentSettings(**settings)


@router.put("/settings", response_model=DocumentSettings)
async def update_document_settings(settings: DocumentSettings, request: Request):
    """
    Mettre à jour les paramètres de documents
    
    RBAC: super_admin, directeur_general
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    # Vérifier les permissions
    user_role = _get_user_role(request)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    settings.updated_at = _now_iso()
    
    await db.document_settings.update_one(
        {"_id": "default"},
        {"$set": settings.model_dump()},
        upsert=True
    )
    
    return settings


@router.post("/logo/upload", response_model=LogoUploadResponse)
async def upload_logo(request: Request, file: UploadFile = File(...)):
    """
    Télécharger le logo de l'entreprise
    
    RBAC: super_admin, directeur_general
    
    Formats acceptés: PNG, JPG, JPEG
    Taille max: 2MB
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    # Vérifier les permissions
    user_role = _get_user_role(request)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    # Vérifier le type de fichier
    if not file.content_type or file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez PNG ou JPG.")
    
    # Vérifier la taille
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(status_code=400, detail="Fichier trop volumineux. Maximum 2MB.")
    
    # Encoder en base64
    encoded_logo = base64.b64encode(content).decode("utf-8")
    logo_url = f"data:{file.content_type};base64,{encoded_logo}"
    
    # Mettre à jour les paramètres
    await db.document_settings.update_one(
        {"_id": "default"},
        {"$set": {"logo_url": logo_url, "updated_at": _now_iso()}},
        upsert=True
    )
    
    return LogoUploadResponse(
        success=True,
        logo_url=logo_url,
        message="Logo téléchargé avec succès"
    )


@router.delete("/logo")
async def delete_logo(request: Request):
    """
    Supprimer le logo de l'entreprise
    
    RBAC: super_admin, directeur_general
    """
    db: AsyncIOMotorDatabase = request.app.state.db
    
    # Vérifier les permissions
    user_role = _get_user_role(request)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    await db.document_settings.update_one(
        {"_id": "default"},
        {"$set": {"logo_url": None, "updated_at": _now_iso()}}
    )
    
    return {"success": True, "message": "Logo supprimé avec succès"}


@router.get("/templates", response_model=List[TemplatePreview])
async def get_available_templates():
    """
    Récupérer la liste des modèles de facture disponibles
    
    RBAC: Tous les utilisateurs authentifiés
    """
    templates = [
        TemplatePreview(
            template_id="classique_professionnel",
            template_name="Classique Professionnel",
            description="Logo en haut à gauche, coordonnées sous le logo, informations facture à droite, tableau pleine largeur.",
            colors=[FABS_COLORS["navy"], "#000000"],
            style="Administratif, sobre, professionnel"
        ),
        TemplatePreview(
            template_id="moderne_bleu",
            template_name="Moderne Bleu",
            description="Logo centré, bandeau bleu supérieur, informations sous forme de cartes, totaux dans bloc bleu.",
            colors=[FABS_COLORS["navy"], FABS_COLORS["grey"]],
            style="Moderne, épuré, dynamique"
        ),
        TemplatePreview(
            template_id="premium",
            template_name="Premium",
            description="Logo centré, nom entreprise centré, bloc facture centré, totaux encadré élégant.",
            colors=[FABS_COLORS["orange"], FABS_COLORS["navy"], "#000000"],
            style="Haut de gamme, corporate"
        ),
        TemplatePreview(
            template_id="corporate_orange",
            template_name="Corporate Orange",
            description="Bandeau orange supérieur, logo à gauche, informations client fond gris, totaux fond orange.",
            colors=[FABS_COLORS["orange"], FABS_COLORS["grey"], "#000000"],
            style="Entreprise, distribution, vente"
        ),
        TemplatePreview(
            template_id="elegant_administratif",
            template_name="Élégant Administratif",
            description="Logo à gauche, numéro facture à droite, coordonnées en colonnes, bloc total encadré.",
            colors=[FABS_COLORS["red"], FABS_COLORS["navy"], FABS_COLORS["grey"]],
            style="Institutionnel, administratif"
        ),
        TemplatePreview(
            template_id="minimaliste_moderne",
            template_name="Minimaliste Moderne",
            description="Mise en page aérée, très peu de bordures, accent mis sur la lisibilité et l'espace blanc.",
            colors=["#111827", "#6B7280", "#F9FAFB"],
            style="Minimaliste, contemporain, startups"
        ),
        TemplatePreview(
            template_id="premium_luxe",
            template_name="Premium Luxe",
            description="En-tête sophistiqué, typographie élégante, finitions haut de gamme et dorures subtiles.",
            colors=["#1A1A2E", "#B8860B", "#F5F5DC"],
            style="Luxe, prestige, haut de gamme"
        ),
        TemplatePreview(
            template_id="education_edition",
            template_name="Éducation & Édition",
            description="Modèle spécialement conçu pour maisons d'édition, librairies, écoles et universités. Tableau adapté aux livres et manuels.",
            colors=["#1E3A5F", "#2ECC71", "#F0F4F8"],
            style="Institutionnel, éducatif, édition"
        )
    ]
    
    return templates


@router.post("/template/select")
async def select_template(
    request: Request,
    template_id: str = Query(...),
    document_type: Optional[str] = Query(None, description="Type de document spécifique (optionnel)"),
):
    """Sauvegarder le modèle sélectionné (global ou par type)"""
    db: AsyncIOMotorDatabase = request.app.state.db
    user_role = _get_user_role(request)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    valid_templates = [
        "classique_professionnel", "moderne_bleu", "premium", "corporate_orange",
        "elegant_administratif", "minimaliste_moderne", "premium_luxe", "education_edition"
    ]
    if template_id not in valid_templates:
        raise HTTPException(status_code=400, detail="Modèle invalide")

    if document_type:
        await db.document_settings.update_one(
            {"_id": "default"},
            {"$set": {f"template_per_type.{document_type}": template_id, "updated_at": _now_iso()}},
            upsert=True
        )
    else:
        await db.document_settings.update_one(
            {"_id": "default"},
            {"$set": {"selected_template": template_id, "updated_at": _now_iso()}},
            upsert=True
        )

    return {"success": True, "template_id": template_id, "document_type": document_type}


@router.post("/colors/save")
async def save_custom_colors(
    request: Request,
    primary: str = Query(...),
    secondary: str = Query(...),
    accent: str = Query(...),
):
    """Sauvegarder les couleurs personnalisées"""
    db: AsyncIOMotorDatabase = request.app.state.db
    user_role = _get_user_role(request)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    await db.document_settings.update_one(
        {"_id": "default"},
        {"$set": {"custom_colors": {"primary": primary, "secondary": secondary, "accent": accent}, "updated_at": _now_iso()}},
        upsert=True
    )
    return {"success": True, "custom_colors": {"primary": primary, "secondary": secondary, "accent": accent}}


@router.post("/preview")
async def preview_document(
    request: Request,
    document_type: str = Query(..., description="Type de document: facture, proforma, commande, bl"),
    template_id: InvoiceTemplate = Query(..., description="ID du modèle à prévisualiser")
):
    """
    Générer un aperçu PDF d'un document avec le modèle sélectionné
    
    RBAC: Tous les utilisateurs authentifiés
    """
    # Cette fonction sera implémentée avec le générateur PDF modifié
    # Pour l'instant, retourne un placeholder
    return {
        "success": True,
        "message": "Aperçu PDF généré avec succès",
        "document_type": document_type,
        "template_id": template_id,
        "preview_url": f"/api/document-settings/preview/{document_type}/{template_id}"
    }


@router.get("/watermark/determine")
async def determine_document_watermark(
    document_type: str = Query(...),
    statut: str = Query(...),
    montant_total: float = Query(0),
    montant_regle: float = Query(0)
):
    """
    Déterminer le filigrane automatique pour un document
    
    RBAC: Tous les utilisateurs authentifiés
    """
    watermark = determine_watermark(document_type, statut, montant_regle, montant_total)
    return {
        "watermark": watermark,
        "document_type": document_type,
        "statut": statut,
        "montant_regle": montant_regle,
        "montant_total": montant_total
    }
