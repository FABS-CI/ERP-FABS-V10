"""
Génération PDF — État de Compte Clients FABS-CI
Thème : identique à stock_pdf_generator.py (bleu #1F4E79 + orange #FF6200)
Groupé par client : ville/zone + infos client + tableau factures
"""
from __future__ import annotations

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional
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

# Couleurs
C_ORANGE       = colors.HexColor("#FF6200")
C_BLUE         = colors.HexColor("#1F4E79")
C_BLUE_MED     = colors.HexColor("#5B8DB8")
C_GREY         = colors.HexColor("#6B7280")
C_RED          = colors.HexColor("#DC2626")
C_RED_LIGHT    = colors.HexColor("#FEE2E2")
C_GREEN        = colors.HexColor("#16A34A")
C_GREEN_LIGHT  = colors.HexColor("#DCFCE7")
C_ORANGE_LIGHT = colors.HexColor("#FFF7ED")
C_WHITE        = colors.white
C_LIGHT_GREY   = colors.HexColor("#F3F4F6")
LOGO_COLORS    = ("#888888", "#CC0000", "#0A2540", "#FF6200")

_ASSET_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_fabs.png")

FILTRE_LABELS = {
    "tous":    "Tous les comptes",
    "paye":    "Comptes soldés (payés)",
    "impaye":  "Comptes avec solde impayé",
}


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def _fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except Exception:
        return str(n) if n is not None else "0"


def _fmt_date(raw) -> str:
    if not raw:
        return "—"
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(raw)[:10]


def _get_logo() -> Optional[str]:
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        doc = client["fabsci_erp"]["document_settings"].find_one({"_id": "default"}) or {}
        uploaded = doc.get("logo_url")
        if uploaded:
            return uploaded
    except Exception:
        pass
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
    S_NORMAL  = ParagraphStyle("cc_n",  parent=_base["Normal"], fontSize=8.5, leading=11)
    S_BOLD    = ParagraphStyle("cc_b",  parent=_base["Normal"], fontSize=8.5,
                               fontName="Helvetica-Bold", leading=11)
    S_SMALL   = ParagraphStyle("cc_s",  parent=_base["Normal"], fontSize=7, leading=9)
    S_FOOTER  = ParagraphStyle("cc_f",  parent=_base["Normal"], fontSize=6.5,
                               textColor=C_GREY, alignment=TA_CENTER, leading=8.5)
    S_TITLE   = ParagraphStyle("cc_t",  parent=_base["Normal"], fontSize=13,
                               fontName="Helvetica-Bold", textColor=C_BLUE,
                               alignment=TA_RIGHT, leading=16)
    S_SUB     = ParagraphStyle("cc_sub", parent=_base["Normal"], fontSize=9,
                               textColor=C_GREY, alignment=TA_RIGHT, leading=11)
    S_CLIENT  = ParagraphStyle("cc_cli", parent=_base["Normal"], fontSize=9.5,
                               fontName="Helvetica-Bold", textColor=C_BLUE, leading=13)
    S_CLIENT_INFO = ParagraphStyle("cc_ci", parent=_base["Normal"], fontSize=8,
                               textColor=C_GREY, leading=10)
    S_TH      = ParagraphStyle("cc_th",  parent=_base["Normal"], fontSize=7.5,
                               fontName="Helvetica-Bold", textColor=C_WHITE,
                               alignment=TA_CENTER, leading=10)
    S_CELL    = ParagraphStyle("cc_cell",  parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_LEFT)
    S_CELL_C  = ParagraphStyle("cc_cellc", parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_CENTER)
    S_CELL_R  = ParagraphStyle("cc_cellr", parent=_base["Normal"], fontSize=7.5,
                               leading=10, alignment=TA_RIGHT)
    S_TOTAL   = ParagraphStyle("cc_tot",  parent=_base["Normal"], fontSize=8,
                               fontName="Helvetica-Bold", leading=11, alignment=TA_RIGHT)
    S_TOTAL_C = ParagraphStyle("cc_totc", parent=_base["Normal"], fontSize=8,
                               fontName="Helvetica-Bold", leading=11, alignment=TA_CENTER)
    S_TOTAL_L = ParagraphStyle("cc_totl", parent=_base["Normal"], fontSize=8,
                               fontName="Helvetica-Bold", leading=11, alignment=TA_LEFT)
    S_KPI_V   = ParagraphStyle("cc_kv", parent=_base["Normal"], fontSize=13,
                               fontName="Helvetica-Bold", textColor=C_BLUE,
                               alignment=TA_CENTER, leading=16)
    S_KPI_L   = ParagraphStyle("cc_kl", parent=_base["Normal"], fontSize=7.5,
                               textColor=C_GREY, alignment=TA_CENTER, leading=10)
    return (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
            S_CLIENT, S_CLIENT_INFO, S_TH, S_CELL, S_CELL_C, S_CELL_R,
            S_TOTAL, S_TOTAL_C, S_TOTAL_L, S_KPI_V, S_KPI_L)


