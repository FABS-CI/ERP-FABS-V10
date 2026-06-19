"""
Module Factures — Sprint 7
- CRUD complet sur les collections MongoDB `factures` et `facture_lignes`
- Référence auto-incrémentée FABS-FC-26-27-XXXX (factures) et FABS-AV-26-27-XXXX (avoirs)
- Type facture : facture / avoir
- Statut : brouillon, emise, partiellement_payee, payee, annulee
- Génération automatique depuis commandes validées/préparées
- Gestion paiements (montant_regle, montant_restant)
- Génération avoirs (credit notes)
- Génération automatique écritures comptables
- RBAC (2026-06-17) :
    READ    = {super_admin, comptable}
    WRITE   = {super_admin, comptable}
    PAYMENT = {super_admin, comptable}
"""
from __future__ import annotations

from datetime import datetime, timezone, date as date_type
from typing import Literal, Optional, List
from decimal import Decimal
import re
import uuid
import logging
import os
import asyncio

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sanitizers import sanitize_str
from notifications_module import notify_vente_event

logger = logging.getLogger("fabsci.factures")

# Import des fonctions de génération d'écritures comptables
from comptabilite_module import (
    generate_ecriture_comptable_facture,
    generate_ecriture_comptable_avoir
)

# RBAC
READ_ROLES = {
    # RBAC 2026-06-17: DG totalement retiré des factures
    "super_admin", "comptable",
}
WRITE_ROLES = {
    # RBAC 2026-06-17: DG retiré
    "super_admin", "comptable",
}
PAYMENT_ROLES = {"super_admin", "comptable"}  # RBAC 2026-06-17: DG retiré

TypeFacture = Literal["facture", "avoir"]
Statut = Literal["brouillon", "emise", "partiellement_payee", "payee", "annulee"]

TVA_RATE = 0.18  # 18% TVA in Côte d'Ivoire


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


