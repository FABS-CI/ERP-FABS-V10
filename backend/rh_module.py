"""
Module Ressources Humaines - ERP FABS-CI
- Gestion complète des employés
- Départements, Fonctions, Catégories professionnelles
- Contrats, Congés, Absences, Missions
- Évaluations, Délégations, Habilitations ERP
- Dashboard RH et Rapports
- Intégration RBAC, Notifications, Audit Trail, Document Management
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta, date as date_type
from typing import Literal, Optional, List, Dict, Any
import uuid
import logging
import re

from fastapi import APIRouter, HTTPException, Header, Query, Request, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator, EmailStr

logger = logging.getLogger("fabsci.rh")

# ============================================================================
# RBAC - Permissions
# ============================================================================
READ_ROLES = {
    "super_admin", "directeur_general", "responsable_rh",
    "comptable", "directeur_commercial", "secretariat",
}
WRITE_ROLES = {
    "super_admin", "directeur_general", "responsable_rh",
}
DELETE_ROLES = {
    "super_admin", "directeur_general",
}
APPROVE_ROLES = {
    "super_admin", "directeur_general", "responsable_rh",
}

# ============================================================================
# TYPES & LITERALS
# ============================================================================
Sexe = Literal["H", "F"]
SituationMatrimoniale = Literal["Celibataire", "Marie(e)", "Divorce(e)", "Veuf/Veuve"]
TypeEmploye = Literal["Direction", "Administration", "Commercial", "Logistique", "Stock", "Informatique", "Comptabilite"]
StatutEmploye = Literal["Actif", "En conge", "Suspendu", "Demissionnaire", "Licencie", "Retraite"]
TypeContrat = Literal["CDI", "CDD", "Stage", "Consultant", "Prestataire"]
StatutContrat = Literal["Actif", "Expiré", "Resilie"]
TypeConge = Literal["conge_annuel", "conge_maladie", "conge_maternite", "permission", "conge_exceptionnel"]
StatutConge = Literal["en_attente", "approuve_sup", "approuve_direction", "approuve_rh", "refuse", "annule"]
TypeAbsence = Literal["retard", "absence_justifiee", "absence_non_justifiee", "sortie_autorisee"]
TypeMission = Literal["mission_commerciale", "mission_logistique", "mission_administrative", "mission_inventaire"]
StatutMission = Literal["planifiee", "en_cours", "terminee", "annulee"]
TypeEvaluation = Literal["commercial", "magasinier", "gestionnaire_stock", "administratif"]
StatutEvaluation = Literal["brouillon", "soumis", "approuve", "refuse"]

# ============================================================================
# UTILITAIRES
# ============================================================================
def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

async def next_reference(db: AsyncIOMotorDatabase, counter_id: str, prefix: str) -> str:
    """Generate auto-incremented reference"""
    doc = await db.counters.find_one_and_update(
        {"_id": counter_id},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"{prefix}-{seq:04d}"

# ============================================================================
# SCHEMAS - EMPLOYES
# ============================================================================
class EmployeIn(BaseModel):
    matricule: str = Field(..., min_length=3, max_length=20)
    nom: str = Field(..., min_length=2, max_length=100)
    prenoms: str = Field(..., min_length=2, max_length=100)
    photo: Optional[str] = None
    sexe: Sexe
    date_naissance: str  # ISO date YYYY-MM-DD
    lieu_naissance: str = Field(..., max_length=100)
    nationalite: str = Field(default="Côte d'Ivoire", max_length=50)
    situation_matrimoniale: SituationMatrimoniale
    nombre_enfants: int = Field(default=0, ge=0)
    groupe_sanguin: Optional[str] = Field(default=None, max_length=5)
    telephone_principal: str = Field(..., min_length=8, max_length=20)
    telephone_secondaire: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    adresse: str = Field(..., max_length=200)
    ville: str = Field(..., max_length=50)
    commune: Optional[str] = Field(default=None, max_length=50)
    personne_a_prevenir: str = Field(..., max_length=100)
    telephone_urgence: str = Field(..., min_length=8, max_length=20)
    numero_cni: str = Field(..., min_length=10, max_length=20)
    date_delivrance_cni: str  # ISO date YYYY-MM-DD
    date_expiration_cni: str  # ISO date YYYY-MM-DD
    numero_cnps: str = Field(..., min_length=10, max_length=20)
    date_affiliation_cnps: str  # ISO date YYYY-MM-DD
    numero_cmu: Optional[str] = Field(default=None, max_length=20)
    numero_compte_bancaire: Optional[str] = Field(default=None, max_length=30)
    banque: Optional[str] = Field(default=None, max_length=50)
    numero_permis: Optional[str] = Field(default=None, max_length=20)
    date_expiration_permis: Optional[str] = None  # ISO date YYYY-MM-DD
    date_embauche: str  # ISO date YYYY-MM-DD
    date_prise_fonction: str  # ISO date YYYY-MM-DD
    departement_id: str
    fonction_id: str
    categorie_pro_id: str
    echelon: Optional[str] = Field(default=None, max_length=20)
    superieur_hierarchique_id: Optional[str] = None
    type_employe: TypeEmploye
    statut: StatutEmploye = Field(default="Actif")
    zone_commerciale: Optional[str] = Field(default=None, max_length=100)
    portefeuille_clients: Optional[List[str]] = Field(default=None)
    objectif_mensuel: Optional[float] = Field(default=None, ge=0)
    objectif_annuel: Optional[float] = Field(default=None, ge=0)
    commission: Optional[float] = Field(default=None, ge=0)
    montant_ventes: Optional[float] = Field(default=0, ge=0)
    montant_encaisse: Optional[float] = Field(default=0, ge=0)
    creances_clients: Optional[float] = Field(default=0, ge=0)
    depot_principal: Optional[str] = Field(default=None, max_length=50)
    responsable_inventaire: Optional[bool] = Field(default=False)
    responsable_reapprovisionnement: Optional[bool] = Field(default=False)
    responsable_controle_stock: Optional[bool] = Field(default=False)
    user_id: Optional[str] = None

class EmployeOut(BaseModel):
    employe_id: str
    matricule: str
    nom: str
    prenoms: str
    photo: Optional[str] = None
    sexe: Sexe
    date_naissance: str
    lieu_naissance: str
    nationalite: str
    situation_matrimoniale: SituationMatrimoniale
    nombre_enfants: int
    groupe_sanguin: Optional[str] = None
    telephone_principal: str
    telephone_secondaire: Optional[str] = None
    email: Optional[str] = None
    adresse: str
    ville: str
    commune: Optional[str] = None
    personne_a_prevenir: str
    telephone_urgence: str
    numero_cni: str
    date_delivrance_cni: str
    date_expiration_cni: str
    numero_cnps: str
    date_affiliation_cnps: str
    numero_cmu: Optional[str] = None
    numero_compte_bancaire: Optional[str] = None
    banque: Optional[str] = None
    numero_permis: Optional[str] = None
    date_expiration_permis: Optional[str] = None
    date_embauche: str
    date_prise_fonction: str
    departement_id: str
    departement_nom: Optional[str] = None
    fonction_id: str
    fonction_nom: Optional[str] = None
    categorie_pro_id: str
    categorie_pro_nom: Optional[str] = None
    echelon: Optional[str] = None
    superieur_hierarchique_id: Optional[str] = None
    superieur_nom: Optional[str] = None
    type_employe: TypeEmploye
    statut: StatutEmploye
    zone_commerciale: Optional[str] = None
    portefeuille_clients: Optional[List[str]] = []
    objectif_mensuel: Optional[float] = None
    objectif_annuel: Optional[float] = None
    commission: Optional[float] = None
    montant_ventes: Optional[float] = None
    montant_encaisse: Optional[float] = None
    creances_clients: Optional[float] = None
    depot_principal: Optional[str] = None
    responsable_inventaire: Optional[bool] = None
    responsable_reapprovisionnement: Optional[bool] = None
    responsable_controle_stock: Optional[bool] = None
    user_id: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - DEPARTEMENTS
# ============================================================================
class DepartementIn(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    responsable_id: Optional[str] = None

class DepartementOut(BaseModel):
    departement_id: str
    nom: str
    description: Optional[str] = None
    responsable_id: Optional[str] = None
    responsable_nom: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - FONCTIONS
# ============================================================================
class FonctionIn(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    departement_id: Optional[str] = None

class FonctionOut(BaseModel):
    fonction_id: str
    nom: str
    description: Optional[str] = None
    departement_id: Optional[str] = None
    departement_nom: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - CATEGORIES PROFESSIONNELLES
# ============================================================================
class CategorieProIn(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

class CategorieProOut(BaseModel):
    categorie_pro_id: str
    nom: str
    description: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - CONTRATS
# ============================================================================
class ContratIn(BaseModel):
    employe_id: str
    type_contrat: TypeContrat
    date_debut: str  # ISO date YYYY-MM-DD
    date_fin: Optional[str] = None  # ISO date YYYY-MM-DD
    periode_essai: Optional[int] = Field(default=None, ge=0)  # jours
    salaire_base: float = Field(..., gt=0)
    prime_transport: float = Field(default=0, ge=0)
    prime_logement: float = Field(default=0, ge=0)
    prime_fonction: float = Field(default=0, ge=0)
    autres_primes: float = Field(default=0, ge=0)
    observations: Optional[str] = Field(default=None, max_length=1000)
    document_id: Optional[str] = None

class ContratOut(BaseModel):
    contrat_id: str
    reference: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    type_contrat: TypeContrat
    date_debut: str
    date_fin: Optional[str] = None
    periode_essai: Optional[int] = None
    salaire_base: float
    prime_transport: float
    prime_logement: float
    prime_fonction: float
    autres_primes: float
    observations: Optional[str] = None
    statut: StatutContrat
    document_id: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - CONGES
# ============================================================================
class CongeIn(BaseModel):
    employe_id: str
    type_conge: TypeConge
    date_debut: str  # ISO date YYYY-MM-DD
    date_fin: str  # ISO date YYYY-MM-DD
    nombre_jours: int = Field(..., gt=0)
    motif: str = Field(..., min_length=5, max_length=500)
    piece_jointe_id: Optional[str] = None

class CongeOut(BaseModel):
    conge_id: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    type_conge: TypeConge
    date_debut: str
    date_fin: str
    nombre_jours: int
    motif: str
    piece_jointe_id: Optional[str] = None
    statut: StatutConge
    superieur_hierarchique_id: Optional[str] = None
    approbation_sup_date: Optional[str] = None
    approbation_sup_commentaire: Optional[str] = None
    approbation_direction_id: Optional[str] = None
    approbation_direction_nom: Optional[str] = None
    approbation_direction_date: Optional[str] = None
    approbation_direction_commentaire: Optional[str] = None
    approbation_rh_id: Optional[str] = None
    approbation_rh_nom: Optional[str] = None
    approbation_rh_date: Optional[str] = None
    approbation_rh_commentaire: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

class ApprobationCongeIn(BaseModel):
    commentaire: Optional[str] = Field(default=None, max_length=500)

# ============================================================================
# SCHEMAS - ABSENCES
# ============================================================================
class AbsenceIn(BaseModel):
    employe_id: str
    type_absence: TypeAbsence
    date: str  # ISO date YYYY-MM-DD
    heure_debut: Optional[str] = None  # ISO time HH:MM
    heure_fin: Optional[str] = None  # ISO time HH:MM
    duree_minutes: int = Field(default=0, ge=0)
    motif: Optional[str] = Field(default=None, max_length=500)
    justifie: bool = Field(default=False)
    piece_jointe_id: Optional[str] = None

class AbsenceOut(BaseModel):
    absence_id: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    type_absence: TypeAbsence
    date: str
    heure_debut: Optional[str] = None
    heure_fin: Optional[str] = None
    duree_minutes: int
    motif: Optional[str] = None
    justifie: bool
    piece_jointe_id: Optional[str] = None
    enregistre_par_id: str
    enregistre_par_nom: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - MISSIONS
# ============================================================================
class MissionIn(BaseModel):
    employe_id: str
    type_mission: TypeMission
    ville: str = Field(..., max_length=100)
    date_depart: str  # ISO date YYYY-MM-DD
    date_retour: str  # ISO date YYYY-MM-DD
    objet: str = Field(..., min_length=5, max_length=500)
    budget: Optional[float] = Field(default=None, ge=0)
    compte_rendu: Optional[str] = Field(default=None, max_length=2000)
    document_id: Optional[str] = None

class MissionOut(BaseModel):
    mission_id: str
    reference: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    type_mission: TypeMission
    ville: str
    date_depart: str
    date_retour: str
    objet: str
    budget: Optional[float] = None
    compte_rendu: Optional[str] = None
    statut: StatutMission
    document_id: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - HABILITATIONS ERP
# ============================================================================
class HabilitationIn(BaseModel):
    employe_id: str
    role_erp: str
    modules_autorises: List[str] = Field(default_factory=list)
    date_debut: str  # ISO date YYYY-MM-DD
    date_fin: Optional[str] = None  # ISO date YYYY-MM-DD

class HabilitationOut(BaseModel):
    habilitation_id: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    role_erp: str
    modules_autorises: List[str]
    date_debut: str
    date_fin: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - EVALUATIONS
# ============================================================================
class EvaluationIn(BaseModel):
    employe_id: str
    type_evaluation: TypeEvaluation
    periode_debut: str  # ISO date YYYY-MM-DD
    periode_fin: str  # ISO date YYYY-MM-DD
    criteres: Dict[str, Any] = Field(default_factory=dict)
    note_globale: Optional[float] = Field(default=None, ge=0, le=100)
    commentaire: Optional[str] = Field(default=None, max_length=2000)
    evaluateur_id: str

class EvaluationOut(BaseModel):
    evaluation_id: str
    employe_id: str
    employe_nom: Optional[str] = None
    employe_matricule: Optional[str] = None
    type_evaluation: TypeEvaluation
    periode_debut: str
    periode_fin: str
    criteres: Dict[str, Any]
    note_globale: Optional[float] = None
    commentaire: Optional[str] = None
    evaluateur_id: str
    evaluateur_nom: Optional[str] = None
    statut: StatutEvaluation
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - DELEGATIONS
# ============================================================================
class DelegationIn(BaseModel):
    titulaire_id: str
    remplacant_id: str
    date_debut: str  # ISO date YYYY-MM-DD
    date_fin: str  # ISO date YYYY-MM-DD
    motif: str = Field(..., min_length=5, max_length=500)

class DelegationOut(BaseModel):
    delegation_id: str
    titulaire_id: str
    titulaire_nom: Optional[str] = None
    titulaire_matricule: Optional[str] = None
    remplacant_id: str
    remplacant_nom: Optional[str] = None
    remplacant_matricule: Optional[str] = None
    date_debut: str
    date_fin: str
    motif: str
    actif: bool
    created_at: str
    updated_at: str

# ============================================================================
# SCHEMAS - DASHBOARD RH
# ============================================================================
class RHDashboardStats(BaseModel):
    total_employes: int
    employes_actifs: int
    employes_conge: int
    employes_absents: int
    contrats_actifs: int
    contrats_expirant_90: int
    contrats_expirant_30: int
    contrats_expires: int
    missions_en_cours: int
    conges_en_attente: int
    documents_expires: int

class RHAlerte(BaseModel):
    type: str
    message: str
    severite: str
    donnees: Optional[Dict[str, Any]] = None

# ============================================================================
# ROUTER FACTORY
# ============================================================================
def build_rh_router(db: AsyncIOMotorDatabase, resolve_user) -> APIRouter:
    router = APIRouter(prefix="/rh", tags=["rh"])
    
    # =========================================================================
    # DASHBOARD RH
    # =========================================================================
    @router.get("/dashboard", response_model=RHDashboardStats)
    async def get_rh_dashboard(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        now = datetime.now(timezone.utc)
        date_90_jours = (now + timedelta(days=90)).isoformat()
        date_30_jours = (now + timedelta(days=30)).isoformat()
        
        total_employes = await db.employes.count_documents({"actif": True})
        employes_actifs = await db.employes.count_documents({"actif": True, "statut": "Actif"})
        employes_conge = await db.employes.count_documents({"actif": True, "statut": "En conge"})
        employes_absents = await db.employes.count_documents({"actif": True, "statut": "Suspendu"})
        
        contrats_actifs = await db.contrats.count_documents({"actif": True, "statut": "Actif"})
        contrats_expirant_90 = await db.contrats.count_documents({
            "actif": True,
            "date_fin": {"$lte": date_90_jours, "$gt": now.isoformat()}
        })
        contrats_expirant_30 = await db.contrats.count_documents({
            "actif": True,
            "date_fin": {"$lte": date_30_jours, "$gt": now.isoformat()}
        })
        contrats_expires = await db.contrats.count_documents({
            "actif": True,
            "date_fin": {"$lte": now.isoformat()}
        })
        
        missions_en_cours = await db.missions.count_documents({"actif": True, "statut": "en_cours"})
        conges_en_attente = await db.conges.count_documents({"actif": True, "statut": "en_attente"})
        
        # Documents expirés (CNI, Permis)
        documents_expires = await db.employes.count_documents({
            "actif": True,
            "$or": [
                {"date_expiration_cni": {"$lte": now.isoformat()}},
                {"date_expiration_permis": {"$lte": now.isoformat()}}
            ]
        })
        
        return RHDashboardStats(
            total_employes=total_employes,
            employes_actifs=employes_actifs,
            employes_conge=employes_conge,
            employes_absents=employes_absents,
            contrats_actifs=contrats_actifs,
            contrats_expirant_90=contrats_expirant_90,
            contrats_expirant_30=contrats_expirant_30,
            contrats_expires=contrats_expires,
            missions_en_cours=missions_en_cours,
            conges_en_attente=conges_en_attente,
            documents_expires=documents_expires
        )
    
    @router.get("/dashboard/alertes", response_model=List[RHAlerte])
    async def get_rh_alertes(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        now = datetime.now(timezone.utc)
        date_90_jours = (now + timedelta(days=90)).isoformat()
        date_30_jours = (now + timedelta(days=30)).isoformat()
        
        alertes = []
        
        # Contrats expirant dans 90 jours
        contrats_90 = await db.contrats.find({
            "actif": True,
            "date_fin": {"$lte": date_90_jours, "$gt": now.isoformat()}
        }).to_list(100)
        if contrats_90:
            alertes.append(RHAlerte(
                type="contrat_expirant_90",
                message=f"{len(contrats_90)} contrat(s) expire(nt) dans 90 jours",
                severite="warning",
                donnees={"count": len(contrats_90)}
            ))
        
        # Contrats expirant dans 30 jours
        contrats_30 = await db.contrats.find({
            "actif": True,
            "date_fin": {"$lte": date_30_jours, "$gt": now.isoformat()}
        }).to_list(100)
        if contrats_30:
            alertes.append(RHAlerte(
                type="contrat_expirant_30",
                message=f"{len(contrats_30)} contrat(s) expire(nt) dans 30 jours",
                severite="error",
                donnees={"count": len(contrats_30)}
            ))
        
        # CNI expirées
        cni_expires = await db.employes.find({
            "actif": True,
            "date_expiration_cni": {"$lte": now.isoformat()}
        }).to_list(100)
        if cni_expires:
            alertes.append(RHAlerte(
                type="cni_expiree",
                message=f"{len(cni_expires)} CNI expirée(s)",
                severite="error",
                donnees={"count": len(cni_expires)}
            ))
        
        # CNPS manquante
        cnps_manquantes = await db.employes.count_documents({
            "actif": True,
            "$or": [
                {"numero_cnps": None},
                {"numero_cnps": ""}
            ]
        })
        if cnps_manquantes > 0:
            alertes.append(RHAlerte(
                type="cnps_manquante",
                message=f"{cnps_manquantes} employé(s) sans CNPS",
                severite="warning",
                donnees={"count": cnps_manquantes}
            ))
        
        # Congés en attente
        conges_attente = await db.conges.count_documents({
            "actif": True,
            "statut": "en_attente"
        })
        if conges_attente > 0:
            alertes.append(RHAlerte(
                type="conge_en_attente",
                message=f"{conges_attente} demande(s) de congé en attente",
                severite="info",
                donnees={"count": conges_attente}
            ))
        
        # Missions non clôturées
        missions_non_cloturees = await db.missions.count_documents({
            "actif": True,
            "statut": "en_cours",
            "date_retour": {"$lt": now.isoformat()}
        })
        if missions_non_cloturees > 0:
            alertes.append(RHAlerte(
                type="mission_non_cloturee",
                message=f"{missions_non_cloturees} mission(s) non clôturée(s)",
                severite="warning",
                donnees={"count": missions_non_cloturees}
            ))
        
        return alertes
    
    # =========================================================================
    # EMPLOYES
    # =========================================================================
    @router.get("/employes", response_model=List[EmployeOut])
    async def list_employes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = None,
        departement_id: Optional[str] = None,
        fonction_id: Optional[str] = None,
        categorie_pro_id: Optional[str] = None,
        statut: Optional[StatutEmploye] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {"actif": True} if actif is None or actif else {}
        
        if q:
            filters["$or"] = [
                {"nom": {"$regex": q, "$options": "i"}},
                {"prenoms": {"$regex": q, "$options": "i"}},
                {"matricule": {"$regex": q, "$options": "i"}},
            ]
        
        if departement_id:
            filters["departement_id"] = departement_id
        if fonction_id:
            filters["fonction_id"] = fonction_id
        if categorie_pro_id:
            filters["categorie_pro_id"] = categorie_pro_id
        if statut:
            filters["statut"] = statut
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.employes.find(filters, {"_id": 0})
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with related data
        for doc in docs:
            # Departement
            if doc.get("departement_id"):
                dept = await db.departements.find_one(
                    {"departement_id": doc["departement_id"]},
                    {"_id": 0, "nom": 1}
                )
                doc["departement_nom"] = dept.get("nom") if dept else None
            
            # Fonction
            if doc.get("fonction_id"):
                fonc = await db.fonctions.find_one(
                    {"fonction_id": doc["fonction_id"]},
                    {"_id": 0, "nom": 1}
                )
                doc["fonction_nom"] = fonc.get("nom") if fonc else None
            
            # Catégorie pro
            if doc.get("categorie_pro_id"):
                cat = await db.categories_pro.find_one(
                    {"categorie_pro_id": doc["categorie_pro_id"]},
                    {"_id": 0, "nom": 1}
                )
                doc["categorie_pro_nom"] = cat.get("nom") if cat else None
            
            # Supérieur hiérarchique
            if doc.get("superieur_hierarchique_id"):
                sup = await db.employes.find_one(
                    {"employe_id": doc["superieur_hierarchique_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if sup:
                    doc["superieur_nom"] = f"{sup['nom']} {sup['prenoms']}"
        
        return [EmployeOut(**doc) for doc in docs]
    
    @router.get("/employes/{employe_id}", response_model=EmployeOut)
    async def get_employe(
        employe_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        doc = await db.employes.find_one({"employe_id": employe_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Employé introuvable")
        
        # Enrich with related data
        if doc.get("departement_id"):
            dept = await db.departements.find_one(
                {"departement_id": doc["departement_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["departement_nom"] = dept.get("nom") if dept else None
        
        if doc.get("fonction_id"):
            fonc = await db.fonctions.find_one(
                {"fonction_id": doc["fonction_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["fonction_nom"] = fonc.get("nom") if fonc else None
        
        if doc.get("categorie_pro_id"):
            cat = await db.categories_pro.find_one(
                {"categorie_pro_id": doc["categorie_pro_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["categorie_pro_nom"] = cat.get("nom") if cat else None
        
        if doc.get("superieur_hierarchique_id"):
            sup = await db.employes.find_one(
                {"employe_id": doc["superieur_hierarchique_id"]},
                {"_id": 0, "nom": 1, "prenoms": 1}
            )
            if sup:
                doc["superieur_nom"] = f"{sup['nom']} {sup['prenoms']}"
        
        return EmployeOut(**doc)
    
    @router.post("/employes", response_model=EmployeOut, status_code=201)
    async def create_employe(
        payload: EmployeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check matricule unique
        existing = await db.employes.find_one({"matricule": payload.matricule})
        _ensure(existing is None, 409, "Matricule déjà utilisé")
        
        # Check CNI unique
        existing_cni = await db.employes.find_one({"numero_cni": payload.numero_cni})
        _ensure(existing_cni is None, 409, "Numéro CNI déjà utilisé")
        
        # Check CNPS unique
        existing_cnps = await db.employes.find_one({"numero_cnps": payload.numero_cnps})
        _ensure(existing_cnps is None, 409, "Numéro CNPS déjà utilisé")
        
        now = _now_iso()
        doc = {
            "employe_id": _generate_id("emp"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.employes.insert_one(doc)
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CREATE",
            "resource_type": "employe",
            "resource_id": doc["employe_id"],
            "details": {"matricule": payload.matricule, "nom": payload.nom, "prenoms": payload.prenoms},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        # Enrich for response
        if doc.get("departement_id"):
            dept = await db.departements.find_one(
                {"departement_id": doc["departement_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["departement_nom"] = dept.get("nom") if dept else None
        
        if doc.get("fonction_id"):
            fonc = await db.fonctions.find_one(
                {"fonction_id": doc["fonction_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["fonction_nom"] = fonc.get("nom") if fonc else None
        
        if doc.get("categorie_pro_id"):
            cat = await db.categories_pro.find_one(
                {"categorie_pro_id": doc["categorie_pro_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["categorie_pro_nom"] = cat.get("nom") if cat else None
        
        return EmployeOut(**doc)
    
    @router.patch("/employes/{employe_id}", response_model=EmployeOut)
    async def update_employe(
        employe_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.employes.find_one({"employe_id": employe_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Employé introuvable")
        
        # Check matricule unique if changed
        if "matricule" in payload and payload["matricule"] != doc["matricule"]:
            existing = await db.employes.find_one({"matricule": payload["matricule"]})
            _ensure(existing is None, 409, "Matricule déjà utilisé")
        
        now = _now_iso()
        updates = {**payload, "updated_at": now}
        
        await db.employes.update_one(
            {"employe_id": employe_id},
            {"$set": updates}
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "UPDATE",
            "resource_type": "employe",
            "resource_id": employe_id,
            "details": {"updates": list(payload.keys())},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        updated = await db.employes.find_one({"employe_id": employe_id}, {"_id": 0})
        
        # Enrich for response
        if updated.get("departement_id"):
            dept = await db.departements.find_one(
                {"departement_id": updated["departement_id"]},
                {"_id": 0, "nom": 1}
            )
            updated["departement_nom"] = dept.get("nom") if dept else None
        
        if updated.get("fonction_id"):
            fonc = await db.fonctions.find_one(
                {"fonction_id": updated["fonction_id"]},
                {"_id": 0, "nom": 1}
            )
            updated["fonction_nom"] = fonc.get("nom") if fonc else None
        
        if updated.get("categorie_pro_id"):
            cat = await db.categories_pro.find_one(
                {"categorie_pro_id": updated["categorie_pro_id"]},
                {"_id": 0, "nom": 1}
            )
            updated["categorie_pro_nom"] = cat.get("nom") if cat else None
        
        return EmployeOut(**updated)
    
    @router.delete("/employes/{employe_id}")
    async def delete_employe(
        employe_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès refusé")
        
        doc = await db.employes.find_one({"employe_id": employe_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Employé introuvable")
        
        now = _now_iso()
        await db.employes.update_one(
            {"employe_id": employe_id},
            {"$set": {"actif": False, "updated_at": now}}
        )
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "DELETE",
            "resource_type": "employe",
            "resource_id": employe_id,
            "details": {"matricule": doc["matricule"]},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        return {"message": "Employé désactivé avec succès"}
    
    # =========================================================================
    # DEPARTEMENTS
    # =========================================================================
    @router.get("/departements", response_model=List[DepartementOut])
    async def list_departements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        actif: Optional[bool] = None
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None else {"actif": actif}
        
        cursor = db.departements.find(filters, {"_id": 0}).sort([("nom", 1)])
        docs = await cursor.to_list(100)
        
        # Enrich with responsable
        for doc in docs:
            if doc.get("responsable_id"):
                resp = await db.employes.find_one(
                    {"employe_id": doc["responsable_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if resp:
                    doc["responsable_nom"] = f"{resp['nom']} {resp['prenoms']}"
        
        return [DepartementOut(**doc) for doc in docs]
    
    @router.post("/departements", response_model=DepartementOut, status_code=201)
    async def create_departement(
        payload: DepartementIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        existing = await db.departements.find_one({"nom": payload.nom})
        _ensure(existing is None, 409, "Département déjà existant")
        
        now = _now_iso()
        doc = {
            "departement_id": _generate_id("dep"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.departements.insert_one(doc)
        
        # Enrich
        if doc.get("responsable_id"):
            resp = await db.employes.find_one(
                {"employe_id": doc["responsable_id"]},
                {"_id": 0, "nom": 1, "prenoms": 1}
            )
            if resp:
                doc["responsable_nom"] = f"{resp['nom']} {resp['prenoms']}"
        
        return DepartementOut(**doc)
    
    @router.patch("/departements/{departement_id}", response_model=DepartementOut)
    async def update_departement(
        departement_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.departements.find_one({"departement_id": departement_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Département introuvable")
        
        now = _now_iso()
        await db.departements.update_one(
            {"departement_id": departement_id},
            {"$set": {**payload, "updated_at": now}}
        )
        
        updated = await db.departements.find_one({"departement_id": departement_id}, {"_id": 0})
        
        # Enrich
        if updated.get("responsable_id"):
            resp = await db.employes.find_one(
                {"employe_id": updated["responsable_id"]},
                {"_id": 0, "nom": 1, "prenoms": 1}
            )
            if resp:
                updated["responsable_nom"] = f"{resp['nom']} {resp['prenoms']}"
        
        return DepartementOut(**updated)
    
    @router.delete("/departements/{departement_id}")
    async def delete_departement(
        departement_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès refusé")
        
        doc = await db.departements.find_one({"departement_id": departement_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Département introuvable")
        
        now = _now_iso()
        await db.departements.update_one(
            {"departement_id": departement_id},
            {"$set": {"actif": False, "updated_at": now}}
        )
        
        return {"message": "Département désactivé avec succès"}
    
    # =========================================================================
    # FONCTIONS
    # =========================================================================
    @router.get("/fonctions", response_model=List[FonctionOut])
    async def list_fonctions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        actif: Optional[bool] = None
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None else {"actif": actif}
        
        cursor = db.fonctions.find(filters, {"_id": 0}).sort([("nom", 1)])
        docs = await cursor.to_list(100)
        
        # Enrich with departement
        for doc in docs:
            if doc.get("departement_id"):
                dept = await db.departements.find_one(
                    {"departement_id": doc["departement_id"]},
                    {"_id": 0, "nom": 1}
                )
                doc["departement_nom"] = dept.get("nom") if dept else None
        
        return [FonctionOut(**doc) for doc in docs]
    
    @router.post("/fonctions", response_model=FonctionOut, status_code=201)
    async def create_fonction(
        payload: FonctionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        existing = await db.fonctions.find_one({"nom": payload.nom})
        _ensure(existing is None, 409, "Fonction déjà existante")
        
        now = _now_iso()
        doc = {
            "fonction_id": _generate_id("fnc"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.fonctions.insert_one(doc)
        
        # Enrich
        if doc.get("departement_id"):
            dept = await db.departements.find_one(
                {"departement_id": doc["departement_id"]},
                {"_id": 0, "nom": 1}
            )
            doc["departement_nom"] = dept.get("nom") if dept else None
        
        return FonctionOut(**doc)
    
    @router.patch("/fonctions/{fonction_id}", response_model=FonctionOut)
    async def update_fonction(
        fonction_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.fonctions.find_one({"fonction_id": fonction_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Fonction introuvable")
        
        now = _now_iso()
        await db.fonctions.update_one(
            {"fonction_id": fonction_id},
            {"$set": {**payload, "updated_at": now}}
        )
        
        updated = await db.fonctions.find_one({"fonction_id": fonction_id}, {"_id": 0})
        
        # Enrich
        if updated.get("departement_id"):
            dept = await db.departements.find_one(
                {"departement_id": updated["departement_id"]},
                {"_id": 0, "nom": 1}
            )
            updated["departement_nom"] = dept.get("nom") if dept else None
        
        return FonctionOut(**updated)
    
    @router.delete("/fonctions/{fonction_id}")
    async def delete_fonction(
        fonction_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès refusé")
        
        doc = await db.fonctions.find_one({"fonction_id": fonction_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Fonction introuvable")
        
        now = _now_iso()
        await db.fonctions.update_one(
            {"fonction_id": fonction_id},
            {"$set": {"actif": False, "updated_at": now}}
        )
        
        return {"message": "Fonction désactivée avec succès"}
    
    # =========================================================================
    # CATEGORIES PROFESSIONNELLES
    # =========================================================================
    @router.get("/categories-pro", response_model=List[CategorieProOut])
    async def list_categories_pro(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        actif: Optional[bool] = None
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None else {"actif": actif}
        
        cursor = db.categories_pro.find(filters, {"_id": 0}).sort([("nom", 1)])
        docs = await cursor.to_list(100)
        
        return [CategorieProOut(**doc) for doc in docs]
    
    @router.post("/categories-pro", response_model=CategorieProOut, status_code=201)
    async def create_categorie_pro(
        payload: CategorieProIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        existing = await db.categories_pro.find_one({"nom": payload.nom})
        _ensure(existing is None, 409, "Catégorie déjà existante")
        
        now = _now_iso()
        doc = {
            "categorie_pro_id": _generate_id("cat"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.categories_pro.insert_one(doc)
        return CategorieProOut(**doc)
    
    @router.patch("/categories-pro/{categorie_pro_id}", response_model=CategorieProOut)
    async def update_categorie_pro(
        categorie_pro_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.categories_pro.find_one({"categorie_pro_id": categorie_pro_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Catégorie introuvable")
        
        now = _now_iso()
        await db.categories_pro.update_one(
            {"categorie_pro_id": categorie_pro_id},
            {"$set": {**payload, "updated_at": now}}
        )
        
        updated = await db.categories_pro.find_one({"categorie_pro_id": categorie_pro_id}, {"_id": 0})
        return CategorieProOut(**updated)
    
    @router.delete("/categories-pro/{categorie_pro_id}")
    async def delete_categorie_pro(
        categorie_pro_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès refusé")
        
        doc = await db.categories_pro.find_one({"categorie_pro_id": categorie_pro_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Catégorie introuvable")
        
        now = _now_iso()
        await db.categories_pro.update_one(
            {"categorie_pro_id": categorie_pro_id},
            {"$set": {"actif": False, "updated_at": now}}
        )
        
        return {"message": "Catégorie désactivée avec succès"}
    
    # =========================================================================
    # CONTRATS
    # =========================================================================
    @router.get("/contrats", response_model=List[ContratOut])
    async def list_contrats(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        type_contrat: Optional[TypeContrat] = None,
        statut: Optional[StatutContrat] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if type_contrat:
            filters["type_contrat"] = type_contrat
        if statut:
            filters["statut"] = statut
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.contrats.find(filters, {"_id": 0})
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
        
        return [ContratOut(**doc) for doc in docs]
    
    @router.post("/contrats", response_model=ContratOut, status_code=201)
    async def create_contrat(
        payload: ContratIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        # Validation: date_fin obligatoire pour CDD
        if payload.type_contrat == "CDD" and not payload.date_fin:
            _ensure(False, 400, "Date fin obligatoire pour les contrats CDD")
        
        # Validation: date_fin doit être après date_debut
        if payload.date_fin:
            date_debut = datetime.fromisoformat(payload.date_debut)
            date_fin = datetime.fromisoformat(payload.date_fin)
            _ensure(date_fin > date_debut, 400, "Date fin doit être après date début")
        
        now = _now_iso()
        reference = await next_reference(db, "contrats", "FABS-CTR")
        
        # Calculate duration in days
        duree_jours = None
        if payload.date_fin:
            date_debut = datetime.fromisoformat(payload.date_debut)
            date_fin = datetime.fromisoformat(payload.date_fin)
            duree_jours = (date_fin - date_debut).days
        
        # Determine statut based on date_fin
        statut = "Actif"
        if payload.date_fin:
            date_fin = datetime.fromisoformat(payload.date_fin)
            if date_fin < datetime.now(timezone.utc):
                statut = "Expiré"
        
        doc = {
            "contrat_id": _generate_id("ctr"),
            "reference": reference,
            **payload.model_dump(),
            "statut": statut,
            "duree_jours": duree_jours,
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.contrats.insert_one(doc)
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CREATE",
            "resource_type": "contrat",
            "resource_id": doc["contrat_id"],
            "details": {"reference": reference, "employe_id": payload.employe_id},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        return ContratOut(**doc)
    
    @router.patch("/contrats/{contrat_id}", response_model=ContratOut)
    async def update_contrat(
        contrat_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.contrats.find_one({"contrat_id": contrat_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Contrat introuvable")
        
        now = _now_iso()
        await db.contrats.update_one(
            {"contrat_id": contrat_id},
            {"$set": {**payload, "updated_at": now}}
        )
        
        updated = await db.contrats.find_one({"contrat_id": contrat_id}, {"_id": 0})
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": updated["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            updated["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            updated["employe_matricule"] = emp.get("matricule")
        
        return ContratOut(**updated)
    
    @router.delete("/contrats/{contrat_id}")
    async def delete_contrat(
        contrat_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès refusé")
        
        doc = await db.contrats.find_one({"contrat_id": contrat_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Contrat introuvable")
        
        now = _now_iso()
        await db.contrats.update_one(
            {"contrat_id": contrat_id},
            {"$set": {"actif": False, "statut": "Resilie", "updated_at": now}}
        )
        
        return {"message": "Contrat désactivé avec succès"}
    
    # =========================================================================
    # CONGES
    # =========================================================================
    @router.get("/conges", response_model=List[CongeOut])
    async def list_conges(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        statut: Optional[StatutConge] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if statut:
            filters["statut"] = statut
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.conges.find(filters, {"_id": 0})
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
            
            # Enrich with approbateurs
            if doc.get("superieur_hierarchique_id"):
                sup = await db.employes.find_one(
                    {"employe_id": doc["superieur_hierarchique_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if sup:
                    doc["superieur_nom"] = f"{sup['nom']} {sup['prenoms']}"
            
            if doc.get("approbation_direction_id"):
                dir_emp = await db.employes.find_one(
                    {"employe_id": doc["approbation_direction_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if dir_emp:
                    doc["approbation_direction_nom"] = f"{dir_emp['nom']} {dir_emp['prenoms']}"
            
            if doc.get("approbation_rh_id"):
                rh_emp = await db.employes.find_one(
                    {"employe_id": doc["approbation_rh_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if rh_emp:
                    doc["approbation_rh_nom"] = f"{rh_emp['nom']} {rh_emp['prenoms']}"
        
        return [CongeOut(**doc) for doc in docs]
    
    @router.post("/conges", response_model=CongeOut, status_code=201)
    async def create_conge(
        payload: CongeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        # Validation: date_fin doit être après date_debut
        date_debut = datetime.fromisoformat(payload.date_debut)
        date_fin = datetime.fromisoformat(payload.date_fin)
        _ensure(date_fin > date_debut, 400, "Date fin doit être après date début")
        
        # Calculate nombre_jours automatically
        nombre_jours_calc = (date_fin - date_debut).days
        
        # Validate coherence with payload.nombre_jours if provided
        if payload.nombre_jours:
            _ensure(nombre_jours_calc == payload.nombre_jours, 400, f"Nombre de jours calculé ({nombre_jours_calc}) ne correspond pas à celui fourni ({payload.nombre_jours})")
        
        # Get supérieur hiérarchique
        superieur_id = employe.get("superieur_hierarchique_id")
        
        now = _now_iso()
        doc = {
            "conge_id": _generate_id("cng"),
            **payload.model_dump(),
            "nombre_jours": nombre_jours_calc,
            "statut": "en_attente",
            "superieur_hierarchique_id": superieur_id,
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.conges.insert_one(doc)
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CREATE",
            "resource_type": "conge",
            "resource_id": doc["conge_id"],
            "details": {"employe_id": payload.employe_id, "type_conge": payload.type_conge},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        return CongeOut(**doc)
    
    @router.post("/conges/{conge_id}/approuver-sup")
    async def approuver_conge_sup(
        conge_id: str,
        payload: ApprobationCongeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in APPROVE_ROLES, 403, "Accès refusé")
        
        doc = await db.conges.find_one({"conge_id": conge_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Congé introuvable")
        _ensure(doc["statut"] == "en_attente", 400, "Congé n'est pas en attente")
        
        now = _now_iso()
        await db.conges.update_one(
            {"conge_id": conge_id},
            {"$set": {
                "statut": "approuve_sup",
                "approbation_sup_date": now,
                "approbation_sup_commentaire": payload.commentaire,
                "updated_at": now
            }}
        )
        
        # Create notification
        await db.notifications.insert_one({
            "notification_id": _generate_id("notif"),
            "user_id": doc["employe_id"],
            "type": "success",
            "categorie": "rh",
            "titre": "Congé approuvé par supérieur",
            "message": f"Votre demande de congé a été approuvée par votre supérieur hiérarchique",
            "lue": False,
            "created_at": now,
        })
        
        return {"message": "Congé approuvé par supérieur"}
    
    @router.post("/conges/{conge_id}/approuver-direction")
    async def approuver_conge_direction(
        conge_id: str,
        payload: ApprobationCongeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in APPROVE_ROLES, 403, "Accès refusé")
        
        doc = await db.conges.find_one({"conge_id": conge_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Congé introuvable")
        _ensure(doc["statut"] == "approuve_sup", 400, "Congé doit être approuvé par supérieur d'abord")
        
        now = _now_iso()
        await db.conges.update_one(
            {"conge_id": conge_id},
            {"$set": {
                "statut": "approuve_direction",
                "approbation_direction_id": user["user_id"],
                "approbation_direction_date": now,
                "approbation_direction_commentaire": payload.commentaire,
                "updated_at": now
            }}
        )
        
        return {"message": "Congé approuvé par direction"}
    
    @router.post("/conges/{conge_id}/approuver-rh")
    async def approuver_conge_rh(
        conge_id: str,
        payload: ApprobationCongeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in APPROVE_ROLES, 403, "Accès refusé")
        
        doc = await db.conges.find_one({"conge_id": conge_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Congé introuvable")
        _ensure(doc["statut"] == "approuve_direction", 400, "Congé doit être approuvé par direction d'abord")
        
        now = _now_iso()
        await db.conges.update_one(
            {"conge_id": conge_id},
            {"$set": {
                "statut": "approuve_rh",
                "approbation_rh_id": user["user_id"],
                "approbation_rh_date": now,
                "approbation_rh_commentaire": payload.commentaire,
                "updated_at": now
            }}
        )
        
        # Update employe statut
        await db.employes.update_one(
            {"employe_id": doc["employe_id"]},
            {"$set": {"statut": "En conge", "updated_at": now}}
        )
        
        return {"message": "Congé approuvé par RH - Employé mis en congé"}
    
    # =========================================================================
    # ABSENCES
    # =========================================================================
    @router.get("/absences", response_model=List[AbsenceOut])
    async def list_absences(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        type_absence: Optional[TypeAbsence] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if type_absence:
            filters["type_absence"] = type_absence
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.absences.find(filters, {"_id": 0})
            .sort([("date", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
            
            if doc.get("enregistre_par_id"):
                reg = await db.employes.find_one(
                    {"employe_id": doc["enregistre_par_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if reg:
                    doc["enregistre_par_nom"] = f"{reg['nom']} {reg['prenoms']}"
        
        return [AbsenceOut(**doc) for doc in docs]
    
    @router.post("/absences", response_model=AbsenceOut, status_code=201)
    async def create_absence(
        payload: AbsenceIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        now = _now_iso()
        doc = {
            "absence_id": _generate_id("abs"),
            **payload.model_dump(),
            "enregistre_par_id": user["user_id"],
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.absences.insert_one(doc)
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        reg = await db.employes.find_one(
            {"employe_id": doc["enregistre_par_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1}
        )
        if reg:
            doc["enregistre_par_nom"] = f"{reg['nom']} {reg['prenoms']}"
        
        return AbsenceOut(**doc)
    
    # =========================================================================
    # MISSIONS
    # =========================================================================
    @router.get("/missions", response_model=List[MissionOut])
    async def list_missions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        statut: Optional[StatutMission] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if statut:
            filters["statut"] = statut
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.missions.find(filters, {"_id": 0})
            .sort([("date_depart", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
        
        return [MissionOut(**doc) for doc in docs]
    
    @router.post("/missions", response_model=MissionOut, status_code=201)
    async def create_mission(
        payload: MissionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        # Validation: date_retour doit être après date_depart
        date_depart = datetime.fromisoformat(payload.date_depart)
        date_retour = datetime.fromisoformat(payload.date_retour)
        _ensure(date_retour > date_depart, 400, "Date retour doit être après date départ")
        
        now = _now_iso()
        reference = await next_reference(db, "missions", "FABS-MIS")
        
        doc = {
            "mission_id": _generate_id("mis"),
            "reference": reference,
            **payload.model_dump(),
            "statut": "planifiee",
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.missions.insert_one(doc)
        
        # Log audit
        await db.audit_logs.insert_one({
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user['user_id'][:8]}",
            "user_id": user["user_id"],
            "action": "CREATE",
            "resource_type": "mission",
            "resource_id": doc["mission_id"],
            "details": {"reference": reference, "employe_id": payload.employe_id},
            "ip_address": request.client.host if request.client else None,
            "timestamp": now,
        })
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        return MissionOut(**doc)
    
    @router.post("/missions/{mission_id}/cloturer")
    async def cloturer_mission(
        mission_id: str,
        payload: dict,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        doc = await db.missions.find_one({"mission_id": mission_id}, {"_id": 0})
        _ensure(doc is not None, 404, "Mission introuvable")
        
        now = _now_iso()
        await db.missions.update_one(
            {"mission_id": mission_id},
            {"$set": {
                "statut": "terminee",
                "compte_rendu": payload.get("compte_rendu"),
                "updated_at": now
            }}
        )
        
        return {"message": "Mission clôturée avec succès"}
    
    # =========================================================================
    # HABILITATIONS ERP
    # =========================================================================
    @router.get("/habilitations", response_model=list[HabilitationOut])
    async def list_habilitations(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        actif: Optional[bool] = None
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if actif is not None:
            filters["actif"] = actif
        
        cursor = db.habilitations.find(filters, {"_id": 0}).sort([("created_at", -1)])
        docs = await cursor.to_list(100)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
        
        return [HabilitationOut(**doc) for doc in docs]
    
    @router.post("/habilitations", response_model=HabilitationOut, status_code=201)
    async def create_habilitation(
        payload: HabilitationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        now = _now_iso()
        doc = {
            "habilitation_id": _generate_id("hab"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.habilitations.insert_one(doc)
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        return HabilitationOut(**doc)
    
    # =========================================================================
    # EVALUATIONS
    # =========================================================================
    @router.get("/evaluations", response_model=List[EvaluationOut])
    async def list_evaluations(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        employe_id: Optional[str] = None,
        type_evaluation: Optional[TypeEvaluation] = None,
        statut: Optional[StatutEvaluation] = None,
        actif: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        if employe_id:
            filters["employe_id"] = employe_id
        if type_evaluation:
            filters["type_evaluation"] = type_evaluation
        if statut:
            filters["statut"] = statut
        if actif is not None:
            filters["actif"] = actif
        
        cursor = (
            db.evaluations.find(filters, {"_id": 0})
            .sort([("periode_fin", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(limit)
        
        # Enrich with employe
        for doc in docs:
            if doc.get("employe_id"):
                emp = await db.employes.find_one(
                    {"employe_id": doc["employe_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if emp:
                    doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
                    doc["employe_matricule"] = emp.get("matricule")
            
            if doc.get("evaluateur_id"):
                eval_emp = await db.employes.find_one(
                    {"employe_id": doc["evaluateur_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1}
                )
                if eval_emp:
                    doc["evaluateur_nom"] = f"{eval_emp['nom']} {eval_emp['prenoms']}"
        
        return [EvaluationOut(**doc) for doc in docs]
    
    @router.post("/evaluations", response_model=EvaluationOut, status_code=201)
    async def create_evaluation(
        payload: EvaluationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check employe exists
        employe = await db.employes.find_one({"employe_id": payload.employe_id})
        _ensure(employe is not None, 404, "Employé introuvable")
        
        # Check evaluateur exists
        evaluateur = await db.employes.find_one({"employe_id": payload.evaluateur_id})
        _ensure(evaluateur is not None, 404, "Évaluateur introuvable")
        
        now = _now_iso()
        doc = {
            "evaluation_id": _generate_id("eval"),
            **payload.model_dump(),
            "statut": "brouillon",
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.evaluations.insert_one(doc)
        
        # Enrich
        emp = await db.employes.find_one(
            {"employe_id": doc["employe_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if emp:
            doc["employe_nom"] = f"{emp['nom']} {emp['prenoms']}"
            doc["employe_matricule"] = emp.get("matricule")
        
        eval_emp = await db.employes.find_one(
            {"employe_id": doc["evaluateur_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1}
        )
        if eval_emp:
            doc["evaluateur_nom"] = f"{eval_emp['nom']} {eval_emp['prenoms']}"
        
        return EvaluationOut(**doc)
    
    # =========================================================================
    # DELEGATIONS
    # =========================================================================
    @router.get("/delegations", response_model=List[DelegationOut])
    async def list_delegations(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        actif: Optional[bool] = None
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        
        filters = {} if actif is None or actif else {}
        
        cursor = db.delegations.find(filters, {"_id": 0}).sort([("date_debut", -1)])
        docs = await cursor.to_list(100)
        
        # Enrich with employes
        for doc in docs:
            if doc.get("titulaire_id"):
                tit = await db.employes.find_one(
                    {"employe_id": doc["titulaire_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if tit:
                    doc["titulaire_nom"] = f"{tit['nom']} {tit['prenoms']}"
                    doc["titulaire_matricule"] = tit.get("matricule")
            
            if doc.get("remplacant_id"):
                rep = await db.employes.find_one(
                    {"employe_id": doc["remplacant_id"]},
                    {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
                )
                if rep:
                    doc["remplacant_nom"] = f"{rep['nom']} {rep['prenoms']}"
                    doc["remplacant_matricule"] = rep.get("matricule")
        
        return [DelegationOut(**doc) for doc in docs]
    
    @router.post("/delegations", response_model=DelegationOut, status_code=201)
    async def create_delegation(
        payload: DelegationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        
        # Check titulaire exists
        titulaire = await db.employes.find_one({"employe_id": payload.titulaire_id})
        _ensure(titulaire is not None, 404, "Titulaire introuvable")
        
        # Check remplaçant exists
        remplacant = await db.employes.find_one({"employe_id": payload.remplacant_id})
        _ensure(remplacant is not None, 404, "Remplaçant introuvable")
        
        now = _now_iso()
        doc = {
            "delegation_id": _generate_id("del"),
            **payload.model_dump(),
            "actif": True,
            "created_at": now,
            "updated_at": now,
        }
        
        await db.delegations.insert_one(doc)
        
        # Enrich
        tit = await db.employes.find_one(
            {"employe_id": doc["titulaire_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if tit:
            doc["titulaire_nom"] = f"{tit['nom']} {tit['prenoms']}"
            doc["titulaire_matricule"] = tit.get("matricule")
        
        rep = await db.employes.find_one(
            {"employe_id": doc["remplacant_id"]},
            {"_id": 0, "nom": 1, "prenoms": 1, "matricule": 1}
        )
        if rep:
            doc["remplacant_nom"] = f"{rep['nom']} {rep['prenoms']}"
            doc["remplacant_matricule"] = rep.get("matricule")
        
        return DelegationOut(**doc)
    
    return router


# ============================================================================
# SEED DATA
# ============================================================================
async def seed_rh_data(db: AsyncIOMotorDatabase):
    """Seed initial RH data"""
    logger.info("Seeding RH data...")
    
    now = _now_iso()
    
    # Create MongoDB indexes for performance
    logger.info("Creating MongoDB indexes...")
    
    # Indexes for employes collection
    await db.employes.create_index([("employe_id", 1)], unique=True)
    await db.employes.create_index([("matricule", 1)], unique=True)
    await db.employes.create_index([("numero_cni", 1)], unique=True, sparse=True)
    await db.employes.create_index([("numero_cnps", 1)], unique=True, sparse=True)
    await db.employes.create_index([("nom", 1)])
    await db.employes.create_index([("prenoms", 1)])
    await db.employes.create_index([("departement_id", 1)])
    await db.employes.create_index([("fonction_id", 1)])
    await db.employes.create_index([("categorie_pro_id", 1)])
    await db.employes.create_index([("statut", 1)])
    await db.employes.create_index([("actif", 1)])
    await db.employes.create_index([("created_at", -1)])
    
    # Indexes for contrats collection
    await db.contrats.create_index([("contrat_id", 1)], unique=True)
    await db.contrats.create_index([("employe_id", 1)])
    await db.contrats.create_index([("statut", 1)])
    await db.contrats.create_index([("date_fin", 1)])
    await db.contrats.create_index([("actif", 1)])
    
    # Indexes for conges collection
    await db.conges.create_index([("conge_id", 1)], unique=True)
    await db.conges.create_index([("employe_id", 1)])
    await db.conges.create_index([("statut", 1)])
    await db.conges.create_index([("date_debut", 1)])
    await db.conges.create_index([("date_fin", 1)])
    await db.conges.create_index([("actif", 1)])
    
    # Indexes for missions collection
    await db.missions.create_index([("mission_id", 1)], unique=True)
    await db.missions.create_index([("employe_id", 1)])
    await db.missions.create_index([("statut", 1)])
    await db.missions.create_index([("date_depart", -1)])
    await db.missions.create_index([("date_retour", 1)])
    await db.missions.create_index([("actif", 1)])
    
    # Indexes for other collections
    await db.departements.create_index([("departement_id", 1)], unique=True)
    await db.departements.create_index([("nom", 1)])
    await db.fonctions.create_index([("fonction_id", 1)], unique=True)
    await db.fonctions.create_index([("nom", 1)])
    await db.categories_pro.create_index([("categorie_pro_id", 1)], unique=True)
    await db.categories_pro.create_index([("nom", 1)])
    await db.absences.create_index([("absence_id", 1)], unique=True)
    await db.absences.create_index([("employe_id", 1)])
    await db.habilitations.create_index([("habilitation_id", 1)], unique=True)
    await db.habilitations.create_index([("employe_id", 1)])
    await db.evaluations.create_index([("evaluation_id", 1)], unique=True)
    await db.evaluations.create_index([("employe_id", 1)])
    await db.delegations.create_index([("delegation_id", 1)], unique=True)
    await db.delegations.create_index([("titulaire_id", 1)])
    
    logger.info("MongoDB indexes created successfully")
    
    # Seed Départements
    departements_data = [
        {"nom": "Direction Générale", "description": "Direction générale de l'entreprise"},
        {"nom": "Secrétariat & Administration", "description": "Secrétariat et administration"},
        {"nom": "Informatique", "description": "Service informatique"},
        {"nom": "Comptabilité", "description": "Service comptabilité"},
        {"nom": "Commercial", "description": "Service commercial"},
        {"nom": "Logistique", "description": "Service logistique"},
        {"nom": "Magasin & Stock", "description": "Magasin et gestion de stock"},
    ]
    
    for dept_data in departements_data:
        existing = await db.departments.find_one({"nom": dept_data["nom"]})
        if not existing:
            doc = {
                "departement_id": _generate_id("dep"),
                **dept_data,
                "actif": True,
                "created_at": now,
                "updated_at": now,
            }
            await db.departements.insert_one(doc)
            logger.info(f"Created department: {dept_data['nom']}")
    
    # Seed Fonctions
    fonctions_data = [
        {"nom": "Directeur Général", "description": "Directeur général"},
        {"nom": "Directeur Général Adjoint", "description": "Directeur général adjoint"},
        {"nom": "Responsable Informatique", "description": "Responsable du service informatique"},
        {"nom": "Comptable", "description": "Comptable"},
        {"nom": "Assistante Comptable", "description": "Assistante comptable"},
        {"nom": "Assistante de Direction", "description": "Assistante de direction"},
        {"nom": "Secrétaire", "description": "Secrétaire"},
        {"nom": "Assistante Administrative", "description": "Assistante administrative"},
        {"nom": "Commercial", "description": "Commercial"},
        {"nom": "Commerciale", "description": "Commerciale"},
        {"nom": "Responsable Logistique Commerciale", "description": "Responsable logistique commerciale"},
        {"nom": "Gestionnaire de Stock", "description": "Gestionnaire de stock"},
        {"nom": "Chef Magasinier", "description": "Chef magasinier"},
        {"nom": "Magasinier", "description": "Magasinier"},
        {"nom": "Livreur", "description": "Livreur"},
        {"nom": "Chauffeur-Livreur", "description": "Chauffeur-livreur"},
        {"nom": "Agent Logistique", "description": "Agent logistique"},
        {"nom": "Stagiaire", "description": "Stagiaire"},
        {"nom": "Consultant", "description": "Consultant"},
    ]
    
    for fonc_data in fonctions_data:
        existing = await db.fonctions.find_one({"nom": fonc_data["nom"]})
        if not existing:
            doc = {
                "fonction_id": _generate_id("fnc"),
                **fonc_data,
                "actif": True,
                "created_at": now,
                "updated_at": now,
            }
            await db.fonctions.insert_one(doc)
            logger.info(f"Created function: {fonc_data['nom']}")
    
    # Seed Catégories Professionnelles
    categories_data = [
        {"nom": "Direction", "description": "Direction"},
        {"nom": "Cadre Supérieur", "description": "Cadre supérieur"},
        {"nom": "Cadre", "description": "Cadre"},
        {"nom": "Agent de Maîtrise", "description": "Agent de maîtrise"},
        {"nom": "Employé", "description": "Employé"},
        {"nom": "Ouvrier", "description": "Ouvrier"},
        {"nom": "Stagiaire", "description": "Stagiaire"},
        {"nom": "Prestataire", "description": "Prestataire"},
    ]
    
    for cat_data in categories_data:
        existing = await db.categories_pro.find_one({"nom": cat_data["nom"]})
        if not existing:
            doc = {
                "categorie_pro_id": _generate_id("cat"),
                **cat_data,
                "actif": True,
                "created_at": now,
                "updated_at": now,
            }
            await db.categories_pro.insert_one(doc)
            logger.info(f"Created category: {cat_data['nom']}")
    
    logger.info("RH data seeding completed")
