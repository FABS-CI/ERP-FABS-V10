#!/usr/bin/env python3
"""Cleanup test data before go-live"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

async def cleanup_test_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 80)
    print("NETTOYAGE DONNÉES DE TEST - COMMANDES ORPHELINES")
    print("=" * 80)
    
    try:
        # Get before count
        print("\n[AVANT]")
        cmd_before = await db.commandes.count_documents({})
        lig_before = await db.commande_lignes.count_documents({})
        fact_before = await db.factures.count_documents({})
        paiem_before = await db.paiements.count_documents({})
        
        print(f"  Commandes: {cmd_before}")
        print(f"  Lignes commandes: {lig_before}")
        print(f"  Factures: {fact_before}")
        print(f"  Paiements: {paiem_before}")
        
        print("\n[SUPPRESSION EN COURS]")
        
        # Cleanup
        result1 = await db.commandes.delete_many({})
        print(f"  ✅ Commandes supprimées: {result1.deleted_count}")
        
        result2 = await db.commande_lignes.delete_many({})
        print(f"  ✅ Lignes commandes supprimées: {result2.deleted_count}")
        
        result3 = await db.factures.delete_many({})
        print(f"  ✅ Factures supprimées: {result3.deleted_count}")
        
        result4 = await db.paiements.delete_many({})
        print(f"  ✅ Paiements supprimés: {result4.deleted_count}")
        
        # Get after count
        print("\n[APRÈS]")
        cmd_after = await db.commandes.count_documents({})
        lig_after = await db.commande_lignes.count_documents({})
        fact_after = await db.factures.count_documents({})
        paiem_after = await db.paiements.count_documents({})
        
        print(f"  Commandes: {cmd_after}")
        print(f"  Lignes commandes: {lig_after}")
        print(f"  Factures: {fact_after}")
        print(f"  Paiements: {paiem_after}")
        
        # Validation
        print("\n[VALIDATION]")
        if cmd_after == 0 and fact_after == 0 and paiem_after == 0:
            print("  ✅ CLEANUP RÉUSSI")
            print("  ✅ DB PROPRE POUR PRODUCTION")
            return True
        else:
            print("  ⚠️ DONNÉES RESTANTES")
            return False
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False
    finally:
        if hasattr(client, 'close'):
            client.close()

if __name__ == "__main__":
    result = asyncio.run(cleanup_test_data())
    print("\n" + "=" * 80)
    exit(0 if result else 1)
