"""
Génération PDF — État des Stocks FABS-CI
Thème : classique_professionnel (orange #FF6200 + bleu #1F4E79)
Pattern identique à pdf_generator.py
"""
from __future__ import annotations

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

# ══════════════════════════════════════════════════════════════════
# CONSTANTES FABS-CI
# ══════════════════════════════════════════════════════════════════
FABS_NAME  = "EDITIONS FABS-CI"
FABS_ADDR  = "Adresse :  BP 693"
FABS_PHONE = "Phone : +225 0759737123"
FABS_EMAIL = "Email : edition693fabs@gmail.com"

FABS_SIEGE_L1 = (
    "Siège social : Bingerville, Qt N'GOTTO, Immeuble cité Angan A. fils et petits-fils, "
    "Rez de chaussée. BP 693 TEL : 2122800995/"
)
FABS_SIEGE_L2 = "+225 0759737123 E-MAIL : edition693fabs@gmail.com"
FABS_SIEGE_L3 = (
    "Bingerville .Banques : CORIS BANK : C116 01011 007630824101 34 ; "
    "SGBCI : CI008 01123012343259990 95."
)

PAGE_W, PAGE_H = A4
ML = 1.5 * cm
MR = 1.5 * cm
MT = 3.6 * cm
MB = 2.6 * cm

# Couleurs thème classique_professionnel
C_ORANGE  = colors.HexColor("#FF6200")
C_BLUE    = colors.HexColor("#1F4E79")
C_BLUE_MED = colors.HexColor("#5B8DB8")
C_GREY    = colors.HexColor("#6B7280")
C_RED     = colors.HexColor("#DC2626")
C_RED_LIGHT = colors.HexColor("#FEE2E2")
C_ORANGE_LIGHT = colors.HexColor("#FFF7ED")
C_GREEN   = colors.HexColor("#16A34A")
C_GREEN_LIGHT = colors.HexColor("#DCFCE7")
C_WHITE   = colors.white
C_LIGHT_GREY = colors.HexColor("#F3F4F6")
LOGO_COLORS = ("#888888", "#CC0000", "#0A2540", "#FF6200")

_ASSET_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_fabs.png")

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def _fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except Exception:
        return str(n) if n is not None else "0"

def _fmt_float(n, decimals=0) -> str:
    try:
        v = round(float(n), decimals)
        if decimals == 0:
            return f"{int(v):,}".replace(",", " ")
        return f"{v:,.{decimals}f}".replace(",", " ")
    except Exception:
        return "0"

def _get_settings() -> Dict:
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        doc = client["fabsci_erp"]["document_settings"].find_one({"_id": "default"}) or {}
        return doc
    except Exception:
        return {}

def _get_logo(settings: Optional[Dict] = None) -> Optional[str]:
    if settings is None:
        settings = _get_settings()
    uploaded = settings.get("logo_url")
    if uploaded:
        return uploaded
    if os.path.exists(_ASSET_LOGO):
        return _ASSET_LOGO
    return None

def _load_image_reader(logo_data: str):
    try:
        if logo_data.startswith("data:") or (len(logo_data) > 200 and "/" not in logo_data[:50]):
            import base64
            raw = logo_data.split(",")[-1] if "," in logo_data else logo_data
            return ImageReader(BytesIO(base64.b64decode(raw)))
        if os.path.exists(logo_data):
            return ImageReader(logo_data)
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════
_base = getSampleStyleSheet()