# ══════════════════════════════════════════════════════════════════
# LOGO 4-BLOCS (canvas fallback)
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
def _draw_header(canvas, doc, date_str: str, heure_str: str,
                 logo_data: Optional[str], filtre: str, annee: str):
    canvas.saveState()
    w, h = A4

    LOGO_W = 1.7 * cm
    LOGO_H = 1.7 * cm
    LOGO_Y = h - 2.55 * cm
    LOGO_X = ML

    # Logo
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

    # Infos société (gauche)
    tx = LOGO_X + LOGO_W + 0.3 * cm
    ty = h - 1.1 * cm
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(C_BLUE)
    canvas.drawString(tx, ty, FABS_NAME)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_GREY)
    for i, line in enumerate([FABS_ADDR, FABS_PHONE, FABS_EMAIL]):
        canvas.drawString(tx, ty - (i + 1) * 0.38 * cm, line)

    # Titre + filtre (droite)
    rx = w - MR
    title_y = h - 1.0 * cm
    canvas.setFont("Helvetica-BoldOblique", 13)
    canvas.setFillColor(C_BLUE)
    canvas.drawRightString(rx, title_y, "ÉTAT DE COMPTE CLIENTS")

    filtre_label = FILTRE_LABELS.get(filtre, filtre)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_GREY)
    canvas.drawRightString(rx, title_y - 0.45 * cm, f"Filtre : {filtre_label}   —   Année : {annee}")
    canvas.drawRightString(rx, title_y - 0.82 * cm, f"Date : {date_str}   Heure : {heure_str}")

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

    fy = MB - 0.25 * cm
    canvas.setStrokeColor(C_ORANGE)
    canvas.setLineWidth(1.5)
    canvas.line(ML, fy, w - MR, fy)

    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(C_GREY)
    for i, line in enumerate([FABS_SIEGE_L1, FABS_SIEGE_L2, FABS_SIEGE_L3]):
        canvas.drawCentredString(w / 2, fy - 0.35 * cm - i * 0.32 * cm, line)

    canvas.setLineWidth(1)
    canvas.line(ML, 0.55 * cm, w - MR, 0.55 * cm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_GREY)
    canvas.drawRightString(w - MR, 0.62 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ══════════════════════════════════════════════════════════════════
# BLOC KPI GLOBAL
# ══════════════════════════════════════════════════════════════════
def _build_kpi_block(resume: Dict, styles) -> List:
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CLIENT, S_CLIENT_INFO, S_TH, S_CELL, S_CELL_C, S_CELL_R,
     S_TOTAL, S_TOTAL_C, S_TOTAL_L, S_KPI_V, S_KPI_L) = styles

    nb_clients    = resume.get("nb_clients", 0)
    nb_factures   = resume.get("nb_factures", 0)
    total_vente   = resume.get("total_vente", 0)
    total_regle   = resume.get("total_regle", 0)
    total_solde   = resume.get("total_solde", 0)

    kpis = [
        (_fmt(nb_clients),        "Clients"),
        (_fmt(nb_factures),       "Factures"),
        (_fmt(total_vente),       "Montant ventes (FCFA)"),
        (_fmt(total_regle),       "Total réglé (FCFA)"),
        (_fmt(total_solde),       "Solde restant (FCFA)"),
    ]

    usable = PAGE_W - ML - MR
    col_w = usable / 5

    row_vals = [Paragraph(v, S_KPI_V) for v, _ in kpis]
    row_lbls = [Paragraph(l, S_KPI_L) for _, l in kpis]

    kpi_table = Table(
        [row_vals, row_lbls],
        colWidths=[col_w] * 5,
        rowHeights=[0.7 * cm, 0.4 * cm],
    )
    kpi_table.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BLUE_MED),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_LIGHT_GREY),
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Solde en rouge si > 0
        ("TEXTCOLOR",     (4, 0), (4, 0), C_RED),
    ]))
    return [kpi_table, Spacer(1, 0.4 * cm)]


