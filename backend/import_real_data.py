#!/usr/bin/env python3
"""
Import des VRAIES données FABS-CI : users, articles (catalogue 2025-2026), clients.
Purge toutes les données fictives/démo et réinjecte le réel.

USAGE:
    python import_real_data.py --dry-run   # parse + stats, n'écrit rien
    python import_real_data.py --apply     # purge + insère réellement
"""
from __future__ import annotations
import argparse
import re
import sys
import uuid
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "fabsci_erp"

ART_FILE = Path("/home/user/Attachments/ARTICLES_FABS_CI_NUMEROTES_9EAPbW.txt")
CLI_FILE = Path("/home/user/Attachments/CLIENTS_EDITIONS_FABS-CI_-_Liste_des_Clients_d4ac8s.txt")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ===========================================================================
# 1) USERS  (les 9 vrais)
# ===========================================================================
USERS = [
    {"user_id": "admin_super_001", "nom_complet": "AKE APPIA YVES DORIS", "email": "pissken@editionsfabsci.com",      "password": "Admin@2025", "role": "super_admin"},
    {"user_id": "dg_001",          "nom_complet": "ALI MAMIN",            "email": "ali.mamin@editionsfabsci.com",     "password": "Fabs@2025",  "role": "directeur_general"},
    {"user_id": "magasinier_001",  "nom_complet": "JOACHIN",              "email": "joachin@editionsfabsci.com",       "password": "Fabs@2025",  "role": "responsable_magasinier"},
    {"user_id": "secretariat_001", "nom_complet": "MME AHOMAN DADJE",     "email": "dadjelarissa@editionsfabsci.com",  "password": "Fabs@2025",  "role": "secretariat"},
    {"user_id": "logistique_001",  "nom_complet": "YAKE BEN",             "email": "yakeben@editionsfabsci.com",       "password": "Fabs@2025",  "role": "service_logistique"},
    {"user_id": "comptable_001",   "nom_complet": "NATACHA KOFFI",        "email": "natachakoffi@editionsfabsci.com",  "password": "Fabs@2025",  "role": "comptable"},
    {"user_id": "stock_001",       "nom_complet": "NIANGORAN GEORGIE",    "email": "niangorangeorgie@editionsfabsci.com","password": "Fabs@2025", "role": "gestionnaire_stock"},
    {"user_id": "commercial_001",  "nom_complet": "DETY MICHEL",          "email": "detymichel@editionsfabsci.com",    "password": "Fabs@2025",  "role": "directeur_commercial"},
    {"user_id": "assistante_001",  "nom_complet": "AMENAN",               "email": "amenan@editionsfabsci.com",        "password": "Fabs@2025",  "role": "assistante"},
]


