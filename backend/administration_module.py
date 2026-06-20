"""
Module Utilisateurs & Paramètres — Sprint 13
- CRUD utilisateurs complet (super_admin uniquement)
- Gestion rôles et permissions
- Paramètres système (entreprise, banques, TVA, etc.)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
import logging
import uuid

from fastapi import APIRouter, HTTPException, Header, Query, Request, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Any

logger = logging.getLogger("fabsci.administration")

ADMIN_ROLES = {"super_admin"}
# PRD : seul le super_admin a accès au module Utilisateurs (le DG en est exclu)
READ_ROLES = {"super_admin"}
# PRD : seul super_admin accède aux Paramètres (matrice frontend)
PARAMETRES_READ_ROLES = {"super_admin"}

ROLES_DISPONIBLES = [
    "super_admin",
    "directeur_general",
    "comptable",
    "directeur_commercial",
    "gestionnaire_stock",
    "responsable_magasinier",
    "secretariat",
    "service_logistique",
    "assistante",
]


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# UTILISATEURS
# ---------------------------------------------------------------------------
class UtilisateurUpdate(BaseModel):
    nom_complet: Optional[str] = None
    role: Optional[str] = None
    actif: Optional[bool] = None


class UtilisateurIn(BaseModel):
    """Schema for creating a new user (admin only)"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 caractères")
    nom_complet: str = Field(..., min_length=2, max_length=120)
    role: str = Field(..., description="Un des rôles disponibles")
    actif: bool = True


