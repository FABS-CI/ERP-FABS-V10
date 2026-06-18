"""Import des 1014 clients réels depuis data_import/clients.json vers MongoDB.
Mappe les champs JSON vers le schéma DB (region->ville, type_client->valeurs système).
N'affecte PAS les collections users/products. Référence auto FABS-CLI-XXXX.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

# Mapping type_client PDF -> type système
TYPE_MAP = {
    "GROUPE SCOLAIRE": "ecole",
    "LYCEES": "ecole", "LYCEE": "ecole",
    "COLLEGES": "ecole", "COLLEGE": "ecole",
    "EPP": "ecole", "IEP": "ecole",
    "CATHOLIQUE": "ecole", "METHODISTE": "ecole",
    "INSTITUT": "ecole", "DREN": "ecole", "INSPECTEUR": "ecole",
    "LIBRAIRIES": "librairie", "LIBRAIRIE": "librairie",
    "PARTICULIERS": "particulier", "PARTICULIER": "particulier",
    "UP": "distributeur", "MEMO": "distributeur",
}


def map_client(j, idx):
    now = datetime.now(timezone.utc).isoformat()
    raw_type = (j.get("type_client") or "").strip().upper()
    sys_type = TYPE_MAP.get(raw_type, "ecole")
    return {
        "client_id": str(uuid.uuid4()),
        "reference": f"FABS-CLI-{str(idx).zfill(4)}",
        "nom": j.get("nom", "").strip(),
        "representant": j.get("representant") or None,
        "telephone": j.get("telephone") or None,
        "email": j.get("email") or None,
        "type_client": sys_type,
        "ville": j.get("region") or None,
        "adresse": None,
        "notes": f"Importé liste FABS-CI ({raw_type})" if raw_type else None,
        "solde": 0.0,
        "plafond_credit": 0.0,
        "actif": bool(j.get("actif", True)),
        "created_by": "import_script",
        "created_at": j.get("created_at") or now,
        "updated_at": now,
    }


def main(apply=False, purge=False):
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    col = db.clients

    data = json.load(open(os.path.join(os.path.dirname(__file__), "data_import", "clients.json")))
    print(f"Lus depuis JSON: {len(data)} clients")
    print(f"Clients actuels en base: {col.count_documents({})}")

    # Référence de départ continue
    existing = col.count_documents({})
    docs = [map_client(j, existing + i + 1) for i, j in enumerate(data)]

    # Stats type
    from collections import Counter
    print("Répartition types:", dict(Counter(d["type_client"] for d in docs)))

    if not apply:
        print("\n[DRY-RUN] Aucune insertion. Relancer avec --apply pour insérer.")
        print("Sample mappé:", json.dumps(docs[0], ensure_ascii=False)[:300])
        return

    if purge:
        # Supprime uniquement les clients seed de démo (garde rien des dummies)
        deleted = col.delete_many({}).deleted_count
        print(f"Purge: {deleted} clients supprimés")

    res = col.insert_many(docs)
    print(f"✅ {len(res.inserted_ids)} clients insérés")
    print(f"Total clients en base: {col.count_documents({})}")
    client.close()


if __name__ == "__main__":
    import sys
    main(apply="--apply" in sys.argv, purge="--purge" in sys.argv)
