"""
Module Fleet Management - Gestion de la flotte automobile
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("fabsci.fleet")

# ============================================================================
# SCHEMAS
# ============================================================================

class VehiculeIn(BaseModel):
    reference: str
    marque: str
    modele: str
    annee: int = Field(ge=2000, le=2030)
    immatriculation: str
    type: str = Field(pattern="^(camion|fourgonnette|voiture|moto)$")
    capacite_kg: float = Field(gt=0)
    capacite_m3: float = Field(ge=0)
    kilometrage: float = Field(ge=0)
    statut: str = Field(pattern="^(disponible|en_mission|maintenance|hors_service)$")
    chauffeur_id: Optional[str] = None

class VehiculeOut(BaseModel):
    vehicule_id: str
    reference: str
    marque: Optional[str] = None
    modele: Optional[str] = None
    annee: Optional[int] = None
    immatriculation: str
    type: str
    capacite_kg: float
    capacite_m3: float
    kilometrage: Optional[float] = 0.0
    statut: str
    chauffeur_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

class AssuranceIn(BaseModel):
    vehicule_id: str
    compagnie: str
    numero_police: str
    type_assurance: str = Field(pattern="^(responsabilite_civile|tous_risques|commerciale)$")
    date_debut: str
    date_fin: str
    montant: float = Field(gt=0)
    documents: Optional[List[str]] = None

class AssuranceOut(BaseModel):
    assurance_id: str
    vehicule_id: str
    compagnie: str
    numero_police: str
    type_assurance: str
    date_debut: str
    date_fin: str
    montant: float
    documents: Optional[List[str]] = []
    statut: str
    created_at: str

class VisiteTechniqueIn(BaseModel):
    vehicule_id: str
    date_visite: str
    date_prochaine_visite: str
    resultat: str = Field(pattern="^(conforme|non_conforme|ajustements_requis)$")
    centre: str
    rapport: Optional[str] = None
    documents: Optional[List[str]] = None

class VisiteTechniqueOut(BaseModel):
    visite_id: str
    vehicule_id: str
    date_visite: str
    date_prochaine_visite: str
    resultat: str
    centre: str
    rapport: Optional[str] = None
    documents: Optional[List[str]] = []
    created_at: str

class MaintenanceIn(BaseModel):
    vehicule_id: str
    type: str = Field(pattern="^(preventive|corrective|urgence)$")
    description: str
    cout: float = Field(ge=0)
    date_debut: str
    date_fin: Optional[str] = None
    statut: str = Field(pattern="^(planifie|en_cours|termine)$")
    technicien: Optional[str] = None
    pieces: Optional[List[dict]] = None

class MaintenanceOut(BaseModel):
    maintenance_id: str
    vehicule_id: str
    type: str
    description: str
    cout: float
    date_debut: str
    date_fin: Optional[str] = None
    statut: str
    technicien: Optional[str] = None
    pieces: Optional[List[dict]] = []
    created_at: str

class AffectationVehiculeIn(BaseModel):
    vehicule_id: str
    chauffeur_id: str
    mission_id: Optional[str] = None
    date_debut: str
    date_fin: Optional[str] = None
    kilometrage_depart: float = Field(ge=0)
    notes: Optional[str] = None

class AffectationVehiculeOut(BaseModel):
    affectation_id: str
    vehicule_id: str
    chauffeur_id: str
    mission_id: Optional[str] = None
    date_debut: str
    date_fin: Optional[str] = None
    kilometrage_depart: float
    kilometrage_retour: Optional[float] = None
    notes: Optional[str] = None
    statut: str
    created_at: str
    created_by: str

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire", "service_logistique"]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire", "service_logistique"]
DELETE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _generate_reference(prefix: str) -> str:
    """Génère une référence unique"""
    year = datetime.now().strftime("%Y")
    return f"{prefix}-{year}-{datetime.now().strftime('%m%d%H%M%S')}"

async def _check_assurance_valide(db, vehicule_id: str) -> bool:
    """Vérifie si l'assurance est valide"""
    today = datetime.now(timezone.utc).date()
    assurance = await db.assurances.find_one({
        "vehicule_id": vehicule_id,
        "statut": "active",
        "date_fin": {"$gte": today.isoformat()}
    })
    return assurance is not None