class UtilisateurOut(BaseModel):
    user_id: str
    email: EmailStr
    nom_complet: str
    role: str
    actif: bool
    picture: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator("updated_at", "created_at", pre=True, always=True)
    def coerce_datetime_to_str(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


def build_utilisateurs_router(db: AsyncIOMotorDatabase, resolve_user, hash_password=None, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])

    @router.get("", response_model=List[UtilisateurOut])
    async def list_utilisateurs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        actif: Optional[bool] = None,
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if actif is not None:
            filters["actif"] = actif

        cursor = db.users.find(filters, {"_id": 0}).sort("created_at", -1)
        docs = await cursor.to_list(200)
        
        return [UtilisateurOut(**d) for d in docs]

    @router.post("", response_model=UtilisateurOut, status_code=201)
    async def create_utilisateur(
        request: Request,
        payload: UtilisateurIn = Body(...),
        authorization: Optional[str] = Header(default=None),
    ):
        """Create a new user (super_admin only). Email must be unique."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] == "super_admin", 403, "Réservé au super_admin")

        if payload.role not in ROLES_DISPONIBLES:
            _ensure(False, 400, f"Rôle invalide. Valeurs autorisées: {ROLES_DISPONIBLES}")

        existing = await db.users.find_one({"email": payload.email.lower()})
        _ensure(existing is None, 409, "Email déjà utilisé")

        if not hash_password:
            raise HTTPException(status_code=500, detail="Hash password function not available")

        now = _now_iso()
        user_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": payload.email.lower(),
            "nom_complet": payload.nom_complet.strip(),
            "role": payload.role,
            "actif": payload.actif,
            "password_hash": hash_password(payload.password),
            "picture": None,
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(user_doc)
        
        # Log user creation
        if log_audit_event:
            await log_audit_event(
                user_id=me['user_id'],
                action="CREATE_USER",
                resource_type="user",
                resource_id=user_doc['user_id'],
                details={
                    "target_email": payload.email,
                    "target_role": payload.role,
                    "created_by": me['email']
                },
                ip_address=request.client.host if request.client else None,
                user_email=me['email']
            )
        
        logger.info("✅ User %s created by %s", payload.email, me["email"])
        return UtilisateurOut(**{k: v for k, v in user_doc.items() if k != "password_hash"})

    @router.get("/{user_id}", response_model=UtilisateurOut)
    async def get_utilisateur(
        user_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        _ensure(user is not None, 404, "Utilisateur introuvable")
        
        return UtilisateurOut(**user)

    @router.patch("/{user_id}", response_model=UtilisateurOut)
    async def update_utilisateur(
        user_id: str,
        payload: UtilisateurUpdate,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in ADMIN_ROLES, 403, "Accès refusé - super_admin requis")

        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        _ensure(user is not None, 404, "Utilisateur introuvable")

        updates = {"updated_at": _now_iso()}
        
        if payload.nom_complet is not None:
            updates["nom_complet"] = payload.nom_complet
        
        if payload.role is not None:
            _ensure(payload.role in ROLES_DISPONIBLES, 400, f"Rôle invalide. Valeurs: {ROLES_DISPONIBLES}")
            updates["role"] = payload.role
        
        if payload.actif is not None:
            # Prevent deactivating last super_admin
            if not payload.actif and user["role"] == "super_admin":
                count_admins = await db.users.count_documents({"role": "super_admin", "actif": True})
                _ensure(count_admins > 1, 400, "Impossible de désactiver le dernier super_admin")
            updates["actif"] = payload.actif

        await db.users.update_one({"user_id": user_id}, {"$set": updates})
        
        updated = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        return UtilisateurOut(**updated)

    @router.delete("/{user_id}")
    async def delete_utilisateur(
        user_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in ADMIN_ROLES, 403, "Accès refusé - super_admin requis")

        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        _ensure(user is not None, 404, "Utilisateur introuvable")
        
        # Prevent deleting last super_admin
        if user["role"] == "super_admin":
            count_admins = await db.users.count_documents({"role": "super_admin", "actif": True})
            _ensure(count_admins > 1, 400, "Impossible de supprimer le dernier super_admin")
        
        # Soft delete
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"actif": False, "updated_at": _now_iso()}}
        )
        
        return {"message": "Utilisateur désactivé avec succès"}

    return router


# ---------------------------------------------------------------------------
# PARAMETRES
# ---------------------------------------------------------------------------
class ParametreUpdate(BaseModel):
    valeur: str


class ParametreOut(BaseModel):
    cle: str
    valeur: str
    description: Optional[str] = None
    updated_at: str


def build_parametres_router(db: AsyncIOMotorDatabase, resolve_user) -> APIRouter:
    router = APIRouter(prefix="/parametres", tags=["parametres"])

    @router.get("", response_model=List[ParametreOut])
    async def list_parametres(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in PARAMETRES_READ_ROLES, 403, "Accès refusé")

        cursor = db.parametres.find({}, {"_id": 0}).sort("cle", 1)
        docs = await cursor.to_list(100)
        
        return [ParametreOut(**d) for d in docs]

    @router.get("/{cle}", response_model=ParametreOut)
    async def get_parametre(
        cle: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in PARAMETRES_READ_ROLES, 403, "Accès refusé")

        param = await db.parametres.find_one({"cle": cle}, {"_id": 0})
        _ensure(param is not None, 404, "Paramètre introuvable")
        
        return ParametreOut(**param)

    @router.patch("/{cle}", response_model=ParametreOut)
    async def update_parametre(
        cle: str,
        payload: ParametreUpdate,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in ADMIN_ROLES, 403, "Accès refusé - super_admin requis")

        param = await db.parametres.find_one({"cle": cle}, {"_id": 0})
        _ensure(param is not None, 404, "Paramètre introuvable")

        now = _now_iso()
        await db.parametres.update_one(
            {"cle": cle},
            {"$set": {"valeur": payload.valeur, "updated_at": now}}
        )
        
        updated = await db.parametres.find_one({"cle": cle}, {"_id": 0})
        return ParametreOut(**updated)

    return router


async def seed_parametres(db: AsyncIOMotorDatabase) -> int:
    """Seed default parametres"""
    existing = await db.parametres.count_documents({})
    if existing > 0:
        return 0
    
    now = _now_iso()
    
    parametres_default = [
        {
            "cle": "entreprise_nom",
            "valeur": "EDITIONS FABS-CI",
            "description": "Nom de l'entreprise",
            "updated_at": now
        },
        {
            "cle": "entreprise_slogan",
            "valeur": "Les livres sont des fenêtres par lesquelles on regarde le monde",
            "description": "Slogan de l'entreprise",
            "updated_at": now
        },
        {
            "cle": "entreprise_telephone",
            "valeur": "+225 XX XX XX XX XX",
            "description": "Téléphone principal",
            "updated_at": now
        },
        {
            "cle": "entreprise_email",
            "valeur": "contact@editionsfabsci.com",
            "description": "Email de contact",
            "updated_at": now
        },
        {
            "cle": "entreprise_adresse",
            "valeur": "Abidjan, Côte d'Ivoire",
            "description": "Adresse postale",
            "updated_at": now
        },
        {
            "cle": "tva_taux",
            "valeur": "18",
            "description": "Taux TVA en pourcentage",
            "updated_at": now
        },
        {
            "cle": "banque_principale",
            "valeur": "CORIS BANK",
            "description": "Nom de la banque principale",
            "updated_at": now
        },
        {
            "cle": "banque_iban",
            "valeur": "CI XX XXXX XXXX XXXX XXXX XXXX",
            "description": "IBAN compte principal",
            "updated_at": now
        },
        {
            "cle": "seuil_validation_dg",
            "valeur": "500000",
            "description": "Seuil montant pour validation DG (FCFA)",
            "updated_at": now
        },
    ]
    
    await db.parametres.insert_many(parametres_default)
    await db.parametres.create_index("cle", unique=True)
    
    return len(parametres_default)



# ---------------------------------------------------------------------------
# AUDIT LOGS ENDPOINT
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    """Schema for audit log response"""
    _id: Optional[str] = None
    timestamp: str
    utilisateur_id: Optional[str] = None
    utilisateur_email: Optional[str] = None
    utilisateur_nom: Optional[str] = None
    module: str
    action: str
    objet_type: Optional[str] = None
    objet_id: Optional[str] = None
    statut: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


def build_audit_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    """Build audit logs router"""
    router = APIRouter(prefix="/audit", tags=["audit"])
    
    # Allowed roles for audit access
    AUDIT_ROLES = {"super_admin", "admin", "auditeur"}
    
    @router.get("", response_model=List[AuditLogOut])
    async def list_audit_logs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        module: Optional[str] = Query(None, description="Filter by module"),
        utilisateur_email: Optional[str] = Query(None, description="Filter by user email"),
        action: Optional[str] = Query(None, description="Filter by action"),
        limite: int = Query(100, ge=1, le=1000, description="Max results"),
        offset: int = Query(0, ge=0, description="Pagination offset"),
    ):
        """
        GET /api/audit
        List audit logs with optional filters
        Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR
        """
        me = await resolve_user(request, authorization)
        
        # RBAC check
        if me.get("role") not in AUDIT_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"Audit access denied. Required roles: {AUDIT_ROLES}"
            )
        
        # Build query filters
        filters = {"statut": {"$in": ["success", "error", "warning"]}}
        
        if module:
            filters["module"] = module
        
        if utilisateur_email:
            filters["utilisateur_email"] = utilisateur_email
        
        if action:
            filters["action"] = action
        
        # Query audit logs
        audit_logs = await db.audit_logs.find(filters).skip(offset).limit(limite).sort("timestamp", -1).to_list(None)
        
        # Convert ObjectId to string for JSON response
        result = []
        for log in audit_logs:
            log["_id"] = str(log.get("_id", ""))
            result.append(log)
        
        return result
    
    @router.get("/stats", response_model=dict)
    async def get_audit_stats(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """
        GET /api/audit/stats
        Summary statistics of audit logs
        Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR
        """
        me = await resolve_user(request, authorization)
        
        # RBAC check
        if me.get("role") not in AUDIT_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"Audit access denied. Required roles: {AUDIT_ROLES}"
            )
        
        total_logs = await db.audit_logs.count_documents({})
        success_count = await db.audit_logs.count_documents({"statut": "success"})
        error_count = await db.audit_logs.count_documents({"statut": "error"})
        warning_count = await db.audit_logs.count_documents({"statut": "warning"})
        
        # Get unique modules and actions
        modules = await db.audit_logs.distinct("module")
        actions = await db.audit_logs.distinct("action")
        
        return {
            "total_logs": total_logs,
            "success_count": success_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "unique_modules": len(modules) if modules else 0,
            "unique_actions": len(actions) if actions else 0,
            "modules": sorted(modules) if modules else [],
            "actions": sorted(actions) if actions else [],
        }
    
    return router
