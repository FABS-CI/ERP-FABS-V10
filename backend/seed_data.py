"""
Script de seeding: utilisateurs, clients, rôles
"""
import asyncio
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import bcrypt
import re

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "fabsci_erp")

NOW = datetime.now(timezone.utc).isoformat()

# ─────────────────────────────────────────────
# 1. UTILISATEURS
# ─────────────────────────────────────────────
USERS = [
    {"nom_complet": "JOACHIN",            "email": "joachin@editionsfabsci.com",       "role": "responsable_magasinier"},
    {"nom_complet": "MME AHOMAN DADJE",   "email": "dadjelarissa@editionsfabsci.com",  "role": "secretariat"},
    {"nom_complet": "YAKE BEN",           "email": "yakeben@editionsfabsci.com",       "role": "service_logistique"},
    {"nom_complet": "NATACHA KOFFI",      "email": "natachakoffi@editionsfabsci.com",  "role": "comptable"},
    {"nom_complet": "NIANGORAN GEOGIE",   "email": "niangorangeorgie@editionsfabsci.com", "role": "gestionnaire_stock"},
    {"nom_complet": "DETY MICHEL",        "email": "detymichel@editionsfabsci.com",    "role": "directeur_commercial"},
]
DEFAULT_PASSWORD = "Fabs@2025"

# ─────────────────────────────────────────────
# 2. RÔLES
# ─────────────────────────────────────────────
def perm(modules_rw=[], modules_r=[], modules_denied=[]):
    perms = {}
    for m in modules_denied:
        perms[m] = 0
    for m in modules_r:
        perms[m] = 1
    for m in modules_rw:
        perms[m] = 2
    return perms

