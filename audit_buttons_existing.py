#!/usr/bin/env python3
"""
AUDIT COMPLET ERP : Tester tous les boutons des pages EXISTANTES
Commandes (liste + détail) → Factures → Paiements → Stock → Clients → Produits
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
            "date": datetime.now().isoformat(),
            "modules": {}
        }
        
        # Auto-accept dialogs
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))
        
        # LOGIN
        print("🔐 Login...")
        await page.goto("http://localhost:3000/login")
        await page.fill('input[type="email"]', "pissken@editionsfabsci.com")
        await page.fill('input[type="password"]', "Admin@2025")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        print("✅ Connecté\n")
        
        # === COMMANDES (LISTE) ===
        print("="*60)
        print("1. PAGE COMMANDES (LISTE)")
        print("="*60)
        
        await page.goto("http://localhost:3000/commandes")
        await page.wait_for_load_state("networkidle")
        
        cmd_list_btns = {
            'btn-nova-cmd': 'button:has-text("Nouvelle commande")',
            'btn-filter': 'button:has-text("Filtrer")',
            'btn-search': 'input[placeholder*="Rechercher"]',
        }
        
        results["modules"]["Commandes (liste)"] = {
            "buttons": {},
            "rows_clickable": False
        }
        
        for btn_id, sel in cmd_list_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=2000)
                results["modules"]["Commandes (liste)"]["buttons"][btn_id] = "✅" if is_visible else "❌"
                print(f"  {btn_id}: {'✅' if is_visible else '❌'}")
            except:
                results["modules"]["Commandes (liste)"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        # Chercher une commande cliquable
        rows = await page.query_selector_all("tbody tr, [role='row']")
        if rows:
            print(f"  Lignes trouvées: {len(rows)}")
            results["modules"]["Commandes (liste)"]["rows_clickable"] = len(rows) > 0
            
            # Cliquer sur la première ligne
            for row in rows[:1]:
                try:
                    await row.click()
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    url = page.url
                    if "/commandes/" in url:
                        print(f"  ✅ Ligne cliquable → {url}")
                        break
                except:
                    pass
        
        # === COMMANDE DÉTAIL ===
        print("\n" + "="*60)
        print("2. PAGE COMMANDE (DÉTAIL)")
        print("="*60)
        
        results["modules"]["Commande (détail)"] = {"buttons": {}}
        
        detail_btns = {
            'apercu-pdf': 'button:has-text("Aperçu PDF")',
            'telecharger-pdf': 'button:has-text("Télécharger")',
            'imprimer': 'button:has-text("Imprimer")',
            'whatsapp': 'button:has-text("WhatsApp")',
            'email': 'button:has-text("Email")',
            'valider': 'button:has-text("Valider")',
            'preparer': 'button:has-text("Préparer")',
            'livrer': 'button:has-text("Marquer livrée")',
            'facture': 'button:has-text("Générer Facture")',
            'annuler': 'button:has-text("Annuler")',
            'supprimer': 'button:has-text("Supprimer")',
        }
        
        for btn_id, sel in detail_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=1000)
                results["modules"]["Commande (détail)"]["buttons"][btn_id] = "✅" if is_visible else "⚠️"
                print(f"  {btn_id}: {'✅' if is_visible else '⚠️'}")
            except:
                results["modules"]["Commande (détail)"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        # === FACTURES (LISTE) ===
        print("\n" + "="*60)
        print("3. PAGE FACTURES (LISTE)")
        print("="*60)
        
        await page.goto("http://localhost:3000/factures")
        await page.wait_for_load_state("networkidle")
        
        results["modules"]["Factures (liste)"] = {"buttons": {}}
        
        facture_list_btns = {
            'btn-nova-facture': 'button:has-text("Nouvelle facture")',
            'btn-filter': 'button:has-text("Filtrer")',
            'btn-search': 'input[placeholder*="Rechercher"]',
        }
        
        for btn_id, sel in facture_list_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=2000)
                results["modules"]["Factures (liste)"]["buttons"][btn_id] = "✅" if is_visible else "❌"
                print(f"  {btn_id}: {'✅' if is_visible else '❌'}")
            except:
                results["modules"]["Factures (liste)"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        # === FACTURE DÉTAIL ===
        print("\n" + "="*60)
        print("4. PAGE FACTURE (DÉTAIL)")
        print("="*60)
        
        # Chercher une facture
        rows = await page.query_selector_all("tbody tr, [role='row']")
        if rows:
            for row in rows[:1]:
                try:
                    await row.click()
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    break
                except:
                    pass
        
        results["modules"]["Facture (détail)"] = {"buttons": {}}
        
        facture_detail_btns = {
            'apercu-pdf': 'button:has-text("Aperçu PDF")',
            'telecharger-pdf': 'button:has-text("Télécharger")',
            'imprimer': 'button:has-text("Imprimer")',
            'email': 'button:has-text("Email")',
            'marquer-payee': 'button:has-text("Marquer payée")',
            'annuler': 'button:has-text("Annuler")',
        }
        
        for btn_id, sel in facture_detail_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=1000)
                results["modules"]["Facture (détail)"]["buttons"][btn_id] = "✅" if is_visible else "⚠️"
                print(f"  {btn_id}: {'✅' if is_visible else '⚠️'}")
            except:
                results["modules"]["Facture (détail)"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        # === PAIEMENTS ===
        print("\n" + "="*60)
        print("5. PAGE PAIEMENTS")
        print("="*60)
        
        await page.goto("http://localhost:3000/paiements")
        await page.wait_for_load_state("networkidle")
        
        results["modules"]["Paiements"] = {"buttons": {}}
        
        paiement_btns = {
            'btn-nova-paiement': 'button:has-text("Nouveau paiement")',
            'btn-filter': 'button:has-text("Filtrer")',
            'btn-lettrer': 'button:has-text("Lettrer")',
        }
        
        for btn_id, sel in paiement_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=2000)
                results["modules"]["Paiements"]["buttons"][btn_id] = "✅" if is_visible else "⚠️"
                print(f"  {btn_id}: {'✅' if is_visible else '⚠️'}")
            except:
                results["modules"]["Paiements"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        # === STOCK ===
        print("\n" + "="*60)
        print("6. PAGE STOCK")
        print("="*60)
        
        await page.goto("http://localhost:3000/stock")
        await page.wait_for_load_state("networkidle")
        
        results["modules"]["Stock"] = {"buttons": {}}
        
        stock_btns = {
            'btn-ajustement': 'button:has-text("Ajustement")',
            'btn-transfert': 'button:has-text("Transfert")',
            'btn-filter': 'button:has-text("Filtrer")',
        }
        
        for btn_id, sel in stock_btns.items():
            try:
                btn = page.locator(sel)
                is_visible = await btn.is_visible(timeout=2000)
                results["modules"]["Stock"]["buttons"][btn_id] = "✅" if is_visible else "⚠️"
                print(f"  {btn_id}: {'✅' if is_visible else '⚠️'}")
            except:
                results["modules"]["Stock"]["buttons"][btn_id] = "❌"
                print(f"  {btn_id}: ❌")
        
        await browser.close()
        
        # Sauver résumé
        with open("/home/user/ERP-FABS-V10/AUDIT_BUTTONS.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print("RÉSUMÉ")
        print("="*60)
        
        total_btns = sum(len(m.get("buttons", {})) for m in results["modules"].values())
        ok_btns = sum(1 for m in results["modules"].values() for v in m.get("buttons", {}).values() if v == "✅")
        
        print(f"Modules testés: {len(results['modules'])}")
        print(f"Boutons OK: {ok_btns} / {total_btns}")
        
        for module, data in results["modules"].items():
            ok = sum(1 for v in data.get("buttons", {}).values() if v == "✅")
            total = len(data.get("buttons", {}))
            print(f"  • {module}: {ok}/{total}")
        
        print(f"\n📄 Audit: /home/user/ERP-FABS-V10/AUDIT_BUTTONS.json")

asyncio.run(main())
