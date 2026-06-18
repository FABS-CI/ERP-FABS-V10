"""
pdf_base.py — Base commune pour tous les générateurs PDF FABS V10

Ce module centralise les helpers partagés entre pdf_generator.py
et stock_pdf_generator.py pour éviter la duplication.

Usage:
    from pdf_base import (
        fmt, fmt_pct, fmt_date, fmt_heure,
        get_settings, get_logo, load_image_reader,
        draw_logo_4blocs, BRAND_COLORS
    )
"""
from __future__ import annotations

import os
import base64
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


# ── Couleurs FABS ──────────────────────────────────────────────────────────────

BRAND_COLORS = {
    "primary": colors.HexColor("#1B4F8A"),    # Bleu FABS
    "secondary": colors.HexColor("#E8F0FB"),  # Bleu clair
    "accent": colors.HexColor("#F0A500"),     # Or FABS
    "danger": colors.HexColor("#C0392B"),     # Rouge stock bas
    "warning": colors.HexColor("#F39C12"),    # Orange stock moyen
    "success": colors.HexColor("#27AE60"),    # Vert stock normal
    "text_dark": colors.HexColor("#1A1A2E"),  # Texte principal
    "text_grey": colors.HexColor("#7F8C8D"),  # Texte secondaire
    "border": colors.HexColor("#BDC3C7"),     # Bordures légères
    "white": colors.white,
}


# ── Formatters ─────────────────────────────────────────────────────────────────

def fmt(n) -> str:
    """Formate un nombre en monnaie XOF (ex: 1 500 000 FCFA)."""
    try:
        v = float(n or 0)
        return f"{v:,.0f} FCFA".replace(",", " ")
    except (ValueError, TypeError):
        return "0 FCFA"


def fmt_pct(n) -> str:
    """Formate un pourcentage (ex: 18,0%)."""
    try:
        return f"{float(n or 0):.1f}%"
    except (ValueError, TypeError):
        return "0,0%"


def fmt_date(raw: str) -> str:
    """Formate une date ISO en DD/MM/YYYY."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, AttributeError):
        return str(raw)[:10]


def fmt_heure(raw: str) -> str:
    """Formate une heure ISO en HH:MM."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return ""


def fmt_float(n, decimals: int = 0) -> str:
    """Formate un flottant avec un nombre de décimales donné."""
    try:
        return f"{float(n or 0):,.{decimals}f}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"


# ── Settings & Logo ────────────────────────────────────────────────────────────

def get_settings() -> Dict:
    """Récupère les paramètres de l'entreprise depuis l'env ou les valeurs par défaut."""
    return {
        "nom_entreprise": os.getenv("COMPANY_NAME", "Éditions FABS CI"),
        "adresse": os.getenv("COMPANY_ADDRESS", "Abidjan, Côte d'Ivoire"),
        "telephone": os.getenv("COMPANY_PHONE", "+225 27 00 00 00 00"),
        "email": os.getenv("COMPANY_EMAIL", "contact@editionsfabsci.com"),
        "site_web": os.getenv("COMPANY_WEBSITE", "www.editionsfabsci.com"),
        "numero_contribuable": os.getenv("COMPANY_TAX_ID", ""),
        "logo": os.getenv("COMPANY_LOGO_B64", ""),
    }


def get_logo(settings: Optional[Dict] = None) -> Optional[str]:
    """Retourne le logo en base64 ou None si absent."""
    if settings is None:
        settings = get_settings()
    logo_data = settings.get("logo", "")
    if logo_data and len(logo_data) > 100:
        return logo_data
    # Chemin fichier fallback
    logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def load_image_reader(logo_data: str) -> Optional[ImageReader]:
    """Convertit du base64 en ImageReader ReportLab."""
    if not logo_data:
        return None
    try:
        # Supprimer le préfixe data:image/...;base64, si présent
        if "," in logo_data:
            logo_data = logo_data.split(",", 1)[1]
        img_bytes = base64.b64decode(logo_data)
        return ImageReader(BytesIO(img_bytes))
    except Exception:
        return None


# ── Logo 4 blocs FABS ──────────────────────────────────────────────────────────

def draw_logo_4blocs(
    canvas,
    x: float,
    y: float,
    size: float,
    logo_colors: Tuple[str, str, str, str] = ("#1B4F8A", "#E8F0FB", "#F0A500", "#27AE60"),
) -> None:
    """Dessine le logo 4 blocs FABS (fallback si pas de logo image).
    
    Args:
        canvas: ReportLab canvas
        x, y: Position coin supérieur gauche
        size: Taille du carré total
        logo_colors: 4 couleurs pour les 4 quadrants
    """
    half = size / 2
    quadrants = [
        (x, y - half, logo_colors[0]),          # Bas-gauche
        (x + half, y - half, logo_colors[1]),   # Bas-droit
        (x, y, logo_colors[2]),                  # Haut-gauche
        (x + half, y, logo_colors[3]),           # Haut-droit
    ]
    for qx, qy, color_hex in quadrants:
        canvas.setFillColor(colors.HexColor(color_hex))
        canvas.rect(qx, qy, half, half, fill=1, stroke=0)
