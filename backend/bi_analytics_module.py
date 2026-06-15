"""
Module Business Intelligence & Analytics - KPI avancés et forecasting
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger("fabsci.bi_analytics")

# ============================================================================
# SCHEMAS
# ============================================================================

class KPIVentesOut(BaseModel):
    periode_debut: str
    periode_fin: str
    ventes_totales: float
    nombre_commandes: int
    panier_moyen: float
    top_produits: List[dict]
    top_clients: List[dict]
    tendance_ventes: str
    croissance: float

class KPILogistiqueOut(BaseModel):
    periode_debut: str
    periode_fin: str
    nombre_missions: int
    distance_totale: float
    cout_total: float
    rentabilite_moyenne: float
    top_vehicules: List[dict]
    top_chauffeurs: List[dict]

class KPIFinanceOut(BaseModel):
    periode_debut: str
    periode_fin: str
    revenus: float
    depenses: float
    benefice: float
    marge: float
    taux_marge: float
    factures_impayees: float
    cash_flow: float

class ForecastVentesOut(BaseModel):
    periode: str
    ventes_previsionnelles: float
    confiance: float
    facteurs: List[str]

class ForecastDepensesOut(BaseModel):
    periode: str
    depenses_previsionnelles: float
    confiance: float
    categories: dict

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "comptable", "directeur_general"]
WRITE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

async def _calculate_kpi_ventes(db, date_debut: str, date_fin: str) -> dict:
    """Calculer les KPI de ventes"""
    # Récupérer les commandes de la période
    cursor = db.commandes.find({
        "date_commande": {"$gte": date_debut, "$lte": date_fin}
    })
    commandes = await cursor.to_list(500)
    
    ventes_totales = sum(c.get("montant_total", 0) for c in commandes)
    nombre_commandes = len(commandes)
    panier_moyen = ventes_totales / nombre_commandes if nombre_commandes > 0 else 0
    
    # Top produits
    produits_counts = {}
    for cmd in commandes:
        for ligne in cmd.get("lignes", []):
            prod_id = ligne.get("produit_id")
            produits_counts[prod_id] = produits_counts.get(prod_id, 0) + ligne.get("quantite", 0)
    
    top_produits = [
        {"produit_id": k, "quantite": v}
        for k, v in sorted(produits_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Top clients
    clients_counts = {}
    for cmd in commandes:
        client_id = cmd.get("client_id")
        clients_counts[client_id] = clients_counts.get(client_id, 0) + cmd.get("montant_total", 0)

    top_clients = [
        {"client_id": k, "montant": v}
        for k, v in sorted(clients_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Tendance (comparaison avec période précédente)
    periode_precedente_debut = (datetime.fromisoformat(date_debut) - timedelta(days=30)).date().isoformat()
    periode_precedente_fin = date_debut
    
    cursor_prev = db.commandes.find({
        "date_commande": {"$gte": periode_precedente_debut, "$lte": periode_precedente_fin}
    })
    commandes_prev = await cursor_prev.to_list(500)
    ventes_precedentes = sum(c.get("montant_total", 0) for c in commandes_prev)
    
    croissance = ((ventes_totales - ventes_precedentes) / ventes_precedentes * 100) if ventes_precedentes > 0 else 0
    tendance = "hausse" if croissance > 0 else "baisse" if croissance < 0 else "stable"
    
    return {
        "periode_debut": date_debut,
        "periode_fin": date_fin,
        "ventes_totales": ventes_totales,
        "nombre_commandes": nombre_commandes,
        "panier_moyen": panier_moyen,
        "top_produits": top_produits,
        "top_clients": top_clients,
        "tendance_ventes": tendance,
        "croissance": croissance
    }

async def _calculate_kpi_logistique(db, date_debut: str, date_fin: str) -> dict:
    """Calculer les KPI logistiques"""
    # Récupérer les missions de la période
    cursor = db.missions_logistiques.find({
        "date_mission": {"$gte": date_debut, "$lte": date_fin}
    })
    missions = await cursor.to_list(200)
    
    nombre_missions = len(missions)
    distance_totale = sum(m.get("distance_totale_km", 0) for m in missions)
    
    # Récupérer les coûts
    cursor_couts = db.couts_missions.find({
        "created_at": {"$gte": date_debut, "$lte": date_fin}
    })
    couts = await cursor_couts.to_list(200)
    cout_total = sum(c.get("cout_total", 0) for c in couts)
    
    # Rentabilité moyenne
    rentabilites = []
    for mission in missions:
        # Calculer revenu et coût par mission
        revenu = 0
        for exp_id in mission.get("expedition_ids", []):
            exp = await db.expeditions.find_one({"expedition_id": exp_id})
            if exp:
                revenu += exp.get("montant", 0)
        
        cout_mission = 0
        cout_doc = await db.couts_missions.find_one({"mission_id": mission["mission_id"]})
        if cout_doc:
            cout_mission = cout_doc.get("cout_total", 0)
        
        if revenu > 0:
            rentabilites.append((revenu - cout_mission) / revenu * 100)
    
    rentabilite_moyenne = sum(rentabilites) / len(rentabilites) if rentabilites else 0
    
    # Top véhicules
    vehicules_counts = {}
    for mission in missions:
        veh_id = mission.get("vehicule_id")
        vehicules_counts[veh_id] = vehicules_counts.get(veh_id, 0) + 1
    
    top_vehicules = [
        {"vehicule_id": k, "nombre_missions": v}
        for k, v in sorted(vehicules_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Top chauffeurs
    chauffeurs_counts = {}
    for mission in missions:
        chauff_id = mission.get("chauffeur_id")
        chauffeurs_counts[chauff_id] = chauffeurs_counts.get(chauff_id, 0) + 1

    top_chauffeurs = [
        {"chauffeur_id": k, "nombre_missions": v}
        for k, v in sorted(chauffeurs_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    return {
        "periode_debut": date_debut,
        "periode_fin": date_fin,
        "nombre_missions": nombre_missions,
        "distance_totale": distance_totale,
        "cout_total": cout_total,
        "rentabilite_moyenne": rentabilite_moyenne,
        "top_vehicules": top_vehicules,
        "top_chauffeurs": top_chauffeurs
    }

async def _calculate_kpi_finance(db, date_debut: str, date_fin: str) -> dict:
    """Calculer les KPI financiers"""
    # Revenus (factures)
    cursor_factures = db.factures.find({
        "date_facture": {"$gte": date_debut, "$lte": date_fin}
    })
    factures = await cursor_factures.to_list(500)
    revenus = sum(f.get("montant_ttc", 0) for f in factures)
    
    # Dépenses (paiements sortants + coûts logistiques)
    cursor_paiements = db.paiements.find({
        "date_paiement": {"$gte": date_debut, "$lte": date_fin},
        "type": "sortant"
    })
    paiements = await cursor_paiements.to_list(500)
    depenses_paiements = sum(p.get("montant", 0) for p in paiements)
    
    cursor_couts = db.couts_missions.find({
        "created_at": {"$gte": date_debut, "$lte": date_fin}
    })
    couts = await cursor_couts.to_list(200)
    depenses_logistique = sum(c.get("cout_total", 0) for c in couts)
    
    depenses = depenses_paiements + depenses_logistique
    
    benefice = revenus - depenses
    marge = benefice
    taux_marge = (marge / revenus * 100) if revenus > 0 else 0
    
    # Factures impayées
    cursor_impayees = db.factures.find({
        "statut": "en_attente"
    })
    impayees = await cursor_impayees.to_list(500)
    factures_impayees = sum(f.get("montant_ttc", 0) for f in impayees)
    
    # Cash flow (entrées - sorties)
    cursor_entrees = db.paiements.find({
        "date_paiement": {"$gte": date_debut, "$lte": date_fin},
        "type": "entrant"
    })
    entrees = await cursor_entrees.to_list(500)
    entrees_total = sum(e.get("montant", 0) for e in entrees)
    
    cash_flow = entrees_total - depenses_paiements
    
    return {
        "periode_debut": date_debut,
        "periode_fin": date_fin,
        "revenus": revenus,
        "depenses": depenses,
        "benefice": benefice,
        "marge": marge,
        "taux_marge": taux_marge,
        "factures_impayees": factures_impayees,
        "cash_flow": cash_flow
    }

async def _forecast_ventes(db, mois: int) -> dict:
    """Prévision des ventes pour les N prochains mois"""
    # Simple forecasting basé sur la moyenne des 3 derniers mois
    today = datetime.now(timezone.utc).date()
    periode_debut = (today - timedelta(days=90)).isoformat()
    periode_fin = today.isoformat()
    
    kpi = await _calculate_kpi_ventes(db, periode_debut, periode_fin)
    ventes_mensuelles_moyennes = kpi["ventes_totales"] / 3
    
    # Ajustement pour saisonnalité (simplifié)
    ajustement = 1.0  # Peut être ajusté selon les saisons
    
    ventes_previsionnelles = ventes_mensuelles_moyennes * ajustement * mois
    
    return {
        "periode": f"{mois} mois",
        "ventes_previsionnelles": ventes_previsionnelles,
        "confiance": 0.75,  # 75% de confiance
        "facteurs": ["Historique 3 derniers mois", "Tendance actuelle"]
    }

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_bi_analytics_router(db, resolve_user):
    router = APIRouter(prefix="/bi-analytics", tags=["bi-analytics"])

    # ============================================================================
    # KPI VENTES
    # ============================================================================

    @router.get("/kpi/ventes", response_model=KPIVentesOut)
    async def get_kpi_ventes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Calculer les KPI de ventes"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        kpi = await _calculate_kpi_ventes(db, date_debut, date_fin)
        return KPIVentesOut(**kpi)

    # ============================================================================
    # KPI LOGISTIQUE
    # ============================================================================

    @router.get("/kpi/logistique", response_model=KPILogistiqueOut)
    async def get_kpi_logistique(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Calculer les KPI logistiques"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        kpi = await _calculate_kpi_logistique(db, date_debut, date_fin)
        return KPILogistiqueOut(**kpi)

    # ============================================================================
    # KPI FINANCE
    # ============================================================================

    @router.get("/kpi/finance", response_model=KPIFinanceOut)
    async def get_kpi_finance(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Calculer les KPI financiers"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        kpi = await _calculate_kpi_finance(db, date_debut, date_fin)
        return KPIFinanceOut(**kpi)

    # ============================================================================
    # DASHBOARD GLOBAL
    # ============================================================================

    @router.get("/dashboard")
    async def get_dashboard_global(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        jours: int = Query(30, ge=1, le=365)
    ):
        """Récupérer le dashboard global"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        today = datetime.now(timezone.utc).date().isoformat()
        date_debut = (datetime.now(timezone.utc) - timedelta(days=jours)).date().isoformat()
        
        # Calculer tous les KPI
        kpi_ventes = await _calculate_kpi_ventes(db, date_debut, today)
        kpi_logistique = await _calculate_kpi_logistique(db, date_debut, today)
        kpi_finance = await _calculate_kpi_finance(db, date_debut, today)
        
        return {
            "periode": {"debut": date_debut, "fin": today, "jours": jours},
            "ventes": kpi_ventes,
            "logistique": kpi_logistique,
            "finance": kpi_finance
        }

    # ============================================================================
    # FORECASTING
    # ============================================================================

    @router.get("/forecast/ventes", response_model=ForecastVentesOut)
    async def forecast_ventes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        mois: int = Query(3, ge=1, le=12)
    ):
        """Prévision des ventes"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        forecast = await _forecast_ventes(db, mois)
        return ForecastVentesOut(**forecast)

    @router.get("/forecast/depenses", response_model=ForecastDepensesOut)
    async def forecast_depenses(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        mois: int = Query(3, ge=1, le=12)
    ):
        """Prévision des dépenses"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Simple forecasting basé sur la moyenne des 3 derniers mois
        today = datetime.now(timezone.utc).date()
        periode_debut = (today - timedelta(days=90)).isoformat()
        periode_fin = today.isoformat()
        
        kpi = await _calculate_kpi_finance(db, periode_debut, periode_fin)
        depenses_mensuelles_moyennes = kpi["depenses"] / 3
        
        depenses_previsionnelles = depenses_mensuelles_moyennes * mois
        
        # Répartition par catégorie (simplifiée)
        categories = {
            "paiements": depenses_previsionnelles * 0.6,
            "logistique": depenses_previsionnelles * 0.3,
            "autres": depenses_previsionnelles * 0.1
        }
        
        return ForecastDepensesOut(
            periode=f"{mois} mois",
            depenses_previsionnelles=depenses_previsionnelles,
            confiance=0.70,
            categories=categories
        )

    # ============================================================================
    # ANALYSES AVANCÉES
    # ============================================================================

    @router.get("/analyse/rentabilite-client")
    async def analyse_rentabilite_client(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Analyser la rentabilité par client"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Récupérer les commandes par client
        cursor = db.commandes.find({
            "date_commande": {"$gte": date_debut, "$lte": date_fin}
        })
        commandes = await cursor.to_list(500)
        
        clients_data = {}
        for cmd in commandes:
            client_id = cmd.get("client_id")
            if client_id not in clients_data:
                clients_data[client_id] = {
                    "client_id": client_id,
                    "nombre_commandes": 0,
                    "montant_total": 0,
                    "depenses_logistiques": 0
                }
            clients_data[client_id]["nombre_commandes"] += 1
            clients_data[client_id]["montant_total"] += cmd.get("montant_total", 0)
        
        # Calculer la rentabilité pour chaque client
        result = []
        for client_id, data in clients_data.items():
            # Simplification: rentabilité = revenu - 10% (coûts estimés)
            rentabilite = data["montant_total"] * 0.9
            taux = (rentabilite / data["montant_total"] * 100) if data["montant_total"] > 0 else 0
            
            result.append({
                "client_id": client_id,
                "nombre_commandes": data["nombre_commandes"],
                "montant_total": data["montant_total"],
                "rentabilite": rentabilite,
                "taux_rentabilite": taux
            })
        
        # Trier par rentabilité
        result.sort(key=lambda x: x["rentabilite"], reverse=True)
        
        return result[:20]

    @router.get("/analyse/rentabilite-vehicule")
    async def analyse_rentabilite_vehicule(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        date_debut: str = Query(...),
        date_fin: str = Query(...)
    ):
        """Analyser la rentabilité par véhicule"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        # Calcul rentabilité véhicules depuis missions logistiques
        cursor = db.vehicules.find({}, {"_id": 0})
        vehicules = await cursor.to_list(100)

        result = []
        for veh in vehicules:
            veh_id = veh.get("vehicule_id")
            filters = {"vehicule_id": veh_id,
                       "date_mission": {"$gte": date_debut, "$lte": date_fin}}
            mis_cursor = db.missions_logistiques.find(filters, {"_id": 0})
            missions = await mis_cursor.to_list(200)
            nb = len(missions)
            distance = sum(m.get("distance_totale_km", 0) for m in missions)
            cout = sum(m.get("cout_transport", 0) for m in missions)
            result.append({
                "vehicule_id": veh_id,
                "immatriculation": veh.get("immatriculation", "—"),
                "nombre_missions": nb,
                "distance_totale_km": distance,
                "cout_total": cout
            })

        result.sort(key=lambda x: x["nombre_missions"], reverse=True)
        return result[:20]

    return router
