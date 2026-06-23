"""
Module de génération PDF — EDITIONS FABS-CI.

Structure STRICTE conforme au document de référence :
  EN-TÊTE  : Logo 4-blocs (gris/rouge/bleu/orange) + Société+Adresse (gauche)
             Date + Heure + Titre document en bleu-gras-italique (droite)
             Ligne orange séparatrice

  CORPS    : Bloc client | Tableaux par cycle | Totaux + QR

  PIED     : Ligne orange haute
             Siège social centré (3 lignes)
             Banques centrées
             Ligne orange basse

8 thèmes disponibles via document_settings.selected_template
"""
from __future__ import annotations

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, Image,
)

# ═══════════════════════════════════════════════════════════════════
# CONSTANTES FABS-CI
# ═══════════════════════════════════════════════════════════════════
FABS_NAME  = "EDITIONS FABS-CI"
FABS_SLOGAN = "Une innovation pour une école de qualité"
FABS_ADDR  = "Adresse :  BP 693"
FABS_PHONE = "Phone : +225 0759737123"
FABS_EMAIL = "Email : edition693fabs@gmail.com"

FABS_SIEGE_L1 = "Siège social : Bingerville, Qt N'GOTTO, Immeuble cité Angan A. fils et petits-fils, Rez de chaussée. BP 693 TEL : 2122800995/"
FABS_SIEGE_L2 = "+225 0759737123 E-MAIL : edition693fabs@gmail.com"
FABS_SIEGE_L3 = "Bingerville .Banques : CORIS BANK : C116 01011 007630824101 34 ; SGBCI : CI008 01123012343259990 95."

PAGE_W, PAGE_H = A4
ML = 1.5 * cm
MR = 1.5 * cm
MT = 3.6 * cm   # topMargin (réservé en-tête)
MB = 2.6 * cm   # bottomMargin (réservé pied)

# ═══════════════════════════════════════════════════════════════════
# 8 THÈMES DE COULEURS
# Chaque thème = (primary, accent, header_text, table_header_bg, table_header_text)
# primary    = couleur principale (ligne séparatrice, logo dominant, pied)
# accent     = couleur secondaire (logo, détails)
# header_text= couleur du titre document (droite)
# table_hdr  = fond en-tête tableau
# table_txt  = texte en-tête tableau
# ═══════════════════════════════════════════════════════════════════
THEMES: Dict[str, Dict] = {
    "classique_professionnel": {
        "name": "Classique Professionnel",
        "primary":      colors.HexColor("#FF6200"),   # orange (pied de page)
        "accent":       colors.HexColor("#1F4E79"),   # bleu
        "title_color":  colors.HexColor("#1F4E79"),   # bleu (Facture Client)
        "table_hdr":    colors.HexColor("#5B8DB8"),   # bleu moyen (en-tête tableau, comme la facture)
        "table_txt":    colors.white,
        "logo_colors":  ("#888888", "#CC0000", "#0A2540", "#FF6200"),  # gris/rouge/bleu/orange
    },
    "moderne_bleu": {
        "name": "Moderne Bleu",
        "primary":      colors.HexColor("#2563EB"),
        "accent":       colors.HexColor("#1E40AF"),
        "title_color":  colors.HexColor("#1E40AF"),
        "table_hdr":    colors.HexColor("#2563EB"),
        "table_txt":    colors.white,
        "logo_colors":  ("#93C5FD", "#2563EB", "#1E40AF", "#BFDBFE"),
    },
    "premium": {
        "name": "Premium",
        "primary":      colors.HexColor("#B8860B"),   # or foncé
        "accent":       colors.HexColor("#1A1A2E"),   # noir profond
        "title_color":  colors.HexColor("#1A1A2E"),
        "table_hdr":    colors.HexColor("#1A1A2E"),
        "table_txt":    colors.HexColor("#B8860B"),
        "logo_colors":  ("#2C2C54", "#B8860B", "#FFD700", "#1A1A2E"),
    },
    "corporate_orange": {
        "name": "Corporate Orange",
        "primary":      colors.HexColor("#EA580C"),
        "accent":       colors.HexColor("#1C1917"),
        "title_color":  colors.HexColor("#1C1917"),
        "table_hdr":    colors.HexColor("#EA580C"),
        "table_txt":    colors.white,
        "logo_colors":  ("#1C1917", "#EA580C", "#FED7AA", "#78350F"),
    },
    "elegant_administratif": {
        "name": "Élégant Administratif",
        "primary":      colors.HexColor("#475569"),   # slate
        "accent":       colors.HexColor("#0F172A"),
        "title_color":  colors.HexColor("#0F172A"),
        "table_hdr":    colors.HexColor("#334155"),
        "table_txt":    colors.white,
        "logo_colors":  ("#64748B", "#0F172A", "#94A3B8", "#475569"),
    },
    "minimaliste_moderne": {
        "name": "Minimaliste Moderne",
        "primary":      colors.HexColor("#6366F1"),   # indigo
        "accent":       colors.HexColor("#111827"),
        "title_color":  colors.HexColor("#4F46E5"),
        "table_hdr":    colors.HexColor("#6366F1"),
        "table_txt":    colors.white,
        "logo_colors":  ("#E0E7FF", "#6366F1", "#4F46E5", "#C7D2FE"),
    },
    "premium_luxe": {
        "name": "Premium Luxe",
        "primary":      colors.HexColor("#7C3AED"),   # violet
        "accent":       colors.HexColor("#1E1B4B"),
        "title_color":  colors.HexColor("#1E1B4B"),
        "table_hdr":    colors.HexColor("#5B21B6"),
        "table_txt":    colors.HexColor("#FDE68A"),
        "logo_colors":  ("#DDD6FE", "#7C3AED", "#5B21B6", "#EDE9FE"),
    },
    "education_edition": {
        "name": "Éducation Édition",
        "primary":      colors.HexColor("#059669"),   # vert
        "accent":       colors.HexColor("#064E3B"),
        "title_color":  colors.HexColor("#064E3B"),
        "table_hdr":    colors.HexColor("#047857"),
        "table_txt":    colors.white,
        "logo_colors":  ("#A7F3D0", "#059669", "#064E3B", "#D1FAE5"),
    },
}

