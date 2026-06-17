"""
seed_comptabilite.py — Seed des journaux comptables et du plan SYSCOHADA.

Idempotent : vérifie count > 0 avant d'insérer.
Journaux : VTE, ACH, BQ, CAI, OD
Comptes SYSCOHADA : 411000, 401000, 701000, 601000, 443100, 445100, 521000, 571000, 707000
"""

import uuid
from datetime import datetime, timezone


JOURNAUX = [
    {
        "code": "VTE",
        "intitule": "Journal des Ventes",
        "type": "ventes",
        "actif": True,
    },
    {
        "code": "ACH",
        "intitule": "Journal des Achats",
        "type": "achats",
        "actif": True,
    },
    {
        "code": "BQ",
        "intitule": "Journal de Banque",
        "type": "banque",
        "actif": True,
    },
    {
        "code": "CAI",
        "intitule": "Journal de Caisse",
        "type": "od",
        "actif": True,
    },
    {
        "code": "OD",
        "intitule": "Journal des Opérations Diverses",
        "type": "od",
        "actif": True,
    },
]

PLAN_COMPTABLE = [
    {
        "numero": "411000",
        "libelle": "Clients",
        "classe": "4",
        "type": "actif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "401000",
        "libelle": "Fournisseurs",
        "classe": "4",
        "type": "passif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "701000",
        "libelle": "Ventes de marchandises",
        "classe": "7",
        "type": "produit",
        "nature": "resultat",
        "actif": True,
    },
    {
        "numero": "601000",
        "libelle": "Achats de marchandises",
        "classe": "6",
        "type": "charge",
        "nature": "resultat",
        "actif": True,
    },
    {
        "numero": "443100",
        "libelle": "TVA collectée",
        "classe": "4",
        "type": "passif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "445100",
        "libelle": "TVA déductible",
        "classe": "4",
        "type": "actif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "521000",
        "libelle": "Banque",
        "classe": "5",
        "type": "actif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "571000",
        "libelle": "Caisse",
        "classe": "5",
        "type": "actif",
        "nature": "bilan",
        "actif": True,
    },
    {
        "numero": "707000",
        "libelle": "Produits accessoires",
        "classe": "7",
        "type": "produit",
        "nature": "resultat",
        "actif": True,
    },
]


async def seed_journaux_et_plan_comptable(db) -> dict:
    """
    Seed journaux comptables + plan SYSCOHADA.
    Idempotent — skip si données déjà présentes.
    Returns {"journaux": int, "comptes": int} counts of inserted docs.
    """
    now = datetime.now(timezone.utc).isoformat()
    inserted = {"journaux": 0, "comptes": 0}

    # --- Journaux ---
    # Fix existing docs without journal_id/intitule
    async for doc in db.journaux_comptables.find({}):
        update = {}
        if "journal_id" not in doc:
            update["journal_id"] = f"journal_{doc['code'].lower()}_{str(uuid.uuid4())[:8]}"
        if "intitule" not in doc and "libelle" in doc:
            update["intitule"] = doc["libelle"]
        if update:
            await db.journaux_comptables.update_one({"_id": doc["_id"]}, {"$set": update})

    count_journaux = await db.journaux_comptables.count_documents({})
    if count_journaux == 0:
        docs = [
            {**j, "journal_id": f"journal_{j['code'].lower()}_{str(uuid.uuid4())[:8]}", "created_at": now, "updated_at": now}
            for j in JOURNAUX
        ]
        result = await db.journaux_comptables.insert_many(docs)
        inserted["journaux"] = len(result.inserted_ids)
    else:
        # Upsert manquants seulement
        for j in JOURNAUX:
            existing = await db.journaux_comptables.find_one({"code": j["code"]})
            if not existing:
                doc = {
                    **j,
                    "journal_id": f"journal_{j['code'].lower()}_{str(uuid.uuid4())[:8]}",
                    "created_at": now,
                    "updated_at": now,
                }
                await db.journaux_comptables.insert_one(doc)
                inserted["journaux"] += 1

    # --- Plan comptable ---
    count_plan = await db.plan_comptable.count_documents({})
    if count_plan == 0:
        docs = [{**c, "created_at": now, "updated_at": now} for c in PLAN_COMPTABLE]
        result = await db.plan_comptable.insert_many(docs)
        inserted["comptes"] = len(result.inserted_ids)
    else:
        for c in PLAN_COMPTABLE:
            existing = await db.plan_comptable.find_one({"numero": c["numero"]})
            if not existing:
                await db.plan_comptable.insert_one({**c, "created_at": now, "updated_at": now})
                inserted["comptes"] += 1

    return inserted