def _make_styles():
    S_NORMAL = ParagraphStyle("st_n", parent=_base["Normal"], fontSize=8.5, leading=11)
    S_BOLD   = ParagraphStyle("st_b", parent=S_NORMAL, fontName="Helvetica-Bold")
    S_SMALL  = ParagraphStyle("st_s", parent=_base["Normal"], fontSize=7, leading=9)
    S_FOOTER = ParagraphStyle("st_f", parent=_base["Normal"], fontSize=6.5,
                               textColor=C_GREY, alignment=TA_CENTER, leading=8.5)
    S_TITLE  = ParagraphStyle("st_t", parent=_base["Normal"], fontSize=13,
                               fontName="Helvetica-Bold", textColor=C_BLUE,
                               alignment=TA_RIGHT, leading=16)
    S_SUB    = ParagraphStyle("st_sub", parent=_base["Normal"], fontSize=9,
                               textColor=C_GREY, alignment=TA_RIGHT, leading=11)
    S_CAT    = ParagraphStyle("st_cat", parent=_base["Normal"], fontSize=9,
                               fontName="Helvetica-Bold", textColor=C_BLUE, leading=12)
    S_KPI_V  = ParagraphStyle("st_kv", parent=_base["Normal"], fontSize=14,
                               fontName="Helvetica-Bold", textColor=C_BLUE,
                               alignment=TA_CENTER, leading=17)
    S_KPI_L  = ParagraphStyle("st_kl", parent=_base["Normal"], fontSize=7.5,
                               textColor=C_GREY, alignment=TA_CENTER, leading=10)
    S_TH     = ParagraphStyle("st_th", parent=_base["Normal"], fontSize=7.5,
                               fontName="Helvetica-Bold", textColor=C_WHITE,
                               alignment=TA_CENTER, leading=10)
    S_CELL   = ParagraphStyle("st_cell", parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_LEFT)
    S_CELL_C = ParagraphStyle("st_cellc", parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_CENTER)
    S_CELL_R = ParagraphStyle("st_cellr", parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_RIGHT)
    S_TOTAL  = ParagraphStyle("st_tot", parent=_base["Normal"], fontSize=8,
                               fontName="Helvetica-Bold", leading=11, alignment=TA_RIGHT)
    S_TOTAL_C = ParagraphStyle("st_totc", parent=_base["Normal"], fontSize=8,
                               fontName="Helvetica-Bold", leading=11, alignment=TA_CENTER)
    return (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
            S_CAT, S_KPI_V, S_KPI_L, S_TH, S_CELL, S_CELL_C, S_CELL_R, S_TOTAL, S_TOTAL_C)


# ══════════════════════════════════════════════════════════════════
# LOGO 4-BLOCS (canvas)
# ══════════════════════════════════════════════════════════════════
def _draw_logo_4blocs(canvas, x, y, size, logo_colors):
    h = size / 2
    tl, tr, bl, br = logo_colors
    for col, ox, oy in [(tl, 0, h), (tr, h, h), (bl, 0, 0), (br, h, 0)]:
        canvas.setFillColor(colors.HexColor(col))
        canvas.rect(x + ox, y + oy, h, h, fill=1, stroke=0)


# ══════════════════════════════════════════════════════════════════
# EN-TÊTE CANVAS
# ══════════════════════════════════════════════════════════════════
def _draw_header(canvas, doc, date_str: str, heure_str: str, logo_data: Optional[str],
                 categorie: Optional[str] = None):
    canvas.saveState()
    w, h = A4

    LOGO_W = 1.7 * cm
    LOGO_H = 1.7 * cm
    LOGO_Y = h - 2.55 * cm
    LOGO_X = ML

    # Logo image ou 4-blocs
    reader = _load_image_reader(logo_data) if logo_data else None
    if reader is not None:
        try:
            iw, ih = reader.getSize()
            ratio = min(LOGO_W / iw, LOGO_H / ih)
            dw, dh = iw * ratio, ih * ratio
            canvas.drawImage(reader, LOGO_X, LOGO_Y + (LOGO_H - dh) / 2, dw, dh,
                             preserveAspectRatio=True, mask="auto")
        except Exception:
            _draw_logo_4blocs(canvas, LOGO_X, LOGO_Y, LOGO_W, LOGO_COLORS)
    else:
        _draw_logo_4blocs(canvas, LOGO_X, LOGO_Y, LOGO_W, LOGO_COLORS)

    # Texte société (gauche)
    tx = LOGO_X + LOGO_W + 0.3 * cm
    ty = h - 1.1 * cm
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(C_BLUE)
    canvas.drawString(tx, ty, FABS_NAME)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_GREY)
    for i, line in enumerate([FABS_ADDR, FABS_PHONE, FABS_EMAIL]):
        canvas.drawString(tx, ty - (i + 1) * 0.38 * cm, line)

    # Titre + date (droite)
    rx = w - MR
    title_y = h - 1.0 * cm
    title_text = "ÉTAT DES STOCKS"
    if categorie:
        title_text += f" — {categorie.upper()}"
    canvas.setFont("Helvetica-BoldOblique", 13)
    canvas.setFillColor(C_BLUE)
    canvas.drawRightString(rx, title_y, title_text)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_GREY)
    canvas.drawRightString(rx, title_y - 0.45 * cm, f"Date : {date_str}   Heure : {heure_str}")
    canvas.drawRightString(rx, title_y - 0.82 * cm, "EDITIONS FABS-CI — Inventaire produits")

    # Ligne séparatrice orange
    sep_y = h - MT + 0.15 * cm
    canvas.setStrokeColor(C_ORANGE)
    canvas.setLineWidth(2)
    canvas.line(ML, sep_y, w - MR, sep_y)

    canvas.restoreState()


