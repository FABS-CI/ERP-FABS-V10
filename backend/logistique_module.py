"""
Module Logistique et Transport - Gestion des missions logistiques et livraisons
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger("fabsci.logistique")

# ============================================================================
# SCHEMAS
# ============================================================================

class EtapeItineraire(BaseModel):
    expedition_id: str
    ordre: int
    adresse: str
    statut: str = Field(pattern="^(en_attente|en_cours|livre|echec)$")

class MissionLogistiqueIn(BaseModel):
    expedition_ids: Optional[List[str]] = []
    chauffeur_id: Optional[str] = None
    vehicule_id: Optional[str] = None
    date_mission: str
    notes: Optional[str] = None

class MissionLogistiqueOut(BaseModel):
    mission_id: str
    reference: str
    expedition_ids: Optional[List[str]] = []
    chauffeur_id: Optional[str] = None
    vehicule_id: Optional[str] = None
    date_mission: str
    itineraire: List[dict]
    statut: str
    distance_totale_km: float
    cout_transport: float
    notes: Optional[str] = None
    created_at: str
    created_by: str
    updated_at: str

class VehiculeIn(BaseModel):
    reference: str
    type: str = Field(pattern="^(camion|fourgonnette|moto)$")
    immatriculation: str
    capacite_kg: float = Field(gt=0)
    capacite_m3: float = Field(ge=0)
    chauffeur_id: Optional[str] = None

class VehiculeOut(BaseModel):
    vehicule_id: str
    reference: str
    type: str
    immatriculation: str
    capacite_kg: float
    capacite_m3: float
    chauffeur_id: Optional[str] = None
    statut: str
    created_at: str

class SuiviLivraisonIn(BaseModel):
    statut: str = Field(pattern="^(en_transit|livre|retarde|annule)$")
    localisation: Optional[dict] = None
    preuve_livraison: Optional[dict] = None

class SuiviLivraisonOut(BaseModel):
    suivi_id: str
    expedition_id: str
    mission_id: Optional[str] = None
    statut: str
    localisation: Optional[dict] = None
    preuve_livraison: Optional[dict] = None
    updated_by: str
    updated_at: str

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

def _calculate_distance_km(adresses: List[str]) -> float:
    """Calcule la distance totale en km (simplifié - utiliser API réelle en production)"""
    # En production, utiliser Google Maps API ou OpenRouteService
    return len(adresses) * 15.0  # Estimation simplifiée

def _calculate_transport_cost(distance_km: float, vehicule_type: str) -> float:
    """Calcule le coût de transport (simplifié)"""
    base_cost = 5000
    per_km_cost = 100
    if vehicule_type == "camion":
        per_km_cost = 200
    elif vehicule_type == "fourgonnette":
        per_km_cost = 150
    return base_cost + (distance_km * per_km_cost)

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_logistique_router(db, resolve_user):
    router = APIRouter(prefix="/logistique", tags=["logistique"])

    # ============================================================================
    # MISSIONS LOGISTIQUES ENDPOINTS
    # ============================================================================

    @router.get("/missions", response_model=List[MissionLogistiqueOut])
    async def list_missions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[str] = None,
        chauffeur_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les missions logistiques"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut
        if chauffeur_id:
            filters["chauffeur_id"] = chauffeur_id

        cursor = db.missions_logistiques.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [MissionLogistiqueOut(**d) for d in docs]

    @router.get("/missions/{mission_id}", response_model=MissionLogistiqueOut)
    async def get_mission(
        mission_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les détails d'une mission"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        mission = await db.missions_logistiques.find_one({"mission_id": mission_id}, {"_id": 0})
        if not mission:
            raise HTTPException(status_code=404, detail="Mission introuvable")
        return MissionLogistiqueOut(**mission)

    @router.post("/missions", response_model=MissionLogistiqueOut, status_code=201)
    async def create_mission(
        payload: MissionLogistiqueIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer une nouvelle mission logistique"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Récupérer les adresses des expéditions (skip les IDs introuvables)
        adresses = []
        itineraire = []
        valid_expedition_ids = []
        for idx, exp_id in enumerate(payload.expedition_ids or []):
            exp = await db.expeditions.find_one({"expedition_id": exp_id})
            if not exp:
                logger.warning(f"Expédition {exp_id} introuvable, ignorée")
                continue
            adresse = exp["adresse_livraison"]["adresse"] + ", " + exp["adresse_livraison"]["ville"]
            adresses.append(adresse)
            itineraire.append({
                "expedition_id": exp_id,
                "ordre": len(valid_expedition_ids) + 1,
                "adresse": adresse,
                "statut": "en_attente"
            })
            valid_expedition_ids.append(exp_id)

        # Calculer distance et coût
        distance_km = _calculate_distance_km(adresses)
        
        # Récupérer le type de véhicule si spécifié
        vehicule_type = "fourgonnette"
        if payload.vehicule_id:
            veh = await db.vehicules.find_one({"vehicule_id": payload.vehicule_id})
            if veh:
                vehicule_type = veh["type"]
        
        cout_transport = _calculate_transport_cost(distance_km, vehicule_type)

        mission_id = f"mis_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        reference = _generate_reference("FABS-MIS")

        mission_doc = {
            "mission_id": mission_id,
            "reference": reference,
            "expedition_ids": valid_expedition_ids,
            "chauffeur_id": payload.chauffeur_id,
            "vehicule_id": payload.vehicule_id,
            "date_mission": payload.date_mission,
            "itineraire": itineraire,
            "statut": "planifie",
            "distance_totale_km": distance_km,
            "cout_transport": cout_transport,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.missions_logistiques.insert_one(mission_doc)

        # Mettre à jour les expéditions avec la mission
        for exp_id in valid_expedition_ids:
            await db.expeditions.update_one(
                {"expedition_id": exp_id},
                {"$set": {"mission_id": mission_id}}
            )

        logger.info(f"Mission logistique créée: {reference} par {user['email']}")
        return MissionLogistiqueOut(**mission_doc)

    @router.patch("/missions/{mission_id}/statut")
    async def update_mission_statut(
        mission_id: str,
        statut: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour le statut d'une mission"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        if statut not in ["planifie", "en_cours", "termine", "annule"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        existing = await db.missions_logistiques.find_one({"mission_id": mission_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Mission introuvable")

        await db.missions_logistiques.update_one(
            {"mission_id": mission_id},
            {"$set": {"statut": statut, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )

        logger.info(f"Statut mission {mission_id} mis à jour: {statut}")
        return {"message": f"Statut mis à jour: {statut}"}

    # ============================================================================
    # VEHICULES ENDPOINTS
    # ============================================================================

    @router.get("/vehicules", response_model=List[VehiculeOut])
    async def list_vehicules(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les véhicules"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if statut:
            filters["statut"] = statut

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
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        vehicule_id = f"veh_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        vehicule_doc = {
            "vehicule_id": vehicule_id,
            "reference": payload.reference,
            "type": payload.type,
            "immatriculation": payload.immatriculation,
            "capacite_kg": payload.capacite_kg,
            "capacite_m3": payload.capacite_m3,
            "chauffeur_id": payload.chauffeur_id,
            "statut": "disponible",
            "created_at": datetime.now(timezone.utc).isoformat()
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

        if statut not in ["disponible", "en_mission", "maintenance"]:
            raise HTTPException(status_code=400, detail="Statut invalide")

        await db.vehicules.update_one(
            {"vehicule_id": vehicule_id},
            {"$set": {"statut": statut}}
        )

        return {"message": f"Statut mis à jour: {statut}"}

    # ============================================================================
    # SUIVI LIVRAISONS ENDPOINTS
    # ============================================================================

    @router.get("/suivi", response_model=List[SuiviLivraisonOut])
    async def list_suivi(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        expedition_id: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister le suivi des livraisons"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if expedition_id:
            filters["expedition_id"] = expedition_id
        if statut:
            filters["statut"] = statut

        cursor = db.suivi_livraisons.find(filters, {"_id": 0}).sort("updated_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [SuiviLivraisonOut(**d) for d in docs]

    @router.get("/suivi/{expedition_id}", response_model=SuiviLivraisonOut)
    async def get_suivi_expedition(
        expedition_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer le suivi d'une expédition"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        suivi = await db.suivi_livraisons.find_one({"expedition_id": expedition_id}, {"_id": 0})
        if not suivi:
            raise HTTPException(status_code=404, detail="Suivi introuvable")
        return SuiviLivraisonOut(**suivi)

    @router.post("/suivi/{expedition_id}", response_model=SuiviLivraisonOut, status_code=201)
    async def create_or_update_suivi(
        expedition_id: str,
        payload: SuiviLivraisonIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer ou mettre à jour le suivi d'une expédition"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Vérifier que l'expédition existe
        exp = await db.expeditions.find_one({"expedition_id": expedition_id})
        if not exp:
            raise HTTPException(status_code=404, detail="Expédition introuvable")

        suivi_id = f"suivi_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        suivi_doc = {
            "suivi_id": suivi_id,
            "expedition_id": expedition_id,
            "mission_id": exp.get("mission_id"),
            "statut": payload.statut,
            "localisation": payload.localisation,
            "preuve_livraison": payload.preuve_livraison,
            "updated_by": user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Upsert
        existing = await db.suivi_livraisons.find_one({"expedition_id": expedition_id})
        if existing:
            await db.suivi_livraisons.update_one(
                {"expedition_id": expedition_id},
                {"$set": {k: v for k, v in suivi_doc.items() if k != "suivi_id"}}
            )
            suivi_doc["suivi_id"] = existing["suivi_id"]
        else:
            await db.suivi_livraisons.insert_one(suivi_doc)

        # Mettre à jour le statut de l'expédition
        await db.expeditions.update_one(
            {"expedition_id": expedition_id},
            {"$set": {"statut": payload.statut}}
        )

        logger.info(f"Suivi mis à jour pour expédition {expedition_id}: {payload.statut}")
        return SuiviLivraisonOut(**suivi_doc)

    return router
