"""
Module Colisage v2 - Workflow: Commande → Facture → Ordre Colisage → Cartons → Livraison/Expédition → Clôture
Colisage basé sur CARTONS/CONDITIONNEMENT (pas sur le poids).
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field, field_validator
from sanitizers import sanitize_str
from typing import Optional, List, Literal
from datetime import datetime, timezone
import math
import uuid
import logging

logger = logging.getLogger("fabsci.colisage")

# ============================================================================
# CONSTANTES RÔLES
# ============================================================================

READ_ROLES = [
    "super_admin", "admin", "gestionnaire", "preparateur",
    "directeur_commercial", "directeur_general", "comptable", "livreur"
]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire", "preparateur"]
VALIDATE_ROLES = ["super_admin", "admin", "gestionnaire"]
DELETE_ROLES = ["super_admin", "admin"]
DELIVERY_ROLES = ["super_admin", "admin", "gestionnaire", "livreur"]

STATUTS_FACTURE_AUTORISES = ["emise", "partiellement_payee", "payee"]

COLISAGE_NOTIF_ROLES = [
    "super_admin", "admin", "gestionnaire", "preparateur", "directeur_general"
]

# ============================================================================
# SCHEMAS — ORDRE DE COLISAGE
# ============================================================================

StatutOrdreColisage = Literal[
    "a_coliser", "en_preparation", "colisage_termine", "livre", "expedie", "cloture"
]

class OrdreColisageIn(BaseModel):
    """Créé manuellement ou automatiquement à l'émission d'une facture."""
    # P5 — validation stricte des champs string libres
    facture_id: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class OrdreColisageUpdate(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=1000)
    transporteur: Optional[str] = Field(default=None, min_length=2, max_length=120)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


# ============================================================================
# SCHEMAS — CARTON
# ============================================================================

class LigneCarton(BaseModel):
    produit_id: str = Field(..., min_length=3, max_length=64)
    designation: str = Field(..., min_length=1, max_length=255)
    quantite: int = Field(gt=0, le=100000)


class CartonIn(BaseModel):
    ordre_colisage_id: str = Field(..., min_length=3, max_length=64)
    lignes: List[LigneCarton] = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class CartonStatutIn(BaseModel):
    statut: str = Field(..., min_length=2, max_length=50)
    motif: Optional[str] = Field(default=None, max_length=500)


# ============================================================================
# SCHEMAS — LIVRAISON DIRECTE
# ============================================================================

StatutLivraison = Literal[
    "a_charger", "charge", "en_livraison", "livre", "incident", "annule"
]

class LivraisonDirecteIn(BaseModel):
    ordre_colisage_id: str = Field(..., min_length=3, max_length=64)
    livreur_nom: str = Field(..., min_length=2, max_length=120)
    livreur_telephone: Optional[str] = Field(default=None, max_length=30)
    vehicule: Optional[str] = Field(default=None, max_length=80)
    date_depart: Optional[str] = Field(default=None, max_length=30)
    date_prevue: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class ReceptionLivraisonIn(BaseModel):
    nom_receptionnaire: str = Field(..., min_length=2, max_length=120)
    telephone: Optional[str] = Field(default=None, max_length=30)
    commentaire: Optional[str] = Field(default=None, max_length=1000)
    photo_url: Optional[str] = Field(default=None, max_length=512)

    _san_commentaire = field_validator("commentaire", mode="before")(sanitize_str)


class IncidentIn(BaseModel):
    type_incident: Literal[
        "client_absent", "adresse_introuvable", "telephone_injoignable",
        "refus_colis", "colis_manquant", "colis_deteriore", "erreur_livraison", "autre"
    ]
    description: Optional[str] = Field(default=None, max_length=1000)

    _san_description = field_validator("description", mode="before")(sanitize_str)


# ============================================================================
# SCHEMAS — EXPÉDITION
# ============================================================================

StatutExpedition = Literal[
    "expedie", "arrive_destination", "client_informe", "client_recupere", "cloture", "annule"
]

class ExpeditionIn(BaseModel):
    ordre_colisage_id: str = Field(..., min_length=3, max_length=64)
    transporteur: str = Field(..., min_length=2, max_length=120)
    gare_compagnie: Optional[str] = Field(default=None, max_length=120)
    numero_bordereau: Optional[str] = Field(default=None, max_length=80)
    ville_destination: str = Field(..., min_length=2, max_length=100)
    date_expedition: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class ReceptionExpeditionIn(BaseModel):
    date_arrivee: Optional[str] = Field(default=None, max_length=30)
    nom_receptionnaire: Optional[str] = Field(default=None, max_length=120)
    telephone: Optional[str] = Field(default=None, max_length=30)
    commentaire: Optional[str] = Field(default=None, max_length=1000)

    _san_commentaire = field_validator("commentaire", mode="before")(sanitize_str)


class RecuperationExpeditionIn(BaseModel):
    client_recupere: bool
    date_recuperation: Optional[str] = Field(default=None, max_length=30)
    commentaire: Optional[str] = Field(default=None, max_length=1000)

    _san_commentaire = field_validator("commentaire", mode="before")(sanitize_str)


# ============================================================================
# SCHEMAS — LEGACY COMPAT (conservé pour rétrocompatibilité)
# ============================================================================

class LigneColis(BaseModel):
    ligne_facture_id: str = Field(..., min_length=3, max_length=64)
    produit_id: str = Field(..., min_length=3, max_length=64)
    designation: str = Field(..., min_length=1, max_length=255)
    quantite_facturee: int = Field(gt=0, le=100000)
    quantite_colisee: int = Field(gt=0, le=100000)
    poids_unitaire: float = Field(ge=0, default=0.0)
    poids_total: float = Field(ge=0, default=0.0)


class ColisIn(BaseModel):
    facture_id: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    lignes: List[LigneColis] = Field(..., min_length=1, max_length=500)
    poids_total: float = Field(ge=0, default=0.0)
    dimensions: Optional[dict] = None
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class ColisUpdate(BaseModel):
    lignes: List[LigneColis] = Field(..., min_length=1, max_length=500)
    poids_total: float = Field(ge=0, default=0.0)
    dimensions: Optional[dict] = None
    notes: Optional[str] = Field(default=None, max_length=1000)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class ColisStatutIn(BaseModel):
    statut: str = Field(..., min_length=2, max_length=50)
    motif: Optional[str] = Field(default=None, max_length=500)


# ============================================================================
# HELPERS
# ============================================================================

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _generate_qr_code(entity_type: str, entity_id: str) -> str:
    return f"https://erp.fabsci.ci/{entity_type}/{entity_id}"


def _generate_code_barres() -> str:
    import random
    return f"{random.randint(1000000000000, 9999999999999)}"


async def _next_counter(db, name: str) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]


def _gen_reference(prefix: str, year2: str, counter: int) -> str:
    return f"{prefix}-{year2}-{counter:05d}"


async def _log_historique(db, collection: str, doc_id: str, id_field: str,
                           action: str, user_id: str, details: dict = None):
    now = _now_iso()
    await db[collection].update_one(
        {id_field: doc_id},
        {"$push": {"historique": {
            "action": action,
            "user_id": user_id,
            "timestamp": now,
            "details": details or {}
        }}}
    )


async def _notify_colisage_roles(db, titre: str, message: str, lien: str,
                                   exclude_user_id: str = None):
    """Notifier tous les utilisateurs des rôles colisage."""
    try:
        import asyncio as _aio
        from notifications_module import _send_notification
        cursor = db.users.find(
            {"role": {"$in": COLISAGE_NOTIF_ROLES}, "actif": True},
            {"user_id": 1, "_id": 0}
        )
        users = await cursor.to_list(500)
        tasks = []
        for u in users:
            uid = u.get("user_id")
            if uid and (not exclude_user_id or uid != exclude_user_id):
                tasks.append(_send_notification(
                    db, uid, "info", "livraison", titre, message, lien
                ))
        if tasks:
            await _aio.gather(*tasks, return_exceptions=True)
    except Exception as exc:
        logger.warning(f"notify_colisage_roles failed: {exc}")


async def _get_quantites_colisees(db, facture_id: str, exclude_colis_id: str = None) -> dict:
    """Retourne {ligne_facture_id: qte_colisee} pour les colis actifs d'une facture."""
    filters = {"facture_id": facture_id, "statut": {"$ne": "annule"}}
    if exclude_colis_id:
        filters["colis_id"] = {"$ne": exclude_colis_id}
    colis_list = await db.colis.find(filters, {"_id": 0, "lignes": 1}).to_list(200)
    qtés = {}
    for colis in colis_list:
        for ligne in colis.get("lignes", []):
            lid = ligne.get("ligne_facture_id")
            if lid:
                qtés[lid] = qtés.get(lid, 0) + ligne.get("quantite_colisee", 0)
    return qtés


# ============================================================================
# CALCUL AUTOMATIQUE DES CARTONS
# ============================================================================