# ══════════════════════════════════════════════════════════════════
# PIED DE PAGE CANVAS
# ══════════════════════════════════════════════════════════════════
def _draw_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Ligne orange haute
    fy = MB - 0.25 * cm
    canvas.setStrokeColor(C_ORANGE)
    canvas.setLineWidth(1.5)
    canvas.line(ML, fy, w - MR, fy)

    # Texte pied
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(C_GREY)
    lines = [FABS_SIEGE_L1, FABS_SIEGE_L2, FABS_SIEGE_L3]
    for i, line in enumerate(lines):
        canvas.drawCentredString(w / 2, fy - 0.35 * cm - i * 0.32 * cm, line)

    # Ligne orange basse
    canvas.setLineWidth(1)
    canvas.line(ML, 0.55 * cm, w - MR, 0.55 * cm)

    # Numéro page
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_GREY)
    canvas.drawRightString(w - MR, 0.62 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ══════════════════════════════════════════════════════════════════
# BLOC KPI
# ══════════════════════════════════════════════════════════════════
def _build_kpi_block(resume: Dict, styles) -> List:
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CAT, S_KPI_V, S_KPI_L, S_TH, S_CELL, S_CELL_C, S_CELL_R, S_TOTAL, S_TOTAL_C) = styles

    # Accepte plusieurs noms de clés (compatibilité endpoint)
    total_refs = resume.get("total_references") or resume.get("nb_references") or 0
    total_qty  = resume.get("total_quantite") or resume.get("quantite_totale") or 0
    ruptures   = resume.get("ruptures") or resume.get("nb_ruptures") or 0
    alertes    = resume.get("alertes") or resume.get("nb_alertes") or 0
    valeur     = resume.get("valeur_totale") or resume.get("valeur_totale_fcfa") or 0

    kpis = [
        (_fmt(total_refs), "Références"),
        (_fmt(total_qty), "Qté totale"),
        (_fmt(ruptures), "Ruptures"),
        (_fmt(alertes), "Alertes seuil"),
        (_fmt_float(valeur), "Valeur totale (FCFA)"),
    ]

    cells = []
    for val, lbl in kpis:
        cells.append([
            Paragraph(val, S_KPI_V),
            Paragraph(lbl, S_KPI_L),
        ])

    # 5 colonnes égales
    usable = PAGE_W - ML - MR
    col_w = usable / 5

    tbl = Table([
        [Table([[v, l]], colWidths=[col_w - 0.4 * cm], rowHeights=None) for v, l in
         [(Paragraph(val, S_KPI_V), Paragraph(lbl, S_KPI_L)) for val, lbl in kpis]]
    ], colWidths=[col_w] * 5)

    # Rebuild plus simple : une seule ligne, 5 blocs
    row_vals = [Paragraph(v, S_KPI_V) for v, _ in kpis]
    row_lbls = [Paragraph(l, S_KPI_L) for _, l in kpis]

    kpi_table = Table(
        [row_vals, row_lbls],
        colWidths=[col_w] * 5,
        rowHeights=[0.7 * cm, 0.4 * cm],
    )
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BLUE_MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, C_LIGHT_GREY),
        ("BACKGROUND", (0, 0), (-1, 0), C_LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Ruptures en rouge
        ("TEXTCOLOR", (2, 0), (2, 0), C_RED),
        # Alertes en orange
        ("TEXTCOLOR", (3, 0), (3, 0), C_ORANGE),
    ]))
    return [kpi_table, Spacer(1, 0.35 * cm)]


# ══════════════════════════════════════════════════════════════════
# TABLEAU PRODUITS
# ══════════════════════════════════════════════════════════════════
def _statut_produit(stock: int, seuil: int) -> Tuple[str, object, object]:
    """Retourne (texte_statut, bg_color, text_color)"""
    if stock == 0:
        return "RUPTURE", C_RED_LIGHT, C_RED
    if stock <= seuil:
        return "ALERTE", C_ORANGE_LIGHT, C_ORANGE
    return "OK", C_GREEN_LIGHT, C_GREEN