async def _send_email_smtp(destinataire: str, sujet: str, corps_html: str, corps_texte: str) -> dict:
    """Envoyer email via SMTP"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")
    
    if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
        raise HTTPException(
            status_code=503,
            detail="Service email non configuré. Contactez l'administrateur."
        )

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"] = smtp_from
        msg["To"] = destinataire
        
        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
        msg.attach(MIMEText(corps_html, "html", "utf-8"))
        
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            try:
                server.login(smtp_user, smtp_password)
            except smtplib.SMTPAuthenticationError as auth_err:
                logger.error(f"Erreur authentification SMTP: {auth_err}")
                raise HTTPException(
                    status_code=503,
                    detail="Échec d'authentification SMTP. Vérifiez les identifiants SMTP."
                )
            server.send_message(msg)
        
        return {"success": True, "message_id": f"email_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur SMTP: {e}")
        return {"success": False, "error": str(e)}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_facture_reference(db: AsyncIOMotorDatabase, type_facture: TypeFacture) -> str:
    """Generate FABS-FC-26-27-XXXX (facture) or FABS-AV-26-27-XXXX (avoir)"""
    counter_id = "factures" if type_facture == "facture" else "avoirs"
    prefix = "FABS-FC-26-27" if type_facture == "facture" else "FABS-AV-26-27"
    
    doc = await db.counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"{prefix}-{seq:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class LigneFactureIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    produit_id: str = Field(..., alias='product_id')
    designation: str  # Product title/description
    quantite: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., gt=0)
    remise_ligne: float = Field(default=0, ge=0, le=100)

    @property
    def montant_ht(self) -> float:
        base = self.quantite * self.prix_unitaire
        return base * (1 - self.remise_ligne / 100)


class LigneFactureOut(BaseModel):
    ligne_id: str
    facture_id: str
    produit_id: str
    designation: str
    quantite: int
    prix_unitaire: float
    remise_ligne: float
    montant_ht: float
    code_article: Optional[str] = None
    niveau: Optional[str] = None
    matiere: Optional[str] = None
    cycle: Optional[str] = None


class FactureIn(BaseModel):
    client_id: str
    commande_id: Optional[str] = None
    date_facture: Optional[str] = None  # ISO date YYYY-MM-DD
    date_echeance: Optional[str] = None
    remise_globale: float = Field(default=0, ge=0, le=100)
    taux_tva: float = Field(default=18.0, ge=0, le=100, description="Taux TVA en % (0 pour exonérés)")
    notes: Optional[str] = Field(default=None, max_length=1000)
    lignes: List[LigneFactureIn] = Field(..., min_length=1)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)

    @field_validator("date_facture", "date_echeance", mode="before")
    @classmethod
    def _validate_date(cls, v):
        if v:
            try:
                date_type.fromisoformat(v)
            except ValueError:
                raise ValueError("Format de date invalide (YYYY-MM-DD attendu)")
        return v


class FacturePatch(BaseModel):
    date_facture: Optional[str] = None
    date_echeance: Optional[str] = None
    remise_globale: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=1000)
    lignes: Optional[List[LigneFactureIn]] = None


class FactureOut(BaseModel):
    facture_id: str
    reference: str
    type_facture: TypeFacture
    client_id: str
    client_nom: Optional[str] = None
    commande_id: Optional[str] = None
    commande_reference: Optional[str] = None
    statut: Statut
    date_facture: str
    date_echeance: Optional[str] = None
    date_emission: Optional[str] = None
    remise_globale: float
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    montant_regle: float
    montant_restant: float
    notes: Optional[str] = None
    facture_origine_id: Optional[str] = None  # Pour les avoirs
    created_by: str
    created_at: str
    updated_at: str


class FactureDetail(FactureOut):
    lignes: List[LigneFactureOut]


class GenerateFactureFromCommandeIn(BaseModel):
    commande_id: str
    date_facture: Optional[str] = None
    date_echeance: Optional[str] = None


class GenerateAvoirIn(BaseModel):
    facture_id: str
    montant: float = Field(..., gt=0)
    motif: str = Field(..., min_length=10, max_length=500)


class WhatsAppPayload(BaseModel):
    numero: Optional[str] = None


class EmailPayload(BaseModel):
    destinataire: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    objet: Optional[str] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
async def _get_client_nom(db: AsyncIOMotorDatabase, client_id: str) -> Optional[str]:
    client = await db.clients.find_one({"client_id": client_id}, {"_id": 0, "nom": 1})
    return client["nom"] if client else None


async def _get_commande_reference(db: AsyncIOMotorDatabase, commande_id: str) -> Optional[str]:
    cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0, "reference": 1})
    return cmd["reference"] if cmd else None


async def _calculate_totals(lignes: List[LigneFactureIn], remise_globale: float, taux_tva: float = 18.0) -> dict:
    """Calculate montant_ht, montant_tva, montant_ttc"""
    montant_ht_brut = sum(l.montant_ht for l in lignes)
    montant_remise_globale = montant_ht_brut * (remise_globale / 100)
    montant_ht = montant_ht_brut - montant_remise_globale
    montant_tva = montant_ht * (taux_tva / 100)
    montant_ttc = montant_ht + montant_tva
    
    return {
        "montant_ht": round(montant_ht, 2),
        "montant_tva": round(montant_tva, 2),
        "montant_ttc": round(montant_ttc, 2),
    }


async def _enrich_facture_with_client(db: AsyncIOMotorDatabase, facture: dict) -> dict:
    """Add client_nom and commande_reference to facture dict"""
    if facture.get("client_id"):
        facture["client_nom"] = await _get_client_nom(db, facture["client_id"])
    if facture.get("commande_id"):
        facture["commande_reference"] = await _get_commande_reference(db, facture["commande_id"])
    return facture


async def _get_facture_with_lignes(db: AsyncIOMotorDatabase, facture_id: str) -> Optional[dict]:
    """Fetch facture + lignes"""
    facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
    if not facture:
        return None
    
    # Fetch lignes
    lignes_cursor = db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0})
    lignes = await lignes_cursor.to_list(500)

    await _enrich_lignes_produit(db, lignes)
    facture["lignes"] = lignes
    await _enrich_facture_with_client(db, facture)
    return facture


async def _enrich_lignes_produit(db: AsyncIOMotorDatabase, lignes: list) -> None:
    """Ajoute code_article (reference), niveau (niveau_scolaire) et cycle aux lignes
    de vente en récupérant les vraies données produit. Utilisé pour PDF/WhatsApp/email."""
    try:
        from pdf_generator import enrich_lignes_for_pdf
    except Exception:
        return
    pids = list({(l.get("produit_id") or l.get("product_id")) for l in lignes if (l.get("produit_id") or l.get("product_id"))})
    if not pids:
        return
    prods = await db.produits.find(
        {"$or": [{"product_id": {"$in": pids}}, {"produit_id": {"$in": pids}}]}, {"_id": 0}
    ).to_list(1000)
    by_id = {(p.get("product_id") or p.get("produit_id")): p for p in prods}
    enrich_lignes_for_pdf(by_id, lignes)


async def _update_facture_statut(db: AsyncIOMotorDatabase, facture_id: str) -> None:
    """Update facture statut based on montant_regle"""
    facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
    if not facture:
        return
    
    montant_ttc = facture["montant_ttc"]
    montant_regle = facture["montant_regle"]
    
    if montant_regle >= montant_ttc:
        new_statut = "payee"
    elif montant_regle > 0:
        new_statut = "partiellement_payee"
    else:
        new_statut = facture["statut"]  # Keep current if no payment
    
    await db.factures.update_one(
        {"facture_id": facture_id},
        {"$set": {
            "statut": new_statut,
            "montant_restant": round(montant_ttc - montant_regle, 2),
            "updated_at": _now_iso(),
        }}
    )


# ---------------------------------------------------------------------------
# Router Builder
# ---------------------------------------------------------------------------
def build_factures_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/factures", tags=["factures"])

    # ---------- LIST ----------
    @router.get("")
    async def list_factures(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        type_facture: Optional[TypeFacture] = None,
        statut: Optional[Statut] = None,
        client_id: Optional[str] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        q: Optional[str] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        # Secrétariat : uniquement les factures générées depuis une commande
        if me["role"] == "secretariat":
            filters["commande_id"] = {"$ne": None, "$exists": True}
        if type_facture:
            filters["type_facture"] = type_facture
        if statut:
            filters["statut"] = statut
        if client_id:
            filters["client_id"] = client_id
        if date_debut or date_fin:
            date_filter = {}
            if date_debut:
                date_filter["$gte"] = date_debut
            if date_fin:
                date_filter["$lte"] = date_fin
            filters["date_facture"] = date_filter
        
        # Use aggregation with $lookup to avoid N+1 queries
        pipeline = [
            {"$match": filters},
            {"$lookup": {
                "from": "clients",
                "localField": "client_id",
                "foreignField": "client_id",
                "as": "client_info"
            }},
            {"$lookup": {
                "from": "commandes",
                "localField": "commande_id",
                "foreignField": "commande_id",
                "as": "commande_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
                "commande_reference": {"$arrayElemAt": ["$commande_info.reference", 0]}
            }},
            {"$project": {
                "client_info": 0,
                "commande_info": 0,
                "_id": 0
            }},
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
        pipeline_count = [{"$match": filters}]
        if q:
            safe_q = re.escape(q)
            pipeline_count.append({"$match": {"$or": [
                {"reference": {"$regex": safe_q, "$options": "i"}},
                {"client_nom": {"$regex": safe_q, "$options": "i"}},
                {"client_ville": {"$regex": safe_q, "$options": "i"}},
                {"client_telephone": {"$regex": safe_q, "$options": "i"}},
                {"client_representant": {"$regex": safe_q, "$options": "i"}},
            ]}})
        pipeline_count.append({"$count": "total"})

        pipeline += [
            {"$sort": {"date_facture": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]

        docs, count_res = await asyncio.gather(
            db.factures.aggregate(pipeline).to_list(limit),
            db.factures.aggregate(pipeline_count).to_list(1),
        )
        total = count_res[0]["total"] if count_res else 0
        page = (skip // limit) + 1 if limit else 1
        items = []
        for d in docs:
            try:
                items.append(FactureOut(**d).model_dump())
            except Exception as exc:
                logger.error(
                    "Facture doc invalide ignorée (numero=%s): %s",
                    d.get("numero") or d.get("_id"), exc,
                )
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": skip + limit < total,
        }

    # ---------- CREATE ----------
    @router.post("", response_model=FactureOut, status_code=201)
    async def create_facture(
        payload: FactureIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        type_facture: TypeFacture = Query("facture"),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Verify client exists
        client = await db.clients.find_one({"client_id": payload.client_id, "actif": True}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable ou inactif")

        # Verify commande if provided
        if payload.commande_id:
            cmd = await db.commandes.find_one({"commande_id": payload.commande_id}, {"_id": 0})
            _ensure(cmd is not None, 404, "Commande introuvable")
            # Unicité : une seule facture de type "facture" par commande
            existing = await db.factures.find_one(
                {"commande_id": payload.commande_id, "type_facture": "facture"},
                {"_id": 0, "reference": 1}
            )
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Une facture existe déjà pour cette commande : {existing['reference']}"
                )

        # Calculate totals
        totals = await _calculate_totals(payload.lignes, payload.remise_globale, payload.taux_tva)

        # Create facture
        facture_id = f"fac_{uuid.uuid4().hex[:12]}"
        reference = await next_facture_reference(db, type_facture)
        date_facture = payload.date_facture or _now_iso()[:10]

        now = _now_iso()
        facture_doc = {
            "facture_id": facture_id,
            "reference": reference,
            "type_facture": type_facture,
            "client_id": payload.client_id,
            "commande_id": payload.commande_id,
            "statut": "brouillon",
            "date_facture": date_facture,
            "date_echeance": payload.date_echeance,
            "date_emission": None,
            "taux_tva": payload.taux_tva,
            "remise_globale": payload.remise_globale,
            "montant_ht": totals["montant_ht"],
            "montant_tva": totals["montant_tva"],
            "montant_ttc": totals["montant_ttc"],
            "total_ttc": totals["montant_ttc"],
            "montant_regle": 0.0,
            "montant_restant": totals["montant_ttc"],
            "notes": payload.notes,
            "facture_origine_id": None,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.factures.insert_one(facture_doc)

        # Create lignes
        for ligne in payload.lignes:
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "facture_id": facture_id,
                "produit_id": ligne.produit_id,
                "designation": ligne.designation,
                "quantite": ligne.quantite,
                "prix_unitaire": ligne.prix_unitaire,
                "remise_ligne": ligne.remise_ligne,
                "montant_ht": ligne.montant_ht,
            }
            await db.facture_lignes.insert_one(ligne_doc)

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_FACTURE",
                resource_type="facture",
                resource_id=facture_id,
                details={
                    "reference": reference,
                    "type_facture": type_facture,
                    "client_id": payload.client_id,
                    "commande_id": payload.commande_id,
                    "montant_ttc": totals["montant_ttc"],
                    "lignes_count": len(payload.lignes)
                },
                ip_address=request.client.host if request.client else None
            )

        # Return with client_nom
        facture_doc["client_nom"] = client["nom"]
        if payload.commande_id:
            facture_doc["commande_reference"] = await _get_commande_reference(db, payload.commande_id)

        # 🔔 Notification vente — nouvelle facture
        try:
            await notify_vente_event(
                db, "success", "paiement",
                f"🧾 Nouvelle facture {facture_doc['reference']}",
                f"Facture générée pour {client['nom']} — {facture_doc['montant_ttc']:,.0f} FCFA",
                lien=f"/factures/{facture_doc['facture_id']}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify create_facture: %s", _e)

        return FactureOut(**facture_doc)

    # ---------- GENERATE FROM COMMANDE ----------
    @router.post("/generer-depuis-commande", response_model=FactureOut, status_code=201)
    async def generate_facture_from_commande(
        payload: GenerateFactureFromCommandeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Get commande with lignes
        cmd = await db.commandes.find_one({"commande_id": payload.commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        # Unicité : une seule facture de type "facture" par commande
        existing = await db.factures.find_one(
            {"commande_id": payload.commande_id, "type_facture": "facture"},
            {"_id": 0, "reference": 1}
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Une facture existe déjà pour cette commande : {existing['reference']}"
            )
        _ensure(cmd["statut"] in {"validee", "preparee", "livree"}, 400, "Commande doit être validée, préparée ou livrée")

        # Get commande lignes
        lignes_cursor = db.commande_lignes.find({"commande_id": payload.commande_id}, {"_id": 0})
        cmd_lignes = await lignes_cursor.to_list(500)
        _ensure(len(cmd_lignes) > 0, 400, "Commande sans lignes")

        # Get product designations
        lignes_facture = []
        for ligne in cmd_lignes:
            pid = ligne["produit_id"]
            prod = await db.produits.find_one(
                {"$or": [{"product_id": pid}, {"$or": [{"product_id": pid}, {"produit_id": pid}]}]},
                {"_id": 0, "titre": 1, "matiere": 1, "niveau_scolaire": 1, "cycle": 1, "categorie": 1}
            )
            lignes_facture.append(LigneFactureIn(
                produit_id=pid,
                designation=prod["titre"] if prod else pid,
                quantite=ligne["quantite"],
                prix_unitaire=ligne["prix_unitaire"],
                remise_ligne=ligne["remise_ligne"],
            ))

        # Create facture — hériter taux_tva de la commande
        taux_tva_cmd = cmd.get("taux_tva", 18.0)
        facture_in = FactureIn(
            client_id=cmd["client_id"],
            commande_id=payload.commande_id,
            date_facture=payload.date_facture or _now_iso()[:10],
            date_echeance=payload.date_echeance,
            remise_globale=cmd["remise_globale"],
            taux_tva=taux_tva_cmd,
            notes=f"Facture générée depuis commande {cmd['reference']}",
            lignes=lignes_facture,
        )

        # Use create_facture logic
        totals = await _calculate_totals(facture_in.lignes, facture_in.remise_globale, facture_in.taux_tva)
        
        facture_id = f"fac_{uuid.uuid4().hex[:12]}"
        reference = await next_facture_reference(db, "facture")
        
        now = _now_iso()
        facture_doc = {
            "facture_id": facture_id,
            "reference": reference,
            "type_facture": "facture",
            "client_id": facture_in.client_id,
            "commande_id": facture_in.commande_id,
            "statut": "emise",
            "date_facture": facture_in.date_facture,
            "date_echeance": facture_in.date_echeance,
            "date_emission": now[:10],
            "remise_globale": facture_in.remise_globale,
            "montant_ht": totals["montant_ht"],
            "montant_tva": totals["montant_tva"],
            "montant_ttc": totals["montant_ttc"],
            "montant_regle": 0.0,
            "montant_restant": totals["montant_ttc"],
            "notes": facture_in.notes,
            "facture_origine_id": None,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.factures.insert_one(facture_doc)

        # Create lignes
        for ligne in facture_in.lignes:
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "facture_id": facture_id,
                "produit_id": ligne.produit_id,
                "designation": ligne.designation,
                "quantite": ligne.quantite,
                "prix_unitaire": ligne.prix_unitaire,
                "remise_ligne": ligne.remise_ligne,
                "montant_ht": ligne.montant_ht,
            }
            await db.facture_lignes.insert_one(ligne_doc)

        # Enrich and return
        await _enrich_facture_with_client(db, facture_doc)

        # 🔔 Notification vente — facture depuis commande
        try:
            _client_nom = facture_doc.get("client_nom", "")
            await notify_vente_event(
                db, "success", "paiement",
                f"🧾 Facture auto {facture_doc['reference']}",
                f"Facture générée depuis commande pour {_client_nom} — {facture_doc['montant_ttc']:,.0f} FCFA",
                lien=f"/factures/{facture_doc['facture_id']}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify generate_facture_from_commande: %s", _e)

        return FactureOut(**facture_doc)

    # ---------- GET DETAIL ----------
    @router.get("/{facture_id}", response_model=FactureDetail)
    async def get_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        facture = await _get_facture_with_lignes(db, facture_id)
        _ensure(facture is not None, 404, "Facture introuvable")
        
        return FactureDetail(**facture)

    # ---------- UPDATE ----------
    @router.patch("/{facture_id}", response_model=FactureOut)
    async def update_facture(
        facture_id: str,
        payload: FacturePatch,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        _ensure(facture is not None, 404, "Facture introuvable")
        _ensure(facture["statut"] == "brouillon", 400, "Seules les factures brouillon peuvent être modifiées")

        updates = {"updated_at": _now_iso()}
        
        if payload.date_facture is not None:
            updates["date_facture"] = payload.date_facture
        
        if payload.date_echeance is not None:
            updates["date_echeance"] = payload.date_echeance
        
        if payload.remise_globale is not None:
            updates["remise_globale"] = payload.remise_globale
        
        if payload.notes is not None:
            updates["notes"] = payload.notes
        
        # Update lignes if provided
        if payload.lignes is not None:
            _ensure(len(payload.lignes) > 0, 400, "Au moins une ligne requise")
            
            # Delete old lignes
            await db.facture_lignes.delete_many({"facture_id": facture_id})
            
            # Create new lignes
            for ligne in payload.lignes:
                ligne_doc = {
                    "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                    "facture_id": facture_id,
                    "produit_id": ligne.produit_id,
                    "designation": ligne.designation,
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "remise_ligne": ligne.remise_ligne,
                    "montant_ht": ligne.montant_ht,
                }
                await db.facture_lignes.insert_one(ligne_doc)
            
            # Recalculate totals — conserver taux_tva existant si non modifié
            taux_tva_upd = payload.taux_tva if hasattr(payload, "taux_tva") and payload.taux_tva is not None else facture.get("taux_tva", 18.0)
            totals = await _calculate_totals(payload.lignes, payload.remise_globale or facture["remise_globale"], taux_tva_upd)
            updates.update(totals)
            updates["total_ttc"] = totals["montant_ttc"]
            updates["montant_restant"] = totals["montant_ttc"]

        await db.factures.update_one({"facture_id": facture_id}, {"$set": updates})
        
        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="UPDATE_FACTURE",
                resource_type="facture",
                resource_id=facture_id,
                details={
                    "reference": facture["reference"],
                    "type_facture": facture["type_facture"],
                    "client_id": facture["client_id"],
                    "old_statut": facture["statut"],
                    "updates": {k: v for k, v in updates.items() if k not in ["updated_at", "montant_restant"]}
                },
                ip_address=request.client.host if request.client else None
            )
        
        updated = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        await _enrich_facture_with_client(db, updated)
        return FactureOut(**updated)

    # ---------- EMETTRE (EMIT) ----------
    @router.post("/{facture_id}/emettre", response_model=FactureOut)
    async def emettre_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        _ensure(facture is not None, 404, "Facture introuvable")
        _ensure(facture["statut"] == "brouillon", 400, "Seules les factures brouillon peuvent être émises")

        now = _now_iso()
        await db.factures.update_one(
            {"facture_id": facture_id},
            {"$set": {
                "statut": "emise",
                "date_emission": now[:10],
                "updated_at": now,
            }}
        )
        
        # Génération automatique des écritures comptables
        if facture["type_facture"] == "facture":
            try:
                await generate_ecriture_comptable_facture(
                    db=db,
                    facture_id=facture_id,
                    facture_reference=facture["reference"],
                    client_id=facture["client_id"],
                    montant_ht=facture["montant_ht"],
                    montant_tva=facture["montant_tva"],
                    montant_ttc=facture["montant_ttc"],
                    user_id=me["user_id"],
                    log_audit_event=log_audit_event
                )
                logger.info(f"✅ Écritures comptables générées pour facture {facture['reference']}")
            except Exception as e:
                logger.error(f"❌ Erreur génération écritures comptables pour facture {facture['reference']}: {e}")
        
        # Création automatique de l'ordre de colisage
        if facture.get("type_facture", "facture") == "facture":
            try:
                from colisage_module import _create_ordre_colisage_internal
                oc = await _create_ordre_colisage_internal(db, facture_id, me["user_id"])
                logger.info(f"✅ Ordre de colisage créé automatiquement: {oc.get('reference')} pour {facture['reference']}")
            except Exception as e:
                logger.error(f"❌ Erreur création ordre de colisage pour facture {facture['reference']}: {e}")

        updated = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        await _enrich_facture_with_client(db, updated)
        return FactureOut(**updated)

    # ---------- CERTIFIER FNE (MANUEL) ----------
    @router.post("/{facture_id}/certifier-fne", response_model=FactureOut)
    async def certifier_fne(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Certifie manuellement une facture via l'API FNE de la DGI"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        _ensure(facture is not None, 404, "Facture introuvable")
        _ensure(facture["statut"] == "emise", 400, "Seules les factures émises peuvent être certifiées")
        _ensure(facture["type_facture"] == "facture", 400, "Seules les factures peuvent être certifiées (pas les avoirs)")
        _ensure(facture.get("fne_status") in [None, "pending", "failed"], 400, "Facture déjà certifiée ou en cours de certification")

        # Déclenchement de la certification FNE (asynchrone)
        try:
            from fne_queue import FNEQueue
            
            # Récupérer les données du client
            client = await db.clients.find_one({"client_id": facture["client_id"]}, {"_id": 0})
            
            # Récupérer les lignes de facture
            lignes_cursor = db.facture_lignes.find({"facture_id": facture_id}, {"_id": 0})
            lignes_facture = []
            async for ligne in lignes_cursor:
                lignes_facture.append(ligne)
            
            # Préparer les données pour FNE
            invoice_data = {
                "reference": facture["reference"],
                "client_nom": client["nom"] if client else "",
                "client_ncc": client.get("ncc"),
                "client_telephone": client.get("telephone", ""),
                "client_email": client.get("email"),
                "client_type": client.get("type_client", "entreprise"),
                "payment_method": facture.get("mode_paiement", "cash"),
                "date_facture": facture["date_facture"],
                "montant_ht": facture["montant_ht"],
                "montant_tva": facture["montant_tva"],
                "montant_ttc": facture["montant_ttc"],
                "remise_globale": facture["remise_globale"],
                "vendeur": me.get("nom", "Système"),
                "point_of_vente": "SIEGE FABS-CI",
                "etablissement": "EDITIONS FABS-CI"
            }
            
            # Déduire le code taxe DGI depuis taux_tva de la facture (C5)
            taux_tva_facture = facture.get("taux_tva", 18.0)
            if taux_tva_facture == 0:
                taxes_dgi = []           # Exonéré
            elif taux_tva_facture <= 9:
                taxes_dgi = ["TVAB"]     # TVA réduite 9%
            else:
                taxes_dgi = ["TVA"]      # TVA normale 18%

            items_data = []
            for ligne in lignes_facture:
                # Chaque ligne peut avoir son propre taux — on garde la même logique
                ligne_taux = ligne.get("taux_tva", taux_tva_facture)
                if ligne_taux == 0:
                    ligne_taxes = []
                elif ligne_taux <= 9:
                    ligne_taxes = ["TVAB"]
                else:
                    ligne_taxes = ["TVA"]

                items_data.append({
                    "reference": ligne.get("reference", ""),
                    "description": ligne["designation"],
                    "quantity": ligne["quantite"],
                    "prix_unitaire": ligne["prix_unitaire"],
                    "remise": ligne["remise_ligne"],
                    "unite": ligne.get("unite", "pcs"),
                    "taxes": ligne_taxes,
                    "custom_taxes": []
                })
            
            # Enqueue la certification FNE
            queue = FNEQueue(db)
            await queue.enqueue_invoice_certification(
                invoice_id=facture["reference"],
                invoice_data=invoice_data,
                items_data=items_data
            )
            
            # Mettre à jour le statut FNE à pending
            await db.factures.update_one(
                {"facture_id": facture_id},
                {"$set": {"fne_status": "pending", "fne_submitted_at": _now_iso()}}
            )
            
            logger.info(f"📋 Certification FNE enqueued pour facture {facture['reference']}")
        except Exception as e:
            logger.error(f"❌ Erreur enqueue certification FNE pour facture {facture['reference']}: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de la certification FNE")
        
        updated = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
        await _enrich_facture_with_client(db, updated)
        return FactureOut(**updated)

    # ---------- GENERER AVOIR ----------
    @router.post("/generer-avoir", response_model=FactureOut, status_code=201)
    async def generer_avoir(
        payload: GenerateAvoirIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Get original facture
        facture_orig = await _get_facture_with_lignes(db, payload.facture_id)
        _ensure(facture_orig is not None, 404, "Facture origine introuvable")
        _ensure(facture_orig["type_facture"] == "facture", 400, "Impossible de créer un avoir depuis un avoir")
        _ensure(payload.montant <= facture_orig["montant_ttc"], 400, "Montant avoir supérieur au montant facture")

        # Create avoir with same lignes but negative amounts
        avoir_id = f"fac_{uuid.uuid4().hex[:12]}"
        reference = await next_facture_reference(db, "avoir")
        
        # Calculate proportional amounts
        ratio = payload.montant / facture_orig["montant_ttc"]
        montant_ht = round(facture_orig["montant_ht"] * ratio, 2)
        montant_tva = round(facture_orig["montant_tva"] * ratio, 2)
        montant_ttc = round(payload.montant, 2)

        now = _now_iso()
        avoir_doc = {
            "avoir_id": avoir_id,
            "reference": reference,
            "type_facture": "avoir",
            "client_id": facture_orig["client_id"],
            "commande_id": facture_orig.get("commande_id"),
            "statut": "emise",
            "date_facture": now[:10],
            "date_echeance": None,
            "date_emission": now[:10],
            "remise_globale": 0,
            "montant_ht": -montant_ht,  # Negative
            "montant_tva": -montant_tva,
            "montant_ttc": -montant_ttc,
            "montant_regle": 0.0,
            "montant_restant": -montant_ttc,
            "notes": f"Avoir généré depuis facture {facture_orig['reference']}. Motif: {payload.motif}",
            "facture_origine_id": payload.facture_id,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        # Fix: use facture_id as key
        avoir_doc["facture_id"] = avoir_id
        await db.factures.insert_one(avoir_doc)

        # Copy lignes (proportional quantities)
        for ligne_orig in facture_orig["lignes"]:
            ligne_avoir = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "facture_id": avoir_id,
                "produit_id": ligne_orig["produit_id"],
                "designation": ligne_orig["designation"],
                "quantite": -int(ligne_orig["quantite"] * ratio),  # Negative
                "prix_unitaire": ligne_orig["prix_unitaire"],
                "remise_ligne": ligne_orig["remise_ligne"],
                "montant_ht": -round(ligne_orig["montant_ht"] * ratio, 2),
            }
            await db.facture_lignes.insert_one(ligne_avoir)

        # Génération automatique des écritures comptables pour l'avoir
        try:
            await generate_ecriture_comptable_avoir(
                db=db,
                avoir_id=avoir_id,
                avoir_reference=reference,
                client_id=facture_orig["client_id"],
                montant_ht=montant_ht,
                montant_tva=montant_tva,
                montant_ttc=montant_ttc,
                facture_origine_id=payload.facture_id,
                user_id=me["user_id"],
                log_audit_event=log_audit_event
            )
            logger.info(f"✅ Écritures comptables générées pour avoir {reference}")
        except Exception as e:
            logger.error(f"❌ Erreur génération écritures comptables pour avoir {reference}: {e}")

        # Enrich and return
        await _enrich_facture_with_client(db, avoir_doc)
        return FactureOut(**avoir_doc)

    # ---------- PDF ----------
    @router.get("/{facture_id}/pdf")
    async def facture_pdf(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse
        from pdf_generator import generate_facture_pdf

        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        facture = await _get_facture_with_lignes(db, facture_id)
        _ensure(facture is not None, 404, "Facture introuvable")

        client = await db.clients.find_one({"client_id": facture["client_id"]}, {"_id": 0}) or {}
        # Inject representant from client into facture context if missing
        facture.setdefault("representant", client.get("representant"))

        buffer = generate_facture_pdf(facture, facture.get("lignes", []), client)
        filename = f"{facture['reference']}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    # ---------- WHATSAPP ----------
    @router.post("/{facture_id}/envoyer-whatsapp")
    async def envoyer_facture_whatsapp(
        facture_id: str,
        payload: WhatsAppPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Prepare WhatsApp sharing link for Facture"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await _get_facture_with_lignes(db, facture_id)
        _ensure(facture is not None, 404, "Facture introuvable")

        # Get client WhatsApp number
        client = await db.clients.find_one({"client_id": facture["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        whatsapp_number = (payload.numero if payload and payload.numero else None) \
            or client.get("numero_whatsapp") or client.get("telephone")
        _ensure(whatsapp_number, 400, "Numéro WhatsApp non disponible — veuillez en saisir un")

        # Clean phone number
        clean_number = whatsapp_number.replace(" ", "").replace("-", "").replace("+", "")

        # Prepare message
        message = f"""Bonjour {client.get('nom', 'Client')}