async def _calculer_cartons_depuis_ordre(db, ordre_colisage_id: str) -> List[dict]:
    """
    Génère la liste des cartons à créer à partir d'un ordre de colisage.
    Utilise le conditionnement_carton de chaque produit.
    """
    ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_colisage_id}, {"_id": 0})
    if not ordre:
        return []

    facture_id = ordre["facture_id"]
    lignes_fac = await db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0}).to_list(200)

    cartons_a_creer = []
    for ligne in lignes_fac:
        produit_id = ligne.get("produit_id")
        qte_total = ligne.get("quantite", 0)
        designation = ligne.get("designation", "")

        # Récupérer le conditionnement depuis la fiche produit
        produit = await db.produits.find_one(
            {"produit_id": produit_id},
            {"_id": 0, "conditionnement_carton": 1, "titre": 1, "designation": 1}
        )
        conditionnement = 1
        if produit:
            conditionnement = produit.get("conditionnement_carton") or 1

        nb_cartons = math.ceil(qte_total / conditionnement) if qte_total > 0 else 0
        for i in range(nb_cartons):
            qte_ce_carton = min(conditionnement, qte_total - i * conditionnement)
            cartons_a_creer.append({
                "produit_id": produit_id,
                "designation": designation,
                "quantite_par_carton": conditionnement,
                "quantite": qte_ce_carton,
                "numero_carton": i + 1,
                "total_cartons": nb_cartons,
            })

    return cartons_a_creer


# ============================================================================
# ROUTER
# ============================================================================

