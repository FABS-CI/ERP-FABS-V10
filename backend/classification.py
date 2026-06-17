"""
Classification automatique des produits éditoriaux FABS-CI.

À partir du TITRE d'un article, déduit de façon déterministe :
  - matiere        : Français, Mathématiques, Physique-Chimie, SVT,
                     Histoire-Géographie, Anglais, Philosophie,
                     Éducation Musicale, Arts Plastiques, Littérature
  - niveau_scolaire: CP1..CM2, 6e..3e, 2nde, 1ère, Terminale
  - cycle          : Maternelle, Primaire, Collège (Premier cycle),
                     Lycée (Second cycle)
  - categorie      : maternelle | primaire | premier_cycle | second_cycle
                     | litterature | livre_commun   (littéraux DB)

Règles 100% reproductibles (aucun appel réseau/LLM).
Les valeurs sont des SUGGESTIONS : l'utilisateur peut les écraser.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, TypedDict


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def _norm(s: str) -> str:
    """Majuscule, sans accents, espaces compactés — pour le pattern matching."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # drop accents
    s = s.upper()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ---------------------------------------------------------------------------
# Matières — ordre = priorité (du plus spécifique au plus général)
# ---------------------------------------------------------------------------
# Chaque entrée : (matiere, [regex sur titre normalisé])
_MATIERE_RULES: list[tuple[str, list[str]]] = [
    ("Physique-Chimie", [r"\bPHYSIQUE\b", r"\bCHIMIE\b", r"PHYSIQUE\W*CHIMIE"]),
    ("SVT", [r"\bSVT\b", r"SCIENCES DE LA VIE ET DE LA TERRE"]),
    ("Histoire-Géographie", [r"\bHISTOIRE\b", r"\bGEOGRAPHIE\b", r"HISTOIRE\W*GEO"]),
    ("Philosophie", [r"\bPHILOSOPHIE\b", r"\bPHILO\b"]),
    ("Anglais", [r"\bANGLAIS\b"]),
    ("Mathématiques", [r"\bMATHS?\b", r"\bMATHEMATIQUES?\b", r"\bMATHEMATIQUE\b"]),
    ("Éducation Musicale", [r"\bMUSIQUE\b", r"EDUCATION MUSICALE", r"\bFLUTE\b", r"\bBEC SOPRANO\b"]),
    ("Arts Plastiques", [r"ARTS? PLASTIQUES?"]),
    ("Français", [
        r"\bFRANCAIS\b", r"\bECRITURE\b", r"\bPRELECTURE\b", r"\bLECTURE\b",
        r"\bREDACTION\b", r"\bGRAMMAIRE\b", r"\bORTHOGRAPHE\b",
    ]),
    ("Littérature", [r"\bROMAN\b", r"\bNOUVELLE\b", r"\bOEUVRE\b"]),
]


def detect_matiere(titre: str) -> Optional[str]:
    t = _norm(titre)
    for matiere, patterns in _MATIERE_RULES:
        for pat in patterns:
            if re.search(pat, t):
                return matiere
    return None


# ---------------------------------------------------------------------------
# Niveau scolaire — ordre = priorité (classes explicites avant examens)
# ---------------------------------------------------------------------------
_NIVEAU_RULES: list[tuple[str, str]] = [
    ("CP1", r"\bCP1\b"),
    ("CP2", r"\bCP2\b"),
    ("CE1", r"\bCE1\b"),
    ("CE2", r"\bCE2\b"),
    ("CM1", r"\bCM1\b"),
    ("CM2", r"\bCM2\b"),
    ("6e", r"\b6\s*(?:E|EME|IEME|ERE)\b|\b6E\b|\b6IEME\b"),
    ("5e", r"\b5\s*(?:E|EME|IEME)\b|\b5E\b"),
    ("4e", r"\b4\s*(?:E|EME|IEME)\b|\b4E\b"),
    ("3e", r"\b3\s*(?:E|EME|IEME)\b|\b3E\b"),
    ("2nde", r"\b2\s*(?:NDE|ND)\b|\bSECONDE\b"),
    ("1ère", r"\b1\s*(?:ERE|ERE)\b|\b1ERE\b|\bPREMIERE\b"),
    ("Terminale", r"\bTLE\b|\bTERMINALE\b"),
    # Examens -> niveau de la classe d'examen
    ("CM2", r"\bCEPE\b"),
    ("3e", r"\bBEPC\b"),
    ("Terminale", r"\bBAC\b"),
]


