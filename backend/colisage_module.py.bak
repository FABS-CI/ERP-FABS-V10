"""
Module Colisage - Workflow: Commande → Facture → Colisage → Livraison → Paiement
Le colisage est exclusivement lié à une FACTURE validée (statut: emise/partiellement_payee/payee).
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

class LigneColis(BaseModel):
    ligne_facture_id: str
    produit_id: str
    designation: str
    quantite_facturee: int = Field(gt=0)
    quantite_colisee: int = Field(gt=0)
    poids_unitaire: float = Field(ge=0, default=0.0)
    poids_total: float = Field(ge=0, default=0.0)

class ColisIn(BaseModel):
    facture_id: str
    lignes: List[LigneColis]
    poids_total: float = Field(ge=0, default=0.0)
    dimensions: Optional[dict] = None  # {longueur, largeur, hauteur}
    notes: Optional[str] = None

class ColisUpdate(BaseModel):
    lignes: List[LigneColis]
    poids_total: float = Field(ge=0, default=0.0)
    dimensions: Optional[dict] = None
    notes: Optional[str] = None

class ColisOut(BaseModel):
    colis_id: str
    reference: str
    facture_id: str
    facture_reference: Optional[str] = None
    commande_id: Optional[str] = None
    commande_reference: Optional[str] = None
    client_id: Optional[str] = None
    client_nom: Optional[str] = None
    client_ville: Optional[str] = None
    client_telephone: Optional[str] = None
    client_representant: Optional[str] = None
    lignes: List[dict] = []
    poids_total: float
    dimensions: Optional[dict] = None
    statut: str  # en_preparation | valide | expedie | annule
    code_barres: str
    qr_code: str
    notes: Optional[str] = None
    created_at: str
    created_by: str
    updated_at: str
    historique: List[dict] = []

class ColisStatutIn(BaseModel):
    statut: str
    motif: Optional[str] = None

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire", "preparateur", "directeur_commercial", "directeur_general", "comptable"]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire", "preparateur"]
VALIDATE_ROLES = ["super_admin", "admin", "gestionnaire"]
DELETE_ROLES = ["super_admin", "admin"]

STATUTS_FACTURE_AUTORISÉS = ["emise", "partiellement_payee", "payee"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _generate_reference(prefix: str, counter: int) -> str:
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    return f"{prefix}-{year}{month}-{str(counter).zfill(5)}"

def _generate_code_barres() -> str:
    import random
    return f"{random.randint(1000000000000, 9999999999999)}"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def _next_counter(db, name: str) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]

async def _log_historique(db, colis_id: str, action: str, user_id: str, details: dict = None):
    """Ajoute une entrée dans l'historique du colis"""
    entry = {
        "action": action,
        "user_id": user_id,
        "timestamp": _now_iso(),
        "details": details or {}
    }
    await db.colis.update_one(
        {"colis_id": colis_id},
        {"$push": {"historique": entry}}
    )
    # Log aussi dans mouvements_colis pour traçabilité globale
    mouvement_doc = {
        "mouvement_id": f"mouv_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:20]}",
        "colis_id": colis_id,
        "type_mouvement": action,
        "details": details or {},
        "user_id": user_id,
        "timestamp": _now_iso()
    }
    await db.mouvements_colis.insert_one(mouvement_doc)

