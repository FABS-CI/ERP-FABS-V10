"""
Module Commandes — Sprint 6
- CRUD complet sur les collections MongoDB `commandes` et `commande_lignes`
- Référence auto-incrémentée FABS-CMD-26-27-XXXX
- Workflow : brouillon → en_attente → validee → preparee → livree → annulee
- Validation DG obligatoire si montant_total > 500 000 FCFA
- Actions : valider, préparer, livrer, annuler
- RBAC : 
    READ = {super_admin, DG, commercial, secrétariat, comptable}
    WRITE = {super_admin, DG, commercial, secrétariat}
    VALIDATE = DG (si > 500k), commercial (si <= 500k)
    PREPARE = magasinier
    DELIVER = logistique
- Génération PDF Bon de Commande
"""
from __future__ import annotations

from datetime import datetime, timezone, date
from typing import Literal, Optional, List
from decimal import Decimal
import re
import uuid
import logging
import os
import asyncio

from fastapi import APIRouter, HTTPException, Header, Query, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator
from sanitizers import sanitize_str
from pymongo.errors import InvalidOperation, OperationFailure
from notifications_module import notify_vente_event

logger = logging.getLogger("fabsci.commandes")

# RBAC
READ_ROLES = {
    # RBAC 2026-06-17: DG retiré de commandes
    "super_admin", "directeur_commercial",
    "secretariat", "comptable", "assistante",
    "gestionnaire_stock", "responsable_magasinier",
}
WRITE_ROLES = {
    # RBAC 2026-06-17: DG + dir_com retirés de WRITE
    "super_admin", "secretariat", "assistante", "comptable",
}
# RBAC 2026-06-17: DG + dir_com retirés de VALIDATE
VALIDATE_ROLES = {"super_admin", "secretariat", "comptable"}
# RBAC 2026-06-17: DG + dir_com retirés de CANCEL
CANCEL_ROLES = {"super_admin", "comptable", "secretariat"}
# RBAC 2026-06-17: DG retiré de PREPARE
PREPARE_ROLES = {"super_admin", "responsable_magasinier"}
# RBAC 2026-06-17: DG retiré de DELIVER
DELIVER_ROLES = {"super_admin", "service_logistique"}

Statut = Literal["brouillon", "en_attente", "validee", "preparee", "livree", "annulee"]
STATUT_FLOW = ["brouillon", "en_attente", "validee", "preparee", "livree"]

VALIDATION_THRESHOLD = 500_000  # FCFA


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


async def _send_email_smtp(destinataire: str, sujet: str, corps_html: str, corps_texte: str, pdf_buffer=None, pdf_filename=None) -> dict:
    """Envoyer email via SMTP avec option de pièce jointe PDF"""
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
        from email.mime.application import MIMEApplication
        
        msg = MIMEMultipart("mixed")
        msg["Subject"] = sujet
        msg["From"] = smtp_from
        msg["To"] = destinataire
        
        # Attach HTML body
        msg.attach(MIMEText(corps_html, "html", "utf-8"))
        
        # Attach PDF if provided
        if pdf_buffer and pdf_filename:
            pdf_attachment = MIMEApplication(pdf_buffer.getvalue(), _subtype="pdf")
            pdf_attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
            msg.attach(pdf_attachment)
        
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


async def next_commande_reference(db: AsyncIOMotorDatabase) -> str:
    """Generate FABS-CMD-26-27-XXXX reference"""
    doc = await db.counters.find_one_and_update(
        {"_id": "commandes"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-CMD-26-27-{seq:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class LigneCommandeIn(BaseModel):
    produit_id: Optional[str] = None
    product_id: Optional[str] = None
    quantite: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., gt=0)
    remise_ligne: float = Field(default=0, ge=0, le=100)  # percentage

    @field_validator('produit_id', 'product_id', mode='before')
    @classmethod
    def normalize_product_id(cls, v):
        if v is None:
            raise ValueError('produit_id ou product_id requis')
        return v

    @property
    def montant_ligne(self) -> float:
        base = self.quantite * self.prix_unitaire
        return base * (1 - self.remise_ligne / 100)


class LigneCommandeOut(BaseModel):
    ligne_id: str
    commande_id: str
    produit_id: str
    produit_reference: Optional[str] = None
    produit_titre: Optional[str] = None
    produit_matiere: Optional[str] = None
    produit_niveau_scolaire: Optional[str] = None
    produit_cycle: Optional[str] = None
    produit_categorie: Optional[str] = None
    quantite: int
    prix_unitaire: float
    remise_ligne: float
    montant_ligne: float


class CommandeIn(BaseModel):
    client_id: str
    date_livraison_prevue: Optional[str] = None  # ISO date YYYY-MM-DD
    remise_globale: float = Field(default=0, ge=0, le=100)
    taux_tva: float = Field(default=18.0, ge=0, le=100, description="Taux TVA en % (0 pour produits exonérés)")
    notes: Optional[str] = Field(default=None, max_length=1000)
    lignes: List[LigneCommandeIn] = Field(..., min_length=1)

    _san_notes = field_validator("notes", mode="before")(sanitize_str)

    @field_validator("date_livraison_prevue", mode="before")
    @classmethod
    def _validate_date(cls, v):
        if v:
            try:
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("Format de date invalide (YYYY-MM-DD attendu)")
        return v


class CommandePatch(BaseModel):
    client_id: Optional[str] = None
    date_livraison_prevue: Optional[str] = None
    remise_globale: Optional[float] = Field(default=None, ge=0, le=100)
    taux_tva: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=1000)
    lignes: Optional[List[LigneCommandeIn]] = None


class CommandeOut(BaseModel):
    commande_id: str
    reference: str
    client_id: str
    client_nom: Optional[str] = None
    statut: Statut
    date_commande: str
    date_livraison_prevue: Optional[str] = None
    date_validation: Optional[str] = None
    date_preparation: Optional[str] = None
    date_livraison: Optional[str] = None
    remise_globale: float = 0.0
    taux_tva: Optional[float] = 18.0
    montant_ht: float = 0.0
    montant_remise: float = 0.0
    montant_tva: Optional[float] = None
    montant_total: float = 0.0
    notes: Optional[str] = None
    motif_annulation: Optional[str] = None
    created_by: str
    validated_by: Optional[str] = None
    prepared_by: Optional[str] = None
    delivered_by: Optional[str] = None
    created_at: str
    updated_at: str


class CommandeDetail(CommandeOut):
    lignes: List[LigneCommandeOut]
    # État des transformations (anti-doublon UI) : facture/BL déjà générés
    transformations: Optional[dict] = None


class AnnulerCommandeIn(BaseModel):
    motif: str = Field(..., min_length=10, max_length=500)


class DoublonCheckIn(BaseModel):
    client_id: str
    lignes: List[LigneCommandeIn]
    representant: Optional[str] = None
    telephone: Optional[str] = None


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


async def _get_produit_info(db: AsyncIOMotorDatabase, produit_id: str) -> dict:
    produit = await db.produits.find_one(
        {"produit_id": produit_id},
        {"_id": 0, "reference": 1, "titre": 1, "prix_vente": 1,
         "matiere": 1, "niveau_scolaire": 1, "cycle": 1, "categorie": 1}
    )
    return produit or {}


async def _calculate_totals(lignes: List[LigneCommandeIn], remise_globale: float, taux_tva: float = 18.0) -> dict:
    """Calculate montant_ht, montant_remise, montant_tva, montant_total (TTC)"""
    montant_ht = sum(l.montant_ligne for l in lignes)
    montant_remise = montant_ht * (remise_globale / 100)
    montant_ht_net = montant_ht - montant_remise
    montant_tva = montant_ht_net * (taux_tva / 100)
    montant_total = montant_ht_net + montant_tva
    return {
        "montant_ht": round(montant_ht, 2),
        "montant_remise": round(montant_remise, 2),
        "montant_tva": round(montant_tva, 2),
        "montant_total": round(montant_total, 2),
    }


async def _enrich_commande_with_client(db: AsyncIOMotorDatabase, cmd: dict) -> dict:
    """Add client_nom to commande dict"""
    if cmd.get("client_id"):
        cmd["client_nom"] = await _get_client_nom(db, cmd["client_id"])
    return cmd


async def _get_commande_with_lignes(db: AsyncIOMotorDatabase, commande_id: str) -> Optional[dict]:
    """Fetch commande + lignes"""
    cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
    if not cmd:
        return None
    
    # Fetch lignes
    lignes_cursor = db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0})
    lignes = await lignes_cursor.to_list(500)
    
    # Enrich lignes with product info
    for ligne in lignes:
        prod_info = await _get_produit_info(db, ligne["produit_id"])
        ligne["produit_reference"] = prod_info.get("reference")
        ligne["produit_titre"] = prod_info.get("titre")
        ligne["produit_matiere"] = prod_info.get("matiere")
        ligne["produit_niveau_scolaire"] = prod_info.get("niveau_scolaire")
        ligne["produit_cycle"] = prod_info.get("cycle")
        ligne["produit_categorie"] = prod_info.get("categorie")
    
    cmd["lignes"] = lignes
    await _enrich_commande_with_client(db, cmd)
    return cmd