# ══════════════════════════════════════════════════════════════════
# TABLEAU FACTURES PAR CLIENT
# ══════════════════════════════════════════════════════════════════
def _build_client_block(client: Dict, factures: List[Dict], styles) -> List:
    """
    Construit le bloc KeepTogether pour un client :
      - Bandeau info client (ville/zone, nom, représentant, tél, type)
      - Tableau des factures
      - Ligne sous-total
    """
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CLIENT, S_CLIENT_INFO, S_TH, S_CELL, S_CELL_C, S_CELL_R,
     S_TOTAL, S_TOTAL_C, S_TOTAL_L, S_KPI_V, S_KPI_L) = styles

    usable = PAGE_W - ML - MR

    # ── Bandeau client ───────────────────────────────────────────
    nom          = client.get("nom") or "Client inconnu"
    ville        = client.get("ville") or client.get("zone") or "—"
    representant = client.get("representant") or "—"
    telephone    = client.get("telephone") or "—"
    type_client  = client.get("type_client") or "—"

    nom_para  = Paragraph(f"▶  {nom}", S_CLIENT)

    # Ligne infos en une seule rangée condensée
    info_text = (
        f"<b>Ville/Zone :</b> {ville}   "
        f"<b>Représentant :</b> {representant}   "
        f"<b>Tél :</b> {telephone}   "
        f"<b>Type :</b> {type_client}"
    )
    info_para = Paragraph(info_text, S_CLIENT_INFO)

    # ── Colonnes tableau ─────────────────────────────────────────
    # Num Fact | Date Livr. | Mtt Vente | Remise | Montant HT | Paiement | Solde
    col_widths = [
        usable * 0.14,   # Num Fact
        usable * 0.11,   # Date Livr.
        usable * 0.16,   # Mtt Vente
        usable * 0.10,   # Remise
        usable * 0.16,   # Montant HT
        usable * 0.16,   # Paiement
        usable * 0.17,   # Solde
    ]

    headers = ["Num Fact.", "Date Livr.", "Mtt Vente", "Remise", "Montant HT", "Paiement", "Solde"]
    header_row = [Paragraph(h, S_TH) for h in headers]

    rows = [header_row]
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), C_BLUE_MED),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
        ("ALIGN",         (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN",         (0, 1), (0, -1), "LEFT"),
        ("ALIGN",         (1, 1), (1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]

    sub_vente  = 0.0
    sub_remise = 0.0
    sub_ht     = 0.0
    sub_regle  = 0.0
    sub_solde  = 0.0

    for i, f in enumerate(factures, start=1):
        reference      = f.get("reference") or f.get("numero") or "—"
        date_livr      = _fmt_date(f.get("date_livraison") or f.get("date_facture"))
        mtt_vente      = float(f.get("montant_ttc") or f.get("montant_total") or 0)
        remise         = float(f.get("remise_globale") or f.get("remise") or 0)
        montant_ht     = float(f.get("montant_ht") or 0)
        paiement       = float(f.get("montant_regle") or 0)
        solde          = float(f.get("montant_restant") or (mtt_vente - paiement))

        # Coloration solde : rouge si impayé, vert si soldé
        solde_color = C_RED if solde > 0 else C_GREEN

        row = [
            Paragraph(str(reference)[:18], S_CELL),
            Paragraph(date_livr, S_CELL_C),
            Paragraph(_fmt(mtt_vente), S_CELL_R),
            Paragraph(_fmt(remise), S_CELL_R),
            Paragraph(_fmt(montant_ht), S_CELL_R),
            Paragraph(_fmt(paiement), S_CELL_R),
            Paragraph(_fmt(solde), S_CELL_R),
        ]
        rows.append(row)

        # Colorier le solde de la ligne
        style_cmds.append(("TEXTCOLOR", (6, i), (6, i), solde_color))
        if solde > 0:
            style_cmds.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))

        sub_vente  += mtt_vente
        sub_remise += remise
        sub_ht     += montant_ht
        sub_regle  += paiement
        sub_solde  += solde

    # ── Ligne sous-total client ──────────────────────────────────
    tot_row = [
        Paragraph("Sous-total", S_TOTAL_L),
        Paragraph(f"{len(factures)} fact.", S_TOTAL_C),
        Paragraph(_fmt(sub_vente),  S_TOTAL),
        Paragraph(_fmt(sub_remise), S_TOTAL),
        Paragraph(_fmt(sub_ht),     S_TOTAL),
        Paragraph(_fmt(sub_regle),  S_TOTAL),
        Paragraph(_fmt(sub_solde),  S_TOTAL),
    ]
    rows.append(tot_row)
    tot_idx = len(rows) - 1
    style_cmds += [
        ("BACKGROUND", (0, tot_idx), (-1, tot_idx), C_BLUE_MED),
        ("TEXTCOLOR",  (0, tot_idx), (-1, tot_idx), C_WHITE),
        ("FONTNAME",   (0, tot_idx), (-1, tot_idx), "Helvetica-Bold"),
        ("LINEABOVE",  (0, tot_idx), (-1, tot_idx), 0.8, C_BLUE),
    ]
    # Couleur solde sous-total
    if sub_solde > 0:
        style_cmds.append(("TEXTCOLOR", (6, tot_idx), (6, tot_idx), colors.HexColor("#FFCCCC")))

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))

    block = [
        Spacer(1, 0.25 * cm),
        nom_para,
        info_para,
        Spacer(1, 0.1 * cm),
        tbl,
    ]
    return block


