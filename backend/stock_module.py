"""
Module Stock & Logistique — Sprint 10
- Suivi des mouvements de stock (entrées/sorties)
- Ajustements d'inventaire physique (complet/partiel/tournant)
- Dashboard logistique
- Inventaire global / par matière / par niveau / par cycle
- Gestion des dépôts & transferts
- Alertes logistiques (rupture/faible/surstock/inactif)
- Statistiques éditoriales (top ventes / produits dormants)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal, Optional, List
import uuid
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger("fabsci.stock")

READ_ROLES  = {"super_admin", "directeur_general", "gestionnaire_stock", "responsable_magasinier", "service_logistique"}
WRITE_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock"}

TypeMouvement = Literal["entree", "sortie", "ajustement", "retour", "specimen_gratuit", "inventaire", "transfert"]
TypeInventaire = Literal["complet", "partiel", "tournant"]


# ──────────────────────────────────────────────
# Helpers classification
# ──────────────────────────────────────────────

def _deduire_matiere(titre: str) -> str:
    """Déduit la matière scolaire depuis le titre du produit."""
    t = titre.upper()
    if re.search(r"FLUTE|MUSIQUE|MUSICAL(E)?|ÉDUCATION MUSICALE|EDUCATION MUSICALE", t):
        return "Éducation Musicale"
    if re.search(r"ARTS PLASTIQUES|ART PLASTIQUE", t):
        return "Arts Plastiques"
    if re.search(r"SVT", t):
        return "SVT"
    if re.search(r"PHYSIQUE.CHIMIE|PHYSIQUE CHIMIE", t):
        return "Physique-Chimie"
    if re.search(r"HISTOIRE.GÉOGRAPHIE|HISTOIRE.GEOGRAPHIE|HISTOIRE GÉO|HISTOIRE GEO", t):
        return "Histoire-Géographie"
    if re.search(r"PHILOSOPHIE|PHILO", t):
        return "Philosophie"
    if re.search(r"MATH[ÉE]MATIQUE|MATHS", t):
        return "Mathématiques"
    if re.search(r"PRÉLECTURE|PRELECTURE|ÉCRITURE|ECRITURE|FRANÇAIS|FRANCAIS", t):
        return "Français"
    if re.search(r"SACERDOCE", t):
        return "Éducation Civique"
    return "Autre"


def _deduire_cycle(categorie: str) -> str:
    """Déduit le cycle depuis la catégorie."""
    c = (categorie or "").strip().lower()
    if c in ("maternelle", "primaire"):
        return "Primaire"
    if c == "premier cycle":
        return "Collège"
    if c == "second cycle":
        return "Lycée"
    if c == "livre commun":
        return "Tous cycles"
    return "Autre"


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class MouvementStockIn(BaseModel):
    produit_id: str
    type_mouvement: TypeMouvement
    quantite: int = Field(..., gt=0)
    commande_id: Optional[str] = None
    bl_id: Optional[str] = None
    motif: Optional[str] = Field(default=None, max_length=500)


class MouvementStockOut(BaseModel):
    mouvement_id: str
    produit_id: str
    produit_reference: Optional[str] = None
    produit_titre: Optional[str] = None
    type_mouvement: TypeMouvement
    quantite: int
    stock_avant: int
    stock_apres: int
    commande_id: Optional[str] = None
    bl_id: Optional[str] = None
    motif: Optional[str] = None
    created_by: str
    created_at: str


class LigneInventaireIn(BaseModel):
    produit_id: str
    quantite_comptee: int = Field(..., ge=0)


class InventaireIn(BaseModel):
    date_inventaire: str
    type_inventaire: TypeInventaire = "complet"
    depot: Optional[str] = "principal"
    responsable: Optional[str] = None
    lignes: List[LigneInventaireIn] = Field(..., min_length=1)
    notes: Optional[str] = Field(default=None, max_length=500)


class LigneInventaireOut(BaseModel):
    ligne_id: str
    produit_id: str
    produit_reference: Optional[str] = None
    produit_titre: Optional[str] = None
    quantite_theorique: int
    quantite_comptee: int
    ecart: int
    regularisee: bool


class InventaireOut(BaseModel):
    inventaire_id: str
    reference: str
    date_inventaire: str
    type_inventaire: str = "complet"
    depot: Optional[str] = "principal"
    responsable: Optional[str] = None
    statut: str
    lignes: List[LigneInventaireOut]
    total_ecart: int
    notes: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: str


class DepotIn(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    adresse: Optional[str] = None
    responsable: Optional[str] = None
    description: Optional[str] = None


class TransfertIn(BaseModel):
    produit_id: str
    depot_source: str
    depot_destination: str
    quantite: int = Field(..., gt=0)
    motif: Optional[str] = None


# ──────────────────────────────────────────────
# Router Builder
# ──────────────────────────────────────────────

def build_stock_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/stock", tags=["stock"])

    # ══════════════════════════════════════
    # STOCK GLOBAL SUMMARY
    # ══════════════════════════════════════
    @router.get("", response_model=dict)
    async def get_stock_summary(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Global stock summary: total articles, stock, value, today's movements"""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")
        
        # Total articles in catalogue
        total_articles = await db.produits.count_documents({"actif": True})
        
        # Total stock quantity and value
        stock_pipeline = [
            {"$match": {"actif": True}},
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": {"$ifNull": ["$stock_actuel", 0]}},
                "total_value": {"$sum": {"$multiply": [
                    {"$ifNull": ["$stock_actuel", 0]},
                    {"$ifNull": ["$prix_vente", 0]},
                ]}},
            }}
        ]
        stock_result = await db.produits.aggregate(stock_pipeline).to_list(1)
        stock_data = stock_result[0] if stock_result else {"total_qty": 0, "total_value": 0}
        
        # Today's movements
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_movements = await db.mouvements_stock.count_documents({"created_at": {"$regex": f"^{today}"}})
        
        return {
            "total_articles": total_articles,
            "stock_quantity": stock_data.get("total_qty", 0),
            "stock_value": round(stock_data.get("total_value", 0), 2),
            "movements_today": today_movements,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ══════════════════════════════════════
    # MOUVEMENTS DE STOCK
    # ══════════════════════════════════════

    @router.get("/mouvements", response_model=List[MouvementStockOut])
    async def list_mouvements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        produit_id: Optional[str] = None,
        type_mouvement: Optional[str] = None,
        limit: int = Query(50, ge=1, le=200),
        skip: int = Query(0, ge=0),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if produit_id:
            filters["produit_id"] = produit_id
        if type_mouvement:
            filters["type_mouvement"] = type_mouvement

        cursor = db.mouvements_stock.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)

        for doc in docs:
            prod = await db.produits.find_one(
                {"produit_id": doc["produit_id"]},
                {"_id": 0, "reference": 1, "titre": 1}
            )
            if prod:
                doc["produit_reference"] = prod.get("reference")
                doc["produit_titre"] = prod.get("titre")

        return [MouvementStockOut(**d) for d in docs]

    @router.post("/mouvements", response_model=MouvementStockOut, status_code=201)
    async def create_mouvement(
        payload: MouvementStockIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        produit = await db.produits.find_one({"produit_id": payload.produit_id}, {"_id": 0})
        _ensure(produit is not None, 404, "Produit introuvable")

        stock_avant = produit.get("stock_actuel", 0)
        if payload.type_mouvement in ("entree", "retour"):
            stock_apres = stock_avant + payload.quantite
        else:
            stock_apres = max(0, stock_avant - payload.quantite)

        await db.produits.update_one(
            {"produit_id": payload.produit_id},
            {"$set": {"stock_actuel": stock_apres, "updated_at": _now_iso()}}
        )

        mouvement_id = f"mvt_{uuid.uuid4().hex[:12]}"
        now = _now_iso()
        mouvement_doc = {
            "mouvement_id": mouvement_id,
            "produit_id": payload.produit_id,
            "type_mouvement": payload.type_mouvement,
            "quantite": payload.quantite,
            "stock_avant": stock_avant,
            "stock_apres": stock_apres,
            "commande_id": payload.commande_id,
            "bl_id": payload.bl_id,
            "motif": payload.motif,
            "created_by": me["user_id"],
            "created_at": now,
        }
        await db.mouvements_stock.insert_one(mouvement_doc)

        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_STOCK_MOVEMENT",
                resource_type="stock_movement",
                resource_id=mouvement_id,
                details={
                    "produit_id": payload.produit_id,
                    "type_mouvement": payload.type_mouvement,
                    "quantite": payload.quantite,
                    "stock_avant": stock_avant,
                    "stock_apres": stock_apres,
                },
                ip_address=request.client.host if request.client else None
            )

        mouvement_doc["produit_reference"] = produit.get("reference")
        mouvement_doc["produit_titre"] = produit.get("titre")
        return MouvementStockOut(**mouvement_doc)

    # ══════════════════════════════════════
    # DASHBOARD LOGISTIQUE
    # ══════════════════════════════════════

    @router.get("/dashboard-logistique")
    async def dashboard_logistique(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Tableau de bord logistique global."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        total_references = len(produits)
        total_quantite = sum(p.get("stock_actuel", 0) for p in produits)
        valeur_stock = sum(
            p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0))
            for p in produits
        )

        ruptures = []
        alertes_faibles = []
        surstocks = []
        inactifs = []

        for p in produits:
            s = p.get("stock_actuel", 0)
            seuil = p.get("seuil_alerte", 20)
            # rupture = stock = 0
            if s == 0:
                ruptures.append(p.get("produit_id"))
            # faible = 0 < stock <= seuil
            elif s <= seuil:
                alertes_faibles.append(p.get("produit_id"))
            # surstock = stock > 5x seuil (heuristique)
            elif s > seuil * 5 and seuil > 0:
                surstocks.append(p.get("produit_id"))

        # Mouvements récents (30 derniers jours)
        from datetime import timedelta
        date_limite = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        mouvements_recents = await db.mouvements_stock.count_documents({"created_at": {"$gte": date_limite}})
        entrees_recentes = await db.mouvements_stock.count_documents(
            {"created_at": {"$gte": date_limite}, "type_mouvement": "entree"}
        )
        sorties_recentes = await db.mouvements_stock.count_documents(
            {"created_at": {"$gte": date_limite}, "type_mouvement": {"$in": ["sortie", "specimen_gratuit"]}}
        )

        # Produits inactifs (aucun mouvement en 90j)
        date_90j = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        ids_actifs = set()
        async for m in db.mouvements_stock.find({"created_at": {"$gte": date_90j}}, {"produit_id": 1, "_id": 0}):
            ids_actifs.add(m["produit_id"])
        inactifs = [p.get("produit_id") for p in produits if p.get("produit_id") not in ids_actifs]

        # Inventaires en cours
        inventaires_ouverts = await db.inventaires.count_documents({"statut": "brouillon"})

        # Dépôts
        depots_count = await db.depots.count_documents({})

        return {
            "resume": {
                "total_references": total_references,
                "total_quantite": total_quantite,
                "valeur_stock_fcfa": valeur_stock,
                "nb_ruptures": len(ruptures),
                "nb_alertes_faibles": len(alertes_faibles),
                "nb_surstocks": len(surstocks),
                "nb_inactifs": len(inactifs),
                "inventaires_en_cours": inventaires_ouverts,
                "nb_depots": max(depots_count, 1),
            },
            "activite_30j": {
                "total_mouvements": mouvements_recents,
                "entrees": entrees_recentes,
                "sorties": sorties_recentes,
            },
            "ids_ruptures": ruptures[:10],
            "ids_alertes": alertes_faibles[:10],
        }

    # ══════════════════════════════════════
    # INVENTAIRE GLOBAL
    # ══════════════════════════════════════

    @router.get("/inventaire-global")
    async def inventaire_global(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Vue globale du stock : totaux, valeur, répartition par catégorie."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        total_references = len(produits)
        total_quantite   = sum(p.get("stock_actuel", 0) for p in produits)
        valeur_totale    = sum(
            p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0))
            for p in produits
        )
        valeur_vente     = sum(
            p.get("stock_actuel", 0) * p.get("prix_vente", 0)
            for p in produits
        )

        # Répartition par catégorie
        par_categorie: dict = {}
        for p in produits:
            cat = p.get("categorie", "Autre")
            if cat not in par_categorie:
                par_categorie[cat] = {"categorie": cat, "nb_references": 0, "quantite_totale": 0, "valeur_fcfa": 0}
            par_categorie[cat]["nb_references"] += 1
            par_categorie[cat]["quantite_totale"] += p.get("stock_actuel", 0)
            par_categorie[cat]["valeur_fcfa"] += p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0))

        return {
            "totaux": {
                "nb_references": total_references,
                "quantite_totale": total_quantite,
                "valeur_achat_fcfa": valeur_totale,
                "valeur_vente_fcfa": valeur_vente,
                "marge_potentielle_fcfa": valeur_vente - valeur_totale,
            },
            "par_categorie": list(par_categorie.values()),
        }

    # ══════════════════════════════════════
    # INVENTAIRE PAR MATIÈRE
    # ══════════════════════════════════════

    @router.get("/inventaire-par-matiere")
    async def inventaire_par_matiere(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Agrégation stock par matière scolaire (déduite du titre)."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        par_matiere: dict = {}
        for p in produits:
            matiere = _deduire_matiere(p.get("titre", ""))
            if matiere not in par_matiere:
                par_matiere[matiere] = {
                    "matiere": matiere,
                    "nb_references": 0,
                    "quantite_totale": 0,
                    "valeur_fcfa": 0,
                    "produits": [],
                }
            s = p.get("stock_actuel", 0)
            par_matiere[matiere]["nb_references"] += 1
            par_matiere[matiere]["quantite_totale"] += s
            par_matiere[matiere]["valeur_fcfa"] += s * p.get("prix_achat", p.get("prix_vente", 0))
            par_matiere[matiere]["produits"].append({
                "produit_id": p.get("produit_id"),
                "titre": p.get("titre"),
                "niveau_scolaire": p.get("niveau_scolaire"),
                "stock_actuel": s,
            })

        result = sorted(par_matiere.values(), key=lambda x: x["quantite_totale"], reverse=True)
        return {"par_matiere": result, "nb_matieres": len(result)}

    # ══════════════════════════════════════
    # INVENTAIRE PAR NIVEAU
    # ══════════════════════════════════════

    @router.get("/inventaire-par-niveau")
    async def inventaire_par_niveau(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Agrégation stock par niveau scolaire."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        # Ordre logique des niveaux
        ORDRE_NIVEAUX = [
            "Grande section", "CP1", "CP2", "CE1", "CE2", "CM1", "CM2",
            "6ème", "5ème", "4ème", "3ème",
            "2nde", "1ère", "Terminale",
            "6ème à Terminale",
        ]

        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        par_niveau: dict = {}
        for p in produits:
            niveau = p.get("niveau_scolaire", "Non défini")
            if niveau not in par_niveau:
                par_niveau[niveau] = {
                    "niveau": niveau,
                    "categorie": p.get("categorie", ""),
                    "nb_references": 0,
                    "quantite_totale": 0,
                    "valeur_fcfa": 0,
                }
            s = p.get("stock_actuel", 0)
            par_niveau[niveau]["nb_references"] += 1
            par_niveau[niveau]["quantite_totale"] += s
            par_niveau[niveau]["valeur_fcfa"] += s * p.get("prix_achat", p.get("prix_vente", 0))

        def sort_key(item):
            try:
                return ORDRE_NIVEAUX.index(item["niveau"])
            except ValueError:
                return 999

        result = sorted(par_niveau.values(), key=sort_key)
        return {"par_niveau": result, "nb_niveaux": len(result)}

    # ══════════════════════════════════════
    # INVENTAIRE PAR CYCLE
    # ══════════════════════════════════════

    @router.get("/inventaire-par-cycle")
    async def inventaire_par_cycle(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Agrégation stock par cycle scolaire (déduit de la catégorie)."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        par_cycle: dict = {}
        for p in produits:
            cycle = _deduire_cycle(p.get("categorie", ""))
            if cycle not in par_cycle:
                par_cycle[cycle] = {
                    "cycle": cycle,
                    "nb_references": 0,
                    "quantite_totale": 0,
                    "valeur_fcfa": 0,
                    "categories": set(),
                }
            s = p.get("stock_actuel", 0)
            par_cycle[cycle]["nb_references"] += 1
            par_cycle[cycle]["quantite_totale"] += s
            par_cycle[cycle]["valeur_fcfa"] += s * p.get("prix_achat", p.get("prix_vente", 0))
            par_cycle[cycle]["categories"].add(p.get("categorie", ""))

        ORDER = ["Primaire", "Collège", "Lycée", "Tous cycles", "Autre"]
        result = []
        for cycle_name in ORDER:
            if cycle_name in par_cycle:
                item = par_cycle.pop(cycle_name)
                item["categories"] = list(item["categories"])
                result.append(item)
        for item in par_cycle.values():
            item["categories"] = list(item["categories"])
            result.append(item)

        return {"par_cycle": result, "nb_cycles": len(result)}

    # ══════════════════════════════════════
    # INVENTAIRE PHYSIQUE
    # ══════════════════════════════════════

    @router.get("/inventaire", response_model=List[dict])
    async def list_inventaires(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        limit: int = Query(50, ge=1, le=200),
        skip: int = Query(0, ge=0),
        statut: Optional[str] = None,
        type_inventaire: Optional[str] = None,
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters: dict = {}
        if statut:
            filters["statut"] = statut
        if type_inventaire:
            filters["type_inventaire"] = type_inventaire

        docs = await db.inventaires.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return docs

    @router.get("/inventaire/{inventaire_id}", response_model=InventaireOut)
    async def get_inventaire(
        inventaire_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        inventaire = await db.inventaires.find_one({"inventaire_id": inventaire_id}, {"_id": 0})
        _ensure(inventaire is not None, 404, "Inventaire introuvable")

        lignes_cursor = db.inventaire_lignes.find({"inventaire_id": inventaire_id}, {"_id": 0})
        lignes = await lignes_cursor.to_list(500)
        lignes_out = []
        for ligne in lignes:
            prod = await db.produits.find_one({"produit_id": ligne["produit_id"]}, {"_id": 0, "reference": 1, "titre": 1})
            lignes_out.append({
                "ligne_id": ligne["ligne_id"],
                "produit_id": ligne["produit_id"],
                "produit_reference": prod.get("reference") if prod else None,
                "produit_titre": prod.get("titre") if prod else None,
                "quantite_theorique": ligne["quantite_theorique"],
                "quantite_comptee": ligne["quantite_comptee"],
                "ecart": ligne["ecart"],
                "regularisee": ligne.get("regularisee", False),
            })

        inventaire["lignes"] = lignes_out
        return InventaireOut(**inventaire)

    @router.post("/inventaire", response_model=InventaireOut, status_code=201)
    async def create_inventaire(
        payload: InventaireIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        inventaire_id = f"inv_{uuid.uuid4().hex[:12]}"
        reference = f"INV-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        now = _now_iso()

        lignes_out = []
        total_ecart = 0
        for ligne in payload.lignes:
            produit = await db.produits.find_one({"produit_id": ligne.produit_id}, {"_id": 0})
            _ensure(produit is not None, 404, f"Produit {ligne.produit_id} introuvable")

            quantite_theorique = produit.get("stock_actuel", 0)
            ecart = ligne.quantite_comptee - quantite_theorique
            total_ecart += ecart

            ligne_doc = {
                "ligne_id": f"ligne_{uuid.uuid4().hex[:12]}",
                "inventaire_id": inventaire_id,
                "produit_id": ligne.produit_id,
                "quantite_theorique": quantite_theorique,
                "quantite_comptee": ligne.quantite_comptee,
                "ecart": ecart,
                "regularisee": False,
            }
            await db.inventaire_lignes.insert_one(ligne_doc)

            lignes_out.append({
                "ligne_id": ligne_doc["ligne_id"],
                "produit_id": ligne.produit_id,
                "produit_reference": produit.get("reference"),
                "produit_titre": produit.get("titre"),
                "quantite_theorique": quantite_theorique,
                "quantite_comptee": ligne.quantite_comptee,
                "ecart": ecart,
                "regularisee": False,
            })

        inventaire_doc = {
            "inventaire_id": inventaire_id,
            "reference": reference,
            "date_inventaire": payload.date_inventaire,
            "type_inventaire": payload.type_inventaire,
            "depot": payload.depot or "principal",
            "responsable": payload.responsable,
            "statut": "brouillon",
            "total_ecart": total_ecart,
            "notes": payload.notes,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.inventaires.insert_one(inventaire_doc)

        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_INVENTORY",
                resource_type="inventory",
                resource_id=inventaire_id,
                details={
                    "reference": reference,
                    "type_inventaire": payload.type_inventaire,
                    "depot": payload.depot,
                    "total_ecart": total_ecart,
                    "lignes_count": len(payload.lignes),
                },
                ip_address=request.client.host if request.client else None
            )

        inventaire_doc["lignes"] = lignes_out
        return InventaireOut(**inventaire_doc)

    @router.post("/inventaire/{inventaire_id}/regulariser", response_model=InventaireOut)
    async def regulariser_inventaire(
        inventaire_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        inventaire = await db.inventaires.find_one({"inventaire_id": inventaire_id}, {"_id": 0})
        _ensure(inventaire is not None, 404, "Inventaire introuvable")
        _ensure(inventaire["statut"] == "brouillon", 400, "Inventaire déjà régularisé")

        now = _now_iso()
        lignes = await db.inventaire_lignes.find({"inventaire_id": inventaire_id}, {"_id": 0}).to_list(500)

        for ligne in lignes:
            if ligne["ecart"] != 0:
                mouvement_id = f"mvt_{uuid.uuid4().hex[:12]}"
                produit = await db.produits.find_one({"produit_id": ligne["produit_id"]}, {"_id": 0})
                stock_avant = produit.get("stock_actuel", 0) if produit else 0
                stock_apres = ligne["quantite_comptee"]

                await db.produits.update_one(
                    {"produit_id": ligne["produit_id"]},
                    {"$set": {"stock_actuel": stock_apres, "updated_at": now}}
                )
                await db.mouvements_stock.insert_one({
                    "mouvement_id": mouvement_id,
                    "produit_id": ligne["produit_id"],
                    "type_mouvement": "inventaire",
                    "quantite": abs(ligne["ecart"]),
                    "stock_avant": stock_avant,
                    "stock_apres": stock_apres,
                    "motif": f"Régularisation inventaire {inventaire['reference']}",
                    "created_by": me["user_id"],
                    "created_at": now,
                })
                await db.inventaire_lignes.update_one(
                    {"ligne_id": ligne["ligne_id"]},
                    {"$set": {"regularisee": True}}
                )

        await db.inventaires.update_one(
            {"inventaire_id": inventaire_id},
            {"$set": {"statut": "regularise", "updated_at": now}}
        )

        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="REGULARIZE_INVENTORY",
                resource_type="inventory",
                resource_id=inventaire_id,
                details={"reference": inventaire["reference"], "total_ecart": inventaire["total_ecart"]},
                ip_address=request.client.host if request.client else None
            )

        updated = await db.inventaires.find_one({"inventaire_id": inventaire_id}, {"_id": 0})
        lignes_out = []
        for ligne in lignes:
            prod = await db.produits.find_one({"produit_id": ligne["produit_id"]}, {"_id": 0})
            lignes_out.append({
                "ligne_id": ligne["ligne_id"],
                "produit_id": ligne["produit_id"],
                "produit_reference": prod.get("reference") if prod else None,
                "produit_titre": prod.get("titre") if prod else None,
                "quantite_theorique": ligne["quantite_theorique"],
                "quantite_comptee": ligne["quantite_comptee"],
                "ecart": ligne["ecart"],
                "regularisee": True,
            })
        updated["lignes"] = lignes_out
        return InventaireOut(**updated)

    # ══════════════════════════════════════
    # DÉPÔTS
    # ══════════════════════════════════════

    @router.get("/depots")
    async def list_depots(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        depots = await db.depots.find({}, {"_id": 0}).to_list(100)

        # Toujours inclure le dépôt principal par défaut
        noms_existants = {d["code"] for d in depots}
        if "PRINCIPAL" not in noms_existants:
            # Calculer le stock du dépôt principal (tous les produits sans champ depot ou depot=principal)
            produits_principal = await db.produits.find(
                {"$or": [{"depot": {"$exists": False}}, {"depot": "principal"}]},
                {"_id": 0, "stock_actuel": 1, "prix_achat": 1, "prix_vente": 1}
            ).to_list(1000)
            quantite_principal = sum(p.get("stock_actuel", 0) for p in produits_principal)
            valeur_principal = sum(
                p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0))
                for p in produits_principal
            )
            depots.insert(0, {
                "depot_id": "principal",
                "code": "PRINCIPAL",
                "nom": "Dépôt Principal",
                "adresse": "Siège Éditions FABS CI",
                "responsable": None,
                "description": "Dépôt principal par défaut",
                "quantite_totale": quantite_principal,
                "valeur_fcfa": valeur_principal,
                "nb_references": len(produits_principal),
                "created_at": None,
            })

        # Enrichir chaque dépôt avec ses stats
        for depot in depots:
            if depot.get("depot_id") != "principal":
                produits_depot = await db.produits.find(
                    {"depot": depot["code"]},
                    {"_id": 0, "stock_actuel": 1, "prix_achat": 1, "prix_vente": 1}
                ).to_list(1000)
                depot["quantite_totale"] = sum(p.get("stock_actuel", 0) for p in produits_depot)
                depot["valeur_fcfa"] = sum(
                    p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0))
                    for p in produits_depot
                )
                depot["nb_references"] = len(produits_depot)

        return {"depots": depots, "nb_depots": len(depots)}

    @router.post("/depots", status_code=201)
    async def create_depot(
        payload: DepotIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        existing = await db.depots.find_one({"code": payload.code.upper()})
        _ensure(existing is None, 409, f"Dépôt avec le code {payload.code} existe déjà")

        depot_id = f"depot_{uuid.uuid4().hex[:12]}"
        now = _now_iso()
        depot_doc = {
            "depot_id": depot_id,
            "code": payload.code.upper(),
            "nom": payload.nom,
            "adresse": payload.adresse,
            "responsable": payload.responsable,
            "description": payload.description,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.depots.insert_one(depot_doc)
        depot_doc.pop("_id", None)
        return depot_doc

    @router.post("/depots/transfert", status_code=201)
    async def transfert_stock(
        payload: TransfertIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Transfert de stock entre deux dépôts."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        produit = await db.produits.find_one({"produit_id": payload.produit_id}, {"_id": 0})
        _ensure(produit is not None, 404, "Produit introuvable")
        _ensure(
            payload.depot_source != payload.depot_destination,
            400, "Les dépôts source et destination doivent être différents"
        )
        _ensure(produit.get("stock_actuel", 0) >= payload.quantite, 400, "Stock insuffisant pour le transfert")

        now = _now_iso()
        # Enregistrer le mouvement de transfert
        mouvement_id = f"mvt_{uuid.uuid4().hex[:12]}"
        await db.mouvements_stock.insert_one({
            "mouvement_id": mouvement_id,
            "produit_id": payload.produit_id,
            "type_mouvement": "transfert",
            "quantite": payload.quantite,
            "stock_avant": produit.get("stock_actuel", 0),
            "stock_apres": produit.get("stock_actuel", 0),  # Stock global inchangé
            "motif": f"Transfert {payload.depot_source} → {payload.depot_destination}. {payload.motif or ''}".strip(),
            "depot_source": payload.depot_source,
            "depot_destination": payload.depot_destination,
            "created_by": me["user_id"],
            "created_at": now,
        })

        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="STOCK_TRANSFER",
                resource_type="stock_movement",
                resource_id=mouvement_id,
                details={
                    "produit_id": payload.produit_id,
                    "quantite": payload.quantite,
                    "depot_source": payload.depot_source,
                    "depot_destination": payload.depot_destination,
                },
                ip_address=request.client.host if request.client else None
            )

        return {
            "mouvement_id": mouvement_id,
            "message": "Transfert enregistré avec succès",
            "produit_id": payload.produit_id,
            "quantite": payload.quantite,
            "depot_source": payload.depot_source,
            "depot_destination": payload.depot_destination,
        }

    # ══════════════════════════════════════
    # ALERTES LOGISTIQUES
    # ══════════════════════════════════════

    @router.get("/alertes-logistiques")
    async def alertes_logistiques(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """Alertes complètes : rupture / faible / surstock / inactif."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        from datetime import timedelta
        produits = await db.produits.find({}, {"_id": 0}).to_list(1000)

        # Produits actifs (avec mouvement récent)
        date_90j = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        ids_actifs: set = set()
        async for m in db.mouvements_stock.find({"created_at": {"$gte": date_90j}}, {"produit_id": 1, "_id": 0}):
            ids_actifs.add(m["produit_id"])

        ruptures = []
        faibles = []
        surstocks = []
        inactifs = []

        for p in produits:
            s = p.get("stock_actuel", 0)
            seuil = p.get("seuil_alerte", 20)
            pid = p.get("produit_id")
            base = {
                "produit_id": pid,
                "reference": p.get("reference"),
                "titre": p.get("titre", "")[:60],
                "stock_actuel": s,
                "seuil_alerte": seuil,
                "categorie": p.get("categorie"),
                "niveau_scolaire": p.get("niveau_scolaire"),
            }

            if s == 0:
                ruptures.append({**base, "niveau_alerte": "critique", "message": "Rupture totale"})
            elif s <= seuil:
                faibles.append({**base, "niveau_alerte": "warning", "ecart": seuil - s, "message": f"Stock faible ({s}/{seuil})"})

            if seuil > 0 and s > seuil * 5:
                surstocks.append({**base, "niveau_alerte": "info", "excedent": s - seuil * 2, "message": f"Surstock ({s} unités)"})

            if pid not in ids_actifs and s > 0:
                inactifs.append({**base, "niveau_alerte": "info", "message": "Aucun mouvement depuis 90 jours"})

        return {
            "resume": {
                "nb_ruptures": len(ruptures),
                "nb_faibles": len(faibles),
                "nb_surstocks": len(surstocks),
                "nb_inactifs": len(inactifs),
                "total_alertes": len(ruptures) + len(faibles),
            },
            "ruptures": ruptures,
            "faibles": faibles,
            "surstocks": surstocks,
            "inactifs": inactifs,
        }

    # Compatibilité ancienne route
    @router.get("/alertes-rupture", response_model=List[dict])
    async def get_alertes_rupture(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        seuil: int = Query(10, ge=0),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        cursor = db.produits.find(
            {"$or": [
                {"stock_actuel": {"$lt": seuil}},
                {"$expr": {"$lt": ["$stock_actuel", "$seuil_alerte"]}}
            ]},
            {"_id": 0, "produit_id": 1, "reference": 1, "titre": 1, "stock_actuel": 1, "seuil_alerte": 1}
        ).sort("stock_actuel", 1)

        produits = await cursor.to_list(200)
        alertes = []
        for prod in produits:
            seuil_eff = prod.get("seuil_alerte", seuil)
            alertes.append({
                "product_id": prod.get("produit_id"),
                "reference": prod.get("reference"),
                "titre": prod.get("titre"),
                "stock_actuel": prod["stock_actuel"],
                "seuil_alerte": seuil_eff,
                "ecart": seuil_eff - prod["stock_actuel"],
            })
        return alertes

    # ══════════════════════════════════════
    # STATISTIQUES ÉDITORIALES
    # ══════════════════════════════════════

    @router.get("/top-ventes")
    async def top_ventes(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        limit: int = Query(10, ge=1, le=50),
        periode_jours: int = Query(90, ge=1, le=365),
    ):
        """Top produits par volume de sorties sur la période."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        from datetime import timedelta
        date_limite = (datetime.now(timezone.utc) - timedelta(days=periode_jours)).isoformat()

        pipeline = [
            {"$match": {
                "type_mouvement": {"$in": ["sortie", "specimen_gratuit"]},
                "created_at": {"$gte": date_limite}
            }},
            {"$group": {
                "_id": "$produit_id",
                "quantite_sortie": {"$sum": "$quantite"},
                "nb_mouvements": {"$sum": 1},
            }},
            {"$sort": {"quantite_sortie": -1}},
            {"$limit": limit},
        ]

        result = await db.mouvements_stock.aggregate(pipeline).to_list(limit)

        enriched = []
        for r in result:
            prod = await db.produits.find_one({"produit_id": r["_id"]}, {"_id": 0})
            if prod:
                enriched.append({
                    "produit_id": r["_id"],
                    "titre": prod.get("titre"),
                    "reference": prod.get("reference"),
                    "categorie": prod.get("categorie"),
                    "niveau_scolaire": prod.get("niveau_scolaire"),
                    "matiere": _deduire_matiere(prod.get("titre", "")),
                    "quantite_sortie": r["quantite_sortie"],
                    "nb_mouvements": r["nb_mouvements"],
                    "stock_actuel": prod.get("stock_actuel", 0),
                    "chiffre_affaires_potentiel": r["quantite_sortie"] * prod.get("prix_vente", 0),
                })

        return {
            "periode_jours": periode_jours,
            "top_ventes": enriched,
            "nb_resultats": len(enriched),
        }

    @router.get("/produits-dormants")
    async def produits_dormants(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        jours_inactivite: int = Query(90, ge=1, le=365),
    ):
        """Produits sans mouvement depuis N jours (avec stock > 0)."""
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        from datetime import timedelta
        date_limite = (datetime.now(timezone.utc) - timedelta(days=jours_inactivite)).isoformat()

        ids_actifs: set = set()
        async for m in db.mouvements_stock.find(
            {"created_at": {"$gte": date_limite}},
            {"produit_id": 1, "_id": 0}
        ):
            ids_actifs.add(m["produit_id"])

        produits = await db.produits.find({"stock_actuel": {"$gt": 0}}, {"_id": 0}).to_list(1000)
        dormants = []
        for p in produits:
            if p.get("produit_id") not in ids_actifs:
                dormants.append({
                    "produit_id": p.get("produit_id"),
                    "titre": p.get("titre"),
                    "reference": p.get("reference"),
                    "categorie": p.get("categorie"),
                    "niveau_scolaire": p.get("niveau_scolaire"),
                    "matiere": _deduire_matiere(p.get("titre", "")),
                    "stock_actuel": p.get("stock_actuel", 0),
                    "valeur_immobilisee_fcfa": p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0)),
                    "jours_inactivite": jours_inactivite,
                })

        dormants.sort(key=lambda x: x["valeur_immobilisee_fcfa"], reverse=True)

        return {
            "jours_inactivite": jours_inactivite,
            "produits_dormants": dormants,
            "nb_dormants": len(dormants),
            "valeur_totale_immobilisee": sum(d["valeur_immobilisee_fcfa"] for d in dormants),
        }

    # ──────────────────────────────────────────────
    # EXPORT PDF — État des stocks
    # ──────────────────────────────────────────────
    @router.get("/export-etat-stock")
    async def export_etat_stock(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        filtre: Optional[str] = Query(None, description="global|matiere|niveau|cycle — None = tous"),
        categorie: Optional[str] = Query(None, description="Filtrer par catégorie"),
        format: Optional[str] = Query("pdf", description="pdf"),
    ):
        """Génère un PDF de l'état des stocks (toutes références ou filtré)."""
        from fastapi.responses import StreamingResponse
        from stock_pdf_generator import generate_etat_stock_pdf

        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        # Récupérer tous les produits
        query: dict = {}
        if categorie:
            query["categorie"] = categorie
        produits = await db.produits.find(query, {"_id": 0}).sort("categorie", 1).to_list(2000)

        # Enrichir avec matière
        for p in produits:
            p["matiere"] = _deduire_matiere(p.get("titre", ""))

        # Agrégats globaux
        total_refs = len(produits)
        total_qty  = sum(p.get("stock_actuel", 0) for p in produits)
        total_val  = sum(p.get("stock_actuel", 0) * p.get("prix_achat", p.get("prix_vente", 0)) for p in produits)
        nb_alertes = sum(1 for p in produits if p.get("stock_actuel", 0) <= p.get("seuil_alerte", 20) and p.get("stock_actuel", 0) > 0)
        nb_ruptures = sum(1 for p in produits if p.get("stock_actuel", 0) == 0)

        resume = {
            "nb_references": total_refs,
            "quantite_totale": total_qty,
            "valeur_totale_fcfa": total_val,
            "nb_alertes": nb_alertes,
            "nb_ruptures": nb_ruptures,
            "date_edition": datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M"),
            "edite_par": me.get("email", me.get("user_id", "")),
            "filtre": filtre or "global",
            "categorie": categorie or "Toutes catégories",
        }

        buffer = generate_etat_stock_pdf(produits, resume)
        filename = f"etat_stock_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Filename": filename,
            },
        )

    return router


# ──────────────────────────────────────────────
# Seed & Index
# ──────────────────────────────────────────────

async def seed_mouvements_stock(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Créer les index nécessaires (idempotent)."""
    await db.mouvements_stock.create_index("mouvement_id", unique=True)
    await db.mouvements_stock.create_index("produit_id")
    await db.mouvements_stock.create_index("type_mouvement")
    await db.mouvements_stock.create_index("created_at")

    await db.inventaires.create_index("inventaire_id", unique=True)
    await db.inventaires.create_index("reference", unique=True)
    await db.inventaires.create_index("date_inventaire")
    await db.inventaires.create_index("statut")
    await db.inventaires.create_index("type_inventaire")

    await db.inventaire_lignes.create_index("ligne_id", unique=True)
    await db.inventaire_lignes.create_index("inventaire_id")
    await db.inventaire_lignes.create_index("produit_id")

    await db.depots.create_index("depot_id", unique=True)
    await db.depots.create_index("code", unique=True)

    return 0
