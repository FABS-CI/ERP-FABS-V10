"""
Script: Charger le catalogue officiel FABS-CI (56 articles)
- Supprime TOUS les produits test
- Parse le fichier catalogue numéroté
- Enrichit avec niveau/matière automatiquement
- Charge en MongoDB avec données réelles
"""

import asyncio
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import motor.motor_asyncio as motor
from pymongo import MongoClient

# =====================================================================
# CATALOGUE 56 ARTICLES FABS-CI — DONNÉES BRUTES
# =====================================================================
ARTICLES_BRUTS = """
ARTICLE 1|FABS-CI79|MON CAHIER DE PRÉLECTURE CP1|978-2-494706-27-9|133|2000|MATERNELLE / PRIMAIRE
ARTICLE 2|FABS-CI76|MON CAHIER D'ÉCRITURE CP1|979-10-91692-07-6|231|2000|MATERNELLE / PRIMAIRE
ARTICLE 3|FABS-CI83|MON CAHIER D'ÉCRITURE CP2|979-10-91692-08-3|264|2000|MATERNELLE / PRIMAIRE
ARTICLE 4|FABS-CI90|MON CAHIER D'ÉCRITURE CE1|979-10-91692-09-0|149|2000|MATERNELLE / PRIMAIRE
ARTICLE 5|FABS-CI06|MON CAHIER D'ÉCRITURE CE2|979-10-91692-10-6|149|2000|MATERNELLE / PRIMAIRE
ARTICLE 6|FABS-CI64|MON CAHIER D'ÉCRITURE CM1|978-2-494706-06-4|150|2000|MATERNELLE / PRIMAIRE
ARTICLE 7|FABS-CI82|MON CAHIER D'ÉCRITURE CM2|979-10-91692-18-2|150|2000|MATERNELLE / PRIMAIRE
ARTICLE 8|FABS-CI08|RÉUSSIR MES SUJETS DE COMPOSITION CM1|978-2-494706-40-8|856|3000|MATERNELLE / PRIMAIRE
ARTICLE 9|FABS-CI54|RÉUSSIR MES RÉVISIONS CM1|978-2-494706-35-4|866|3000|MATERNELLE / PRIMAIRE
ARTICLE 10|FABS-CI49|RÉUSSIR MES SUJETS TYPES CEPE|978-2-494706-14-9|878|3000|MATERNELLE / PRIMAIRE
ARTICLE 11|FABS-CI92|RÉUSSIR MON CEPE MES RÉVISIONS|978-2-494706-39-2|1115|3000|MATERNELLE / PRIMAIRE
ARTICLE 12|FABS-CI56|ANNALES MATH 6E|978-2-494706-15-6|N/A|N/A|MATERNELLE / PRIMAIRE
ARTICLE 13|FABS-CI24|ACTIVITE PRATIQUE DE LA FLUTE A BEC SOPRANO 6ÈME|978-2-494706-22-4|N/A|2000|PREMIER CYCLE
ARTICLE 14|FABS-CI61|ACTIVITE PRATIQUE DE LA FLUTE A BEC SOPRANO 5ÈME|978-2-494706-36-1|N/A|2500|PREMIER CYCLE
ARTICLE 15|FABS-CI68|MON CAHIER D'ACTIVITÉS D'ÉDUCATION MUSICALE 6IÈME|979-10-91692-16-8|N/A|2000|PREMIER CYCLE
ARTICLE 16|FABS-CI75|MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 5EME|979-10-91692-17-5|N/A|2000|PREMIER CYCLE
ARTICLE 17|FABS-CI07|MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 4ÈME|979-10-91692-00-7|N/A|2000|PREMIER CYCLE
ARTICLE 18|FABS-CI20|MON CAHIER D'ACTIVITE D'EDUCATION MUSICALE 3ÈME|979-10-91692-12-0|N/A|2000|PREMIER CYCLE
ARTICLE 19|FABS-CI31|MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 6ÈME|978-2-494706-23-1|420|3000|PREMIER CYCLE
ARTICLE 20|FABS-CI46|MON CAHIER DE COURS ET D'ACTIVITE DE MUSIQUE 6E (NOUVEAU)|978-2-494706-44-6|409|3000|PREMIER CYCLE
ARTICLE 21|FABS-CI48|MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 5ÈME|978-2-494706-24-8|413|3000|PREMIER CYCLE
ARTICLE 22|FABS-CI86|MON CAHIER DE COURS ET D'ACTIVITÉS D'EDUCATION MUSICALE 4EME|978-2-494706-28-6|443|3000|PREMIER CYCLE
ARTICLE 23|FABS-CI93|MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 3ÈME|978-2-494706-29-3|414|3000|PREMIER CYCLE
ARTICLE 24|FABS-CI17|MON CAHIER DE COURS ET D'ACTIVITES D'EDUCATION MUSICALE 2NDE|978-2-494706-21-7|405|3000|PREMIER CYCLE
ARTICLE 25|FABS-CI39|MON CAHIER DE COURS ET D'ACTIVITÉS D'ÉDUCATION MUSICALE 1ERE|978-2-494706-43-9|433|3000|PREMIER CYCLE
ARTICLE 26|FABS-CI38|MON CAHIER DE LEÇON D'EDUCATION MUSICALE|979-10-91692-03-8|346|2000|PREMIER CYCLE
ARTICLE 27|FABS-CI71|MON CAHIER DE COURS D'ARTS PLASTIQUES (6e à Terminale)|978-2-494706-07-1|399|2000|PREMIER CYCLE
ARTICLE 28|FABS-CI53|MANUEL DES ARTS PLASTIQUES 5E|978-2-494706-45-3|N/A|N/A|PREMIER CYCLE
ARTICLE 29|FABS-CI88|MEMO MATH BEPC|978-2-494706-08-8|348|2500|SECOND CYCLE
ARTICLE 30|FABS-CI36|MEMO BEPC PHYSIQUE CHIMIE|979-10-91692-23-6|348|2500|SECOND CYCLE
ARTICLE 31|FABS-CI40|MEMO BEPC FRANÇAIS|978-2-494706-04-0|348|2500|SECOND CYCLE
ARTICLE 32|FABS-CI19|MEMO BEPC SVT|978-24-94706-01-9|348|2500|SECOND CYCLE
ARTICLE 33|FABS-CI05|MEMO HISTOIRE-GÉOGRAPHIE BEPC|979-10-91692-20-5|348|2000|SECOND CYCLE
ARTICLE 34|FABS-CI18|TEST PHYSIQUE-CHIMIE BEPC|978-2-494706-19-4|1993|3000|SECOND CYCLE
ARTICLE 35|FABS-CI32|TEST SVT BEPC|978-2-494706-13-2|1993|3000|SECOND CYCLE
ARTICLE 36|FABS-CI25|TEST FRANÇAIS BEPC|978-2-494706-12-5|1993|3500|SECOND CYCLE
ARTICLE 37|FABS-CI94|TEST HISTOIRE-GEOGRAPHIE BEPC|978-2-494706-11-8|1993|3000|SECOND CYCLE
ARTICLE 38|FABS-CI47|TEST-BEPC ANGLAIS|978-2-494706-34-7|1993|3000|SECOND CYCLE
ARTICLE 39|FABS-CI30|JE ME PREPARE A L'EPREUVE D'ANGLAIS BEPC|978-2-494706-33-0|828|N/A|SECOND CYCLE
ARTICLE 40|FABS-CI195|MEMO MATHEMATIQUE BAC|N/A|348|3000|SECOND CYCLE
ARTICLE 41|FABS-CI02|MEMO PHYSIQUE CHIMIE BAC|978-2-494706-00-2|348|3000|SECOND CYCLE
ARTICLE 42|FABS-CI29|MEMO PHILOSOPHIE BAC|979-10-91692-22-9|348|1500|SECOND CYCLE
ARTICLE 43|FABS-CI99|MEMO HISTOIRE-GÉOGRAPHIE BAC|979-10-91692-19-9|348|3000|SECOND CYCLE
ARTICLE 44|FABS-CI26|MEMO SVT BAC|978-2-494706-02-6|348|3000|SECOND CYCLE
ARTICLE 45|FABS-CI57|MEMO FRANÇAIS BAC|978-2-494706-05-7|348|3000|SECOND CYCLE
ARTICLE 46|FABS-CI63|TEST FRANÇAIS BAC|978-2-494706-16-3|1993|3000|SECOND CYCLE
ARTICLE 47|FABS-CI70|TEST PHILO BAC|978-2-494706-17-0|1993|3000|SECOND CYCLE
ARTICLE 48|FABS-CI00|TEST SVT BAC|978-2-494706-20-0|1993|3000|SECOND CYCLE
ARTICLE 49|FABS-CI78|TEST PHYSIQUE-CHIMIE BAC|978-2-494706-37-8|1993|3000|SECOND CYCLE
ARTICLE 50|FABS-CI84|TEST BAC ANGLAIS|978-2-494706-48-4|1993|3000|SECOND CYCLE
ARTICLE 51|FABS-CI85|MON CAHIER DE RENFORCEMENT DE MES CAPACITÉS PHILOSOPHIE  1ÈRE|978-2-494706-38-5|433|2500|SECOND CYCLE
ARTICLE 52|FABS-CI22|MON CAHIER DE RENFORCEMENT DE MES CAPACITÉS PHILOSOPHIE TLE|978-2-494706-42-2|406|3000|SECOND CYCLE
ARTICLE 53|FABS-CI33|SACERDOCE (ROMAN)|978-2-494706-03-3|N/A|3000|LITTÉRATURE
ARTICLE 54|FABS-CI60|LE SUCCES D'UN ORPHELIN|978-2-494706-46-0|466|3000|LITTÉRATURE
ARTICLE 55|FABS-CI09|MOI LEON SECRETAIRE|978-2-494706-30-9|N/A|3000|LITTÉRATURE
ARTICLE 56|FABS-CI93-B|DE LA PRÉPARATION À LA RÉVÉLATION|978-2-494706-29-3|N/A|3000|LITTÉRATURE
""".strip()

