"""
Module Paiements — Sprint 8
- CRUD complet sur la collection MongoDB `paiements`
- Référence auto-incrémentée FABS-REG-2026-XXXX
- 4 modes de paiement : especes, cheque, virement, mobile_money
- Affectation à une ou plusieurs factures
- Mise à jour automatique des factures (montant_regle, statut)
- Rapprochement bancaire
- Génération automatique écritures comptables
- RBAC : 
    READ = {super_admin, DG, comptable}
    WRITE = {super_admin, DG, comptable}
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional, List
import uuid
import logging
import io

from fastapi import APIRouter, HTTPException, Header, Query, Request
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from notifications_module import notify_vente_event

# ReportLab — génération PDF reçu paiement (TICKET-002)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger("fabsci.paiements")

# Import des fonctions de génération d'écritures comptables
from comptabilite_module import generate_ecriture_comptable_paiement

# RBAC
READ_ROLES = {"super_admin", "directeur_general", "comptable"}
WRITE_ROLES = {"super_admin", "directeur_general", "comptable"}

ModePaiement = Literal["especes", "cheque", "virement", "mobile_money"]


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_paiement_reference(db: AsyncIOMotorDatabase) -> str:
    """Generate FABS-REG-2026-XXXX reference"""
    current_year = datetime.now().year
    doc = await db.counters.find_one_and_update(
        {"_id": "paiements"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-REG-{current_year}-{seq:04d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AffectationFacture(BaseModel):
    facture_id: str
    montant_affecte: float = Field(..., gt=0)


class PaiementIn(BaseModel):
    client_id: str
    date_paiement: str  # ISO date YYYY-MM-DD
    mode_paiement: ModePaiement
    montant_total: float = Field(..., gt=0)
    # Chèque
    banque: Optional[str] = None
    numero_cheque: Optional[str] = None
    # Virement
    reference_virement: Optional[str] = None
    # Mobile Money
    operateur: Optional[str] = None
    numero_transaction: Optional[str] = None
    # Affectation factures (au moins une affectation requise pour intégrité ERP)
    factures: List[AffectationFacture] = Field(..., min_length=1, description="Au moins une facture doit être liée à ce paiement")
    notes: Optional[str] = Field(default=None, max_length=500)


class WhatsAppPayload(BaseModel):
    numero: Optional[str] = None
    message: Optional[str] = None

class EmailPayload(BaseModel):
    destinataire: Optional[str] = None
    objet: Optional[str] = None
    message: Optional[str] = None

class PaiementOut(BaseModel):
    paiement_id: str
    reference: str
    client_id: str
    client_nom: Optional[str] = None
    client_numero_whatsapp: Optional[str] = None
    client_email: Optional[str] = None
    date_paiement: str
    mode_paiement: ModePaiement
    montant_total: float
    montant_affecte: float
    montant_non_affecte: float
    # Details mode paiement
    banque: Optional[str] = None
    numero_cheque: Optional[str] = None
    reference_virement: Optional[str] = None
    operateur: Optional[str] = None
    numero_transaction: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: str


class PaiementDetail(PaiementOut):
    factures: List[dict]  # [{facture_id, facture_reference, montant_affecte}]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
async def _get_client_nom(db: AsyncIOMotorDatabase, client_id: str) -> Optional[str]:
    client = await db.clients.find_one({"client_id": client_id}, {"_id": 0, "nom": 1})
    return client["nom"] if client else None


async def _update_facture_paiement(db: AsyncIOMotorDatabase, facture_id: str, montant: float) -> None:
    """Add payment to facture and update status"""
    facture = await db.factures.find_one({"facture_id": facture_id}, {"_id": 0})
    if not facture:
        return
    
    new_montant_regle = facture["montant_regle"] + montant
    montant_restant = facture["montant_ttc"] - new_montant_regle
    
    # Update status
    if new_montant_regle >= facture["montant_ttc"]:
        new_statut = "payee"
    elif new_montant_regle > 0:
        new_statut = "partiellement_payee"
    else:
        new_statut = facture["statut"]
    
    await db.factures.update_one(
        {"facture_id": facture_id},
        {"$set": {
            "montant_regle": round(new_montant_regle, 2),
            "montant_restant": round(montant_restant, 2),
            "statut": new_statut,
            "updated_at": _now_iso(),
        }}
    )


async def _enrich_paiement(db: AsyncIOMotorDatabase, paiement: dict) -> dict:
    """Add client info to paiement"""
    if paiement.get("client_id"):
        client = await db.clients.find_one({"client_id": paiement["client_id"]}, {"_id": 0, "nom": 1, "email": 1, "numero_whatsapp": 1, "telephone": 1})
        if client:
            paiement["client_nom"] = client.get("nom")
            paiement["client_numero_whatsapp"] = client.get("numero_whatsapp") or client.get("telephone")
            paiement["client_email"] = client.get("email")
    return paiement


# ---------------------------------------------------------------------------
# Router Builder
# ---------------------------------------------------------------------------
def build_paiements_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/paiements", tags=["paiements"])

    # ---------- LIST ----------
    # TICKET-004 : réponse enrichie avec total pour la pagination frontend
    @router.get("")
    async def list_paiements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        mode_paiement: Optional[ModePaiement] = None,
        client_id: Optional[str] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        q: Optional[str] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=200),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if mode_paiement:
            filters["mode_paiement"] = mode_paiement
        if client_id:
            filters["client_id"] = client_id
        if date_debut or date_fin:
            date_filter = {}
            if date_debut:
                date_filter["$gte"] = date_debut
            if date_fin:
                date_filter["$lte"] = date_fin
            filters["date_paiement"] = date_filter

        # Pipeline de base avec $lookup clients pour éviter N+1
        base_pipeline = [
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
        if q:
            base_pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
                {"client_telephone": {"$regex": q, "$options": "i"}},
                {"client_representant": {"$regex": q, "$options": "i"}},
            ]}})

        # Pipeline items paginés + pipeline count — exécutés en parallèle via $facet
        facet_pipeline = base_pipeline + [{
            "$facet": {
                "items": [
                    {"$sort": {"date_paiement": -1}},
                    {"$skip": skip},
                    {"$limit": limit},
                ],
                "total_count": [{"$count": "n"}],
            }
        }]

        result = await db.paiements.aggregate(facet_pipeline).to_list(1)
        facet = result[0] if result else {"items": [], "total_count": []}
        docs = facet.get("items", [])
        total = facet["total_count"][0]["n"] if facet.get("total_count") else 0

        items = []
        for d in docs:
            try:
                items.append(PaiementOut(**d).model_dump())
            except Exception as exc:
                logger.error(
                    "Paiement doc invalide ignoré (numero=%s): %s",
                    d.get("numero") or d.get("_id"), exc,
                )
        return {"items": items, "total": total}

    # ---------- CREATE ----------
    @router.post("", response_model=PaiementOut, status_code=201)
    async def create_paiement(
        payload: PaiementIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Verify client exists
        client = await db.clients.find_one({"client_id": payload.client_id, "actif": True}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable ou inactif")

        # Verify factures if any
        total_affecte = 0.0
        for affect in payload.factures:
            facture = await db.factures.find_one({"facture_id": affect.facture_id}, {"_id": 0})
            _ensure(facture is not None, 404, f"Facture {affect.facture_id} introuvable")
            _ensure(facture["client_id"] == payload.client_id, 400, "Facture n'appartient pas au client")
            total_affecte += affect.montant_affecte

        _ensure(total_affecte <= payload.montant_total, 400, "Montant affecté > montant total")

        # Create paiement
        paiement_id = f"pay_{uuid.uuid4().hex[:12]}"
        reference = await next_paiement_reference(db)
        montant_non_affecte = payload.montant_total - total_affecte

        now = _now_iso()
        paiement_doc = {
            "paiement_id": paiement_id,
            "reference": reference,
            "client_id": payload.client_id,
            "date_paiement": payload.date_paiement,
            "mode_paiement": payload.mode_paiement,
            "montant_total": payload.montant_total,
            "montant_affecte": total_affecte,
            "montant_non_affecte": montant_non_affecte,
            "banque": payload.banque,
            "numero_cheque": payload.numero_cheque,
            "reference_virement": payload.reference_virement,
            "operateur": payload.operateur,
            "numero_transaction": payload.numero_transaction,
            "notes": payload.notes,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.paiements.insert_one(paiement_doc)

        # Create affectations and update factures
        for affect in payload.factures:
            affectation_doc = {
                "affectation_id": f"aff_{uuid.uuid4().hex[:12]}",
                "paiement_id": paiement_id,
                "facture_id": affect.facture_id,
                "montant_affecte": affect.montant_affecte,
                "created_at": now,
            }
            await db.affectations_paiement.insert_one(affectation_doc)
            
            # Update facture
            await _update_facture_paiement(db, affect.facture_id, affect.montant_affecte)

        # Génération automatique des écritures comptables pour le paiement
        try:
            await generate_ecriture_comptable_paiement(
                db=db,
                paiement_id=paiement_id,
                paiement_reference=reference,
                facture_id=payload.factures[0].facture_id if payload.factures else None,
                client_id=payload.client_id,
                montant=payload.montant_total,
                mode_paiement=payload.mode_paiement,
                user_id=me["user_id"],
                log_audit_event=log_audit_event
            )
            logger.info(f"✅ Écritures comptables générées pour paiement {reference}")
        except Exception as e:
            logger.error(f"❌ Erreur génération écritures comptables pour paiement {reference}: {e}")

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_PAIEMENT",
                resource_type="paiement",
                resource_id=paiement_id,
                details={
                    "reference": reference,
                    "client_id": payload.client_id,
                    "mode_paiement": payload.mode_paiement,
                    "montant_total": payload.montant_total,
                    "factures_count": len(payload.factures)
                },
                ip_address=request.client.host if request.client else None
            )

        # Return with client_nom
        paiement_doc["client_nom"] = client["nom"]

        # 🔔 Notification vente — paiement reçu
        try:
            _mode = paiement_doc.get("mode_paiement", "")
            await notify_vente_event(
                db, "success", "paiement",
                f"💰 Paiement reçu — {client['nom']}",
                f"Paiement de {payload.montant_total:,.0f} FCFA reçu ({_mode}) de {client['nom']}",
                lien=f"/paiements/{paiement_doc['paiement_id']}",
                exclude_user_id=user["user_id"],
            )
        except Exception as _e:
            logger.warning("notify create_paiement: %s", _e)

        return PaiementOut(**paiement_doc)

    # ---------- GET DETAIL ----------
    @router.get("/{paiement_id}", response_model=PaiementDetail)
    async def get_paiement(
        paiement_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        paiement = await db.paiements.find_one({"paiement_id": paiement_id}, {"_id": 0})
        _ensure(paiement is not None, 404, "Paiement introuvable")
        
        # Get affectations
        affectations_cursor = db.affectations_paiement.find({"paiement_id": paiement_id}, {"_id": 0})
        affectations = await affectations_cursor.to_list(100)
        
        # Enrich with facture references
        factures_list = []
        for aff in affectations:
            facture = await db.factures.find_one({"facture_id": aff["facture_id"]}, {"_id": 0, "reference": 1})
            factures_list.append({
                "facture_id": aff["facture_id"],
                "facture_reference": facture["reference"] if facture else None,
                "montant_affecte": aff["montant_affecte"],
            })
        
        paiement["factures"] = factures_list
        await _enrich_paiement(db, paiement)
        
        return PaiementDetail(**paiement)

    # ---------- GET PAIEMENTS BY FACTURE ----------
    @router.get("/facture/{facture_id}", response_model=List[dict])
    async def get_paiements_by_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        # Get affectations for this facture
        affectations_cursor = db.affectations_paiement.find({"facture_id": facture_id}, {"_id": 0})
        affectations = await affectations_cursor.to_list(100)
        
        result = []
        for aff in affectations:
            paiement = await db.paiements.find_one({"paiement_id": aff["paiement_id"]}, {"_id": 0})
            if paiement:
                result.append({
                    "paiement_id": paiement["paiement_id"],
                    "reference": paiement["reference"],
                    "date_paiement": paiement["date_paiement"],
                    "mode_paiement": paiement["mode_paiement"],
                    "montant_affecte": aff["montant_affecte"],
                    "created_at": aff["created_at"],
                })
        
        return result

    # ---------- WHATSAPP ----------
    @router.post("/{paiement_id}/envoyer-whatsapp")
    async def envoyer_paiement_whatsapp(
        paiement_id: str,
        payload: WhatsAppPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Prepare WhatsApp sharing link for reçu de paiement"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        paiement = await db.paiements.find_one({"paiement_id": paiement_id}, {"_id": 0})
        _ensure(paiement is not None, 404, "Paiement introuvable")

        client = await db.clients.find_one({"client_id": paiement["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        whatsapp_number = (payload.numero if payload and payload.numero else None) \
            or client.get("numero_whatsapp") or client.get("telephone")
        _ensure(whatsapp_number, 400, "Numéro WhatsApp non disponible — veuillez en saisir un")

        clean_number = whatsapp_number.replace(" ", "").replace("-", "").replace("+", "")

        message = (payload.message if payload and payload.message else None) or \
            f"""Bonjour {client.get('nom', 'Client')},

