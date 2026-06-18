#!/usr/bin/env python3
"""
check_products.py — Vérifie l'état de la collection `products` (obsolète)
vs la collection canonique `produits`.
Usage: python check_products.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "fabsci_erp"


async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    count_products = await db.products.count_documents({})
    count_produits = await db.produits.count_documents({})

    print(f"collection 'products'  (obsolète) : {count_products} documents")
    print(f"collection 'produits'  (canonique): {count_produits} documents")

    if count_products > 0:
        sample = await db.products.find_one({}, {"_id": 0, "product_id": 1, "reference": 1, "nom": 1})
        print(f"Exemple products : {sample}")

    # Vérifier si un module actif référence products
    print()
    print("AVERTISSEMENT : La collection 'products' est un catalogue legacy (PRD00001..56).")
    print("La collection 'produits' est le catalogue actif (UUIDs).")
    print("Aucun module actif n'utilise 'products' — suppression sécurisée via drop_products.py")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
