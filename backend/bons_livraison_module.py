"""
Module Bons de Livraison — Sprint 10
- CRUD bons de livraison
- Référence auto FABS-BL-26-27-XXXX
- Génération depuis commandes préparées
- Mise à jour stock automatique lors de la livraison
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional, List
import re
import uuid
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator
from sanitizers import sanitize_str

logger = logging.getLogger("fabsci.bons_livraison")

READ_ROLES = {"super_admin", "directeur_general", "service_logistique", "responsable_magasinier", "comptable", "directeur_commercial"}
WRITE_ROLES = {"super_admin", "directeur_general", "service_logistique", "comptable", "directeur_commercial"}

StatutBL = Literal["en_preparation", "pret", "livre", "annule"]


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_bl_reference(db: AsyncIOMotorDatabase) -> str:
    """Generate FABS-BL-26-27-XXXX reference"""
    doc = await db.counters.find_one_and_update(
        {"_id": "bons_livraison"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-BL-26-27-{seq:04d}"


class LigneBLIn(BaseModel):
    produit_id: str
    quantite: int = Field(..., gt=0)


class BonLivraisonIn(BaseModel):
    commande_id: str
    date_livraison_prevue: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    lignes: List[LigneBLIn] = Field(..., min_length=1)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)


class BonLivraisonOut(BaseModel):
    bl_id: str
    reference: str
    commande_id: str
    commande_reference: Optional[str] = None
    client_id: str
    client_nom: Optional[str] = None
    statut: StatutBL
    date_creation: str
    date_livraison_prevue: Optional[str] = None
    date_livraison_reelle: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: str


def build_bons_livraison_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/bons-livraison", tags=["bons_livraison"])

    @router.get("", response_model=List[BonLivraisonOut])
    async def list_bons_livraison(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[StatutBL] = None,
        commande_id: Optional[str] = None,
        client_id: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = Query(50, ge=1, le=200),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut
        if commande_id:
            filters["commande_id"] = commande_id
        if client_id:
            filters["client_id"] = client_id

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
            # C5 fix: échapper q pour éviter ReDoS et injection NoSQL
            safe_q = re.escape(q)
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": safe_q, "$options": "i"}},
                {"client_nom": {"$regex": safe_q, "$options": "i"}},
                {"client_ville": {"$regex": safe_q, "$options": "i"}},
                {"client_telephone": {"$regex": safe_q, "$options": "i"}},
                {"client_representant": {"$regex": safe_q, "$options": "i"}},
            ]}})
        pipeline += [{"$sort": {"date_creation": -1}}, {"$limit": limit}]

        docs = await db.bons_livraison.aggregate(pipeline).to_list(limit)
        return [BonLivraisonOut(**d) for d in docs]

    @router.post("", response_model=BonLivraisonOut, status_code=201)
    async def create_bon_livraison(
        payload: BonLivraisonIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Verify commande
        cmd = await db.commandes.find_one({"commande_id": payload.commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(cmd["statut"] in ["preparee", "livree"], 400, "Commande doit être préparée")

        # Anti-doublon : interdire un nouveau BL si la commande est déjà totalement livrée.
        # Les livraisons partielles restent autorisées tant qu'il n'existe pas de BL livré couvrant tout.
        existing_livre = await db.bons_livraison.find_one(
            {"commande_id": payload.commande_id, "statut": "livre"},
            {"_id": 0, "reference": 1},
        )
        if existing_livre or cmd["statut"] == "livree":
            ref = existing_livre.get("reference") if existing_livre else None
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cette commande est déjà totalement livrée"
                    + (f" (BL {ref})" if ref else "")
                    + ". Aucun nouveau bon de livraison ne peut être créé."
                ),
            )

        # Create BL
        bl_id = f"bl_{uuid.uuid4().hex[:12]}"
        reference = await next_bl_reference(db)
        now = _now_iso()

        bl_doc = {
            "bl_id": bl_id,
            "reference": reference,
            "commande_id": payload.commande_id,
            "client_id": cmd["client_id"],
            "statut": "en_preparation",
            "date_creation": now[:10],
            "date_livraison_prevue": payload.date_livraison_prevue,
            "date_livraison_reelle": None,
            "notes": payload.notes,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.bons_livraison.insert_one(bl_doc)

        # Create lignes
        for ligne in payload.lignes:
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "bl_id": bl_id,
                "produit_id": ligne.produit_id,
                "quantite": ligne.quantite,
            }
            await db.bl_lignes.insert_one(ligne_doc)

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_BL",
                resource_type="bon_livraison",
                resource_id=bl_id,
                details={
                    "reference": reference,
                    "commande_id": payload.commande_id,
                    "commande_reference": cmd.get("reference"),
                    "client_id": cmd["client_id"],
                    "lignes_count": len(payload.lignes)
                },
                ip_address=request.client.host if request.client else None
            )

        # Enrich and return
        bl_doc["commande_reference"] = cmd.get("reference")
        client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0, "nom": 1})
        bl_doc["client_nom"] = client["nom"] if client else None

        return BonLivraisonOut(**bl_doc)

    @router.post("/{bl_id}/livrer", response_model=BonLivraisonOut)
    async def livrer_bon(
        bl_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        bl = await db.bons_livraison.find_one({"bl_id": bl_id}, {"_id": 0})
        _ensure(bl is not None, 404, "BL introuvable")
        _ensure(bl["statut"] != "livre", 400, "BL déjà livré")

        now = _now_iso()

        # Get lignes and create stock movements (AVANT de figer les statuts :
        # si le stock est insuffisant, on lève 400 sans rien modifier).
        lignes = await db.bl_lignes.find({"bl_id": bl_id}, {"_id": 0}).to_list(100)
        for ligne in lignes:
            _qte = ligne.get("quantite", ligne.get("quantite_commandee", ligne.get("quantite_livree", 0)))
            # C6 fix: décrémentation atomique avec guard stock >= qte pour éviter stock négatif
            updated = await db.produits.find_one_and_update(
                {"produit_id": ligne["produit_id"], "stock_actuel": {"$gte": _qte}},
                {
                    "$inc": {"stock_actuel": -_qte},
                    "$set": {"updated_at": now},
                },
                return_document=True,
                projection={"_id": 0, "stock_actuel": 1},
            )
            if not updated:
                # Stock insuffisant — lire la valeur actuelle pour le message d'erreur
                produit_cur = await db.produits.find_one(
                    {"produit_id": ligne["produit_id"]},
                    {"_id": 0, "stock_actuel": 1, "reference": 1},
                )
                stock_dispo = produit_cur.get("stock_actuel", 0) if produit_cur else 0
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuffisant pour le produit {ligne['produit_id']}: "
                           f"disponible={stock_dispo}, demandé={_qte}",
                )
            stock_apres = updated.get("stock_actuel", 0)
            stock_avant = stock_apres + _qte

            # TICKET-007 — Mettre à jour quantite_livree dans bl_lignes
            _ligne_key = ligne.get("ligne_bl_id") or ligne.get("ligne_id")
            await db.bl_lignes.update_one(
                {"ligne_bl_id": _ligne_key},
                {"$set": {
                    "quantite_livree": _qte,
                    "updated_at": now,
                }}
            )

            mouvement_doc = {
                "mouvement_id": f"mvt_{uuid.uuid4().hex[:12]}",
                "produit_id": ligne["produit_id"],
                "type_mouvement": "sortie",
                "quantite": _qte,
                "stock_avant": stock_avant,
                "stock_apres": stock_apres,
                "bl_id": bl_id,
                "motif": f"Livraison BL {bl['reference']}",
                "created_by": me["user_id"],
                "created_at": now,
            }
            await db.mouvements_stock.insert_one(mouvement_doc)

        # Déduction stock OK -> on fige les statuts BL + commande
        await db.bons_livraison.update_one(
            {"bl_id": bl_id},
            {"$set": {
                "statut": "livre",
                "date_livraison_reelle": now[:10],
                "updated_at": now,
            }}
        )
        await db.commandes.update_one(
            {"commande_id": bl["commande_id"]},
            {"$set": {"statut": "livree", "date_livraison": now[:10], "updated_at": now}}
        )

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="DELIVER_BL",
                resource_type="bon_livraison",
                resource_id=bl_id,
                details={
                    "reference": bl["reference"],
                    "commande_id": bl["commande_id"],
                    "commande_statut": "livree",
                    "lignes_count": len(lignes),
                    "mouvements_stock_count": len(lignes)
                },
                ip_address=request.client.host if request.client else None
            )

        updated = await db.bons_livraison.find_one({"bl_id": bl_id}, {"_id": 0})
        cmd = await db.commandes.find_one({"commande_id": updated["commande_id"]}, {"_id": 0, "reference": 1, "client_id": 1})
        if cmd:
            updated["commande_reference"] = cmd.get("reference")
            client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0, "nom": 1})
            updated["client_nom"] = client["nom"] if client else None

        return BonLivraisonOut(**updated)

    # ---------- PDF ----------
    @router.get("/{bl_id}/pdf")
    async def bl_pdf(
        bl_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse
        from pdf_generator import generate_bl_pdf

        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        bl = await db.bons_livraison.find_one({"bl_id": bl_id}, {"_id": 0})
        _ensure(bl is not None, 404, "Bon de livraison introuvable")

        # Fetch lignes from bl_lignes if exists, else from commande_lignes
        lignes = await db.bl_lignes.find({"bl_id": bl_id}, {"_id": 0}).to_list(500)
        if not lignes:
            lignes = await db.commande_lignes.find({"commande_id": bl["commande_id"]}, {"_id": 0}).to_list(500)

        from pdf_generator import enrich_lignes_for_pdf
        _pids = list({(l.get("produit_id") or l.get("product_id")) for l in lignes if (l.get("produit_id") or l.get("product_id"))})
        _prods = await db.produits.find({"produit_id": {"$in": _pids}}, {"_id": 0}).to_list(1000) if _pids else []
        enrich_lignes_for_pdf({p["produit_id"]: p for p in _prods}, lignes)

        cmd = await db.commandes.find_one({"commande_id": bl["commande_id"]}, {"_id": 0, "reference": 1, "client_id": 1})
        commande_ref = cmd.get("reference") if cmd else None
        client = {}
        if cmd:
            client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0}) or {}

        buffer = generate_bl_pdf(bl, lignes, client, commande_ref=commande_ref)
        filename = f"{bl['reference']}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    return router


async def seed_bons_livraison(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed demo BL (optional)"""
    existing = await db.bons_livraison.count_documents({})
    if existing > 0:
        return 0
    
    # Create indexes
    await db.bons_livraison.create_index("bl_id", unique=True)
    await db.bons_livraison.create_index("reference", unique=True)
    await db.bl_lignes.create_index("bl_id")
    
    return 0