async def _get_quantites_colisees(db, facture_id: str, exclude_colis_id: str = None) -> dict:
    """Retourne {ligne_facture_id: quantite_totale_colisee} pour une facture (hors annulés)"""
    match = {
        "facture_id": facture_id,
        "statut": {"$ne": "annule"}
    }
    if exclude_colis_id:
        match["colis_id"] = {"$ne": exclude_colis_id}
    
    cursor = db.colis.find(match, {"lignes": 1, "_id": 0})
    result = {}
    async for colis in cursor:
        for ligne in colis.get("lignes", []):
            lid = ligne["ligne_facture_id"]
            result[lid] = result.get(lid, 0) + ligne.get("quantite_colisee", 0)
    return result

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_colisage_router(db, resolve_user):
    router = APIRouter(prefix="/colisage", tags=["colisage"])

    # ============================================================================
    # COLIS ENDPOINTS
    # ============================================================================

    @router.get("/colis")
    async def list_colis(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        facture_id: Optional[str] = None,
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
        if facture_id:
            filters["facture_id"] = facture_id
        if commande_id:
            filters["commande_id"] = commande_id
        if statut:
            filters["statut"] = statut

        pipeline = [
            {"$match": filters},
            # Jointure facture
            {"$lookup": {
                "from": "factures",
                "localField": "facture_id",
                "foreignField": "facture_id",
                "as": "facture_info"
            }},
            {"$addFields": {
                "facture_reference": {"$arrayElemAt": ["$facture_info.reference", 0]},
                "commande_id_from_fac": {"$arrayElemAt": ["$facture_info.commande_id", 0]},
                "client_id_from_fac": {"$arrayElemAt": ["$facture_info.client_id", 0]},
            }},
            # Jointure commande (pour référence uniquement)
            {"$lookup": {
                "from": "commandes",
                "localField": "commande_id_from_fac",
                "foreignField": "commande_id",
                "as": "commande_info"
            }},
            {"$addFields": {
                "commande_reference": {"$arrayElemAt": ["$commande_info.reference", 0]},
            }},
            # Jointure client
            {"$lookup": {
                "from": "clients",
                "localField": "client_id_from_fac",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$addFields": {
                "client_id": {"$arrayElemAt": ["$client_info.client_id", 0]},
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
            }},
            {"$project": {
                "facture_info": 0, "commande_info": 0, "client_info": 0,
                "commande_id_from_fac": 0, "client_id_from_fac": 0,
                "_id": 0
            }},
        ]

        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"facture_reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
                {"client_telephone": {"$regex": q, "$options": "i"}},
            ]}})

        pipeline += [{"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}]

        docs = await db.colis.aggregate(pipeline).to_list(limit)
        # Nettoyer les ObjectId
        for d in docs:
            d.pop("_id", None)
        return docs

    @router.get("/colis/by-facture/{facture_id}")
    async def get_colis_by_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Récupérer tous les colis d'une facture + quantités facturées/colisées/restantes.
        Utilisé par FactureDetail pour afficher le statut colisage.
        """
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Vérifier que la facture existe
        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")

        # Lignes de facture
        lignes_fac = await db.facture_lignes.find(
            {"facture_id": facture_id}, {"_id": 0}
        ).to_list(200)

        # Quantités colisées par ligne
        qtés_colisées = await _get_quantites_colisees(db, facture_id)

        # Enrichir les lignes avec qté colisée et restante
        lignes_enrichies = []
        for lg in lignes_fac:
            qte_col = qtés_colisées.get(lg["ligne_id"], 0)
            lignes_enrichies.append({
                **lg,
                "quantite_colisee": qte_col,
                "quantite_restante": max(0, lg["quantite"] - qte_col),
            })

        # Liste des colis de cette facture
        colis_list = await db.colis.find(
            {"facture_id": facture_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(200)

        return {
            "facture_id": facture_id,
            "facture_reference": facture.get("reference"),
            "facture_statut": facture.get("statut"),
            "lignes": lignes_enrichies,
            "colis": colis_list,
            "nb_colis": len(colis_list),
            "nb_colis_valides": sum(1 for c in colis_list if c["statut"] == "valide"),
            "nb_colis_expedies": sum(1 for c in colis_list if c["statut"] == "expedie"),
        }

    @router.get("/colis/{colis_id}")
    async def get_colis(
        colis_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les détails d'un colis"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        pipeline = [
            {"$match": {"colis_id": colis_id}},
            {"$lookup": {"from": "factures", "localField": "facture_id", "foreignField": "facture_id", "as": "facture_info"}},
            {"$addFields": {
                "facture_reference": {"$arrayElemAt": ["$facture_info.reference", 0]},
                "commande_id_from_fac": {"$arrayElemAt": ["$facture_info.commande_id", 0]},
                "client_id_from_fac": {"$arrayElemAt": ["$facture_info.client_id", 0]},
            }},
            {"$lookup": {"from": "commandes", "localField": "commande_id_from_fac", "foreignField": "commande_id", "as": "commande_info"}},
            {"$addFields": {"commande_reference": {"$arrayElemAt": ["$commande_info.reference", 0]}}},
            {"$lookup": {"from": "clients", "localField": "client_id_from_fac", "foreignField": "client_id", "as": "client_info"}},
            {"$addFields": {
                "client_id": {"$arrayElemAt": ["$client_info.client_id", 0]},
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
            }},
            {"$project": {"facture_info": 0, "commande_info": 0, "client_info": 0, "commande_id_from_fac": 0, "client_id_from_fac": 0, "_id": 0}},
        ]
        docs = await db.colis.aggregate(pipeline).to_list(1)
        if not docs:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        doc = docs[0]
        doc.pop("_id", None)
        return doc

    @router.post("/colis", status_code=201)
    async def create_colis(
        payload: ColisIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un colis lié à une facture validée"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Vérifier que la facture existe et est dans un statut autorisé
        facture = await db.factures.find_one({"facture_id": payload.facture_id})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")
        if facture["statut"] not in STATUTS_FACTURE_AUTORISÉS:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de créer un colis pour une facture en statut '{facture['statut']}'. "
                       f"La facture doit être émise, partiellement payée ou payée."
            )

        # Charger les lignes de la facture
        lignes_fac = await db.facture_lignes.find(
            {"facture_id": payload.facture_id}, {"_id": 0}
        ).to_list(200)
        lignes_fac_map = {lg["ligne_id"]: lg for lg in lignes_fac}

        # Quantités déjà colisées (hors annulés)
        qtés_colisées = await _get_quantites_colisees(db, payload.facture_id)

        # Valider chaque ligne du colis
        for ligne in payload.lignes:
            lg_fac = lignes_fac_map.get(ligne.ligne_facture_id)
            if not lg_fac:
                raise HTTPException(
                    status_code=404,
                    detail=f"Ligne facture '{ligne.ligne_facture_id}' introuvable"
                )
            qte_max = lg_fac["quantite"]
            qte_deja = qtés_colisées.get(ligne.ligne_facture_id, 0)
            qte_restante = qte_max - qte_deja
            if ligne.quantite_colisee > qte_restante:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quantité colisée ({ligne.quantite_colisee}) > quantité restante ({qte_restante}) "
                           f"pour '{lg_fac['designation']}'. Déjà colisé: {qte_deja}/{qte_max}."
                )

        # Générer les IDs
        counter = await _next_counter(db, "colis")
        colis_id = f"colis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}"
        reference = _generate_reference("FABS-COL", counter)
        code_barres = _generate_code_barres()
        qr_code = f"https://erp.fabsci.ci/colis/{colis_id}"

        # Construire les lignes enrichies
        lignes_doc = []
        for ligne in payload.lignes:
            lg_fac = lignes_fac_map[ligne.ligne_facture_id]
            lignes_doc.append({
                "ligne_facture_id": ligne.ligne_facture_id,
                "produit_id": ligne.produit_id,
                "designation": ligne.designation or lg_fac.get("designation", ""),
                "quantite_facturee": lg_fac["quantite"],
                "quantite_colisee": ligne.quantite_colisee,
                "poids_unitaire": ligne.poids_unitaire,
                "poids_total": ligne.poids_total,
            })

        now = _now_iso()
        colis_doc = {
            "colis_id": colis_id,
            "reference": reference,
            "facture_id": payload.facture_id,
            "lignes": lignes_doc,
            "poids_total": payload.poids_total,
            "dimensions": payload.dimensions,
            "statut": "en_preparation",
            "code_barres": code_barres,
            "qr_code": qr_code,
            "notes": payload.notes,
            "created_at": now,
            "created_by": user["user_id"],
            "updated_at": now,
            "historique": [{
                "action": "creation",
                "user_id": user["user_id"],
                "timestamp": now,
                "details": {"reference": reference}
            }]
        }

        await db.colis.insert_one(colis_doc)
        colis_doc.pop("_id", None)

        logger.info(f"Colis créé: {reference} pour facture {payload.facture_id} par {user['email']}")
        return colis_doc

    @router.put("/colis/{colis_id}")
    async def update_colis(
        colis_id: str,
        payload: ColisUpdate,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour un colis (uniquement en_preparation)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        if existing["statut"] in ("valide", "expedie"):
            raise HTTPException(status_code=400, detail=f"Impossible de modifier un colis '{existing['statut']}'")

        facture_id = existing["facture_id"]

        # Charger les lignes de la facture
        lignes_fac = await db.facture_lignes.find(
            {"facture_id": facture_id}, {"_id": 0}
        ).to_list(200)
        lignes_fac_map = {lg["ligne_id"]: lg for lg in lignes_fac}

        # Quantités déjà colisées (excluant ce colis)
        qtés_colisées = await _get_quantites_colisees(db, facture_id, exclude_colis_id=colis_id)

        for ligne in payload.lignes:
            lg_fac = lignes_fac_map.get(ligne.ligne_facture_id)
            if not lg_fac:
                raise HTTPException(status_code=404, detail=f"Ligne facture '{ligne.ligne_facture_id}' introuvable")
            qte_max = lg_fac["quantite"]
            qte_deja = qtés_colisées.get(ligne.ligne_facture_id, 0)
            qte_restante = qte_max - qte_deja
            if ligne.quantite_colisee > qte_restante:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quantité colisée ({ligne.quantite_colisee}) > quantité restante ({qte_restante}) "
                           f"pour '{lg_fac['designation']}'."
                )

        lignes_doc = []
        for ligne in payload.lignes:
            lg_fac = lignes_fac_map[ligne.ligne_facture_id]
            lignes_doc.append({
                "ligne_facture_id": ligne.ligne_facture_id,
                "produit_id": ligne.produit_id,
                "designation": ligne.designation or lg_fac.get("designation", ""),
                "quantite_facturee": lg_fac["quantite"],
                "quantite_colisee": ligne.quantite_colisee,
                "poids_unitaire": ligne.poids_unitaire,
                "poids_total": ligne.poids_total,
            })

        update_data = {
            "lignes": lignes_doc,
            "poids_total": payload.poids_total,
            "dimensions": payload.dimensions,
            "notes": payload.notes,
            "updated_at": _now_iso()
        }
        await db.colis.update_one({"colis_id": colis_id}, {"$set": update_data})
        await _log_historique(db, colis_id, "modification", user["user_id"], {"champs": list(update_data.keys())})

        updated = await db.colis.find_one({"colis_id": colis_id}, {"_id": 0})
        logger.info(f"Colis {colis_id} modifié par {user['email']}")
        return updated

    @router.patch("/colis/{colis_id}/statut")
    async def update_colis_statut(
        colis_id: str,
        payload: ColisStatutIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Changer le statut d'un colis.
        Transitions autorisées:
          en_preparation → valide (VALIDATE_ROLES)
          en_preparation | valide → annule (VALIDATE_ROLES)
          valide → expedie (géré automatiquement par livraisons_module)
        """
        user = await resolve_user(request, authorization)

        STATUTS_VALIDES = ["en_preparation", "valide", "expedie", "annule"]
        if payload.statut not in STATUTS_VALIDES:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs: {STATUTS_VALIDES}")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")

        ancien_statut = existing["statut"]

        # Vérifier les transitions
        if payload.statut == "valide":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Validation réservée aux gestionnaires/admins")
            if ancien_statut != "en_preparation":
                raise HTTPException(status_code=400, detail=f"Impossible de valider un colis '{ancien_statut}'")

        elif payload.statut == "annule":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Annulation réservée aux gestionnaires/admins")
            if ancien_statut in ("expedie",):
                raise HTTPException(status_code=400, detail="Impossible d'annuler un colis expédié")

        elif payload.statut == "expedie":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Expédition réservée aux gestionnaires/admins")
            if ancien_statut != "valide":
                raise HTTPException(status_code=400, detail="Seul un colis validé peut être expédié")

        update_data = {"statut": payload.statut, "updated_at": _now_iso()}
        await db.colis.update_one({"colis_id": colis_id}, {"$set": update_data})
        await _log_historique(db, colis_id, f"statut_{payload.statut}", user["user_id"], {
            "ancien": ancien_statut,
            "nouveau": payload.statut,
            "motif": payload.motif or ""
        })

        logger.info(f"Colis {colis_id}: {ancien_statut} → {payload.statut} par {user['email']}")
        return {"message": f"Statut mis à jour: {ancien_statut} → {payload.statut}", "statut": payload.statut}

    @router.delete("/colis/{colis_id}")
    async def delete_colis(
        colis_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Supprimer un colis (uniquement en_preparation)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        if existing["statut"] in ("valide", "expedie"):
            raise HTTPException(status_code=400, detail=f"Impossible de supprimer un colis '{existing['statut']}'")

        await db.colis.delete_one({"colis_id": colis_id})
        await db.mouvements_colis.insert_one({
            "mouvement_id": f"mouv_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:20]}",
            "colis_id": colis_id,
            "type_mouvement": "suppression",
            "details": {"reference": existing.get("reference"), "statut_avant": existing.get("statut")},
            "user_id": user["user_id"],
            "timestamp": _now_iso()
        })

        logger.info(f"Colis {colis_id} supprimé par {user['email']}")
        return {"message": "Colis supprimé avec succès"}

    # ============================================================================
    # STATS COLISAGE PAR FACTURE
    # ============================================================================

    @router.get("/stats/facture/{facture_id}")
    async def stats_colisage_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Résumé des quantités facturées/colisées/restantes pour une facture"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")

        lignes_fac = await db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0}).to_list(200)
        qtés_colisées = await _get_quantites_colisees(db, facture_id)

        stats = []
        total_facture = 0
        total_colise = 0
        for lg in lignes_fac:
            qte_fac = lg["quantite"]
            qte_col = qtés_colisées.get(lg["ligne_id"], 0)
            total_facture += qte_fac
            total_colise += qte_col
            stats.append({
                "ligne_id": lg["ligne_id"],
                "produit_id": lg["produit_id"],
                "designation": lg["designation"],
                "quantite_facturee": qte_fac,
                "quantite_colisee": qte_col,
                "quantite_restante": max(0, qte_fac - qte_col),
                "colisage_complet": qte_col >= qte_fac,
            })

        nb_colis = await db.colis.count_documents({"facture_id": facture_id, "statut": {"$ne": "annule"}})
        return {
            "facture_id": facture_id,
            "facture_reference": facture.get("reference"),
            "statut_facture": facture.get("statut"),
            "nb_colis": nb_colis,
            "total_quantite_facturee": total_facture,
            "total_quantite_colisee": total_colise,
            "total_quantite_restante": max(0, total_facture - total_colise),
            "colisage_complet": total_colise >= total_facture,
            "lignes": stats,
        }

    # ============================================================================
    # MOUVEMENTS / TRAÇABILITÉ
    # ============================================================================

    # ============================================================================
    # EXPÉDITIONS
    # ============================================================================

    class AdresseLivraison(BaseModel):
        nom: str
        adresse: str
        ville: str
        pays: str = "Côte d'Ivoire"
        telephone: Optional[str] = None

    class ExpeditionIn(BaseModel):
        colis_ids: List[str]
        commande_id: Optional[str] = None
        adresse_livraison: AdresseLivraison
        date_expedition: Optional[str] = None
        date_livraison_prevue: Optional[str] = None
        notes: Optional[str] = None

    @router.get("/expeditions")
    async def list_expeditions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut
        if q:
            filters["$or"] = [
                {"reference": {"$regex": q, "$options": "i"}},
                {"adresse_livraison.nom": {"$regex": q, "$options": "i"}},
                {"adresse_livraison.ville": {"$regex": q, "$options": "i"}},
            ]

        cursor = db.expeditions.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        total = await db.expeditions.count_documents(filters)
        return {"items": docs, "total": total}

    @router.get("/expeditions/{expedition_id}")
    async def get_expedition(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        doc = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Expédition introuvable")
        return doc

    @router.post("/expeditions", status_code=201)
    async def create_expedition(
        payload: ExpeditionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        import uuid as _uuid
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        _ensure(len(payload.colis_ids) > 0, 400, "Au moins un colis requis")

        # Vérifier que tous les colis existent et sont valides
        for colis_id in payload.colis_ids:
            colis = await db.colis.find_one({"colis_id": colis_id}, {"_id": 0, "statut": 1})
            _ensure(colis is not None, 404, f"Colis introuvable : {colis_id}")
            _ensure(colis["statut"] in ("valide", "en_preparation"), 400, f"Colis {colis_id} non prêt à être expédié (statut: {colis['statut']})")

        counter = await _next_counter(db, "expeditions")
        now = _now_iso()
        year = now[:4]
        expedition_id = f"exp_{_uuid.uuid4().hex[:12]}"
        reference = f"FABS-EXP-{year[2:]}-{counter:04d}"

        doc = {
            "expedition_id": expedition_id,
            "reference": reference,
            "colis_ids": payload.colis_ids,
            "commande_id": payload.commande_id,
            "adresse_livraison": payload.adresse_livraison.dict(),
            "statut": "en_preparation",
            "date_expedition": payload.date_expedition or now[:10],
            "date_livraison_prevue": payload.date_livraison_prevue,
            "date_livraison_reelle": None,
            "notes": payload.notes,
            "created_by": user["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.expeditions.insert_one(doc)

        # Passer les colis en statut "expedie"
        for colis_id in payload.colis_ids:
            await db.colis.update_one(
                {"colis_id": colis_id},
                {"$set": {"statut": "expedie", "expedition_id": expedition_id, "updated_at": now}}
            )
            await _log_historique(db, colis_id, "EXPEDIE", user["user_id"],
                                  {"expedition_id": expedition_id, "reference": reference})

        doc.pop("_id", None)
        return doc

    @router.patch("/expeditions/{expedition_id}/statut")
    async def update_expedition_statut(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: str = Query(...),
        date_livraison_reelle: Optional[str] = Query(None),
    ):
        STATUTS_VALIDES = {"en_preparation", "pret", "en_transit", "livre", "annule"}
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        exp = await db.expeditions.find_one({"expedition_id": expedition_id}, {"_id": 0})
        _ensure(exp is not None, 404, "Expédition introuvable")
        _ensure(statut in STATUTS_VALIDES, 400, f"Statut invalide : {statut}")

        now = _now_iso()
        update = {"statut": statut, "updated_at": now}
        if statut == "livre":
            update["date_livraison_reelle"] = date_livraison_reelle or now[:10]
            # Passer les colis en "livre"
            for colis_id in exp.get("colis_ids", []):
                await db.colis.update_one(
                    {"colis_id": colis_id},
                    {"$set": {"statut": "livre", "updated_at": now}}
                )
                await _log_historique(db, colis_id, "LIVRE", user["user_id"],
                                      {"expedition_id": expedition_id})

        await db.expeditions.update_one({"expedition_id": expedition_id}, {"$set": update})
        exp.update(update)
        return exp

    # ============================================================================

    @router.get("/mouvements")
    async def list_mouvements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        colis_id: Optional[str] = None,
        type_mouvement: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les mouvements de colis (traçabilité)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if colis_id:
            filters["colis_id"] = colis_id
        if type_mouvement:
            filters["type_mouvement"] = type_mouvement

        cursor = db.mouvements_colis.find(filters, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        for d in docs:
            d.pop("_id", None)
        return docs

    return router
