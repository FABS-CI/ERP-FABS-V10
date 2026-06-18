"""
analytics_service.py — Service centralisé d'analytics ERP FABS V10

Centralise les pipelines d'agrégation partagés entre
analytics_module.py et bi_analytics_module.py.

Usage:
    from analytics_service import (
        get_kpi_ventes_global,
        get_ventes_pipeline,
        get_top_clients,
        get_top_produits,
        get_evolution_mensuelle,
    )
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


# ── KPIs globaux ───────────────────────────────────────────────────────────────

async def get_kpi_ventes_global(
    db: AsyncIOMotorDatabase,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    exclure_annulees: bool = True,
) -> Dict[str, Any]:
    """Calcule les KPIs de ventes globaux depuis les factures.

    Returns:
        dict avec total_ventes, total_ttc, total_factures, total_remises,
              clients_actifs, quantite_totale
    """
    filters: Dict[str, Any] = {}
    if exclure_annulees:
        filters["statut"] = {"$ne": "annulee"}
    if date_debut:
        filters.setdefault("date_facture", {})["$gte"] = date_debut
    if date_fin:
        filters.setdefault("date_facture", {})["$lte"] = date_fin

    pipeline_total = [
        {"$match": filters},
        {"$group": {
            "_id": None,
            "total_ventes": {"$sum": "$montant_ht"},
            "total_factures": {"$sum": 1},
            "total_remises": {"$sum": "$remise_montant"},
            "total_ttc": {"$sum": "$montant_ttc"}
        }}
    ]
    total_result = await db.factures.aggregate(pipeline_total).to_list(1)
    totals = total_result[0] if total_result else {
        "total_ventes": 0, "total_factures": 0,
        "total_remises": 0, "total_ttc": 0
    }

    clients_actifs = await db.clients.count_documents({"actif": True})

    pipeline_qty = [
        {"$match": filters},
        {"$unwind": "$lignes"},
        {"$group": {"_id": None, "total_qty": {"$sum": "$lignes.quantite"}}}
    ]
    qty_result = await db.factures.aggregate(pipeline_qty).to_list(1)
    total_qty = qty_result[0]["total_qty"] if qty_result else 0

    return {
        "total_ventes": totals.get("total_ventes", 0),
        "total_ttc": totals.get("total_ttc", 0),
        "total_factures": totals.get("total_factures", 0),
        "total_remises": totals.get("total_remises", 0),
        "clients_actifs": clients_actifs,
        "quantite_totale": total_qty,
    }


# ── Pipeline facture_lignes générique ──────────────────────────────────────────

def get_ventes_pipeline(
    group_field: str,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    exclure_annulees: bool = True,
) -> List[Dict]:
    """Construit un pipeline d'agrégation sur facture_lignes avec lookup
    vers factures, produits et clients.

    Args:
        group_field: Champ de regroupement (ex: "$prod.matiere", "$cli.ville")
        date_debut: Filtre date ISO (inclus)
        date_fin: Filtre date ISO (inclus)
        exclure_annulees: Exclure les factures annulées

    Returns:
        Liste de stages MongoDB aggregation
    """
    fac_match: Dict[str, Any] = {}
    if exclure_annulees:
        fac_match["statut"] = {"$ne": "annulee"}
    if date_debut:
        fac_match.setdefault("date_facture", {})["$gte"] = date_debut
    if date_fin:
        fac_match.setdefault("date_facture", {})["$lte"] = date_fin

    fac_match_stage = {f"fac.{k}": v for k, v in fac_match.items()} if fac_match else {}

    pipeline = [
        {"$lookup": {
            "from": "factures",
            "localField": "facture_id",
            "foreignField": "facture_id",
            "as": "fac",
        }},
        {"$unwind": "$fac"},
    ]

    if fac_match_stage:
        pipeline.append({"$match": fac_match_stage})

    pipeline += [
        {"$lookup": {
            "from": "produits",
            "let": {"pid": "$produit_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$produit_id", "$$pid"]}}}
            ],
            "as": "prod",
        }},
        {"$unwind": {"path": "$prod", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "clients",
            "localField": "fac.client_id",
            "foreignField": "client_id",
            "as": "cli",
        }},
        {"$unwind": {"path": "$cli", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": group_field,
            "total_ventes": {"$sum": "$montant_ht"},
            "quantite": {"$sum": "$quantite"},
            "nb_lignes": {"$sum": 1},
        }},
        {"$sort": {"total_ventes": -1}},
    ]

    return pipeline


# ── Top clients ────────────────────────────────────────────────────────────────

async def get_top_clients(
    db: AsyncIOMotorDatabase,
    limit: int = 10,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
) -> List[Dict]:
    """Retourne les N meilleurs clients par CA HT.

    Returns:
        Liste de {client_id, client_nom, ville, total_ventes, nb_factures}
    """
    filters: Dict[str, Any] = {"statut": {"$ne": "annulee"}}
    if date_debut:
        filters.setdefault("date_facture", {})["$gte"] = date_debut
    if date_fin:
        filters.setdefault("date_facture", {})["$lte"] = date_fin

    pipeline = [
        {"$match": filters},
        {"$lookup": {
            "from": "clients",
            "localField": "client_id",
            "foreignField": "client_id",
            "as": "cli",
        }},
        {"$unwind": {"path": "$cli", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$client_id",
            "client_nom": {"$first": "$cli.nom"},
            "ville": {"$first": "$cli.ville"},
            "total_ventes": {"$sum": "$montant_ht"},
            "nb_factures": {"$sum": 1},
        }},
        {"$sort": {"total_ventes": -1}},
        {"$limit": limit},
    ]

    results = await db.factures.aggregate(pipeline).to_list(limit)
    return [
        {
            "client_id": r["_id"],
            "client_nom": r.get("client_nom", "Inconnu"),
            "ville": r.get("ville", ""),
            "total_ventes": r.get("total_ventes", 0),
            "nb_factures": r.get("nb_factures", 0),
        }
        for r in results
    ]


# ── Top produits ───────────────────────────────────────────────────────────────

async def get_top_produits(
    db: AsyncIOMotorDatabase,
    limit: int = 10,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
) -> List[Dict]:
    """Retourne les N produits les plus vendus (par quantité et par CA).

    Returns:
        Liste de {produit_id, titre, reference, quantite, total_ventes}
    """
    pipeline = get_ventes_pipeline("$produit_id", date_debut, date_fin)
    pipeline += [{"$limit": limit}]

    # Enrichir avec les infos produit
    results = await db.facture_lignes.aggregate(pipeline).to_list(limit)

    top = []
    for r in results:
        pid = r["_id"]
        if not pid:
            continue
        prod = await db.produits.find_one(
            {"produit_id": pid},
            {"_id": 0, "titre": 1, "reference": 1}
        )
        top.append({
            "produit_id": pid,
            "titre": prod.get("titre", "") if prod else "",
            "reference": prod.get("reference", "") if prod else "",
            "quantite": r.get("quantite", 0),
            "total_ventes": r.get("total_ventes", 0),
        })

    return top


# ── Évolution mensuelle ────────────────────────────────────────────────────────

async def get_evolution_mensuelle(
    db: AsyncIOMotorDatabase,
    annee: int,
    exclure_annulees: bool = True,
) -> List[Dict]:
    """Retourne l'évolution mensuelle du CA pour une année donnée.

    Returns:
        Liste de 12 dicts {mois, annee, total_ventes, nb_factures}
    """
    filters: Dict[str, Any] = {}
    if exclure_annulees:
        filters["statut"] = {"$ne": "annulee"}
    filters["date_facture"] = {
        "$gte": f"{annee}-01-01",
        "$lte": f"{annee}-12-31",
    }

    pipeline = [
        {"$match": filters},
        {"$group": {
            "_id": {"$substr": ["$date_facture", 5, 2]},  # mois MM
            "total_ventes": {"$sum": "$montant_ht"},
            "nb_factures": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]

    results = await db.factures.aggregate(pipeline).to_list(12)
    return [
        {
            "mois": int(r["_id"]),
            "annee": annee,
            "total_ventes": r.get("total_ventes", 0),
            "nb_factures": r.get("nb_factures", 0),
        }
        for r in results
    ]
