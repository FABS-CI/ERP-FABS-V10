"""
Seed des 8 utilisateurs officiels EDITIONS FABS-CI (2026-2027)
Source : utilisateurs_editionsfabsci.txt (artefact utilisateur)

- Idempotent (UPSERT sur email)
- Mot de passe initial commun : "Fabs@2026" (à changer au premier login)
- Conserve les comptes existants : si l'email existe déjà, on ne touche PAS au password_hash
  (sauf si --reset-password est passé en argument)

Usage :
    python -m backend.scripts.seed_utilisateurs_fabs
    python -m backend.scripts.seed_utilisateurs_fabs --reset-password
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient


# Liste officielle des 8 utilisateurs EDITIONS FABS-CI (2026-2027)
USERS = [
    {"nom_complet": "JOACHIN",                "email": "joachin@editionsfabsci.com",          "role": "responsable_magasinier"},
    {"nom_complet": "MME AHOMAN DADJE",       "email": "dadjelarissa@editionsfabsci.com",     "role": "secretariat"},
    {"nom_complet": "YAKE BEN",               "email": "yakeben@editionsfabsci.com",          "role": "service_logistique"},
    {"nom_complet": "NATACHA KOFFI",          "email": "natachakoffi@editionsfabsci.com",     "role": "comptable"},
    {"nom_complet": "NIANGORAN GEOGIE",       "email": "niangorangeorgie@editionsfabsci.com", "role": "gestionnaire_stock"},
    {"nom_complet": "DETY MICHEL",            "email": "detymichel@editionsfabsci.com",       "role": "directeur_commercial"},
    {"nom_complet": "ALI MAMIN",              "email": "ali.mamin@editionsfabsci.com",        "role": "directeur_general"},
    {"nom_complet": "AKE APPIA YVES DORIS",   "email": "pissken@editionsfabsci.com",          "role": "super_admin"},
]

DEFAULT_PASSWORD = "Fabs@2026"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def main(reset_password: bool = False):
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    now = datetime.now(timezone.utc).isoformat()
    pwd_hash = hash_password(DEFAULT_PASSWORD)

    created, updated, kept = 0, 0, 0
    for u in USERS:
        existing = await db.users.find_one({"email": u["email"].lower()})
        if existing:
            updates = {
                "nom_complet": u["nom_complet"],
                "role": u["role"],
                "actif": True,
                "updated_at": now,
            }
            if reset_password:
                updates["password_hash"] = pwd_hash
            await db.users.update_one({"email": u["email"].lower()}, {"$set": updates})
            if reset_password:
                updated += 1
                print(f"  ↻ Mis à jour (avec reset password) : {u['email']} [{u['role']}]")
            else:
                kept += 1
                print(f"  = Conservé (existait déjà) : {u['email']} [{u['role']}]")
        else:
            doc = {
                "user_id": f"user_{uuid.uuid4().hex[:12]}",
                "email": u["email"].lower(),
                "nom_complet": u["nom_complet"],
                "role": u["role"],
                "actif": True,
                "password_hash": pwd_hash,
                "picture": None,
                "created_at": now,
                "updated_at": now,
            }
            await db.users.insert_one(doc)
            created += 1
            print(f"  + Créé : {u['email']} [{u['role']}]")

    print()
    print(f"✅ Terminé : {created} créés, {updated} mis à jour, {kept} conservés.")
    if created > 0 or reset_password:
        print(f"🔐 Mot de passe initial pour les NOUVEAUX comptes : {DEFAULT_PASSWORD}")
        print("   ⚠️  Les utilisateurs doivent le changer à leur premier login.")
    client.close()


if __name__ == "__main__":
    # Charger /app/backend/.env
    from pathlib import Path
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    reset = "--reset-password" in sys.argv
    asyncio.run(main(reset_password=reset))
