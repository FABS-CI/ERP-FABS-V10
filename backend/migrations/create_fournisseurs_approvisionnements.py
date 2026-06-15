"""
Migration MongoDB - Création des collections fournisseurs et approvisionnements

Cette migration crée les collections nécessaires pour la gestion des fournisseurs
et des approvisionnements dans le module Produits/Inventaire.

À exécuter avec: python backend/migrations/create_fournisseurs_approvisionnements.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabs_erp")


async def migrate():
    """Exécute la migration MongoDB"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print("🚀 Début de la migration Fournisseurs/Approvisionnements...")
    print(f"📦 Base de données: {DB_NAME}")
    print(f"🔗 URI: {MONGODB_URI}")
    print()
    
    # 1. Créer la collection fournisseurs avec indexes
    print("📝 Collection: fournisseurs")
    
    # Créer un fournisseur de test
    fournisseur_test = {
        "fournisseur_id": "test-fournisseur-001",
        "reference": "FABS-FRN-0001",
        "nom": "Imprimerie Test CI",
        "contact": "M. Kouassi",
        "telephone": "+225 01 02 03 04 05",
        "email": "contact@imprimerietest.ci",
        "adresse": "Abidjan, Cocody",
        "actif": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # Insérer le fournisseur de test
    existing = await db.fournisseurs.find_one({"fournisseur_id": "test-fournisseur-001"})
    if not existing:
        await db.fournisseurs.insert_one(fournisseur_test)
        print("  ✅ Fournisseur de test créé")
    else:
        print("  ℹ️  Fournisseur de test existe déjà")
    
    # Créer les indexes
    await db.fournisseurs.create_index("fournisseur_id", unique=True)
    await db.fournisseurs.create_index("reference", unique=True)
    await db.fournisseurs.create_index("nom")
    await db.fournisseurs.create_index("actif")
    print("  ✅ Indexes créés")
    
    # 2. Créer la collection approvisionnements avec indexes
    print("📝 Collection: approvisionnements")
    
    # Créer un approvisionnement de test
    approvisionnement_test = {
        "approvisionnement_id": "test-appro-001",
        "reference": "FABS-APP-0001",
        "fournisseur_id": "test-fournisseur-001",
        "fournisseur_nom": "Imprimerie Test CI",
        "depot": "principal",
        "lignes": [
            {
                "produit_id": "test-produit-001",
                "quantite": 100,
                "prix_achat": 2500.0,
            }
        ],
        "statut": "brouillon",
        "notes": "Approvisionnement de test",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "valide_le": None,
        "valide_par": None,
    }
    
    # Insérer l'approvisionnement de test
    existing = await db.approvisionnements.find_one({"approvisionnement_id": "test-appro-001"})
    if not existing:
        await db.approvisionnements.insert_one(approvisionnement_test)
        print("  ✅ Approvisionnement de test créé")
    else:
        print("  ℹ️  Approvisionnement de test existe déjà")
    
    # Créer les indexes
    await db.approvisionnements.create_index("approvisionnement_id", unique=True)
    await db.approvisionnements.create_index("reference", unique=True)
    await db.approvisionnements.create_index("fournisseur_id")
    await db.approvisionnements.create_index("statut")
    await db.approvisionnements.create_index("depot")
    await db.approvisionnements.create_index("created_at")
    print("  ✅ Indexes créés")
    
    # 3. Mettre à jour la collection produits pour ajouter les champs FNE
    print("📝 Mise à jour collection: produits")
    
    # Ajouter les champs fournisseur_id, depot, derniere_entree si absents
    result = await db.produits.update_many(
        {
            "$or": [
                {"fournisseur_id": {"$exists": False}},
                {"depot": {"$exists": False}},
                {"derniere_entree": {"$exists": False}},
            ]
        },
        {
            "$set": {
                "fournisseur_id": None,
                "depot": "principal",
                "derniere_entree": None,
            }
        }
    )
    print(f"  ✅ {result.modified_count} produits mis à jour")
    
    # Créer les indexes sur les nouveaux champs
    await db.produits.create_index("fournisseur_id")
    await db.produits.create_index("depot")
    await db.produits.create_index("derniere_entree")
    print("  ✅ Indexes créés")
    
    # 4. Initialiser le compteur pour les références
    print("📝 Initialisation compteurs")
    
    # Compteur fournisseurs
    existing_counter = await db.counters.find_one({"_id": "fournisseurs"})
    if not existing_counter:
        await db.counters.insert_one({"_id": "fournisseurs", "seq": 1})
        print("  ✅ Compteur fournisseurs initialisé")
    else:
        print("  ℹ️  Compteur fournisseurs existe déjà")
    
    # Compteur approvisionnements
    existing_counter = await db.counters.find_one({"_id": "approvisionnements"})
    if not existing_counter:
        await db.counters.insert_one({"_id": "approvisionnements", "seq": 1})
        print("  ✅ Compteur approvisionnements initialisé")
    else:
        print("  ℹ️  Compteur approvisionnements existe déjà")
    
    print()
    print("✅ Migration terminée avec succès!")
    print()
    print("📊 Résumé:")
    print("  - Collection fournisseurs créée avec indexes")
    print("  - Collection approvisionnements créée avec indexes")
    print("  - Collection produits mise à jour avec nouveaux champs")
    print("  - Compteurs initialisés")
    print()
    print("🎯 Prochaines étapes:")
    print("  1. Enregistrer les modules dans server.py")
    print("  2. Ajouter la route dans le router frontend")
    print("  3. Tester l'interface")


async def rollback():
    """Annule la migration (supprime les collections)"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print("🔄 Rollback de la migration...")
    
    await db.fournisseurs.drop()
    print("  ✅ Collection fournisseurs supprimée")
    
    await db.approvisionnements.drop()
    print("  ✅ Collection approvisionnements supprimée")
    
    await db.counters.delete_many({"_id": {"$in": ["fournisseurs", "approvisionnements"]}})
    print("  ✅ Compteurs supprimés")
    
    print("✅ Rollback terminé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