def build_users():
    docs = []
    for u in USERS:
        docs.append({
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
    return docs


# ===========================================================================
# 2) ARTICLES  (catalogue 2025-2026)
# ===========================================================================
# Map titre de section (catalogue) -> categorie systeme
SECTION_TO_CAT = {
    "MATERNELLE / PRIMAIRE": "primaire",
    "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS": "premier_cycle",
    "SECOND CYCLE - MÉMOS ET TESTS BEPC": "premier_cycle",
    "SECOND CYCLE - MÉMOS ET TESTS BAC": "second_cycle",
    "LITTÉRATURE / ROMANS": "litterature",
}


def parse_fcfa(s: str):
    """ '2 000 FCFA' -> 2000.0 ; 'N/A' -> None ; '3000' -> 3000.0 """
    if not s:
        return None
    s = s.strip()
    if s.upper().startswith("N/A") or s.upper() == "N/A":
        return None
    m = re.search(r"([\d\s.]+)", s.replace("\xa0", " "))
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace(".", "")
    if not num.isdigit():
        return None
    return float(num)


# Affinage catégorie d'après le niveau/titre (maternelle vs primaire)
def refine_categorie(base_cat: str, reference: str, titre: str) -> str:
    t = titre.upper()
    if base_cat == "primaire":
        if "PRÉLECTURE" in t or "PRELECTURE" in t:
            return "maternelle"
        return "primaire"
    return base_cat


def derive_niveau(titre: str) -> str | None:
    t = titre.upper()
    patterns = [
        (r"\bCP1\b", "CP1"), (r"\bCP2\b", "CP2"), (r"\bCE1\b", "CE1"), (r"\bCE2\b", "CE2"),
        (r"\bCM1\b", "CM1"), (r"\bCM2\b", "CM2"),
        (r"\b6[EÈ]ME\b|\b6IEME\b|\b6E\b", "6ème"), (r"\b5[EÈ]ME\b|\b5E\b", "5ème"),
        (r"\b4[EÈ]ME\b|\b4E\b", "4ème"), (r"\b3[EÈ]ME\b|\b3E\b", "3ème"),
        (r"\b2NDE\b|\b2ND\b", "2nde"), (r"\b1[EÈ]RE\b|\b1ERE\b", "1ère"),
        (r"\bTLE\b|TERMINALE", "Terminale"),
        (r"\bBEPC\b", "3ème"), (r"\bBAC\b", "Terminale"),
        (r"\bCEPE\b", "CM2"),
    ]
    for pat, lvl in patterns:
        if re.search(pat, t):
            return lvl
    return None


def parse_articles():
    text = ART_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    articles = []
    current_section = None
    i = 0
    # detect section headers: line of dashes, then a section title, then dashes
    section_titles = set(SECTION_TO_CAT.keys())

    cur = {}
    for idx, line in enumerate(lines):
        ls = line.strip()
        # section detection
        if ls in section_titles:
            current_section = ls
            continue
        if ls.startswith("ARTICLE "):
            cur = {"_section": current_section}
            continue
        if ls.startswith("Code Article"):
            cur["reference"] = ls.split(":", 1)[1].strip()
        elif ls.startswith("Référence"):
            cur["titre"] = ls.split(":", 1)[1].strip()
        elif ls.startswith("ISBN"):
            v = ls.split(":", 1)[1].strip()
            cur["isbn"] = None if v.upper().startswith("N/A") else v
        elif ls.startswith("Prix d'achat"):
            cur["prix_achat"] = parse_fcfa(ls.split(":", 1)[1])
        elif ls.startswith("Prix de vente"):
            cur["prix_vente"] = parse_fcfa(ls.split(":", 1)[1])
            # vente is last field of a block -> finalize
            if cur.get("reference") and cur.get("titre"):
                articles.append(cur)
            cur = {}
    return articles


def build_products(articles):
    docs = []
    incomplete = []
    seen_ref = set()
    for a in articles:
        ref = a["reference"].strip()
        if ref in seen_ref:
            # variante / doublon de code -> garder unique sur reference
            ref_orig = ref
            suffix = 2
            while ref in seen_ref:
                ref = f"{ref_orig}-{suffix}"
                suffix += 1
        seen_ref.add(ref)

        base_cat = SECTION_TO_CAT.get(a.get("_section") or "", "primaire")
        cat = refine_categorie(base_cat, ref, a["titre"])
        niveau = derive_niveau(a["titre"])

        prix_vente = a.get("prix_vente")
        prix_achat = a.get("prix_achat")
        a_completer = False
        if prix_vente is None or prix_vente <= 0:
            prix_vente = 1.0  # placeholder (schema exige >0)
            a_completer = True
        if prix_achat is None:
            prix_achat = 0.0
            a_completer = True

        # Classification auto (matière/cycle/niveau/catégorie) depuis le titre
        try:
            from classification import classify
            cl = classify(a["titre"])
            matiere = cl.get("matiere")
            cycle = cl.get("cycle")
            if cl.get("niveau_scolaire"):
                niveau = cl["niveau_scolaire"]
            if cl.get("categorie"):
                cat = cl["categorie"]
        except Exception:
            matiere, cycle = None, None

        # La section du catalogue fait autorité pour la Littérature
        if a.get("_section") == "LITTÉRATURE / ROMANS":
            matiere, cycle, cat, niveau = "Littérature", "Littérature", "litterature", None

        doc = {
            "product_id": f"prd_{uuid.uuid4().hex[:12]}",
            "reference": ref,
            "code_article": a["reference"].strip(),  # code original
            "titre": a["titre"].strip(),
            "categorie": cat,
            "matiere": matiere,
            "cycle": cycle,
            "niveau_scolaire": niveau,
            "isbn": a.get("isbn"),
            "prix_achat": prix_achat,
            "prix_vente": prix_vente,
            "stock_actuel": 0,
            "stock_minimum": 10,
            "actif": True,
            "a_completer": a_completer,
            "created_by": "admin_super_001",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        docs.append(doc)
        if a_completer:
            incomplete.append(ref)
    return docs, incomplete


# ===========================================================================
# 3) CLIENTS
# ===========================================================================
TYPE_MAPPING = {
    "LYCEES": "lycee", "LYCEE": "lycee",
    "COLLEGES": "college", "COLLEGE": "college",
    "EPP": "epp", "IEP": "iep",
    "GROUPE SCOLAIRE": "groupe_scolaire",
    "CATHOLIQUE": "catholique", "METHODISTE": "methodiste",
    "INSTITUT": "institut", "MEMO": "memo", "DREN": "dren",
    "INSPECTEUR": "inspecteur", "UP": "up",
    "LIBRAIRIES": "librairie", "LIBRAIRIE": "librairie",
    "PARTICULIERS": "particulier", "PARTICULIER": "particulier",
}

# type_client_fne template
FNE_TEMPLATE = {
    "lycee": "B2G", "college": "B2G", "epp": "B2G", "iep": "B2G",
    "groupe_scolaire": "B2B", "catholique": "B2B", "methodiste": "B2B",
    "institut": "B2B", "memo": "B2B", "dren": "B2G", "inspecteur": "B2G",
    "up": "B2B", "librairie": "B2B", "particulier": "B2C",
}


def normalize_phone(s: str) -> str | None:
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    return digits


def parse_clients():
    text = CLI_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    clients = []
    current_city = None
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip("\n")
        ls = line.strip()
        # city header: ==== then CITY then ====
        if ls.startswith("====") and set(ls) == {"="}:
            # next non-empty line is city
            if i + 1 < n:
                city_line = lines[i + 1].strip()
                if city_line and not city_line.startswith("Client") and not city_line.startswith("===="):
                    current_city = city_line
            i += 1
            continue
        # skip header rows / separators
        if (not ls or ls.startswith("Client") or ls.startswith("----")
                or ls.startswith("EDITIONS FABS-CI") or ls.startswith("====")
                or city_is_header(ls, current_city)):
            i += 1
            continue
        # data row: fixed-width columns. Use column positions.
        # Columns based on header alignment: Client(0-50), Representant(50-86), Phone(86-102), Email(102-128), Type(128-)
        parsed = parse_client_row(line)
        if parsed:
            parsed["ville"] = (current_city or "").title() if current_city else None
            clients.append(parsed)
        i += 1
    return clients


def city_is_header(ls: str, current_city) -> bool:
    return current_city is not None and ls == current_city


def parse_client_row(line: str):
    # Use whitespace-run splitting on 2+ spaces, more robust than fixed width
    parts = re.split(r"\s{2,}", line.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return None
    nom = parts[0]
    if len(nom) < 2:
        return None
    representant = parts[1] if len(parts) > 1 else None
    phone = None
    email = None
    type_raw = None
    # find phone (mostly digits), email (has @), type (known keyword) among remaining
    for p in parts[1:]:
        pu = p.upper()
        if "@" in p:
            email = p
        elif pu in TYPE_MAPPING:
            type_raw = pu
        elif re.fullmatch(r"[\d\s]+", p) and len(re.sub(r"\D", "", p)) >= 7:
            if phone is None:
                phone = p
    # representant: if parts[1] is actually the phone or type, fix
    if representant and (representant.upper() in TYPE_MAPPING or re.fullmatch(r"[\d\s]+", representant)):
        representant = None
    type_client = TYPE_MAPPING.get(type_raw, "autre") if type_raw else "autre"
    return {
        "nom": nom,
        "representant": representant,
        "telephone": normalize_phone(phone),
        "email": email,
        "type_client": type_client,
        "type_raw": type_raw,
    }


def build_clients(parsed, start_seq=1):
    docs = []
    seq = start_seq
    seen = set()
    skipped = 0
    for c in parsed:
        nom = c["nom"].strip()
        rep = (c.get("representant") or "").strip()
        ville = (c.get("ville") or "").strip()
        key = (nom.lower(), rep.lower(), ville.lower())
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        # representant obligatoire (min 2) dans le schema -> fallback
        if not rep or len(rep) < 2:
            rep = "N/C"
        tclient = c["type_client"]
        doc = {
            "client_id": f"cli_{uuid.uuid4().hex[:12]}",
            "reference": f"FABS-CLI-{seq:04d}",
            "nom": nom,
            "type_client": tclient,
            "representant": rep,
            "telephone": c.get("telephone"),
            "email": c.get("email"),
            "adresse": None,
            "ville": ville or None,
            "type_client_fne": FNE_TEMPLATE.get(tclient, "B2C"),
            "plafond_credit": 0,
            "notes": None,
            "solde": 0,
            "actif": True,
            "created_by": "admin_super_001",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        docs.append(doc)
        seq += 1
    return docs, skipped


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    # PARSE
    articles = parse_articles()
    products, incomplete = build_products(articles)
    parsed_clients = parse_clients()
    clients, skipped = build_clients(parsed_clients)
    users = build_users()

    # STATS
    print("=" * 60)
    print("RÉSUMÉ DU PARSE")
    print("=" * 60)
    print(f"Users           : {len(users)}")
    print(f"Articles parsés : {len(articles)}  ->  produits: {len(products)}")
    print(f"  - à compléter (prix N/A) : {len(incomplete)} -> {incomplete}")
    from collections import Counter
    print(f"  - par catégorie : {dict(Counter(p['categorie'] for p in products))}")
    print(f"Clients parsés  : {len(parsed_clients)}  ->  uniques: {len(clients)}  (doublons ignorés: {skipped})")
    print(f"  - par type      : {dict(Counter(c['type_client'] for c in clients))}")
    villes = sorted(set(c['ville'] for c in clients if c['ville']))
    print(f"  - villes        : {len(villes)}")
    print()
    print("Exemple produit :", {k: products[0][k] for k in ('reference','titre','categorie','niveau_scolaire','isbn','prix_vente','prix_achat')})
    print("Exemple client  :", {k: clients[0][k] for k in ('reference','nom','type_client','representant','telephone','ville')})

    if not apply:
        print("\n[DRY-RUN] Aucune écriture. Lance avec --apply pour purger + insérer.")
        return

    # APPLY
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    print("\n" + "=" * 60)
    print("PURGE + INSERTION")
    print("=" * 60)

    # Purge données démo/fictives
    for coll in ["commandes", "factures", "bons_livraison", "bons_retour",
                 "paiements", "mouvements_stock", "proformas"]:
        r = db[coll].delete_many({})
        print(f"purge {coll:20s}: {r.deleted_count} supprimés")

    # Users
    db.users.delete_many({})
    db.users.insert_many(users)
    print(f"users insérés         : {len(users)}")

    # Produits
    db.produits.delete_many({})
    db.counters.update_one({"_id": "produits"}, {"$set": {"seq": len(products)}}, upsert=True)
    db.produits.insert_many(products)
    print(f"produits insérés      : {len(products)}")

    # Clients
    db.clients.delete_many({})
    db.counters.update_one({"_id": "clients"}, {"$set": {"seq": len(clients)}}, upsert=True)
    db.clients.insert_many(clients)
    print(f"clients insérés       : {len(clients)}")

    print("\n✅ Terminé.")


if __name__ == "__main__":
    main()