async def _check_visite_technique_valide(db, vehicule_id: str) -> bool:
    """Vérifie si la visite technique est valide"""
    today = datetime.now(timezone.utc).date()
    visite = await db.visites_techniques.find_one({
        "vehicule_id": vehicule_id,
        "date_prochaine_visite": {"$gte": today.isoformat()}
    })
    return visite is not None

async def _check_vehicule_eligible_sortie(db, vehicule_id: str) -> dict:
    """Vérifie si un véhicule est éligible pour sortir"""
    vehicule = await db.vehicules.find_one({"vehicule_id": vehicule_id})
    if not vehicule:
        return {"eligible": False, "raison": "Véhicule introuvable"}
    
    if vehicule["statut"] != "disponible":
        return {"eligible": False, "raison": f"Véhicule non disponible (statut: {vehicule['statut']})"}
    
    if not await _check_assurance_valide(db, vehicule_id):
        return {"eligible": False, "raison": "Assurance expirée"}
    
    if not await _check_visite_technique_valide(db, vehicule_id):
        return {"eligible": False, "raison": "Visite technique expirée"}
    
    return {"eligible": True, "raison": "Véhicule éligible"}

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_fleet_router(db, resolve_user):
    router = APIRouter(prefix="/fleet", tags=["fleet"])

    # ============================================================================
    # VÉHICULES ENDPOINTS
    # ============================================================================

    @router.get("/vehicules", response_model=List[VehiculeOut])
    async def list_vehicules(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[str] = None,
        type_vehicule: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les véhicules"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut
        if type_vehicule:
            filters["type"] = type_vehicule

        cursor = db.vehicules.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [VehiculeOut(**d) for d in docs]

    @router.post("/vehicules", response_model=VehiculeOut, status_code=201)
    async def create_vehicule(
        payload: VehiculeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un nouveau véhicule"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        vehicule_id = f"veh_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        vehicule_doc = {
            "vehicule_id": vehicule_id,
            "reference": payload.reference,
            "marque": payload.marque,
            "modele": payload.modele,
            "annee": payload.annee,
            "immatriculation": payload.immatriculation,
            "type": payload.type,
            "capacite_kg": payload.capacite_kg,
            "capacite_m3": payload.capacite_m3,
            "kilometrage": payload.kilometrage,
            "statut": payload.statut,
            "chauffeur_id": payload.chauffeur_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.vehicules.insert_one(vehicule_doc)
        logger.info(f"Véhicule créé: {payload.reference} par {user['email']}")
        
        return VehiculeOut(**vehicule_doc)

    @router.patch("/vehicules/{vehicule_id}/statut")
    async def update_vehicule_statut(
        vehicule_id: str,
        statut: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour le statut d'un véhicule"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        if statut not in ["disponible", "en_mission", "maintenance", "hors_service"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        await db.vehicules.update_one(
            {"vehicule_id": vehicule_id},
            {"$set": {"statut": statut, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

        logger.info(f"Statut véhicule {vehicule_id} mis à jour: {statut}")
        return {"message": f"Statut mis à jour: {statut}"}

    @router.get("/vehicules/{vehicule_id}/eligibilite")
    async def check_vehicule_eligibilite(
        vehicule_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Vérifier l'éligibilité d'un véhicule pour sortie"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        check = await _check_vehicule_eligible_sortie(db, vehicule_id)
        return check

    # ============================================================================
    # ASSURANCES ENDPOINTS
    # ============================================================================

    @router.get("/assurances", response_model=List[AssuranceOut])
    async def list_assurances(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        vehicule_id: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les assurances"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if vehicule_id:
            filters["vehicule_id"] = vehicule_id
        if statut:
            filters["statut"] = statut

        cursor = db.assurances.find(filters, {"_id": 0}).sort("date_fin", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [AssuranceOut(**d) for d in docs]

    @router.post("/assurances", response_model=AssuranceOut, status_code=201)
    async def create_assurance(
        payload: AssuranceIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une assurance"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        assurance_id = f"ass_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        assurance_doc = {
            "assurance_id": assurance_id,
            "vehicule_id": payload.vehicule_id,
            "compagnie": payload.compagnie,
            "numero_police": payload.numero_police,
            "type_assurance": payload.type_assurance,
            "date_debut": payload.date_debut,
            "date_fin": payload.date_fin,
            "montant": payload.montant,
            "documents": payload.documents,
            "statut": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.assurances.insert_one(assurance_doc)
        logger.info(f"Assurance créée pour véhicule {payload.vehicule_id} par {user['email']}")
        
        return AssuranceOut(**assurance_doc)

    @router.get("/assurances/expirantes")
    async def list_assurances_expirantes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        jours: int = Query(30, ge=1, le=90)
    ):
        """Lister les assurances expirant dans les X jours"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        date_limite = (datetime.now(timezone.utc) + timedelta(days=jours)).date().isoformat()
        today = datetime.now(timezone.utc).date().isoformat()

        cursor = db.assurances.find({
            "statut": "active",
            "date_fin": {"$gte": today, "$lte": date_limite}
        }, {"_id": 0}).sort("date_fin", 1)
        
        docs = await cursor.to_list(50)
        return [AssuranceOut(**d) for d in docs]

    # ============================================================================
    # VISITES TECHNIQUES ENDPOINTS
    # ============================================================================

    @router.get("/visites-techniques", response_model=List[VisiteTechniqueOut])
    async def list_visites_techniques(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        vehicule_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les visites techniques"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if vehicule_id:
            filters["vehicule_id"] = vehicule_id

        cursor = db.visites_techniques.find(filters, {"_id": 0}).sort("date_visite", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [VisiteTechniqueOut(**d) for d in docs]

    @router.post("/visites-techniques", response_model=VisiteTechniqueOut, status_code=201)
    async def create_visite_technique(
        payload: VisiteTechniqueIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une visite technique"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        visite_id = f"vt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        visite_doc = {
            "visite_id": visite_id,
            "vehicule_id": payload.vehicule_id,
            "date_visite": payload.date_visite,
            "date_prochaine_visite": payload.date_prochaine_visite,
            "resultat": payload.resultat,
            "centre": payload.centre,
            "rapport": payload.rapport,
            "documents": payload.documents,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.visites_techniques.insert_one(visite_doc)
        logger.info(f"Visite technique créée pour véhicule {payload.vehicule_id} par {user['email']}")
        
        return VisiteTechniqueOut(**visite_doc)

    @router.get("/visites-techniques/expirantes")
    async def list_visites_expirantes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        jours: int = Query(30, ge=1, le=90)
    ):
        """Lister les visites techniques expirant dans les X jours"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        date_limite = (datetime.now(timezone.utc) + timedelta(days=jours)).date().isoformat()
        today = datetime.now(timezone.utc).date().isoformat()

        cursor = db.visites_techniques.find({
            "date_prochaine_visite": {"$gte": today, "$lte": date_limite}
        }, {"_id": 0}).sort("date_prochaine_visite", 1)
        
        docs = await cursor.to_list(50)
        return [VisiteTechniqueOut(**d) for d in docs]

    # ============================================================================
    # MAINTENANCE ENDPOINTS
    # ============================================================================

    @router.get("/maintenances", response_model=list[MaintenanceOut])
    async def list_maintenances(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        vehicule_id: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les maintenances"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if vehicule_id:
            filters["vehicule_id"] = vehicule_id
        if statut:
            filters["statut"] = statut

        cursor = db.maintenances.find(filters, {"_id": 0}).sort("date_debut", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [MaintenanceOut(**d) for d in docs]

    @router.post("/maintenances", response_model=MaintenanceOut, status_code=201)
    async def create_maintenance(
        payload: MaintenanceIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une maintenance"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        maintenance_id = f"mnt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        maintenance_doc = {
            "maintenance_id": maintenance_id,
            "vehicule_id": payload.vehicule_id,
            "type": payload.type,
            "description": payload.description,
            "cout": payload.cout,
            "date_debut": payload.date_debut,
            "date_fin": payload.date_fin,
            "statut": payload.statut,
            "technicien": payload.technicien,
            "pieces": payload.pieces,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.maintenances.insert_one(maintenance_doc)
        
        # Mettre le véhicule en maintenance si nécessaire
        if payload.statut == "en_cours":
            await db.vehicules.update_one(
                {"vehicule_id": payload.vehicule_id},
                {"$set": {"statut": "maintenance"}}
            )
        
        logger.info(f"Maintenance créée pour véhicule {payload.vehicule_id} par {user['email']}")
        
        return MaintenanceOut(**maintenance_doc)

    @router.patch("/maintenances/{maintenance_id}/statut")
    async def update_maintenance_statut(
        maintenance_id: str,
        statut: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour le statut d'une maintenance"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        if statut not in ["planifie", "en_cours", "termine"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        maintenance = await db.maintenances.find_one({"maintenance_id": maintenance_id})
        if not maintenance:
            raise HTTPException(status_code=404, detail="Maintenance introuvable")

        await db.maintenances.update_one(
            {"maintenance_id": maintenance_id},
            {"$set": {"statut": statut}}
        )

        # Libérer le véhicule si maintenance terminée
        if statut == "termine" and maintenance["statut"] == "en_cours":
            await db.vehicules.update_one(
                {"vehicule_id": maintenance["vehicule_id"]},
                {"$set": {"statut": "disponible"}}
            )

        return {"message": f"Statut mis à jour: {statut}"}

    # ============================================================================
    # AFFECTATIONS VÉHICULES ENDPOINTS
    # ============================================================================

    @router.get("/affectations", response_model=List[AffectationVehiculeOut])
    async def list_affectations(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        vehicule_id: Optional[str] = None,
        chauffeur_id: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les affectations de véhicules"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if vehicule_id:
            filters["vehicule_id"] = vehicule_id
        if chauffeur_id:
            filters["chauffeur_id"] = chauffeur_id
        if statut:
            filters["statut"] = statut

        cursor = db.affectations_vehicules.find(filters, {"_id": 0}).sort("date_debut", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [AffectationVehiculeOut(**d) for d in docs]

    @router.post("/affectations", response_model=AffectationVehiculeOut, status_code=201)
    async def create_affectation(
        payload: AffectationVehiculeIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une affectation de véhicule"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        # Vérifier l'éligibilité du véhicule
        eligibility = await _check_vehicule_eligible_sortie(db, payload.vehicule_id)
        if not eligibility["eligible"]:
            raise HTTPException(status_code=400, detail=eligibility["raison"])

        affectation_id = f"aff_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        affectation_doc = {
            "affectation_id": affectation_id,
            "vehicule_id": payload.vehicule_id,
            "chauffeur_id": payload.chauffeur_id,
            "mission_id": payload.mission_id,
            "date_debut": payload.date_debut,
            "date_fin": payload.date_fin,
            "kilometrage_depart": payload.kilometrage_depart,
            "kilometrage_retour": None,
            "notes": payload.notes,
            "statut": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.affectations_vehicules.insert_one(affectation_doc)
        
        # Mettre le véhicule en mission
        await db.vehicules.update_one(
            {"vehicule_id": payload.vehicule_id},
            {"$set": {"statut": "en_mission", "chauffeur_id": payload.chauffeur_id}}
        )

        logger.info(f"Affectation créée pour véhicule {payload.vehicule_id} par {user['email']}")
        
        return AffectationVehiculeOut(**affectation_doc)

    @router.patch("/affectations/{affectation_id}/retour")
    async def retour_affectation(
        affectation_id: str,
        kilometrage_retour: float,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Enregistrer le retour d'une affectation"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        affectation = await db.affectations_vehicules.find_one({"affectation_id": affectation_id})
        if not affectation:
            raise HTTPException(status_code=404, detail="Affectation introuvable")

        await db.affectations_vehicules.update_one(
            {"affectation_id": affectation_id},
            {
                "$set": {
                    "kilometrage_retour": kilometrage_retour,
                    "statut": "terminee",
                    "date_fin": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        # Libérer le véhicule et mettre à jour le kilométrage
        await db.vehicules.update_one(
            {"vehicule_id": affectation["vehicule_id"]},
            {
                "$set": {
                    "statut": "disponible",
                    "chauffeur_id": None,
                    "kilometrage": kilometrage_retour,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        logger.info(f"Retour affectation {affectation_id} enregistré par {user['email']}")
        return {"message": "Retour enregistré"}

    return router
