#!/usr/bin/env python3
"""
Enrichir les produits avec Niveau Scolaire, Matière, Cycle
en se basant sur l'analyse du titre et du code article
"""
import os
import re
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "fabsci_erp")

# Mapping titre → (niveau, matière, cycle, catégorie)
MAPPINGS = [
    # PRÉLECTURE
    (r"PRÉLECTURE|PRELECTURE", "CP1-CP2", "Français", "Maternelle/Primaire", "maternelle"),
    
    # CP1 - CP2
    (r"\bCP1\b", "CP1", "Français", "Primaire", "primaire"),
    (r"\bCP2\b", "CP2", "Français", "Primaire", "primaire"),
    
    # CE1 - CE2
    (r"\bCE1\b", "CE1", "Français", "Primaire", "primaire"),
    (r"\bCE2\b", "CE2", "Français", "Primaire", "primaire"),
    
    # CM1 - CM2
    (r"\bCM1\b", "CM1", "Français", "Primaire", "primaire"),
    (r"\bCM2\b", "CM2", "Français", "Primaire", "primaire"),
    
    # BEPC (3ème) - Sciences
    (r"BEPC.*SVT|SVT.*BEPC", "3ème", "Sciences de la Vie et de la Terre", "Premier Cycle", "premier_cycle"),
    (r"BEPC.*PHYSIQUE|PHYSIQUE.*BEPC", "3ème", "Physique-Chimie", "Premier Cycle", "premier_cycle"),
    (r"BEPC.*FRANCAIS|FRANCAIS.*BEPC", "3ème", "Français", "Premier Cycle", "premier_cycle"),
    (r"BEPC.*MATH|MATH.*BEPC", "3ème", "Mathématiques", "Premier Cycle", "premier_cycle"),
    (r"BEPC.*ANGLAIS|ANGLAIS.*BEPC", "3ème", "Anglais", "Premier Cycle", "premier_cycle"),
    (r"BEPC.*HISTOIRE|HISTOIRE.*BEPC", "3ème", "Histoire-Géographie", "Premier Cycle", "premier_cycle"),
    (r"BEPC", "3ème", "Multidisciplinaire", "Premier Cycle", "premier_cycle"),
    
    # BAC (Terminale) - Sciences
    (r"BAC.*SVT|SVT.*BAC", "Terminale", "Sciences de la Vie et de la Terre", "Second Cycle", "second_cycle"),
    (r"BAC.*PHYSIQUE|PHYSIQUE.*BAC", "Terminale", "Physique-Chimie", "Second Cycle", "second_cycle"),
    (r"BAC.*FRANCAIS|FRANCAIS.*BAC", "Terminale", "Français", "Second Cycle", "second_cycle"),
    (r"BAC.*MATH|MATH.*BAC", "Terminale", "Mathématiques", "Second Cycle", "second_cycle"),
    (r"BAC.*ANGLAIS|ANGLAIS.*BAC", "Terminale", "Anglais", "Second Cycle", "second_cycle"),
    (r"BAC", "Terminale", "Multidisciplinaire", "Second Cycle", "second_cycle"),
    
    # 6ème - 5ème - 4ème
    (r"\b6[EÈ]ME\b|\b6E\b", "6ème", "Multidisciplinaire", "Premier Cycle", "premier_cycle"),
    (r"\b5[EÈ]ME\b|\b5E\b", "5ème", "Multidisciplinaire", "Premier Cycle", "premier_cycle"),
    (r"\b4[EÈ]ME\b|\b4E\b", "4ème", "Multidisciplinaire", "Premier Cycle", "premier_cycle"),
    (r"\b3[EÈ]ME\b|\b3E\b", "3ème", "Multidisciplinaire", "Premier Cycle", "premier_cycle"),
    
    # 2nde - 1ère - Terminale
    (r"\b2NDE\b|\b2ND\b", "2nde", "Multidisciplinaire", "Second Cycle", "second_cycle"),
    (r"\b1[EÈ]RE\b|\b1ERE\b", "1ère", "Multidisciplinaire", "Second Cycle", "second_cycle"),
    (r"\bTERMINALE\b|\bTLE\b", "Terminale", "Multidisciplinaire", "Second Cycle", "second_cycle"),
    
    # LITTÉRATURE
    (r"LITTÉRATURE|ROMAN|CONTE|POÉSIE", "Tous", "Littérature", "Littérature", "litterature"),
    
    # ÉDUCATION MUSICALE / ARTS
    (r"MUSIQUE|ÉDUCATION MUSICALE", "Tous", "Éducation Musicale", "Arts", "arts"),
    (r"ARTS|DESSIN|PEINTURE", "Tous", "Arts Plastiques", "Arts", "arts"),
]