# ══════════════════════════════════════════════════════════════════
# GRAND TOTAL GÉNÉRAL
# ══════════════════════════════════════════════════════════════════
def _build_grand_total(resume: Dict, styles) -> List:
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CLIENT, S_CLIENT_INFO, S_TH, S_CELL, S_CELL_C, S_CELL_R,
     S_TOTAL, S_TOTAL_C, S_TOTAL_L, S_KPI_V, S_KPI_L) = styles

    usable = PAGE_W - ML - MR
    col_widths = [
        usable * 0.14,
        usable * 0.11,
        usable * 0.16,
        usable * 0.10,
        usable * 0.16,
        usable * 0.16,
        usable * 0.17,
    ]

    S_GT = ParagraphStyle("cc_gt", parent=_base["Normal"], fontSize=9,
                          fontName="Helvetica-Bold", textColor=C_WHITE,
                          alignment=TA_CENTER, leading=12)
    S_GT_R = ParagraphStyle("cc_gtr", parent=_base["Normal"], fontSize=9,
                            fontName="Helvetica-Bold", textColor=C_WHITE,
                            alignment=TA_RIGHT, leading=12)
    S_GT_L = ParagraphStyle("cc_gtl", parent=_base["Normal"], fontSize=9,
                            fontName="Helvetica-Bold", textColor=C_WHITE,
                            alignment=TA_LEFT, leading=12)

    row = [
        Paragraph("TOTAL GÉNÉRAL", S_GT_L),
        Paragraph(f"{resume.get('nb_factures', 0)} fact.", S_GT),
        Paragraph(_fmt(resume.get("total_vente",  0)), S_GT_R),
        Paragraph(_fmt(resume.get("total_remise", 0)), S_GT_R),
        Paragraph(_fmt(resume.get("total_ht",     0)), S_GT_R),
        Paragraph(_fmt(resume.get("total_regle",  0)), S_GT_R),
        Paragraph(_fmt(resume.get("total_solde",  0)), S_GT_R),
    ]

    grand_tbl = Table([row], colWidths=col_widths)
    grand_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("LEFTPADDING",   (0, 0), (-1, 0), 4),
        ("RIGHTPADDING",  (0, 0), (-1, 0), 4),
        ("BOX",           (0, 0), (-1, 0), 1.5, C_ORANGE),
    ]))
    return [Spacer(1, 0.5 * cm), grand_tbl]


