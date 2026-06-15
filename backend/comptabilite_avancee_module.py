"""
Module Comptabilité Avancée - Plan comptable, journaux, écritures automatiques, rapprochement bancaire
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger("fabsci.comptabilite_avancee")

# ============================================================================
# SCHEMAS
# ============================================================================

class CompteComptableIn(BaseModel):
    numero: str = Field(pattern="^\d{6}$")
    intitule: str
    parent_id: Optional[str] = None
    type: str = Field(pattern="^(actif|passif|charge|produit)$")
    classe: int = Field(ge=1, le=9)
    actif: bool = True

class CompteComptableOut(BaseModel):
    compte_id: str
    numero: str
    intitule: str
    parent_id: Optional[str] = None
    type: str
    classe: int
    solde_debit: float = 0.0
    solde_credit: float = 0.0
    actif: bool = True
    created_at: str

class JournalComptableIn(BaseModel):
    code: str
    intitule: str
    type: str = Field(pattern="^(ventes|achats|banque|od)$")
    actif: bool = True

class JournalComptableOut(BaseModel):
    journal_id: str
    code: str
    intitule: str
    type: str
    actif: bool
    created_at: str

class LigneEcriture(BaseModel):
    compte_id: str
    compte_numero: str
    compte_intitule: str
    debit: float = Field(ge=0)
    credit: float = Field(ge=0)

class EcritureComptableIn(BaseModel):
    journal_id: str
    date_ecriture: str
    libelle: str
    lignes: List[LigneEcriture]
    reference_source: Optional[str] = None
    type_source: Optional[str] = None

class EcritureComptableOut(BaseModel):
    ecriture_id: str
    journal_id: str
    reference: str
    date_ecriture: str
    libelle: str
    lignes: List[dict]
    montant_total_debit: float
    montant_total_credit: float
    reference_source: Optional[str] = None
    type_source: Optional[str] = None
    created_at: str
    created_by: str

class OperationBancaire(BaseModel):
    date: str
    reference: str
    libelle: str
    montant: float
    lettrage: Optional[str] = None

class RapprochementBancaireIn(BaseModel):
    compte_bancaire_id: str
    date_rapprochement: str
    solde_initial: float
    solde_final: float
    operations_bancaires: List[OperationBancaire]

class RapprochementBancaireOut(BaseModel):
    rapprochement_id: str
    compte_bancaire_id: str
    date_rapprochement: str
    solde_initial: float
    solde_final: float
    ecritures_lettrees: List[str]
    operations_bancaires: List[dict]
    ecarts: List[dict]
    created_at: str
    created_by: str

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "comptable"]
WRITE_ROLES = ["super_admin", "admin", "comptable"]
DELETE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _generate_reference(prefix: str) -> str:
    """Génère une référence unique"""
    year = datetime.now().strftime("%Y")
    return f"{prefix}-{year}-{datetime.now().strftime('%m%d%H%M%S')}"

async def _generate_ecriture_automatique_facture(db, facture_id: str, user_id: str):
    """Génère automatiquement l'écriture comptable pour une facture"""
    facture = await db.factures.find_one({"facture_id": facture_id})
    if not facture:
        return None

    # Récupérer le journal des ventes (VTE) — fallback sur tout journal actif
    journal = await db.journaux_comptables.find_one({"code": "VTE", "actif": True})
    if not journal:
        journal = await db.journaux_comptables.find_one({"actif": True})
    if not journal:
        return None

    # Récupérer les comptes SYSCOHADA
    compte_clients = await db.plan_comptable.find_one({"numero": "411000"})
    compte_ventes = await db.plan_comptable.find_one({"numero": "701000"})
    compte_tva = await db.plan_comptable.find_one({"numero": "443100"})

    if not compte_clients or not compte_ventes:
        return None

    montant_ht = facture["montant_ht"]
    montant_tva = facture["montant_tva"]
    montant_ttc = facture["montant_ttc"]

    lignes = [
        {
            "compte_id": compte_clients["compte_id"],
            "compte_numero": compte_clients["numero"],
            "compte_intitule": compte_clients["intitule"],
            "debit": montant_ttc,
            "credit": 0
        },
        {
            "compte_id": compte_ventes["compte_id"],
            "compte_numero": compte_ventes["numero"],
            "compte_intitule": compte_ventes["intitule"],
            "debit": 0,
            "credit": montant_ht
        }
    ]

    if compte_tva and montant_tva > 0:
        lignes.append({
            "compte_id": compte_tva["compte_id"],
            "compte_numero": compte_tva["numero"],
            "compte_intitule": compte_tva["intitule"],
            "debit": 0,
            "credit": montant_tva
        })

    ecriture_id = f"ecr_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    ecriture_doc = {
        "ecriture_id": ecriture_id,
        "journal_id": journal["journal_id"],
        "reference": _generate_reference("FABS-ECR"),
        "date_ecriture": facture["date_facture"],
        "libelle": f"Facture {facture['reference']}",
        "lignes": lignes,
        "montant_total_debit": montant_ttc,
        "montant_total_credit": montant_ttc,
        "reference_source": facture_id,
        "type_source": "facture",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "system"
    }

    await db.ecritures_comptables.insert_one(ecriture_doc)
    
    # Mettre à jour les soldes des comptes
    for ligne in lignes:
        await db.plan_comptable.update_one(
            {"compte_id": ligne["compte_id"]},
            {"$inc": {"solde_debit": ligne["debit"], "solde_credit": ligne["credit"]}}
        )

    logger.info(f"Écriture automatique générée pour facture {facture_id}")
    return ecriture_id

