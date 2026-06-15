"""
Module Logistics Costs Management - Gestion des coûts logistiques et rentabilité transport
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger("fabsci.logistics_costs")

# ============================================================================
# SCHEMAS
# ============================================================================

class CoutMissionIn(BaseModel):
    mission_id: str
    cout_carburant: float = Field(ge=0)
    cout_chauffeur: float = Field(ge=0)
    cout_peage: float = Field(ge=0)
    cout_manutention: float = Field(ge=0)
    cout_gare: float = Field(ge=0)
    cout_chargement: float = Field(ge=0)
    cout_divers: float = Field(ge=0)
    notes: Optional[str] = None

class CoutMissionOut(BaseModel):
    cout_id: str
    mission_id: str
    cout_carburant: float
    cout_chauffeur: float
    cout_peage: float
    cout_manutention: float
    cout_gare: float
    cout_chargement: float
    cout_divers: float
    cout_total: float
    notes: Optional[str] = None
    created_at: str
    created_by: str

class RentabiliteTransportOut(BaseModel):
    mission_id: str
    vehicule_id: str
    distance_km: float
    revenu: float
    cout_total: float
    marge: float
    taux_rentabilite: float
    cout_par_km: float
    date_mission: str

class RapportCoutsOut(BaseModel):
    periode_debut: str
    periode_fin: str
    cout_total: float
    cout_moyen_par_mission: float
    nombre_missions: int
    cout_par_categorie: dict
    top_5_missions_couteuses: List[dict]

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire", "service_logistique", "comptable"]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire", "service_logistique"]
DELETE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _calculate_cout_total(cout_data: dict) -> float:
    """Calcule le coût total d'une mission"""
    return (
        cout_data.get("cout_carburant", 0) +
        cout_data.get("cout_chauffeur", 0) +
        cout_data.get("cout_peage", 0) +
        cout_data.get("cout_manutention", 0) +
        cout_data.get("cout_gare", 0) +
        cout_data.get("cout_chargement", 0) +
        cout_data.get("cout_divers", 0)
    )