def build_colisage_router(db, resolve_user, log_audit_event=None):
    router = APIRouter(prefix="/colisage", tags=["colisage"])

    year2 = datetime.now().strftime("%y")

    # =========================================================================
    # ORDRES DE COLISAGE
    # =========================================================================

    @router.get("/ordres")
    async def list_ordres_colisage(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0),
    ):
        """Lister les ordres de colisage."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut

        pipeline = [
            {"$match": filters},
            {"$lookup": {
                "from": "factures",
                "localField": "facture_id",
                "foreignField": "facture_id",
                "as": "facture_info"
            }},
            {"$addFields": {
                "facture_reference": {"$arrayElemAt": ["$facture_info.reference", 0]},
                "client_id_fac": {"$arrayElemAt": ["$facture_info.client_id", 0]},
            }},
            {"$lookup": {
                "from": "clients",
                "localField": "client_id_fac",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
            }},
            {"$project": {"facture_info": 0, "client_info": 0, "client_id_fac": 0, "_id": 0}},
        ]

        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"facture_reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
            ]}})

        pipeline += [{"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}]
        docs = await db.ordres_colisage.aggregate(pipeline).to_list(limit)
        for d in docs:
            d.pop("_id", None)

        total = await db.ordres_colisage.count_documents(filters)
        return {"items": docs, "total": total}

    @router.get("/ordres/dashboard")
    async def dashboard_colisage(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Tableau de bord KPIs colisage."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        stats = {}
        for statut in ["a_coliser", "en_preparation", "colisage_termine", "livre", "expedie", "cloture"]:
            stats[statut] = await db.ordres_colisage.count_documents({"statut": statut})

        stats["total_ordres"] = sum(stats.values())
        stats["cartons_en_preparation"] = await db.cartons_colisage.count_documents(
            {"statut": "en_preparation"}
        )
        stats["cartons_valides"] = await db.cartons_colisage.count_documents({"statut": "valide"})
        stats["livraisons_en_cours"] = await db.livraisons_directes.count_documents(
            {"statut": {"$in": ["a_charger", "charge", "en_livraison"]}}
        )
        stats["expeditions_en_cours"] = await db.expeditions_colisage.count_documents(
            {"statut": {"$in": ["expedie", "arrive_destination", "client_informe"]}}
        )
        return stats

    @router.get("/ordres/{ordre_id}")
    async def get_ordre_colisage(
        ordre_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Détail d'un ordre de colisage avec ses cartons."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        pipeline = [
            {"$match": {"ordre_colisage_id": ordre_id}},
            {"$lookup": {
                "from": "factures",
                "localField": "facture_id",
                "foreignField": "facture_id",
                "as": "facture_info"
            }},
            {"$addFields": {
                "facture_reference": {"$arrayElemAt": ["$facture_info.reference", 0]},
                "client_id_fac": {"$arrayElemAt": ["$facture_info.client_id", 0]},
                "montant_ttc": {"$arrayElemAt": ["$facture_info.montant_ttc", 0]},
            }},
            {"$lookup": {
                "from": "clients",
                "localField": "client_id_fac",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_adresse": {"$arrayElemAt": ["$client_info.adresse", 0]},
            }},
            {"$project": {"facture_info": 0, "client_info": 0, "client_id_fac": 0, "_id": 0}},
        ]
        docs = await db.ordres_colisage.aggregate(pipeline).to_list(1)
        if not docs:
            raise HTTPException(status_code=404, detail="Ordre de colisage introuvable")
        ordre = docs[0]
        ordre.pop("_id", None)

        # Récupérer les cartons de cet ordre
        cartons = await db.cartons_colisage.find(
            {"ordre_colisage_id": ordre_id}, {"_id": 0}
        ).sort("numero_carton", 1).to_list(500)

        # Récupérer les lignes de la facture pour le résumé
        lignes_fac = await db.facture_lignes.find(
            {"facture_id": ordre["facture_id"]}, {"_id": 0}
        ).to_list(200)

        ordre["cartons"] = cartons
        ordre["nb_cartons"] = len(cartons)
        ordre["nb_cartons_valides"] = sum(1 for c in cartons if c.get("statut") == "valide")
        ordre["lignes_facture"] = lignes_fac

        return ordre

    @router.post("/ordres", status_code=201)
    async def create_ordre_colisage(
        payload: OrdreColisageIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Créer manuellement un ordre de colisage pour une facture émise."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": payload.facture_id}, {"_id": 0})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")
        if facture["statut"] not in STATUTS_FACTURE_AUTORISES:
            raise HTTPException(
                status_code=400,
                detail=f"Facture doit être émise (statut actuel: {facture['statut']})"
            )

        # Vérifier qu'il n'existe pas déjà un OC non clôturé pour cette facture
        existing_oc = await db.ordres_colisage.find_one({
            "facture_id": payload.facture_id,
            "statut": {"$nin": ["cloture", "annule"]}
        })
        if existing_oc:
            raise HTTPException(
                status_code=409,
                detail=f"Un ordre de colisage existe déjà: {existing_oc.get('reference')}"
            )

        result = await _create_ordre_colisage_internal(db, payload.facture_id, user["user_id"], payload.notes)
        # TICKET-016 — audit
        if log_audit_event:
            await log_audit_event(
                user_id=user["user_id"],
                action="CREATE_ORDRE_COLISAGE",
                resource_type="ordre_colisage",
                resource_id=result.get("ordre_colisage_id", ""),
                details={"facture_id": payload.facture_id, "notes": payload.notes},
                ip_address=request.client.host if request.client else None,
            )
        return result

    @router.patch("/ordres/{ordre_id}/statut")
    async def update_ordre_statut(
        ordre_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: str = Query(...),
        motif: Optional[str] = Query(None),
    ):
        """Changer le statut d'un ordre de colisage."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in VALIDATE_ROLES, 403, "Accès refusé")

        STATUTS_VALIDES = ["a_coliser", "en_preparation", "colisage_termine", "livre", "expedie", "cloture"]
        _ensure(statut in STATUTS_VALIDES, 400, f"Statut invalide: {statut}")

        ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_id})
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre introuvable")

        ancien_statut = ordre["statut"]
        now = _now_iso()

        update_data = {
            "statut": statut,
            "updated_at": now,
        }
        if statut == "colisage_termine":
            update_data["date_colisage_termine"] = now
            update_data["colisage_par"] = user["user_id"]
        elif statut == "cloture":
            update_data["date_cloture"] = now
            update_data["cloture_par"] = user["user_id"]

        await db.ordres_colisage.update_one(
            {"ordre_colisage_id": ordre_id},
            {"$set": update_data}
        )
        await _log_historique(db, "ordres_colisage", ordre_id, "ordre_colisage_id",
                               f"statut_{statut}", user["user_id"],
                               {"ancien": ancien_statut, "nouveau": statut, "motif": motif or ""})

        # Notification si colisage terminé
        if statut == "colisage_termine":
            await _notify_colisage_roles(
                db,
                titre=f"Colisage terminé — {ordre.get('reference')}",
                message=f"L'ordre {ordre.get('reference')} est prêt. Choisissez livraison ou expédition.",
                lien=f"/ordres-colisage/{ordre_id}",
                exclude_user_id=user["user_id"]
            )

        # TICKET-016 — audit
        if log_audit_event:
            await log_audit_event(
                user_id=user["user_id"],
                action="UPDATE_STATUT_ORDRE_COLISAGE",
                resource_type="ordre_colisage",
                resource_id=ordre_id,
                details={
                    "old_statut": ancien_statut,
                    "new_statut": statut,
                    "motif": motif or "",
                    "reference": ordre.get("reference"),
                },
                ip_address=request.client.host if request.client else None,
            )
        logger.info(f"Ordre {ordre_id}: {ancien_statut} → {statut} par {user['email']}")
        return {"message": f"Statut: {ancien_statut} → {statut}", "statut": statut}

    @router.get("/ordres/{ordre_id}/cartons-suggeres")
    async def get_cartons_suggeres(
        ordre_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Calculer les cartons suggérés selon le conditionnement des produits."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_id}, {"_id": 0})
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre introuvable")

        lignes_fac = await db.facture_lignes.find(
            {"facture_id": ordre["facture_id"]}, {"_id": 0}
        ).to_list(200)

        result = []
        total_cartons = 0
        for ligne in lignes_fac:
            produit_id = ligne.get("produit_id")
            qte_total = ligne.get("quantite", 0)
            designation = ligne.get("designation", "")

            produit = await db.produits.find_one(
                {"produit_id": produit_id},
                {"_id": 0, "conditionnement_carton": 1}
            )
            conditionnement = (produit or {}).get("conditionnement_carton") or 1
            nb_cartons = math.ceil(qte_total / conditionnement) if qte_total > 0 else 0
            total_cartons += nb_cartons

            detail_cartons = []
            for i in range(nb_cartons):
                qte_ce_carton = min(conditionnement, qte_total - i * conditionnement)
                detail_cartons.append({
                    "numero": i + 1,
                    "total": nb_cartons,
                    "quantite": qte_ce_carton,
                })

            result.append({
                "produit_id": produit_id,
                "designation": designation,
                "quantite_totale": qte_total,
                "conditionnement_carton": conditionnement,
                "nb_cartons": nb_cartons,
                "cartons": detail_cartons,
            })

        return {
            "ordre_colisage_id": ordre_id,
            "nb_cartons_total": total_cartons,
            "lignes": result
        }

    # =========================================================================
    # CARTONS
    # =========================================================================

    @router.get("/cartons")
    async def list_cartons(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        ordre_colisage_id: Optional[str] = None,
        statut: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(100, le=500),
        skip: int = Query(0, ge=0),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if ordre_colisage_id:
            filters["ordre_colisage_id"] = ordre_colisage_id
        if statut:
            filters["statut"] = statut
        if q:
            filters["$or"] = [
                {"reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
            ]

        docs = await db.cartons_colisage.find(
            filters, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        total = await db.cartons_colisage.count_documents(filters)
        return {"items": docs, "total": total}

    @router.get("/cartons/{carton_id}")
    async def get_carton(
        carton_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Détail d'un carton. Accessible via QR Code sans auth (lecture publique minimale)."""
        # Auth optionnelle pour le scan QR
        try:
            user = await resolve_user(request, authorization)
            _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        except HTTPException as e:
            if e.status_code == 401:
                # Scan QR public : retourner uniquement les infos non sensibles
                carton = await db.cartons_colisage.find_one({"carton_id": carton_id}, {"_id": 0})
                if not carton:
                    raise HTTPException(status_code=404, detail="Carton introuvable")
                return {k: v for k, v in carton.items()
                        if k in ["carton_id", "reference", "client_nom", "client_ville",
                                 "facture_reference", "commande_reference", "numero_carton",
                                 "total_cartons", "lignes", "statut", "colise_le", "qr_code"]}
            raise

        carton = await db.cartons_colisage.find_one({"carton_id": carton_id}, {"_id": 0})
        if not carton:
            raise HTTPException(status_code=404, detail="Carton introuvable")
        return carton

    @router.post("/cartons/generer-automatique/{ordre_id}", status_code=201)
    async def generer_cartons_automatique(
        ordre_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """
        Génère automatiquement les cartons d'un ordre de colisage
        en se basant sur le conditionnement des produits.
        """
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_id}, {"_id": 0})
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre introuvable")
        if ordre["statut"] not in ("a_coliser", "en_preparation"):
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de générer des cartons pour un ordre '{ordre['statut']}'"
            )

        # Supprimer les cartons existants non validés
        await db.cartons_colisage.delete_many({
            "ordre_colisage_id": ordre_id,
            "statut": {"$in": ["en_preparation", "en_attente"]}
        })

        # Récupérer les lignes facture
        lignes_fac = await db.facture_lignes.find(
            {"facture_id": ordre["facture_id"]}, {"_id": 0}
        ).to_list(200)

        # Récupérer les infos client via facture
        facture = await db.factures.find_one({"facture_id": ordre["facture_id"]}, {"_id": 0})
        client = {}
        if facture:
            client = await db.clients.find_one(
                {"client_id": facture.get("client_id")}, {"_id": 0}
            ) or {}

        now = _now_iso()
        cartons_crees = []
        global_carton_num = 1
        total_cartons_global = 0

        # Calcul du total global
        lignes_avec_cond = []
        for ligne in lignes_fac:
            produit_id = ligne.get("produit_id")
            qte_total = ligne.get("quantite", 0)
            produit = await db.produits.find_one(
                {"produit_id": produit_id},
                {"_id": 0, "conditionnement_carton": 1}
            )
            conditionnement = (produit or {}).get("conditionnement_carton") or 1
            nb_cartons = math.ceil(qte_total / conditionnement) if qte_total > 0 else 0
            total_cartons_global += nb_cartons
            lignes_avec_cond.append((ligne, conditionnement, nb_cartons))

        # Créer les cartons
        for ligne, conditionnement, nb_cartons in lignes_avec_cond:
            if nb_cartons == 0:
                continue
            produit_id = ligne.get("produit_id")
            qte_total = ligne.get("quantite", 0)
            designation = ligne.get("designation", "")

            counter = await _next_counter(db, "cartons_colisage")
            for i in range(nb_cartons):
                qte_ce_carton = min(conditionnement, qte_total - i * conditionnement)
                carton_id = f"carton_{uuid.uuid4().hex[:12]}"
                ref_carton = _gen_reference("FABS-CAR", year2, counter + i)
                qr = _generate_qr_code("carton", carton_id)

                carton_doc = {
                    "carton_id": carton_id,
                    "reference": ref_carton,
                    "ordre_colisage_id": ordre_id,
                    "ordre_reference": ordre.get("reference"),
                    "facture_id": ordre["facture_id"],
                    "facture_reference": facture.get("reference") if facture else None,
                    "client_id": client.get("client_id"),
                    "client_nom": client.get("nom"),
                    "client_ville": client.get("ville"),
                    "client_adresse": client.get("adresse"),
                    "client_telephone": client.get("telephone"),
                    "numero_carton": global_carton_num,
                    "total_cartons": total_cartons_global,
                    "lignes": [{
                        "produit_id": produit_id,
                        "designation": designation,
                        "quantite_par_carton": conditionnement,
                        "quantite": qte_ce_carton,
                    }],
                    "statut": "en_preparation",
                    "qr_code": qr,
                    "code_barres": _generate_code_barres(),
                    "colise_par": None,
                    "colise_le": None,
                    "notes": None,
                    "created_at": now,
                    "created_by": user["user_id"],
                    "updated_at": now,
                }
                await db.cartons_colisage.insert_one(carton_doc)
                carton_doc.pop("_id", None)
                cartons_crees.append(carton_doc)
                global_carton_num += 1

        # Passer l'ordre en "en_preparation"
        await db.ordres_colisage.update_one(
            {"ordre_colisage_id": ordre_id},
            {"$set": {
                "statut": "en_preparation",
                "nb_cartons": len(cartons_crees),
                "updated_at": now
            }}
        )
        await _log_historique(db, "ordres_colisage", ordre_id, "ordre_colisage_id",
                               "cartons_generes", user["user_id"],
                               {"nb_cartons": len(cartons_crees)})

        logger.info(f"OC {ordre_id}: {len(cartons_crees)} cartons générés par {user['email']}")
        return {
            "message": f"{len(cartons_crees)} cartons générés",
            "nb_cartons": len(cartons_crees),
            "cartons": cartons_crees
        }

    @router.patch("/cartons/{carton_id}/valider")
    async def valider_carton(
        carton_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Valider un carton (préparateur confirme son contenu)."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        carton = await db.cartons_colisage.find_one({"carton_id": carton_id})
        if not carton:
            raise HTTPException(status_code=404, detail="Carton introuvable")
        if carton["statut"] != "en_preparation":
            raise HTTPException(status_code=400, detail=f"Carton déjà '{carton['statut']}'")

        now = _now_iso()
        await db.cartons_colisage.update_one(
            {"carton_id": carton_id},
            {"$set": {
                "statut": "valide",
                "colise_par": user["user_id"],
                "colise_le": now,
                "updated_at": now,
            }}
        )

        # Vérifier si tous les cartons de l'ordre sont validés
        ordre_id = carton["ordre_colisage_id"]
        total = await db.cartons_colisage.count_documents({"ordre_colisage_id": ordre_id})
        valides = await db.cartons_colisage.count_documents(
            {"ordre_colisage_id": ordre_id, "statut": "valide"}
        )
        if total > 0 and valides >= total:
            await db.ordres_colisage.update_one(
                {"ordre_colisage_id": ordre_id},
                {"$set": {"statut": "colisage_termine", "updated_at": now, "colisage_par": user["user_id"]}}
            )
            ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_id}, {"_id": 0})
            await _notify_colisage_roles(
                db,
                titre=f"Colisage terminé — {ordre.get('reference', ordre_id)}",
                message=f"Tous les cartons sont prêts ({valides}/{total}). Créez une livraison ou expédition.",
                lien=f"/ordres-colisage/{ordre_id}",
                exclude_user_id=user["user_id"]
            )

        return {"message": "Carton validé", "carton_id": carton_id, "colisage_complet": valides >= total}

    @router.delete("/cartons/{carton_id}")
    async def delete_carton(
        carton_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")

        carton = await db.cartons_colisage.find_one({"carton_id": carton_id})
        if not carton:
            raise HTTPException(status_code=404, detail="Carton introuvable")
        if carton["statut"] == "valide":
            raise HTTPException(status_code=400, detail="Impossible de supprimer un carton validé")

        await db.cartons_colisage.delete_one({"carton_id": carton_id})
        return {"message": "Carton supprimé"}

    # =========================================================================
    # LIVRAISONS DIRECTES
    # =========================================================================

    @router.get("/livraisons")
    async def list_livraisons_directes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[str] = None,
        q: Optional[str] = None,
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
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"livreur_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
            ]

        docs = await db.livraisons_directes.find(
            filters, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        total = await db.livraisons_directes.count_documents(filters)
        return {"items": docs, "total": total}

    @router.get("/livraisons/{livraison_id}")
    async def get_livraison_directe(
        livraison_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        doc = await db.livraisons_directes.find_one({"livraison_id": livraison_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Livraison introuvable")
        return doc

    @router.post("/livraisons", status_code=201)
    async def create_livraison_directe(
        payload: LivraisonDirecteIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Créer une livraison directe depuis un ordre de colisage terminé."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        ordre = await db.ordres_colisage.find_one(
            {"ordre_colisage_id": payload.ordre_colisage_id}, {"_id": 0}
        )
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre de colisage introuvable")
        if ordre["statut"] not in ("colisage_termine", "en_preparation"):
            raise HTTPException(
                status_code=400,
                detail=f"L'ordre doit être au moins en préparation (statut: {ordre['statut']})"
            )

        # Récupérer les infos client
        facture = await db.factures.find_one({"facture_id": ordre["facture_id"]}, {"_id": 0})
        client = {}
        if facture:
            client = await db.clients.find_one(
                {"client_id": facture.get("client_id")}, {"_id": 0}
            ) or {}

        counter = await _next_counter(db, "livraisons_directes")
        livraison_id = f"liv_{uuid.uuid4().hex[:12]}"
        reference = _gen_reference("FABS-LIV", year2, counter)
        now = _now_iso()

        # Cartons associés à cet ordre
        cartons = await db.cartons_colisage.find(
            {"ordre_colisage_id": payload.ordre_colisage_id},
            {"_id": 0, "carton_id": 1, "reference": 1, "statut": 1}
        ).to_list(500)

        doc = {
            "livraison_id": livraison_id,
            "reference": reference,
            "ordre_colisage_id": payload.ordre_colisage_id,
            "ordre_reference": ordre.get("reference"),
            "facture_id": ordre.get("facture_id"),
            "facture_reference": facture.get("reference") if facture else None,
            "client_id": client.get("client_id"),
            "client_nom": client.get("nom"),
            "client_ville": client.get("ville"),
            "client_adresse": client.get("adresse"),
            "client_telephone": client.get("telephone"),
            "livreur_nom": payload.livreur_nom,
            "livreur_telephone": payload.livreur_telephone,
            "vehicule": payload.vehicule,
            "date_depart": payload.date_depart or _today(),
            "date_prevue": payload.date_prevue,
            "date_livraison_reelle": None,
            "nb_cartons": len(cartons),
            "cartons": [{"carton_id": c["carton_id"], "reference": c["reference"], "statut": c["statut"]}
                        for c in cartons],
            "cartons_charges": [],
            "statut": "a_charger",
            "reception": None,
            "incidents": [],
            "notes": payload.notes,
            "historique": [{
                "action": "creation",
                "user_id": user["user_id"],
                "timestamp": now,
                "details": {"reference": reference}
            }],
            "created_at": now,
            "created_by": user["user_id"],
            "updated_at": now,
        }
        await db.livraisons_directes.insert_one(doc)
        doc.pop("_id", None)

        # Passer l'ordre en statut "livre" (en cours)
        await db.ordres_colisage.update_one(
            {"ordre_colisage_id": payload.ordre_colisage_id},
            {"$set": {"statut": "livre", "livraison_id": livraison_id, "updated_at": now}}
        )

        await _notify_colisage_roles(
            db,
            titre=f"Livraison créée — {reference}",
            message=f"Livraison {reference} créée pour {client.get('nom', '')} → {client.get('ville', '')}",
            lien=f"/livraisons-directes/{livraison_id}",
            exclude_user_id=user["user_id"]
        )

        logger.info(f"Livraison {reference} créée par {user['email']}")
        return doc

    @router.patch("/livraisons/{livraison_id}/statut")
    async def update_livraison_statut(
        livraison_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: str = Query(...),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELIVERY_ROLES, 403, "Accès refusé")

        STATUTS = ["a_charger", "charge", "en_livraison", "livre", "incident", "annule"]
        _ensure(statut in STATUTS, 400, f"Statut invalide: {statut}")

        liv = await db.livraisons_directes.find_one({"livraison_id": livraison_id})
        if not liv:
            raise HTTPException(status_code=404, detail="Livraison introuvable")

        ancien = liv["statut"]
        now = _now_iso()
        update = {"statut": statut, "updated_at": now}
        if statut == "livre":
            update["date_livraison_reelle"] = now[:10]

        await db.livraisons_directes.update_one({"livraison_id": livraison_id}, {"$set": update})
        await _log_historique(db, "livraisons_directes", livraison_id, "livraison_id",
                               f"statut_{statut}", user["user_id"],
                               {"ancien": ancien, "nouveau": statut})

        if statut == "livre":
            # Passer l'ordre en cloture
            await db.ordres_colisage.update_one(
                {"livraison_id": livraison_id},
                {"$set": {"statut": "cloture", "updated_at": now}}
            )
            await _notify_colisage_roles(
                db,
                titre=f"Livraison effectuée — {liv.get('reference')}",
                message=f"Livraison {liv.get('reference')} livrée à {liv.get('client_nom', '')}.",
                lien=f"/livraisons-directes/{livraison_id}",
                exclude_user_id=user["user_id"]
            )

        return {"message": f"Statut: {ancien} → {statut}", "statut": statut}

    @router.post("/livraisons/{livraison_id}/charger-carton")
    async def charger_carton(
        livraison_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        carton_id: str = Query(...),
    ):
        """Scanner/charger un carton dans le véhicule avant départ."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELIVERY_ROLES, 403, "Accès refusé")

        liv = await db.livraisons_directes.find_one({"livraison_id": livraison_id}, {"_id": 0})
        if not liv:
            raise HTTPException(status_code=404, detail="Livraison introuvable")
        if liv["statut"] not in ("a_charger", "charge"):
            raise HTTPException(status_code=400, detail=f"Livraison en statut '{liv['statut']}', chargement impossible")

        # Vérifier que le carton appartient à cette livraison
        carton_ids = [c["carton_id"] for c in liv.get("cartons", [])]
        if carton_id not in carton_ids:
            raise HTTPException(status_code=400, detail="Ce carton n'appartient pas à cette livraison")

        charges = liv.get("cartons_charges", [])
        if carton_id not in charges:
            charges.append(carton_id)

        now = _now_iso()
        nouveau_statut = "charge" if len(charges) < len(carton_ids) else "charge"
        await db.livraisons_directes.update_one(
            {"livraison_id": livraison_id},
            {"$set": {"cartons_charges": charges, "statut": nouveau_statut, "updated_at": now}}
        )

        manquants = [cid for cid in carton_ids if cid not in charges]
        return {
            "message": "Carton chargé",
            "cartons_charges": len(charges),
            "total_cartons": len(carton_ids),
            "manquants": len(manquants),
            "cartons_manquants": manquants
        }

    @router.post("/livraisons/{livraison_id}/reception")
    async def enregistrer_reception(
        livraison_id: str,
        payload: ReceptionLivraisonIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Enregistrer la réception à la livraison."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELIVERY_ROLES, 403, "Accès refusé")

        liv = await db.livraisons_directes.find_one({"livraison_id": livraison_id})
        if not liv:
            raise HTTPException(status_code=404, detail="Livraison introuvable")

        now = _now_iso()
        reception = {
            "nom_receptionnaire": payload.nom_receptionnaire,
            "telephone": payload.telephone,
            "commentaire": payload.commentaire,
            "photo_url": payload.photo_url,
            "date": now,
            "enregistre_par": user["user_id"],
        }
        await db.livraisons_directes.update_one(
            {"livraison_id": livraison_id},
            {"$set": {
                "reception": reception,
                "statut": "livre",
                "date_livraison_reelle": now[:10],
                "updated_at": now,
            }}
        )
        await _log_historique(db, "livraisons_directes", livraison_id, "livraison_id",
                               "reception_enregistree", user["user_id"],
                               {"receptionnaire": payload.nom_receptionnaire})

        # Clôturer l'ordre
        await db.ordres_colisage.update_one(
            {"livraison_id": livraison_id},
            {"$set": {"statut": "cloture", "updated_at": now}}
        )
        await _notify_colisage_roles(
            db,
            titre=f"Livraison livrée — {liv.get('reference')}",
            message=f"Réceptionnaire: {payload.nom_receptionnaire}. Livraison {liv.get('reference')} clôturée.",
            lien=f"/livraisons-directes/{livraison_id}",
            exclude_user_id=user["user_id"]
        )

        return {"message": "Réception enregistrée", "statut": "livre"}

    @router.post("/livraisons/{livraison_id}/incident")
    async def declarer_incident(
        livraison_id: str,
        payload: IncidentIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Déclarer un incident sur une livraison."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELIVERY_ROLES, 403, "Accès refusé")

        liv = await db.livraisons_directes.find_one({"livraison_id": livraison_id})
        if not liv:
            raise HTTPException(status_code=404, detail="Livraison introuvable")

        now = _now_iso()
        incident = {
            "incident_id": f"inc_{uuid.uuid4().hex[:12]}",  # TICKET-011 : ID unique pour résolution
            "type": payload.type_incident,
            "description": payload.description,
            "date": now,
            "declare_par": user["user_id"],
            "statut_resolution": "ouvert",
            "historique_resolution": [],
        }
        await db.livraisons_directes.update_one(
            {"livraison_id": livraison_id},
            {
                "$push": {"incidents": incident},
                "$set": {"statut": "incident", "updated_at": now}
            }
        )
        await _notify_colisage_roles(
            db,
            titre=f"⚠️ Incident — {liv.get('reference')}",
            message=f"Incident: {payload.type_incident}. {payload.description or ''}",
            lien=f"/livraisons-directes/{livraison_id}",
            exclude_user_id=user["user_id"]
        )

        # TICKET-016 — audit
        if log_audit_event:
            await log_audit_event(
                user_id=user["user_id"],
                action="DECLARE_INCIDENT",
                resource_type="livraison_directe",
                resource_id=livraison_id,
                details={
                    "incident_id": incident["incident_id"],
                    "type_incident": payload.type_incident,
                    "description": payload.description or "",
                    "reference": liv.get("reference"),
                },
                ip_address=request.client.host if request.client else None,
            )
        return {"message": "Incident déclaré", "incident": incident}

    # =========================================================================
    # EXPÉDITIONS
    # =========================================================================

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
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"ville_destination": {"$regex": q, "$options": "i"}},
                {"numero_bordereau": {"$regex": q, "$options": "i"}},
            ]

        docs = await db.expeditions_colisage.find(
            filters, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        total = await db.expeditions_colisage.count_documents(filters)
        return {"items": docs, "total": total}

    @router.get("/expeditions/{expedition_id}")
    async def get_expedition(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        doc = await db.expeditions_colisage.find_one({"expedition_id": expedition_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Expédition introuvable")
        return doc

    @router.post("/expeditions", status_code=201)
    async def create_expedition(
        payload: ExpeditionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Créer une expédition (hors zone de livraison directe)."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        ordre = await db.ordres_colisage.find_one(
            {"ordre_colisage_id": payload.ordre_colisage_id}, {"_id": 0}
        )
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre de colisage introuvable")
        if ordre["statut"] not in ("colisage_termine", "en_preparation"):
            raise HTTPException(
                status_code=400,
                detail=f"L'ordre doit être au moins en préparation (statut: {ordre['statut']})"
            )

        facture = await db.factures.find_one({"facture_id": ordre["facture_id"]}, {"_id": 0})
        client = {}
        if facture:
            client = await db.clients.find_one(
                {"client_id": facture.get("client_id")}, {"_id": 0}
            ) or {}

        counter = await _next_counter(db, "expeditions_colisage")
        expedition_id = f"exp_{uuid.uuid4().hex[:12]}"
        reference = _gen_reference("FABS-EXP", year2, counter)
        now = _now_iso()

        cartons = await db.cartons_colisage.find(
            {"ordre_colisage_id": payload.ordre_colisage_id},
            {"_id": 0, "carton_id": 1, "reference": 1, "statut": 1}
        ).to_list(500)

        doc = {
            "expedition_id": expedition_id,
            "reference": reference,
            "ordre_colisage_id": payload.ordre_colisage_id,
            "ordre_reference": ordre.get("reference"),
            "facture_id": ordre.get("facture_id"),
            "facture_reference": facture.get("reference") if facture else None,
            "client_id": client.get("client_id"),
            "client_nom": client.get("nom"),
            "transporteur": payload.transporteur,
            "gare_compagnie": payload.gare_compagnie,
            "numero_bordereau": payload.numero_bordereau,
            "ville_destination": payload.ville_destination,
            "date_expedition": payload.date_expedition or _today(),
            "nb_cartons": len(cartons),
            "cartons": [{"carton_id": c["carton_id"], "reference": c["reference"]} for c in cartons],
            "statut": "expedie",
            "date_arrivee": None,
            "reception": None,
            "recuperation": None,
            "incidents": [],
            "notes": payload.notes,
            "historique": [{
                "action": "creation",
                "user_id": user["user_id"],
                "timestamp": now,
                "details": {"reference": reference, "ville": payload.ville_destination}
            }],
            "created_at": now,
            "created_by": user["user_id"],
            "updated_at": now,
        }
        await db.expeditions_colisage.insert_one(doc)
        doc.pop("_id", None)

        # Passer l'ordre en "expedie"
        await db.ordres_colisage.update_one(
            {"ordre_colisage_id": payload.ordre_colisage_id},
            {"$set": {"statut": "expedie", "expedition_id": expedition_id, "updated_at": now}}
        )

        await _notify_colisage_roles(
            db,
            titre=f"Expédition créée — {reference}",
            message=f"Expédition {reference} vers {payload.ville_destination} via {payload.transporteur}.",
            lien=f"/expeditions/{expedition_id}",
            exclude_user_id=user["user_id"]
        )

        logger.info(f"Expédition {reference} créée par {user['email']}")
        return doc

    @router.patch("/expeditions/{expedition_id}/statut")
    async def update_expedition_statut(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: str = Query(...),
    ):
        STATUTS = ["expedie", "arrive_destination", "client_informe", "client_recupere", "cloture", "annule"]
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        _ensure(statut in STATUTS, 400, f"Statut invalide: {statut}")

        exp = await db.expeditions_colisage.find_one({"expedition_id": expedition_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        ancien = exp["statut"]
        now = _now_iso()
        update = {"statut": statut, "updated_at": now}

        await db.expeditions_colisage.update_one({"expedition_id": expedition_id}, {"$set": update})
        await _log_historique(db, "expeditions_colisage", expedition_id, "expedition_id",
                               f"statut_{statut}", user["user_id"],
                               {"ancien": ancien, "nouveau": statut})

        if statut in ("client_recupere", "cloture"):
            await db.ordres_colisage.update_one(
                {"expedition_id": expedition_id},
                {"$set": {"statut": "cloture", "updated_at": now}}
            )

        if statut == "arrive_destination":
            await _notify_colisage_roles(
                db,
                titre=f"Expédition arrivée — {exp.get('reference')}",
                message=f"Expédition {exp.get('reference')} arrivée à {exp.get('ville_destination', '')}. Informer le client.",
                lien=f"/expeditions/{expedition_id}",
                exclude_user_id=user["user_id"]
            )

        return {"message": f"Statut: {ancien} → {statut}", "statut": statut}

    @router.post("/expeditions/{expedition_id}/reception")
    async def enregistrer_reception_expedition(
        expedition_id: str,
        payload: ReceptionExpeditionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        exp = await db.expeditions_colisage.find_one({"expedition_id": expedition_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        now = _now_iso()
        reception = {
            "date_arrivee": payload.date_arrivee or now[:10],
            "nom_receptionnaire": payload.nom_receptionnaire,
            "telephone": payload.telephone,
            "commentaire": payload.commentaire,
            "enregistre_le": now,
            "enregistre_par": user["user_id"],
        }
        await db.expeditions_colisage.update_one(
            {"expedition_id": expedition_id},
            {"$set": {
                "reception": reception,
                "date_arrivee": payload.date_arrivee or now[:10],
                "statut": "arrive_destination",
                "updated_at": now
            }}
        )
        await _notify_colisage_roles(
            db,
            titre=f"Expédition arrivée — {exp.get('reference')}",
            message=f"Arrivée confirmée à {exp.get('ville_destination', '')}. À récupérer.",
            lien=f"/expeditions/{expedition_id}",
            exclude_user_id=user["user_id"]
        )
        return {"message": "Réception enregistrée"}

    @router.post("/expeditions/{expedition_id}/recuperation")
    async def enregistrer_recuperation(
        expedition_id: str,
        payload: RecuperationExpeditionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        exp = await db.expeditions_colisage.find_one({"expedition_id": expedition_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        now = _now_iso()
        recuperation = {
            "client_recupere": payload.client_recupere,
            "date_recuperation": payload.date_recuperation or now[:10],
            "commentaire": payload.commentaire,
            "enregistre_le": now,
            "enregistre_par": user["user_id"],
        }
        nouveau_statut = "client_recupere" if payload.client_recupere else "client_informe"
        await db.expeditions_colisage.update_one(
            {"expedition_id": expedition_id},
            {"$set": {
                "recuperation": recuperation,
                "statut": nouveau_statut,
                "updated_at": now
            }}
        )
        if payload.client_recupere:
            await db.ordres_colisage.update_one(
                {"expedition_id": expedition_id},
                {"$set": {"statut": "cloture", "updated_at": now}}
            )
            await _notify_colisage_roles(
                db,
                titre=f"Client récupéré — {exp.get('reference')}",
                message=f"Expédition {exp.get('reference')} récupérée le {payload.date_recuperation or now[:10]}. Clôturée.",
                lien=f"/expeditions/{expedition_id}",
                exclude_user_id=user["user_id"]
            )
        return {"message": "Récupération enregistrée", "statut": nouveau_statut}

    @router.post("/expeditions/{expedition_id}/incident")
    async def declarer_incident_expedition(
        expedition_id: str,
        payload: IncidentIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        exp = await db.expeditions_colisage.find_one({"expedition_id": expedition_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        now = _now_iso()
        incident = {
            "incident_id": f"inc_{uuid.uuid4().hex[:12]}",  # TICKET-011 : ID unique pour résolution
            "type": payload.type_incident,
            "description": payload.description,
            "date": now,
            "declare_par": user["user_id"],
            "statut_resolution": "ouvert",
            "historique_resolution": [],
        }
        await db.expeditions_colisage.update_one(
            {"expedition_id": expedition_id},
            {"$push": {"incidents": incident}, "$set": {"updated_at": now}}
        )
        await _notify_colisage_roles(
            db,
            titre=f"⚠️ Incident expédition — {exp.get('reference')}",
            message=f"Incident: {payload.type_incident}. {payload.description or ''}",
            lien=f"/expeditions/{expedition_id}",
            exclude_user_id=user["user_id"]
        )
        return {"message": "Incident déclaré", "incident_id": incident["incident_id"]}

    # =========================================================================
    # LEGACY — COLIS (rétrocompatibilité)
    # =========================================================================

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
            {"$project": {
                "facture_info": 0, "commande_info": 0, "client_info": 0,
                "commande_id_from_fac": 0, "client_id_from_fac": 0, "_id": 0
            }},
        ]

        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"facture_reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
            ]}})

        pipeline += [{"$sort": {"created_at": -1}}, {"$skip": skip}, {"$limit": limit}]
        docs = await db.colis.aggregate(pipeline).to_list(limit)
        for d in docs:
            d.pop("_id", None)
        return docs

    @router.get("/colis/by-facture/{facture_id}")
    async def get_colis_by_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")

        lignes_fac = await db.facture_lignes.find(
            {"facture_id": facture_id}, {"_id": 0}
        ).to_list(200)

        qtés_colisées = await _get_quantites_colisees(db, facture_id)

        lignes_enrichies = []
        for lg in lignes_fac:
            qte_col = qtés_colisées.get(lg["ligne_id"], 0)
            lignes_enrichies.append({
                **lg,
                "quantite_colisee": qte_col,
                "quantite_restante": max(0, lg["quantite"] - qte_col),
            })

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
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": payload.facture_id})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")
        if facture["statut"] not in STATUTS_FACTURE_AUTORISES:
            raise HTTPException(status_code=400, detail=f"Facture doit être émise (statut: {facture['statut']})")

        lignes_fac = await db.facture_lignes.find(
            {"facture_id": payload.facture_id}, {"_id": 0}
        ).to_list(200)
        lignes_fac_map = {lg["ligne_id"]: lg for lg in lignes_fac}
        qtés_colisées = await _get_quantites_colisees(db, payload.facture_id)

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
                    detail=f"Quantité ({ligne.quantite_colisee}) > restante ({qte_restante}) pour '{lg_fac['designation']}'"
                )

        counter = await _next_counter(db, "colis")
        colis_id = f"colis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}"
        reference = f"FABS-COL-{year2}-{counter:05d}"
        code_barres = _generate_code_barres()
        qr_code = _generate_qr_code("colis", colis_id)

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
            "historique": [{"action": "creation", "user_id": user["user_id"], "timestamp": now, "details": {}}]
        }
        await db.colis.insert_one(colis_doc)
        colis_doc.pop("_id", None)
        return colis_doc

    @router.put("/colis/{colis_id}")
    async def update_colis(
        colis_id: str,
        payload: ColisUpdate,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        if existing["statut"] in ("valide", "expedie"):
            raise HTTPException(status_code=400, detail=f"Impossible de modifier un colis '{existing['statut']}'")

        facture_id = existing["facture_id"]
        lignes_fac = await db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0}).to_list(200)
        lignes_fac_map = {lg["ligne_id"]: lg for lg in lignes_fac}
        qtés_colisées = await _get_quantites_colisees(db, facture_id, exclude_colis_id=colis_id)

        for ligne in payload.lignes:
            lg_fac = lignes_fac_map.get(ligne.ligne_facture_id)
            if not lg_fac:
                raise HTTPException(status_code=404, detail=f"Ligne facture '{ligne.ligne_facture_id}' introuvable")
            qte_max = lg_fac["quantite"]
            qte_deja = qtés_colisées.get(ligne.ligne_facture_id, 0)
            if ligne.quantite_colisee > qte_max - qte_deja:
                raise HTTPException(status_code=400, detail=f"Quantité excessive pour '{lg_fac['designation']}'")

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
        updated = await db.colis.find_one({"colis_id": colis_id}, {"_id": 0})
        return updated

    @router.patch("/colis/{colis_id}/statut")
    async def update_colis_statut(
        colis_id: str,
        payload: ColisStatutIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        STATUTS_VALIDES = ["en_preparation", "valide", "expedie", "annule"]
        if payload.statut not in STATUTS_VALIDES:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {STATUTS_VALIDES}")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")

        ancien_statut = existing["statut"]
        if payload.statut == "valide":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Validation réservée")
            if ancien_statut != "en_preparation":
                raise HTTPException(status_code=400, detail=f"Impossible de valider un colis '{ancien_statut}'")
        elif payload.statut == "annule":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Annulation réservée")
            if ancien_statut == "expedie":
                raise HTTPException(status_code=400, detail="Impossible d'annuler un colis expédié")
        elif payload.statut == "expedie":
            _ensure(user["role"] in VALIDATE_ROLES, 403, "Expédition réservée")
            if ancien_statut != "valide":
                raise HTTPException(status_code=400, detail="Seul un colis validé peut être expédié")

        update_data = {"statut": payload.statut, "updated_at": _now_iso()}
        await db.colis.update_one({"colis_id": colis_id}, {"$set": update_data})
        await _log_historique(db, "colis", colis_id, "colis_id",
                               f"statut_{payload.statut}", user["user_id"],
                               {"ancien": ancien_statut, "nouveau": payload.statut, "motif": payload.motif or ""})

        return {"message": f"Statut: {ancien_statut} → {payload.statut}", "statut": payload.statut}

    @router.delete("/colis/{colis_id}")
    async def delete_colis(
        colis_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")

        existing = await db.colis.find_one({"colis_id": colis_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Colis introuvable")
        if existing["statut"] in ("valide", "expedie"):
            raise HTTPException(status_code=400, detail=f"Impossible de supprimer un colis '{existing['statut']}'")

        await db.colis.delete_one({"colis_id": colis_id})
        return {"message": "Colis supprimé"}

    @router.get("/stats/facture/{facture_id}")
    async def stats_colisage_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
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

    @router.get("/mouvements")
    async def list_mouvements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        colis_id: Optional[str] = None,
        type_mouvement: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if colis_id:
            filters["colis_id"] = colis_id
        if type_mouvement:
            filters["type_mouvement"] = type_mouvement

        docs = await db.mouvements_colis.find(filters, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        for d in docs:
            d.pop("_id", None)
        return docs


    # =========================================================================
    # ENDPOINTS QR CODE + ÉTIQUETTES PDF
    # =========================================================================

    @router.get("/cartons/{carton_id}/qrcode")
    async def get_carton_qrcode(
        carton_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        token: Optional[str] = Query(default=None),
    ):
        """Retourne l'image QR Code du carton en PNG."""
        from fastapi.responses import Response as FastAPIResponse
        import qrcode as qrcode_lib
        import io

        auth_header = authorization or (f"Bearer {token}" if token else None)
        user = await resolve_user(request, auth_header)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        carton = await db.cartons_colisage.find_one({"carton_id": carton_id}, {"_id": 0})
        if not carton:
            raise HTTPException(status_code=404, detail="Carton introuvable")

        qr_url = carton.get("qr_code") or f"https://erp.fabsci.ci/carton/{carton_id}"
        qr = qrcode_lib.QRCode(version=1, error_correction=qrcode_lib.constants.ERROR_CORRECT_L, box_size=8, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return FastAPIResponse(content=buf.read(), media_type="image/png")

    @router.get("/cartons/{carton_id}/etiquette")
    async def get_carton_etiquette(
        carton_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        token: Optional[str] = Query(default=None),
    ):
        """Génère une étiquette PDF A6 pour le carton."""
        from fastapi.responses import Response as FastAPIResponse
        import qrcode as qrcode_lib
        import io
        from reportlab.lib.pagesizes import A6
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        auth_header = authorization or (f"Bearer {token}" if token else None)
        user = await resolve_user(request, auth_header)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        carton = await db.cartons_colisage.find_one({"carton_id": carton_id}, {"_id": 0})
        if not carton:
            raise HTTPException(status_code=404, detail="Carton introuvable")

        # QR Code image
        qr_url = carton.get("qr_code") or f"https://erp.fabsci.ci/carton/{carton_id}"
        qr = qrcode_lib.QRCode(version=1, error_correction=qrcode_lib.constants.ERROR_CORRECT_M, box_size=5, border=2)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buf = io.BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        # PDF
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf,
            pagesize=A6,
            leftMargin=8*mm, rightMargin=8*mm,
            topMargin=6*mm, bottomMargin=6*mm,
        )
        styles = getSampleStyleSheet()
        bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9)
        normal = ParagraphStyle("normal", parent=styles["Normal"], fontName="Helvetica", fontSize=8)
        small = ParagraphStyle("small", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=colors.grey)
        title_style = ParagraphStyle("title", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, alignment=1)

        designation = carton.get("designation") or "—"
        quantite = carton.get("quantite") or "—"
        numero_x = carton.get("numero_carton") or "?"
        total_y = carton.get("total_cartons") or "?"
        est_partiel = carton.get("est_partiel", False)

        elems = [
            Paragraph("EDITIONS FABS-CI", title_style),
            Spacer(1, 3*mm),
            Table(
                [
                    [Paragraph("Référence carton", small), Paragraph(carton.get("reference", carton_id), bold)],
                    [Paragraph("Ordre colisage", small), Paragraph(carton.get("ordre_reference", "—"), normal)],
                    [Paragraph("Facture", small), Paragraph(carton.get("facture_reference", "—"), normal)],
                    [Paragraph("Client", small), Paragraph(carton.get("client_nom", "—"), bold)],
                    [Paragraph("Ville", small), Paragraph(carton.get("client_ville", "—"), normal)],
                    [Paragraph("Article", small), Paragraph(str(designation), normal)],
                    [Paragraph("Quantité", small), Paragraph(str(quantite) + (" (PARTIEL)" if est_partiel else ""), bold)],
                ],
                colWidths=[30*mm, None],
            ),
            Spacer(1, 3*mm),
            Paragraph(f"Carton {numero_x} / {total_y}", ParagraphStyle("cn", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, alignment=1)),
            Spacer(1, 3*mm),
            RLImage(qr_buf, width=28*mm, height=28*mm),
            Spacer(1, 2*mm),
            Paragraph(carton.get("colise_le", "")[:10] if carton.get("colise_le") else "", small),
        ]

        doc.build(elems)
        pdf_buf.seek(0)

        ref_safe = (carton.get("reference") or carton_id).replace("/", "-")
        return FastAPIResponse(
            content=pdf_buf.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="etiquette-{ref_safe}.pdf"'}
        )

    @router.get("/ordres/{ordre_id}/etiquettes-bulk")
    async def get_ordre_etiquettes_bulk(
        ordre_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        token: Optional[str] = Query(default=None),
    ):
        """Génère un PDF multi-pages contenant toutes les étiquettes des cartons d'un ordre."""
        from fastapi.responses import Response as FastAPIResponse
        import qrcode as qrcode_lib
        import io
        from reportlab.lib.pagesizes import A6
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image as RLImage, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        auth_header = authorization or (f"Bearer {token}" if token else None)
        user = await resolve_user(request, auth_header)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        ordre = await db.ordres_colisage.find_one({"ordre_colisage_id": ordre_id}, {"_id": 0})
        if not ordre:
            raise HTTPException(status_code=404, detail="Ordre introuvable")

        cartons = await db.cartons_colisage.find({"ordre_colisage_id": ordre_id}, {"_id": 0}).sort("numero_carton", 1).to_list(500)
        if not cartons:
            raise HTTPException(status_code=404, detail="Aucun carton trouvé pour cet ordre")

        styles = getSampleStyleSheet()
        bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9)
        normal = ParagraphStyle("normal", parent=styles["Normal"], fontName="Helvetica", fontSize=8)
        small = ParagraphStyle("small", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=colors.grey)
        title_style = ParagraphStyle("title", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, alignment=1)

        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=A6,
            leftMargin=8*mm, rightMargin=8*mm,
            topMargin=6*mm, bottomMargin=6*mm,
        )

        all_elems = []
        for i, carton in enumerate(cartons):
            carton_id = carton.get("carton_id", "")
            qr_url = carton.get("qr_code") or f"https://erp.fabsci.ci/carton/{carton_id}"
            qr = qrcode_lib.QRCode(version=1, error_correction=qrcode_lib.constants.ERROR_CORRECT_M, box_size=5, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_buf = io.BytesIO()
            qr_img.save(qr_buf, format="PNG")
            qr_buf.seek(0)

            est_partiel = carton.get("est_partiel", False)
            elems = [
                Paragraph("EDITIONS FABS-CI", title_style),
                Spacer(1, 3*mm),
                Table(
                    [
                        [Paragraph("Réf. carton", small), Paragraph(carton.get("reference", carton_id), bold)],
                        [Paragraph("Ordre", small), Paragraph(carton.get("ordre_reference", "—"), normal)],
                        [Paragraph("Facture", small), Paragraph(carton.get("facture_reference", "—"), normal)],
                        [Paragraph("Client", small), Paragraph(carton.get("client_nom", "—"), bold)],
                        [Paragraph("Ville", small), Paragraph(carton.get("client_ville", "—"), normal)],
                        [Paragraph("Article", small), Paragraph(str(carton.get("designation", "—")), normal)],
                        [Paragraph("Qté", small), Paragraph(str(carton.get("quantite", "—")) + (" (PARTIEL)" if est_partiel else ""), bold)],
                    ],
                    colWidths=[28*mm, None],
                ),
                Spacer(1, 3*mm),
                Paragraph(f"Carton {carton.get('numero_carton', '?')} / {carton.get('total_cartons', '?')}",
                          ParagraphStyle("cn", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, alignment=1)),
                Spacer(1, 3*mm),
                RLImage(qr_buf, width=28*mm, height=28*mm),
            ]
            if i < len(cartons) - 1:
                elems.append(PageBreak())
            all_elems.extend(elems)

        doc.build(all_elems)
        pdf_buf.seek(0)
        ref_safe = (ordre.get("reference") or ordre_id).replace("/", "-")
        return FastAPIResponse(
            content=pdf_buf.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="etiquettes-{ref_safe}.pdf"'}
        )

    # =========================================================================
    # INCIDENTS CONSOLIDÉS
    # =========================================================================

    @router.get("/incidents")
    async def list_incidents_consolides(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        source: Optional[str] = Query(None, description="livraison | expedition"),
        type_incident: Optional[str] = Query(None),
        limit: int = Query(100, le=500),
    ):
        """Liste consolidée de tous les incidents (livraisons + expéditions)."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        incidents = []

        if not source or source == "livraison":
            livs = await db.livraisons_directes.find(
                {"incidents": {"$exists": True, "$ne": []}},
                {"_id": 0, "livraison_id": 1, "reference": 1, "client_nom": 1, "ville_destination": 1, "statut": 1, "incidents": 1}
            ).to_list(500)
            for liv in livs:
                for inc in (liv.get("incidents") or []):
                    incidents.append({
                        "source": "livraison",
                        "document_id": liv["livraison_id"],
                        "document_reference": liv.get("reference"),
                        "client_nom": liv.get("client_nom"),
                        "ville": liv.get("ville_destination"),
                        "statut_document": liv.get("statut"),
                        "type_incident": inc.get("type"),
                        "description": inc.get("description"),
                        "date": inc.get("date"),
                        "declare_par": inc.get("declare_par"),
                    })

        if not source or source == "expedition":
            exps = await db.expeditions_colisage.find(
                {"incidents": {"$exists": True, "$ne": []}},
                {"_id": 0, "expedition_id": 1, "reference": 1, "client_nom": 1, "ville_destination": 1, "statut": 1, "incidents": 1}
            ).to_list(500)
            for exp in exps:
                for inc in (exp.get("incidents") or []):
                    incidents.append({
                        "source": "expedition",
                        "document_id": exp["expedition_id"],
                        "document_reference": exp.get("reference"),
                        "client_nom": exp.get("client_nom"),
                        "ville": exp.get("ville_destination"),
                        "statut_document": exp.get("statut"),
                        "type_incident": inc.get("type"),
                        "description": inc.get("description"),
                        "date": inc.get("date"),
                        "declare_par": inc.get("declare_par"),
                    })

        if type_incident:
            incidents = [i for i in incidents if i.get("type_incident") == type_incident]

        incidents.sort(key=lambda x: x.get("date") or "", reverse=True)
        return incidents[:limit]

    # TICKET-011 — Résolution d'un incident (livraison ou expédition)
    # Un incident est identifié par son document_id (livraison_id ou expedition_id)
    # et son incident_id (uuid généré à la déclaration).
    # Workflow : ouvert → en_cours → resolu → cloture
    INCIDENT_STATUTS_VALIDES = ["ouvert", "en_cours", "resolu", "cloture"]

    class IncidentResolutionIn(BaseModel):
        statut_resolution: str
        commentaire: Optional[str] = None

    @router.patch("/livraisons/{livraison_id}/incident/{incident_id}/resolution")
    async def resoudre_incident_livraison(
        livraison_id: str,
        incident_id: str,
        payload: IncidentResolutionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Mettre à jour le statut de résolution d'un incident de livraison."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELIVERY_ROLES, 403, "Accès refusé")
        _ensure(
            payload.statut_resolution in INCIDENT_STATUTS_VALIDES,
            400,
            f"Statut invalide. Valeurs acceptées : {INCIDENT_STATUTS_VALIDES}",
        )

        liv = await db.livraisons_directes.find_one({"livraison_id": livraison_id}, {"_id": 0})
        _ensure(liv is not None, 404, "Livraison introuvable")

        incidents_liv = liv.get("incidents", [])
        idx = next((i for i, inc in enumerate(incidents_liv) if inc.get("incident_id") == incident_id), None)
        _ensure(idx is not None, 404, f"Incident {incident_id} introuvable sur cette livraison")

        now = _now_iso()
        # Entrée historique
        historique_entry = {
            "statut_precedent": incidents_liv[idx].get("statut_resolution", "ouvert"),
            "nouveau_statut": payload.statut_resolution,
            "commentaire": payload.commentaire or "",
            "date": now,
            "modifie_par": user["user_id"],
        }
        # Mise à jour dans le tableau subdocument
        update_fields = {
            f"incidents.{idx}.statut_resolution": payload.statut_resolution,
            f"incidents.{idx}.updated_at": now,
            "updated_at": now,
        }
        if payload.statut_resolution == "resolu":
            update_fields[f"incidents.{idx}.date_resolution"] = now
            update_fields[f"incidents.{idx}.resolu_par"] = user["user_id"]
        if payload.statut_resolution == "cloture":
            update_fields[f"incidents.{idx}.date_cloture"] = now

        await db.livraisons_directes.update_one(
            {"livraison_id": livraison_id},
            {
                "$set": update_fields,
                "$push": {f"incidents.{idx}.historique_resolution": historique_entry},
            },
        )
        # TICKET-016 — audit
        if log_audit_event:
            await log_audit_event(
                user_id=user["user_id"],
                action="RESOLVE_INCIDENT",
                resource_type="livraison_directe",
                resource_id=livraison_id,
                details={
                    "incident_id": incident_id,
                    "statut_resolution": payload.statut_resolution,
                    "commentaire": payload.commentaire or "",
                },
                ip_address=request.client.host if request.client else None,
            )
        return {
            "message": f"Incident mis à jour → {payload.statut_resolution}",
            "incident_id": incident_id,
            "livraison_id": livraison_id,
        }

    @router.patch("/expeditions/{expedition_id}/incident/{incident_id}/resolution")
    async def resoudre_incident_expedition(
        expedition_id: str,
        incident_id: str,
        payload: IncidentResolutionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Mettre à jour le statut de résolution d'un incident d'expédition."""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        _ensure(
            payload.statut_resolution in INCIDENT_STATUTS_VALIDES,
            400,
            f"Statut invalide. Valeurs acceptées : {INCIDENT_STATUTS_VALIDES}",
        )

        exp = await db.expeditions_colisage.find_one({"expedition_id": expedition_id}, {"_id": 0})
        _ensure(exp is not None, 404, "Expédition introuvable")

        incidents_exp = exp.get("incidents", [])
        idx = next((i for i, inc in enumerate(incidents_exp) if inc.get("incident_id") == incident_id), None)
        _ensure(idx is not None, 404, f"Incident {incident_id} introuvable sur cette expédition")

        now = _now_iso()
        historique_entry = {
            "statut_precedent": incidents_exp[idx].get("statut_resolution", "ouvert"),
            "nouveau_statut": payload.statut_resolution,
            "commentaire": payload.commentaire or "",
            "date": now,
            "modifie_par": user["user_id"],
        }
        update_fields = {
            f"incidents.{idx}.statut_resolution": payload.statut_resolution,
            f"incidents.{idx}.updated_at": now,
            "updated_at": now,
        }
        if payload.statut_resolution == "resolu":
            update_fields[f"incidents.{idx}.date_resolution"] = now
            update_fields[f"incidents.{idx}.resolu_par"] = user["user_id"]
        if payload.statut_resolution == "cloture":
            update_fields[f"incidents.{idx}.date_cloture"] = now

        await db.expeditions_colisage.update_one(
            {"expedition_id": expedition_id},
            {
                "$set": update_fields,
                "$push": {f"incidents.{idx}.historique_resolution": historique_entry},
            },
        )
        return {
            "message": f"Incident mis à jour → {payload.statut_resolution}",
            "incident_id": incident_id,
            "expedition_id": expedition_id,
        }

    return router


# ============================================================================
# FONCTION INTERNE — Création automatique OC depuis factures_module
# ============================================================================

async def _create_ordre_colisage_internal(db, facture_id: str, user_id: str, notes: str = None) -> dict:
    """
    Crée un ordre de colisage automatiquement lors de l'émission d'une facture.
    Appelé depuis factures_module.py
    """
    year2 = datetime.now().strftime("%y")

    # Récupérer la facture
    facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    # Récupérer le client
    client = await db.clients.find_one({"client_id": facture.get("client_id")}, {"_id": 0}) or {}

    counter_result = await db.counters.find_one_and_update(
        {"_id": "ordres_colisage"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    counter = counter_result["seq"]

    ordre_id = f"oc_{uuid.uuid4().hex[:12]}"
    reference = f"ORD-COL-{year2}-{counter:05d}"
    now = datetime.now(timezone.utc).isoformat()

    ordre_doc = {
        "ordre_colisage_id": ordre_id,
        "reference": reference,
        "facture_id": facture_id,
        "facture_reference": facture.get("reference"),
        "client_id": client.get("client_id"),
        "client_nom": client.get("nom"),
        "client_ville": client.get("ville"),
        "client_adresse": client.get("adresse"),
        "client_telephone": client.get("telephone"),
        "statut": "a_coliser",
        "notes": notes,
        "nb_cartons": 0,
        "colisage_par": None,
        "date_colisage_termine": None,
        "date_cloture": None,
        "cloture_par": None,
        "livraison_id": None,
        "expedition_id": None,
        "historique": [{
            "action": "creation_auto",
            "user_id": user_id,
            "timestamp": now,
            "details": {"facture_reference": facture.get("reference"), "client": client.get("nom")}
        }],
        "created_at": now,
        "created_by": user_id,
        "updated_at": now,
    }

    await db.ordres_colisage.insert_one(ordre_doc)
    ordre_doc.pop("_id", None)

    logger.info(f"Ordre de colisage {reference} créé automatiquement pour facture {facture.get('reference')}")
    return ordre_doc
