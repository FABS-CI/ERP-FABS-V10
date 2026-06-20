#!/usr/bin/env python3
"""
Import des 9 utilisateurs FABS-CI avec leurs rôles et habilitations.
Crée les utilisateurs et leurs rôles correspondants.
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient
import bcrypt

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# Les 9 utilisateurs avec leurs données
USERS_DATA = [
    {
        "user_id": "admin_super_001",
        "nom_complet": "AKE APPIA YVES DORIS",
        "email": "pissken@editionsfabsci.com",
        "password": "Admin@2025",
        "role": "super_admin",
        "permissions": ["all"]
    },
    {
        "user_id": "dg_001",
        "nom_complet": "ALI MAMIN",
        "email": "ali.mamin@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "directeur_general",
        "permissions": ["view_all", "edit_clients", "edit_commandes", "view_reports"]
    },
    {
        "user_id": "magasinier_001",
        "nom_complet": "JOACHIN",
        "email": "joachin@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "responsable_magasinier",
        "permissions": ["manage_stock", "view_stock", "edit_mouvements"]
    },
    {
        "user_id": "secretariat_001",
        "nom_complet": "MME AHOMAN DADJE",
        "email": "dadjelarissa@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "secretariat",
        "permissions": ["view_commandes", "create_commandes", "view_clients", "manage_documents"]
    },
    {
        "user_id": "logistique_001",
        "nom_complet": "YAKE BEN",
        "email": "yakeben@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "service_logistique",
        "permissions": ["view_commandes", "manage_livraisons", "view_stock", "manage_bons_livraison"]
    },
    {
        "user_id": "comptable_001",
        "nom_complet": "NATACHA KOFFI",
        "email": "natachakoffi@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "comptable",
        "permissions": ["view_factures", "manage_paiements", "view_comptabilite", "generate_reports"]
    },
    {
        "user_id": "stock_001",
        "nom_complet": "NIANGORAN GEORGIE",
        "email": "niangorangeorgie@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "gestionnaire_stock",
        "permissions": ["manage_stock", "view_stock", "manage_mouvements_stock", "edit_articles"]
    },
    {
        "user_id": "commercial_001",
        "nom_complet": "DETY MICHEL",
        "email": "detymichel@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "directeur_commercial",
        "permissions": ["manage_clients", "manage_commandes", "view_factures", "view_analytics"]
    },
    {
        "user_id": "assistante_001",
        "nom_complet": "AMENAN",
        "email": "amenan@editionsfabsci.com",
        "password": "Fabs@2025",
        "role": "assistante",
        "permissions": ["view_commandes", "view_clients", "create_documents", "manage_notes"]
    },
]

def main(apply=False, purge=False):
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    users_col = db.users
    roles_col = db.roles
    
    print(f"📊 Utilisateurs actuels: {users_col.count_documents({})}")
    print(f"📊 Rôles actuels: {roles_col.count_documents({})}")
    
    # Construire les docs utilisateurs
    user_docs = []
    for u in USERS_DATA:
        user_docs.append({
            "user_id": u["user_id"],
            "email": u["email"],
            "nom_complet": u["nom_complet"],
            "role": u["role"],
            "actif": True,
            "password_hash": hash_password(u["password"]),
            "picture": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
    
    # Construire les docs rôles (permissions)
    roles_by_type = {}
    for u in USERS_DATA:
        role = u["role"]
        if role not in roles_by_type:
            roles_by_type[role] = {
                "role_name": role,
                "permissions": u["permissions"],
                "description": f"Rôle {role}",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
    
    print(f"\n📝 À insérer: {len(user_docs)} utilisateurs, {len(roles_by_type)} rôles")
    print(f"   Rôles: {', '.join(roles_by_type.keys())}")
    
    if not apply:
        print("\n[DRY-RUN] Aucune insertion. Relancer avec --apply pour insérer.")
        print("\n📧 Compte admin (déjà créé):")
        print("   Email: pissken@editionsfabsci.com")
        print("   Password: Admin@2025")
        print("\n📧 Autres comptes:")
        for u in USERS_DATA[1:]:
            print(f"   {u['email']} / {u['password']}")
        return
    
    if purge:
        # Supprimer les utilisateurs (sauf super_admin créé via create_super_admin.py)
        deleted_users = users_col.delete_many({"user_id": {"$ne": "admin_super_001"}}).deleted_count
        deleted_roles = roles_col.delete_many({}).deleted_count
        print(f"🗑️  Purge: {deleted_users} utilisateurs (sauf super_admin), {deleted_roles} rôles supprimés")
    
    # Insérer les rôles
    res_roles = roles_col.insert_many(list(roles_by_type.values()))
    print(f"✅ {len(res_roles.inserted_ids)} rôles insérés")
    
    # Insérer les utilisateurs (sauf si déjà existants)
    users_to_insert = []
    for user in user_docs:
        existing = users_col.find_one({"email": user["email"]})
        if not existing:
            users_to_insert.append(user)
    
    if users_to_insert:
        res_users = users_col.insert_many(users_to_insert)
        print(f"✅ {len(res_users.inserted_ids)} utilisateurs insérés")
    else:
        print("ℹ️  Tous les utilisateurs existent déjà")
    
    print(f"\n📊 Après import:")
    print(f"   Utilisateurs total: {users_col.count_documents({})}")
    print(f"   Rôles total: {roles_col.count_documents({})}")
    
    # Afficher les comptes
    print("\n🔐 Comptes de connexion:")
    all_users = list(users_col.find({}, {"email": 1, "nom_complet": 1, "role": 1, "_id": 0}).sort("role", 1))
    for user in all_users:
        password = next((u["password"] for u in USERS_DATA if u["email"] == user["email"]), "?")
        print(f"   [{user['role']:25}] {user['email']:35} / {password}")
    
    client.close()

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    purge = "--purge" in sys.argv
    main(apply=apply, purge=purge)