GREY = colors.HexColor("#6B7280")


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except Exception:
        return str(n)

def fmt_pct(n) -> str:
    try:
        return f"{float(n):.2f} %"
    except Exception:
        return str(n)

def fmt_date(raw: str) -> str:
    """ISO (2026-01-07) ou (2026-01-07T08:11) -> 07/01/2026."""
    if not raw:
        return ""
    d = raw[:10]
    try:
        y, m, day = d.split("-")
        return f"{day}/{m}/{y}"
    except Exception:
        return d

def fmt_heure(raw: str) -> str:
    if raw and len(raw) > 10:
        return raw[11:16]
    return datetime.now().strftime("%H:%M")

def _make_qr(data: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(data or FABS_NAME)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def _get_settings() -> Dict:
    """Charge logo + template depuis MongoDB."""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        doc = client["fabsci_erp"]["document_settings"].find_one({"_id": "default"}) or {}
        return doc
    except Exception:
        return {}

def _get_theme(doc_type: Optional[str] = None) -> Dict:
    """Retourne le thème actif (per-type ou global)."""
    settings = _get_settings()
    tpt = settings.get("template_per_type", {})
    tid = (tpt.get(doc_type) if doc_type else None) or settings.get("selected_template", "classique_professionnel")
    return THEMES.get(tid, THEMES["classique_professionnel"])

import os
_ASSET_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_fabs.png")

def _get_logo(settings: Optional[Dict] = None) -> Optional[str]:
    """Logo uploadé en priorité, sinon logo FABS-CI par défaut (asset embarqué)."""
    if settings is None:
        settings = _get_settings()
    uploaded = settings.get("logo_url")
    if uploaded:
        return uploaded
    # Fallback : logo officiel FABS-CI embarqué
    if os.path.exists(_ASSET_LOGO):
        return _ASSET_LOGO
    return None


# ═══════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════
_base = getSampleStyleSheet()
S_NORMAL = ParagraphStyle("s_n", parent=_base["Normal"], fontSize=8.5, leading=11)
S_BOLD   = ParagraphStyle("s_b", parent=S_NORMAL, fontName="Helvetica-Bold")
S_SMALL  = ParagraphStyle("s_s", parent=_base["Normal"], fontSize=7, leading=9)
S_CYCLE  = ParagraphStyle("s_c", parent=_base["Normal"], fontSize=9, fontName="Helvetica-Bold", leading=12)
S_FOOTER = ParagraphStyle("s_f", parent=_base["Normal"], fontSize=6.5, textColor=GREY,
                           alignment=TA_CENTER, leading=8.5)


# ═══════════════════════════════════════════════════════════════════
# EN-TÊTE CANVAS — structure STRICTE du modèle de référence
# ═══════════════════════════════════════════════════════════════════
def _draw_logo_4blocs(canvas, x: float, y: float, size: float, logo_colors: Tuple[str,str,str,str]):
    """
    Reproduit le logo FABS-CI : 4 carrés (2x2)
    TL=gris  TR=rouge
    BL=bleu  BR=orange  (tel que sur le modèle)
    """
    h = size / 2
    tl, tr, bl, br = logo_colors
    for col, ox, oy in [
        (tl, 0,  h),
        (tr, h,  h),
        (bl, 0,  0),
        (br, h,  0),
    ]:
        canvas.setFillColor(colors.HexColor(col))
        canvas.rect(x + ox, y + oy, h, h, fill=1, stroke=0)


def _load_image_reader(logo_data: str):
    """Accepte un chemin fichier OU une data-uri base64 et retourne un ImageReader."""
    try:
        # data-uri ou base64 brut
        if logo_data.startswith("data:") or (len(logo_data) > 200 and "/" not in logo_data[:50]):
            import base64
            raw = logo_data.split(",")[-1] if "," in logo_data else logo_data
            return ImageReader(BytesIO(base64.b64decode(raw)))
        # chemin fichier
        if os.path.exists(logo_data):
            return ImageReader(logo_data)
    except Exception:
        pass
    return None


def _draw_header(canvas, doc, title: str, date_str: str, heure_str: str,
                 theme: Dict, logo_data: Optional[str]):
    canvas.saveState()
    w, h = A4
    # PAS DE FOND DE COULEUR sur l'en-tête (fond blanc).

    LOGO_X = ML
    TOP_Y  = h - 0.85 * cm

    # ─── Logo (image réelle FABS-CI, ratio préservé) ──────────────
    LOGO_W = 1.7 * cm
    LOGO_H = 1.7 * cm
    LOGO_Y = h - 2.55 * cm
    reader = _load_image_reader(logo_data) if logo_data else None
    if reader is not None:
        try:
            iw, ih = reader.getSize()
            ratio = iw / ih if ih else 1
            draw_h = LOGO_H
            draw_w = draw_h * ratio
            if draw_w > LOGO_W * 1.6:
                draw_w = LOGO_W * 1.6
                draw_h = draw_w / ratio
            canvas.drawImage(reader, LOGO_X, LOGO_Y + (LOGO_H - draw_h) / 2,
                             width=draw_w, height=draw_h,
                             preserveAspectRatio=True, mask="auto")
            logo_right = LOGO_X + draw_w
        except Exception:
            _draw_logo_4blocs(canvas, LOGO_X, LOGO_Y, LOGO_H, theme["logo_colors"])
            logo_right = LOGO_X + LOGO_H
    else:
        _draw_logo_4blocs(canvas, LOGO_X, LOGO_Y, LOGO_H, theme["logo_colors"])
        logo_right = LOGO_X + LOGO_H

    TXT_X = logo_right + 0.4 * cm

    # ─── Nom société (noir, identique sur les 8 modèles) ──────────
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(TXT_X, TOP_Y, FABS_NAME)

    # ─── Slogan (italique, gris foncé) ──────────────────────────
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.drawString(TXT_X, TOP_Y - 0.30 * cm, FABS_SLOGAN)

    # ─── Adresse / Phone / Email (identique sur les 8 modèles) ────
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(TXT_X, TOP_Y - 0.70 * cm, FABS_ADDR)
    canvas.drawString(TXT_X, TOP_Y - 1.15 * cm, FABS_PHONE)
    canvas.drawString(TXT_X, TOP_Y - 1.60 * cm, FABS_EMAIL)

    # ─── Date + Heure (droite, noir) ──────────────────────────────
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - MR, TOP_Y,              date_str)
    canvas.drawRightString(w - MR, TOP_Y - 0.50 * cm, heure_str)

    # ─── Titre document (droite, couleur du thème, gras) ──────────
    canvas.setFillColor(theme["title_color"])
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawRightString(w - MR, TOP_Y - 1.45 * cm, title)

    # ─── Ligne séparatrice fine GRISE (comme la facture, pas de couleur)
    SEP_Y = h - MT + 0.05 * cm
    canvas.setStrokeColor(colors.HexColor("#9CA3AF"))
    canvas.setLineWidth(0.7)
    canvas.line(ML, SEP_Y, w - MR, SEP_Y)

    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════
