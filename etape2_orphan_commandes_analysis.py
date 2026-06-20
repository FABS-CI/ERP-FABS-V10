#!/usr/bin/env python3
"""
ÉTAPE 2: Analyse des 9 commandes orphelines détectées
Objectif: Confirmer que AUCUNE donnée métier n'est perdue
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson.objectid import ObjectId

# MongoDB config
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

async def analyze_orphaned_commandes():
    """Analyze orphaned commandes"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db: AsyncIOMotorDatabase = client[DB_NAME]
    
    print("=" * 100)
    print("ÉTAPE 2: ANALYSE DES 9 COMMANDES ORPHELINES")
    print("=" * 100)
    
    try:
        # 1. Find orphaned commandes (client_id not in active clients)
        print("\n[1/6] Récupération clients actifs...")
        active_clients = await db.clients.find({"actif": True}).to_list(None)
        active_client_ids = [c["_id"] for c in active_clients]
        print(f"  Clients actifs: {len(active_clients)}")
        
        # 2. Find deleted clients
        print("\n[2/6] Récupération clients supprimés (soft-delete)...")
        deleted_clients = await db.clients.find({"actif": False}).to_list(None)
        deleted_client_ids = {str(c["_id"]): c for c in deleted_clients}
        print(f"  Clients supprimés: {len(deleted_clients)}")
        
        # 3. Find orphaned commandes
        print("\n[3/6] Détection commandes orphelines...")
        orphaned_commandes = await db.commandes.find({
            "client_id": {"$nin": active_client_ids}
        }).to_list(None)
        print(f"  Commandes orphelines détectées: {len(orphaned_commandes)}")
        
        if not orphaned_commandes:
            print("  ✅ Aucune commande orpheline!")
            return True
        
        # 4. Analyze each orphaned commande
        print("\n[4/6] Analyse détaillée (1 par 1)...")
        print("")
        
        for idx, cmd in enumerate(orphaned_commandes, 1):
            print(f"┌─ COMMANDE #{idx}/{len(orphaned_commandes)} ─────────────────────────")
            print(f"│  ID Commande: {cmd.get('_id')}")
            
            client_id = cmd.get("client_id")
            print(f"│  Client ID: {client_id}")
            
            # Find original client
            original_client = None
            for dc_id, dc in deleted_client_ids.items():
                if str(client_id) == dc_id or (hasattr(client_id, '__str__') and str(client_id) == str(dc["_id"])):
                    original_client = dc
                    break
            
            if original_client:
                print(f"│  Client Original: {original_client.get('nom', 'N/A')} ({original_client.get('email', 'N/A')})")
                print(f"│  Raison suppression: {original_client.get('deletion_reason', 'N/A')}")
                print(f"│  Date suppression: {original_client.get('deleted_at', 'N/A')}")
            else:
                print(f"│  ⚠️  Client original NON TROUVÉ en DB")
            
            # Get commande details
            print(f"│  Numéro: {cmd.get('numero_commande', 'N/A')}")
            print(f"│  Date: {cmd.get('date_commande', 'N/A')}")
            print(f"│  Montant: {cmd.get('montant_total', 0)} FCFA")
            print(f"│  Status: {cmd.get('statut', 'N/A')}")
            
            # Find facture associée
            facture = await db.factures.find_one({"commande_id": cmd["_id"]})
            if facture:
                print(f"│  Facture: {facture.get('numero_facture', 'N/A')} (ID: {facture['_id']})")
                print(f"│  Facture status: {facture.get('statut', 'N/A')}")
            else:
                print(f"│  Facture: ❌ AUCUNE")
            
            # Find paiements associés
            paiements = await db.paiements.find({"commande_id": cmd["_id"]}).to_list(None)
            if paiements:
                print(f"│  Paiements: {len(paiements)}")
                for p in paiements:
                    print(f"│    - {p.get('montant_total', 0)} FCFA ({p.get('statut', 'N/A')})")
            else:
                print(f"│  Paiements: ❌ AUCUN")
            
            # Find écritures comptables
            ecritures = await db.ecritures_comptables.find({"commande_id": cmd["_id"]}).to_list(None)
            if ecritures:
                print(f"│  Écritures comptables: {len(ecritures)}")
            else:
                print(f"│  Écritures: ❌ AUCUNE")
            
            print(f"└────────────────────────────────────────\n")
        
        # 5. Data integrity check
        print("[5/6] Vérification intégrité données...")
        
        # Check factures orphelines
        orphan_factures = await db.factures.count_documents({
            "commande_id": {"$nin": [c["_id"] for c in await db.commandes.find({"actif": True}).to_list(None)]}
        })
        print(f"  Factures sans commande active: {orphan_factures}")
        
        # Check paiements orphelins
        orphan_paiements = await db.paiements.count_documents({
            "commande_id": {"$nin": [c["_id"] for c in await db.commandes.find({"actif": True}).to_list(None)]}
        })
        print(f"  Paiements sans commande active: {orphan_paiements}")
        
        # 6. Summary
        print("\n[6/6] RÉSUMÉ INTÉGRITÉ DONNÉES...")
        
        total_commandes = await db.commandes.count_documents({})
        active_commandes = await db.commandes.count_documents({"actif": True})
        
        print(f"  Total commandes: {total_commandes}")
        print(f"  Commandes actives: {active_commandes}")
        print(f"  Commandes orphelines: {len(orphaned_commandes)}")
        print(f"  Taux orphelines: {(len(orphaned_commandes)/total_commandes*100):.2f}%")
        
        # Final verdict
        print("\n" + "=" * 100)
        print("VERDICT INTÉGRITÉ")
        print("=" * 100)
        
        if len(orphaned_commandes) <= 1 and orphan_factures == 0 and orphan_paiements == 0:
            print("✅ INTÉGRITÉ CONFIRMÉE")
            print("   - Commandes orphelines acceptables (soft-delete client)")
            print("   - Aucune facture orpheline")
            print("   - Aucun paiement orphelin")
            print("   - Pas de perte de données métier")
            return True
        else:
            print("⚠️  ALERTES DÉTECTÉES")
            if orphan_factures > 0:
                print(f"   - {orphan_factures} factures orphelines")
            if orphan_paiements > 0:
                print(f"   - {orphan_paiements} paiements orphelins")
            return False
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if hasattr(client, 'close'):
            client.close()

if __name__ == "__main__":
    result = asyncio.run(analyze_orphaned_commandes())
    exit(0 if result else 1)