async def _generate_ecriture_automatique_paiement(db, paiement_id: str, user_id: str):
    """Génère automatiquement l'écriture comptable pour un paiement"""
    paiement = await db.paiements.find_one({"paiement_id": paiement_id})
    if not paiement:
        return None

    # Récupérer le journal de banque (BQ) — fallback sur tout journal actif
    journal = await db.journaux_comptables.find_one({"code": "BQ", "actif": True})
    if not journal:
        journal = await db.journaux_comptables.find_one({"actif": True})
    if not journal:
        return None

    # Récupérer les comptes SYSCOHADA
    compte_banque = await db.plan_comptable.find_one({"numero": "521000"})
    compte_clients = await db.plan_comptable.find_one({"numero": "411000"})

    if not compte_banque or not compte_clients:
        return None

    montant = paiement.get("montant") or paiement.get("montant_total") or paiement.get("montant_affecte") or 0

    lignes = [
        {
            "compte_id": compte_banque["compte_id"],
            "compte_numero": compte_banque["numero"],
            "compte_intitule": compte_banque["intitule"],
            "debit": montant,
            "credit": 0
        },
        {
            "compte_id": compte_clients["compte_id"],
            "compte_numero": compte_clients["numero"],
            "compte_intitule": compte_clients["intitule"],
            "debit": 0,
            "credit": montant
        }
    ]

    ecriture_id = f"ecr_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    ecriture_doc = {
        "ecriture_id": ecriture_id,
        "journal_id": journal["journal_id"],
        "reference": _generate_reference("FABS-ECR"),
        "date_ecriture": paiement["date_paiement"],
        "libelle": f"Paiement {paiement['reference']}",
        "lignes": lignes,
        "montant_total_debit": montant,
        "montant_total_credit": montant,
        "reference_source": paiement_id,
        "type_source": "paiement",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "system"
    }

    await db.ecritures_comptables.insert_one(ecriture_doc)
    
    # Mettre à jour les soldes des comptes
    for ligne in lignes:
        await db.plan_comptable.update_one(
            {"compte_id": ligne["compte_id"]},
            {"$inc": {"solde_debit": ligne["debit"], "solde_credit": ligne["credit"]}}
        )

    logger.info(f"Écriture automatique générée pour paiement {paiement_id}")
    return ecriture_id

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_comptabilite_avancee_router(db, resolve_user):
    router = APIRouter(prefix="/comptabilite-avancee", tags=["comptabilite-avancee"])

    # ============================================================================
    # PLAN COMPTABLE ENDPOINTS
    # ============================================================================

    @router.get("/plan-comptable", response_model=List[CompteComptableOut])
    async def list_plan_comptable(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        classe: Optional[int] = None,
        actif: Optional[bool] = None,
        limit: int = Query(200, le=500),
        skip: int = Query(0, ge=0)
    ):
        """Lister le plan comptable"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if classe:
            filters["classe"] = classe
        if actif is not None:
            filters["actif"] = actif

        cursor = db.plan_comptable.find(filters, {"_id": 0}).sort("numero", 1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [CompteComptableOut(**d) for d in docs]

    @router.post("/plan-comptable", response_model=CompteComptableOut, status_code=201)
    async def create_compte_comptable(
        payload: CompteComptableIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un compte comptable"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        compte_id = f"cpt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        compte_doc = {
            "compte_id": compte_id,
            "numero": payload.numero,
            "intitule": payload.intitule,
            "parent_id": payload.parent_id,
            "type": payload.type,
            "classe": payload.classe,
            "solde_debit": 0,
            "solde_credit": 0,
            "actif": payload.actif,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.plan_comptable.insert_one(compte_doc)
        logger.info(f"Compte comptable créé: {payload.numero} par {user['email']}")
        
        return CompteComptableOut(**compte_doc)

    # ============================================================================
    # JOURNAUX COMPTABLES ENDPOINTS
    # ============================================================================

    @router.get("/journaux", response_model=List[JournalComptableOut])
    async def list_journaux(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Lister les journaux comptables"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        cursor = db.journaux_comptables.find({}, {"_id": 0}).sort("code", 1)
        docs = await cursor.to_list(50)
        return [JournalComptableOut(**d) for d in docs]

    @router.post("/journaux", response_model=JournalComptableOut, status_code=201)
    async def create_journal(
        payload: JournalComptableIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un journal comptable"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        journal_id = f"journal_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        journal_doc = {
            "journal_id": journal_id,
            "code": payload.code,
            "intitule": payload.intitule,
            "type": payload.type,
            "actif": payload.actif,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.journaux_comptables.insert_one(journal_doc)
        logger.info(f"Journal comptable créé: {payload.code} par {user['email']}")
        
        return JournalComptableOut(**journal_doc)

    # ============================================================================
    # ECRITURES COMPTABLES ENDPOINTS
    # ============================================================================

    @router.get("/ecritures", response_model=List[EcritureComptableOut])
    async def list_ecritures(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        journal_id: Optional[str] = None,
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les écritures comptables"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if journal_id:
            filters["journal_id"] = journal_id
        if date_debut:
            filters["date_ecriture"] = {"$gte": date_debut}
        if date_fin:
            if "date_ecriture" in filters:
                filters["date_ecriture"]["$lte"] = date_fin
            else:
                filters["date_ecriture"] = {"$lte": date_fin}

        cursor = db.ecritures_comptables.find(filters, {"_id": 0}).sort("date_ecriture", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [EcritureComptableOut(**d) for d in docs]

    @router.post("/ecritures", response_model=EcritureComptableOut, status_code=201)
    async def create_ecriture(
        payload: EcritureComptableIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une écriture comptable manuelle"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        # Vérifier l'équilibre débit/crédit
        total_debit = sum(l.debit for l in payload.lignes)
        total_credit = sum(l.credit for l in payload.lignes)
        
        if abs(total_debit - total_credit) > 0.01:
            raise HTTPException(status_code=400, detail="L'écriture n'est pas équilibrée")

        ecriture_id = f"ecr_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        ecriture_doc = {
            "ecriture_id": ecriture_id,
            "journal_id": payload.journal_id,
            "reference": _generate_reference("FABS-ECR"),
            "date_ecriture": payload.date_ecriture,
            "libelle": payload.libelle,
            "lignes": [l.dict() for l in payload.lignes],
            "montant_total_debit": total_debit,
            "montant_total_credit": total_credit,
            "reference_source": payload.reference_source,
            "type_source": payload.type_source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.ecritures_comptables.insert_one(ecriture_doc)
        
        # Mettre à jour les soldes des comptes
        for ligne in payload.lignes:
            await db.plan_comptable.update_one(
                {"compte_id": ligne.compte_id},
                {"$inc": {"solde_debit": ligne.debit, "solde_credit": ligne.credit}}
            )

        logger.info(f"Écriture comptable créée: {ecriture_doc['reference']} par {user['email']}")
        return EcritureComptableOut(**ecriture_doc)

    @router.post("/ecritures/auto/facture/{facture_id}")
    async def generate_ecriture_facture(
        facture_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Générer automatiquement l'écriture pour une facture"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        ecriture_id = await _generate_ecriture_automatique_facture(db, facture_id, user["user_id"])
        
        if not ecriture_id:
            raise HTTPException(status_code=400, detail="Impossible de générer l'écriture")
        
        return {"message": "Écriture générée", "ecriture_id": ecriture_id}

    @router.post("/ecritures/auto/paiement/{paiement_id}")
    async def generate_ecriture_paiement(
        paiement_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Générer automatiquement l'écriture pour un paiement"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        ecriture_id = await _generate_ecriture_automatique_paiement(db, paiement_id, user["user_id"])
        
        if not ecriture_id:
            raise HTTPException(status_code=400, detail="Impossible de générer l'écriture")
        
        return {"message": "Écriture générée", "ecriture_id": ecriture_id}

    # ============================================================================
    # RAPPROCHEMENT BANCAIRE ENDPOINTS
    # ============================================================================

    @router.get("/rapprochements", response_model=List[RapprochementBancaireOut])
    async def list_rapprochements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        compte_bancaire_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les rapprochements bancaires"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if compte_bancaire_id:
            filters["compte_bancaire_id"] = compte_bancaire_id

        cursor = db.rapprochements_bancaires.find(filters, {"_id": 0}).sort("date_rapprochement", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [RapprochementBancaireOut(**d) for d in docs]

    @router.post("/rapprochements", response_model=RapprochementBancaireOut, status_code=201)
    async def create_rapprochement(
        payload: RapprochementBancaireIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un rapprochement bancaire"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        rapprochement_id = f"rapp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # Lettrage automatique simplifié
        ecritures_lettrees = []
        ecarts = []

        for op in payload.operations_bancaires:
            # Recherche d'une écriture correspondante
            ecriture = await db.ecritures_comptables.find_one({
                "date_ecriture": op.date,
                "montant_total_debit": op.montant
            })
            if ecriture:
                ecritures_lettrees.append(ecriture["ecriture_id"])
                op.lettrage = ecriture["ecriture_id"]
            else:
                ecarts.append({
                    "type": "ecart_montant",
                    "description": f"Opération non lettrée: {op.reference}",
                    "montant": op.montant
                })

        rapprochement_doc = {
            "rapprochement_id": rapprochement_id,
            "compte_bancaire_id": payload.compte_bancaire_id,
            "date_rapprochement": payload.date_rapprochement,
            "solde_initial": payload.solde_initial,
            "solde_final": payload.solde_final,
            "ecritures_lettrees": ecritures_lettrees,
            "operations_bancaires": [op.dict() for op in payload.operations_bancaires],
            "ecarts": ecarts,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.rapprochements_bancaires.insert_one(rapprochement_doc)
        logger.info(f"Rapprochement bancaire créé: {rapprochement_id} par {user['email']}")
        
        return RapprochementBancaireOut(**rapprochement_doc)

    return router
