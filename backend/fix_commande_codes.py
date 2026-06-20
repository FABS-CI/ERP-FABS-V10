"""
Script: Corriger les lignes de commande pour ajouter le code_article réel (FABS-CIxxx)
- Cherche toutes les lignes de commande
- Pour chaque produit_id, récupère le code_article depuis la table produits
- Ajoute/met à jour le champ code_article dans la ligne
"""

import asyncio
import motor.motor_asyncio as motor

async def fix_codes():
    client = motor.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fabsci"]
    
    print("\n" + "="*70)
    print("CORRECTION: Ajout des codes_article réels aux lignes de commande")
    print("="*70)
    
    # Récupérer toutes les lignes de commande
    lignes = await db.commande_lignes.find({}).to_list(None)
    print(f"\nLignes de commande trouvées: {len(lignes)}")
    
    if not lignes:
        print("Aucune ligne à corriger")
        client.close()
        return
    
    # Map produit_id → code_article réel
    produits = await db.produits.find({}, {"code_article": 1, "product_id": 1, "produit_id": 1, "_id": 1}).to_list(None)
    produit_map = {}
    
    for prod in produits:
        code = prod.get('code_article') or prod.get('_id')
        pid = prod.get('product_id') or prod.get('produit_id') or prod.get('_id')
        produit_map[pid] = code
    
    print(f"\nProduits en DB: {len(produit_map)}")
    print(f"Exemples de mapping: {list(produit_map.items())[:3]}")
    
    # Corriger chaque ligne
    updated = 0
    errors = 0
    
    for ligne in lignes:
        produit_id = ligne.get('produit_id') or ligne.get('product_id')
        code_article = produit_map.get(produit_id)
        
        if not code_article:
            print(f"⚠️  Produit inconnu: {produit_id}")
            errors += 1
            continue
        
        # Update la ligne avec le code_article
        result = await db.commande_lignes.update_one(
            {"ligne_id": ligne["ligne_id"]},
            {
                "$set": {
                    "code_article": code_article,
                    "updated_at": asyncio.datetime.datetime.now().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            updated += 1
    
    print(f"\n✅ Lignes corrigées: {updated}")
    print(f"❌ Erreurs: {errors}")
    
    # Afficher quelques exemples
    print(f"\n📋 EXEMPLES AVANT/APRÈS:")
    lignes_updated = await db.commande_lignes.find({"code_article": {"$exists": True}}).limit(3).to_list(3)
    for l in lignes_updated:
        print(f"\n  Ligne: {l['ligne_id']}")
        print(f"    produit_id: {l.get('produit_id')}")
        print(f"    code_article: {l.get('code_article')}")
        print(f"    quantite: {l.get('quantite')}")
    
    client.close()
    print("\n" + "="*70)
    print("✅ Correction terminée!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(fix_codes())
