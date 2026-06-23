"""
Templates de documents PDF - 5 modèles de facture pour ERP FABS-CI
Chaque modèle utilise une mise en page et des couleurs différentes
"""
from typing import Dict, List, Optional
from datetime import datetime


# ============================================================================
# MODÈLE 1: CLASSIQUE PROFESSIONNEL
# ============================================================================
TEMPLATE_1_CLASSIQUE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Helvetica', Arial, sans-serif; font-size: 11px; color: #333; }
        .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .logo-section { flex: 1; }
        .logo { max-width: 120px; max-height: 80px; }
        .company-info { margin-top: 10px; }
        .company-name { font-size: 16px; font-weight: bold; color: #0A2540; }
        .company-slogan { font-size: 8px; color: #666; font-style: italic; margin-top: 3px; }
        .company-details { font-size: 9px; color: #666; line-height: 1.4; }
        .invoice-info { text-align: right; flex: 1; }
        .invoice-title { font-size: 24px; font-weight: bold; color: #FF6200; margin-bottom: 10px; }
        .invoice-number { font-size: 14px; font-weight: bold; color: #0A2540; }
        .invoice-date { font-size: 11px; color: #333; }
        .client-section { background: #F8FAFC; padding: 15px; border: 1px solid #0A2540; margin-bottom: 20px; }
        .client-title { font-weight: bold; color: #0A2540; margin-bottom: 10px; }
        .client-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .client-label { font-weight: bold; color: #0A2540; }
        .table-container { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #0A2540; color: white; padding: 10px; text-align: left; font-weight: bold; }
        td { padding: 8px; border-bottom: 1px solid #D1D5DB; }
        .totals { float: right; width: 300px; margin-top: 20px; }
        .total-row { display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #D1D5DB; }
        .total-final { background: #FF6200; color: white; font-weight: bold; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #6B7280; padding: 10px; border-top: 1px solid #D1D5DB; }
        .signature { position: fixed; bottom: 3cm; right: 2cm; width: 150px; height: 80px; border: 1px solid #0A2540; }
        .signature-label { text-align: center; font-size: 8px; color: #0A2540; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-section">
            {logo_html}
            <div class="company-info">
                <div class="company-name">{company_name}</div>
                <div class="company-slogan">{company_slogan}</div>
                <div class="company-details">
                    {company_address}<br>
                    {company_phone}<br>
                    {company_email}
                </div>
            </div>
        </div>
        <div class="invoice-info">
            <div class="invoice-title">{document_title}</div>
            <div class="invoice-number">N° {reference}</div>
            <div class="invoice-date">{date_str}</div>
        </div>
    </div>
    
    <div class="client-section">
        <div class="client-title">CLIENT</div>
        <div class="client-grid">
            <div><span class="client-label">Nom :</span> {client_nom}</div>
            <div><span class="client-label">Type :</span> {client_type}</div>
            <div><span class="client-label">Ville :</span> {client_ville}</div>
            <div><span class="client-label">Tél. :</span> {client_telephone}</div>
            <div><span class="client-label">Adresse :</span> {client_adresse}</div>
            <div><span class="client-label">Représentant :</span> {client_representant}</div>
        </div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Niveau</th>
                    <th>Matière</th>
                    <th>Code Article</th>
                    <th>Désignation</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix Unitaire</th>
                    <th style="text-align: right;">Montant</th>
                </tr>
            </thead>
            <tbody>
                {articles_rows}
            </tbody>
        </table>
    </div>
    
    <div class="totals">
        <div class="total-row"><span>Montant HT</span><span>{montant_ht}</span></div>
        <div class="total-row"><span>Remise globale</span><span>{remise_globale}</span></div>
        <div class="total-row"><span>TVA (18%)</span><span>{montant_tva}</span></div>
        <div class="total-row total-final"><span>TOTAL TTC</span><span>{montant_ttc}</span></div>
    </div>
    
    <div class="signature">
        <div class="signature-label">Signature & Cachet</div>
    </div>
    
    <div class="footer">
        {siege_social}<br>
        {banques}
    </div>
</body>
</html>
"""


# ============================================================================
# MODÈLE 2: MODERNE BLEU
# ============================================================================
TEMPLATE_2_MODERNE_BLEU = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Helvetica', Arial, sans-serif; font-size: 11px; color: #333; }
        .header { text-align: center; margin-bottom: 30px; }
        .header-banner { background: linear-gradient(135deg, #0A2540 0%, #2563EB 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .logo { max-width: 100px; max-height: 70px; margin: 0 auto; display: block; }
        .company-name { font-size: 18px; font-weight: bold; color: white; margin-top: 10px; }
        .company-slogan { font-size: 10px; color: #E5E7EB; font-style: italic; margin-top: 5px; }
        .invoice-title { font-size: 28px; font-weight: bold; color: #0A2540; margin: 20px 0; }
        .invoice-card { background: #F8FAFC; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #0A2540; }
        .invoice-label { font-weight: bold; color: #0A2540; font-size: 10px; text-transform: uppercase; }
        .invoice-value { font-size: 14px; color: #333; }
        .client-card { background: #EFF6FF; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #2563EB; }
        .client-title { font-size: 16px; font-weight: bold; color: #0A2540; margin-bottom: 15px; }
        .client-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .table-container { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #0A2540; color: white; padding: 12px; text-align: left; font-weight: bold; }
        td { padding: 10px; border-bottom: 1px solid #E5E7EB; }
        tr:hover { background: #F3F4F6; }
        .totals-block { background: #0A2540; color: white; padding: 20px; border-radius: 8px; float: right; width: 350px; margin-top: 20px; }
        .total-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.2); }
        .total-final { font-size: 18px; font-weight: bold; margin-top: 10px; padding-top: 10px; border-top: 2px solid #FF6200; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #6B7280; padding: 15px; background: #F8FAFC; }
    </style>
</head>
<body>
    <div class="header-banner">
        {logo_html}
        <div class="company-name">{company_name}</div>
        <div class="company-slogan">{company_slogan}</div>
    </div>
    
    <div class="header">
        <div class="invoice-title">{document_title}</div>
    </div>
    
    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
        <div class="invoice-card" style="flex: 1;">
            <div class="invoice-label">Référence</div>
            <div class="invoice-value">{reference}</div>
        </div>
        <div class="invoice-card" style="flex: 1;">
            <div class="invoice-label">Date</div>
            <div class="invoice-value">{date_str}</div>
        </div>
    </div>
    
    <div class="client-card">
        <div class="client-title">INFORMATIONS CLIENT</div>
        <div class="client-grid">
            <div><strong>Nom :</strong> {client_nom}</div>
            <div><strong>Type :</strong> {client_type}</div>
            <div><strong>Ville :</strong> {client_ville}</div>
            <div><strong>Tél. :</strong> {client_telephone}</div>
            <div><strong>Adresse :</strong> {client_adresse}</div>
            <div><strong>Représentant :</strong> {client_representant}</div>
        </div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Niveau</th>
                    <th>Matière</th>
                    <th>Code Article</th>
                    <th>Désignation</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix Unitaire</th>
                    <th style="text-align: right;">Montant</th>
                </tr>
            </thead>
            <tbody>
                {articles_rows}
            </tbody>
        </table>
    </div>
    
    <div class="totals-block">
        <div class="total-row"><span>Montant HT</span><span>{montant_ht}</span></div>
        <div class="total-row"><span>Remise globale</span><span>{remise_globale}</span></div>
        <div class="total-row"><span>TVA (18%)</span><span>{montant_tva}</span></div>
        <div class="total-row total-final"><span>TOTAL TTC</span><span>{montant_ttc}</span></div>
    </div>
    
    <div class="footer">
        {siege_social} | {banques}
    </div>
</body>
</html>
"""


# ============================================================================
# MODÈLE 3: PREMIUM
# ============================================================================
TEMPLATE_3_PREMIUM = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 2.5cm; }
        body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 11px; color: #333; }
        .header { text-align: center; margin-bottom: 40px; }
        .logo { max-width: 120px; max-height: 90px; margin: 0 auto 20px; display: block; }
        .company-name { font-size: 22px; font-weight: bold; color: #0A2540; letter-spacing: 2px; }
        .company-slogan { font-size: 11px; color: #6B7280; font-style: italic; margin-top: 5px; }
        .company-divider { width: 100px; height: 3px; background: #FF6200; margin: 15px auto; }
        .invoice-block { text-align: center; border: 3px double #0A2540; padding: 30px; margin: 30px auto; max-width: 400px; }
        .invoice-title { font-size: 26px; font-weight: bold; color: #FF6200; margin-bottom: 10px; }
        .invoice-number { font-size: 16px; color: #0A2540; font-weight: bold; }
        .invoice-date { font-size: 12px; color: #6B7280; margin-top: 5px; }
        .client-section { text-align: center; margin: 30px 0; }
        .client-title { font-size: 14px; font-weight: bold; color: #0A2540; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
        .client-info { font-size: 12px; line-height: 1.8; }
        .table-container { margin: 30px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: linear-gradient(to right, #0A2540, #FF6200); color: white; padding: 15px; text-align: left; font-weight: bold; text-transform: uppercase; font-size: 10px; }
        td { padding: 12px; border-bottom: 1px solid #E5E7EB; }
        .totals-elegant { border: 2px solid #0A2540; padding: 25px; float: right; width: 320px; margin-top: 30px; background: linear-gradient(135deg, #FF6200 0%, #0A2540 100%); }
        .total-row { display: flex; justify-content: space-between; padding: 12px 0; color: white; }
        .total-final { font-size: 20px; font-weight: bold; margin-top: 15px; padding-top: 15px; border-top: 2px solid white; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 9px; color: #6B7280; padding: 15px; border-top: 2px solid #0A2540; background: #F8FAFC; }
    </style>
</head>
<body>
    <div class="header">
        {logo_html}
        <div class="company-name">{company_name}</div>
        <div class="company-slogan">{company_slogan}</div>
        <div class="company-divider"></div>
    </div>
    
    <div class="invoice-block">
        <div class="invoice-title">{document_title}</div>
        <div class="invoice-number">N° {reference}</div>
        <div class="invoice-date">{date_str}</div>
    </div>
    
    <div class="client-section">
        <div class="client-title">Informations Client</div>
        <div class="client-info">
            <strong>{client_nom}</strong> - {client_type}<br>
            {client_adresse} - {client_ville}<br>
            Tél: {client_telephone}<br>
            Représentant: {client_representant}
        </div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Niveau</th>
                    <th>Matière</th>
                    <th>Code Article</th>
                    <th>Désignation</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix Unitaire</th>
                    <th style="text-align: right;">Montant</th>
                </tr>
            </thead>
            <tbody>
                {articles_rows}
            </tbody>
        </table>
    </div>
    
    <div class="totals-elegant">
        <div class="total-row"><span>Montant HT</span><span>{montant_ht}</span></div>
        <div class="total-row"><span>Remise globale</span><span>{remise_globale}</span></div>
        <div class="total-row"><span>TVA (18%)</span><span>{montant_tva}</span></div>
        <div class="total-row total-final"><span>TOTAL TTC</span><span>{montant_ttc}</span></div>
    </div>
    
    <div class="footer">
        {siege_social} | {banques}
    </div>
</body>
</html>
"""


# ============================================================================
# MODÈLE 4: CORPORATE ORANGE
# ============================================================================
TEMPLATE_4_CORPORATE_ORANGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Arial', sans-serif; font-size: 11px; color: #333; }
        .header-banner { background: #FF6200; padding: 20px; margin-bottom: 20px; }
        .header-content { display: flex; justify-content: space-between; align-items: center; }
        .logo { max-width: 100px; max-height: 70px; }
        .company-name { font-size: 18px; font-weight: bold; color: white; }
        .company-slogan { font-size: 9px; color: #FFE4CC; font-style: italic; display: block; margin-top: 5px; }
        .invoice-ref { font-size: 16px; font-weight: bold; color: white; }
        .client-section { background: #F3F4F6; padding: 20px; margin-bottom: 20px; }
        .client-title { font-size: 14px; font-weight: bold; color: #FF6200; margin-bottom: 15px; }
        .client-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .table-container { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #FF6200; color: white; padding: 12px; text-align: left; font-weight: bold; }
        td { padding: 10px; border-bottom: 1px solid #D1D5DB; }
        tr:nth-child(even) { background: #F9FAFB; }
        .totals-orange { background: #FF6200; color: white; padding: 20px; float: right; width: 320px; margin-top: 20px; }
        .total-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.3); }
        .total-final { font-size: 18px; font-weight: bold; margin-top: 10px; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #6B7280; padding: 12px; background: #F3F4F6; border-top: 2px solid #FF6200; }
    </style>
</head>
<body>
    <div class="header-banner">
        <div class="header-content">
            <div style="display: flex; align-items: center; gap: 15px;">
                {logo_html}
                <div>
                    <div class="company-name">{company_name}</div>
                    <div class="company-slogan">{company_slogan}</div>
                </div>
            </div>
            <div class="invoice-ref">N° {reference}</div>
        </div>
    </div>
    
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 24px; font-weight: bold; color: #FF6200;">{document_title}</div>
        <div style="font-size: 12px; color: #6B7280; margin-top: 5px;">{date_str}</div>
    </div>
    
    <div class="client-section">
        <div class="client-title">CLIENT</div>
        <div class="client-grid">
            <div><strong>Nom :</strong> {client_nom}</div>
            <div><strong>Type :</strong> {client_type}</div>
            <div><strong>Ville :</strong> {client_ville}</div>
            <div><strong>Tél. :</strong> {client_telephone}</div>
            <div><strong>Adresse :</strong> {client_adresse}</div>
            <div><strong>Représentant :</strong> {client_representant}</div>
        </div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Niveau</th>
                    <th>Matière</th>
                    <th>Code Article</th>
                    <th>Désignation</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix Unitaire</th>
                    <th style="text-align: right;">Montant</th>
                </tr>
            </thead>
            <tbody>
                {articles_rows}
            </tbody>
        </table>
    </div>
    
    <div class="totals-orange">
        <div class="total-row"><span>Montant HT</span><span>{montant_ht}</span></div>
        <div class="total-row"><span>Remise globale</span><span>{remise_globale}</span></div>
        <div class="total-row"><span>TVA (18%)</span><span>{montant_tva}</span></div>
        <div class="total-row total-final"><span>TOTAL TTC</span><span>{montant_ttc}</span></div>
    </div>
    
    <div class="footer">
        {siege_social} | {banques}
    </div>
</body>
</html>
"""


# ============================================================================
# MODÈLE 5: ÉLÉGANT ADMINISTRATIF
# ============================================================================
TEMPLATE_5_ELEGANT_ADMINISTRATIF = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Times New Roman', serif; font-size: 11px; color: #333; }
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
        .logo-section { flex: 1; }
        .logo { max-width: 100px; max-height: 80px; }
        .invoice-number { text-align: right; font-size: 18px; font-weight: bold; color: #DC2626; }
        .columns { display: flex; gap: 30px; margin-bottom: 30px; }
        .column { flex: 1; }
        .column-title { font-size: 12px; font-weight: bold; color: #0A2540; text-transform: uppercase; border-bottom: 2px solid #0A2540; padding-bottom: 5px; margin-bottom: 15px; }
        .column-content { font-size: 10px; line-height: 1.6; }
        .table-container { margin: 30px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #0A2540; color: white; padding: 15px; text-align: left; font-weight: bold; }
        td { padding: 12px; border-bottom: 1px solid #D1D5DB; }
        .totals-box { border: 3px solid #0A2540; padding: 25px; float: right; width: 340px; margin-top: 30px; }
        .total-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #D1D5DB; }
        .total-final { font-size: 18px; font-weight: bold; color: #DC2626; margin-top: 15px; padding-top: 15px; border-top: 2px solid #DC2626; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #6B7280; padding: 15px; border-top: 2px solid #0A2540; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-section">
            {logo_html}
        </div>
        <div class="invoice-number">
            {document_title}<br>
            <span style="font-size: 14px; color: #333;">N° {reference}</span>
        </div>
    </div>
    
    <div class="columns">
        <div class="column">
            <div class="column-title">Coordonnées Société</div>
            <div class="column-content">
                <strong>{company_name}</strong><br>
                <em style="font-size: 9px; color: #6B7280;">{company_slogan}</em><br>
                {company_address}<br>
                {company_phone}<br>
                {company_email}
            </div>
        </div>
        <div class="column">
            <div class="column-title">Informations Client</div>
            <div class="column-content">
                <strong>{client_nom}</strong> ({client_type})<br>
                {client_adresse}<br>
                {client_ville}<br>
                Tél: {client_telephone}<br>
                Représentant: {client_representant}
            </div>
        </div>
    </div>
    
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 12px; color: #6B7280;">Date: {date_str}</div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Niveau</th>
                    <th>Matière</th>
                    <th>Code Article</th>
                    <th>Désignation</th>
                    <th style="text-align: center;">Qté</th>
                    <th style="text-align: right;">Prix Unitaire</th>
                    <th style="text-align: right;">Montant</th>
                </tr>
            </thead>
            <tbody>
                {articles_rows}
            </tbody>
        </table>
    </div>
    
    <div class="totals-box">
        <div class="total-row"><span>Montant HT</span><span>{montant_ht}</span></div>
        <div class="total-row"><span>Remise globale</span><span>{remise_globale}</span></div>
        <div class="total-row"><span>TVA (18%)</span><span>{montant_tva}</span></div>
        <div class="total-row total-final"><span>TOTAL TTC</span><span>{montant_ttc}</span></div>
    </div>
    
    <div class="footer">
        {siege_social} | {banques}
    </div>
</body>
</html>
"""


# ============================================================================
# Fonction de sélection de template
# ============================================================================
def get_template(template_id: str) -> str:
    """Retourne le template HTML correspondant à l'ID"""
    templates = {
        "classique_professionnel": TEMPLATE_1_CLASSIQUE,
        "moderne_bleu": TEMPLATE_2_MODERNE_BLEU,
        "premium": TEMPLATE_3_PREMIUM,
        "corporate_orange": TEMPLATE_4_CORPORATE_ORANGE,
        "elegant_administratif": TEMPLATE_5_ELEGANT_ADMINISTRATIF
    }
    return templates.get(template_id, TEMPLATE_1_CLASSIQUE)


def format_fcfa(montant: float) -> str:
    """Formate un montant en FCFA"""
    return f"{montant:,.0f} FCFA".replace(",", " ")


def build_articles_rows(articles: List[Dict]) -> str:
    """Génère les lignes HTML du tableau d'articles avec Niveau et Matière"""
    rows = []
    for article in articles:
        # Extraire niveau et matière du produit enrichi
        niveau = article.get('niveau_scolaire') or article.get('classe', '')
        matiere = article.get('matiere', '')
        code_article = str(article.get('code_article') or article.get('produit_id', ''))[:14]
        
        row = f"""
        <tr>
            <td><strong>{niveau}</strong></td>
            <td>{article.get('matiere', '')}</td>
            <td>{code_article}</td>
            <td>{article.get('designation', '')}</td>
            <td style="text-align: center;">{article.get('quantite', 0)}</td>
            <td style="text-align: right;">{format_fcfa(float(article.get('prix_unitaire', 0)))}</td>
            <td style="text-align: right;">{format_fcfa(float(article.get('montant_ht', 0)))}</td>
        </tr>
        """
        rows.append(row)
    return "".join(rows)


def render_template(
    template_id: str,
    document_title: str,
    reference: str,
    date_str: str,
    company_info: Dict,
    client_info: Dict,
    articles: List[Dict],
    totals: Dict,
    logo_html: str = ""
) -> str:
    """
    Rend un template avec les données fournies
    
    Args:
        template_id: ID du template à utiliser
        document_title: Titre du document (ex: FACTURE CLIENT)
        reference: Numéro de référence
        date_str: Date du document
        company_info: Informations de l'entreprise
        client_info: Informations du client
        articles: Liste des articles
        totals: Totaux (montant_ht, montant_tva, montant_ttc, remise_globale)
        logo_html: HTML du logo (img tag)
    """
    template = get_template(template_id)
    
    # Formater les totaux
    montant_ht = format_fcfa(float(totals.get('montant_ht', 0)))
    montant_tva = format_fcfa(float(totals.get('montant_tva', 0)))
    montant_ttc = format_fcfa(float(totals.get('montant_ttc', 0)))
    remise_globale = format_fcfa(float(totals.get('remise_globale', 0)))
    
    # Générer les lignes d'articles
    articles_rows = build_articles_rows(articles)
    
    # Remplacer les placeholders
    html = template.format(
        logo_html=logo_html or '<div style="width: 100px; height: 70px; background: #FF6200; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">LOGO</div>',
        company_name=company_info.get('nom', 'EDITIONS FABS-CI'),
        company_slogan=company_info.get('slogan', 'Une innovation pour une école de qualité'),
        company_address=company_info.get('adresse', 'BP 693'),
        company_phone=company_info.get('telephone', '+225 07 59 73 71 23'),
        company_email=company_info.get('email', 'edition693fabs@gmail.com'),
        siege_social=company_info.get('siege_social', 'Bingerville, Quartier N\'GOTTO, Immeuble cité Angan A. fils et petits-fils, Rez-de-chaussée'),
        banques=f"Banques : {company_info.get('banques', {}).get('CORIS BANK', '')} ; {company_info.get('banques', {}).get('SGBCI', '')}",
        document_title=document_title,
        reference=reference,
        date_str=date_str,
        client_nom=client_info.get('nom', '-'),
        client_type=client_info.get('type_client', '-'),
        client_ville=client_info.get('ville', '-'),
        client_telephone=client_info.get('telephone', '-'),
        client_adresse=client_info.get('adresse', '-'),
        client_representant=client_info.get('representant', '-'),
        articles_rows=articles_rows,
        montant_ht=montant_ht,
        montant_tva=montant_tva,
        montant_ttc=montant_ttc,
        remise_globale=remise_globale
    )
    
    return html