def extract_niveau_matiere(titre: str, code: str) -> dict:
    """Extraire niveau, matière, cycle du titre"""
    titre_upper = titre.upper()
    code_upper = code.upper()
    
    for pattern, niveau, matiere, cycle, categorie in MAPPINGS:
        if re.search(pattern, titre_upper):
            return {
                "niveau_scolaire": niveau,
                "matiere": matiere,
                "cycle": cycle,
                "categorie": categorie,
            }
    
    # Défaut: Primaire si contient "cahier"
    if "CAHIER" in titre_upper:
        return {
            "niveau_scolaire": "Primaire (à préciser)",
            "matiere": "Français",
            "cycle": "Primaire",
            "categorie": "primaire",
        }
    
    # Défaut: Non classé
    return {
        "niveau_scolaire": None,
        "matiere": None,
        "cycle": None,
        "categorie": None,
    }

def main(apply=False, dry_run=True):
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    col = db.produits
    
    total = col.count_documents({})
    updated = 0
    stats_by_niveau = {}
    stats_by_matiere = {}
    
    print(f"📊 Total produits: {total}")
    print("=" * 80)
    
    for prod in col.find({}, {"_id": 0}):
        infos = extract_niveau_matiere(prod.get("titre", ""), prod.get("code_article", ""))
        
        # Compter stats
        niveau = infos.get("niveau_scolaire")
        matiere = infos.get("matiere")
        if niveau:
            stats_by_niveau[niveau] = stats_by_niveau.get(niveau, 0) + 1
        if matiere:
            stats_by_matiere[matiere] = stats_by_matiere.get(matiere, 0) + 1
        
        if not dry_run and (
            prod.get("niveau_scolaire") != infos.get("niveau_scolaire")
            or prod.get("matiere") != infos.get("matiere")
            or prod.get("cycle") != infos.get("cycle")
        ):
            col.update_one(
                {"produit_id": prod["produit_id"]},
                {
                    "$set": {
                        "niveau_scolaire": infos.get("niveau_scolaire"),
                        "matiere": infos.get("matiere"),
                        "cycle": infos.get("cycle"),
                        "categorie": infos.get("categorie"),
                    }
                },
            )
            updated += 1
            if updated <= 5:  # Afficher les 5 premiers
                print(f"✏️  {prod['code_article']:12} | {prod['titre'][:40]:40} | {niveau:25} | {matiere}")
    
    print("=" * 80)
    if dry_run:
        print(f"\n[DRY-RUN] {updated} produits à mettre à jour")
        print("\nRelancer avec --apply pour confirmer les modifications")
    else:
        print(f"\n✅ {updated} produits mis à jour")
    
    print("\n📊 Répartition par NIVEAU SCOLAIRE:")
    for niveau, count in sorted(stats_by_niveau.items(), key=lambda x: -x[1]):
        print(f"   {niveau:30} : {count:3} produits")
    
    print("\n📊 Répartition par MATIÈRE:")
    for matiere, count in sorted(stats_by_matiere.items(), key=lambda x: -x[1]):
        print(f"   {matiere:30} : {count:3} produits")
    
    client.close()

if __name__ == "__main__":
    import sys
    apply = "--apply" in sys.argv
    main(apply=apply, dry_run=not apply)