# PIED DE PAGE CANVAS — structure STRICTE du modèle de référence
# ═══════════════════════════════════════════════════════════════════
def _draw_footer(canvas, doc, reference: str, theme: Dict,
                 show_qr: bool = True, signature_label: str = "La Comptabilité"):
    canvas.saveState()
    w, h = A4

    # Zone pied : de 0 à MB (2.6cm)
    # Ligne orange haute du pied
    LINE_TOP = MB - 0.1 * cm
    canvas.setStrokeColor(theme["primary"])
    canvas.setLineWidth(1.5)
    canvas.line(ML, LINE_TOP, w - MR, LINE_TOP)

    # 3 lignes texte siège (centrées, petit, gris)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(GREY)
    canvas.drawCentredString(w / 2, LINE_TOP - 0.38 * cm, FABS_SIEGE_L1)
    canvas.drawCentredString(w / 2, LINE_TOP - 0.72 * cm, FABS_SIEGE_L2)
    canvas.drawCentredString(w / 2, LINE_TOP - 1.06 * cm, FABS_SIEGE_L3)

    # Ligne orange basse du pied
    LINE_BOT = LINE_TOP - 1.25 * cm
    canvas.setStrokeColor(theme["primary"])
    canvas.setLineWidth(1.5)
    canvas.line(ML, LINE_BOT, w - MR, LINE_BOT)

    # ─── QR code : juste AU-DESSUS du pied (dans le corps) ────────
    if show_qr:
        qr_buf = _make_qr(f"FABS-CI | {reference}")
        canvas.drawImage(
            ImageReader(qr_buf),
            ML, LINE_TOP + 0.25 * cm,
            width=2.1 * cm, height=2.1 * cm,
            mask="auto",
        )

    # ─── Signature (droite, au-dessus du pied) ────────────────────
    canvas.setFont("Helvetica-BoldOblique", 9)
    canvas.setFillColor(theme["accent"])
    canvas.drawRightString(w - MR, LINE_TOP + 0.3 * cm, signature_label)

    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════
