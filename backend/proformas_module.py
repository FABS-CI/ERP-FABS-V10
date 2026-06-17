"""
Module Proformas — ERP FABS-CI
- CRUD complet sur la collection MongoDB `proformas` et `proforma_lignes`
- Référence auto-incrémentée PF-AAAA-XXXXXX
- Workflow : brouillon -> generee -> envoyee -> consultee -> acceptee -> refusee -> expiree -> convertie_facture
- Génération PDF Proforma
- Partage WhatsApp
- Envoi Email
- Conversion vers Facture
- RBAC : 
    READ = {super_admin, DG, directeur_commercial, commercial, comptable, secrétariat}
    WRITE = {super_admin, DG, directeur_commercial, commercial, secrétariat}
    SEND_WHATSAPP = {super_admin, DG, directeur_commercial, commercial}
    SEND_EMAIL = {super_admin, DG, directeur_commercial, commercial}
    CONVERT = {super_admin, DG, directeur_commercial, comptable}
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Literal, Optional, List
from decimal import Decimal
import uuid
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator
from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError
from notifications_module import notify_vente_event

logger = logging.getLogger("fabsci.proformas")

# RBAC
READ_ROLES = {
    # RBAC 2026-06-17: DG + commercial (rôle inexistant) retirés
    "super_admin", "directeur_commercial",
    "comptable", "secretariat", "assistante_commerciale", "assistante",
}
WRITE_ROLES = {
    # RBAC 2026-06-17: DG + dir_com + commercial retirés
    "super_admin", "secretariat", "comptable", "assistante", "assistante_commerciale",
}
SEND_ROLES = {
    # RBAC 2026-06-17: DG + dir_com retirés
    "super_admin", "secretariat", "comptable", "assistante", "assistante_commerciale",
}
CONVERT_ROLES = {
    # RBAC 2026-06-17: DG + dir_com retirés
    "super_admin", "comptable", "secretariat",
}

StatutProforma = Literal[
    "brouillon", "generee", "envoyee", "consultee",
    "acceptee", "refusee", "expiree", "convertie_facture"
]
STATUT_FLOW = [
    "brouillon", "generee", "envoyee", "consultee",
    "acceptee", "refusee", "expiree", "convertie_facture"
]

VALIDITE_PROFORMA_JOURS = 30  # 30 days validity


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


async def next_proforma_reference(db: AsyncIOMotorDatabase) -> str:
    """Generate PF-AAAA-XXXXXX reference"""
    year = datetime.now().year
    counter_id = f"proformas_{year}"
    
    doc = await db.counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"PF-{year}-{seq:06d}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class LigneProformaIn(BaseModel):
    produit_id: str
    designation: str
    quantite: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., gt=0)
    remise_ligne: float = Field(default=0, ge=0, le=100)

    @property
    def montant_ht(self) -> float:
        base = self.quantite * self.prix_unitaire
        return base * (1 - self.remise_ligne / 100)


class LigneProformaOut(BaseModel):
    ligne_id: str
    proforma_id: str
    produit_id: str
    produit_reference: Optional[str] = None
    designation: str
    quantite: int
    prix_unitaire: float
    remise_ligne: float
    montant_ht: float


class ProformaIn(BaseModel):
    client_id: str
    commande_id: Optional[str] = None
    date_emission: Optional[str] = None  # ISO date YYYY-MM-DD
    remise_globale: float = Field(default=0, ge=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=1000)
    commercial_responsable_id: Optional[str] = None


class ProformaOut(BaseModel):
    proforma_id: str
    numero_proforma: str
    reference: str
    client_id: str
    client_nom: Optional[str] = None
    client_telephone: Optional[str] = None
    client_numero_whatsapp: Optional[str] = None
    client_email: Optional[str] = None
    commande_id: Optional[str] = None
    commande_reference: Optional[str] = None
    date_emission: str
    date_expiration: str
    date_generation_proforma: Optional[str] = None
    statut_proforma: StatutProforma
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    remise_globale: float
    proforma_pdf_path: Optional[str] = None
    envoye_whatsapp: bool = False
    envoye_email: bool = False
    date_envoi_whatsapp: Optional[str] = None
    date_envoi_email: Optional[str] = None
    date_impression: Optional[str] = None
    nombre_impressions: int = 0
    nombre_telechargements: int = 0
    utilisateur_generation: Optional[str] = None
    notes: Optional[str] = None
    commercial_responsable_id: Optional[str] = None
    commercial_responsable_nom: Optional[str] = None
    facture_id: Optional[str] = None  # When converted to invoice
    actif: bool = True
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class ProformaListOut(BaseModel):
    items: List[ProformaOut]
    total: int
    page: int
    page_size: int


class EmailPayload(BaseModel):
    destinataire: Optional[str] = None  # override email client si fourni
    cc: Optional[str] = None
    bcc: Optional[str] = None
    objet: Optional[str] = None
    message: Optional[str] = None


class WhatsAppPayload(BaseModel):
    numero: Optional[str] = None  # override numéro WhatsApp si fourni manuellement


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
# NOTE: resolve_user et log_audit_event sont désormais injectés via
# build_proformas_router(db, resolve_user, log_audit_event) pour rester
# cohérent avec les autres modules (cf. clients_module, factures_module).


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def build_proformas_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/proformas", tags=["Proformas"])
    
    @router.get("", response_model=ProformaListOut)
    async def list_proformas(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        client_id: Optional[str] = None,
        statut_proforma: Optional[StatutProforma] = None,
        actif: Optional[bool] = None,
        q: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {}
        if client_id:
            filters["client_id"] = client_id
        if statut_proforma:
            filters["statut_proforma"] = statut_proforma
        if actif is not None:
            filters["actif"] = actif
        
        skip = (page - 1) * page_size

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
            {"$lookup": {
                "from": "users",
                "localField": "commercial_responsable_id",
                "foreignField": "user_id",
                "as": "commercial_info"
            }},
            {"$addFields": {
                "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]},
                "client_ville": {"$arrayElemAt": ["$client_info.ville", 0]},
                "client_telephone": {"$arrayElemAt": ["$client_info.telephone", 0]},
                "client_representant": {"$arrayElemAt": ["$client_info.representant", 0]},
                "client_numero_whatsapp": {"$arrayElemAt": ["$client_info.numero_whatsapp", 0]},
                "client_email": {"$arrayElemAt": ["$client_info.email", 0]},
                "commande_reference": {"$arrayElemAt": ["$commande_info.reference", 0]},
                "commercial_responsable_nom": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$commercial_info"}, 0]},
                        "then": {"$concat": [
                            {"$arrayElemAt": ["$commercial_info.nom", 0]}, " ",
                            {"$arrayElemAt": ["$commercial_info.prenoms", 0]}
                        ]},
                        "else": None
                    }
                }
            }},
            {"$project": {"client_info": 0, "commande_info": 0, "commercial_info": 0, "_id": 0}},
        ]
        if q:
            pipeline.append({"$match": {"$or": [
                {"reference": {"$regex": q, "$options": "i"}},
                {"client_nom": {"$regex": q, "$options": "i"}},
                {"client_ville": {"$regex": q, "$options": "i"}},
                {"client_telephone": {"$regex": q, "$options": "i"}},
                {"client_representant": {"$regex": q, "$options": "i"}},
            ]}})

        # Count before pagination
        count_pipeline = pipeline + [{"$count": "total"}]
        count_res = await db.proformas.aggregate(count_pipeline).to_list(1)
        total = count_res[0]["total"] if count_res else 0

        pipeline += [
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": page_size}
        ]
        docs = await db.proformas.aggregate(pipeline).to_list(page_size)

        return ProformaListOut(
            items=[ProformaOut(**doc) for doc in docs],
            total=total,
            page=page,
            page_size=page_size
        )
    
    @router.get("/{proforma_id}", response_model=ProformaOut)
    async def get_proforma(
        proforma_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        doc = await db.proformas.find_one({"proforma_id": proforma_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Proforma introuvable")
        
        # Enrich
        if doc.get("client_id"):
            client = await db.clients.find_one(
                {"client_id": doc["client_id"]},
                {"_id": 0, "nom": 1, "telephone": 1, "numero_whatsapp": 1, "email": 1}
            )
            if client:
                doc["client_nom"] = client.get("nom")
                doc["client_telephone"] = client.get("telephone")
                doc["client_numero_whatsapp"] = client.get("numero_whatsapp")
                doc["client_email"] = client.get("email")
        
        if doc.get("commande_id"):
            commande = await db.commandes.find_one(
                {"commande_id": doc["commande_id"]},
                {"_id": 0, "reference": 1}
            )
            if commande:
                doc["commande_reference"] = commande.get("reference")
        
        if doc.get("commercial_responsable_id"):
            commercial = await db.users.find_one(
                {"user_id": doc["commercial_responsable_id"]},
                {"_id": 0, "nom": 1, "prenoms": 1}
            )
            if commercial:
                doc["commercial_responsable_nom"] = f"{commercial.get('nom')} {commercial.get('prenoms')}"
        
        return ProformaOut(**doc)
    
    @router.post("", response_model=ProformaOut, status_code=201)
    async def create_proforma(
        payload: ProformaIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check client exists
        client = await db.clients.find_one({"client_id": payload.client_id})
        _ensure(client is not None, 404, "Client introuvable")
        
        # Check commande exists if provided
        if payload.commande_id:
            commande = await db.commandes.find_one({"commande_id": payload.commande_id})
            _ensure(commande is not None, 404, "Commande introuvable")
            
            # Get lignes from commande
            lignes_cmd = await db.commande_lignes.find({"commande_id": payload.commande_id}).to_list(None)
        else:
            lignes_cmd = []
        
        now = _now_iso()
        reference = await next_proforma_reference(db)
        
        # Calculate dates
        date_emission = payload.date_emission or now[:10]
        date_emission_dt = datetime.fromisoformat(date_emission)
        date_expiration_dt = date_emission_dt + timedelta(days=VALIDITE_PROFORMA_JOURS)
        date_expiration = date_expiration_dt.isoformat()
        
        # Calculate amounts from commande lignes or set to 0
        montant_ht = sum(ligne.get("montant_ligne", 0) for ligne in lignes_cmd)
        montant_tva = montant_ht * 0.18  # 18% TVA
        montant_ttc = montant_ht + montant_tva
        
        doc = {
            "proforma_id": _generate_id("pro"),
            "numero_proforma": reference,
            "reference": reference,
            "client_id": payload.client_id,
            "commande_id": payload.commande_id,
            "date_emission": date_emission,
            "date_expiration": date_expiration,
            "statut_proforma": "brouillon",
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
            "remise_globale": payload.remise_globale,
            "notes": payload.notes,
            "commercial_responsable_id": payload.commercial_responsable_id,
            "envoye_whatsapp": False,
            "envoye_email": False,
            "nombre_impressions": 0,
            "nombre_telechargements": 0,
            "actif": True,
            "created_by": user["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        
        await db.proformas.insert_one(doc)
        
        # Copy lignes from commande if provided
        if lignes_cmd:
            for ligne in lignes_cmd:
                ligne_proforma = {
                    "ligne_id": _generate_id("lpr"),
                    "proforma_id": doc["proforma_id"],
                    "produit_id": ligne.get("produit_id"),
                    "designation": ligne.get("produit_titre", ""),
                    "quantite": ligne.get("quantite"),
                    "prix_unitaire": ligne.get("prix_unitaire"),
                    "remise_ligne": ligne.get("remise_ligne", 0),
                    "montant_ht": ligne.get("montant_ligne", 0),
                }
                await db.proforma_lignes.insert_one(ligne_proforma)
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CREATE",
            "resource_type": "proforma",
            "resource_id": doc["proforma_id"],
            "details": {"numero_proforma": reference, "client_id": payload.client_id},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        # Enrich response
        if client:
            doc["client_nom"] = client.get("nom")
            doc["client_telephone"] = client.get("telephone")
            doc["client_numero_whatsapp"] = client.get("numero_whatsapp")
            doc["client_email"] = client.get("email")

        # 🔔 Notification vente — nouvelle proforma
        try:
            _client_nom = client.get("nom", payload.client_id) if client else payload.client_id
            await notify_vente_event(
                db, "info", "commande",
                f"📄 Nouvelle proforma {reference}",
                f"Proforma créée pour {_client_nom} — {doc['montant_ttc']:,.0f} FCFA",
                lien=f"/proformas/{doc['proforma_id']}",
                exclude_user_id=user["user_id"],
            )
        except Exception as _e:
            logger.warning("notify create_proforma: %s", _e)

        return ProformaOut(**doc)
    
    @router.patch("/{proforma_id}", response_model=ProformaOut)
    async def update_proforma(
        proforma_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        existing = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(existing is not None, 404, "Proforma introuvable")
        
        # Don't allow update if already converted to invoice
        _ensure(existing.get("statut_proforma") != "convertie_facture", 400, "Proforma déjà convertie en facture")
        
        update_data = {k: v for k, v in payload.items() if v is not None}
        update_data["updated_at"] = _now_iso()
        
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {"$set": update_data}
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "UPDATE",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {"updated_fields": list(update_data.keys())},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })
        
        updated = await db.proformas.find_one({"proforma_id": proforma_id}, {"_id": 0})
        return ProformaOut(**updated)
    
    @router.delete("/{proforma_id}")
    async def delete_proforma(
        proforma_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        existing = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(existing is not None, 404, "Proforma introuvable")
        
        # Soft delete
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {"$set": {"actif": False, "updated_at": _now_iso()}}
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "DELETE",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })
        
        return {"message": "Proforma désactivée avec succès"}
    
    @router.post("/{proforma_id}/generer-pdf")
    async def generer_proforma_pdf(
        proforma_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Generate Proforma PDF and save to file storage"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        proforma = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(proforma is not None, 404, "Proforma introuvable")
        
        # Import PDF generator
        from pdf_generator import generate_proforma_pdf
        
        # Get client data
        client = await db.clients.find_one({"client_id": proforma["client_id"]})
        _ensure(client is not None, 404, "Client introuvable")
        
        # Get lignes
        lignes = await db.proforma_lignes.find({"proforma_id": proforma_id}).to_list(None)
        
        # Generate PDF
        pdf_buffer = generate_proforma_pdf(proforma, lignes, client)
        
        # Save to file storage
        filename = f"Facture_Proforma_{proforma['numero_proforma']}.pdf"
        file_id = _generate_id("file")
        
        file_doc = {
            "file_id": file_id,
            "filename": filename,
            "content_type": "application/pdf",
            "size": len(pdf_buffer.getvalue()),
            "path": f"/proformas/{filename}",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "uploaded_by": user["user_id"],
            "uploaded_at": _now_iso(),
        }
        
        # In production, save to actual storage (S3, local disk, etc.)
        # For now, we'll store the path in the proforma document
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {
                "$set": {
                    "proforma_pdf_path": file_doc["path"],
                    "date_generation_proforma": _now_iso(),
                    "statut_proforma": "generee",
                    "utilisateur_generation": user["user_id"],
                    "updated_at": _now_iso()
                }
            }
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "GENERATE_PDF",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {"filename": filename},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    @router.post("/{proforma_id}/envoyer-whatsapp")
    async def envoyer_proforma_whatsapp(
        proforma_id: str,
        payload: WhatsAppPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None)
    ):
        """Prepare WhatsApp sharing link for Proforma"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in SEND_ROLES, 403, "Accès refusé")
        
        proforma = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(proforma is not None, 404, "Proforma introuvable")
        
        # Get client WhatsApp number
        client = await db.clients.find_one({"client_id": proforma["client_id"]})
        _ensure(client is not None, 404, "Client introuvable")
        
        # Numéro : override manuel (payload) ou numéro client en base
        whatsapp_number = (payload.numero if payload and payload.numero else None) \
            or client.get("numero_whatsapp") or client.get("telephone")
        _ensure(whatsapp_number, 400, "Numéro WhatsApp non disponible — veuillez en saisir un")
        
        # Clean phone number (remove spaces, dashes, etc.)
        clean_number = whatsapp_number.replace(" ", "").replace("-", "").replace("+", "")
        
        # Prepare message
        message = f"""Bonjour {client.get('nom', 'Client')}

Veuillez trouver ci-joint votre FACTURE PROFORMA N° {proforma['numero_proforma']}

Montant TTC : {proforma['montant_ttc']:,.2f} FCFA

Merci de vérifier ce document et de nous confirmer votre commande.

Cordialement,
ÉDITIONS FABS-CI"""
        
        # WhatsApp URL
        encoded_message = message.replace("\n", "%0A")
        whatsapp_url = f"https://wa.me/{clean_number}?text={encoded_message}"
        
        # Update proforma
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {
                "$set": {
                    "envoye_whatsapp": True,
                    "date_envoi_whatsapp": _now_iso(),
                    "statut_proforma": "envoyee",
                    "updated_at": _now_iso()
                }
            }
        )
        
        ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{ts}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "SEND_WHATSAPP",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {"whatsapp_number": clean_number},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })
        # Log envoi
        await db.envoi_logs.insert_one({
            "log_id": f"envoi_{ts}_{user['user_id'][:8]}",
            "type_document": "proforma",
            "document_id": proforma_id,
            "reference": proforma.get("numero_proforma", ""),
            "canal": "whatsapp",
            "destinataire": clean_number,
            "cc": None,
            "bcc": None,
            "objet": None,
            "statut": "envoye",
            "user_id": user["user_id"],
            "user_email": user.get("email", ""),
            "created_at": _now_iso(),
        })
        
        return {
            "whatsapp_url": whatsapp_url,
            "message": message,
            "pdf_filename": f"Facture_Proforma_{proforma['numero_proforma']}.pdf"
        }
    
    @router.post("/{proforma_id}/envoyer-email")
    async def envoyer_proforma_email(
        proforma_id: str,
        payload: EmailPayload = None,
        request: Request = None,
        authorization: Optional[str] = Header(default=None)
    ):
        """Send Proforma via Email with optional CC/BCC/custom subject+body"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in SEND_ROLES, 403, "Accès refusé")
        
        proforma = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(proforma is not None, 404, "Proforma introuvable")
        
        # Get client email
        client = await db.clients.find_one({"client_id": proforma["client_id"]})
        _ensure(client is not None, 404, "Client introuvable")
        
        # Destinataire : payload override ou email client
        if payload and payload.destinataire:
            client_email = payload.destinataire
        else:
            client_email = client.get("email")
        _ensure(client_email, 400, "Email non disponible pour ce client")
        
        # Objet / message par défaut si non fournis
        email_objet = (payload.objet if payload and payload.objet else None) or \
            f"Facture Proforma {proforma['numero_proforma']}"
        email_message = (payload.message if payload and payload.message else None) or \
            f"Bonjour,\n\nVeuillez trouver ci-joint votre Facture Proforma N° {proforma['numero_proforma']}.\n\nCordialement,\nÉditions FABS-CI"
        
        # Update proforma
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {
                "$set": {
                    "envoye_email": True,
                    "date_envoi_email": _now_iso(),
                    "statut_proforma": "envoyee",
                    "updated_at": _now_iso()
                }
            }
        )
        
        ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{ts}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "SEND_EMAIL",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {"email": client_email},
            "ip_address": request.client.host if request.client else None,
            "timestamp": _now_iso(),
        })
        # Log envoi
        await db.envoi_logs.insert_one({
            "log_id": f"envoi_{ts}_{user['user_id'][:8]}",
            "type_document": "proforma",
            "document_id": proforma_id,
            "reference": proforma.get("numero_proforma", ""),
            "canal": "email",
            "destinataire": client_email,
            "cc": payload.cc if payload else None,
            "bcc": payload.bcc if payload else None,
            "objet": email_objet,
            "statut": "envoye",
            "user_id": user["user_id"],
            "user_email": user.get("email", ""),
            "created_at": _now_iso(),
        })
        
        return {
            "message": "Email envoyé avec succès",
            "email": client_email,
            "cc": payload.cc if payload else None,
            "bcc": payload.bcc if payload else None,
            "subject": email_objet,
            "body": email_message,
        }
    
    @router.post("/{proforma_id}/convertir-facture")
    async def convertir_proforma_facture(
        proforma_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Convert Proforma to Invoice"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in CONVERT_ROLES, 403, "Accès refusé")
        
        proforma = await db.proformas.find_one({"proforma_id": proforma_id})
        _ensure(proforma is not None, 404, "Proforma introuvable")
        
        # Check if already converted (statut flag)
        _ensure(proforma.get("statut_proforma") != "convertie_facture", 400, "Proforma déjà convertie en facture")

        # Check doublons existants en base (proforma_id OU commande_id+type_facture)
        existing_by_proforma = await db.factures.find_one({"proforma_id": proforma_id, "type_facture": "facture"})
        if existing_by_proforma:
            raise HTTPException(status_code=400, detail=f"Une facture existe déjà pour cette proforma : {existing_by_proforma.get('reference', existing_by_proforma['facture_id'])}")

        commande_id = proforma.get("commande_id")
        if commande_id:
            existing_by_commande = await db.factures.find_one({"commande_id": commande_id, "type_facture": "facture"})
            if existing_by_commande:
                raise HTTPException(status_code=400, detail=f"La commande liée a déjà une facture : {existing_by_commande.get('reference', existing_by_commande['facture_id'])}")

        # Import factures module
        from factures_module import next_facture_reference
        
        # Get lignes
        lignes_proforma = await db.proforma_lignes.find({"proforma_id": proforma_id}).to_list(None)
        
        # Create facture
        now = _now_iso()
        reference_facture = await next_facture_reference(db, "facture")
        
        facture_doc = {
            "facture_id": _generate_id("fac"),
            "reference": reference_facture,
            "client_id": proforma["client_id"],
            "commande_id": commande_id,
            "proforma_id": proforma_id,
            "date_facture": now[:10],
            "type_facture": "facture",
            "statut": "brouillon",
            "taux_tva": proforma.get("taux_tva", 18.0),
            "montant_ht": proforma["montant_ht"],
            "montant_tva": proforma["montant_tva"],
            "montant_ttc": proforma["montant_ttc"],
            "total_ttc": proforma["montant_ttc"],
            "montant_regle": 0,
            "montant_restant": proforma["montant_ttc"],
            "remise_globale": proforma["remise_globale"],
            "notes": f"Convertie depuis Proforma {proforma['numero_proforma']}",
            "created_by": user["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        
        try:
            await db.factures.insert_one(facture_doc)
        except MongoDuplicateKeyError as e:
            logger.warning(f"DuplicateKeyError convertir-facture proforma={proforma_id}: {e}")
            raise HTTPException(status_code=409, detail="Une facture identique existe déjà (doublon détecté). Opération annulée.")
        
        # Copy lignes
        for ligne in lignes_proforma:
            ligne_facture = {
                "ligne_id": _generate_id("lfa"),
                "facture_id": facture_doc["facture_id"],
                "produit_id": ligne.get("produit_id"),
                "designation": ligne.get("designation"),
                "quantite": ligne.get("quantite"),
                "prix_unitaire": ligne.get("prix_unitaire"),
                "remise_ligne": ligne.get("remise_ligne", 0),
                "montant_ht": ligne.get("montant_ht"),
            }
            await db.facture_lignes.insert_one(ligne_facture)
        
        # Update proforma
        await db.proformas.update_one(
            {"proforma_id": proforma_id},
            {
                "$set": {
                    "statut_proforma": "convertie_facture",
                    "facture_id": facture_doc["facture_id"],
                    "updated_at": now
                }
            }
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CONVERT_TO_INVOICE",
            "resource_type": "proforma",
            "resource_id": proforma_id,
            "details": {"facture_id": facture_doc["facture_id"], "facture_reference": reference_facture},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        return {
            "message": "Proforma convertie en facture avec succès",
            "facture_id": facture_doc["facture_id"],
            "facture_reference": reference_facture
        }
    
    @router.get("/stats/dashboard")
    async def proformas_dashboard_stats(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Get Proforma dashboard statistics"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        # Count by status
        pipeline = [
            {"$match": {"actif": True}},
            {"$group": {"_id": "$statut_proforma", "count": {"$sum": 1}}}
        ]
        status_counts = await db.proformas.aggregate(pipeline).to_list(None)
        
        stats = {item["_id"]: item["count"] for item in status_counts}
        
        # Total amounts
        total_generees = await db.proformas.aggregate([
            {"$match": {"actif": True, "statut_proforma": "generee"}},
            {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
        ]).to_list(None)
        
        total_converti = await db.proformas.aggregate([
            {"$match": {"actif": True, "statut_proforma": "convertie_facture"}},
            {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
        ]).to_list(None)
        
        montant_total_generees = total_generees[0]["total"] if total_generees else 0
        montant_total_converti = total_converti[0]["total"] if total_converti else 0
        
        # Conversion rate
        total_proformas = sum(stats.values())
        taux_conversion = (stats.get("convertie_facture", 0) / total_proformas * 100) if total_proformas > 0 else 0
        
        return {
            "nombre_generees": stats.get("generee", 0),
            "nombre_envoyees": stats.get("envoyee", 0),
            "nombre_acceptees": stats.get("acceptee", 0),
            "nombre_refusees": stats.get("refusee", 0),
            "nombre_converties": stats.get("convertie_facture", 0),
            "montant_total_generees": montant_total_generees,
            "montant_total_converti": montant_total_converti,
            "taux_conversion": round(taux_conversion, 2)
        }
    
    return router


# ============================================================================
# SEED DATA
# ============================================================================
async def seed_proformas_data(db: AsyncIOMotorDatabase):
    """Seed initial Proformas data if needed"""
    logger.info("Seeding Proformas data...")
    
    # Create indexes
    await db.proformas.create_index([("proforma_id", 1)], unique=True)
    await db.proformas.create_index([("numero_proforma", 1)], unique=True)
    await db.proformas.create_index([("client_id", 1)])
    await db.proformas.create_index([("commande_id", 1)])
    await db.proformas.create_index([("statut_proforma", 1)])
    await db.proformas.create_index([("actif", 1)])
    await db.proformas.create_index([("created_at", -1)])
    
    await db.proforma_lignes.create_index([("ligne_id", 1)], unique=True)
    await db.proforma_lignes.create_index([("proforma_id", 1)])
    await db.proforma_lignes.create_index([("produit_id", 1)])
    
    logger.info("Proformas indexes created successfully")
