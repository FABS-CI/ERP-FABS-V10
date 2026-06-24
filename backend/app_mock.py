"""
ERP FABS-CI Mock Backend
Simulates all endpoints for validation testing without MongoDB
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
from typing import Optional, List
import uuid

app = FastAPI(title="ERP FABS-CI Mock API")

# CORS
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('JWT_SECRET', 'dev-secret-key-2026')

# Mock data storage
mock_db = {
    "users": [
        {
            "_id": "user_001",
            "email": "pissken@editionsfabsci.com",
            "password": pwd_context.hash("Admin@2025"),
            "role": "super_admin",
            "nom": "Pissken",
        }
    ],
    "prospects": [],
    "clients": [],
    "devis": [],
    "commandes": [],
    "livraisons": [],
    "factures": [],
    "paiements": [],
    "demandes_achat": [],
    "commandes_fournisseur": [],
    "receptions": [],
    "factures_fournisseur": [],
    "paiements_fournisseur": [],
    "stock_entrees": [],
    "stock_sorties": [],
    "stock_balance": [],
    "inventaires": [],
    "employes": [],
    "presences": [],
    "bulletins": [],
}

def generate_id():
    return str(uuid.uuid4())[:12]

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ERP FABS-CI Mock API", "timestamp": datetime.now().isoformat()}

@app.get("/api/db-status")
async def db_status():
    return {"status": "connected", "type": "mock", "records": sum(len(v) for v in mock_db.values())}

# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Login with email/password, return JWT token"""
    user = next((u for u in mock_db["users"] if u["email"] == email), None)
    
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    if not pwd_context.verify(password, user.get("password", "")):
        # For dev: accept plain text too
        if password != "Admin@2025":
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    token = jwt.encode(
        {"user_id": user["_id"], "email": user["email"], "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )
    
    return {
        "access_token": token,
        "user_id": user["_id"],
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "nom": user.get("nom"),
            "role": user.get("role", "user"),
        }
    }

@app.get("/api/utilisateurs/me")
async def get_current_user(authorization: Optional[str] = None):
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = next((u for u in mock_db["users"] if u["_id"] == user_id), None)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# PROSPECTS
# ============================================================================

@app.post("/api/prospects")
async def create_prospect(
    nom: str,
    email: str,
    telephone: str = "",
    secteur: str = "",
    adresse: str = "",
    pays: str = "",
):
    """Create a new prospect"""
    prospect = {
        "id": generate_id(),
        "nom": nom,
        "email": email,
        "telephone": telephone,
        "secteur": secteur,
        "adresse": adresse,
        "pays": pays,
        "created_at": datetime.now().isoformat(),
        "statut": "NOUVEAU",
    }
    mock_db["prospects"].append(prospect)
    return prospect

@app.post("/api/prospects/{prospect_id}/convert")
async def convert_prospect_to_client(prospect_id: str, type_client: str = "PARTICULIER", reference: str = ""):
    """Convert prospect to client"""
    prospect = next((p for p in mock_db["prospects"] if p["id"] == prospect_id), None)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    client = {
        "id": generate_id(),
        "prospect_id": prospect_id,
        "nom": prospect["nom"],
        "email": prospect["email"],
        "telephone": prospect["telephone"],
        "adresse": prospect["adresse"],
        "type": type_client,
        "reference": reference or f"CLI_{prospect_id[:8]}",
        "created_at": datetime.now().isoformat(),
        "statut": "ACTIF",
    }
    mock_db["clients"].append(client)
    return {"client_id": client["id"], "reference": client["reference"]}

# ============================================================================
# CLIENTS
# ============================================================================

@app.get("/api/clients")
async def list_clients(limit: int = Query(10), skip: int = Query(0)):
    """List all clients"""
    clients = mock_db["clients"][skip:skip+limit]
    return {
        "count": len(clients),
        "total": len(mock_db["clients"]),
        "clients": clients,
    }

# ============================================================================
# DEVIS (QUOTES)
# ============================================================================

@app.post("/api/devis")
async def create_devis(
    client_id: str,
    reference: str,
    date_devis: str,
    date_validite: str = "",
    lignes: list = None,
    devise: str = "XOF",
    statut: str = "DRAFT",
):
    """Create a quote (devis)"""
    devis = {
        "id": generate_id(),
        "client_id": client_id,
        "reference": reference,
        "date_devis": date_devis,
        "date_validite": date_validite,
        "lignes": lignes or [],
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["devis"].append(devis)
    return devis

@app.post("/api/devis/{devis_id}/valider")
async def validate_devis(devis_id: str):
    """Validate devis and convert to commande"""
    devis = next((d for d in mock_db["devis"] if d["id"] == devis_id), None)
    if not devis:
        raise HTTPException(status_code=404, detail="Devis not found")
    
    # Create commande
    commande = {
        "id": generate_id(),
        "devis_id": devis_id,
        "client_id": devis["client_id"],
        "reference": f"CMD_{devis['reference']}",
        "date_commande": datetime.now().strftime("%Y-%m-%d"),
        "lignes": devis["lignes"],
        "devise": devis["devise"],
        "statut": "CONFIRMEE",
        "created_at": datetime.now().isoformat(),
    }
    mock_db["commandes"].append(commande)
    
    # Update devis status
    devis["statut"] = "VALIDEE"
    
    return {
        "status": "ok",
        "commande_id": commande["id"],
        "devis_id": devis_id,
    }

# ============================================================================
# COMMANDES
# ============================================================================

@app.get("/api/commandes")
async def list_commandes(limit: int = Query(10), skip: int = Query(0)):
    """List all commandes"""
    commandes = mock_db["commandes"][skip:skip+limit]
    return {
        "count": len(commandes),
        "total": len(mock_db["commandes"]),
        "commandes": commandes,
    }

# ============================================================================
# LIVRAISONS (DELIVERIES)
# ============================================================================

@app.post("/api/livraisons")
async def create_livraison(
    commande_id: str,
    reference: str,
    date_prevue: str,
    adresse_livraison: str,
    statut: str = "CONFIRMEE",
):
    """Create delivery"""
    livraison = {
        "id": generate_id(),
        "commande_id": commande_id,
        "reference": reference,
        "date_prevue": date_prevue,
        "adresse_livraison": adresse_livraison,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["livraisons"].append(livraison)
    return livraison

# ============================================================================
# FACTURES (INVOICES)
# ============================================================================

@app.post("/api/factures")
async def create_facture(
    client_id: str,
    commande_id: str,
    reference: str,
    date_facture: str,
    montant_ht: float,
    tva: float,
    montant_ttc: float,
    devise: str = "XOF",
    statut: str = "EMISE",
):
    """Create invoice"""
    facture = {
        "id": generate_id(),
        "client_id": client_id,
        "commande_id": commande_id,
        "reference": reference,
        "date_facture": date_facture,
        "montant_ht": montant_ht,
        "tva": tva,
        "montant_ttc": montant_ttc,
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["factures"].append(facture)
    return facture

# ============================================================================
# PAIEMENTS (PAYMENTS)
# ============================================================================

@app.post("/api/paiements")
async def create_paiement(
    facture_id: str,
    client_id: str,
    montant: float,
    mode_paiement: str,
    date_paiement: str,
    reference: str,
    statut: str = "CONFIRMEE",
):
    """Create payment"""
    paiement = {
        "id": generate_id(),
        "facture_id": facture_id,
        "client_id": client_id,
        "montant": montant,
        "mode_paiement": mode_paiement,
        "date_paiement": date_paiement,
        "reference": reference,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["paiements"].append(paiement)
    return paiement

# ============================================================================
# PURCHASE ORDERS
# ============================================================================

@app.post("/api/demandes-achat")
async def create_demande_achat(
    reference: str,
    date_demande: str,
    lignes: list = None,
    statut: str = "BROUILLON",
):
    """Create purchase request"""
    demande = {
        "id": generate_id(),
        "reference": reference,
        "date_demande": date_demande,
        "lignes": lignes or [],
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["demandes_achat"].append(demande)
    return demande

@app.post("/api/demandes-achat/{demande_id}/valider")
async def validate_demande_achat(demande_id: str):
    """Validate purchase request"""
    demande = next((d for d in mock_db["demandes_achat"] if d["id"] == demande_id), None)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande not found")
    
    demande["statut"] = "VALIDEE"
    return {"status": "ok", "demande_id": demande_id}

@app.post("/api/commandes-fournisseur")
async def create_commande_fournisseur(
    fournisseur_id: str,
    demande_achat_id: str,
    reference: str,
    date_commande: str,
    montant: float,
    devise: str = "XOF",
    statut: str = "CONFIRMEE",
):
    """Create supplier order"""
    commande = {
        "id": generate_id(),
        "fournisseur_id": fournisseur_id,
        "demande_achat_id": demande_achat_id,
        "reference": reference,
        "date_commande": date_commande,
        "montant": montant,
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["commandes_fournisseur"].append(commande)
    return commande

@app.post("/api/receptions")
async def create_reception(
    commande_fournisseur_id: str,
    reference: str,
    date_reception: str,
    quantite_recu: float,
    statut: str = "COMPLETEE",
):
    """Create receipt"""
    reception = {
        "id": generate_id(),
        "commande_fournisseur_id": commande_fournisseur_id,
        "reference": reference,
        "date_reception": date_reception,
        "quantite_recu": quantite_recu,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["receptions"].append(reception)
    return reception

@app.post("/api/factures-fournisseur")
async def create_facture_fournisseur(
    fournisseur_id: str,
    commande_fournisseur_id: str,
    reference: str,
    date_facture: str,
    montant_ht: float,
    tva: float,
    montant_ttc: float,
    devise: str = "XOF",
    statut: str = "REÇUE",
):
    """Create supplier invoice"""
    facture = {
        "id": generate_id(),
        "fournisseur_id": fournisseur_id,
        "commande_fournisseur_id": commande_fournisseur_id,
        "reference": reference,
        "date_facture": date_facture,
        "montant_ht": montant_ht,
        "tva": tva,
        "montant_ttc": montant_ttc,
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["factures_fournisseur"].append(facture)
    return facture

@app.post("/api/paiements-fournisseur")
async def create_paiement_fournisseur(
    facture_fournisseur_id: str,
    fournisseur_id: str,
    montant: float,
    mode_paiement: str,
    date_paiement: str,
    reference: str,
    statut: str = "CONFIRMEE",
):
    """Create supplier payment"""
    paiement = {
        "id": generate_id(),
        "facture_fournisseur_id": facture_fournisseur_id,
        "fournisseur_id": fournisseur_id,
        "montant": montant,
        "mode_paiement": mode_paiement,
        "date_paiement": date_paiement,
        "reference": reference,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["paiements_fournisseur"].append(paiement)
    return paiement

# ============================================================================
# STOCK
# ============================================================================

@app.post("/api/stock/entrees")
async def create_stock_entry(
    reference: str,
    date_entree: str,
    produit_id: str,
    quantite: float,
    prix_unitaire: float,
    type_entree: str = "ACHAT",
    statut: str = "VALIDEE",
):
    """Create stock entry"""
    entry = {
        "id": generate_id(),
        "reference": reference,
        "date_entree": date_entree,
        "produit_id": produit_id,
        "quantite": quantite,
        "prix_unitaire": prix_unitaire,
        "type_entree": type_entree,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["stock_entrees"].append(entry)
    
    # Update balance
    balance = next((b for b in mock_db["stock_balance"] if b["produit_id"] == produit_id), None)
    if balance:
        balance["quantite"] += quantite
    else:
        mock_db["stock_balance"].append({
            "produit_id": produit_id,
            "quantite": quantite,
            "prix_unitaire": prix_unitaire,
            "valeur": quantite * prix_unitaire,
        })
    
    return entry

@app.post("/api/stock/sorties")
async def create_stock_exit(
    reference: str,
    date_sortie: str,
    produit_id: str,
    quantite: float,
    type_sortie: str = "VENTE",
    commande_id: str = "",
    statut: str = "VALIDEE",
):
    """Create stock exit"""
    exit_record = {
        "id": generate_id(),
        "reference": reference,
        "date_sortie": date_sortie,
        "produit_id": produit_id,
        "quantite": quantite,
        "type_sortie": type_sortie,
        "commande_id": commande_id,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["stock_sorties"].append(exit_record)
    
    # Update balance
    balance = next((b for b in mock_db["stock_balance"] if b["produit_id"] == produit_id), None)
    if balance:
        balance["quantite"] = max(0, balance["quantite"] - quantite)
    
    return exit_record

@app.get("/api/stock/balance")
async def get_stock_balance(produit_id: str = Query("")):
    """Get stock balance"""
    if produit_id:
        balance = next((b for b in mock_db["stock_balance"] if b["produit_id"] == produit_id), None)
        if balance:
            return balance
        return {"produit_id": produit_id, "quantite": 0, "prix_unitaire": 0, "valeur": 0}
    return mock_db["stock_balance"]

@app.post("/api/stock/inventaires")
async def create_inventaire(
    reference: str,
    date_inventaire: str,
    lignes: list = None,
    statut: str = "VALIDEE",
):
    """Create inventory"""
    inventaire = {
        "id": generate_id(),
        "reference": reference,
        "date_inventaire": date_inventaire,
        "lignes": lignes or [],
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["inventaires"].append(inventaire)
    return inventaire

# ============================================================================
# FINANCE
# ============================================================================

@app.get("/api/finance/dashboard")
async def get_finance_dashboard():
    """Get finance dashboard"""
    total_factures = sum(f.get("montant_ttc", 0) for f in mock_db["factures"])
    total_paiements = sum(p.get("montant", 0) for p in mock_db["paiements"])
    
    return {
        "total_factures": total_factures,
        "total_paiements": total_paiements,
        "solde": total_factures - total_paiements,
        "factures_en_attente": len([f for f in mock_db["factures"] if f.get("statut") != "PAYEE"]),
    }

@app.get("/api/finance/journaux")
async def get_journaux(mois: int = Query(6), annee: int = Query(2026)):
    """Get journal entries"""
    return {
        "mois": mois,
        "annee": annee,
        "journaux": [],
        "count": 0,
    }

@app.get("/api/finance/grand-livre")
async def get_grand_livre(compte: str = Query("")):
    """Get general ledger"""
    return {
        "compte": compte,
        "solde": 0,
        "mouvements": [],
    }

@app.get("/api/finance/balance")
async def get_balance(mois: int = Query(6), annee: int = Query(2026)):
    """Get balance"""
    return {
        "mois": mois,
        "annee": annee,
        "total_debit": 0,
        "total_credit": 0,
        "solde": 0,
    }

@app.get("/api/finance/encaissements")
async def get_encaissements(mois: int = Query(6)):
    """Get receipts"""
    receipts = [p for p in mock_db["paiements"] if p.get("statut") == "CONFIRMEE"]
    return {
        "mois": mois,
        "total": sum(p.get("montant", 0) for p in receipts),
        "encaissements": receipts,
    }

@app.get("/api/finance/decaissements")
async def get_decaissements(mois: int = Query(6)):
    """Get payments"""
    payments = [p for p in mock_db["paiements_fournisseur"] if p.get("statut") == "CONFIRMEE"]
    return {
        "mois": mois,
        "total": sum(p.get("montant", 0) for p in payments),
        "decaissements": payments,
    }

# ============================================================================
# HR
# ============================================================================

@app.post("/api/rh/employes")
async def create_employe(
    nom: str,
    prenom: str,
    email: str,
    telephone: str = "",
    date_embauche: str = "",
    poste: str = "",
    departement_id: str = "",
    salaire_base: float = 0,
    devise: str = "XOF",
    statut: str = "ACTIF",
):
    """Create employee"""
    employe = {
        "id": generate_id(),
        "nom": nom,
        "prenom": prenom,
        "email": email,
        "telephone": telephone,
        "date_embauche": date_embauche,
        "poste": poste,
        "departement_id": departement_id,
        "salaire_base": salaire_base,
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["employes"].append(employe)
    return employe

@app.post("/api/rh/presences")
async def create_presence(
    employe_id: str,
    date: str,
    heure_arrivee: str = "",
    heure_depart: str = "",
    heures_travaillees: float = 0,
    type: str = "NORMAL",
    statut: str = "VALIDEE",
):
    """Create attendance"""
    presence = {
        "id": generate_id(),
        "employe_id": employe_id,
        "date": date,
        "heure_arrivee": heure_arrivee,
        "heure_depart": heure_depart,
        "heures_travaillees": heures_travaillees,
        "type": type,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["presences"].append(presence)
    return presence

@app.post("/api/rh/bulletins")
async def create_bulletin(
    employe_id: str,
    mois: int,
    annee: int,
    salaire_brut: float,
    deductions: float,
    salaire_net: float,
    devise: str = "XOF",
    statut: str = "VALIDEE",
):
    """Create payroll"""
    bulletin = {
        "id": generate_id(),
        "employe_id": employe_id,
        "mois": mois,
        "annee": annee,
        "salaire_brut": salaire_brut,
        "deductions": deductions,
        "salaire_net": salaire_net,
        "devise": devise,
        "statut": statut,
        "created_at": datetime.now().isoformat(),
    }
    mock_db["bulletins"].append(bulletin)
    return bulletin

@app.post("/api/rh/bulletins/comptabiliser")
async def comptabilize_bulletin(
    bulletin_id: str,
    date_comptabilisation: str = "",
):
    """Record payroll in accounting"""
    bulletin = next((b for b in mock_db["bulletins"] if b["id"] == bulletin_id), None)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    
    bulletin["comptabilisee"] = True
    bulletin["date_comptabilisation"] = date_comptabilisation
    
    return {"status": "ok", "bulletin_id": bulletin_id}

# ============================================================================
# GENERIC LISTS
# ============================================================================

@app.get("/api/utilisateurs")
async def list_users(limit: int = Query(10), skip: int = Query(0)):
    """List users"""
    users = mock_db["users"][skip:skip+limit]
    return {
        "count": len(users),
        "total": len(mock_db["users"]),
        "users": users,
    }

@app.get("/api/produits")
async def list_products(limit: int = Query(10), skip: int = Query(0)):
    """List products"""
    # Mock products
    products = [
        {"id": "product_001", "nom": "Produit Test 1", "prix": 5000},
        {"id": "product_002", "nom": "Produit Test 2", "prix": 10000},
    ]
    return {
        "count": min(len(products), limit),
        "total": len(products),
        "products": products[skip:skip+limit],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