# CONSTRUCTION DU DOCUMENT
# ═══════════════════════════════════════════════════════════════════
def _build_doc(
    buffer: BytesIO, title: str, reference: str,
    date_str: str, heure_str: str,
    theme: Dict,
    logo_data: Optional[str] = None,
    show_qr: bool = True,
    signature_label: str = "La Comptabilité",
) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT, bottomMargin=MB,
        title=f"{title} {reference}",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  id="body", showBoundary=0)

    def on_page(c, d):
        _draw_header(c, d, title, date_str, heure_str, theme, logo_data)
        _draw_footer(c, d, reference, theme, show_qr=show_qr, signature_label=signature_label)

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    return doc


# ═══════════════════════════════════════════════════════════════════
# BLOC CLIENT  (conforme au modèle de référence)
# ═══════════════════════════════════════════════════════════════════
def _client_block(rows_data: List[List[str]], theme: Dict) -> Table:
    """
    Tableau 2 colonnes sans bordure lourde.
    Ligne séparatrice bas = couleur primary du thème.
    """
    rows = [[Paragraph(a, S_NORMAL), Paragraph(b, S_NORMAL)] for a, b in rows_data]
    t = Table(rows, colWidths=[9 * cm, 9.3 * cm])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.4, colors.HexColor("#9CA3AF")),
    ]))
    return t


def _client_rows_facture(facture: Dict, client: Dict) -> List[List[str]]:
    date_f   = fmt_date(facture.get("date_facture") or facture.get("created_at", ""))
    ref      = facture.get("reference", "-")
    repres   = facture.get("representant") or client.get("representant", "-")
    ph_rep   = client.get("telephone_representant") or client.get("phone_repre", "-")
    nom      = client.get("nom", "-")
    tel      = client.get("telephone", "-")
    mode     = facture.get("mode_paiement") or "Paiement à la livraison"
    return [
        [f"<b>Date :</b>          {date_f}", f"<b>Représentant : {repres}</b>"],
        [f"<b>Réf. Facture :</b>  {ref}",    f"<b>Phone Repre.  {ph_rep}</b>"],
        [f"<b>{nom}</b>",                     ""],
        [tel,                                  f"<b>{mode}</b>"],
    ]