Nous confirmons la réception de votre paiement {paiement['reference']}.

Montant : {paiement['montant_total']:,.0f} FCFA
Date : {paiement['date_paiement']}

Merci de votre confiance.

Cordialement,
ÉDITIONS FABS-CI"""

        encoded_message = message.replace("\n", "%0A")
        whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"

        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
            "user_id": me["user_id"],
            "action": "SEND_WHATSAPP",
            "resource_type": "paiement",
            "resource_id": paiement_id,
            "details": {"whatsapp_number": clean_number},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })

        return {
            "whatsapp_url": whatsapp_url,
            "message": message,
            "pdf_filename": f"{paiement['reference']}.pdf"
        }

    # ---------- EMAIL ----------
    @router.post("/{paiement_id}/envoyer-email")
    async def envoyer_paiement_email(
        paiement_id: str,
        payload: EmailPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None),
    ):
        """Send reçu de paiement via Email"""
        import os
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        paiement = await db.paiements.find_one({"paiement_id": paiement_id}, {"_id": 0})
        _ensure(paiement is not None, 404, "Paiement introuvable")

        client = await db.clients.find_one({"client_id": paiement["client_id"]}, {"_id": 0})
        _ensure(client is not None, 404, "Client introuvable")

        if payload and payload.destinataire:
            client_email = payload.destinataire
        else:
            client_email = client.get("email")
        _ensure(client_email, 400, "Email non disponible — veuillez en saisir un")

        sujet = (payload.objet if payload and payload.objet else None) or \
            f"Reçu de paiement {paiement['reference']} - ÉDITIONS FABS-CI"
        corps_texte = (payload.message if payload and payload.message else None) or \
            f"""Bonjour {client.get('nom', 'Client')},

