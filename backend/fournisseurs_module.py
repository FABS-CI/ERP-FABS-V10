"""
Module Fournisseurs — Gestion des imprimeurs/fournisseurs
- CRUD complet sur la collection MongoDB `fournisseurs`
- Référence auto-incrémentée FABS-FRN-XXXX
- RBAC :
    READ = {super_admin, DG, gestionnaire_stock}
    WRITE = {super_admin, DG, gestionnaire_stock}
"""
from __future__ import annotations

import os
import jwt
from datetime import datetime, timezone
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("fabsci.fournisseurs")

READ_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock"}
WRITE_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock"}


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_fournisseur_reference(db: AsyncIOMotorDatabase) -> str:
    doc = await db.counters.find_one_and_update(
        {"_id": "fournisseurs"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-FRN-{seq:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class FournisseurIn(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    contact: Optional[str] = Field(default=None, max_length=120)
    telephone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=120)
    adresse: Optional[str] = Field(default=None, max_length=500)

    @field_validator("nom", "contact", "telephone", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class FournisseurPatch(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=2, max_length=200)
    contact: Optional[str] = Field(default=None, max_length=120)
    telephone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=120)
    adresse: Optional[str] = Field(default=None, max_length=500)

    @field_validator("nom", "contact", "telephone", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class FournisseurOut(BaseModel):
    fournisseur_id: str
    reference: str
    nom: str
    contact: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    actif: bool = True
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/fournisseurs", tags=["fournisseurs"])


async def resolve_user(request: Request, authorization: Optional[str] = Header(default=None)):
    """Résout l'utilisateur depuis le token JWT (header Authorization ou cookie session_token)."""
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "")
    else:
        token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET', 'fabsci-secret-key-change-in-development-only'), algorithms=['HS256'])
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"user_id": user_id, "role": payload.get('role', 'user')}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


@router.get("", response_model=list[FournisseurOut])
async def list_fournisseurs(
    request: Request,
    q: Optional[str] = Query(default=None),
    actif: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    authorization: Optional[str] = Header(default=None),
):
    """Liste tous les fournisseurs avec filtres"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    filter_query = {}
    if q:
        filter_query["$or"] = [
            {"nom": {"$regex": q, "$options": "i"}},
            {"contact": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]
    if actif is not None:
        filter_query["actif"] = actif
    
    cursor = db.fournisseurs.find(filter_query).skip(offset).limit(limit).sort("created_at", -1)
    items = await cursor.to_list(length=limit)
    
    return [FournisseurOut(**item) for item in items]


@router.get("/{fournisseur_id}", response_model=FournisseurOut)
async def get_fournisseur(
    fournisseur_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Récupère un fournisseur par ID"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    fournisseur = await db.fournisseurs.find_one({"fournisseur_id": fournisseur_id}, {"_id": 0})
    
    _ensure(fournisseur is not None, 404, "Fournisseur introuvable")
    
    return FournisseurOut(**fournisseur)


@router.post("", response_model=FournisseurOut, status_code=201)
async def create_fournisseur(
    data: FournisseurIn,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Crée un nouveau fournisseur"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    # Vérifier si un fournisseur avec le même nom existe déjà
    existing = await db.fournisseurs.find_one({"nom": data.nom})
    _ensure(existing is None, 400, "Un fournisseur avec ce nom existe déjà")
    
    fournisseur_id = str(__import__("uuid").uuid4())
    reference = await next_fournisseur_reference(db)
    now = _now_iso()
    
    doc = {
        "fournisseur_id": fournisseur_id,
        "reference": reference,
        "nom": data.nom,
        "contact": data.contact,
        "telephone": data.telephone,
        "email": data.email,
        "adresse": data.adresse,
        "actif": True,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.fournisseurs.insert_one(doc)
    
    logger.info(f"Fournisseur créé: {reference} - {data.nom} par {me['user_id']}")
    
    return FournisseurOut(**doc)


@router.put("/{fournisseur_id}", response_model=FournisseurOut)
async def update_fournisseur(
    fournisseur_id: str,
    data: FournisseurPatch,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Met à jour un fournisseur"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    fournisseur = await db.fournisseurs.find_one({"fournisseur_id": fournisseur_id})
    _ensure(fournisseur is not None, 404, "Fournisseur introuvable")
    
    # Si le nom est modifié, vérifier qu'il n'existe pas déjà
    if data.nom and data.nom != fournisseur["nom"]:
        existing = await db.fournisseurs.find_one({"nom": data.nom})
        _ensure(existing is None, 400, "Un fournisseur avec ce nom existe déjà")
    
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = _now_iso()
        await db.fournisseurs.update_one(
            {"fournisseur_id": fournisseur_id},
            {"$set": update_data}
        )
    
    updated = await db.fournisseurs.find_one({"fournisseur_id": fournisseur_id}, {"_id": 0})
    
    logger.info(f"Fournisseur mis à jour: {fournisseur['reference']} par {me['user_id']}")
    
    return FournisseurOut(**updated)


@router.delete("/{fournisseur_id}", status_code=204)
async def delete_fournisseur(
    fournisseur_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Supprime un fournisseur (soft delete)"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    fournisseur = await db.fournisseurs.find_one({"fournisseur_id": fournisseur_id})
    _ensure(fournisseur is not None, 404, "Fournisseur introuvable")
    
    # Vérifier si des produits sont liés à ce fournisseur
    produits_lies = await db.produits.count_documents({"fournisseur_id": fournisseur_id})
    _ensure(produits_lies == 0, 400, "Des produits sont liés à ce fournisseur")
    
    await db.fournisseurs.update_one(
        {"fournisseur_id": fournisseur_id},
        {"$set": {"actif": False, "updated_at": _now_iso()}}
    )
    
    logger.info(f"Fournisseur désactivé: {fournisseur['reference']} par {me['user_id']}")


@router.get("/{fournisseur_id}/livraisons")
async def get_livraisons_fournisseur(
    fournisseur_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    authorization: Optional[str] = Header(default=None),
):
    """Récupère l'historique des livraisons d'un fournisseur"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    fournisseur = await db.fournisseurs.find_one({"fournisseur_id": fournisseur_id})
    _ensure(fournisseur is not None, 404, "Fournisseur introuvable")
    
    cursor = db.approvisionnements.find(
        {"fournisseur_id": fournisseur_id}
    ).skip(offset).limit(limit).sort("created_at", -1)
    
    livraisons = await cursor.to_list(length=limit)
    
    return {
        "fournisseur": fournisseur,
        "livraisons": livraisons,
        "total": len(livraisons)
    }