# ═══════════════════════════════════════════════════════════════════
# TABLEAUX ARTICLES — groupés par cycle, conforme au modèle
# ═══════════════════════════════════════════════════════════════════
HDR_PRIX = ["Niveau", "Matière", "Code Article", "Désignation", "Qté", "Prix Unitaire", "Montant"]
HDR_NOPX = ["Niveau", "Matière", "Code Article", "Désignation", "Qté"]
COL_PRIX = [1.9*cm, 2.3*cm, 2.2*cm, 4.0*cm, 1.0*cm, 2.6*cm, 3.3*cm]
COL_NOPX = [2.4*cm, 2.8*cm, 2.8*cm, 7.5*cm, 1.6*cm]


# Libellés lisibles des cycles à partir de la catégorie produit
_CYCLE_LABELS = {
    "primaire":      "PRIMAIRE",
    "premier_cycle": "PREMIER CYCLE",
    "second_cycle":  "SECOND CYCLE",
    "litterature":   "LITTÉRATURE",
    "livre_commun":  "LIVRES COMMUNS",
}


def enrich_lignes_for_pdf(produits_by_id: Dict[str, Dict], lignes: List[Dict]) -> List[Dict]:
    """Enrichit chaque ligne de document de vente avec les vraies données produit.

    Mapping métier FABS-CI :
      - Code Article = produit.reference         (ex. FABS-CI79)
      - Niveau       = produit.niveau_scolaire   (ex. CP1, 6ème, Terminale)
      - Cycle (regroupement) = produit.categorie (primaire, premier_cycle, ...)
      - Désignation  = produit.titre (fallback designation de la ligne)
    Aucune mutation destructrice : on ne remplit que les champs manquants.
    """
    for l in lignes:
        pid = l.get("produit_id") or l.get("product_id")
        prod = produits_by_id.get(pid, {})
        if prod:
            l["code_article"] = prod.get("reference") or l.get("code_article") or ""
            l["niveau"] = prod.get("niveau_scolaire") or l.get("niveau") or ""
            l["matiere"] = prod.get("matiere") or l.get("matiere") or ""
            cat = prod.get("categorie") or ""
            l["cycle"] = _CYCLE_LABELS.get(cat, cat.replace("_", " ").upper() if cat else "")
            if not l.get("designation"):
                l["designation"] = prod.get("titre") or ""
        else:
            l.setdefault("code_article", "")
            l.setdefault("niveau", "")
            l.setdefault("matiere", "")
            l.setdefault("cycle", "")
    return lignes


def _articles_tables(lignes: List[Dict], include_prix: bool, theme: Dict) -> List:
    """Retourne une liste de flowables (titre cycle + table)."""
    # Grouper par cycle en conservant l'ordre d'insertion
    seen_cycles: List[str] = []
    cycles: Dict[str, List[Dict]] = {}
    for l in lignes:
        c = l.get("cycle") or l.get("classe_cycle") or ""
        if c not in cycles:
            seen_cycles.append(c)
            cycles[c] = []
        cycles[c].append(l)

    headers    = HDR_PRIX if include_prix else HDR_NOPX
    col_widths = COL_PRIX if include_prix else COL_NOPX
    flowables  = []

    stripe_odd  = colors.white
    stripe_even = colors.HexColor("#F0F4F8")

    for cycle_name in seen_cycles:
        items = cycles[cycle_name]

        if cycle_name:
            flowables.append(Spacer(1, 0.35 * cm))
            flowables.append(Paragraph(cycle_name, S_CYCLE))
            flowables.append(Spacer(1, 0.1 * cm))

        data = [headers]
        subtotal = 0.0
        for ligne in items:
            m = float(ligne.get("montant_ht", 0))
            subtotal += m
            row = [
                Paragraph(str(ligne.get("niveau") or ligne.get("classe") or ""), S_NORMAL),
                Paragraph(str(ligne.get("matiere") or ""), S_NORMAL),
                Paragraph(str(ligne.get("code_article") or ligne.get("produit_id", ""))[:16], S_NORMAL),
                Paragraph(str(ligne.get("designation", "")), S_NORMAL),
                Paragraph(str(int(ligne.get("quantite", 0))), S_NORMAL),
            ]
            if include_prix:
                row += [
                    Paragraph(fmt(ligne.get("prix_unitaire", 0)), S_NORMAL),
                    Paragraph(fmt(m), S_NORMAL),
                ]
            data.append(row)

        # Ligne sous-total par cycle (droite, gras) — comme dans le modèle
        if include_prix and cycle_name:
            empty = [Paragraph("", S_NORMAL)] * (len(headers) - 1)
            data.append(empty + [Paragraph(f"<b>{fmt(subtotal)}</b>", S_BOLD)])

        t = Table(data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            # En-tête tableau
            ("BACKGROUND",    (0, 0), (-1, 0), theme["table_hdr"]),
            ("TEXTCOLOR",     (0, 0), (-1, 0), theme["table_txt"]),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 8.5),
            ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
            # Corps
            ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [stripe_odd, stripe_even]),
        ])
        if include_prix:
            style.add("ALIGN", (3, 1), (-1, -1), "RIGHT")
        if include_prix and cycle_name:
            # fond sous-total
            style.add("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EEF2F7"))
            style.add("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold")
        t.setStyle(style)
        flowables.append(t)

    return flowables


