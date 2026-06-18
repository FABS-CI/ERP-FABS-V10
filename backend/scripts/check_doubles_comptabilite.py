#!/usr/bin/env python3
"""
check_doubles_comptabilite.py — Détecte les écritures comptables dupliquées.

Un doublon = deux écritures avec le même reference_source + type_source.
Usage: python scripts/check_doubles_comptabilite.py [--fix]
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "fabsci_erp"


async def main(fix: bool = False):
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # Vérifier que la collection existe
    count = await db.ecritures_comptables.count_documents({})
    print(f"Collection 'ecritures_comptables': {count} documents")

    if count == 0:
        print("Aucune écriture — pas de doublon possible.")
        client.close()
        return

    # Détecter les doublons via aggregation
    pipeline = [
        {
            "$group": {
                "_id": {
                    "reference_source": "$reference_source",
                    "type_source": "$type_source"
                },
                "count": {"$sum": 1},
                "ecriture_ids": {"$push": "$ecriture_id"},
                "references": {"$push": "$reference"},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]

    doublons = await db.ecritures_comptables.aggregate(pipeline).to_list(1000)

    if not doublons:
        print("✓ Aucun doublon détecté.")
        client.close()
        return

    print(f"\n⚠ {len(doublons)} groupe(s) de doublons détectés:")
    total_a_supprimer = 0

    for d in doublons:
        src = d["_id"]
        print(f"\n  reference_source={src['reference_source']} type={src['type_source']}")
        print(f"  {d['count']} écritures: {d['ecriture_ids']}")
        # Garder la première, supprimer les suivantes
        ids_to_delete = d["ecriture_ids"][1:]
        total_a_supprimer += len(ids_to_delete)
        print(f"  → À supprimer: {ids_to_delete}")

        if fix:
            result = await db.ecritures_comptables.delete_many(
                {"ecriture_id": {"$in": ids_to_delete}}
            )
            print(f"  ✓ {result.deleted_count} doublon(s) supprimé(s)")

    if not fix:
        print(f"\nTotal: {total_a_supprimer} écriture(s) en doublon.")
        print("Relancez avec --fix pour supprimer les doublons (conserve la première occurrence).")
    else:
        print(f"\nCorrection terminée: {total_a_supprimer} doublon(s) supprimé(s).")

    client.close()


if __name__ == "__main__":
    fix = "--fix" in sys.argv
    asyncio.run(main(fix))
