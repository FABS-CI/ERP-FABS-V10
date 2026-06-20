#!/usr/bin/env python3
"""
TEST FINAL WORKFLOW : Audit complet ERP FABS-CI
Test tous les boutons des pages critiques + workflow E2E
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "workflow": {},
            "pages_buttons": {}
        }
        
        # Auto-accept dialogs
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))
        
        try:
            # LOGIN
            print("\n🔐 LOGIN")
            await page.goto("http://localhost:3000/login")
            await page.fill('input[type="email"]', "pissken@editionsfabsci.com")
            await page.fill('input[type="password"]', "Admin@2025")
            await page.click('button[type="submit"]')
            await page.wait_for_url("**/dashboard", timeout=10000)
            await page.wait_for_load_state("networkidle")
            print("✅ Connecté\n")
            
            # === TEST 1 : PAGE COMMANDES (LISTE) ===
            print("="*60)
            print("TEST 1 : PAGE COMMANDES (LISTE)")
            print("="*60)
            
            await page.goto("http://localhost:3000/commandes")
            await page.wait_for_load_state("networkidle")
            
            buttons_to_find = [
                ("Nouvelle commande", "Créer"),
                ("Filtrer", "Filtrer"),
                ("button[placeholder*='Rechercher']", "Rechercher"),
            ]
            
            results["pages_buttons"]["Commandes (liste)"] = {}
            
            for btn_text, label in buttons_to_find[:2]:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}')")
                    is_visible = await btn.is_visible(timeout=2000)
                    results["pages_buttons"]["Commandes (liste)"][label] = "✅" if is_visible else "❌"
                    print(f"  {label}: {'✅' if is_visible else '❌'}")
                except:
                    results["pages_buttons"]["Commandes (liste)"][label] = "❌"
                    print(f"  {label}: ❌")
            
            # Chercher une commande à ouvrir
            print("\n  Cherchant une commande...")
            rows = await page.query_selector_all("tbody tr")
            if rows:
                print(f"  Trouvé {len(rows)} ligne(s)")
                # Cliquer sur la 1ère
                await rows[0].click()
                await page.wait_for_load_state("networkidle", timeout=5000)
                cmd_url = page.url
                if "/commandes/" in cmd_url:
                    print(f"  ✅ Ouvert : {cmd_url.split('/')[-1][:12]}...")
                    results["workflow"]["commande_opened"] = True
            else:
                print("  ⚠️  Aucune commande trouvée")
                results["workflow"]["commande_opened"] = False
            
            # === TEST 2 : PAGE DÉTAIL COMMANDE ===
            if results["workflow"].get("commande_opened"):
                print("\n" + "="*60)
                print("TEST 2 : PAGE DÉTAIL COMMANDE")
                print("="*60)
                
                results["pages_buttons"]["Commande (détail)"] = {}
                
                detail_buttons = [
                    "Aperçu PDF", "Télécharger", "Imprimer", "Email", "WhatsApp",
                    "Valider", "Marquer", "Générer Facture", "Annuler", "Supprimer"
                ]
                
                for btn_text in detail_buttons:
                    try:
                        btn = page.locator(f"button:has-text('{btn_text}')")
                        is_visible = await btn.is_visible(timeout=1000)
                        results["pages_buttons"]["Commande (détail)"][btn_text] = "✅" if is_visible else "⚠️"
                        if is_visible:
                            print(f"  ✅ {btn_text}")
                        else:
                            print(f"  ⚠️  {btn_text} (caché/désactivé)")
                    except:
                        results["pages_buttons"]["Commande (détail)"][btn_text] = "❌"
                        print(f"  ❌ {btn_text}")
            
            # === TEST 3 : PAGE FACTURES ===
            print("\n" + "="*60)
            print("TEST 3 : PAGE FACTURES")
            print("="*60)
            
            await page.goto("http://localhost:3000/factures")
            await page.wait_for_load_state("networkidle")
            
            results["pages_buttons"]["Factures (liste)"] = {}
            facture_buttons = ["Nouvelle facture", "Filtrer"]
            
            for btn_text in facture_buttons:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}')")
                    is_visible = await btn.is_visible(timeout=2000)
                    results["pages_buttons"]["Factures (liste)"][btn_text] = "✅" if is_visible else "❌"
                    print(f"  {btn_text}: {'✅' if is_visible else '❌'}")
                except:
                    results["pages_buttons"]["Factures (liste)"][btn_text] = "❌"
                    print(f"  {btn_text}: ❌")
            
            # === TEST 4 : PAGE PAIEMENTS ===
            print("\n" + "="*60)
            print("TEST 4 : PAGE PAIEMENTS")
            print("="*60)
            
            await page.goto("http://localhost:3000/paiements")
            await page.wait_for_load_state("networkidle")
            
            results["pages_buttons"]["Paiements"] = {}
            paiement_buttons = ["Nouveau paiement", "Lettrer"]
            
            for btn_text in paiement_buttons:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}')")
                    is_visible = await btn.is_visible(timeout=2000)
                    results["pages_buttons"]["Paiements"][btn_text] = "✅" if is_visible else "⚠️"
                    print(f"  {btn_text}: {'✅' if is_visible else '⚠️'}")
                except:
                    results["pages_buttons"]["Paiements"][btn_text] = "❌"
                    print(f"  {btn_text}: ❌")
            
            # === TEST 5 : PAGE STOCK ===
            print("\n" + "="*60)
            print("TEST 5 : PAGE STOCK")
            print("="*60)
            
            await page.goto("http://localhost:3000/stock")
            await page.wait_for_load_state("networkidle")
            
            results["pages_buttons"]["Stock"] = {}
            stock_buttons = ["Ajustement", "Transfert"]
            
            for btn_text in stock_buttons:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}')")
                    is_visible = await btn.is_visible(timeout=2000)
                    results["pages_buttons"]["Stock"][btn_text] = "✅" if is_visible else "⚠️"
                    print(f"  {btn_text}: {'✅' if is_visible else '⚠️'}")
                except:
                    results["pages_buttons"]["Stock"][btn_text] = "❌"
                    print(f"  {btn_text}: ❌")
            
        except Exception as e:
            print(f"\n❌ ERREUR : {e}")
            results["error"] = str(e)
        finally:
            await browser.close()
        
        # RÉSUMÉ
        print("\n" + "="*60)
        print("📊 RÉSUMÉ")
        print("="*60)
        
        total_btns = 0
        ok_btns = 0
        
        for page_name, buttons in results["pages_buttons"].items():
            ok = sum(1 for v in buttons.values() if v == "✅")
            total = len(buttons)
            total_btns += total
            ok_btns += ok
            pct = int(100 * ok / total) if total > 0 else 0
            print(f"{page_name:30} : {ok:2}/{total:2} ({pct:3}%)")
        
        print(f"\nTOTAL : {ok_btns}/{total_btns} boutons ({int(100*ok_btns/total_btns)}%)")
        
        # Sauver
        with open("/home/user/ERP-FABS-V10/RAPPORT_AUDIT_FINAL.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport : /home/user/ERP-FABS-V10/RAPPORT_AUDIT_FINAL.json")

asyncio.run(main())
