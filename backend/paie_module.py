"""
Module Paie — Sprint 6b V10 (ERP FABS-CI)
Calculs ITS / CNPS / CMU pour la Côte d'Ivoire + bulletins de paie

NOTE FISCALE :
Les taux et tranches sont configurés selon les règles 2024-2026 en Côte d'Ivoire.
Ils sont stockés en constantes en haut du fichier pour être facilement ajustés
si la DGI publie de nouveaux barèmes (loi de finances annuelle).
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging
import os
import jwt

logger = logging.getLogger("fabsci.paie")

# ============================================================================
# CONSTANTES FISCALES CÔTE D'IVOIRE — ajustables sans redéploiement
# ============================================================================

# Barème ITS (Impôt sur Traitements et Salaires) — tranches progressives
# Source : Code Général des Impôts, art. 116 — applicable au salaire net catégoriel
ITS_TRANCHES = [
    (75_000,    0.00),
    (240_000,   0.16),
    (800_000,   0.21),
    (2_400_000, 0.24),
    (8_000_000, 0.28),
    (float("inf"), 0.32),
]

# CNPS — taux salarial (cotisation vieillesse + caisse retraite)
CNPS_TAUX_SALARIAL = 0.063          # 6.3 % à la charge du salarié
CNPS_PLAFOND = 1_647_315            # plafond mensuel 2026 (FCFA)

# Cotisations patronales (à la charge de l'employeur)
CNPS_TAUX_PATRONAL = 0.077          # 7.7 % retraite + ITS prestation famille
ACCIDENTS_TRAVAIL = 0.02            # 2 % (varie par secteur — moyenne tertiaire)
PRESTATIONS_FAMILLE = 0.0575        # 5.75 %

# CMU (Couverture Maladie Universelle) — forfait mensuel
CMU_FORFAIT = 1_000                 # 1 000 FCFA/mois/salarié


# ============================================================================
# MOTEUR DE CALCUL
# ============================================================================

def calculer_its(base_imposable: float) -> float:
    """Calcule l'ITS selon le barème progressif Côte d'Ivoire."""
    if base_imposable <= 0:
        return 0.0
    impot = 0.0
    seuil_prec = 0
    for seuil, taux in ITS_TRANCHES:
        if base_imposable <= seuil:
            impot += (base_imposable - seuil_prec) * taux
            return round(impot, 0)
        impot += (seuil - seuil_prec) * taux
        seuil_prec = seuil
    return round(impot, 0)


def calculer_paie(
    salaire_brut: float,
    primes: float = 0.0,
    avantages_nature: float = 0.0,
    retenues_diverses: float = 0.0,
) -> dict:
    """Calcule la paie complète d'un employé sur un mois.

    Retourne un dict structuré :
      - salaire_brut
      - primes, avantages_nature
      - brut_imposable
      - cnps_salarial
      - base_its
      - its
      - cmu
      - retenues_diverses
      - total_retenues
      - net_a_payer
      - charges_patronales (détail)
      - cout_total_employeur
    """
    salaire_brut = float(salaire_brut or 0)
    primes = float(primes or 0)
    avantages_nature = float(avantages_nature or 0)
    retenues_diverses = float(retenues_diverses or 0)

    # Brut imposable
    brut_imposable = salaire_brut + primes + avantages_nature

    # CNPS salarial (plafonné)
    base_cnps = min(brut_imposable, CNPS_PLAFOND)
    cnps_salarial = round(base_cnps * CNPS_TAUX_SALARIAL, 0)

    # Base ITS = brut imposable − CNPS salarial
    base_its = max(0, brut_imposable - cnps_salarial)
    its = calculer_its(base_its)

    # CMU forfait
    cmu = CMU_FORFAIT

    # Retenues totales
    total_retenues = cnps_salarial + its + cmu + retenues_diverses

    # Net à payer
    net_a_payer = brut_imposable - total_retenues

    # Charges patronales
    base_pat = min(brut_imposable, CNPS_PLAFOND)
    cnps_patronal = round(base_pat * CNPS_TAUX_PATRONAL, 0)
    accidents = round(base_pat * ACCIDENTS_TRAVAIL, 0)
    prestations = round(base_pat * PRESTATIONS_FAMILLE, 0)
    charges_patronales_total = cnps_patronal + accidents + prestations

    return {
        "salaire_brut": salaire_brut,
        "primes": primes,
        "avantages_nature": avantages_nature,
        "brut_imposable": round(brut_imposable, 0),
        "cnps_salarial": cnps_salarial,
        "base_its": round(base_its, 0),
        "its": its,
        "cmu": cmu,
        "retenues_diverses": retenues_diverses,
        "total_retenues": round(total_retenues, 0),
        "net_a_payer": round(net_a_payer, 0),
        "charges_patronales": {
            "cnps_patronal": cnps_patronal,
            "accidents_travail": accidents,
            "prestations_famille": prestations,
            "total": charges_patronales_total,
        },
        "cout_total_employeur": round(brut_imposable + charges_patronales_total, 0),
        "taux_appliques": {
            "cnps_salarial": CNPS_TAUX_SALARIAL,
            "cnps_patronal": CNPS_TAUX_PATRONAL,
            "accidents_travail": ACCIDENTS_TRAVAIL,
            "prestations_famille": PRESTATIONS_FAMILLE,
            "cmu_forfait": CMU_FORFAIT,
            "its_bareme": [{"seuil": s if s != float("inf") else None, "taux": t} for s, t in ITS_TRANCHES],
        },
    }


# ============================================================================
# SCHEMAS
# ============================================================================

class CalculPaieIn(BaseModel):
    salaire_brut: float = Field(..., ge=0)
    primes: float = Field(default=0, ge=0)
    avantages_nature: float = Field(default=0, ge=0)
    retenues_diverses: float = Field(default=0, ge=0)


class BulletinIn(BaseModel):
    employe_id: str
    periode: str = Field(..., description="Format YYYY-MM (ex: 2026-06)")
    salaire_brut: float = Field(..., ge=0)
    primes: float = Field(default=0, ge=0)
    avantages_nature: float = Field(default=0, ge=0)
    retenues_diverses: float = Field(default=0, ge=0)
    notes: Optional[str] = None


# ============================================================================
# AUTH HELPER
# ============================================================================

async def _resolve_user(request: Request, authorization: Optional[str]) -> dict:
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "")
    else:
        token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Token manquant")
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET", ""), algorithms=["HS256"])
        return {"user_id": payload.get("user_id"), "role": payload.get("role")}
    except Exception as exc:
        raise HTTPException(401, f"Token invalide: {exc}")


# ============================================================================
# ROUTES
# ============================================================================

router = APIRouter(prefix="/paie", tags=["Paie"])


@router.post("/calculer")
async def calculer_paie_endpoint(
    request: Request,
    payload: CalculPaieIn = Body(...),
    authorization: Optional[str] = Header(default=None),
):
    """Preview du calcul de paie sans persister (utilisable depuis l'UI live)."""
    await _resolve_user(request, authorization)
    return calculer_paie(
        payload.salaire_brut,
        payload.primes,
        payload.avantages_nature,
        payload.retenues_diverses,
    )


@router.post("/bulletins")
async def creer_bulletin(
    request: Request,
    payload: BulletinIn = Body(...),
    authorization: Optional[str] = Header(default=None),
):
    """Crée et enregistre un bulletin de paie."""
    user = await _resolve_user(request, authorization)
    db = request.app.state.db

    employe = await db.employes.find_one({"employe_id": payload.employe_id})
    if not employe:
        raise HTTPException(404, "Employé introuvable")

    calc = calculer_paie(
        payload.salaire_brut, payload.primes,
        payload.avantages_nature, payload.retenues_diverses,
    )

    now = datetime.now(timezone.utc).isoformat()
    bulletin = {
        "bulletin_id": f"BULL-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}",
        "employe_id": payload.employe_id,
        "employe_matricule": employe.get("matricule"),
        "employe_nom": f"{employe.get('nom', '')} {employe.get('prenoms', '')}".strip(),
        "periode": payload.periode,
        "calcul": calc,
        "notes": payload.notes,
        "created_by": user["user_id"],
        "created_at": now,
        "statut": "brouillon",
    }
    await db.bulletins_paie.insert_one(bulletin)
    bulletin.pop("_id", None)
    return bulletin


@router.get("/bulletins")
async def liste_bulletins(
    request: Request,
    employe_id: Optional[str] = Query(default=None),
    periode: Optional[str] = Query(default=None),
    limit: int = 100,
    authorization: Optional[str] = Header(default=None),
):
    await _resolve_user(request, authorization)
    db = request.app.state.db
    q = {}
    if employe_id: q["employe_id"] = employe_id
    if periode: q["periode"] = periode
    items = await db.bulletins_paie.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"items": items, "total": len(items)}


@router.get("/bulletins/{bulletin_id}")
async def detail_bulletin(
    bulletin_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    await _resolve_user(request, authorization)
    db = request.app.state.db
    b = await db.bulletins_paie.find_one({"bulletin_id": bulletin_id}, {"_id": 0})
    if not b:
        raise HTTPException(404, "Bulletin introuvable")
    return b


@router.get("/bareme")
async def get_bareme(request: Request, authorization: Optional[str] = Header(default=None)):
    """Retourne la configuration fiscale appliquée (lecture seule)."""
    await _resolve_user(request, authorization)
    return {
        "its_tranches": [
            {"seuil_max": s if s != float("inf") else None, "taux": t}
            for s, t in ITS_TRANCHES
        ],
        "cnps_taux_salarial": CNPS_TAUX_SALARIAL,
        "cnps_plafond": CNPS_PLAFOND,
        "cnps_taux_patronal": CNPS_TAUX_PATRONAL,
        "accidents_travail": ACCIDENTS_TRAVAIL,
        "prestations_famille": PRESTATIONS_FAMILLE,
        "cmu_forfait": CMU_FORFAIT,
        "source": "Code Général des Impôts CI · CNPS 2024-2026",
    }
