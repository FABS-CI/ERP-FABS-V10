"""Import des 56 produits réels depuis data_import/articles.json vers MongoDB (collection produits)."""
import json
import os
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")


def map_produit(j):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "produit_id": str(uuid.uuid4()),
        "code_article": j.get("code") or j.get("reference") or "",
        "titre": j.get("reference") or j.get("titre") or "",
        "categorie": j.get("categorie") or "premier_cycle",
        "niveau_scolaire": j.get("niveau_scolaire") or None,
        "prix_vente": float(j.get("prix_vente") or 0),
        "stock_actuel": int(j.get("stock") or 0),
        "seuil_alerte": int(j.get("seuil_alerte") or 10),
        "actif": bool(j.get("actif", True)),
        "created_by": "import_script",
        "created_at": j.get("created_at") or now,
        "updated_at": now,
    }


def main(apply=False, purge=False):
    db = MongoClient(MONGO_URL)[DB_NAME]
    col = db.produits
    data = json.load(open(os.path.join(os.path.dirname(__file__), "data_import", "articles.json")))
    print(f"Lus depuis JSON: {len(data)} produits")
    print(f"Produits actuels en base: {col.count_documents({})}")
    docs = [map_produit(j) for j in data]
    if not apply:
        print("\n[DRY-RUN] Relancer avec --apply.")
        print("Sample:", json.dumps(docs[0], ensure_ascii=False)[:300])
        return
    if purge:
        print(f"Purge: {col.delete_many({}).deleted_count} produits supprimés")
    res = col.insert_many(docs)
    print(f"✅ {len(res.inserted_ids)} produits insérés | Total: {col.count_documents({})}")


if __name__ == "__main__":
    import sys
    main(apply="--apply" in sys.argv, purge="--purge" in sys.argv)
