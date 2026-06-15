"""
Module Packaging/Colisage - Gestion des colis et expéditions
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger("fabsci.colisage")

# ============================================================================
# SCHEMAS
# ============================================================================

class ProduitColis(BaseModel):
    produit_id: str
    quantite: int = Field(gt=0)
    poids_unitaire: float = Field(ge=0)
    poids_total: float = Field(ge=0)

class ColisIn(BaseModel):
    commande_id: str
    ligne_commande_ids: List[str]
    produits: List[ProduitColis]
    poids_total: float = Field(ge=0)
    dimensions: Optional[dict] = None  # {longueur, largeur, hauteur}
    notes: Optional[str] = None

class ColisOut(BaseModel):
    colis_id: str
    reference: str
    commande_id: str
    commande_reference: Optional[str] = None
    client_nom: Optional[str] = None
    client_ville: Optional[str] = None
    client_telephone: Optional[str] = None
    client_representant: Optional[str] = None
    ligne_commande_ids: List[str]
    produits: List[dict]
    poids_total: float
    dimensions: Optional[dict] = None
    statut: str
    expedition_id: Optional[str] = None
    code_barres: str
    qr_code: str
    notes: Optional[str] = None
    created_at: str
    created_by: str
    updated_at: str

class AdresseLivraison(BaseModel):
    nom: str
    adresse: str
    ville: str
    pays: str = "Côte d'Ivoire"
    telephone: str

class ExpeditionIn(BaseModel):
    colis_ids: List[str]
    commande_id: str
    adresse_livraison: AdresseLivraison
    transporteur_id: Optional[str] = None
    date_expedition: Optional[str] = None
    date_livraison_prevue: Optional[str] = None
    notes: Optional[str] = None

class ExpeditionOut(BaseModel):
    expedition_id: str
    reference: Optional[str] = None
    colis_ids: List[str] = []
    commande_id: Optional[str] = None
    client_id: Optional[str] = None
    adresse_livraison: Optional[dict] = None
    transporteur_id: Optional[str] = None
    statut: Optional[str] = "preparation"
    date_expedition: Optional[str] = None
    date_livraison_prevue: Optional[str] = None
    date_livraison_reelle: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None

class MouvementColisOut(BaseModel):
    mouvement_id: str
    colis_id: str
    type_mouvement: str
    details: dict
    user_id: str
    timestamp: str

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire", "preparateur"]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire", "preparateur"]
DELETE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _generate_reference(prefix: str) -> str:
    """Génère une référence unique"""
    year = datetime.now().strftime("%Y")
    # Dans un vrai système, on utiliserait un compteur séquentiel
    return f"{prefix}-{year}-{datetime.now().strftime('%m%d%H%M%S')}"

def _generate_code_barres() -> str:
    """Génère un code-barres unique (13 chiffres)"""
    import random
    return f"{random.randint(1000000000000, 9999999999999)}"

async def _log_mouvement_colis(db, colis_id: str, type_mouvement: str, details: dict, user_id: str):
    """Enregistre un mouvement de colis"""
    # Sanitize details: remove any ObjectId fields (MongoDB mutates dicts passed to insert_one)
    clean_details = {k: str(v) if hasattr(v, '__class__') and v.__class__.__name__ == 'ObjectId' else v
                     for k, v in details.items() if k != "_id"}
    mouvement_doc = {
        "mouvement_id": f"mouv_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{colis_id[:8]}",
        "colis_id": colis_id,
        "type_mouvement": type_mouvement,
        "details": clean_details,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.mouvements_colis.insert_one(mouvement_doc)

async def _update_stock_from_colis(db, colis_id: str, operation: str):
    """Met à jour le stock lors de la création/expédition d'un colis"""
    colis = await db.colis.find_one({"colis_id": colis_id})
    if not colis:
        return
    
    for produit in colis.get("produits", []):
        produit_id = produit["produit_id"]
        quantite = produit["quantite"]
        
        if operation == "expedition":
            # Déduire du stock
            await db.produits.update_one(
                {"produit_id": produit_id},
                {"$inc": {"stock_actuel": -quantite}}
            )
        elif operation == "annulation":
            # Remettre en stock
            await db.produits.update_one(
                {"produit_id": produit_id},
                {"$inc": {"stock_actuel": quantite}}
            )

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_colisage_router(db, resolve_user):
    router = APIRouter(prefix="/colisage", tags=["colisage"])

    # ============================================================================
    # COLIS ENDPOINTS
    # ============================================================================

    @router.get("/colis", response_model=List[ColisOut])
    async def list_colis(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        commande_id: Optional[str] = None,
        statut: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les colis avec filtres"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if commande_id:
            filters["commande_id"] = commande_id
        if statut:
            filters["statut"] = statut

        pipeline = [
            {"$match": filters},
            {"$lookup": {
                "from": "commandes",
                "localField": "commande_id",
                "foreignField": "commande_id",
                "as": "commande_info"
            }},
            {"$addFields": {
                "commande_reference": {"$arrayElemAt": ["$commande_info.reference", 0]},
                "client_id_from_cmd": {"$arrayElemAt": ["$commande_info.client_id", 0]},
            }},
            {"$lookup": {
                "from": "clients",
                "localField": "client_id_from_cmd",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
            }},
            {"$project": {"commande_info": 0, "client_info": 0, "client_id_from_cmd": 0, "_id": 0}},
        ]
        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
                {"client_telephone": {"$regex": q, "$options": "i"}},
                {"client_representant": {"$regex": q, "$options": "i"}},
            ]}})
        pipeline += [{"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}]

        docs = await db.colis.aggregate(pipeline).to_list(limit)
        return [ColisOut(**d) for d in docs]

    @router.get("/colis/{colis_id}", response_model=ColisOut)
    async def get_colis(
        colis_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les détails d'un colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        colis = await db.colis.find_one({"colis_id": colis_id}, {"_id": 0})
        if not colis:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        return ColisOut(**colis)

    @router.post("/colis", response_model=ColisOut, status_code=201)
    async def create_colis(
        payload: ColisIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un nouveau colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Vérifier que la commande existe
        commande = await db.commandes.find_one({"commande_id": payload.commande_id})
        if not commande:
            raise HTTPException(status_code=404, detail="Commande introuvable")

        # Vérifier que les produits existent
        for prod in payload.produits:
            produit = await db.produits.find_one({"produit_id": prod.produit_id})
            if not produit:
                raise HTTPException(status_code=404, detail=f"Produit {prod.produit_id} introuvable")

        colis_id = f"colis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        reference = _generate_reference("FABS-COL")
        code_barres = _generate_code_barres()
        qr_code = f"https://erp.fabsci.ci/colis/{colis_id}"

        colis_doc = {
            "colis_id": colis_id,
            "reference": reference,
            "commande_id": payload.commande_id,
            "ligne_commande_ids": payload.ligne_commande_ids,
            "produits": [p.dict() for p in payload.produits],
            "poids_total": payload.poids_total,
            "dimensions": payload.dimensions,
            "statut": "en_preparation",
            "expedition_id": None,
            "code_barres": code_barres,
            "qr_code": qr_code,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.colis.insert_one(colis_doc)
        
        # Logger le mouvement
        await _log_mouvement_colis(db, colis_id, "creation", colis_doc, user["user_id"])

        logger.info(f"Colis créé: {reference} par {user['email']}")
        return ColisOut(**colis_doc)

    @router.put("/colis/{colis_id}", response_model=ColisOut)
    async def update_colis(
        colis_id: str,
        payload: ColisIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour un colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")

        # Empêcher la modification si déjà expédié
        if existing["statut"] == "expedie":
            raise HTTPException(status_code=400, detail="Impossible de modifier un colis expédié")

        update_data = {
            "produits": [p.dict() for p in payload.produits],
            "poids_total": payload.poids_total,
            "dimensions": payload.dimensions,
            "notes": payload.notes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.colis.update_one({"colis_id": colis_id}, {"$set": update_data})
        
        # Logger le mouvement
        await _log_mouvement_colis(db, colis_id, "modification", update_data, user["user_id"])

        updated = await db.colis.find_one({"colis_id": colis_id}, {"_id": 0})
        return ColisOut(**updated)

    @router.delete("/colis/{colis_id}")
    async def delete_colis(
        colis_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Supprimer un colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")

        # Empêcher la suppression si déjà expédié
        if existing["statut"] == "expedie":
            raise HTTPException(status_code=400, detail="Impossible de supprimer un colis expédié")

        await db.colis.delete_one({"colis_id": colis_id})
        
        # Logger le mouvement
        await _log_mouvement_colis(db, colis_id, "suppression", existing, user["user_id"])

        logger.info(f"Colis supprimé: {colis_id} par {user['email']}")
        return {"message": "Colis supprimé avec succès"}

    @router.patch("/colis/{colis_id}/statut")
    async def update_colis_statut(
        colis_id: str,
        statut: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour le statut d'un colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        if statut not in ["en_preparation", "pret", "expedie"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")

        update_data = {"statut": statut, "updated_at": datetime.now(timezone.utc).isoformat()}
        await db.colis.update_one({"colis_id": colis_id}, {"$set": update_data})
        
        # Logger le mouvement
        await _log_mouvement_colis(db, colis_id, "changement_statut", {"ancien": existing["statut"], "nouveau": statut}, user["user_id"])

        logger.info(f"Statut colis {colis_id} mis à jour: {statut}")
        return {"message": f"Statut mis à jour: {statut}"}

    # ============================================================================
    # EXPEDITIONS ENDPOINTS
    # ============================================================================

    @router.get("/expeditions", response_model=List[ExpeditionOut])
    async def list_expeditions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        commande_id: Optional[str] = None,
        client_id: Optional[str] = None,
        statut: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les expéditions avec filtres"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if commande_id:
            filters["commande_id"] = commande_id
        if client_id:
            filters["client_id"] = client_id
        if statut:
            filters["statut"] = statut

        pipeline = [
            {"$match": filters},
            {"$lookup": {
                "from": "clients",
                "localField": "client_id",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
            }},
            {"$project": {"client_info": 0, "_id": 0}},
        ]
        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
                {"client_telephone": {"$regex": q, "$options": "i"}},
                {"client_representant": {"$regex": q, "$options": "i"}},
            ]}})
        pipeline += [{"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}]

        docs = await db.expeditions.aggregate(pipeline).to_list(limit)
        return [ExpeditionOut(**d) for d in docs]

    @router.get("/expeditions/{expedition_id}", response_model=ExpeditionOut)
    async def get_expedition(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les détails d'une expédition"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        expedition = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
        if not expedition:
            raise HTTPException(status_code=404, detail="Expédition introuvable")
        return ExpeditionOut(**expedition)

    @router.post("/expeditions", response_model=ExpeditionOut, status_code=201)
    async def create_expedition(
        payload: ExpeditionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une nouvelle expédition"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Vérifier que la commande existe
        commande = await db.commandes.find_one({"commande_id": payload.commande_id})
        if not commande:
            raise HTTPException(status_code=404, detail="Commande introuvable")

        # Vérifier que tous les colis existent et sont prêts
        colis_list = []
        for colis_id in payload.colis_ids:
            colis = await db.colis.find_one({"colis_id": colis_id})
            if not colis:
                raise HTTPException(status_code=404, detail=f"Colis {colis_id} introuvable")
            if colis["statut"] != "pret":
                raise HTTPException(status_code=400, detail=f"Colis {colis_id} n'est pas prêt")
            colis_list.append(colis)

        expedition_id = f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        reference = _generate_reference("FABS-EXP")

        expedition_doc = {
            "expedition_id": expedition_id,
            "reference": reference,
            "colis_ids": payload.colis_ids,
            "commande_id": payload.commande_id,
            "client_id": commande["client_id"],
            "adresse_livraison": payload.adresse_livraison.dict(),
            "transporteur_id": payload.transporteur_id,
            "statut": "en_preparation",
            "date_expedition": payload.date_expedition,
            "date_livraison_prevue": payload.date_livraison_prevue,
            "date_livraison_reelle": None,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.expeditions.insert_one(expedition_doc)

        # Mettre à jour les colis avec l'expedition_id
        for colis_id in payload.colis_ids:
            await db.colis.update_one(
                {"colis_id": colis_id},
                {"$set": {"expedition_id": expedition_id}}
            )

        logger.info(f"Expédition créée: {reference} par {user['email']}")
        return ExpeditionOut(**expedition_doc)

    @router.patch("/expeditions/{expedition_id}/statut")
    async def update_expedition_statut(
        expedition_id: str,
        request: Request,
        statut: str,
        date_livraison_reelle: Optional[str] = None,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour le statut d'une expédition"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        if statut not in ["en_preparation", "pret", "en_transit", "livre", "annule"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        existing = await db.expeditions.find_one({"expedition_id": expedition_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        update_data = {"statut": statut, "updated_at": datetime.now(timezone.utc).isoformat()}
        if date_livraison_reelle:
            update_data["date_livraison_reelle"] = date_livraison_reelle

        await db.expeditions.update_one({"expedition_id": expedition_id}, {"$set": update_data})

        # Si expédié, mettre à jour les colis et le stock
        if statut == "en_transit":
            for colis_id in existing["colis_ids"]:
                await db.colis.update_one(
                    {"colis_id": colis_id},
                    {"$set": {"statut": "expedie"}}
                )
                await _update_stock_from_colis(db, colis_id, "expedition")

        logger.info(f"Statut expédition {expedition_id} mis à jour: {statut}")
        return {"message": f"Statut mis à jour: {statut}"}

    # ============================================================================
    # MOUVEMENTS ENDPOINTS
    # ============================================================================

    @router.get("/mouvements", response_model=List[MouvementColisOut])
    async def list_mouvements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        colis_id: Optional[str] = None,
        type_mouvement: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les mouvements de colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if colis_id:
            filters["colis_id"] = colis_id
        if type_mouvement:
            filters["type_mouvement"] = type_mouvement

        cursor = db.mouvements_colis.find(filters, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        result = []
        for d in docs:
            d.pop("_id", None)
            # Sanitize nested ObjectIds in details dict (legacy docs may contain them)
            if "details" in d and isinstance(d["details"], dict):
                d["details"] = {
                    k: str(v) if hasattr(v, '__class__') and v.__class__.__name__ == 'ObjectId' else v
                    for k, v in d["details"].items()
                    if k != "_id"
                }
            result.append(MouvementColisOut(**d))
        return result

    return router
