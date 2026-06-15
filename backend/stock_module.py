"""
Module Stock & Mouvements — Sprint 9
- Suivi des mouvements de stock (entrées/sorties)
- Ajustements d'inventaire
- Historique des mouvements par produit
- Alertes stock automatiques
- Inventaire physique
- Régularisations d'inventaire
- Alertes rupture stock
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional, List
import uuid
import logging

from fastapi import APIRouter, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger("fabsci.stock")

READ_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock", "responsable_magasinier"}
WRITE_ROLES = {"super_admin", "directeur_general", "gestionnaire_stock", "responsable_magasinier"}

TypeMouvement = Literal["entree", "sortie", "ajustement", "retour", "specimen_gratuit", "inventaire"]


def _ensure(condition: bool, status: int, detail: str) -> None:
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    date_inventaire: str  # ISO date YYYY-MM-DD
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
    statut: str
    lignes: List[LigneInventaireOut]
    total_ecart: int
    notes: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: str


def build_stock_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    router = APIRouter(prefix="/stock", tags=["stock"])

    @router.get("/mouvements", response_model=List[MouvementStockOut])
    async def list_mouvements(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        produit_id: Optional[str] = None,
        type_mouvement: Optional[TypeMouvement] = None,
        limit: int = Query(50, ge=1, le=200),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if produit_id:
            filters["produit_id"] = produit_id
        if type_mouvement:
            filters["type_mouvement"] = type_mouvement

        cursor = db.mouvements_stock.find(filters, {"_id": 0}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(limit)
        
        for doc in docs:
            prod = await db.produits.find_one({"product_id": doc["produit_id"]}, {"_id": 0, "reference": 1, "titre": 1})
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

        # Get product
        produit = await db.produits.find_one({"product_id": payload.produit_id}, {"_id": 0})
        _ensure(produit is not None, 404, "Produit introuvable")

        stock_avant = produit.get("stock_actuel", 0)
        
        # Calculate new stock
        if payload.type_mouvement in ["entree", "retour"]:
            stock_apres = stock_avant + payload.quantite
        elif payload.type_mouvement == "specimen_gratuit":
            # Specimens gratuits : sortie sans facturation
            stock_apres = max(0, stock_avant - payload.quantite)
        else:  # sortie, ajustement
            stock_apres = max(0, stock_avant - payload.quantite)

        # Update product stock
        await db.produits.update_one(
            {"product_id": payload.produit_id},
            {"$set": {"stock_actuel": stock_apres, "updated_at": _now_iso()}}
        )

        # Create mouvement
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

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_STOCK_MOVEMENT",
                resource_type="stock_movement",
                resource_id=mouvement_id,
                details={
                    "produit_id": payload.produit_id,
                    "produit_reference": produit.get("reference"),
                    "type_mouvement": payload.type_mouvement,
                    "quantite": payload.quantite,
                    "stock_avant": stock_avant,
                    "stock_apres": stock_apres,
                    "commande_id": payload.commande_id,
                    "bl_id": payload.bl_id
                },
                ip_address=request.client.host if request.client else None
            )

        mouvement_doc["produit_reference"] = produit.get("reference")
        mouvement_doc["produit_titre"] = produit.get("titre")
        
        return MouvementStockOut(**mouvement_doc)

    # ---------- INVENTAIRE PHYSIQUE ----------
    @router.post("/inventaire", response_model=InventaireOut, status_code=201)
    async def create_inventaire(
        payload: InventaireIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in WRITE_ROLES, 403, "Accès refusé")

        # Generate inventaire reference
        inventaire_id = f"inv_{uuid.uuid4().hex[:12]}"
        reference = f"INV-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        now = _now_iso()

        # Process lignes
        lignes_out = []
        total_ecart = 0
        for ligne in payload.lignes:
            produit = await db.produits.find_one({"product_id": ligne.produit_id}, {"_id": 0})
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

            ligne_out = {
                "ligne_id": ligne_doc["ligne_id"],
                "produit_id": ligne.produit_id,
                "produit_reference": produit.get("reference"),
                "produit_titre": produit.get("titre"),
                "quantite_theorique": quantite_theorique,
                "quantite_comptee": ligne.quantite_comptee,
                "ecart": ecart,
                "regularisee": False,
            }
            lignes_out.append(ligne_out)

        # Create inventaire
        inventaire_doc = {
            "inventaire_id": inventaire_id,
            "reference": reference,
            "date_inventaire": payload.date_inventaire,
            "statut": "brouillon",
            "total_ecart": total_ecart,
            "notes": payload.notes,
            "created_by": me["user_id"],
            "created_at": now,
            "updated_at": now,
        }
        await db.inventaires.insert_one(inventaire_doc)

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="CREATE_INVENTORY",
                resource_type="inventory",
                resource_id=inventaire_id,
                details={
                    "reference": reference,
                    "date_inventaire": payload.date_inventaire,
                    "total_ecart": total_ecart,
                    "lignes_count": len(payload.lignes)
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
        lignes_cursor = db.inventaire_lignes.find({"inventaire_id": inventaire_id}, {"_id": 0})
        lignes = await lignes_cursor.to_list(500)

        # Regulariser chaque ligne
        for ligne in lignes:
            if ligne["ecart"] != 0:
                # Create mouvement d'inventaire
                mouvement_id = f"mvt_{uuid.uuid4().hex[:12]}"
                produit = await db.produits.find_one({"product_id": ligne["produit_id"]}, {"_id": 0})
                stock_avant = produit.get("stock_actuel", 0)
                stock_apres = ligne["quantite_comptee"]

                await db.produits.update_one(
                    {"product_id": ligne["produit_id"]},
                    {"$set": {"stock_actuel": stock_apres, "updated_at": now}}
                )

                mouvement_doc = {
                    "mouvement_id": mouvement_id,
                    "produit_id": ligne["produit_id"],
                    "type_mouvement": "inventaire",
                    "quantite": abs(ligne["ecart"]),
                    "stock_avant": stock_avant,
                    "stock_apres": stock_apres,
                    "motif": f"Régularisation inventaire {inventaire['reference']}",
                    "created_by": me["user_id"],
                    "created_at": now,
                }
                await db.mouvements_stock.insert_one(mouvement_doc)

                # Marquer ligne comme régularisée
                await db.inventaire_lignes.update_one(
                    {"ligne_id": ligne["ligne_id"]},
                    {"$set": {"regularisee": True}}
                )

        # Update inventaire statut
        await db.inventaires.update_one(
            {"inventaire_id": inventaire_id},
            {"$set": {"statut": "regularise", "updated_at": now}}
        )

        # Audit log
        if log_audit_event:
            await log_audit_event(
                user_id=me["user_id"],
                action="REGULARIZE_INVENTORY",
                resource_type="inventory",
                resource_id=inventaire_id,
                details={
                    "reference": inventaire['reference'],
                    "total_ecart": inventaire["total_ecart"],
                    "lignes_regularisees": len([l for l in lignes if l["ecart"] != 0])
                },
                ip_address=request.client.host if request.client else None
            )

        updated = await db.inventaires.find_one({"inventaire_id": inventaire_id}, {"_id": 0})
        
        # Rebuild lignes with product info
        lignes_out = []
        for ligne in lignes:
            produit = await db.produits.find_one({"product_id": ligne["produit_id"]}, {"_id": 0})
            ligne_out = {
                "ligne_id": ligne["ligne_id"],
                "produit_id": ligne["produit_id"],
                "produit_reference": produit.get("reference") if produit else None,
                "produit_titre": produit.get("titre") if produit else None,
                "quantite_theorique": ligne["quantite_theorique"],
                "quantite_comptee": ligne["quantite_comptee"],
                "ecart": ligne["ecart"],
                "regularisee": True,
            }
            lignes_out.append(ligne_out)

        updated["lignes"] = lignes_out
        return InventaireOut(**updated)

    # ---------- ALERTES RUPTURE STOCK ----------
    @router.get("/alertes-rupture", response_model=List[dict])
    async def get_alertes_rupture(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        seuil: int = Query(10, ge=0, description="Seuil d'alerte (défaut: 10)"),
    ):
        me = await resolve_user(request, authorization)
        _ensure(me["role"] in READ_ROLES, 403, "Accès refusé")

        # Find products with stock below threshold
        cursor = db.produits.find(
            {"stock_actuel": {"$lt": seuil}},
            {"_id": 0, "product_id": 1, "reference": 1, "titre": 1, "stock_actuel": 1, "stock_initial": 1}
        ).sort("stock_actuel", 1)
        
        produits = await cursor.to_list(200)
        
        alertes = []
        for prod in produits:
            alertes.append({
                "product_id": prod["product_id"],
                "reference": prod.get("reference"),
                "titre": prod.get("titre"),
                "stock_actuel": prod["stock_actuel"],
                "stock_initial": prod.get("stock_initial", 0),
                "seuil_alerte": seuil,
                "ecart": seuil - prod["stock_actuel"],
            })
        
        return alertes

    return router


async def seed_mouvements_stock(db: AsyncIOMotorDatabase, user_id: str) -> int:
    """Seed demo mouvements (optional)"""
    existing = await db.mouvements_stock.count_documents({})
    if existing > 0:
        return 0
    
    # Create indexes
    await db.mouvements_stock.create_index("mouvement_id", unique=True)
    await db.mouvements_stock.create_index("produit_id")
    await db.mouvements_stock.create_index("type_mouvement")
    await db.mouvements_stock.create_index("created_at")
    
    # Create indexes for inventaires
    await db.inventaires.create_index("inventaire_id", unique=True)
    await db.inventaires.create_index("reference", unique=True)
    await db.inventaires.create_index("date_inventaire")
    await db.inventaires.create_index("statut")
    await db.inventaire_lignes.create_index("ligne_id", unique=True)
    await db.inventaire_lignes.create_index("inventaire_id")
    await db.inventaire_lignes.create_index("produit_id")
    
    return 0
