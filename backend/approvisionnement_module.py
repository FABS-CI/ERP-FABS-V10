"""
Module Approvisionnement — Gestion des entrées de stock
- CRUD sur la collection MongoDB `approvisionnements`
- Référence auto-incrémentée FABS-APP-XXXX
- RBAC :
    READ = {super_admin, DG, gestionnaire_stock}
    WRITE = {super_admin, DG, gestionnaire_stock}
- Logique métier:
    * Toute entrée de stock vient d'un fournisseur
    * Validation génère automatiquement des mouvements de stock (type IN)
    * Historisation des livraisons par fournisseur
"""
from __future__ import annotations

import os
import jwt
from datetime import datetime, timezone
from typing import Optional, List
import logging
import uuid

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("fabsci.approvisionnement")

READ_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock"}
WRITE_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock"}


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_approvisionnement_reference(db: AsyncIOMotorDatabase) -> str:
    doc = await db.counters.find_one_and_update(
        {"_id": "approvisionnements"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-APP-{seq:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ApprovisionnementLigneIn(BaseModel):
    produit_id: str = Field(..., description="ID du produit")
    quantite: int = Field(..., gt=0, description="Quantité reçue")
    prix_achat: float = Field(..., ge=0, description="Prix d'achat unitaire")


class ApprovisionnementIn(BaseModel):
    fournisseur_id: str = Field(..., description="ID du fournisseur")
    depot: str = Field(..., description="Dépôt de destination (principal/secondaire)")
    lignes: List[ApprovisionnementLigneIn] = Field(..., min_length=1, description="Lignes de produits")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Notes additionnelles")


class ApprovisionnementOut(BaseModel):
    approvisionnement_id: str
    reference: str
    fournisseur_id: str
    fournisseur_nom: Optional[str] = None
    depot: str
    lignes: List[dict]
    statut: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    valide_le: Optional[str] = None
    valide_par: Optional[str] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/approvisionnements", tags=["approvisionnements"])


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


@router.get("", response_model=list[ApprovisionnementOut])
async def list_approvisionnements(
    request: Request,
    fournisseur_id: Optional[str] = Query(default=None),
    statut: Optional[str] = Query(default=None),
    depot: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    authorization: Optional[str] = Header(default=None),
):
    """Liste tous les approvisionnements avec filtres"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    filter_query = {}
    if fournisseur_id:
        filter_query["fournisseur_id"] = fournisseur_id
    if statut:
        filter_query["statut"] = statut
    if depot:
        filter_query["depot"] = depot
    
    cursor = db.approvisionnements.find(filter_query).skip(offset).limit(limit).sort("created_at", -1)
    items = await cursor.to_list(length=limit)
    
    # Enrichir avec le nom du fournisseur
    for item in items:
        if item.get("fournisseur_id"):
            fournisseur = await db.fournisseurs.find_one(
                {"fournisseur_id": item["fournisseur_id"]},
                {"_id": 0, "nom": 1}
            )
            item["fournisseur_nom"] = fournisseur["nom"] if fournisseur else None
    
    return [ApprovisionnementOut(**item) for item in items]


@router.get("/{approvisionnement_id}", response_model=ApprovisionnementOut)
async def get_approvisionnement(
    approvisionnement_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Récupère un approvisionnement par ID"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    appro = await db.approvisionnements.find_one({"approvisionnement_id": approvisionnement_id}, {"_id": 0})
    
    _ensure(appro is not None, 404, "Approvisionnement introuvable")
    
    # Enrichir avec le nom du fournisseur
    if appro.get("fournisseur_id"):
        fournisseur = await db.fournisseurs.find_one(
            {"fournisseur_id": appro["fournisseur_id"]},
            {"_id": 0, "nom": 1}
        )
        appro["fournisseur_nom"] = fournisseur["nom"] if fournisseur else None
    
    return ApprovisionnementOut(**appro)


@router.post("", response_model=ApprovisionnementOut, status_code=201)
async def create_approvisionnement(
    data: ApprovisionnementIn,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Crée un nouvel approvisionnement (brouillon)"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    # Vérifier que le fournisseur existe
    fournisseur = await db.fournisseurs.find_one({"fournisseur_id": data.fournisseur_id})
    _ensure(fournisseur is not None, 404, "Fournisseur introuvable")
    
    # Vérifier que tous les produits existent
    for ligne in data.lignes:
        produit = await db.produits.find_one({"product_id": ligne.produit_id})
        _ensure(produit is not None, 404, f"Produit {ligne.produit_id} introuvable")
    
    approvisionnement_id = str(uuid.uuid4())
    reference = await next_approvisionnement_reference(db)
    now = _now_iso()
    
    doc = {
        "approvisionnement_id": approvisionnement_id,
        "reference": reference,
        "fournisseur_id": data.fournisseur_id,
        "fournisseur_nom": fournisseur["nom"],
        "depot": data.depot,
        "lignes": [ligne.model_dump() for ligne in data.lignes],
        "statut": "brouillon",
        "notes": data.notes,
        "created_at": now,
        "updated_at": now,
        "valide_le": None,
        "valide_par": None,
    }
    
    await db.approvisionnements.insert_one(doc)
    
    logger.info(f"Approvisionnement créé: {reference} par {me['user_id']}")
    
    return ApprovisionnementOut(**doc)


@router.post("/{approvisionnement_id}/valider", response_model=ApprovisionnementOut)
async def valider_approvisionnement(
    approvisionnement_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Valide un approvisionnement et génère les mouvements de stock"""
    me = await resolve_user(request, authorization)
    _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")
    
    db: AsyncIOMotorDatabase = request.app.state.db
    
    appro = await db.approvisionnements.find_one({"approvisionnement_id": approvisionnement_id})
    _ensure(appro is not None, 404, "Approvisionnement introuvable")
    _ensure(appro["statut"] == "brouillon", 400, "Seuls les approvisionnements en brouillon peuvent être validés")
    
    # Générer les mouvements de stock pour chaque ligne
    now = _now_iso()
    mouvements_creates = []
    
    for ligne in appro["lignes"]:
        # Récupérer le produit actuel
        produit = await db.produits.find_one({"product_id": ligne["produit_id"]})
        if produit:
            stock_avant = produit.get("stock_actuel", 0)
            stock_apres = stock_avant + ligne["quantite"]
            
            # Créer le mouvement de stock
            mouvement_id = str(uuid.uuid4())
            mouvement = {
                "mouvement_id": mouvement_id,
                "produit_id": ligne["produit_id"],
                "produit_reference": produit.get("reference", ""),
                "produit_titre": produit.get("titre", ""),
                "type_mouvement": "entree",
                "quantite": ligne["quantite"],
                "stock_avant": stock_avant,
                "stock_apres": stock_apres,
                "motif": f"Approvisionnement {appro['reference']} - Fournisseur: {appro['fournisseur_nom']}",
                "approvisionnement_id": approvisionnement_id,
                "fournisseur_id": appro["fournisseur_id"],
                "depot": appro["depot"],
                "created_at": now,
            }
            mouvements_creates.append(mouvement)
            
            # Mettre à jour le stock du produit
            await db.produits.update_one(
                {"product_id": ligne["produit_id"]},
                {
                    "$set": {
                        "stock_actuel": stock_apres,
                        "derniere_entree": now,
                        "updated_at": now,
                    }
                }
            )
            
            logger.info(f"Stock mis à jour: {produit['reference']} +{ligne['quantite']} = {stock_apres}")
    
    # Insérer tous les mouvements
    if mouvements_creates:
        await db.mouvements.insert_many(mouvements_creates)
        logger.info(f"{len(mouvements_creates)} mouvements créés pour approvisionnement {appro['reference']}")
    
    # Mettre à jour l'approvisionnement
    await db.approvisionnements.update_one(
        {"approvisionnement_id": approvisionnement_id},
        {
            "$set": {
                "statut": "valide",
                "valide_le": now,
                "valide_par": me["user_id"],
                "updated_at": now,
            }
        }
    )
    
    updated = await db.approvisionnements.find_one({"approvisionnement_id": approvisionnement_id}, {"_id": 0})
    
    logger.info(f"Approvisionnement validé: {appro['reference']} par {me['user_id']}")
    
    return ApprovisionnementOut(**updated)
