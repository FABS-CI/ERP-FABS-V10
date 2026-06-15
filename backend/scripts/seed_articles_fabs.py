"""
Seed des articles officiels EDITIONS FABS-CI (2026-2027)
Source : ARTICLES_FABS_CI_NUMEROTES.txt (artefact utilisateur, 59 articles)

- Idempotent (UPSERT sur référence FABS-CIxx)
- Catégorie mappée vers les littéraux acceptés (maternelle/primaire/premier_cycle/second_cycle/litterature/livre_commun)
- Prix unitaire en FCFA (int). "N/A" → 0
- Stock initial : 0 (à ajuster via les approvisionnements/bons de livraison)
- Niveau scolaire + matière conservés dans le titre + champ niveau_scolaire

Usage :
    python -m backend.scripts.seed_articles_fabs
"""
import asyncio
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient


# 59 articles officiels — source : ARTICLES_FABS_CI_NUMEROTES.txt
ARTICLES = [
    {"sku": "FABS-CI79", "nom": "MON CAHIER DE PRÉLECTURE CP1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CP1"},
    {"sku": "FABS-CI76", "nom": "MON CAHIER D'ÉCRITURE CP1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CP1"},
    {"sku": "FABS-CI83", "nom": "MON CAHIER D'ÉCRITURE CP2", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CP2"},
    {"sku": "FABS-CI90", "nom": "MON CAHIER D'ÉCRITURE CE1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CE1"},
    {"sku": "FABS-CI06", "nom": "MON CAHIER D'ÉCRITURE CE2", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CE2"},
    {"sku": "FABS-CI64", "nom": "MON CAHIER D'ÉCRITURE CM1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CM1"},
    {"sku": "FABS-CI82", "nom": "MON CAHIER D'ÉCRITURE CM2", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "2 000 FCFA", "niveau": "CM2"},
    {"sku": "FABS-CI08", "nom": "RÉUSSIR MES SUJETS DE COMPOSITION CM1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "3 000 FCFA", "niveau": "CM1"},
    {"sku": "FABS-CI54", "nom": "RÉUSSIR MES RÉVISIONS CM1", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "3 000 FCFA", "niveau": "CM1"},
    {"sku": "FABS-CI49", "nom": "RÉUSSIR MES SUJETS TYPES CEPE", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "3 000 FCFA", "niveau": "CEPE"},
    {"sku": "FABS-CI92", "nom": "RÉUSSIR MON CEPE MES RÉVISIONS", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "3 000 FCFA", "niveau": "CEPE"},
    {"sku": "FABS-CI56", "nom": "ANNALES MATH 6E", "categorie": "MATERNELLE / PRIMAIRE", "prix_unitaire": "N/A", "niveau": "6e"},
    {"sku": "FABS-CI24", "nom": "ACTIVITE PRATIQUE DE LA FLUTE A BEC SOPRANO 6ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "6ème"},
    {"sku": "FABS-CI61", "nom": "ACTIVITE PRATIQUE DE LA FLUTE A BEC SOPRANO 5ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 500 FCFA", "niveau": "5ème"},
    {"sku": "FABS-CI68", "nom": "MON CAHIER D'ACTIVITÉS D'ÉDUCATION MUSICALE 6IÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "6ième"},
    {"sku": "FABS-CI75", "nom": "MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 5EME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "5ème"},
    {"sku": "FABS-CI07", "nom": "MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 4ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "4ème"},
    {"sku": "FABS-CI20", "nom": "MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 3ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "3ème"},
    {"sku": "FABS-CI31", "nom": "MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 6ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "6ème"},
    {"sku": "FABS-CI46", "nom": "MON CAHIER DE COURS ET D'ACTIVITE DE MUSIQUE 6E (NOUVEAU)", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "6e"},
    {"sku": "FABS-CI48", "nom": "MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 5ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "5ème"},
    {"sku": "FABS-CI86", "nom": "MON CAHIER DE COURS ET D'ACTIVITÉS D'EDUCATION MUSICALE 4EME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "4ème"},
    {"sku": "FABS-CI93", "nom": "MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 3ÈME", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "3ème"},
    {"sku": "FABS-CI17", "nom": "MON CAHIER DE COURS ET D'ACTIVITES D'EDUCATION MUSICALE 2NDE", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "2nde"},
    {"sku": "FABS-CI39", "nom": "MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 1ERE", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "3 000 FCFA", "niveau": "1ère"},
    {"sku": "FABS-CI38", "nom": "MON CAHIER DE LEÇON D'EDUCATION MUSICALE", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "Tous niveaux"},
    {"sku": "FABS-CI71", "nom": "MON CAHIER DE COURS D'ARTS PLASTIQUES (6e à Terminale)", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "2 000 FCFA", "niveau": "6e à Tle"},
    {"sku": "FABS-CI53", "nom": "MANUEL DES ARTS PLASTIQUES 5E", "categorie": "PREMIER CYCLE - ÉDUCATION MUSICALE / ARTS", "prix_unitaire": "N/A", "niveau": "5e"},
    {"sku": "FABS-CI88", "nom": "MEMO MATH BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "2 500 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI36", "nom": "MEMO BEPC PHYSIQUE CHIMIE", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "2 500 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI40", "nom": "MEMO BEPC FRANÇAIS", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "2 500 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI19", "nom": "MEMO BEPC SVT", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "2 500 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI05", "nom": "MEMO HISTOIRE-GÉOGRAPHIE BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "2 000 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI18", "nom": "TEST PHYSIQUE-CHIMIE BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "3 000 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI32", "nom": "TEST SVT BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "3 000 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI25", "nom": "TEST FRANÇAIS BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "3 500 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI94", "nom": "TEST HISTOIRE-GEOGRAPHIE BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "3 000 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI47", "nom": "TEST-BEPC ANGLAIS", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "3 000 FCFA", "niveau": "BEPC"},
    {"sku": "FABS-CI30", "nom": "JE ME PRÉPARE À L'EPREUVE D'ANGLAIS BEPC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BEPC", "prix_unitaire": "N/A", "niveau": "BEPC"},
    {"sku": "FABS-CI195", "nom": "MEMO MATHÉMATIQUE BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI02", "nom": "MEMO PHYSIQUE CHIMIE BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI29", "nom": "MEMO PHILOSOPHIE BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "1 500 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI99", "nom": "MEMO HISTOIRE-GÉOGRAPHIE BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI26", "nom": "MEMO SVT BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI57", "nom": "MEMO FRANÇAIS BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI63", "nom": "TEST FRANÇAIS BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI70", "nom": "TEST PHILO BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI00", "nom": "TEST SVT BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI78", "nom": "TEST PHYSIQUE-CHIMIE BAC", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI84", "nom": "TEST BAC ANGLAIS", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "BAC"},
    {"sku": "FABS-CI85", "nom": "MON CAHIER DE RENFORCEMENT DE MES CAPACITÉS PHILOSOPHIE 1ÈRE", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "2 500 FCFA", "niveau": "1ère"},
    {"sku": "FABS-CI22", "nom": "MON CAHIER DE RENFORCEMENT DE MES CAPACITÉS PHILOSOPHIE TLE", "categorie": "SECOND CYCLE - MÉMOS ET TESTS BAC", "prix_unitaire": "3 000 FCFA", "niveau": "Tle"},
    {"sku": "FABS-CI33", "nom": "SACERDOCE (ROMAN)", "categorie": "LITTÉRATURE / ROMANS", "prix_unitaire": "3 000 FCFA", "niveau": "Tous niveaux"},
    {"sku": "FABS-CI60", "nom": "LE SUCCES D'UN ORPHELIN", "categorie": "LITTÉRATURE / ROMANS", "prix_unitaire": "3 000 FCFA", "niveau": "Tous niveaux"},
    {"sku": "FABS-CI09", "nom": "MOI LEON SECRETAIRE", "categorie": "LITTÉRATURE / ROMANS", "prix_unitaire": "3 000 FCFA", "niveau": "Tous niveaux"},
    {"sku": "FABS-CI93-B", "nom": "DE LA PRÉPARATION À LA RÉVÉLATION", "categorie": "LITTÉRATURE / ROMANS", "prix_unitaire": "3 000 FCFA", "niveau": "Tous niveaux"},
]


# Mapping catégorie source → littéral accepté côté backend
def map_categorie(src: str, niveau: str) -> str:
    s = src.upper()
    if "LITT" in s:
        return "litterature"
    if "BAC" in s:
        return "second_cycle"
    if "BEPC" in s or "PREMIER CYCLE" in s:
        return "premier_cycle"
    if "MATERNELLE" in s:
        # MATERNELLE / PRIMAIRE — niveau CP/CE/CM/CEPE → primaire, sinon premier_cycle (6e)
        if niveau and (niveau.upper().startswith(("CP", "CE", "CM", "CEPE"))):
            return "primaire"
        if niveau and "6" in niveau:
            return "premier_cycle"
        return "primaire"
    return "livre_commun"


def parse_prix(prix_str: str) -> int:
    """ '2 000 FCFA' → 2000 ;  'N/A' → 0 ; '3000' → 3000 """
    if not prix_str or prix_str.strip().upper() in ("N/A", "NA", ""):
        return 0
    digits = re.sub(r"[^\d]", "", prix_str)
    return int(digits) if digits else 0


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    now = datetime.now(timezone.utc).isoformat()
    created, updated = 0, 0

    for art in ARTICLES:
        prix = parse_prix(art["prix_unitaire"])
        cat = map_categorie(art["categorie"], art.get("niveau", ""))

        existing = await db.produits.find_one({"reference": art["sku"]})
        if existing:
            await db.produits.update_one(
                {"reference": art["sku"]},
                {"$set": {
                    "titre": art["nom"],
                    "categorie": cat,
                    "categorie_source": art["categorie"],
                    "niveau_scolaire": art.get("niveau"),
                    "prix_vente": float(prix) if prix > 0 else float(existing.get("prix_vente", 1)),
                    "updated_at": now,
                    "actif": True,
                }},
            )
            updated += 1
            print(f"  ↻ Maj : {art['sku']:<14} {art['nom'][:60]}")
        else:
            doc = {
                "product_id": f"prd_{uuid.uuid4().hex[:12]}",
                "reference": art["sku"],
                "titre": art["nom"],
                "auteur": None,
                "collection": "FABS-CI",
                "categorie": cat,
                "categorie_source": art["categorie"],
                "niveau_scolaire": art.get("niveau"),
                "isbn": None,
                "prix_achat": 0.0,
                "prix_vente": float(prix) if prix > 0 else 1.0,  # gt=0 requis par schema
                "stock_actuel": 0,
                "stock_minimum": 10,
                "actif": True,
                "created_at": now,
                "updated_at": now,
            }
            await db.produits.insert_one(doc)
            created += 1
            print(f"  + Créé : {art['sku']:<14} {art['nom'][:60]}  ({prix} FCFA)")

    print()
    print(f"✅ Terminé : {created} créés, {updated} mis à jour ({len(ARTICLES)} articles au total).")
    print("   Pour les articles dont prix = N/A, prix_vente = 1 FCFA (à éditer manuellement).")
    client.close()


if __name__ == "__main__":
    from pathlib import Path
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    asyncio.run(main())