def _build_produits_table(produits: List[Dict], styles) -> List:
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CAT, S_KPI_V, S_KPI_L, S_TH, S_CELL, S_CELL_C, S_CELL_R, S_TOTAL, S_TOTAL_C) = styles

    usable = PAGE_W - ML - MR
    # Colonnes : Titre | Catég | Niveau | Matière | Stock | Seuil | Prix vente | Valeur | Statut
    col_widths = [
        usable * 0.22,  # Titre
        usable * 0.09,  # Catégorie
        usable * 0.07,  # Niveau
        usable * 0.08,  # Matière
        usable * 0.07,  # Stock
        usable * 0.06,  # Seuil
        usable * 0.11,  # Prix vente
        usable * 0.13,  # Valeur stock
        usable * 0.08,  # Statut (réduit)
        usable * 0.09,  # Ref (ajout pour padding)
    ]
    # Recalcul à 9 colonnes
    col_widths = [
        usable * 0.23,  # Titre
        usable * 0.09,  # Catégorie
        usable * 0.07,  # Niveau
        usable * 0.08,  # Matière
        usable * 0.065, # Stock
        usable * 0.06,  # Seuil
        usable * 0.115, # Prix vente
        usable * 0.12,  # Valeur stock
        usable * 0.075, # Statut
    ]

    headers = ["Titre", "Catégorie", "Niveau", "Matière", "Stock", "Seuil",
               "Prix vente", "Valeur stock", "Statut"]
    header_row = [Paragraph(h, S_TH) for h in headers]

    # Grouper par catégorie
    cats: Dict[str, List] = {}
    for p in produits:
        cat = p.get("categorie") or "—"
        cats.setdefault(cat, []).append(p)

    all_elements = []
    grand_total_qty = 0
    grand_total_val = 0.0
    grand_total_refs = 0

    for cat_name in sorted(cats.keys()):
        cat_produits = cats[cat_name]
        # Titre catégorie
        cat_title = Paragraph(f"▶  {cat_name}", S_CAT)
        all_elements.append(Spacer(1, 0.2 * cm))

        rows = [header_row]
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_BLUE_MED),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ALIGN", (4, 1), (-1, -1), "CENTER"),
            ("ALIGN", (0, 1), (3, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        sub_qty = 0
        sub_val = 0.0

        for i, p in enumerate(cat_produits, start=1):
            stock = int(p.get("stock_actuel") or p.get("quantite_stock") or 0)
            seuil = int(p.get("seuil_alerte") or p.get("stock_minimum") or 0)
            prix = float(p.get("prix_vente") or p.get("prix") or 0)
            valeur = stock * prix
            statut_txt, bg, fg = _statut_produit(stock, seuil)

            titre = (p.get("titre") or p.get("nom") or "—")[:45]
            niveau = (p.get("niveau") or p.get("classe") or "—")[:12]
            matiere = (p.get("matiere") or "—")[:12]

            row = [
                Paragraph(titre, S_CELL),
                Paragraph(cat_name[:14], S_CELL_C),
                Paragraph(niveau, S_CELL_C),
                Paragraph(matiere, S_CELL_C),
                Paragraph(_fmt(stock), S_CELL_C),
                Paragraph(_fmt(seuil), S_CELL_C),
                Paragraph(_fmt_float(prix), S_CELL_R),
                Paragraph(_fmt_float(valeur), S_CELL_R),
                Paragraph(statut_txt, S_CELL_C),
            ]
            rows.append(row)

            # Colorier la ligne selon statut
            if statut_txt == "RUPTURE":
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), C_RED_LIGHT))
                style_cmds.append(("TEXTCOLOR", (8, i), (8, i), C_RED))
                style_cmds.append(("FONTNAME", (8, i), (8, i), "Helvetica-Bold"))
            elif statut_txt == "ALERTE":
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), C_ORANGE_LIGHT))
                style_cmds.append(("TEXTCOLOR", (8, i), (8, i), C_ORANGE))
                style_cmds.append(("FONTNAME", (8, i), (8, i), "Helvetica-Bold"))
            else:
                style_cmds.append(("TEXTCOLOR", (8, i), (8, i), C_GREEN))

            sub_qty += stock
            sub_val += valeur

        # Ligne total catégorie
        tot_row = [
            Paragraph(f"Sous-total {cat_name}", S_TOTAL),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph(_fmt(sub_qty), S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph(_fmt_float(sub_val), S_TOTAL),
            Paragraph(f"{len(cat_produits)} réf.", S_TOTAL_C),
        ]
        rows.append(tot_row)
        tot_row_idx = len(rows) - 1
        style_cmds += [
            ("BACKGROUND", (0, tot_row_idx), (-1, tot_row_idx), C_BLUE_MED),
            ("TEXTCOLOR", (0, tot_row_idx), (-1, tot_row_idx), C_WHITE),
            ("FONTNAME", (0, tot_row_idx), (-1, tot_row_idx), "Helvetica-Bold"),
            ("LINEABOVE", (0, tot_row_idx), (-1, tot_row_idx), 0.8, C_BLUE),
        ]

        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(style_cmds))
        all_elements.append(KeepTogether([cat_title, tbl]))

        grand_total_qty += sub_qty
        grand_total_val += sub_val
        grand_total_refs += len(cat_produits)

    # ─── Grand total ───────────────────────────────────────────────
    all_elements.append(Spacer(1, 0.4 * cm))
    grand_data = [
        [
            Paragraph("TOTAL GÉNÉRAL", S_TOTAL),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph(_fmt(grand_total_qty), S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph("", S_TOTAL_C),
            Paragraph(_fmt_float(grand_total_val), S_TOTAL),
            Paragraph(f"{grand_total_refs} réf.", S_TOTAL_C),
        ]
    ]
    grand_tbl = Table(grand_data, colWidths=col_widths)
    grand_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (7, 0), (7, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("LEFTPADDING", (0, 0), (-1, 0), 4),
        ("RIGHTPADDING", (0, 0), (-1, 0), 4),
        ("BOX", (0, 0), (-1, 0), 1.5, C_ORANGE),
    ]))
    all_elements.append(grand_tbl)

    return all_elements