# ══════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════
def generate_etat_compte_clients_pdf(
    clients_data: List[Dict],
    resume: Dict,
    filtre: str = "tous",
    annee: Optional[str] = None,
) -> BytesIO:
    """
    Génère le PDF État de Compte Clients.

    Args:
        clients_data : liste de dicts, chacun contenant :
            - client : dict (id, nom, ville, representant, telephone, type_client)
            - factures : list de dicts (reference, date_facture, montant_ttc,
                         remise_globale, montant_ht, montant_regle, montant_restant)
        resume : dict KPI global (nb_clients, nb_factures, total_vente,
                 total_remise, total_ht, total_regle, total_solde)
        filtre : "tous" | "paye" | "impaye"
        annee  : année affichée dans l'en-tête (ex: "2025")

    Returns:
        BytesIO contenant le PDF prêt à streamer
    """
    logo_data = _get_logo()
    now = datetime.now()
    date_str  = now.strftime("%d/%m/%Y")
    heure_str = now.strftime("%H:%M")
    if annee is None:
        annee = str(now.year)

    styles = _make_styles()

    buf = BytesIO()

    # ─── PageTemplate ────────────────────────────────────────────
    def make_header_footer(canvas, doc):
        _draw_header(canvas, doc, date_str, heure_str, logo_data, filtre, annee)
        _draw_footer(canvas, doc)

    frame = Frame(ML, MB, PAGE_W - ML - MR, PAGE_H - MT - MB, id="main")
    template = PageTemplate(id="cc", frames=[frame], onPage=make_header_footer)
    doc = BaseDocTemplate(buf, pagesize=A4, pageTemplates=[template],
                          leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB)

    # ─── Styles ──────────────────────────────────────────────────
    (S_NORMAL, S_BOLD, S_SMALL, S_FOOTER, S_TITLE, S_SUB,
     S_CLIENT, S_CLIENT_INFO, S_TH, S_CELL, S_CELL_C, S_CELL_R,
     S_TOTAL, S_TOTAL_C, S_TOTAL_L, S_KPI_V, S_KPI_L) = styles

    story = []

    # Titre
    filtre_label = FILTRE_LABELS.get(filtre, filtre)
    story.append(Paragraph("État de Compte Clients", S_TITLE))
    story.append(Paragraph(f"{filtre_label}   —   Généré le {date_str} à {heure_str}", S_SUB))
    story.append(Spacer(1, 0.4 * cm))

    # KPI
    story += _build_kpi_block(resume, styles)

    # Blocs clients
    if clients_data:
        for entry in clients_data:
            client   = entry.get("client", {})
            factures = entry.get("factures", [])
            if not factures:
                continue
            block = _build_client_block(client, factures, styles)
            story.append(KeepTogether(block))
    else:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Aucun client trouvé pour ce filtre.", S_NORMAL))

    # Grand total
    story += _build_grand_total(resume, styles)

    doc.build(story)
    buf.seek(0)
    return buf