ROLES = [
    {
        "role_id": "super_admin",
        "nom": "Super Admin",
        "description": "Administrateur système avec accès total",
        "niveau": 8,
        "permissions": {m: 2 for m in [
            "dashboard","clients","produits","commandes","factures","paiements",
            "livraisons","retours","stock","colis","expeditions","logistique","fleet",
            "logistics_costs","comptabilite","comptabilite_avancee","bi_analytics",
            "rapports","rh","utilisateurs","parametres","backup",
            "workflow_approvals","file_storage","multi_channel_notifications","notifications"
        ]},
    },
    {
        "role_id": "directeur_general",
        "nom": "Directeur Général",
        "description": "Direction générale, accès lecture",
        "niveau": 7,
        "permissions": perm(
            modules_rw=[],
            modules_r=["dashboard","clients","produits","commandes","factures","paiements",
                       "livraisons","retours","stock","colis","expeditions","logistique",
                       "fleet","rapports","rh","notifications"],
            modules_denied=["comptabilite_avancee","logistics_costs","multi_channel_notifications",
                            "bi_analytics","workflow_approvals","file_storage","comptabilite",
                            "parametres","utilisateurs","backup"]
        ),
    },
    {
        "role_id": "comptable",
        "nom": "Comptable",
        "description": "Responsable comptabilité et finances",
        "niveau": 6,
        "permissions": perm(
            modules_rw=["factures","commandes","livraisons","paiements",
                        "comptabilite_avancee","comptabilite","rapports"],
            modules_r=["dashboard","clients","logistics_costs","rh","notifications"],
            modules_denied=["produits","retours","stock","colis","expeditions","logistique",
                            "fleet","multi_channel_notifications","bi_analytics",
                            "workflow_approvals","file_storage","utilisateurs","backup","parametres"]
        ),
    },
    {
        "role_id": "directeur_commercial",
        "nom": "Directeur Commercial",
        "description": "Responsable département commercial, lecture uniquement",
        "niveau": 5,
        "permissions": perm(
            modules_rw=[],
            modules_r=["dashboard","clients","produits","commandes","livraisons","retours",
                       "colis","expeditions","logistique","rapports","rh","notifications"],
            modules_denied=["factures","paiements","stock","comptabilite_avancee","fleet",
                            "logistics_costs","multi_channel_notifications","workflow_approvals",
                            "file_storage","comptabilite","utilisateurs","backup","parametres","bi_analytics"]
        ),
    },
    {
        "role_id": "gestionnaire_stock",
        "nom": "Gestionnaire Stock",
        "description": "Responsable stocks et entrepôts",
        "niveau": 4,
        "permissions": perm(
            modules_rw=["produits","retours","stock"],
            modules_r=["dashboard","commandes","livraisons","colis","notifications"],
            modules_denied=["clients","factures","paiements","expeditions","logistique",
                            "comptabilite_avancee","fleet","logistics_costs",
                            "multi_channel_notifications","bi_analytics","workflow_approvals",
                            "file_storage","comptabilite","rapports","utilisateurs","backup",
                            "parametres","rh"]
        ),
    },
    {
        "role_id": "responsable_magasinier",
        "nom": "Responsable Magasinier",
        "description": "Responsable magasin et colisage",
        "niveau": 3,
        "permissions": perm(
            modules_rw=["colis","retours"],
            modules_r=["dashboard","commandes","livraisons","notifications"],
            modules_denied=["clients","produits","factures","paiements","expeditions","logistique",
                            "stock","comptabilite_avancee","fleet","logistics_costs",
                            "multi_channel_notifications","bi_analytics","workflow_approvals",
                            "file_storage","comptabilite","rapports","utilisateurs","backup",
                            "parametres","rh"]
        ),
    },
    {
        "role_id": "secretariat",
        "nom": "Secrétariat",
        "description": "Support administratif",
        "niveau": 2,
        "permissions": perm(
            modules_rw=["clients","commandes","rh"],
            modules_r=["dashboard","notifications"],
            modules_denied=["produits","factures","paiements","livraisons","retours","stock",
                            "colis","expeditions","logistique","comptabilite_avancee","fleet",
                            "logistics_costs","multi_channel_notifications","bi_analytics",
                            "workflow_approvals","file_storage","comptabilite","rapports",
                            "utilisateurs","backup","parametres"]
        ),
    },
    {
        "role_id": "assistante",
        "nom": "Assistante",
        "description": "Support administratif, accès limité",
        "niveau": 1,
        "permissions": perm(
            modules_rw=["clients","commandes"],
            modules_r=["produits","notifications"],
            modules_denied=["dashboard","factures","paiements","livraisons","retours","stock",
                            "colis","expeditions","logistique","comptabilite_avancee","fleet",
                            "logistics_costs","multi_channel_notifications","bi_analytics",
                            "workflow_approvals","file_storage","comptabilite","rapports",
                            "utilisateurs","backup","parametres","rh"]
        ),
    },
    {
        "role_id": "service_logistique",
        "nom": "Service Logistique",
        "description": "Opérations logistiques et transports",
        "niveau": 0,
        "permissions": perm(
            modules_rw=["livraisons","expeditions","logistique","fleet","logistics_costs"],
            modules_r=["dashboard","colis","notifications"],
            modules_denied=["clients","produits","commandes","factures","paiements","retours",
                            "stock","comptabilite_avancee","bi_analytics","workflow_approvals",
                            "file_storage","comptabilite","rapports","utilisateurs","backup",
                            "parametres","rh","multi_channel_notifications"]
        ),
    },
]

# ─────────────────────────────────────────────
# 3. CLIENTS  (parsed from the MD file)
# ─────────────────────────────────────────────
RAW_CLIENTS_MD = """/home/user/Attachments/CLIENTS_FABS_CI_AVEC_NUMEROTATION_OS4gxP.md"""

def parse_clients(filepath):
    clients = []
    current_ville = "Abidjan"
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    type_map = {
        "LIBRAIRIES": "librairie", "LIBRAIRIE": "librairies",
        "LYCEES": "lycee", "LYCEE": "lycee",
        "COLLEGES": "college", "COLLEGE": "college",
        "GROUPE SCOLAIRE": "groupe_scolaire",
        "IEP": "iep", "EPP": "epp",
        "CATHOLIQUE": "catholique", "METHODISTE": "methodiste",
        "MEMO": "memo", "INSPECTEUR": "inspecteur",
        "DREN": "dren", "UP": "up",
        "PARTICULIERS": "particulier", "PARTICULIER": "particulier",
        "INSTITUT": "institut",
    }

    last_was_separator = False
    for line in lines:
        stripped = line.strip()
        # Section separator
        if stripped.startswith("===="):
            last_was_separator = True
            continue
        # City name line (comes right after ====)
        if last_was_separator and stripped and not stripped.startswith("-") and "Client" not in stripped:
            current_ville = stripped.title()
            last_was_separator = False
            continue
        last_was_separator = False
        # Skip header/separator lines
        if stripped.startswith("-") or stripped.startswith("Client") or not stripped:
            continue
        # Client row: starts with 5 digits
        if re.match(r'^\d{5}', stripped):
            # Split by 2+ spaces
            parts = re.split(r'  +', stripped)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) < 1:
                continue
            # parts[0] = "00001 | NOM DU CLIENT"
            m = re.match(r'^(\d{5})\s*\|\s*(.+)', parts[0])
            if not m:
                continue
            num = m.group(1)
            nom = m.group(2).strip()
            representant = parts[1].strip() if len(parts) > 1 else ""
            telephone = parts[2].strip() if len(parts) > 2 else ""
            type_client_raw = parts[3].strip() if len(parts) > 3 else ""
            # Sometimes email is in parts[3] and type in parts[4]
            email = ""
            if len(parts) > 3 and "@" in parts[3]:
                email = parts[3].strip()
                type_client_raw = parts[4].strip() if len(parts) > 4 else ""

            type_client = type_map.get(type_client_raw.upper(), type_client_raw.lower() or "autre")
            if not nom:
                continue
            clients.append({
                "numero": num,
                "nom": nom,
                "representant": representant,
                "telephone": telephone,
                "email": email,
                "type_client": type_client,
                "ville": current_ville,
            })
    return clients