def detect_niveau(titre: str) -> Optional[str]:
    t = _norm(titre)
    for niveau, pat in _NIVEAU_RULES:
        if re.search(pat, t):
            return niveau
    return None


# ---------------------------------------------------------------------------
# Cycle & catégorie — dérivés du niveau (+ ajustements titre)
# ---------------------------------------------------------------------------
_NIVEAU_TO_CYCLE = {
    "CP1": ("Primaire", "primaire"), "CP2": ("Primaire", "primaire"),
    "CE1": ("Primaire", "primaire"), "CE2": ("Primaire", "primaire"),
    "CM1": ("Primaire", "primaire"), "CM2": ("Primaire", "primaire"),
    "6e": ("Collège", "premier_cycle"), "5e": ("Collège", "premier_cycle"),
    "4e": ("Collège", "premier_cycle"), "3e": ("Collège", "premier_cycle"),
    "2nde": ("Lycée", "second_cycle"), "1ère": ("Lycée", "second_cycle"),
    "Terminale": ("Lycée", "second_cycle"),
}


class Classification(TypedDict):
    matiere: Optional[str]
    niveau_scolaire: Optional[str]
    cycle: Optional[str]
    categorie: str


def classify(titre: str) -> Classification:
    """Classifie un article à partir de son titre."""
    t = _norm(titre)
    matiere = detect_matiere(titre)
    niveau = detect_niveau(titre)

    cycle: Optional[str] = None
    categorie: Optional[str] = None

    # Article transversal explicite : plage de niveaux dans le titre
    # ex. "(6e à Terminale)", "6E A TERMINALE", "6EME A TLE"
    is_transversal = bool(re.search(
        r"\b(6|6E|6EME)\b.*\bA\b.*(TERMINALE|TLE)|TOUS\s+NIVEAUX", t))

    # 1) Littérature/roman prime sur le reste pour la catégorie
    if matiere == "Littérature":
        cycle = "Littérature"
        categorie = "litterature"
    elif is_transversal:
        cycle = "Tous niveaux"
        categorie = "livre_commun"
        niveau = None  # pas de niveau unique
    elif niveau and niveau in _NIVEAU_TO_CYCLE:
        cycle, categorie = _NIVEAU_TO_CYCLE[niveau]
        # Prélecture/maternelle : CP1 mais œuvre maternelle
        if "PRELECTURE" in t:
            cycle = "Maternelle"
            categorie = "maternelle"
    else:
        # Pas de niveau détecté : indices d'examen direct
        if re.search(r"\bBEPC\b", t):
            cycle, categorie = "Collège", "premier_cycle"
            niveau = niveau or "3e"
        elif re.search(r"\bBAC\b", t):
            cycle, categorie = "Lycée", "second_cycle"
            niveau = niveau or "Terminale"

    # 2) Article transversal (Arts Plastiques / Musique 6e-Tle) => livre commun
    if categorie is None:
        if matiere in ("Arts Plastiques", "Éducation Musicale"):
            cycle = cycle or "Tous niveaux"
            categorie = "livre_commun"
        else:
            categorie = "livre_commun"

    return {
        "matiere": matiere,
        "niveau_scolaire": niveau,
        "cycle": cycle,
        "categorie": categorie,
    }


def enrich_product(doc: dict, *, override: bool = False) -> dict:
    """
    Renseigne matiere/cycle/niveau_scolaire/categorie dans un doc produit.
    Par défaut, ne remplit QUE les champs vides (préserve l'édition manuelle).
    Avec override=True, recalcule tout depuis le titre (backfill).
    """
    titre = doc.get("titre") or doc.get("designation") or ""
    c = classify(titre)
    for field in ("matiere", "cycle", "niveau_scolaire", "categorie"):
        val = c.get(field)
        if val is None:
            continue
        if override or not doc.get(field):
            doc[field] = val
    return doc