Nous confirmons la réception de votre paiement {paiement['reference']}.

Montant : {paiement['montant_total']:,.0f} FCFA
Date : {paiement['date_paiement']}

Merci de votre confiance.

Cordialement,
ÉDITIONS FABS-CI"""

        corps_html = f"""
<html>
<body>
    <h2>Reçu de paiement {paiement['reference']}</h2>
    <p>Bonjour {client.get('nom', 'Client')},</p>
    <p>Nous confirmons la réception de votre paiement.</p>
    <p><strong>Montant : {paiement['montant_total']:,.0f} FCFA</strong><br>
    Date : {paiement['date_paiement']}</p>
    <p>Merci de votre confiance.</p>
    <p>Cordialement,<br>ÉDITIONS FABS-CI</p>
</body>
</html>"""

        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = os.getenv("SMTP_PORT", "587")
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_from = os.getenv("SMTP_FROM")

            if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
                raise HTTPException(status_code=500, detail="Configuration SMTP manquante")

            msg = MIMEMultipart("mixed")
            msg["Subject"] = sujet
            msg["From"] = smtp_from
            msg["To"] = client_email
            msg.attach(MIMEText(corps_html, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            await db.audit_logs.insert_one({
                "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{me['user_id'][:8]}",
                "user_id": me["user_id"],
                "action": "SEND_EMAIL",
                "resource_type": "paiement",
                "resource_id": paiement_id,
                "details": {"email": client_email},
                "ip_address": request.client.host if request.client else None,
                "timestamp": _now_iso(),
            })

            return {"success": True, "message": f"Email envoyé à {client_email}"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email paiement error: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur envoi email : {str(e)}")

    # ---------- PDF REÇU PAIEMENT (TICKET-002) ----------
    @router.get("/{paiement_id}/pdf")
    async def generer_pdf_paiement(
        paiement_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Génère le reçu PDF d'un paiement — TICKET-002"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        paiement = await db.paiements.find_one({"paiement_id": paiement_id}, {"_id": 0})
        _ensure(paiement is not None, 404, "Paiement introuvable")

        client = await db.clients.find_one({"client_id": paiement.get("client_id")}, {"_id": 0})
        client_nom = client.get("nom", "N/A") if client else "N/A"
        client_tel = client.get("telephone", "") if client else ""
        client_email_val = client.get("email", "") if client else ""

        # Récupérer les affectations factures
        affectations = await db.affectations_paiement.find(
            {"paiement_id": paiement_id}, {"_id": 0}
        ).to_list(100)

        factures_detail = []
        for aff in affectations:
            fac = await db.factures.find_one(
                {"facture_id": aff["facture_id"]}, {"_id": 0, "reference": 1}
            )
            factures_detail.append({
                "reference": fac.get("reference", aff["facture_id"]) if fac else aff["facture_id"],
                "montant": aff.get("montant_affecte", 0),
            })

        MODES_LABEL = {
            "especes": "Espèces",
            "cheque": "Chèque",
            "virement": "Virement bancaire",
            "mobile_money": "Mobile Money",
        }
        mode_label = MODES_LABEL.get(paiement.get("mode_paiement", ""), paiement.get("mode_paiement", "N/A"))
        reference = paiement.get("reference", paiement_id)
        date_pai = paiement.get("date_paiement", datetime.now(timezone.utc).strftime("%d/%m/%Y"))
        montant_total = paiement.get("montant_total", 0)
        montant_affecte = paiement.get("montant_affecte", 0)
        montant_non_affecte = paiement.get("montant_non_affecte", 0)

        # --- Construction PDF ---
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        story = []

        ORANGE = colors.HexColor("#FF6200")
        DARK   = colors.HexColor("#0A2540")
        GRAY   = colors.HexColor("#6B7280")

        style_title = ParagraphStyle("title", parent=styles["Normal"],
            fontSize=20, textColor=DARK, fontName="Helvetica-Bold", spaceAfter=4)
        style_sub = ParagraphStyle("sub", parent=styles["Normal"],
            fontSize=10, textColor=GRAY, spaceAfter=2)
        style_label = ParagraphStyle("label", parent=styles["Normal"],
            fontSize=9, textColor=GRAY)
        style_value = ParagraphStyle("value", parent=styles["Normal"],
            fontSize=10, fontName="Helvetica-Bold", textColor=DARK)
        style_center = ParagraphStyle("center", parent=styles["Normal"],
            fontSize=9, alignment=TA_CENTER, textColor=GRAY)
        style_total = ParagraphStyle("total", parent=styles["Normal"],
            fontSize=14, fontName="Helvetica-Bold", textColor=ORANGE, alignment=TA_RIGHT)

        # En-tête
        story.append(Paragraph("ÉDITIONS FABS-CI", style_title))
        story.append(Paragraph("ERP FABS-CI V10 — Reçu de Paiement", style_sub))
        story.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=12))

        # Bloc référence + date
        header_data = [
            [Paragraph(f"<b>Référence :</b> {reference}", styles["Normal"]),
             Paragraph(f"<b>Date :</b> {date_pai}", styles["Normal"])],
        ]
        header_table = Table(header_data, colWidths=["50%", "50%"])
        header_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.4 * cm))

        # Infos client
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=8))
        client_data = [
            [Paragraph("CLIENT", style_label), Paragraph("", style_label)],
            [Paragraph(client_nom, style_value),
             Paragraph(client_tel or client_email_val or "", style_value)],
        ]
        client_table = Table(client_data, colWidths=["60%", "40%"])
        client_table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 0.4 * cm))

        # Mode de paiement
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=8))
        story.append(Paragraph("MODE DE PAIEMENT", style_label))
        story.append(Paragraph(mode_label, style_value))

        # Détails complémentaires selon le mode
        extras = []
        if paiement.get("banque"):
            extras.append(f"Banque : {paiement['banque']}")
        if paiement.get("numero_cheque"):
            extras.append(f"N° chèque : {paiement['numero_cheque']}")
        if paiement.get("reference_virement"):
            extras.append(f"Réf. virement : {paiement['reference_virement']}")
        if paiement.get("operateur"):
            extras.append(f"Opérateur : {paiement['operateur']}")
        if paiement.get("numero_transaction"):
            extras.append(f"N° transaction : {paiement['numero_transaction']}")
        for ex in extras:
            story.append(Paragraph(ex, style_sub))

        story.append(Spacer(1, 0.5 * cm))

        # Tableau factures affectées
        if factures_detail:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=8))
            story.append(Paragraph("FACTURES AFFECTÉES", style_label))
            story.append(Spacer(1, 0.2 * cm))

            fac_rows = [["Référence facture", "Montant affecté"]]
            for fd in factures_detail:
                fac_rows.append([
                    fd["reference"],
                    f"{fd['montant']:,.0f} FCFA".replace(",", " "),
                ])
            fac_table = Table(fac_rows, colWidths=["60%", "40%"])
            fac_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (0, -1), 8),
                ("RIGHTPADDING", (1, 0), (1, -1), 8),
            ]))
            story.append(fac_table)
            story.append(Spacer(1, 0.5 * cm))

        # Bloc total
        story.append(HRFlowable(width="100%", thickness=1, color=ORANGE, spaceAfter=8))
        total_data = [
            ["Montant total perçu", f"{montant_total:,.0f} FCFA".replace(",", " ")],
            ["Dont affecté", f"{montant_affecte:,.0f} FCFA".replace(",", " ")],
            ["Non affecté", f"{montant_non_affecte:,.0f} FCFA".replace(",", " ")],
        ]
        total_table = Table(total_data, colWidths=["60%", "40%"])
        total_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 0), (1, 0), ORANGE),
            ("FONTSIZE", (0, 0), (1, 0), 13),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(total_table)

        # Notes
        if paiement.get("notes"):
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph("NOTES", style_label))
            story.append(Paragraph(paiement["notes"], styles["Normal"]))

        # Pied de page
        story.append(Spacer(1, 1.5 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6))
        story.append(Paragraph(
            f"Document généré par ERP FABS-CI V10 le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            style_center
        ))
        story.append(Paragraph(
            "Ce reçu constitue une preuve de paiement officielle.",
            style_center
        ))

        doc.build(story)
        buffer.seek(0)

        filename = f"recu-{reference}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    return router


# ---------------------------------------------------------------------------
# Seed (optional demo data)
# ---------------------------------------------------------------------------
async def seed_paiements(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed demo paiements (optional)"""
    existing = await db.paiements.count_documents({})
    if existing > 0:
        return 0
    
    # Get first client and first facture emise
    client = await db.clients.find_one({"actif": True}, {"_id": 0})
    if not client:
        return 0
    
    factures = await db.factures.find({"statut": "emise", "type_facture": "facture"}, {"_id": 0}).limit(1).to_list(1)
    if len(factures) == 0:
        return 0

    facture = factures[0]
    
    # Create 1 demo paiement
    paiement_id = f"pay_{uuid.uuid4().hex[:12]}"
    reference = "FABS-REG-2026-0001"
    montant_affecte = min(facture["montant_ttc"] / 2, 50000)  # Half or 50k max
    
    now = _now_iso()
    paiement_doc = {
        "paiement_id": paiement_id,
        "reference": reference,
        "client_id": client["client_id"],
        "date_paiement": now[:10],
        "mode_paiement": "especes",
        "montant_total": montant_affecte,
        "montant_affecte": montant_affecte,
        "montant_non_affecte": 0.0,
        "banque": None,
        "numero_cheque": None,
        "reference_virement": None,
        "operateur": None,
        "numero_transaction": None,
        "notes": "Paiement de démonstration",
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
    }
    await db.paiements.insert_one(paiement_doc)
    
    # Create affectation
    affectation_doc = {
        "affectation_id": f"aff_{uuid.uuid4().hex[:12]}",
        "paiement_id": paiement_id,
        "facture_id": facture["facture_id"],
        "montant_affecte": montant_affecte,
        "created_at": now,
    }
    await db.affectations_paiement.insert_one(affectation_doc)
    
    # Update facture
    new_montant_regle = facture.get("montant_regle", 0) + montant_affecte
    montant_restant = facture["montant_ttc"] - new_montant_regle
    new_statut = "partiellement_payee" if montant_restant > 0 else "payee"
    
    await db.factures.update_one(
        {"facture_id": facture["facture_id"]},
        {"$set": {
            "montant_regle": round(new_montant_regle, 2),
            "montant_restant": round(montant_restant, 2),
            "statut": new_statut,
            "updated_at": now,
        }}
    )
    
    # Update counter
    await db.counters.update_one(
        {"_id": "paiements"},
        {"$set": {"seq": 1}},
        upsert=True
    )
    
    return 1