def dedup_clients(clients):
    """Remove duplicates by (nom, telephone) keeping first occurrence."""
    seen = set()
    unique = []
    for c in clients:
        key = (c["nom"].upper().strip(), c["telephone"].strip())
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # ── ROLES ──────────────────────────────────
    print("🔐 Insertion des rôles...")
    for role in ROLES:
        role["created_at"] = NOW
        role["updated_at"] = NOW
        existing = await db.roles.find_one({"role_id": role["role_id"]})
        if existing:
            await db.roles.replace_one({"role_id": role["role_id"]}, role)
            print(f"  ↻ Rôle mis à jour: {role['nom']}")
        else:
            await db.roles.insert_one(role)
            print(f"  ✅ Rôle créé: {role['nom']}")

    # ── USERS ──────────────────────────────────
    print("\n👤 Insertion des utilisateurs...")
    hashed_pw = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
    for i, u in enumerate(USERS, start=3):
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            print(f"  ⏩ Existe déjà: {u['email']}")
            continue
        doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": u["email"],
            "nom_complet": u["nom_complet"],
            "role": u["role"],
            "actif": True,
            "password_hash": hashed_pw,
            "picture": None,
            "created_at": NOW,
            "updated_at": NOW,
        }
        await db.users.insert_one(doc)
        print(f"  ✅ {u['nom_complet']} ({u['role']}) — mdp: {DEFAULT_PASSWORD}")

    # ── CLIENTS ────────────────────────────────
    print("\n🏢 Import des clients...")
    raw = parse_clients(RAW_CLIENTS_MD)
    clients = dedup_clients(raw)
    print(f"  {len(raw)} clients parsés → {len(clients)} après déduplification")

    # Get existing client noms to avoid duplicates
    existing_noms = set()
    async for c in db.clients.find({}, {"nom": 1}):
        existing_noms.add(c["nom"].upper().strip())

    inserted = 0
    skipped = 0
    # Get current max reference number
    last = await db.clients.find_one({}, sort=[("reference", -1)])
    ref_counter = 3  # already have 2 seed clients
    if last and last.get("reference"):
        m = re.search(r'(\d+)$', last["reference"])
        if m:
            ref_counter = int(m.group(1))

    for c in clients:
        if c["nom"].upper().strip() in existing_noms:
            skipped += 1
            continue
        ref_counter += 1
        uid = uuid.uuid4().hex[:12]
        doc = {
            "client_id": f"cli_{uid}",
            "reference": f"FABS-CLI-{ref_counter:04d}",
            "nom": c["nom"],
            "type_client": c["type_client"],
            "representant": c["representant"],
            "telephone": c["telephone"],
            "email": c["email"],
            "adresse": "",
            "ville": c["ville"],
            "plafond_credit": 0,
            "solde": 0,
            "notes": "",
            "actif": True,
            "created_by": "admin_super_001",
            "created_at": NOW,
            "updated_at": NOW,
        }
        await db.clients.insert_one(doc)
        existing_noms.add(c["nom"].upper().strip())
        inserted += 1

    print(f"  ✅ {inserted} clients insérés, {skipped} ignorés (déjà présents)")

    print(f"\n🎉 Seeding terminé!")
    print(f"   Rôles: {len(ROLES)}")
    print(f"   Utilisateurs ajoutés: {len(USERS)}")
    print(f"   Clients importés: {inserted}")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
