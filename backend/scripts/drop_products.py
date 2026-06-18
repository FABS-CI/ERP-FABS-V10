#!/usr/bin/env python3
"""
drop_products.py — Supprime la collection obsolète `products`.
PRÉREQUIS : mongodump effectué avant exécution.
Usage: python drop_products.py [--confirm]
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "fabsci_erp"


async def main(confirmed: bool):
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    count = await db.products.count_documents({})
    print(f"Collection 'products' : {count} documents trouvés.")

    if count == 0:
        print("Collection déjà vide ou inexistante. Rien à faire.")
        client.close()
        return

    if not confirmed:
        print()
        print("DANGER : Cette opération est IRRÉVERSIBLE sans backup.")
        print("Relancez avec --confirm pour procéder.")
        print("Conseil : mongodump --db fabsci_erp --out /home/user/backup_avant_drop")
        client.close()
        return

    await db.products.drop()
    count_after = await db.products.count_documents({})
    print(f"Collection 'products' supprimée. Documents restants : {count_after}")

    # Vérifier que produits est intact
    count_produits = await db.produits.count_documents({})
    print(f"Collection 'produits' (canonique) : {count_produits} documents — INTACT.")

    client.close()


if __name__ == "__main__":
    confirmed = "--confirm" in sys.argv
    asyncio.run(main(confirmed))
