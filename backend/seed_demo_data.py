"""
Script de seed pour les données de démonstration - ERP FABS-CI V7
Crée automatiquement des utilisateurs, clients, produits et commandes pour les tests
"""
import asyncio
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

# Configuration
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "fabsci_erp"

async def seed_demo_data():
    """Seed les données de démonstration"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🌱 Seeding demo data for ERP FABS-CI V7...")
    
    # 1. Seed Utilisateurs
    print("\n📝 Creating demo users...")
    users = [
        {
            "user_id": "user_super_admin",
            "email": "pissken@editionsfabsci.com",
            "password_hash": bcrypt.hashpw("Admin@2024".encode(), bcrypt.gensalt()).decode(),
            "nom": "AKE APPIA",
            "prenoms": "YVES DORIS",
            "role": "super_admin",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "user_id": "user_dg",
            "email": "ali.mamin@editionsfabsci.com",
            "password_hash": bcrypt.hashpw("Admin@2024".encode(), bcrypt.gensalt()).decode(),
            "nom": "ALI",
            "prenoms": "MAMIN",
            "role": "directeur_general",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "user_id": "user_commercial",
            "email": "commercial@editionsfabsci.com",
            "password_hash": bcrypt.hashpw("Admin@2024".encode(), bcrypt.gensalt()).decode(),
            "nom": "KOUASSI",
            "prenoms": "JEAN",
            "role": "directeur_commercial",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "user_id": "user_comptable",
            "email": "comptable@editionsfabsci.com",
            "password_hash": bcrypt.hashpw("Admin@2024".encode(), bcrypt.gensalt()).decode(),
            "nom": "YAO",
            "prenoms": "MARIE",
            "role": "comptable",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"  ✅ Created user: {user['email']} ({user['role']})")
        else:
            print(f"  ⏭️  User already exists: {user['email']}")
    
    # 2. Seed Clients
    print("\n👥 Creating demo clients...")
    clients = [
        {
            "client_id": "client_001",
            "reference": "CLI-001",
            "nom": "LIBRAIRIE CENTRALE",
            "type_client": "grossiste",
            "email": "contact@librairie-centrale.ci",
            "telephone": "+225 07 00 00 00 01",
            "adresse": "Abidjan, Plateau",
            "ville": "Abidjan",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "client_id": "client_002",
            "reference": "CLI-002",
            "nom": "ÉCOLE PRIMAIRE SACRÉ-CŒUR",
            "type_client": "particulier",
            "email": "secretariat@sacrecoeur.edu.ci",
            "telephone": "+225 07 00 00 00 02",
            "adresse": "Yamoussoukro",
            "ville": "Yamoussoukro",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "client_id": "client_003",
            "reference": "CLI-003",
            "nom": "UNIVERSITÉ FÉLIX HOUPHOUËT-BOIGNY",
            "type_client": "institution",
            "email": "bibliotheque@ufhb.ci",
            "telephone": "+225 07 00 00 00 03",
            "adresse": "Abidjan, Cocody",
            "ville": "Abidjan",
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for client in clients:
        existing = await db.clients.find_one({"client_id": client["client_id"]})
        if not existing:
            await db.clients.insert_one(client)
            print(f"  ✅ Created client: {client['nom']}")
        else:
            print(f"  ⏭️  Client already exists: {client['nom']}")
    
    # 3. Seed Produits
    print("\n📚 Creating demo products...")
    products = [
        {
            "produit_id": "prod_001",
            "reference": "ISBN-978-2-12345-678-9",
            "titre": "Mathématiques CM1 - Édition 2024",
            "auteur": "MINISTÈRE DE L'ÉDUCATION",
            "editeur": "EDITIONS FABS-CI",
            "categorie": "Manuel Scolaire",
            "prix_vente": 5000,
            "stock_actuel": 100,
            "stock_minimum": 20,
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "produit_id": "prod_002",
            "reference": "ISBN-978-2-12345-679-6",
            "titre": "Français CE2 - Édition 2024",
            "auteur": "MINISTÈRE DE L'ÉDUCATION",
            "editeur": "EDITIONS FABS-CI",
            "categorie": "Manuel Scolaire",
            "prix_vente": 4500,
            "stock_actuel": 150,
            "stock_minimum": 30,
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "produit_id": "prod_003",
            "reference": "ISBN-978-2-12345-680-2",
            "titre": "Histoire-Géographie 6ème - Édition 2024",
            "auteur": "MINISTÈRE DE L'ÉDUCATION",
            "editeur": "EDITIONS FABS-CI",
            "categorie": "Manuel Scolaire",
            "prix_vente": 6000,
            "stock_actuel": 80,
            "stock_minimum": 15,
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "produit_id": "prod_004",
            "reference": "ISBN-978-2-12345-681-9",
            "titre": "Sciences Naturelles CM2 - Édition 2024",
            "auteur": "MINISTÈRE DE L'ÉDUCATION",
            "editeur": "EDITIONS FABS-CI",
            "categorie": "Manuel Scolaire",
            "prix_vente": 5500,
            "stock_actuel": 120,
            "stock_minimum": 25,
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "produit_id": "prod_005",
            "reference": "ISBN-978-2-12345-682-6",
            "titre": "Cahier d'activités CP1 - Édition 2024",
            "auteur": "MINISTÈRE DE L'ÉDUCATION",
            "editeur": "EDITIONS FABS-CI",
            "categorie": "Cahier d'Activités",
            "prix_vente": 2500,
            "stock_actuel": 200,
            "stock_minimum": 50,
            "actif": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for product in products:
        existing = await db.produits.find_one({"produit_id": product["produit_id"]})
        if not existing:
            await db.produits.insert_one(product)
            print(f"  ✅ Created product: {product['titre']}")
        else:
            print(f"  ⏭️  Product already exists: {product['titre']}")
    
    # 4. Seed Commandes
    print("\n📦 Creating demo orders...")
    commandes = [
        {
            "commande_id": "cmd_001",
            "reference": "FABS-CMD-26-27-0001",
            "client_id": "client_001",
            "statut": "validee",
            "montant_ht": 27500,
            "montant_tva": 4950,
            "montant_ttc": 32450,
            "remise_globale": 0,
            "notes": "Commande test pour librairie centrale",
            "lignes": [
                {
                    "ligne_id": "ligne_001",
                    "produit_id": "prod_001",
                    "quantite": 5,
                    "prix_unitaire": 5000,
                    "remise_ligne": 0,
                    "montant_ligne": 25000
                },
                {
                    "ligne_id": "ligne_002",
                    "produit_id": "prod_002",
                    "quantite": 1,
                    "prix_unitaire": 4500,
                    "remise_ligne": 0,
                    "montant_ligne": 4500
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "commande_id": "cmd_002",
            "reference": "FABS-CMD-26-27-0002",
            "client_id": "client_002",
            "statut": "en_attente",
            "montant_ht": 6000,
            "montant_tva": 1080,
            "montant_ttc": 7080,
            "remise_globale": 0,
            "notes": "Commande test pour école primaire",
            "lignes": [
                {
                    "ligne_id": "ligne_003",
                    "produit_id": "prod_003",
                    "quantite": 1,
                    "prix_unitaire": 6000,
                    "remise_ligne": 0,
                    "montant_ligne": 6000
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for commande in commandes:
        existing = await db.commandes.find_one({"commande_id": commande["commande_id"]})
        if not existing:
            await db.commandes.insert_one(commande)
            print(f"  ✅ Created order: {commande['reference']}")
        else:
            print(f"  ⏭️  Order already exists: {commande['reference']}")
    
    print("\n✅ Demo data seeding completed successfully!")
    print("\n📊 Summary:")
    print("  - 4 Users created")
    print("  - 3 Clients created")
    print("  - 5 Products created")
    print("  - 2 Orders created")
    print("\n🔐 Default credentials:")
    print("  Email: pissken@editionsfabsci.com")
    print("  Password: Admin@2024")
    print("\n🌐 You can now login and test all modules!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
