"""
Script d'import des données FABS-CI
Importe les clients, articles et utilisateurs depuis les fichiers texte
"""

import re
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt

# Charger les variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/fabs_erp")
DB_NAME = os.getenv("DB_NAME", "fabs_erp")

# Chemins des fichiers
CLIENTS_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\CLIENTS_FABS_CI_AVEC_NUMEROTATION.txt"
ARTICLES_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\ARTICLES_FABS_CI_NUMEROTES.txt"
USERS_FILE = r"g:\PROMPT LOVABLE EDITIONS FABS-CI ERP\final\PRET A\utilisateurs_editionsfabsci.txt"

def parse_clients(file_path):
    """Parse le fichier des clients"""
    clients = []
    current_region = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Détecter les régions (lignes avec =)
        if line.startswith("=") and len(line) > 50:
            continue
        
        # Détecter les noms de régions (tout en majuscules, pas de |)
        if line.isupper() and len(line) > 3 and "|" not in line and not line.startswith("="):
            current_region = line
            continue
        
        # Parser les lignes de clients (format: ID | Nom | Repre | Phone | Email | Type)
        if "|" in line and re.match(r'\d+\s*\|', line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                client_id = parts[0]
                nom = parts[1]
                representant = parts[2]
                phone = parts[3]
                email = parts[4] if parts[4] else None
                type_client = parts[5] if len(parts) > 5 else "PARTICULIER"
                
                clients.append({
                    "client_id": f"CLI{client_id.zfill(5)}",
                    "nom": nom,
                    "representant": representant,
                    "telephone": phone,
                    "email": email,
                    "type_client": type_client,
                    "region": current_region,
                    "actif": True,
                    "created_at": datetime.now(datetime.UTC).isoformat()
                })
    
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
            "created_at": datetime.now(datetime.UTC).isoformat()
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
        password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        
        formatted_users.append({
            "user_id": f"USR{str(i).zfill(5)}",
            "nom": user["nom"],
            "email": user["email"],
            "role": user["role"],
            "password": password_hash.decode('utf-8'),
            "actif": True,
            "created_at": datetime.now(datetime.UTC).isoformat()
        })
    
    return formatted_users

def import_to_mongodb(data, collection_name):
    """Importe les données dans MongoDB"""
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[collection_name]
    
    # Supprimer les données existantes
    collection.delete_many({})
    
    # Insérer les nouvelles données
    if data:
        result = collection.insert_many(data)
        print(f"✓ {len(result.inserted_ids)} enregistrements importés dans {collection_name}")
    else:
        print(f"⚠ Aucune donnée à importer dans {collection_name}")
    
    client.close()

def main():
    print("=== Import des données FABS-CI ===\n")
    
    # Importer les clients
    print("Import des clients...")
    try:
        clients = parse_clients(CLIENTS_FILE)
        print(f"  {len(clients)} clients parsés")
        import_to_mongodb(clients, "clients")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'import des clients: {e}")
    
    # Importer les articles
    print("\nImport des articles...")
    try:
        articles = parse_articles(ARTICLES_FILE)
        print(f"  {len(articles)} articles parsés")
        import_to_mongodb(articles, "products")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'import des articles: {e}")
    
    # Importer les utilisateurs
    print("\nImport des utilisateurs...")
    try:
        users = parse_users(USERS_FILE)
        print(f"  {len(users)} utilisateurs parsés")
        import_to_mongodb(users, "users")
    except Exception as e:
        print(f"  ✗ Erreur lors de l'import des utilisateurs: {e}")
    
    print("\n=== Import terminé ===")

if __name__ == "__main__":
    main()