Veuillez trouver ci-joint votre FACTURE N° {facture['reference']}

Montant TTC : {facture['montant_ttc']:,.2f} FCFA

Merci de votre confiance.

Cordialement,
ÉDITIONS FABS-CI"""

        # WhatsApp URL
        encoded_message = message.replace("\n", "%0A")
        whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"

        # Update facture tracking
        await db.factures.update_one(
            {"facture_id": facture_id},
            {
                "$set": {
                    "date_envoi_whatsapp": _now_iso(),
                    "updated_at": _now_iso()
                }
            }
        )

        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
            "user_id": me["user_id"],
            "action": "SEND_WHATSAPP",
            "resource_type": "facture",
            "resource_id": facture_id,
            "details": {"whatsapp_number": clean_number},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })

        return {
            "whatsapp_url": whatsapp_url,
            "message": message,
            "pdf_filename": f"{facture['reference']}.pdf"
        }

    # ---------- PARTAGER WHATSAPP (Web Share API — sans numéro) ----------
    @router.post("/{facture_id}/partager-whatsapp")
    async def partager_facture_whatsapp(
        facture_id: str,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Log a WhatsApp native share event (no phone number required)."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0, "reference": 1})
        _ensure(facture is not None, 404, "Facture introuvable")

        now = _now_iso()
        await db.factures.update_one(
            {"facture_id": facture_id},
            {"$set": {"date_partage_whatsapp": now, "updated_at": now}}
        )
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
            "user_id": me["user_id"],
            "action": "SHARE_WHATSAPP_NATIVE",
            "resource_type": "facture",
            "resource_id": facture_id,
            "details": {"canal": "whatsapp", "statut": "partage_lance", "methode": "web_share_api"},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        return {"message": "Partage WhatsApp enregistré", "reference": facture.get("reference")}

    # ---------- EMAIL ----------
    @router.post("/{facture_id}/envoyer-email")
    async def envoyer_facture_email(
        facture_id: str,
        payload: EmailPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Send Facture via Email"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        facture = await _get_facture_with_lignes(db, facture_id)
        _ensure(facture is not None, 404, "Facture introuvable")

        # Get client email
        client = await db.clients.find_one({"client_id": facture["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        # Destinataire : payload override ou email client
        if payload and payload.destinataire:
            client_email = payload.destinataire
        else:
            client_email = client.get("email")
        _ensure(client_email, 400, "Email non disponible — veuillez en saisir un")

        # Generate PDF
        from pdf_generator import generate_facture_pdf
        pdf_buffer = generate_facture_pdf(facture, facture.get("lignes", []), client)
        
        # Prepare email content — payload override si fourni
        sujet = (payload.objet if payload and payload.objet else None) or \
            f"Facture {facture['reference']} - ÉDITIONS FABS-CI"
        corps_texte = (payload.message if payload and payload.message else None) or \
            f"""Bonjour {client.get('nom', 'Client')},