# ═══════════════════════════════════════════════════════════════════
# TOTAUX — conforme au modèle de référence
# ═══════════════════════════════════════════════════════════════════
def _totaux_facture_table(
    total_vente: float, remise_pct: float, remise_montant: float,
    montant_ht: float, montant_paye: float, solde_du: float,
    theme: Dict,
) -> Table:
    rows = [
        [Paragraph("<b>Total Vente :</b>", S_BOLD),  Paragraph(fmt(total_vente),    S_BOLD)],
        [Paragraph("<b>% Remise :</b>",    S_BOLD),  Paragraph(fmt_pct(remise_pct), S_NORMAL)],
        [Paragraph("<b>Remise :</b>",      S_BOLD),  Paragraph(fmt(remise_montant), S_NORMAL)],
        [Paragraph("<b>Montant HT :</b>",  S_BOLD),  Paragraph(fmt(montant_ht),     S_BOLD)],
        [Paragraph("<b>Payé :</b>",        S_BOLD),  Paragraph(fmt(montant_paye) if montant_paye else "", S_NORMAL)],
        [Paragraph("<b>Solde dû :</b>",    S_BOLD),  Paragraph(fmt(solde_du),       S_BOLD)],
    ]
    t = Table(rows, colWidths=[4.5 * cm, 4.0 * cm], hAlign="RIGHT")
    t.setStyle(TableStyle([
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")),
        # Solde dû = dernière ligne, texte gras coloré (PAS de fond) comme la facture
        ("TEXTCOLOR",     (0, -1), (-1, -1), theme["title_color"]),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    return t


def _totaux_generic_table(
    montant_ht: float, remise: float,
    montant_tva: float, montant_ttc: float,
    theme: Dict,
) -> Table:
    rows = [
        [Paragraph("<b>Montant HT :</b>", S_BOLD),  Paragraph(fmt(montant_ht),  S_NORMAL)],
        [Paragraph("<b>Remise :</b>",      S_BOLD),  Paragraph(fmt(remise),      S_NORMAL)],
        [Paragraph("<b>TVA (18%) :</b>",   S_BOLD),  Paragraph(fmt(montant_tva), S_NORMAL)],
        [Paragraph("<b>TOTAL TTC :</b>",   S_BOLD),  Paragraph(fmt(montant_ttc), S_BOLD)],
    ]
    t = Table(rows, colWidths=[4.5 * cm, 4.0 * cm], hAlign="RIGHT")
    t.setStyle(TableStyle([
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
        ("BACKGROUND",    (0, -1), (-1, -1), theme["table_hdr"]),
        ("TEXTCOLOR",     (0, -1), (-1, -1), theme["table_txt"]),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    return t


def _bottom_block(left_text: str, totaux: Table, theme: Dict) -> Table:
    """Bloc bas : texte gauche (mode pmt) + totaux droite."""
    t = Table(
        [[Paragraph(f"<b>{left_text}</b>", S_BOLD), totaux]],
        colWidths=[9 * cm, 9.3 * cm],
    )
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════
# API PUBLIQUE
# ═══════════════════════════════════════════════════════════════════

def generate_facture_pdf(facture: Dict, lignes: List[Dict], client: Dict) -> BytesIO:
    """Facture Client / Avoir Client."""
    settings  = _get_settings()
    theme     = _get_theme("facture")
    logo_data = _get_logo(settings)

    is_avoir  = facture.get("type_facture") == "avoir"
    title     = "Avoir Client" if is_avoir else "Facture Client"
    reference = facture.get("reference", "—")
    raw_date  = facture.get("date_facture") or facture.get("created_at", "")
    date_str  = fmt_date(raw_date) if raw_date else ""
    heure_str = fmt_heure(raw_date) if raw_date else datetime.now().strftime("%H:%M")

    total_vente    = sum(float(l.get("montant_ht", 0)) for l in lignes)
    remise_pct     = float(facture.get("remise_globale", 0))
    remise_montant = round(total_vente * remise_pct / 100, 2)
    montant_ht     = round(total_vente - remise_montant, 2)
    montant_paye   = float(facture.get("montant_regle", 0))
    solde_du       = float(facture.get("montant_restant", montant_ht - montant_paye))

    buffer = BytesIO()
    doc = _build_doc(buffer, title, reference, date_str, heure_str, theme,
                     logo_data=logo_data, show_qr=True,
                     signature_label="La Comptabilité")

    mode_pmt = facture.get("mode_paiement") or "Paiement à la livraison"
    totaux   = _totaux_facture_table(total_vente, remise_pct, remise_montant,
                                     montant_ht, montant_paye, solde_du, theme)
    story: list = []
    story.append(_client_block(_client_rows_facture(facture, client), theme))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_articles_tables(lignes, include_prix=True, theme=theme))
    story.append(Spacer(1, 0.4 * cm))
    story.append(_bottom_block(mode_pmt, totaux, theme))
    if facture.get("notes"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Notes :</b> {facture['notes']}", S_NORMAL))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_proforma_pdf(facture: Dict, lignes: List[Dict], client: Dict) -> BytesIO:
    settings  = _get_settings()
    theme     = _get_theme("proforma")
    logo_data = _get_logo(settings)

    reference = facture.get("reference", "—")
    raw_date  = facture.get("date_facture") or facture.get("created_at", "")
    date_str  = fmt_date(raw_date) if raw_date else ""
    heure_str = fmt_heure(raw_date) if raw_date else datetime.now().strftime("%H:%M")

    total_vente    = sum(float(l.get("montant_ht", 0)) for l in lignes)
    remise_pct     = float(facture.get("remise_globale", 0))
    remise_montant = round(total_vente * remise_pct / 100, 2)
    montant_ht     = round(total_vente - remise_montant, 2)
    montant_paye   = float(facture.get("montant_regle", 0))
    solde_du       = montant_ht - montant_paye

    buffer = BytesIO()
    doc = _build_doc(buffer, "Facture Proforma", reference, date_str, heure_str, theme,
                     logo_data=logo_data, show_qr=True,
                     signature_label="La Comptabilité")

    repres = facture.get("representant") or client.get("representant", "-")
    rows = [
        [f"<b>Date :</b>            {date_str}",    f"<b>Représentant : {repres}</b>"],
        [f"<b>Réf. Proforma :</b>  {reference}",   "<b>Validité : 30 jours</b>"],
        [f"<b>{client.get('nom', '-')}</b>",         ""],
        [client.get("telephone", "-"),               "<b>À convenir</b>"],
    ]
    totaux = _totaux_facture_table(total_vente, remise_pct, remise_montant,
                                   montant_ht, montant_paye, solde_du, theme)
    story: list = []
    story.append(_client_block(rows, theme))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_articles_tables(lignes, include_prix=True, theme=theme))
    story.append(Spacer(1, 0.4 * cm))
    story.append(_bottom_block("Facture Proforma — non fiscale", totaux, theme))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_commande_pdf(commande: Dict, lignes: List[Dict], client: Dict) -> BytesIO:
    settings  = _get_settings()
    theme     = _get_theme("commande")
    logo_data = _get_logo(settings)

    reference = commande.get("reference", "—")
    raw_date  = commande.get("date_commande") or commande.get("created_at", "")
    date_str  = fmt_date(raw_date) if raw_date else ""
    heure_str = fmt_heure(raw_date) if raw_date else datetime.now().strftime("%H:%M")
    montant_ht  = float(commande.get("montant_ht",  commande.get("montant_total", 0)))
    montant_tva = float(commande.get("montant_tva", 0))
    montant_ttc = float(commande.get("montant_ttc", commande.get("montant_total", 0)))
    remise      = float(commande.get("remise_globale", 0))

    buffer = BytesIO()
    doc = _build_doc(buffer, "Bon de Commande", reference, date_str, heure_str, theme,
                     logo_data=logo_data, show_qr=True,
                     signature_label="La Comptabilité")

    repres = client.get("representant", "-")
    mode   = commande.get("mode_paiement", "À la livraison")
    statut = (commande.get("statut") or "-").upper()
    rows = [
        [f"<b>Date :</b>          {date_str}",     f"<b>Représentant : {repres}</b>"],
        [f"<b>Réf. Commande :</b> {reference}",   f"<b>Statut : {statut}</b>"],
        [f"<b>{client.get('nom', '-')}</b>",        ""],
        [client.get("telephone", "-"),              f"<b>{mode}</b>"],
    ]
    totaux = _totaux_generic_table(montant_ht, remise, montant_tva, montant_ttc, theme)
    story: list = []
    story.append(_client_block(rows, theme))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_articles_tables(lignes, include_prix=True, theme=theme))
    story.append(Spacer(1, 0.4 * cm))
    story.append(_bottom_block(mode, totaux, theme))
    if commande.get("notes"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Commentaires :</b> {commande['notes']}", S_NORMAL))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_bl_pdf(bl: Dict, lignes: List[Dict], client: Dict,
                    commande_ref: Optional[str] = None) -> BytesIO:
    settings  = _get_settings()
    theme     = _get_theme("bon_livraison")
    logo_data = _get_logo(settings)

    reference = bl.get("reference", "—")
    raw_date  = bl.get("date_livraison") or bl.get("created_at", "")
    date_str  = fmt_date(raw_date) if raw_date else ""
    heure_str = fmt_heure(raw_date) if raw_date else datetime.now().strftime("%H:%M")

    buffer = BytesIO()
    doc = _build_doc(buffer, "Bon de Livraison", reference, date_str, heure_str, theme,
                     logo_data=logo_data, show_qr=True,
                     signature_label="Signature du Réceptionnaire")

    bc_ref = commande_ref or bl.get("commande_ref", "-")
    repres = client.get("representant", "-")
    rows = [
        [f"<b>Date livraison :</b> {date_str}",  f"<b>BC N° : {bc_ref}</b>"],
        [f"<b>Réf. BL :</b>       {reference}", f"<b>Représentant : {repres}</b>"],
        [f"<b>{client.get('nom', '-')}</b>",      ""],
        [client.get("telephone", "-"),             ""],
    ]
    story: list = []
    story.append(_client_block(rows, theme))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_articles_tables(lignes, include_prix=False, theme=theme))
    if bl.get("notes"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Observations :</b> {bl['notes']}", S_NORMAL))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_retour_pdf(retour: Dict, lignes: List[Dict], client: Dict) -> BytesIO:
    settings  = _get_settings()
    theme     = _get_theme("bon_retour")
    logo_data = _get_logo(settings)

    reference = retour.get("reference", "—")
    raw_date  = retour.get("date_retour") or retour.get("created_at", "")
    date_str  = fmt_date(raw_date) if raw_date else ""
    heure_str = fmt_heure(raw_date) if raw_date else datetime.now().strftime("%H:%M")

    buffer = BytesIO()
    doc = _build_doc(buffer, "Bon de Retour", reference, date_str, heure_str, theme,
                     logo_data=logo_data, show_qr=True,
                     signature_label="Signature Réceptionnaire FABS-CI")

    repres = client.get("representant", "-")
    motif  = retour.get("motif", "-") or "-"
    rows = [
        [f"<b>Date retour :</b>  {date_str}",   f"<b>Motif : {motif}</b>"],
        [f"<b>Réf. Retour :</b>  {reference}",  f"<b>Représentant : {repres}</b>"],
        [f"<b>{client.get('nom', '-')}</b>",      ""],
        [client.get("telephone", "-"),             ""],
    ]
    story: list = []
    story.append(_client_block(rows, theme))
    story.append(Spacer(1, 0.4 * cm))
    story.extend(_articles_tables(lignes, include_prix=True, theme=theme))
    if retour.get("notes"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Observations :</b> {retour['notes']}", S_NORMAL))

    doc.build(story)
    buffer.seek(0)
    return buffer
