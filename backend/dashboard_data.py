"""
Dashboard data — ERP FABS-CI V10.
KPIs calculés en temps réel depuis MongoDB (Motor async).
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from calendar import monthrange

# ---------------------------------------------------------------------------
# Mapping role -> ordered list of KPI keys (max 6)
# ---------------------------------------------------------------------------
ROLE_KPIS: Dict[str, List[str]] = {
    "super_admin":            ["ca_mois", "factures_impayees", "paiements_mois", "commandes_en_cours", "total_clients", "alertes_stock"],
    "directeur_general":      ["ca_mois", "factures_impayees", "paiements_mois", "commandes_en_cours", "total_clients", "alertes_stock"],
    "directeur_commercial":   ["ventes_mois", "top_clients_count", "commandes_en_cours", "total_clients", "factures_impayees", "alertes_stock"],
    "comptable":              ["ca_mois", "factures_impayees", "paiements_mois", "creances_total", "total_clients", "commandes_en_cours"],
    "gestionnaire_stock":     ["alertes_stock", "ruptures", "total_produits", "commandes_en_cours"],
    "responsable_magasinier": ["alertes_stock", "commandes_en_cours", "ruptures", "total_produits"],
    "secretariat":            ["commandes_en_cours", "total_clients", "factures_impayees"],
    "assistante":             ["total_clients", "commandes_en_cours", "commandes_attente"],
    "service_logistique":     ["commandes_en_cours", "total_clients", "alertes_stock"],
    "commercial":             ["ventes_mois", "top_clients_count", "commandes_en_cours", "factures_impayees"],
    "responsable_rh":         ["total_clients", "commandes_en_cours"],
}

ROLES_WITH_CHARTS   = {"super_admin", "directeur_general", "directeur_commercial"}
ROLES_WITH_PAYMENTS = {"super_admin", "directeur_general", "comptable"}
ROLES_WITH_TREASURY = {"super_admin", "directeur_general", "comptable"}

TREASURY_SEUIL_FCFA = 5_000_000


def _debut_fin_mois():
    today = date.today()
    debut = datetime(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    fin = datetime(today.year, today.month, last_day, 23, 59, 59)
    return debut, fin


async def _compute_kpi(key: str, db) -> dict:
    debut_mois, fin_mois = _debut_fin_mois()
    debut_str = debut_mois.strftime("%Y-%m-%d")
    fin_str = fin_mois.strftime("%Y-%m-%d")

    if key in ("ca_mois", "ventes_mois"):
        val = 0
        try:
            pipeline = [
                {"$match": {"statut": {"$in": ["payee", "partiellement_payee"]},
                            "date_emission": {"$gte": debut_str, "$lte": fin_str}}},
                {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
            ]
            res = await db.factures.aggregate(pipeline).to_list(length=1)
            val = int(res[0]["total"]) if res else 0
        except Exception:
            val = 0
        label = "Chiffre d'affaires du mois" if key == "ca_mois" else "Ventes du mois"
        return {"key": key, "label": label, "value": val,
                "suffix": "FCFA", "icon": "TrendingUp", "accent": "#2E7D32", "variation_pct": 0.0}

    elif key == "factures_impayees":
        val, montant = 0, 0
        try:
            pipeline = [
                {"$match": {"statut": {"$in": ["emise", "en_retard"]}}},
                {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$montant_ttc"}}}
            ]
            res = await db.factures.aggregate(pipeline).to_list(length=1)
            if res:
                val = int(res[0]["count"])
                montant = int(res[0]["total"])
        except Exception:
            pass
        return {"key": key, "label": "Factures impayées", "value": val,
                "suffix": "factures", "secondary_value": montant, "secondary_suffix": "FCFA",
                "icon": "AlertCircle", "accent": "#C62828", "variation_pct": 0.0}

    elif key == "paiements_mois":
        val = 0
        try:
            pipeline = [
                {"$match": {"date_paiement": {"$gte": debut_str, "$lte": fin_str}}},
                {"$group": {"_id": None, "total": {"$sum": "$montant_total"}}}
            ]
            res = await db.paiements.aggregate(pipeline).to_list(length=1)
            val = int(res[0]["total"]) if res else 0
        except Exception:
            val = 0
        return {"key": key, "label": "Paiements reçus ce mois", "value": val,
                "suffix": "FCFA", "icon": "CheckCircle", "accent": "#2E7D32", "variation_pct": 0.0}

    elif key == "commandes_en_cours":
        val = 0
        try:
            val = await db.commandes.count_documents({"statut": {"$in": ["en_attente", "validee", "en_cours"]}})
        except Exception:
            val = 0
        return {"key": key, "label": "Commandes en cours", "value": val,
                "suffix": "", "icon": "ShoppingCart", "accent": "#FF6200", "variation_pct": 0.0}

    elif key in ("total_clients", "top_clients_count"):
        val = 0
        try:
            val = await db.clients.count_documents({})
        except Exception:
            val = 0
        return {"key": key, "label": "Total clients", "value": val,
                "suffix": "", "icon": "Users", "accent": "#0A2540", "variation_pct": 0.0}

    elif key == "alertes_stock":
        val = 0
        try:
            pipeline = [
                {"$match": {"$expr": {"$lte": ["$stock_actuel", "$stock_minimum"]}}},
                {"$count": "total"}
            ]
            res = await db.produits.aggregate(pipeline).to_list(length=1)
            val = res[0]["total"] if res else 0
        except Exception:
            val = 0
        return {"key": key, "label": "Alertes stock", "value": val,
                "suffix": "produits", "icon": "Package", "accent": "#C62828", "variation_pct": 0.0}

    elif key == "ruptures":
        val = 0
        try:
            val = await db.produits.count_documents({"stock_actuel": 0})
        except Exception:
            val = 0
        return {"key": key, "label": "Produits en rupture", "value": val,
                "suffix": "", "icon": "AlertCircle", "accent": "#C62828", "variation_pct": 0.0}

    elif key == "total_produits":
        val = 0
        try:
            val = await db.produits.count_documents({})
        except Exception:
            val = 0
        return {"key": key, "label": "Total produits", "value": val,
                "suffix": "", "icon": "Package", "accent": "#0A2540", "variation_pct": 0.0}

    elif key == "creances_total":
        val = 0
        try:
            pipeline = [
                {"$match": {"statut": {"$in": ["emise", "en_retard"]}}},
                {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
            ]
            res = await db.factures.aggregate(pipeline).to_list(length=1)
            val = int(res[0]["total"]) if res else 0
        except Exception:
            val = 0
        return {"key": key, "label": "Créances clients (total)", "value": val,
                "suffix": "FCFA", "icon": "Wallet", "accent": "#C62828", "variation_pct": 0.0}

    elif key == "commandes_attente":
        val = 0
        try:
            val = await db.commandes.count_documents({"statut": "en_attente"})
        except Exception:
            val = 0
        return {"key": key, "label": "Commandes en attente", "value": val,
                "suffix": "", "icon": "Clock", "accent": "#F59E0B", "variation_pct": 0.0}

    else:
        return {"key": key, "label": key, "value": 0, "suffix": "",
                "icon": "Activity", "accent": "#0A2540", "variation_pct": 0.0}


async def _compute_charts(db) -> dict:
    charts: dict = {}
    try:
        from dateutil.relativedelta import relativedelta as rdelta
        today = date.today()
        ventes_12 = []
        for i in range(11, -1, -1):
            d = today - rdelta(months=i)
            debut = datetime(d.year, d.month, 1)
            _, last = monthrange(d.year, d.month)
            fin = datetime(d.year, d.month, last, 23, 59, 59)
            pipeline = [
                {"$match": {"statut": {"$in": ["payee", "partiellement_payee"]},
                            "date_emission": {"$gte": debut.strftime("%Y-%m-%d"), "$lte": fin.strftime("%Y-%m-%d")}}},
                {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
            ]
            res = await db.factures.aggregate(pipeline).to_list(length=1)
            ca = int(res[0]["total"]) if res else 0
            mois_label = d.strftime("%b %y").capitalize()
            ventes_12.append({"mois": mois_label, "ca": ca})
        charts["ventes_12_mois"] = ventes_12

        # Top clients par CA
        pipeline_top = [
            {"$group": {"_id": "$client_id", "ca": {"$sum": "$montant_ttc"}}},
            {"$sort": {"ca": -1}},
            {"$limit": 5},
            {"$lookup": {"from": "clients", "localField": "_id",
                         "foreignField": "client_id", "as": "client_info"}},
            {"$unwind": {"path": "$client_info", "preserveNullAndEmptyArrays": True}}
        ]
        res_top = await db.factures.aggregate(pipeline_top).to_list(length=5)
        charts["top_clients"] = [
            {"nom": r.get("client_info", {}).get("nom", "Inconnu"), "ca": int(r["ca"])}
            for r in res_top
        ]

        # Catégories
        charts["ventes_categorie"] = []
    except Exception:
        pass
    return charts


async def _compute_payments_chart(db) -> list:
    try:
        pipeline = [
            {"$group": {"_id": "$mode_paiement", "total": {"$sum": "$montant_total"}}},
            {"$sort": {"total": -1}}
        ]
        res = await db.paiements.aggregate(pipeline).to_list(length=10)
        colors = ["#0A2540", "#FF6200", "#C62828", "#2E7D32", "#9C27B0"]
        return [{"mode": r["_id"] or "Autre", "value": int(r["total"]), "color": colors[i % len(colors)]}
                for i, r in enumerate(res)]
    except Exception:
        return []


async def _compute_treasury(db) -> Optional[dict]:
    try:
        pipeline = [
            {"$match": {"statut": {"$in": ["emise", "en_retard"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$montant_ttc"}}}
        ]
        res = await db.factures.aggregate(pipeline).to_list(length=1)
        total_creances = int(res[0]["total"]) if res else 0

        factures_cursor = db.factures.find(
            {"statut": {"$in": ["emise", "en_retard"]}},
            {"facture_id": 1, "client_id": 1, "montant_ttc": 1, "date_emission": 1}
        ).sort("date_emission", 1).limit(7)

        today = datetime.now()
        factures_a_relancer = []
        async for f in factures_cursor:
            date_em_raw = f.get("date_emission")
            if date_em_raw:
                try:
                    if isinstance(date_em_raw, datetime):
                        date_em = date_em_raw
                    else:
                        date_em = datetime.strptime(str(date_em_raw)[:10], "%Y-%m-%d")
                    jours = max(0, (today - date_em).days)
                except Exception:
                    jours = 0
            else:
                jours = 0
            client = await db.clients.find_one({"client_id": f.get("client_id")}, {"nom": 1})
            client_nom = client["nom"] if client else f.get("client_id", "Inconnu")
            factures_a_relancer.append({
                "reference": f.get("facture_id", ""),
                "client": client_nom,
                "montant": int(f.get("montant_ttc", 0)),
                "jours_retard": jours
            })

        factures_a_relancer.sort(key=lambda x: x["jours_retard"], reverse=True)
        return {
            "seuil_fcfa": TREASURY_SEUIL_FCFA,
            "total_creances": total_creances,
            "depasse": total_creances >= TREASURY_SEUIL_FCFA,
            "factures_a_relancer": factures_a_relancer,
        }
    except Exception:
        return None


async def build_dashboard_payload(role: str, db=None) -> dict:
    """Construit le payload dashboard depuis les données réelles MongoDB (async)."""
    kpi_keys = ROLE_KPIS.get(role, ["commandes_en_cours", "total_clients"])
    kpis = []
    for k in kpi_keys:
        kpi = await _compute_kpi(k, db)
        kpis.append(kpi)

    charts: dict = {}
    if role in ROLES_WITH_CHARTS and db is not None:
        charts = await _compute_charts(db)
    if role in ROLES_WITH_PAYMENTS and db is not None:
        paiements_chart = await _compute_payments_chart(db)
        if paiements_chart:
            charts["paiements_mode"] = paiements_chart

    treasury = None
    if role in ROLES_WITH_TREASURY and db is not None:
        treasury = await _compute_treasury(db)

    return {
        "role": role,
        "kpis": kpis,
        "charts": charts,
        "treasury_alert": treasury,
        "is_demo_data": False,
    }
