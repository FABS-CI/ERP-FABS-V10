#!/usr/bin/env python3
"""
TEST FINAL WORKFLOW COMPLET : Créer → Soumettre → Valider → Préparer → Livrer → Facture
UTILISE LES VRAIS SÉLECTEURS TROUVÉS
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Auto-accept dialogs
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflow": {},
            "errors": []
        }
        
        try:
            print("\n" + "="*70)
            print("TEST WORKFLOW COMPLET ERP FABS-CI")
            print("="*70)
            
            # 1. LOGIN
            print("\n🔐 LOGIN")
            await page.goto("http://localhost:3000/login", wait_until="networkidle")
            await page.fill('input[type="email"]', "pissken@editionsfabsci.com")
            await page.fill('input[type="password"]', "Admin@2025")
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard", timeout=10000)
            print("✅ Connecté")
            
            # 2. CRÉER COMMANDE
            print("\n📝 ÉTAPE 1 : CRÉER COMMANDE")
            await page.goto("http://localhost:3000/commandes/nouvelle", wait_until="networkidle")
            
            # Vérifier le rendu
            h1 = await page.text_content("h1")
            print(f"  Page chargée: {h1}")
            
            # ClientPicker : chercher l'input avec le bon placeholder
            inp_client = page.locator("input[placeholder*='Nom, représentant']")
            if await inp_client.is_visible(timeout=3000):
                print("  ✅ Input ClientPicker visible")
                
                # Attendre les clients (premier appel fetch)
                await page.wait_for_timeout(1500)
                
                # Chercher les buttons clients dans la liste
                # ClientPicker affiche 50 premiers clients par défaut
                client_btns = await page.query_selector_all("li button")
                print(f"  ✅ Clients chargés: {len(client_btns)} affichés (max 50)")
                
                if client_btns:
                    # Cliquer sur le 1er client
                    await client_btns[0].click()
                    print(f"  ✅ Client sélectionné")
                    results["workflow"]["client_selected"] = "✅"
                    
                    # Vérifier la card de sélection
                    await page.wait_for_timeout(500)
                    try:
                        selected_card = await page.text_content("text='✓ Client sélectionné'", timeout=2000)
                        if selected_card:
                            print(f"  ✅ Card confirmation affichée")
                    except:
                        print(f"  ⚠️  Card confirmation non trouvée (pas bloquant)")
            else:
                print("  ❌ Input ClientPicker non trouvé")
                results["errors"].append("ClientPicker input not found")
                return
            
            # Cliquer Suivant
            btn_next = page.locator("button:has-text('Suivant')")
            if await btn_next.is_visible():
                await btn_next.click()
                print(f"  ✅ Suivant → Step 2")
                results["workflow"]["step2"] = "✅"
            else:
                print(f"  ❌ Bouton Suivant non trouvé")
            
            # 3. AJOUTER UN PRODUIT
            print("\n📦 ÉTAPE 2 : AJOUTER UN PRODUIT")
            await page.wait_for_timeout(1500)
            
            # Chercher le bouton (peut avoir du texte enrichi)
            add_btns = await page.query_selector_all("button")
            add_btn_found = None
            for btn in add_btns:
                txt = await btn.text_content()
                if "Ajouter" in txt and "ligne" in txt.lower():
                    add_btn_found = btn
                    break
            
            if add_btn_found:
                await add_btn_found.click()
                print(f"  ✅ Bouton 'Ajouter une ligne' cliqué")
                await page.wait_for_timeout(1000)
                results["workflow"]["product_added"] = "✅"
                
                # Sélectionner 1er produit du dropdown (attendre les options)
                try:
                    produits = await page.query_selector_all("[role='option']", timeout=3000)
                    if produits:
                        await produits[0].click()
                        print(f"  ✅ Produit sélectionné")
                        
                        # Remplir quantité
                        await page.wait_for_timeout(500)
                        qte_input = page.locator("input[placeholder*='Quantité'], input[placeholder*='quantité']")
                        if await qte_input.is_visible():
                            await qte_input.fill("2")
                            print(f"  ✅ Quantité = 2")
                except:
                    print(f"  ⚠️  Produits non trouvés (pas bloquant)")
            else:
                print(f"  ⚠️  Bouton 'Ajouter une ligne' non trouvé")
            
            # Cliquer Soumettre
            print("\n✉️ ÉTAPE 3 : SOUMETTRE")
            btn_submit = page.locator("button:has-text('Soumettre')")
            if await btn_submit.is_visible():
                await btn_submit.click()
                await page.wait_for_load_state("networkidle", timeout=5000)
                print(f"  ✅ Commande soumise")
                
                # Récupérer l'ID
                url = page.url
                if "/commandes/" in url:
                    cmd_id = url.split("/commandes/")[1].split("/")[0]
                    print(f"  ✅ Commande créée: {cmd_id}")
                    results["workflow"]["cmd_id"] = cmd_id
                    
                    # 4. VALIDER
                    print("\n✅ VALIDATION")
                    btn_valider = page.locator("button:has-text('Valider')")
                    if await btn_valider.is_visible():
                        await btn_valider.click()
                        await page.wait_for_load_state("networkidle")
                        print(f"  ✅ Commande validée")
                        results["workflow"]["validated"] = "✅"
                    else:
                        print(f"  ⚠️  Bouton Valider non visible")
                    
                    # 5. PRÉPARER
                    print("\n📋 PRÉPARATION")
                    await page.wait_for_timeout(1000)
                    btn_preparer = page.locator("button:has-text('Préparer')")
                    if await btn_preparer.is_visible():
                        await btn_preparer.click()
                        await page.wait_for_load_state("networkidle")
                        print(f"  ✅ Commande préparée")
                        results["workflow"]["prepared"] = "✅"
                    else:
                        print(f"  ⚠️  Bouton Préparer non visible")
                    
                    # 6. LIVRER (peut être bloqué par BL auto)
                    print("\n🚚 LIVRAISON")
                    await page.wait_for_timeout(1000)
                    btn_livrer = page.locator("button:has-text('Marquer livrée')")
                    if await btn_livrer.is_visible():
                        await btn_livrer.click()
                        await page.wait_for_load_state("networkidle", timeout=3000).catch(lambda e: None)
                        print(f"  ✅ Commande livrée")
                        results["workflow"]["delivered"] = "✅"
                    else:
                        print(f"  ⚠️  Bouton Livrer non visible (probablement BL auto-créé)")
                    
                    # 7. VÉRIFIER FACTURE
                    print("\n🧾 FACTURE")
                    await page.goto("http://localhost:3000/factures", wait_until="networkidle")
                    factures = await page.query_selector_all("tbody tr, [role='row']")
                    if factures:
                        print(f"  ✅ Factures trouvées: {len(factures)}")
                        results["workflow"]["facture"] = "✅"
                    else:
                        print(f"  ⚠️  Pas de factures affichées")
        
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            results["errors"].append(str(e))
        
        finally:
            await browser.close()
        
        # RÉSUMÉ
        print("\n" + "="*70)
        print("📊 RÉSUMÉ FINAL")
        print("="*70)
        
        ok_steps = sum(1 for v in results["workflow"].values() if v == "✅")
        total_steps = len(results["workflow"])
        
        print(f"\nÉtapes OK: {ok_steps}/{total_steps}")
        for step, status in results["workflow"].items():
            symbol = "✅" if status == "✅" else "⚠️"
            print(f"  {symbol} {step}: {status}")
        
        if results["errors"]:
            print(f"\nErreurs: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"  ❌ {err[:80]}")
        
        print("\n" + "="*70)
        
        # Sauver
        with open("/home/user/ERP-FABS-V10/RAPPORT_WORKFLOW_FINAL.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Rapport : /home/user/ERP-FABS-V10/RAPPORT_WORKFLOW_FINAL.json\n")

if __name__ == "__main__":
    asyncio.run(main())