# =====================================================================
# EXTRACTION NIVEAU/MATIÈRE
# =====================================================================

def extract_niveau_matiere(designation: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extrait automatiquement le niveau et la matière depuis la désignation.
    Retourne (niveau, matière)
    """
    d = designation.upper()
    
    # Niveaux maternelle/primaire
    if "CP1" in d or "CP 1" in d:
        return ("CP1", "Français")
    if "CP2" in d or "CP 2" in d:
        return ("CP2", "Français")
    if "CE1" in d or "CE 1" in d:
        return ("CE1", "Français")
    if "CE2" in d or "CE 2" in d:
        return ("CE2", "Français")
    if "CM1" in d or "CM 1" in d:
        return ("CM1", None)  # peut être français ou autre
    if "CM2" in d or "CM 2" in d:
        return ("CM2", None)
    if "CEPE" in d:
        return ("CEPE", None)  # Certificat Élémentaire Primaire
    
    # Niveaux collège (PREMIER CYCLE)
    if "6ÈME" in d or "6E" in d or "6EME" in d or "6ÉME" in d:
        niveau = "6ème"
    elif "5ÈME" in d or "5EME" in d or "5ÉME" in d:
        niveau = "5ème"
    elif "4ÈME" in d or "4EME" in d or "4ÉME" in d:
        niveau = "4ème"
    elif "3ÈME" in d or "3EME" in d or "3ÉME" in d:
        niveau = "3ème"
    # Lycée (SECOND CYCLE)
    elif "2NDE" in d:
        niveau = "2nde"
    elif "1ERE" in d or "1ÈRE" in d:
        niveau = "1ère"
    elif "TERMINALE" in d or "TLE" in d:
        niveau = "Terminale"
    # BEPC / BAC
    elif "BEPC" in d:
        niveau = "3ème (BEPC)"
    elif "BAC" in d:
        niveau = "Terminale (BAC)"
    else:
        niveau = None
    
    # Extraction matière
    matiere = None
    if "MATH" in d or "MATHÉMATIQUE" in d:
        matiere = "Mathématiques"
    elif "FRANÇAIS" in d or "FRANCAIS" in d:
        matiere = "Français"
    elif "SVT" in d or "BIOLOGIE" in d or "SCIENCE" in d:
        matiere = "SVT"
    elif "PHYSIQUE" in d or "CHIMIE" in d:
        matiere = "Physique-Chimie"
    elif "HISTOIRE" in d or "GÉOGRAPHIE" in d:
        matiere = "Histoire-Géographie"
    elif "ANGLAIS" in d or "ENGLISH" in d:
        matiere = "Anglais"
    elif "PHILOSOPHIE" in d or "PHILO" in d:
        matiere = "Philosophie"
    elif "MUSIQUE" in d or "ÉDUCATION MUSICALE" in d:
        matiere = "Éducation Musicale"
    elif "ARTS PLASTIQUES" in d:
        matiere = "Arts Plastiques"
    elif "FLUTE" in d or "FLÛTE" in d:
        matiere = "Musique (Flûte)"
    elif "PRÉLÉC" in d or "PRÉLECTURE" in d or "ÉCRITURE" in d:
        matiere = "Français"
    elif "ROMAN" in d:
        matiere = "Littérature"
    
    return (niveau, matiere)


def extract_categorie(section: str) -> str:
    """Extrait la catégorie depuis le header de section du catalogue"""
    s = section.upper()
    if "MATERNELLE" in s or "PRIMAIRE" in s:
        return "primaire"
    elif "PREMIER CYCLE" in s:
        return "premier_cycle"
    elif "SECOND CYCLE" in s:
        return "second_cycle"
    elif "LITTÉRATURE" in s or "LITERATURE" in s:
        return "litterature"
    else:
        return "livre_commun"


# =====================================================================
# PARSING & CHARGEMENT
# =====================================================================

async def load_catalogue():
    """Parse le catalogue et charge en MongoDB"""
    
    # Connexion async
    client = motor.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fabsci"]
    
    print("[1] Suppression de tous les produits existants...")
    result = await db.produits.delete_many({})
    print(f"    ✓ {result.deleted_count} produits supprimés")
    
    # Reset counter
    await db.counters.update_one(
        {"_id": "produits"},
        {"$set": {"seq": 0}},
        upsert=True
    )
    
    print("\n[2] Parsing catalogue...")
    articles = []
    for line in ARTICLES_BRUTS.split('\n'):
        if not line.strip():
            continue
        
        parts = line.split('|')
        if len(parts) < 7:
            continue
        
        num_article = parts[0].replace("ARTICLE ", "").strip()
        code_article = parts[1].strip()
        designation = parts[2].strip()
        isbn_raw = parts[3].strip()
        prix_achat_raw = parts[4].strip()
        prix_vente_raw = parts[5].strip()
        categorie_raw = parts[6].strip()
        
        # Conversion prix
        prix_achat = None if prix_achat_raw == "N/A" else float(prix_achat_raw)
        prix_vente = None if prix_vente_raw == "N/A" else float(prix_vente_raw)
        isbn = isbn_raw if isbn_raw and isbn_raw != "N/A" else None
        
        # Extraction niveau/matière
        niveau, matiere = extract_niveau_matiere(designation)
        categorie = extract_categorie(categorie_raw)
        
        article = {
            "_id": code_article,  # Code article = PK unique
            "code_article": code_article,
            "titre": designation,
            "designation": designation,  # alias pour compat
            "isbn": isbn,
            "niveau_scolaire": niveau,
            "matiere": matiere,
            "categorie": categorie,
            "prix_achat": prix_achat if prix_achat is not None else 0,
            "prix_vente": prix_vente if prix_vente is not None else 0,
            "stock_actuel": 1000,  # Stock initial
            "stock_minimum": 50,
            "actif": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        articles.append(article)
    
    print(f"    ✓ {len(articles)} articles parsés")
    
    print("\n[3] Insertion en MongoDB...")
    if articles:
        result = await db.produits.insert_many(articles)
        print(f"    ✓ {len(result.inserted_ids)} articles insérés")
    
    print("\n[4] Vérification...")
    count = await db.produits.count_documents({})
    print(f"    ✓ Total produits en DB: {count}")
    
    # Afficher un exemple
    sample = await db.produits.find_one()
    if sample:
        print(f"\n    Exemple:\n{sample}")
    
    client.close()
    print("\n✅ Catalogue chargé avec succès!")

if __name__ == "__main__":
    asyncio.run(load_catalogue())
