"""
Script d'export des données FABS-CI vers JSON
Exporte les clients, articles et utilisateurs vers des fichiers JSON
"""

import re
import json
from datetime import datetime, timezone

# Chemins des fichiers
CLIENTS_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\CLIENTS_FABS_CI_AVEC_NUMEROTATION.txt"
ARTICLES_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\ARTICLES_FABS_CI_NUMEROTES.txt"
USERS_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\utilisateurs_editionsfabsci.txt"

# Chemins de sortie
OUTPUT_DIR = r"c:\Users\SMART PISSKEN\Documents\ERP-fabs-ci-v5\backend\data_import"

def parse_clients(file_path):
    """Parse le fichier des clients"""
    clients = []
    current_region = "NON DEFINI"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line = line.rstrip('\n')
        
        # Ignorer les lignes vides
        if not line or line.strip() == "":
            continue
        
        # Détecter les régions (lignes avec =)
        if line.startswith("="):
            continue
        
        # Détecter les séparateurs de colonnes (lignes avec -)
        if line.startswith("-"):
            continue
        
        # Détecter les en-têtes de colonnes
        if "Client" in line and "Représentant" in line:
            continue
        
        # Détecter les noms de régions (tout en majuscules, pas de |)
        if line.isupper() and len(line) > 3 and "|" not in line:
            current_region = line
            continue
        
        # Parser les lignes de clients (format fixe: ID | Nom | Repre | Phone | Email | Type)
        # Positions approximatives basées sur le format du fichier
        if "|" in line:
            # Extraire l'ID (avant le premier |)
            id_part = line.split("|")[0].strip()
            if id_part.isdigit():
                # Parser le reste de la ligne par position fixe
                # Après le premier |, le format semble être: Nom (50 chars) | Repre (35 chars) | Phone (15 chars) | Email (25 chars) | Type
                rest = line.split("|", 1)[1] if "|" in line else ""
                
                # Extraire les champs par position approximative
                nom = rest[:50].strip() if len(rest) > 50 else rest.strip()
                repre = rest[50:85].strip() if len(rest) > 85 else ""
                phone = rest[85:100].strip() if len(rest) > 100 else ""
                email = rest[100:125].strip() if len(rest) > 125 else ""
                type_client = rest[125:].strip() if len(rest) > 125 else "PARTICULIER"
                
                clients.append({
                    "client_id": f"CLI{id_part.zfill(5)}",
                    "nom": nom,
                    "representant": repre,
                    "telephone": phone,
                    "email": email if email else None,
                    "type_client": type_client,
                    "region": current_region,
                    "actif": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
    
    print(f"DEBUG: Total lines processed: {len(lines)}")
    print(f"DEBUG: Clients found: {len(clients)}")
    if len(clients) > 0:
        print(f"DEBUG: First client: {clients[0]}")
    return clients

def parse_articles(file_path):
    """Parse le fichier des articles"""
    articles = []
    current_article = {}
    current_category = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Détecter les catégories
            if line.startswith("-") and len(line) > 50:
                current_category = line.replace("-", "").strip()
                continue
            
            # Détecter début d'article
            if line.startswith("ARTICLE"):
                if current_article:
                    articles.append(current_article)
                current_article = {"category": current_category}
                continue
            
            # Parser les champs
            if line.startswith("Code Article"):
                current_article["code"] = line.split(":")[1].strip()
            elif line.startswith("Référence"):
                current_article["reference"] = line.split(":")[1].strip()
            elif line.startswith("ISBN"):
                current_article["isbn"] = line.split(":")[1].strip()
            elif line.startswith("Prix d'achat"):
                prix_achat = line.split(":")[1].strip()
                # Extraire le prix en FCFA
                match = re.search(r'([\d\s]+)\s*FCFA', prix_achat)
                if match:
                    current_article["prix_achat"] = int(match.group(1).replace(" ", ""))
                else:
                    current_article["prix_achat"] = 0
            elif line.startswith("Prix de vente"):
                prix_vente = line.split(":")[1].strip()
                # Extraire le prix en FCFA
                match = re.search(r'([\d\s]+)\s*FCFA', prix_vente)
                if match:
                    current_article["prix_vente"] = int(match.group(1).replace(" ", ""))
                else:
                    current_article["prix_vente"] = 0
    
    # Ajouter le dernier article
    if current_article:
        articles.append(current_article)
    
    # Formater les articles
    formatted_articles = []
    for i, article in enumerate(articles, 1):
        formatted_articles.append({
            "product_id": f"PRD{str(i).zfill(5)}",
            "code": article.get("code", ""),
            "reference": article.get("reference", ""),
            "isbn": article.get("isbn", ""),
            "prix_achat": article.get("prix_achat", 0),
            "prix_vente": article.get("prix_vente", 0),
            "categorie": article.get("category", ""),
            "stock": 0,
            "actif": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return formatted_articles

def parse_users(file_path):
    """Parse le fichier des utilisateurs"""
    users = []
    current_user = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if line.startswith("NOM COMPLET"):
                if current_user:
                    users.append(current_user)
                current_user = {}
                current_user["nom"] = line.split(":")[1].strip()
            elif line.startswith("EMAIL"):
                current_user["email"] = line.split(":")[1].strip()
            elif line.startswith("RÔLE"):
                current_user["role"] = line.split(":")[1].strip()
    
    # Ajouter le dernier utilisateur
    if current_user:
        users.append(current_user)
    
    # Formater les utilisateurs avec mot de passe par défaut
    formatted_users = []
    for i, user in enumerate(users, 1):
        formatted_users.append({
            "user_id": f"USR{str(i).zfill(5)}",
            "nom": user["nom"],
            "email": user["email"],
            "role": user["role"],
            "password": "password123",  # À hasher lors de l'import MongoDB
            "actif": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return formatted_users

def save_to_json(data, filename):
    """Sauvegarde les données en JSON"""
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ {len(data)} enregistrements exportés vers {filename}")

def main():
    print("=== Export des données FABS-CI vers JSON ===\n")
    
    # Exporter les clients
    print("Export des clients...")
    try:
        clients = parse_clients(CLIENTS_FILE)
        print(f"  {len(clients)} clients parsés")
        save_to_json(clients, "clients.json")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'export des clients: {e}")
    
    # Exporter les articles
    print("\nExport des articles...")
    try:
        articles = parse_articles(ARTICLES_FILE)
        print(f"  {len(articles)} articles parsés")
        save_to_json(articles, "articles.json")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'export des articles: {e}")
    
    # Exporter les utilisateurs
    print("\nExport des utilisateurs...")
    try:
        users = parse_users(USERS_FILE)
        print(f"  {len(users)} utilisateurs parsés")
        save_to_json(users, "users.json")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'export des utilisateurs: {e}")
    
    print(f"\n=== Export terminé ===")
    print(f"Fichiers créés dans : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