Veuillez trouver ci-joint votre facture {facture['reference']}.

Montant TTC : {facture['montant_ttc']:,.2f} FCFA

Merci de votre confiance.

Cordialement,
ÉDITIONS FABS-CI"""

        corps_html = f"""
<html>
<body>
    <h2>Facture {facture['reference']}</h2>
    <p>Bonjour {client.get('nom', 'Client')},</p>
    <p>Veuillez trouver ci-joint votre facture {facture['reference']}.</p>
    <p><strong>Montant TTC : {facture['montant_ttc']:,.2f} FCFA</strong></p>
    <p>Merci de votre confiance.</p>
    <p>Cordialement,<br>ÉDITIONS FABS-CI</p>
</body>
</html>"""

        # Send email with PDF attachment
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = os.getenv("SMTP_PORT", "587")
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_from = os.getenv("SMTP_FROM")
            
            if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
                raise HTTPException(
                    status_code=503,
                    detail="Service email non configuré. Contactez l'administrateur."
                )
            
            msg = MIMEMultipart("mixed")
            msg["Subject"] = sujet
            msg["From"] = smtp_from
            msg["To"] = client_email
            
            # Attach HTML body
            msg.attach(MIMEText(corps_html, "html", "utf-8"))
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype="pdf")
            pdf_attachment.add_header("Content-Disposition", "attachment", filename=f"{facture['reference']}.pdf")
            msg.attach(pdf_attachment)
            
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            # Update facture tracking
            await db.factures.update_one(
                {"facture_id": facture_id},
                {
                    "$set": {
                        "date_envoi_email": _now_iso(),
                        "updated_at": _now_iso()
                    }
                }
            )

            # Log audit
            await db.audit_logs.insert_one({
                "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
                "user_id": me["user_id"],
                "action": "SEND_EMAIL",
                "resource_type": "facture",
                "resource_id": facture_id,
                "details": {"email": client_email, "status": "sent"},
                "ip_address": request.client.host if request.client else None,
                "timestamp": _now_iso(),
            })

            return {
                "message": "Email envoyé avec succès",
                "email": client_email,
                "subject": sujet
            }
        except HTTPException:
            # Erreur déjà explicite (ex: 503 service non configuré) → on la laisse passer telle quelle
            raise
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
            logger.error(f"Erreur envoi email (SMTP): {e}")
            raise HTTPException(
                status_code=503,
                detail="Service email indisponible : identifiants SMTP invalides ou non configurés. "
                       "Vérifiez SMTP_USER / SMTP_PASSWORD côté serveur (mot de passe d'application requis pour Gmail)."
            )
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            # Log failed attempt
            await db.audit_logs.insert_one({
                "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
                "user_id": me["user_id"],
                "action": "SEND_EMAIL",
                "resource_type": "facture",
                "resource_id": facture_id,
                "details": {"email": client_email, "status": "failed", "error": str(e)},
                "ip_address": request.client.host if request.client else None,
                "timestamp": _now_iso(),
            })
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}")

    # ------------------------------------------------------------------
    # TICKET-015 — Relances automatiques factures en retard
    # ------------------------------------------------------------------

    async def _run_relances_once() -> dict:
        """
        Marque en 'en_retard' les factures émises/partiellement payées dont
        l'échéance est dépassée. Retourne un résumé {updated, errors}.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        updated = 0
        errors = 0
        cursor = db.factures.find(
            {
                "statut": {"$in": ["emise", "partiellement_payee"]},
                "date_echeance": {"$lt": today},
            },
            {"_id": 0, "facture_id": 1, "reference": 1, "client_id": 1},
        )
        async for facture in cursor:
            try:
                now_ts = _now_iso()
                await db.factures.update_one(
                    {"facture_id": facture["facture_id"]},
                    {"$set": {"statut": "en_retard", "updated_at": now_ts}},
                )
                if log_audit_event:
                    await log_audit_event(
                        user_id="system",
                        action="RELANCE_FACTURE_EN_RETARD",
                        resource_type="facture",
                        resource_id=facture["facture_id"],
                        details={
                            "reference": facture.get("reference"),
                            "client_id": facture.get("client_id"),
                            "new_statut": "en_retard",
                            "triggered_by": "auto_relance",
                        },
                        ip_address=None,
                    )
                updated += 1
            except Exception as _e:
                logger.error("relance facture %s failed: %s", facture.get("facture_id"), _e)
                errors += 1
        logger.info("TICKET-015 relances: %d updated, %d errors", updated, errors)
        return {"updated": updated, "errors": errors}

    @router.post("/relances/run", summary="Déclencher manuellement les relances factures en retard")
    async def run_relances(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """
        TICKET-015 — Marque en_retard toutes les factures émises/partiellement_payées
        dont la date d'échéance est dépassée. Accessible super_admin / comptable.
        """
        me = await resolve_user(request, authorization)
        # RBAC 2026-06-17: bug C1 corrigé — "DG" était invalide, DG retiré des factures
        _ensure(me["role"] in {"super_admin", "comptable"}, 403, "Accès refusé")
        result = await _run_relances_once()
        return {"status": "ok", **result}

    # Expose la fonction pour le job startup (server.py)
    router.run_relances_once = _run_relances_once  # type: ignore[attr-defined]

    return router


# ---------------------------------------------------------------------------
# Seed (optional demo data)
# ---------------------------------------------------------------------------
async def seed_factures(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed demo factures (optional)"""
    existing = await db.factures.count_documents({})
    if existing > 0:
        return 0
    
    # Get first client and first commande
    client = await db.clients.find_one({"actif": True}, {"_id": 0})
    if not client:
        return 0
    
    commandes = await db.commandes.find({"statut": {"$in": ["validee", "livree"]}}, {"_id": 0}).limit(2).to_list(2)
    if len(commandes) == 0:
        return 0

    demo_factures = []
    for i, cmd in enumerate(commandes):
        cmd_id = cmd.get("commande_id")
        if not cmd_id:
            continue
        # Get commande lignes
        lignes_cursor = db.commande_lignes.find({"commande_id": cmd_id}, {"_id": 0})
        cmd_lignes = await lignes_cursor.to_list(500)
        
        if len(cmd_lignes) == 0:
            continue

        facture_id = f"fac_{uuid.uuid4().hex[:12]}"
        reference = f"FABS-FC-26-27-{i+1:04d}"
        
        # Calculate totals from commande
        montant_ht = cmd["montant_ht"] - cmd["montant_remise"]
        montant_tva = round(montant_ht * TVA_RATE, 2)
        montant_ttc = round(montant_ht + montant_tva, 2)
        
        now = _now_iso()
        statut = "emise" if i == 0 else "payee"
        montant_regle = montant_ttc if i == 1 else 0.0
        
        facture_doc = {
            "facture_id": facture_id,
            "reference": reference,
            "type_facture": "facture",
            "client_id": cmd["client_id"],
            "commande_id": cmd_id,
            "statut": statut,
            "date_facture": now[:10],
            "date_echeance": None,
            "date_emission": now[:10],
            "remise_globale": cmd["remise_globale"],
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
            "montant_regle": montant_regle,
            "montant_restant": montant_ttc - montant_regle,
            "notes": f"Facture de démonstration {i+1}",
            "facture_origine_id": None,
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        }
        demo_factures.append(facture_doc)
        
        # Insert lignes
        for ligne in cmd_lignes:
            pid = ligne["produit_id"]
            prod = await db.produits.find_one(
                {"$or": [{"product_id": pid}, {"$or": [{"product_id": pid}, {"produit_id": pid}]}]},
                {"_id": 0, "titre": 1, "matiere": 1, "niveau_scolaire": 1, "cycle": 1, "categorie": 1}
            )
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "facture_id": facture_id,
                "produit_id": pid,
                "designation": prod["titre"] if prod else "Produit",
                "matiere": prod.get("matiere") if prod else None,
                "niveau_scolaire": prod.get("niveau_scolaire") if prod else None,
                "cycle": prod.get("cycle") if prod else None,
                "categorie": prod.get("categorie") if prod else None,
                "quantite": ligne["quantite"],
                "prix_unitaire": ligne["prix_unitaire"],
                "remise_ligne": ligne["remise_ligne"],
                "montant_ht": ligne["montant_ligne"],
            }
            await db.facture_lignes.insert_one(ligne_doc)
    
    if demo_factures:
        await db.factures.insert_many(demo_factures)
        # Update counter
        await db.counters.update_one(
            {"_id": "factures"},
            {"$set": {"seq": len(demo_factures)}},
            upsert=True
        )
    
    return len(demo_factures)
