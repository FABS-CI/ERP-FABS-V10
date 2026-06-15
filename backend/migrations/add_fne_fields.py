"""
Migration MongoDB - Ajout des champs FNE pour l'intégration API DGI

Cette migration ajoute les champs nécessaires pour la certification FNE
sur les collections existantes et crée la nouvelle collection fne_logs.

À exécuter avec: python backend/migrations/add_fne_fields.py
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
    
    print("🚀 Début de la migration FNE...")
    print(f"📦 Base de données: {DB_NAME}")
    print(f"🔗 URI: {MONGODB_URI}")
    print()
    
    # 1. Ajouter les champs FNE sur la collection invoices
    print("📝 Collection: invoices")
    invoices_result = await db.invoices.update_many(
        {},
        {
            "$set": {
                "fne_status": "pending",
                "fne_reference": None,
                "fne_token": None,
                "fne_invoice_id": None,
                "fne_submitted_at": None,
                "fne_certified_at": None,
                "fne_raw_response": None,
                "fne_retry_count": 0,
                "fne_error_log": None,
                "fne_balance_sticker": None
            }
        }
    )
    print(f"   ✅ {invoices_result.modified_count} factures mises à jour")
    print()
    
    # 2. Ajouter le champ fne_item_id sur la collection invoice_items
    print("📝 Collection: invoice_items")
    items_result = await db.invoice_items.update_many(
        {},
        {
            "$set": {
                "fne_item_id": None
            }
        }
    )
    print(f"   ✅ {items_result.modified_count} lignes de facture mises à jour")
    print()
    
    # 3. Ajouter les champs FNE sur la collection credit_notes (avoirs)
    print("📝 Collection: credit_notes")
    credit_notes_result = await db.credit_notes.update_many(
        {},
        {
            "$set": {
                "fne_status": "pending",
                "fne_reference": None,
                "fne_token": None,
                "fne_submitted_at": None,
                "fne_certified_at": None,
                "fne_raw_response": None,
                "fne_retry_count": 0,
                "fne_error_log": None
            }
        }
    )
    print(f"   ✅ {credit_notes_result.modified_count} avoirs mis à jour")
    print()
    
    # 4. Créer la collection fne_logs avec des indexes
    print("📝 Collection: fne_logs (nouvelle)")
    
    # Créer l'index sur invoice_id pour les recherches rapides
    await db.fne_logs.create_index("invoice_id")
    print("   ✅ Index créé sur invoice_id")
    
    # Créer l'index sur created_at pour le tri chronologique
    await db.fne_logs.create_index("created_at")
    print("   ✅ Index créé sur created_at")
    
    # Créer l'index composite pour les requêtes fréquentes
    await db.fne_logs.create_index([("invoice_id", 1), ("created_at", -1)])
    print("   ✅ Index composite créé sur (invoice_id, created_at)")
    
    # Insérer un enregistrement de log pour la migration
    migration_log = {
        "invoice_id": "MIGRATION",
        "action": "migration",
        "attempt_number": 1,
        "http_status": 200,
        "request_body": {"migration": "add_fne_fields"},
        "response_body": {"status": "success"},
        "duration_ms": 0,
        "created_at": datetime.utcnow()
    }
    await db.fne_logs.insert_one(migration_log)
    print("   ✅ Log de migration inséré")
    print()
    
    print("✨ Migration terminée avec succès!")
    print()
    print("📊 Récapitulatif:")
    print(f"   - Factures mises à jour: {invoices_result.modified_count}")
    print(f"   - Lignes de facture mises à jour: {items_result.modified_count}")
    print(f"   - Avoirs mis à jour: {credit_notes_result.modified_count}")
    print(f"   - Collection fne_logs créée avec indexes")
    print()
    print("⚠️  Note: Les champs FNE sont initialisés à 'pending' pour les factures existantes.")
    print("   Les factures déjà certifiées manuellement devront être mises à jour.")
    
    client.close()


async def rollback():
    """Annule la migration (rollback)"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print("🔄 Rollback de la migration FNE...")
    print()
    
    # 1. Supprimer les champs FNE de invoices
    print("📝 Rollback: invoices")
    invoices_result = await db.invoices.update_many(
        {},
        {
            "$unset": {
                "fne_status": 1,
                "fne_reference": 1,
                "fne_token": 1,
                "fne_invoice_id": 1,
                "fne_submitted_at": 1,
                "fne_certified_at": 1,
                "fne_raw_response": 1,
                "fne_retry_count": 1,
                "fne_error_log": 1,
                "fne_balance_sticker": 1
            }
        }
    )
    print(f"   ✅ {invoices_result.modified_count} factures rollbackées")
    print()
    
    # 2. Supprimer le champ fne_item_id de invoice_items
    print("📝 Rollback: invoice_items")
    items_result = await db.invoice_items.update_many(
        {},
        {
            "$unset": {
                "fne_item_id": 1
            }
        }
    )
    print(f"   ✅ {items_result.modified_count} lignes rollbackées")
    print()
    
    # 3. Supprimer les champs FNE de credit_notes
    print("📝 Rollback: credit_notes")
    credit_notes_result = await db.credit_notes.update_many(
        {},
        {
            "$unset": {
                "fne_status": 1,
                "fne_reference": 1,
                "fne_token": 1,
                "fne_submitted_at": 1,
                "fne_certified_at": 1,
                "fne_raw_response": 1,
                "fne_retry_count": 1,
                "fne_error_log": 1
            }
        }
    )
    print(f"   ✅ {credit_notes_result.modified_count} avoirs rollbackés")
    print()
    
    # 4. Supprimer la collection fne_logs
    print("📝 Rollback: fne_logs")
    await db.fne_logs.drop()
    print("   ✅ Collection fne_logs supprimée")
    print()
    
    print("✨ Rollback terminé avec succès!")
    
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
