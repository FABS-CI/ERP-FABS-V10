"""
Générateur PDF amélioré - Support des modèles personnalisés et filigranes
Intègre les 5 modèles de facture et le système de filigranes automatiques
Intègre le QR code FNE pour la certification DGI
"""
from __future__ import annotations

from io import BytesIO
from typing import Dict, List, Optional
import logging
import base64

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER

from document_templates import render_template, get_template
from document_settings_module import determine_watermark

logger = logging.getLogger("fabsci.pdf_generator_enhanced")


def add_watermark_to_pdf(pdf_buffer: BytesIO, watermark_text: str, 
                        color: str = "#FF0000", size: int = 48, 
                        opacity: float = 0.3, position: str = "center",
                        rotation: int = 45) -> BytesIO:
    """
    Ajoute un filigrane à un PDF existant
    
    Args:
        pdf_buffer: Buffer PDF existant
        watermark_text: Texte du filigrane
        color: Couleur du filigrane (hex)
        size: Taille de la police
        opacity: Opacité (0.1-1.0)
        position: Position (center, top_left, top_right, bottom_left, bottom_right)
        rotation: Rotation en degrés
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Créer un nouveau buffer pour le PDF avec filigrane
    output_buffer = BytesIO()
    
    # Lire le PDF existant
    from PyPDF2 import PdfReader, PdfWriter
    reader = PdfReader(pdf_buffer)
    writer = PdfWriter()
    
    # Pour chaque page, ajouter le filigrane
    for page in reader.pages:
        # Créer un canvas pour le filigrane
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # Configurer le filigrane
        can.saveState()
        can.setFillColorRGB(
            int(color[1:3], 16) / 255,
            int(color[3:5], 16) / 255,
            int(color[5:7], 16) / 255,
            alpha=opacity
        )
        can.setFont("Helvetica-Bold", size)
        
        # Calculer la position
        w, h = A4
        x, y = w / 2, h / 2
        
        if position == "top_left":
            x, y = 3 * cm, h - 5 * cm
        elif position == "top_right":
            x, y = w - 5 * cm, h - 5 * cm
        elif position == "bottom_left":
            x, y = 3 * cm, 3 * cm
        elif position == "bottom_right":
            x, y = w - 5 * cm, 3 * cm
        
        # Rotation
        can.translate(x, y)
        can.rotate(rotation)
        can.drawCentredString(0, 0, watermark_text)
        can.restoreState()
        
        can.save()
        
        # Fusionner le filigrane avec la page
        watermark = PdfReader(packet)
        page.merge_page(watermark.pages[0])
        writer.add_page(page)
    
    # Écrire le PDF final
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer


def add_fne_qr_code_to_pdf(pdf_buffer: BytesIO, fne_token: Optional[str] = None, 
                           fne_reference: Optional[str] = None) -> BytesIO:
    """
    Ajoute le QR code FNE au PDF en bas de page, côté droit
    
    Args:
        pdf_buffer: Buffer PDF existant
        fne_token: URL de vérification DGI (token)
        fne_reference: Référence officielle DGI de la facture
        
    Returns:
        BytesIO: Buffer PDF avec QR code FNE ajouté
    """
    if not fne_token:
        # Si pas certifiée, ajouter un texte "Certification en cours"
        return add_watermark_to_pdf(
            pdf_buffer,
            "Certification en cours — réf. en attente",
            color="#FFA500",
            size=24,
            opacity=0.2,
            position="bottom_right",
            rotation=0
        )
    
    # Générer le QR code
    import qrcode
    from io import BytesIO as BytesIOQR
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(fne_token)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIOQR()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_data = qr_buffer.read()
    
    # Créer un nouveau buffer pour le PDF avec QR code
    output_buffer = BytesIO()
    
    # Lire le PDF existant
    from PyPDF2 import PdfReader, PdfWriter
    reader = PdfReader(pdf_buffer)
    writer = PdfWriter()
    
    # Pour chaque page, ajouter le QR code en bas à droite
    for page in reader.pages:
        # Créer un canvas pour le QR code
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # Dimensions de la page
        w, h = A4
        
        # Position du QR code (bas à droite)
        qr_size = 2.5 * cm
        x = w - qr_size - 1 * cm
        y = 1 * cm
        
        # Ajouter l'image QR code
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(BytesIOQR(qr_data))
        can.drawImage(img_reader, x, y, width=qr_size, height=qr_size, mask='auto')
        
        # Ajouter la référence DGI sous le QR code
        can.setFont("Helvetica-Bold", 8)
        can.setFillColorRGB(0, 0, 0)
        can.drawCentredString(x + qr_size/2, y - 0.3 * cm, fne_reference or "")
        
        # Ajouter la mention légale
        can.setFont("Helvetica", 6)
        can.setFillColorRGB(0.3, 0.3, 0.3)
        can.drawCentredString(x + qr_size/2, y - 0.6 * cm, "Facture Normalisée Électronique")
        can.drawCentredString(x + qr_size/2, y - 0.8 * cm, "DGI Côte d'Ivoire")
        
        can.save()
        
        # Fusionner le QR code avec la page
        qr_page = PdfReader(packet)
        page.merge_page(qr_page.pages[0])
        writer.add_page(page)
    
    # Écrire le PDF final
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer


def generate_pdf_with_template(
    document_type: str,
    document_data: Dict,
    client_data: Dict,
    articles: List[Dict],
    template_id: str = "classique_professionnel",
    watermark_settings: Optional[Dict] = None,
    company_info: Optional[Dict] = None,
    fne_token: Optional[str] = None,
    fne_reference: Optional[str] = None
) -> BytesIO:
    """
    Génère un PDF en utilisant le template sélectionné et les filigranes automatiques
    
    Args:
        document_type: Type de document (facture, proforma, commande, bl, avoir)
        document_data: Données du document
        client_data: Données du client
        articles: Liste des articles
        template_id: ID du template à utiliser
        watermark_settings: Paramètres du filigrane
        company_info: Informations de l'entreprise
        fne_token: URL de vérification DGI (token)
        fne_reference: Référence officielle DGI de la facture
    """
    # Informations entreprise par défaut
    if not company_info:
        company_info = {
            "nom": "EDITIONS FABS-CI",
            "adresse": "BP 693",
            "telephone": "+225 07 59 73 71 23",
            "email": "edition693fabs@gmail.com",
            "siege_social": "Bingerville, Quartier N'GOTTO, Immeuble cité Angan A. fils et petits-fils, Rez-de-chaussée",
            "banques": {
                "CORIS BANK": "C116 01011 007630824101 34",
                "SGBCI": "CI008 01123012343259990 95"
            }
        }
    
    # Déterminer le titre du document
    document_titles = {
        "facture": "FACTURE CLIENT",
        "proforma": "FACTURE PROFORMA",
        "commande": "BON DE COMMANDE",
        "bl": "BON DE LIVRAISON",
        "avoir": "AVOIR CLIENT"
    }
    document_title = document_titles.get(document_type, "DOCUMENT")
    
    # Déterminer le filigrane automatique
    statut = document_data.get("statut", "")
    montant_regle = document_data.get("montant_regle", 0)
    montant_total = document_data.get("montant_ttc", document_data.get("montant_total", 0))
    
    watermark_text = determine_watermark(document_type, statut, montant_regle, montant_total)
    
    # Rendre le template HTML
    html_content = render_template(
        template_id=template_id,
        document_title=document_title,
        reference=document_data.get("reference", ""),
        date_str=document_data.get("date_facture") or document_data.get("date_commande") or document_data.get("created_at", "")[:10],
        company_info=company_info,
        client_info=client_data,
        articles=articles,
        totals={
            "montant_ht": document_data.get("montant_ht", 0),
            "montant_tva": document_data.get("montant_tva", 0),
            "montant_ttc": document_data.get("montant_ttc", 0),
            "remise_globale": document_data.get("remise_globale", 0)
        },
        logo_html=""  # Sera ajouté depuis les paramètres si disponible
    )
    
    # Convertir HTML en PDF
    try:
        import weasyprint
        pdf_buffer = BytesIO()
        weasyprint.HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
    except ImportError:
        # Fallback: utiliser ReportLab si weasyprint n'est pas disponible
        logger.warning("WeasyPrint non disponible, utilisation du générateur ReportLab de base")
        from pdf_generator import generate_facture_pdf
        pdf_buffer = generate_facture_pdf(document_data, articles, client_data)
    
    # Ajouter le filigrane si nécessaire
    if watermark_text and watermark_settings and watermark_settings.get("enabled", True):
        pdf_buffer = add_watermark_to_pdf(
            pdf_buffer=pdf_buffer,
            watermark_text=watermark_text,
            color=watermark_settings.get("color", "#FF0000"),
            size=watermark_settings.get("size", 48),
            opacity=watermark_settings.get("opacity", 0.3),
            position=watermark_settings.get("position", "center"),
            rotation=watermark_settings.get("rotation", 45)
        )
    
    # Ajouter le QR code FNE si disponible (uniquement pour les factures)
    if document_type == "facture" and fne_token:
        pdf_buffer = add_fne_qr_code_to_pdf(
            pdf_buffer=pdf_buffer,
            fne_token=fne_token,
            fne_reference=fne_reference
        )
    
    return pdf_buffer


async def get_document_settings(db) -> Optional[Dict]:
    """Récupérer les paramètres de documents depuis la base de données"""
    try:
        settings = await db.document_settings.find_one({"_id": "default"})
        if settings:
            settings.pop("_id", None)
            return settings
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres de documents: {e}")
    return None


async def generate_pdf_with_settings(
    db,
    document_type: str,
    document_data: Dict,
    client_data: Dict,
    articles: List[Dict],
    fne_token: Optional[str] = None,
    fne_reference: Optional[str] = None
) -> BytesIO:
    """
    Génère un PDF en utilisant les paramètres de documents configurés
    
    Cette fonction est le point d'entrée principal pour la génération de PDF
    avec les modèles personnalisés et filigranes automatiques.
    """
    # Récupérer les paramètres de documents
    settings = await get_document_settings(db)
    
    # Utiliser les paramètres ou les valeurs par défaut
    template_id = settings.get("selected_template", "classique_professionnel") if settings else "classique_professionnel"
    watermark_settings = settings.get("watermark_settings", {}) if settings else {}
    company_info = settings.get("company_info", {}) if settings else {}
    logo_url = settings.get("logo_url", None) if settings else None
    
    # Générer le PDF
    pdf_buffer = generate_pdf_with_template(
        document_type=document_type,
        document_data=document_data,
        client_data=client_data,
        articles=articles,
        template_id=template_id,
        watermark_settings=watermark_settings,
        company_info=company_info,
        fne_token=fne_token,
        fne_reference=fne_reference
    )
    
    return pdf_buffer
