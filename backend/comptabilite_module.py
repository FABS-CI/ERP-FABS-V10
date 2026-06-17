"""
Module Comptabilité — Sprint 12
- Génération écritures comptables depuis factures/paiements
- Suivi créances clients
- Journaux comptables (ventes, banque, caisse)
- États comptables (balance, grand livre)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional, List
import uuid
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger("fabsci.comptabilite")

READ_ROLES = {"super_admin", "directeur_general", "comptable"}
WRITE_ROLES = {"super_admin", "comptable"}

TypeJournal = Literal["ventes", "achats", "banque", "caisse", "operations_diverses"]


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def generate_ecriture_comptable_facture(
    db: AsyncIOMotorDatabase,
    facture_id: str,
    facture_reference: str,
    client_id: str,
    montant_ht: float,
    montant_tva: float,
    montant_ttc: float,
    user_id: str,
    log_audit_event=None
) -> str:
    """
    Génère automatiquement les écritures comptables pour une facture de vente.
    Débit 411 (Client) = montant TTC
    Crédit 701 (Ventes) = montant HT
    Crédit 44571 (TVA collectée) = montant TVA
    """
    now = _now_iso()
    date_facture = now[:10]
    
    # Écriture 1 : Débit client (411)
    ecriture1_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture1_doc = {
        "ecriture_id": ecriture1_id,
        "journal": "ventes",
        "date_ecriture": date_facture,
        "compte": "411",
        "libelle": f"Client {client_id} - Facture {facture_reference}",
        "debit": montant_ttc,
        "credit": 0.0,
        "piece_reference": facture_reference,
        "facture_id": facture_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture1_doc)
    
    # Écriture 2 : Crédit ventes (701)
    ecriture2_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture2_doc = {
        "ecriture_id": ecriture2_id,
        "journal": "ventes",
        "date_ecriture": date_facture,
        "compte": "701",
        "libelle": f"Vente - Facture {facture_reference}",
        "debit": 0.0,
        "credit": montant_ht,
        "piece_reference": facture_reference,
        "facture_id": facture_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture2_doc)
    
    # Écriture 3 : Crédit TVA collectée (44571)
    ecriture3_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture3_doc = {
        "ecriture_id": ecriture3_id,
        "journal": "ventes",
        "date_ecriture": date_facture,
        "compte": "44571",
        "libelle": f"TVA collectée - Facture {facture_reference}",
        "debit": 0.0,
        "credit": montant_tva,
        "piece_reference": facture_reference,
        "facture_id": facture_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture3_doc)
    
    # Audit log
    if log_audit_event:
        await log_audit_event(
            user_id=user_id,
            action="GENERATE_ECRITURE_FACTURE",
            resource_type="ecriture_comptable",
            resource_id=ecriture1_id,
            details={
                "piece_reference": facture_reference,
                "facture_id": facture_id,
                "client_id": client_id,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc
            },
            ip_address=None
        )
    
    return ecriture1_id


async def generate_ecriture_comptable_avoir(
    db: AsyncIOMotorDatabase,
    avoir_id: str,
    avoir_reference: str,
    client_id: str,
    montant_ht: float,
    montant_tva: float,
    montant_ttc: float,
    facture_origine_id: str,
    user_id: str,
    log_audit_event=None
) -> str:
    """
    Génère automatiquement les écritures comptables pour un avoir (contrepassation).
    Crédit 411 (Client) = montant TTC
    Débit 701 (Ventes) = montant HT
    Débit 44571 (TVA collectée) = montant TVA
    """
    now = _now_iso()
    date_avoir = now[:10]
    
    # Écriture 1 : Crédit client (411)
    ecriture1_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture1_doc = {
        "ecriture_id": ecriture1_id,
        "journal": "ventes",
        "date_ecriture": date_avoir,
        "compte": "411",
        "libelle": f"Avoir client {client_id} - {avoir_reference}",
        "debit": 0.0,
        "credit": abs(montant_ttc),
        "piece_reference": avoir_reference,
        "facture_id": avoir_id,
        "facture_origine_id": facture_origine_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture1_doc)
    
    # Écriture 2 : Débit ventes (701)
    ecriture2_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture2_doc = {
        "ecriture_id": ecriture2_id,
        "journal": "ventes",
        "date_ecriture": date_avoir,
        "compte": "701",
        "libelle": f"Contrepassation vente - {avoir_reference}",
        "debit": abs(montant_ht),
        "credit": 0.0,
        "piece_reference": avoir_reference,
        "facture_id": avoir_id,
        "facture_origine_id": facture_origine_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture2_doc)
    
    # Écriture 3 : Débit TVA collectée (44571)
    ecriture3_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture3_doc = {
        "ecriture_id": ecriture3_id,
        "journal": "ventes",
        "date_ecriture": date_avoir,
        "compte": "44571",
        "libelle": f"Contrepassation TVA - {avoir_reference}",
        "debit": abs(montant_tva),
        "credit": 0.0,
        "piece_reference": avoir_reference,
        "facture_id": avoir_id,
        "facture_origine_id": facture_origine_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture3_doc)
    
    # Audit log
    if log_audit_event:
        await log_audit_event(
            user_id=user_id,
            action="GENERATE_ECRITURE_AVOIR",
            resource_type="ecriture_comptable",
            resource_id=ecriture1_id,
            details={
                "piece_reference": avoir_reference,
                "avoir_id": avoir_id,
                "client_id": client_id,
                "facture_origine_id": facture_origine_id,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc
            },
            ip_address=None
        )
    
    return ecriture1_id


async def generate_ecriture_comptable_paiement(
    db: AsyncIOMotorDatabase,
    paiement_id: str,
    paiement_reference: str,
    facture_id: str,
    client_id: str,
    montant: float,
    mode_paiement: str,
    user_id: str,
    log_audit_event=None
) -> str:
    """
    Génère automatiquement les écritures comptables pour un paiement.
    Débit 512 (Banque) ou 53 (Caisse) = montant
    Crédit 411 (Client) = montant
    """
    now = _now_iso()
    date_paiement = now[:10]
    
    # Déterminer le compte selon le mode de paiement
    if mode_paiement in ["virement", "cheque"]:
        compte_debit = "512"
        journal = "banque"
    else:  # especes, mobile
        compte_debit = "53"
        journal = "caisse"
    
    # Écriture 1 : Débit banque/caisse
    ecriture1_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture1_doc = {
        "ecriture_id": ecriture1_id,
        "journal": journal,
        "date_ecriture": date_paiement,
        "compte": compte_debit,
        "libelle": f"Encaissement client {client_id} - {paiement_reference}",
        "debit": montant,
        "credit": 0.0,
        "piece_reference": paiement_reference,
        "paiement_id": paiement_id,
        "facture_id": facture_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture1_doc)
    
    # Écriture 2 : Crédit client (411)
    ecriture2_id = f"ecr_{uuid.uuid4().hex[:12]}"
    ecriture2_doc = {
        "ecriture_id": ecriture2_id,
        "journal": journal,
        "date_ecriture": date_paiement,
        "compte": "411",
        "libelle": f"Règlement client {client_id} - {paiement_reference}",
        "debit": 0.0,
        "credit": montant,
        "piece_reference": paiement_reference,
        "paiement_id": paiement_id,
        "facture_id": facture_id,
        "created_by": user_id,
        "created_at": now,
    }
    await db.ecritures_comptables.insert_one(ecriture2_doc)
    
    # Audit log
    if log_audit_event:
        await log_audit_event(
            user_id=user_id,
            action="GENERATE_ECRITURE_PAIEMENT",
            resource_type="ecriture_comptable",
            resource_id=ecriture1_id,
            details={
                "piece_reference": paiement_reference,
                "paiement_id": paiement_id,
                "client_id": client_id,
                "facture_id": facture_id,
                "montant": montant,
                "mode_paiement": mode_paiement,
                "compte_debit": compte_debit
            },
            ip_address=None
        )
    
    return ecriture1_id


async def validate_ecriture_equilibre(db: AsyncIOMotorDatabase, piece_reference: str) -> bool:
    """
    Valide que les écritures comptables pour une pièce sont équilibrées (débit = crédit).
    """
    pipeline = [
        {"$match": {"piece_reference": piece_reference}},
        {
            "$group": {
                "_id": None,
                "total_debit": {"$sum": "$debit"},
                "total_credit": {"$sum": "$credit"}
            }
        }
    ]
    
    result = await db.ecritures_comptables.aggregate(pipeline).to_list(1)
    if not result:
        return True  # Pas d'écritures, considéré comme équilibré
    
    total_debit = result[0]["total_debit"]
    total_credit = result[0]["total_credit"]
    
    # Tolérance de 0.01 pour les erreurs d'arrondi
    return abs(total_debit - total_credit) < 0.01


class EcritureComptableIn(BaseModel):
    journal: TypeJournal
    date_ecriture: str
    compte: str  # Numéro de compte
    libelle: str
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    piece_reference: Optional[str] = None  # Reference facture/paiement


class EcritureComptableOut(BaseModel):
    ecriture_id: str
    journal: TypeJournal
    date_ecriture: str
    compte: str
    libelle: str
    debit: float
    credit: float
    piece_reference: Optional[str] = None
    created_by: str
    created_at: str


class CreanceClient(BaseModel):
    client_id: str
    client_nom: str
    montant_total_factures: float
    montant_total_paye: float
    montant_restant: float
    nombre_factures: int


def build_comptabilite_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/comptabilite", tags=["comptabilite"])

    # ---------- ECRITURES COMPTABLES ----------
    @router.get("/ecritures", response_model=List[EcritureComptableOut])
    async def list_ecritures(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        journal: Optional[TypeJournal] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if journal:
            filters["journal"] = journal
        if date_debut or date_fin:
            date_filter = {}
            if date_debut:
                date_filter["$gte"] = date_debut
            if date_fin:
                date_filter["$lte"] = date_fin
            filters["date_ecriture"] = date_filter

        cursor = db.ecritures_comptables.find(filters, {"_id": 0}).sort("date_ecriture", -1).limit(limit)
        docs = await cursor.to_list(limit)
        
        return [EcritureComptableOut(**d) for d in docs]

    @router.post("/ecritures", response_model=EcritureComptableOut, status_code=201)
    async def create_ecriture(
        payload: EcritureComptableIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        _ensure(payload.debit > 0 or payload.credit > 0, 400, "Débit ou crédit doit être > 0")
        _ensure(not (payload.debit > 0 and payload.credit > 0), 400, "Débit et crédit ne peuvent pas être tous les deux > 0")

        ecriture_id = f"ecr_{uuid.uuid4().hex[:12]}"
        now = _now_iso()

        ecriture_doc = {
            "ecriture_id": ecriture_id,
            "journal": payload.journal,
            "date_ecriture": payload.date_ecriture,
            "compte": payload.compte,
            "libelle": payload.libelle,
            "debit": payload.debit,
            "credit": payload.credit,
            "piece_reference": payload.piece_reference,
            "created_by": me["user_id"],
            "created_at": now,
        }
        await db.ecritures_comptables.insert_one(ecriture_doc)

        return EcritureComptableOut(**ecriture_doc)

    # ---------- CREANCES CLIENTS ----------
    @router.get("/creances", response_model=List[CreanceClient])
    async def get_creances_clients(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        # Aggregate factures par client with $lookup to avoid N+1
        pipeline = [
            {
                "$match": {
                    "type_facture": "facture",
                    "statut": {"$in": ["emise", "partiellement_payee"]}
                }
            },
            {
                "$group": {
                    "_id": "$client_id",
                    "montant_total_factures": {"$sum": "$montant_ttc"},
                    "montant_total_paye": {"$sum": "$montant_regle"},
                    "montant_restant": {"$sum": "$montant_restant"},
                    "nombre_factures": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": "clients",
                    "localField": "_id",
                    "foreignField": "client_id",
                    "as": "client_info"
                }
            },
            {
                "$addFields": {
                    "client_nom": {"$arrayElemAt": ["$client_info.nom", 0]}
                }
            },
            {
                "$project": {
                    "client_info": 0
                }
            }
        ]
        
        creances = await db.factures.aggregate(pipeline).to_list(200)
        
        result = [
            CreanceClient(
                client_id=creance["_id"],
                client_nom=creance.get("client_nom", "Client inconnu"),
                montant_total_factures=round(creance["montant_total_factures"], 2),
                montant_total_paye=round(creance["montant_total_paye"], 2),
                montant_restant=round(creance["montant_restant"], 2),
                nombre_factures=creance["nombre_factures"]
            )
            for creance in creances if creance.get("client_nom")
        ]
        
        # Sort by montant_restant desc
        result.sort(key=lambda x: x.montant_restant, reverse=True)
        
        return result

    # ---------- BALANCE ----------
    @router.get("/balance")
    async def get_balance(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if date_debut or date_fin:
            date_filter = {}
            if date_debut:
                date_filter["$gte"] = date_debut
            if date_fin:
                date_filter["$lte"] = date_fin
            filters["date_ecriture"] = date_filter

        # Aggregate by compte
        pipeline = [
            {"$match": filters} if filters else {"$match": {}},
            {
                "$group": {
                    "_id": "$compte",
                    "total_debit": {"$sum": "$debit"},
                    "total_credit": {"$sum": "$credit"}
                }
            }
        ]
        
        cursor = db.ecritures_comptables.aggregate(pipeline)
        balances = await cursor.to_list(500)
        
        result = []
        for balance in balances:
            solde = balance["total_debit"] - balance["total_credit"]
            result.append({
                "compte": balance["_id"],
                "total_debit": round(balance["total_debit"], 2),
                "total_credit": round(balance["total_credit"], 2),
                "solde": round(solde, 2)
            })
        
        return result

    return router


async def seed_comptabilite(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed indexes"""
    await db.ecritures_comptables.create_index("ecriture_id", unique=True)
    await db.ecritures_comptables.create_index("journal")
    await db.ecritures_comptables.create_index("date_ecriture")
    await db.ecritures_comptables.create_index("compte")
    
    return 0
