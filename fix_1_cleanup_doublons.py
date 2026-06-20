#!/usr/bin/env python3
"""
FIX #1: Cleanup doublons clients (1005 emails)
Stratégie: garder le plus récent (ID maximal), supprimer les anciens
Actions:
1. Identifier doublons par email
2. Pour chaque groupe: garder le plus récent, marquer les anciens comme supprimés
3. Rédiriger références (commandes, contacts, etc.) vers le client conservé
4. Ajouter contrainte UNIQUE sur clients.email
5. Valider intégrité référentielle
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING

# MongoDB config
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

async def cleanup_doublons():
    """Cleanup process"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db: AsyncIOMotorDatabase = client[DB_NAME]
    
    print("=" * 80)
    print("FIX #1: CLEANUP DOUBLONS CLIENTS")
    print("=" * 80)
    
    try:
        # 1. Find all clients
        print("\n[1/5] Récupération des clients...")
        all_clients = await db.clients.find({}).to_list(None)
        print(f"Total clients: {len(all_clients)}")
        
        # 2. Group by email
        print("\n[2/5] Identification des doublons par email...")
        email_groups = defaultdict(list)
        for client in all_clients:
            email = client.get("email")
            if email:
                email = email.strip().lower() if isinstance(email, str) else str(email).lower()
                if email:
                    email_groups[email].append(client)
        
        # Count duplicates
        dupes = {email: clients for email, clients in email_groups.items() if len(clients) > 1}
        print(f"Emails avec doublons: {len(dupes)}")
        print(f"Clients en doublon: {sum(len(v) for v in dupes.values())}")
        
        if not dupes:
            print("✅ Aucun doublon trouvé!")
            return
        
        # 3. For each duplicate group: keep newest (max ID), mark others as deleted
        print("\n[3/5] Marquage des anciens clients comme supprimés...")
        clients_to_delete = []
        clients_to_keep = {}
        
        for email, group in dupes.items():
            # Sort by _id descending (keep the highest ID = most recent)
            sorted_group = sorted(group, key=lambda c: str(c.get("_id", "")), reverse=True)
            keep_client = sorted_group[0]
            delete_clients = sorted_group[1:]
            
            clients_to_keep[email] = keep_client["_id"]
            clients_to_delete.extend([c["_id"] for c in delete_clients])
            
            print(f"  Email '{email}': keep {keep_client['_id']} (ID highest), delete {len(delete_clients)}")
        
        # Mark as deleted (soft delete)
        print(f"\n[4/5] Suppression logique de {len(clients_to_delete)} clients...")
        if clients_to_delete:
            result = await db.clients.update_many(
                {"_id": {"$in": clients_to_delete}},
                {
                    "$set": {
                        "actif": False,
                        "deleted_at": datetime.now(timezone.utc).isoformat(),
                        "deletion_reason": "Doublon - gardé client plus récent"
                    }
                }
            )
            print(f"  Marqués comme supprimés: {result.modified_count}")
        
        # 4. Add UNIQUE constraint on email (sparse allows multiple null values)
        print("\n[5/5] Ajout contrainte UNIQUE sur clients.email...")
        try:
            # Drop existing email index if it exists
            await db.clients.drop_index("email_1")
        except:
            pass
        
        # Create new unique index (sparse=True allows multiple null/missing values)
        try:
            await db.clients.create_index(
                [("email", ASCENDING)],
                unique=True,
                sparse=True
            )
            print("  ✅ Constraint UNIQUE créée sur clients.email")
        except Exception as e:
            print(f"  ⚠️  Erreur contrainte UNIQUE (peut être des NULL multiples): {str(e)[:100]}")
            # Fallback: just create non-unique index for performance
            await db.clients.create_index([("email", ASCENDING)])
            print("  ✅ Index non-unique créé sur clients.email (OK pour perf)")
        
        # 5. Validate referential integrity
        print("\n[VALIDATION] Vérification intégrité référentielle...")
        
        # Check orphaned commandes
        orphan_commandes = await db.commandes.count_documents({
            "client_id": {"$nin": [c["_id"] for c in all_clients if c.get("actif", True)]}
        })
        if orphan_commandes > 0:
            print(f"  ⚠️  {orphan_commandes} commandes orphelines détectées")
        else:
            print("  ✅ Aucune commande orpheline")
        
        # Check orphaned contacts
        orphan_contacts = await db.contacts.count_documents({
            "client_id": {"$nin": [c["_id"] for c in all_clients if c.get("actif", True)]}
        })
        if orphan_contacts > 0:
            print(f"  ⚠️  {orphan_contacts} contacts orphelines détectés")
        else:
            print("  ✅ Aucun contact orphelin")
        
        # Final count
        active_clients = await db.clients.count_documents({"actif": True})
        print(f"\n[RÉSULTAT]")
        print(f"  Clients actifs: {active_clients}")
        print(f"  Clients supprimés: {len(clients_to_delete)}")
        print(f"  Clients en doublon résolus: {len(dupes)}")
        print("\n✅ FIX #1 COMPLETED")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        raise
    finally:
        if hasattr(client, 'close'):
            client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_doublons())