# ---------------------------------------------------------------------------
# Router Builder
# ---------------------------------------------------------------------------
def build_commandes_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/commandes", tags=["commandes"])

    # ---------- LIST ----------
    @router.get("")
    async def list_commandes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
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
            filters["date_commande"] = date_filter
        
        # Use aggregation with $lookup to avoid N+1 queries
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
            {"$project": {
                "client_info": 0,
                "_id": 0
            }},
        ]

        # Search full-text: reference, client_nom, ville, telephone, representant
        # C5 fix: échapper le paramètre q pour éviter ReDoS et injection NoSQL
        if q:
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
            {"$sort": {"date_commande": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]

        docs, count_res = await asyncio.gather(
            db.commandes.aggregate(pipeline).to_list(limit),
            db.commandes.aggregate(pipeline_count).to_list(1),
        )
        total = count_res[0]["total"] if count_res else 0
        page = (skip // limit) + 1 if limit else 1
        return {
            "items": [CommandeOut(**d).model_dump() for d in docs],
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": skip + limit < total,
        }

    # ---------- CREATE ----------
    @router.post("", response_model=CommandeOut, status_code=201)
    async def create_commande(
        payload: CommandeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
        submit: bool = Query(False, description="True to submit (en_attente), False for draft"),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Verify client exists
        client = await db.clients.find_one({"client_id": payload.client_id, "actif": True}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable ou inactif")

        # Verify all products exist and are active
        for ligne in payload.lignes:
            prod = await db.produits.find_one({"produit_id": ligne.produit_id, "actif": True}, {"_id": 0})
            _ensure(prod is not None, 404, f"Produit {ligne.produit_id} introuvable ou inactif")

        # Calculate totals
        totals = await _calculate_totals(payload.lignes, payload.remise_globale, payload.taux_tva)

        # Create commande
        commande_id = f"cmd_{uuid.uuid4().hex[:12]}"
        reference = await next_commande_reference(db)
        statut = "en_attente" if submit else "brouillon"

        now = _now_iso()
        commande_doc = {
            "commande_id": commande_id,
            "reference": reference,
            "client_id": payload.client_id,
            "statut": statut,
            "date_commande": now[:10],  # YYYY-MM-DD
            "date_livraison_prevue": payload.date_livraison_prevue,
            "date_validation": None,
            "date_preparation": None,
            "date_livraison": None,
            "remise_globale": payload.remise_globale,
            "taux_tva": payload.taux_tva,
            "montant_ht": totals["montant_ht"],
            "montant_remise": totals["montant_remise"],
            "montant_tva": totals["montant_tva"],
            "montant_total": totals["montant_total"],
            "notes": payload.notes,
            "motif_annulation": None,
            "created_by": me["user_id"],
            "validated_by": None,
            "prepared_by": None,
            "delivered_by": None,
            "created_at": now,
            "updated_at": now,
        }
        await db.commandes.insert_one(commande_doc)

        # Create lignes
        for ligne in payload.lignes:
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "commande_id": commande_id,
                "produit_id": ligne.produit_id,
                "quantite": ligne.quantite,
                "prix_unitaire": ligne.prix_unitaire,
                "remise_ligne": ligne.remise_ligne,
                "montant_ligne": ligne.montant_ligne,
            }
            await db.commande_lignes.insert_one(ligne_doc)

        # Audit log création commande
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_COMMANDE",
                resource_type="commande",
                resource_id=commande_id,
                details={
                    "reference": reference,
                    "client_id": payload.client_id,
                    "statut": statut,
                    "montant_total": totals["montant_total"],
                    "lignes_count": len(payload.lignes)
                },
                ip_address=request.client.host if request.client else None
            )

        # 🆕 GÉNÉRATION AUTOMATIQUE PROFORMA À LA CRÉATION
        try:
            from proformas_module import next_proforma_reference, _generate_id as _pro_generate_id

            proforma_id = _pro_generate_id("pro")
            reference_proforma = await next_proforma_reference(db)
            pro_now = _now_iso()

            # Dates
            date_emission = pro_now[:10]
            from datetime import timedelta
            date_emission_dt = datetime.fromisoformat(date_emission)
            date_expiration = (date_emission_dt + timedelta(days=30)).isoformat()

            # Montants (HT net après remise globale)
            montant_ht_net = round(totals["montant_ht"] - totals["montant_remise"], 2)
            montant_tva = totals["montant_tva"]
            montant_ttc = totals["montant_total"]

            proforma_doc = {
                "proforma_id": proforma_id,
                "numero_proforma": reference_proforma,
                "reference": reference_proforma,
                "client_id": payload.client_id,
                "commande_id": commande_id,
                "date_emission": date_emission,
                "date_expiration": date_expiration,
                "statut_proforma": "generee",
                "taux_tva": payload.taux_tva,
                "montant_ht": montant_ht_net,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc,
                "remise_globale": payload.remise_globale,
                "notes": f"Proforma auto depuis commande {reference}",
                "commercial_responsable_id": None,
                "envoye_whatsapp": False,
                "envoye_email": False,
                "nombre_impressions": 0,
                "nombre_telechargements": 0,
                "utilisateur_generation": me["user_id"],
                "actif": True,
                "created_by": me["user_id"],
                "created_at": pro_now,
                "updated_at": pro_now,
            }
            await db.proformas.insert_one(proforma_doc)

            # Lignes proforma depuis lignes commande
            for ligne in payload.lignes:
                await db.proforma_lignes.insert_one({
                    "ligne_id": _pro_generate_id("lpr"),
                    "proforma_id": proforma_id,
                    "produit_id": ligne.produit_id,
                    "designation": "",
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "remise_ligne": ligne.remise_ligne,
                    "montant_ht": ligne.montant_ligne,
                })

            logger.info(f"✅ Proforma auto {reference_proforma} créée pour commande {reference}")
        except Exception as e_pro:
            logger.error(f"⚠️ Erreur proforma auto à la création (non bloquant): {e_pro}")

        # Return with client_nom
        commande_doc["client_nom"] = client["nom"]

        # 🔔 Notification vente — nouvelle commande
        try:
            _notif_statut = "brouillon" if not submit else "en attente de validation"
            await notify_vente_event(
                db, "success", "commande",
                f"📦 Nouvelle commande {reference}",
                f"Commande créée pour {client['nom']} — {totals['montant_total']:,.0f} FCFA ({_notif_statut})",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify create_commande: %s", _e)

        return CommandeOut(**commande_doc)

    # ---------- GET DETAIL ----------
    @router.get("/{commande_id}", response_model=CommandeDetail)
    async def get_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        cmd = await _get_commande_with_lignes(db, commande_id)
        _ensure(cmd is not None, 404, "Commande introuvable")

        # Enrichir avec l'état des transformations (facture / BL déjà générés)
        facture = await db.factures.find_one(
            {"commande_id": commande_id, "type_facture": "facture"},
            {"_id": 0, "facture_id": 1, "reference": 1, "statut": 1},
        )
        bls = await db.bons_livraison.find(
            {"commande_id": commande_id},
            {"_id": 0, "bl_id": 1, "reference": 1, "statut": 1},
        ).to_list(100)
        bl_livre = any(b.get("statut") == "livre" for b in bls)
        cmd["transformations"] = {
            "facture": (
                {
                    "facture_id": facture["facture_id"],
                    "reference": facture.get("reference"),
                    "statut": facture.get("statut"),
                }
                if facture
                else None
            ),
            "facture_generee": facture is not None,
            "bons_livraison": [
                {"bl_id": b.get("bl_id"), "reference": b.get("reference"), "statut": b.get("statut")}
                for b in bls
            ],
            "bl_genere": len(bls) > 0,
            "totalement_livree": bl_livre or cmd.get("statut") == "livree",
        }

        return CommandeDetail(**cmd)

    # ---------- UPDATE ----------
    @router.patch("/{commande_id}", response_model=CommandeOut)
    async def update_commande(
        commande_id: str,
        payload: CommandePatch,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(cmd["statut"] == "brouillon", 400, "Seules les commandes brouillon peuvent être modifiées")

        updates = {"updated_at": _now_iso()}
        
        if payload.client_id is not None:
            client = await db.clients.find_one({"client_id": payload.client_id, "actif": True}, {"_id": 0})
            _ensure(client is not None, 404, "Client introuvable")
            updates["client_id"] = payload.client_id
        
        if payload.date_livraison_prevue is not None:
            updates["date_livraison_prevue"] = payload.date_livraison_prevue
        
        if payload.remise_globale is not None:
            updates["remise_globale"] = payload.remise_globale
        
        if payload.notes is not None:
            updates["notes"] = payload.notes
        
        # Update lignes if provided
        if payload.lignes is not None:
            _ensure(len(payload.lignes) > 0, 400, "Au moins une ligne requise")
            # Verify products
            for ligne in payload.lignes:
                prod = await db.produits.find_one({"produit_id": ligne.produit_id, "actif": True}, {"_id": 0})
                _ensure(prod is not None, 404, f"Produit {ligne.produit_id} introuvable")
            
            # Delete old lignes
            await db.commande_lignes.delete_many({"commande_id": commande_id})
            
            # Create new lignes
            for ligne in payload.lignes:
                ligne_doc = {
                    "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                    "commande_id": commande_id,
                    "produit_id": ligne.produit_id,
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "remise_ligne": ligne.remise_ligne,
                    "montant_ligne": ligne.montant_ligne,
                }
                await db.commande_lignes.insert_one(ligne_doc)
            
            # Recalculate totals
            totals = await _calculate_totals(payload.lignes, payload.remise_globale or cmd["remise_globale"])
            updates.update(totals)

        await db.commandes.update_one({"commande_id": commande_id}, {"$set": updates})
        
        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)
        return CommandeOut(**updated)

    # ---------- SOUMETTRE (brouillon -> en_attente) ----------
    @router.post("/{commande_id}/soumettre", response_model=CommandeOut)
    async def soumettre_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(
            cmd["statut"] == "brouillon",
            400,
            f"Seule une commande en brouillon peut être soumise (statut actuel : {cmd['statut']}).",
        )

        # Au moins une ligne avant soumission
        nb_lignes = await db.commande_lignes.count_documents({"commande_id": commande_id})
        _ensure(nb_lignes > 0, 400, "Impossible de soumettre une commande sans ligne.")

        await db.commandes.update_one(
            {"commande_id": commande_id},
            {"$set": {"statut": "en_attente", "updated_at": _now_iso()}},
        )

        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)

        try:
            _client_nom = updated.get("client_nom", cmd.get("client_id", ""))
            await notify_vente_event(
                db, "info", "commande",
                f"📤 Commande soumise — {cmd['reference']}",
                f"Commande {cmd['reference']} pour {_client_nom} soumise pour validation "
                f"({updated.get('montant_total', 0):,.0f} FCFA)",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning("notify soumettre_commande: %s", _e)

        return CommandeOut(**updated)

    # ---------- VALIDER ----------
    @router.post("/{commande_id}/valider", response_model=CommandeOut)
    async def valider_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        
        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        if cmd["statut"] == "brouillon":
            raise HTTPException(
                status_code=400,
                detail="Cette commande est en brouillon. Passez-la d'abord en attente via /soumettre avant de la valider."
            )
        _ensure(cmd["statut"] == "en_attente", 400, f"Commande déjà {cmd['statut']}")

        # Check validation threshold
        # RBAC 2026-06-17: DG retiré de la validation — super_admin uniquement pour >500k
        needs_dg = cmd["montant_total"] > VALIDATION_THRESHOLD
        if needs_dg:
            _ensure(me["role"] in {"super_admin"}, 403,
                   "Validation super_admin requise pour montant > 500 000 FCFA")
        else:
            _ensure(me["role"] in VALIDATE_ROLES, 403, "Accès refusé")

        # TICKET-006 — Vérification de stock avant validation
        lignes_verif = await db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0}).to_list(100)
        ruptures = []
        for ligne in lignes_verif:
            produit_id = ligne.get("produit_id")
            qte_demandee = int(ligne.get("quantite", 0))
            if not produit_id or qte_demandee <= 0:
                continue
            produit = await db.produits.find_one(
                {"produit_id": produit_id},
                {"_id": 0, "stock_actuel": 1, "titre": 1, "reference": 1},
            )
            if produit is None:
                continue  # Produit supprimé — on laisse passer, géré à la livraison
            stock_dispo = produit.get("stock_actuel", 0)
            if stock_dispo < qte_demandee:
                ruptures.append({
                    "produit_id": produit_id,
                    "designation": produit.get("titre", produit_id),
                    "stock_disponible": stock_dispo,
                    "quantite_demandee": qte_demandee,
                })
        if ruptures:
            detail_str = "; ".join(
                f"{r['designation']} (dispo={r['stock_disponible']}, demandé={r['quantite_demandee']})"
                for r in ruptures
            )
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuffisant pour valider la commande : {detail_str}",
            )

        # TICKET-009 — Vérification plafond de crédit client
        client_data = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0})
        if client_data:
            plafond = client_data.get("plafond_credit", 0) or 0
            if plafond > 0:
                # Calcul encours actuel = somme des montants restants sur factures ouvertes
                factures_ouvertes = await db.factures.find(
                    {
                        "client_id": cmd["client_id"],
                        "statut": {"$in": ["emise", "partiellement_payee", "en_retard"]},
                    },
                    {"_id": 0, "montant_restant": 1, "montant_ttc": 1},
                ).to_list(None)
                encours_actuel = sum(
                    f.get("montant_restant", f.get("montant_ttc", 0))
                    for f in factures_ouvertes
                )
                montant_commande = cmd.get("montant_total", 0)
                encours_apres = encours_actuel + montant_commande
                if encours_apres > plafond:
                    depassement = round(encours_apres - plafond, 2)
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "code": "PLAFOND_CREDIT_DEPASSE",
                            "message": (
                                f"Plafond de crédit dépassé pour {client_data.get('nom', cmd['client_id'])}. "
                                f"Plafond : {plafond:,.0f} FCFA — Encours actuel : {encours_actuel:,.0f} FCFA — "
                                f"Cette commande : {montant_commande:,.0f} FCFA — "
                                f"Dépassement : {depassement:,.0f} FCFA."
                            ),
                            "plafond_credit": plafond,
                            "encours_actuel": round(encours_actuel, 2),
                            "montant_commande": montant_commande,
                            "encours_apres_validation": round(encours_apres, 2),
                            "depassement": depassement,
                        },
                    )

        now = _now_iso()

        # Passer la commande à "validee"
        await db.commandes.update_one(
            {"commande_id": commande_id},
            {"$set": {
                "statut": "validee",
                "date_validation": now[:10],
                "validated_by": me["user_id"],
                "updated_at": now,
            }}
        )

        # Audit log validation
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="VALIDATE_COMMANDE",
                resource_type="commande",
                resource_id=commande_id,
                details={
                    "reference": cmd['reference'],
                    "client_id": cmd["client_id"],
                    "montant_total": cmd["montant_total"],
                },
                ip_address=request.client.host if request.client else None
            )

        # 🆕 AUTO-CRÉATION BON DE LIVRAISON
        try:
            from bons_livraison_module import next_bl_reference
            bl_id = f"bl_{uuid.uuid4().hex[:12]}"
            bl_reference = await next_bl_reference(db)
            bl_now = _now_iso()
            bl_doc = {
                "bl_id": bl_id,
                "reference": bl_reference,
                "commande_id": commande_id,
                "client_id": cmd["client_id"],
                "statut": "en_preparation",
                "date_creation": bl_now[:10],
                "date_livraison_prevue": None,
                "date_livraison_reelle": None,
                "notes": f"BL auto depuis commande {cmd['reference']}",
                "created_by": me["user_id"],
                "created_at": bl_now,
                "updated_at": bl_now,
            }
            await db.bons_livraison.insert_one(bl_doc)
            # Copier les lignes commande dans le BL
            lignes_cmd = await db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0}).to_list(100)
            bl_lignes = [
                {
                    "ligne_bl_id": f"lbl_{uuid.uuid4().hex[:10]}",
                    "bl_id": bl_id,
                    "produit_id": l.get("produit_id"),
                    "designation": l.get("designation", ""),
                    "quantite_commandee": l.get("quantite", 0),
                    "quantite_livree": 0,
                    "prix_unitaire": l.get("prix_unitaire", 0),
                }
                for l in lignes_cmd
            ]
            if bl_lignes:
                await db.bl_lignes.insert_many(bl_lignes)
            await db.audit_logs.insert_one({
                "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}_bl",
                "user_id": me["user_id"],
                "action": "CREATE_BL_AUTO",
                "resource_type": "bon_livraison",
                "resource_id": bl_id,
                "details": {"bl_reference": bl_reference, "commande_id": commande_id},
                "ip_address": request.client.host if request.client else None,
                "timestamp": bl_now,
            })
            logger.info(f"✅ BL auto {bl_reference} créé pour commande {cmd['reference']}")
        except Exception as e_bl:
            logger.error(f"⚠️ Erreur auto-BL (non bloquant): {e_bl}")

        # 🆕 AUTO-GÉNÉRATION FACTURE à la validation
        try:
            from factures_module import next_facture_reference
            # Récupérer les lignes de la commande
            lignes_fac = await db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0}).to_list(100)
            if lignes_fac:
                fac_id = f"fac_{uuid.uuid4().hex[:12]}"
                fac_reference = await next_facture_reference(db, "facture")
                fac_now = _now_iso()
                taux_tva_cmd = cmd.get("taux_tva", 18.0)
                remise_globale_cmd = cmd.get("remise_globale", 0.0)

                # TICKET-008 — Calcul HT net depuis les lignes (évite la double déduction
                # si montant_ht en base est déjà net d'une remise antérieure).
                # montant_ht (base) = Σ montant_ligne = HT brut après remises lignes.
                # montant_remise (base) = remise globale FCFA = montant_ht * remise_globale/100.
                # HT net = montant_ht - montant_remise (calcul unique, sans double soustraction).
                _montant_ht_brut = cmd.get("montant_ht", 0.0)
                _montant_remise = cmd.get("montant_remise", 0.0)
                montant_ht_cmd = round(_montant_ht_brut - _montant_remise, 2)
                if montant_ht_cmd < 0:
                    montant_ht_cmd = 0.0
                    logger.warning(f"[TICKET-008] HT net négatif pour commande {commande_id} — forcé à 0")
                montant_tva_fac = round(montant_ht_cmd * (taux_tva_cmd / 100), 2)
                montant_ttc_fac = round(montant_ht_cmd + montant_tva_fac, 2)

                fac_doc = {
                    "facture_id": fac_id,
                    "reference": fac_reference,
                    "type_facture": "facture",
                    "client_id": cmd["client_id"],
                    "commande_id": commande_id,
                    "statut": "emise",
                    "date_facture": fac_now[:10],
                    "date_echeance": None,
                    "date_emission": fac_now[:10],
                    "taux_tva": taux_tva_cmd,
                    "remise_globale": remise_globale_cmd,
                    "montant_ht": round(montant_ht_cmd, 2),
                    "montant_tva": montant_tva_fac,
                    "montant_ttc": montant_ttc_fac,
                    "total_ttc": montant_ttc_fac,
                    "montant_regle": 0.0,
                    "montant_restant": montant_ttc_fac,
                    "notes": f"Facture auto générée depuis commande {cmd['reference']}",
                    "facture_origine_id": None,
                    "created_by": me["user_id"],
                    "created_at": fac_now,
                    "updated_at": fac_now,
                }
                await db.factures.insert_one(fac_doc)

                # Copier les lignes commande dans la facture
                for l in lignes_fac:
                    _pid = l.get("produit_id")
                    prod = await db.produits.find_one(
                        {"produit_id": _pid},
                        {"_id": 0, "titre": 1, "matiere": 1, "niveau_scolaire": 1, "cycle": 1, "categorie": 1}
                    )
                    fac_ligne = {
                        "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                        "facture_id": fac_id,
                        "produit_id": _pid,
                        "designation": prod["titre"] if prod else l.get("designation", ""),
                        "matiere": prod.get("matiere") if prod else None,
                        "niveau_scolaire": prod.get("niveau_scolaire") if prod else None,
                        "cycle": prod.get("cycle") if prod else None,
                        "categorie": prod.get("categorie") if prod else None,
                        "quantite": l.get("quantite", 0),
                        "prix_unitaire": l.get("prix_unitaire", 0),
                        "remise_ligne": l.get("remise_ligne", 0),
                        "montant_ht": l.get("montant_ligne", 0),
                    }
                    await db.facture_lignes.insert_one(fac_ligne)

                logger.info(f"✅ Facture auto {fac_reference} générée pour commande {cmd['reference']}")
        except Exception as e_fac:
            logger.error(f"⚠️ Erreur auto-Facture (non bloquant): {e_fac}")

        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)

        # 🔔 Notification vente — commande validée
        try:
            _client_nom = updated.get("client_nom", cmd.get("client_id", ""))
            await notify_vente_event(
                db, "success", "commande",
                f"✅ Commande validée — {cmd['reference']}",
                f"Commande {cmd['reference']} pour {_client_nom} validée par {me.get('email', me['user_id'])}",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify valider_commande: %s", _e)

        return CommandeOut(**updated)

    # ---------- PREPARER ----------
    @router.post("/{commande_id}/preparer", response_model=CommandeOut)
    async def preparer_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in PREPARE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(cmd["statut"] == "validee", 400, f"Commande doit être validée (actuellement {cmd['statut']})")

        now = _now_iso()
        await db.commandes.update_one(
            {"commande_id": commande_id},
            {"$set": {
                "statut": "preparee",
                "date_preparation": now[:10],
                "prepared_by": me["user_id"],
                "updated_at": now,
            }}
        )
        
        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="PREPARE_COMMANDE",
                resource_type="commande",
                resource_id=commande_id,
                details={
                    "reference": cmd['reference'],
                    "client_id": cmd["client_id"],
                    "old_statut": cmd["statut"],
                    "new_statut": "preparee"
                },
                ip_address=request.client.host if request.client else None
            )
        
        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)

        # 🔔 Notification vente — commande préparée
        try:
            _client_nom = updated.get("client_nom", cmd.get("client_id", ""))
            await notify_vente_event(
                db, "info", "commande",
                f"🏭 Commande préparée — {cmd['reference']}",
                f"Commande {cmd['reference']} pour {_client_nom} est prête pour livraison",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify preparer_commande: %s", _e)

        return CommandeOut(**updated)

    # ---------- LIVRER ----------
    # TICKET-005 : livrer_commande() — bloquer si BL existant (passer par BL),
    # sinon déduire le stock directement (cas rare sans BL)
    @router.post("/{commande_id}/livrer", response_model=CommandeOut)
    async def livrer_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in DELIVER_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(cmd["statut"] == "preparee", 400, f"Commande doit être préparée (actuellement {cmd['statut']})")

        # TICKET-005 — Chemin A : si un BL non-livré existe, bloquer et rediriger
        bl_existant = await db.bons_livraison.find_one(
            {"commande_id": commande_id, "statut": {"$ne": "livre"}},
            {"_id": 0, "bl_id": 1, "reference": 1},
        )
        if bl_existant:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Un bon de livraison ({bl_existant['reference']}) existe pour cette commande. "
                    f"Veuillez livrer via le BL (POST /bons-livraison/{bl_existant['bl_id']}/livrer) "
                    "afin de garantir la déduction de stock."
                ),
            )

        # TICKET-005 — Chemin B : pas de BL → déduire le stock directement
        # TICKET-013 — Wrapped dans une transaction MongoDB (fallback sans session si replica non dispo)
        now = _now_iso()
        lignes_cmd = await db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0}).to_list(100)

        async def _exec_livraison(session=None):
            """Déduction stock + mouvements + mise à jour commande — transactionnel ou non."""
            for ligne in lignes_cmd:
                produit_id = ligne.get("produit_id")
                qte = int(ligne.get("quantite", 0))
                if not produit_id or qte <= 0:
                    continue
                # Décrémentation atomique avec garde stock >= qte
                updated_prod = await db.produits.find_one_and_update(
                    {"produit_id": produit_id, "stock_actuel": {"$gte": qte}},
                    {"$inc": {"stock_actuel": -qte}, "$set": {"updated_at": now}},
                    return_document=True,
                    projection={"_id": 0, "stock_actuel": 1},
                    session=session,
                )
                if not updated_prod:
                    produit_cur = await db.produits.find_one(
                        {"produit_id": produit_id}, {"_id": 0, "stock_actuel": 1},
                        session=session,
                    )
                    stock_dispo = produit_cur.get("stock_actuel", 0) if produit_cur else 0
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Stock insuffisant pour le produit {produit_id}: "
                            f"disponible={stock_dispo}, demandé={qte}"
                        ),
                    )
                stock_apres = updated_prod.get("stock_actuel", 0)
                await db.mouvements_stock.insert_one({
                    "mouvement_id": f"mvt_{uuid.uuid4().hex[:12]}",
                    "produit_id": produit_id,
                    "type_mouvement": "sortie",
                    "quantite": qte,
                    "stock_avant": stock_apres + qte,
                    "stock_apres": stock_apres,
                    "commande_id": commande_id,
                    "motif": f"Livraison directe commande {cmd['reference']}",
                    "created_by": me["user_id"],
                    "created_at": now,
                }, session=session)

            await db.commandes.update_one(
                {"commande_id": commande_id},
                {"$set": {
                    "statut": "livree",
                    "date_livraison": now[:10],
                    "delivered_by": me["user_id"],
                    "updated_at": now,
                }},
                session=session,
            )

        # Tentative avec session transactionnelle ; fallback sans session (Atlas M0 / standalone)
        try:
            async with await db.client.start_session() as _sess:
                try:
                    async with _sess.start_transaction():
                        await _exec_livraison(session=_sess)
                except (InvalidOperation, OperationFailure) as _tx_err:
                    logger.warning("TICKET-013 transaction aborted (%s) — fallback sans session", _tx_err)
                    await _exec_livraison(session=None)
        except (InvalidOperation, OperationFailure, Exception) as _sess_err:
            # start_session() lui-même peut échouer sur certains drivers/configs
            logger.warning("TICKET-013 start_session failed (%s) — fallback sans session", _sess_err)
            await _exec_livraison(session=None)

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="DELIVER_COMMANDE",
                resource_type="commande",
                resource_id=commande_id,
                details={
                    "reference": cmd['reference'],
                    "client_id": cmd["client_id"],
                    "old_statut": cmd["statut"],
                    "new_statut": "livree",
                    "stock_deduit": True,
                    "nb_lignes": len(lignes_cmd),
                },
                ip_address=request.client.host if request.client else None
            )

        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)

        # 🔔 Notification vente — commande livrée
        try:
            _client_nom = updated.get("client_nom", cmd.get("client_id", ""))
            await notify_vente_event(
                db, "success", "livraison",
                f"🚚 Commande livrée — {cmd['reference']}",
                f"Commande {cmd['reference']} pour {_client_nom} a été livrée",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify livrer_commande: %s", _e)

        return CommandeOut(**updated)

    # ---------- ANNULER ----------
    @router.post("/{commande_id}/annuler", response_model=CommandeOut)
    async def annuler_commande(
        commande_id: str,
        payload: AnnulerCommandeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in CANCEL_ROLES, 403, "Annulation non autorisée pour votre rôle")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")
        _ensure(cmd["statut"] not in {"livree", "annulee"}, 400, "Impossible d'annuler une commande livrée ou déjà annulée")

        now = _now_iso()
        await db.commandes.update_one(
            {"commande_id": commande_id},
            {"$set": {
                "statut": "annulee",
                "motif_annulation": payload.motif,
                "updated_at": now,
            }}
        )
        
        updated = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        await _enrich_commande_with_client(db, updated)

        # 🔔 Notification vente — commande annulée
        try:
            _client_nom = updated.get("client_nom", cmd.get("client_id", ""))
            await notify_vente_event(
                db, "warning", "commande",
                f"❌ Commande annulée — {cmd['reference']}",
                f"Commande {cmd['reference']} pour {_client_nom} annulée. Motif : {payload.motif or 'non précisé'}",
                lien=f"/commandes/{commande_id}",
                exclude_user_id=me["user_id"],
            )
        except Exception as _e:
            logger.warning("notify annuler_commande: %s", _e)

        return CommandeOut(**updated)

    # ---------- DELETE (super_admin uniquement — cascade complète) ----------
    @router.delete("/{commande_id}", status_code=204)
    async def supprimer_commande(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """
        Suppression définitive d'une commande avec cascade automatique :
        commande_lignes → proformas → bl_lignes → bons_livraison
        → facture_lignes → factures → commande
        Réservé au super_admin.
        """
        me = await resolve_user(request, authorization)
        _ensure(me["role"] == "super_admin", 403, "Suppression réservée au super_admin")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")

        ref = cmd.get("reference", commande_id)
        logger.info(f"[DELETE] Début suppression commande {ref} par {me.get('email')}")

        # 1. Lignes de commande
        r = await db.commande_lignes.delete_many({"commande_id": commande_id})
        logger.info(f"[DELETE] {r.deleted_count} commande_lignes supprimées")

        # 2. Proformas liés
        r = await db.proformas.delete_many({"commande_id": commande_id})
        logger.info(f"[DELETE] {r.deleted_count} proformas supprimés")

        # 3. Bons de livraison + leurs lignes
        bls = await db.bons_livraison.find({"commande_id": commande_id}, {"bl_id": 1, "_id": 0}).to_list(200)
        bl_ids = [bl["bl_id"] for bl in bls if "bl_id" in bl]
        if bl_ids:
            r = await db.bl_lignes.delete_many({"bl_id": {"$in": bl_ids}})
            logger.info(f"[DELETE] {r.deleted_count} bl_lignes supprimées")
        r = await db.bons_livraison.delete_many({"commande_id": commande_id})
        logger.info(f"[DELETE] {r.deleted_count} bons_livraison supprimés")

        # 4. Factures + leurs lignes
        factures = await db.factures.find({"commande_id": commande_id}, {"facture_id": 1, "_id": 0}).to_list(200)
        facture_ids = [f["facture_id"] for f in factures if "facture_id" in f]
        if facture_ids:
            r = await db.facture_lignes.delete_many({"facture_id": {"$in": facture_ids}})
            logger.info(f"[DELETE] {r.deleted_count} facture_lignes supprimées")
        r = await db.factures.delete_many({"commande_id": commande_id})
        logger.info(f"[DELETE] {r.deleted_count} factures supprimées")

        # 5. La commande elle-même
        await db.commandes.delete_one({"commande_id": commande_id})
        logger.info(f"[DELETE] Commande {ref} supprimée définitivement par {me.get('email')}")

        # Audit log
        try:
            await db.audit_logs.insert_one({
                "action": "DELETE_COMMANDE",
                "commande_id": commande_id,
                "reference": ref,
                "by": me.get("email"),
                "role": me.get("role"),
                "timestamp": _now_iso(),
                "cascade": {
                    "bl_ids": bl_ids,
                    "facture_ids": facture_ids,
                }
            })
        except Exception:
            pass  # audit non bloquant

        return Response(status_code=204)

    # ---------- PDF ----------
    @router.get("/{commande_id}/pdf")
    async def commande_pdf(
        commande_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        from fastapi.responses import StreamingResponse
        from pdf_generator import generate_commande_pdf

        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")

        lignes = await db.commande_lignes.find({"commande_id": commande_id}, {"_id": 0}).to_list(500)
        # Enrich lignes with code_article (reference) + niveau (niveau_scolaire) + cycle
        from pdf_generator import enrich_lignes_for_pdf
        _pids = list({(l.get("produit_id") or l.get("product_id")) for l in lignes if (l.get("produit_id") or l.get("product_id"))})
        _prods = await db.produits.find(
            {"produit_id": {"$in": _pids}}, {"_id": 0}
        ).to_list(1000) if _pids else []
        enrich_lignes_for_pdf({(p.get("product_id") or p.get("produit_id")): p for p in _prods}, lignes)
        for l in lignes:
            l["montant_ht"] = l.get("montant_ligne", l.get("montant_ht", 0))

        client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0}) or {}
        buffer = generate_commande_pdf(cmd, lignes, client)
        filename = f"{cmd['reference']}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    # ---------- WHATSAPP ----------
    @router.post("/{commande_id}/envoyer-whatsapp")
    async def envoyer_commande_whatsapp(
        commande_id: str,
        payload: WhatsAppPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Prepare WhatsApp sharing link for Bon de Commande"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")

        # Get client WhatsApp number
        client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        whatsapp_number = (payload.numero if payload and payload.numero else None) \
            or client.get("numero_whatsapp") or client.get("telephone")
        _ensure(whatsapp_number, 400, "Numéro WhatsApp non disponible — veuillez en saisir un")

        # Clean phone number
        clean_number = whatsapp_number.replace(" ", "").replace("-", "").replace("+", "")

        # Prepare message
        message = f"""Bonjour {client.get('nom', 'Client')}

Veuillez trouver ci-joint votre BON DE COMMANDE N° {cmd['reference']}

Montant total : {cmd['montant_total']:,.2f} FCFA

Merci de confirmer votre commande.

Cordialement,
ÉDITIONS FABS-CI"""

        # WhatsApp URL
        encoded_message = message.replace("\n", "%0A")
        whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"

        # Update commande tracking
        await db.commandes.update_one(
            {"commande_id": commande_id},
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
            "resource_type": "commande",
            "resource_id": commande_id,
            "details": {"whatsapp_number": clean_number},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })

        return {
            "whatsapp_url": whatsapp_url,
            "message": message,
            "pdf_filename": f"{cmd['reference']}.pdf"
        }

    # ---------- PARTAGER WHATSAPP (Web Share API — sans numéro) ----------
    @router.post("/{commande_id}/partager-whatsapp")
    async def partager_commande_whatsapp(
        commande_id: str,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Log a WhatsApp native share event for Bon de Commande (no phone required)."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0, "reference": 1})
        _ensure(cmd is not None, 404, "Commande introuvable")

        now = _now_iso()
        await db.commandes.update_one(
            {"commande_id": commande_id},
            {"$set": {"date_partage_whatsapp": now, "updated_at": now}}
        )
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
            "user_id": me["user_id"],
            "action": "SHARE_WHATSAPP_NATIVE",
            "resource_type": "commande",
            "resource_id": commande_id,
            "details": {"canal": "whatsapp", "statut": "partage_lance", "methode": "web_share_api"},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        return {"message": "Partage WhatsApp enregistré", "reference": cmd.get("reference")}

    # ---------- EMAIL ----------
    @router.post("/{commande_id}/envoyer-email")
    async def envoyer_commande_email(
        commande_id: str,
        payload: EmailPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Send Bon de Commande via Email"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        cmd = await db.commandes.find_one({"commande_id": commande_id}, {"_id": 0})
        _ensure(cmd is not None, 404, "Commande introuvable")

        # Get client email
        client = await db.clients.find_one({"client_id": cmd["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        # Destinataire : payload override ou email client
        if payload and payload.destinataire:
            client_email = payload.destinataire
        else:
            client_email = client.get("email")
        _ensure(client_email, 400, "Email non disponible — veuillez en saisir un")

        # Generate PDF
        from pdf_generator import generate_commande_pdf
        lignes = await db.commande_lignes.find({"commande_id": commande_id}).to_list(100)
        pdf_buffer = generate_commande_pdf(cmd, lignes, client)
        
        # Prepare email content — payload override si fourni
        sujet = (payload.objet if payload and payload.objet else None) or \
            f"Bon de Commande {cmd['reference']} - ÉDITIONS FABS-CI"
        corps_texte = (payload.message if payload and payload.message else None) or \
            f"""Bonjour {client.get('nom', 'Client')},

Veuillez trouver ci-joint votre BON DE COMMANDE N° {cmd['reference']}.

Montant total : {cmd['montant_total']:,.2f} FCFA

Merci de confirmer votre commande.

Cordialement,
ÉDITIONS FABS-CI"""

        corps_html = f"""
<html>
<body>
    <h2>Bon de Commande {cmd['reference']}</h2>
    <p>Bonjour {client.get('nom', 'Client')},</p>
    <p>Veuillez trouver ci-joint votre BON DE COMMANDE N° {cmd['reference']}.</p>
    <p><strong>Montant total : {cmd['montant_total']:,.2f} FCFA</strong></p>
    <p>Merci de confirmer votre commande.</p>
    <p>Cordialement,<br>ÉDITIONS FABS-CI</p>
</body>
</html>"""

        # Send email with PDF attachment
        try:
            result = await _send_email_smtp(
                client_email, 
                sujet, 
                corps_html, 
                corps_texte, 
                pdf_buffer, 
                f"{cmd['reference']}.pdf"
            )
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result["error"])
            
            # Update commande tracking
            await db.commandes.update_one(
                {"commande_id": commande_id},
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
                "resource_type": "commande",
                "resource_id": commande_id,
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
            raise
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            # Log failed attempt
            await db.audit_logs.insert_one({
                "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
                "user_id": me["user_id"],
                "action": "SEND_EMAIL",
                "resource_type": "commande",
                "resource_id": commande_id,
                "details": {"email": client_email, "status": "failed", "error": str(e)},
                "ip_address": request.client.host if request.client else None,
                "timestamp": _now_iso(),
            })
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")

    # ---------- CHECK DOUBLON ----------
    @router.post("/check-doublon")
    async def check_doublon(
        payload: DoublonCheckIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Détection de doublons en temps réel — fenêtre 48h."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        from datetime import timedelta
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=48)
        since_iso = since.isoformat()

        # Chercher commandes du même client dans les 48h (hors annulées)
        candidates_cursor = db.commandes.find(
            {
                "client_id": payload.client_id,
                "created_at": {"$gte": since_iso},
                "statut": {"$ne": "annulee"},
            },
            {"_id": 0},
        )
        candidates = await candidates_cursor.to_list(50)

        # Normaliser les lignes payload pour comparaison
        payload_lignes_set = {
            (l.produit_id, int(l.quantite)) for l in payload.lignes
        }

        doublon = None
        niveau = None

        for cmd in candidates:
            cmd_lignes_cursor = db.commande_lignes.find(
                {"commande_id": cmd["commande_id"]}, {"_id": 0}
            )
            cmd_lignes = await cmd_lignes_cursor.to_list(200)
            cmd_lignes_set = {
                (l["produit_id"], int(l["quantite"])) for l in cmd_lignes
            }

            if cmd_lignes_set != payload_lignes_set:
                continue  # Produits/quantités différents → pas un doublon

            # Produits identiques — vérifier représentant + téléphone
            rep_match = (
                (cmd.get("representant") or "").strip().lower()
                == (payload.representant or "").strip().lower()
            )
            tel_match = (
                (cmd.get("telephone") or "").strip()
                == (payload.telephone or "").strip()
            )

            if rep_match and tel_match:
                doublon = cmd
                niveau = "certain"
                break
            else:
                # Probable si pas encore trouvé certain
                if niveau != "certain":
                    doublon = cmd
                    niveau = "probable"

        # Enrichir la commande doublon avec info client
        if doublon:
            await _enrich_commande_with_client(db, doublon)

        # Logger dans doublon_logs
        log_id = f"dlog_{uuid.uuid4().hex[:16]}"
        await db.doublon_logs.insert_one({
            "log_id": log_id,
            "ts": now.isoformat(),
            "user_id": me["user_id"],
            "user_email": me.get("email", ""),
            "commande_existante_id": doublon["commande_id"] if doublon else None,
            "commande_en_cours": {
                "client_id": payload.client_id,
                "representant": payload.representant,
                "telephone": payload.telephone,
                "lignes": [{"produit_id": l.produit_id, "quantite": l.quantite} for l in payload.lignes],
            },
            "niveau": niveau,
            "decision": None,
        })

        if not doublon:
            return {"doublon": False, "niveau": None, "commande": None, "log_id": log_id}

        return {
            "doublon": True,
            "niveau": niveau,
            "commande": doublon,
            "log_id": log_id,
        }

    # ---------- LOG DECISION ----------
    @router.patch("/check-doublon/{log_id}")
    async def log_doublon_decision(
        log_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Enregistrer la décision de l'utilisateur face à un doublon."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        body = await request.json()
        decision = body.get("decision")  # "continuer" ou "annuler"
        _ensure(decision in ("continuer", "annuler"), 400, "Decision invalide (continuer|annuler)")

        result = await db.doublon_logs.update_one(
            {"log_id": log_id, "user_id": me["user_id"]},
            {"$set": {"decision": decision, "decision_at": datetime.now(timezone.utc).isoformat()}},
        )
        _ensure(result.matched_count > 0, 404, "Log introuvable")
        return {"ok": True, "log_id": log_id, "decision": decision}

    return router


# ---------------------------------------------------------------------------
# Seed (optional demo data)
# ---------------------------------------------------------------------------
async def seed_commandes(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed demo commandes (optional)"""
    existing = await db.commandes.count_documents({})
    if existing > 0:
        return 0
    
    # Get first client and products
    client = await db.clients.find_one({"actif": True}, {"_id": 0})
    if not client:
        return 0
    
    products = await db.produits.find({"actif": True}, {"_id": 0}).limit(5).to_list(5)
    if len(products) < 2:
        return 0
    
    # Create 3 demo commandes
    demo_commandes = []
    for i in range(3):
        commande_id = f"cmd_{uuid.uuid4().hex[:12]}"
        reference = f"FABS-CMD-26-27-{i+1:04d}"
        
        lignes = [
            {
                "produit_id": products[0].get("product_id") or products[0].get("produit_id"),
                "quantite": 10,
                "prix_unitaire": products[0]["prix_vente"],
                "remise_ligne": 0,
            },
            {
                "produit_id": products[1].get("product_id") or products[1].get("produit_id"),
                "quantite": 5,
                "prix_unitaire": products[1]["prix_vente"],
                "remise_ligne": 5,
            },
        ]
        
        montant_ht = sum(
            l["quantite"] * l["prix_unitaire"] * (1 - l["remise_ligne"] / 100)
            for l in lignes
        )
        montant_total = montant_ht
        
        statuts = ["validee", "preparee", "brouillon"]
        now = _now_iso()
        
        cmd_doc = {
            "commande_id": commande_id,
            "reference": reference,
            "client_id": client["client_id"],
            "statut": statuts[i],
            "date_commande": now[:10],
            "date_livraison_prevue": None,
            "date_validation": now[:10] if i < 2 else None,
            "date_preparation": now[:10] if i < 1 else None,
            "date_livraison": None,
            "remise_globale": 0,
            "montant_ht": round(montant_ht, 2),
            "montant_remise": 0,
            "montant_total": round(montant_total, 2),
            "notes": f"Commande de démonstration {i+1}",
            "motif_annulation": None,
            "created_by": user_id,
            "validated_by": user_id if i < 2 else None,
            "prepared_by": user_id if i < 1 else None,
            "delivered_by": None,
            "created_at": now,
            "updated_at": now,
        }
        demo_commandes.append(cmd_doc)
        
        # Insert lignes
        for ligne in lignes:
            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "commande_id": commande_id,
                "produit_id": ligne["produit_id"],
                "quantite": ligne["quantite"],
                "prix_unitaire": ligne["prix_unitaire"],
                "remise_ligne": ligne["remise_ligne"],
                "montant_ligne": ligne["quantite"] * ligne["prix_unitaire"] * (1 - ligne["remise_ligne"] / 100),
            }
            await db.commande_lignes.insert_one(ligne_doc)
    
    if demo_commandes:
        await db.commandes.insert_many(demo_commandes)
        # Update counter
        await db.counters.update_one(
            {"_id": "commandes"},
            {"$set": {"seq": 3}},
            upsert=True
        )
    
    return len(demo_commandes)