async def _calculate_rentabilite_mission(db, mission_id: str) -> dict:
    """Calcule la rentabilité d'une mission"""
    mission = await db.missions_logistiques.find_one({"mission_id": mission_id})
    if not mission:
        return None
    
    # Récupérer les coûts
    couts = await db.couts_missions.find_one({"mission_id": mission_id})
    cout_total = _calculate_cout_total(couts) if couts else 0
    
    # Récupérer le revenu (basé sur les expéditions)
    revenu = 0
    for exp_id in mission.get("expedition_ids", []):
        exp = await db.expeditions.find_one({"expedition_id": exp_id})
        if exp:
            revenu += exp.get("montant", 0)
    
    distance_km = mission.get("distance_totale_km", 0)
    
    marge = revenu - cout_total
    taux_rentabilite = (marge / revenu * 100) if revenu > 0 else 0
    cout_par_km = (cout_total / distance_km) if distance_km > 0 else 0
    
    return {
        "mission_id": mission_id,
        "vehicule_id": mission.get("vehicule_id"),
        "distance_km": distance_km,
        "revenu": revenu,
        "cout_total": cout_total,
        "marge": marge,
        "taux_rentabilite": taux_rentabilite,
        "cout_par_km": cout_par_km,
        "date_mission": mission.get("date_mission")
    }

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_logistics_costs_router(db, resolve_user):
    router = APIRouter(prefix="/logistics-costs", tags=["logistics-costs"])

    # ============================================================================
    # COÛTS MISSIONS ENDPOINTS
    # ============================================================================

    @router.get("/couts", response_model=List[CoutMissionOut])
    async def list_couts_missions(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        mission_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les coûts des missions"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if mission_id:
            filters["mission_id"] = mission_id

        cursor = db.couts_missions.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [CoutMissionOut(**d) for d in docs]

    @router.post("/couts", response_model=CoutMissionOut, status_code=201)
    async def create_cout_mission(
        payload: CoutMissionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer les coûts d'une mission"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        # Vérifier que la mission existe
        mission = await db.missions_logistiques.find_one({"mission_id": payload.mission_id})
        if not mission:
            raise HTTPException(status_code=404, detail="Mission introuvable")

        cout_id = f"cout_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        cout_total = _calculate_cout_total(payload.dict())

        cout_doc = {
            "cout_id": cout_id,
            "mission_id": payload.mission_id,
            "cout_carburant": payload.cout_carburant,
            "cout_chauffeur": payload.cout_chauffeur,
            "cout_peage": payload.cout_peage,
            "cout_manutention": payload.cout_manutention,
            "cout_gare": payload.cout_gare,
            "cout_chargement": payload.cout_chargement,
            "cout_divers": payload.cout_divers,
            "cout_total": cout_total,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.couts_missions.insert_one(cout_doc)
        
        # Mettre à jour la mission avec le coût total
        await db.missions_logistiques.update_one(
            {"mission_id": payload.mission_id},
            {"$set": {"cout_transport": cout_total}}
        )

        logger.info(f"Coûts créés pour mission {payload.mission_id} par {user['email']}")
        return CoutMissionOut(**cout_doc)

    @router.put("/couts/{cout_id}", response_model=CoutMissionOut)
    async def update_cout_mission(
        cout_id: str,
        payload: CoutMissionIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour les coûts d'une mission"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        cout_total = _calculate_cout_total(payload.dict())

        update_data = {
            "mission_id": payload.mission_id,
            "cout_carburant": payload.cout_carburant,
            "cout_chauffeur": payload.cout_chauffeur,
            "cout_peage": payload.cout_peage,
            "cout_manutention": payload.cout_manutention,
            "cout_gare": payload.cout_gare,
            "cout_chargement": payload.cout_chargement,
            "cout_divers": payload.cout_divers,
            "cout_total": cout_total,
            "notes": payload.notes
        }

        await db.couts_missions.update_one({"cout_id": cout_id}, {"$set": update_data})
        
        # Mettre à jour la mission
        await db.missions_logistiques.update_one(
            {"mission_id": payload.mission_id},
            {"$set": {"cout_transport": cout_total}}
        )

        updated = await db.couts_missions.find_one({"cout_id": cout_id}, {"_id": 0})
        return CoutMissionOut(**updated)

    # ============================================================================
    # RENTABILITÉ ENDPOINTS
    # ============================================================================

    @router.get("/rentabilite/{mission_id}", response_model=RentabiliteTransportOut)
    async def get_rentabilite_mission(
        mission_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Calculer la rentabilité d'une mission"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        rentabilite = await _calculate_rentabilite_mission(db, mission_id)
        
        if not rentabilite:
            raise HTTPException(status_code=404, detail="Mission introuvable")
        
        return RentabiliteTransportOut(**rentabilite)

    @router.get("/rentabilite", response_model=List[RentabiliteTransportOut])
    async def list_rentabilite(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister la rentabilité des missions"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if date_debut:
            filters["date_mission"] = {"$gte": date_debut}
        if date_fin:
            if "date_mission" in filters:
                filters["date_mission"]["$lte"] = date_fin
            else:
                filters["date_mission"] = {"$lte": date_fin}

        cursor = db.missions_logistiques.find(filters, {"_id": 0}).sort("date_mission", -1).skip(skip).limit(limit)
        missions = await cursor.to_list(limit)
        
        rentabilites = []
        for mission in missions:
            rent = await _calculate_rentabilite_mission(db, mission["mission_id"])
            if rent:
                rentabilites.append(RentabiliteTransportOut(**rent))
        
        return rentabilites

    # ============================================================================
    # RAPPORTS ENDPOINTS
    # ============================================================================

    @router.get("/rapport", response_model=RapportCoutsOut)
    async def get_rapport_couts(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Générer un rapport des coûts logistiques"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Récupérer toutes les missions de la période
        cursor = db.couts_missions.find({
            "created_at": {"$gte": date_debut, "$lte": date_fin}
        }, {"_id": 0})
        
        couts = await cursor.to_list(500)
        
        if not couts:
            raise HTTPException(status_code=404, detail="Aucun coût trouvé pour cette période")

        cout_total = sum(c["cout_total"] for c in couts)
        nombre_missions = len(couts)
        cout_moyen_par_mission = cout_total / nombre_missions if nombre_missions > 0 else 0

        # Coûts par catégorie
        cout_par_categorie = {
            "carburant": sum(c["cout_carburant"] for c in couts),
            "chauffeur": sum(c["cout_chauffeur"] for c in couts),
            "peage": sum(c["cout_peage"] for c in couts),
            "manutention": sum(c["cout_manutention"] for c in couts),
            "gare": sum(c["cout_gare"] for c in couts),
            "chargement": sum(c["cout_chargement"] for c in couts),
            "divers": sum(c["cout_divers"] for c in couts)
        }

        # Top 5 missions les plus coûteuses
        top_5 = sorted(couts, key=lambda x: x["cout_total"], reverse=True)[:5]

        return RapportCoutsOut(
            periode_debut=date_debut,
            periode_fin=date_fin,
            cout_total=cout_total,
            cout_moyen_par_mission=cout_moyen_par_mission,
            nombre_missions=nombre_missions,
            cout_par_categorie=cout_par_categorie,
            top_5_missions_couteuses=top_5
        )

    @router.get("/vehicules/rentabilite")
    async def get_rentabilite_par_vehicule(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: Optional[str] = None,
        date_fin: Optional[str] = None
    ):
        """Calculer la rentabilité par véhicule"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Récupérer tous les véhicules
        cursor = db.vehicules.find({}, {"_id": 0})
        vehicules = await cursor.to_list(100)
        
        result = []
        for vehicule in vehicules:
            # Récupérer les missions du véhicule
            filters = {"vehicule_id": vehicule["vehicule_id"]}
            if date_debut:
                filters["date_mission"] = {"$gte": date_debut}
            if date_fin:
                if "date_mission" in filters:
                    filters["date_mission"]["$lte"] = date_fin
                else:
                    filters["date_mission"] = {"$lte": date_fin}
            
            missions_cursor = db.missions_logistiques.find(filters, {"_id": 0})
            missions = await missions_cursor.to_list(100)
            
            total_revenu = 0
            total_cout = 0
            total_distance = 0
            
            for mission in missions:
                rent = await _calculate_rentabilite_mission(db, mission["mission_id"])
                if rent:
                    total_revenu += rent["revenu"]
                    total_cout += rent["cout_total"]
                    total_distance += rent["distance_km"]
            
            if total_distance > 0:
                marge = total_revenu - total_cout
                taux = (marge / total_revenu * 100) if total_revenu > 0 else 0
                
                result.append({
                    "vehicule_id": vehicule["vehicule_id"],
                    "reference": vehicule["reference"],
                    "immatriculation": vehicule["immatriculation"],
                    "nombre_missions": len(missions),
                    "total_revenu": total_revenu,
                    "total_cout": total_cout,
                    "marge": marge,
                    "taux_rentabilite": taux,
                    "cout_par_km": total_cout / total_distance
                })
        
        # Trier par taux de rentabilité
        result.sort(key=lambda x: x["taux_rentabilite"], reverse=True)
        
        return result

    return router