# ══════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════
def generate_etat_stock_pdf(produits: List[Dict], resume: Dict,
                             categorie: Optional[str] = None) -> BytesIO:
    """
    Génère le PDF état des stocks.

    Args:
        produits : liste de dicts produits (champs : titre, categorie, niveau,
                   matiere, stock_actuel, seuil_alerte, prix_vente)
        resume   : dict résumé KPI (total_references, total_quantite, ruptures,
                   alertes, valeur_totale)
        categorie: filtre catégorie affiché dans le titre (optionnel)

    Returns:
        BytesIO contenant le PDF
    """
    settings = _get_settings()
    logo_data = _get_logo(settings)

    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    heure_str = now.strftime("%H:%M")

    styles = _make_styles()

    buf = BytesIO()

    # ─── PageTemplate ────────────────────────────────────────────
    def make_header_footer(canvas, doc):
        _draw_header(canvas, doc, date_str, heure_str, logo_data, categorie)
        _draw_footer(canvas, doc)

    frame = Frame(ML, MB, PAGE_W - ML - MR, PAGE_H - MT - MB, id="main")
    template = PageTemplate(id="stock", frames=[frame], onPage=make_header_footer)
    doc = BaseDocTemplate(buf, pagesize=A4, pageTemplates=[template],
                          leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB)

    # ─── Contenu ─────────────────────────────────────────────────
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CAT, S_KPI_V, S_KPI_L, S_TH, S_CELL, S_CELL_C, S_CELL_R, S_TOTAL, S_TOTAL_C) = styles

    story = []

    # Titre section
    titre_label = "État des stocks"
    if categorie:
        titre_label += f" — {categorie}"
    story.append(Paragraph(titre_label, S_TITLE))
    story.append(Paragraph(f"Généré le {date_str} à {heure_str}", S_SUB))
    story.append(Spacer(1, 0.4 * cm))

    # KPI
    story += _build_kpi_block(resume, styles)
    story.append(Spacer(1, 0.3 * cm))

    # Tableau produits
    if produits:
        story += _build_produits_table(produits, styles)
    else:
        story.append(Paragraph("Aucun produit trouvé.", S_NORMAL))

    doc.build(story)
    buf.seek(0)
    return buf
