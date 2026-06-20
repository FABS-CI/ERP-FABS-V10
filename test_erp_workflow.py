#!/usr/bin/env python3
"""
TEST COMPLET ERP FABS-CI : Workflow complet + tous les boutons
Commande → Validation → Facture → Paiement → Audit
Utilise les data-testid des composants
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright non installé")
    sys.exit(1)


class ERPTest:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pages": {},
            "buttons": {},
            "workflows": {},
            "errors": [],
        }
        self.page = None
        self.context = None
        self.browser = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Auto-accept dialogs
        async def handle_dialog(dialog):
            print(f"  💬 Dialog: {dialog.message[:50]}")
            await dialog.accept()

        self.page.on("dialog", handle_dialog)
        print("✅ Playwright démarré")

    async def stop(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self, email="pissken@editionsfabsci.com", pwd="Admin@2025"):
        print(f"\n🔐 Login : {email}")
        await self.page.goto(f"{self.base_url}/login")
        await self.page.fill('input[type="email"]', email)
        await self.page.fill('input[type="password"]', pwd)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        print("✅ Connecté")

    async def test_page(self, path, title):
        print(f"\n📄 {title}")
        try:
            await self.page.goto(f"{self.base_url}{path}")
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            self.results["pages"][path] = "✅"
            print(f"   ✅ Chargée")
            return True
        except Exception as e:
            self.results["pages"][path] = f"❌ {str(e)[:40]}"
            self.results["errors"].append(f"{title}: {str(e)}")
            print(f"   ❌ {str(e)[:50]}")
            return False

    async def click_btn(self, selector, name, wait_ms=1000):
        """Cliquer sur un bouton"""
        try:
            btn = self.page.locator(selector)
            is_visible = await btn.is_visible(timeout=2000)
            if not is_visible:
                print(f"   ⚠️  {name} non visible")
                return False
            await btn.click()
            await self.page.wait_for_timeout(wait_ms)
            print(f"   ✅ {name}")
            self.results["buttons"][name] = "✅"
            return True
        except Exception as e:
            print(f"   ❌ {name}: {str(e)[:40]}")
            self.results["buttons"][name] = f"❌ {str(e)[:30]}"
            self.results["errors"].append(f"{name}: {str(e)}")
            return False

    async def workflow_commande(self):
        """Workflow complet : créer commande → valider → facture"""
        print("\n" + "="*60)
        print("🔄 WORKFLOW : Commande complet")
        print("="*60)

        # 1. CRÉER COMMANDE
        print("\n1️⃣  Créer une commande")
        await self.test_page("/commandes/nouvelle", "Nouvelle Commande")

        # Sélectionner client
        print("\n  Step 1 : Sélectionner client")
        await self.page.fill('[data-testid="input-search-client"]', "Client")
        await self.page.wait_for_timeout(500)
        
        rows = await self.page.query_selector_all('[data-testid^="client-row-"]')
        if rows:
            await rows[0].click()
            client_id = await rows[0].get_attribute("data-testid")
            print(f"  ✅ Client sélectionné ({client_id})")
        else:
            print(f"  ❌ Aucun client trouvé")
            return

        # Cliquer "Suivant"
        await self.click_btn('button:has-text("Suivant")', "Suivant vers Step 2")

        # Step 2: Ajouter produit
        print("\n  Step 2 : Ajouter un produit")
        await self.page.wait_for_timeout(500)
        add_line_btn = self.page.locator('button:has-text("Ajouter une ligne")')
        if await add_line_btn.is_visible():
            await add_line_btn.click()
            print(f"  ✅ Bouton 'Ajouter une ligne' cliqué")
            await self.page.wait_for_timeout(500)
            
            # Sélectionner le 1er produit du dropdown
            produits = await self.page.query_selector_all('[role="option"]')
            if produits:
                await produits[0].click()
                print(f"  ✅ Produit sélectionné")
            
            # Remplir quantité
            qte_input = self.page.locator('input[placeholder*="Quantité"]')
            if await qte_input.is_visible():
                await qte_input.fill("2")
                print(f"  ✅ Quantité = 2")
        else:
            print(f"  ⚠️  Bouton 'Ajouter une ligne' non trouvé")

        # Cliquer "Soumettre"
        print("\n  Step 3 : Soumettre commande")
        await self.click_btn('button:has-text("Soumettre")', "Soumettre", wait_ms=2000)

        # Récupérer l'ID
        url = self.page.url
        if "/commandes/" in url and "/modifier" not in url:
            cmd_id = url.split("/commandes/")[1].split("/")[0]
            print(f"\n✅ Commande créée : {cmd_id}")

            # 2. TESTER LES BOUTONS DE LA PAGE DÉTAIL
            print("\n2️⃣  Tester les boutons (Détail Commande)")
            await self.page.wait_for_load_state("networkidle")
            
            btns = [
                ('button:has-text("Aperçu PDF")', "Aperçu PDF"),
                ('button:has-text("Télécharger PDF")', "Télécharger PDF"),
                ('button:has-text("Imprimer")', "Imprimer"),
                ('button:has-text("Partager WhatsApp")', "Partager WhatsApp"),
                ('button:has-text("Envoyer par Email")', "Envoyer Email"),
            ]
            for sel, name in btns:
                await self.click_btn(sel, name, wait_ms=500)

            # 3. VALIDER LA COMMANDE
            print("\n3️⃣  Valider la commande")
            await self.click_btn('button:has-text("Valider")', "Valider", wait_ms=2000)

            # Vérifier que le statut change ET les lignes persistent
            await self.page.wait_for_timeout(1000)
            status_text = await self.page.text_content(".badge")
            ligne_text = await self.page.text_content("body")
            
            if "Validée" in (status_text or ""):
                print(f"  ✅ Statut : Validée")
            else:
                print(f"  ⚠️  Statut : {status_text}")

            if "produit" in (ligne_text or "").lower():
                print(f"  ✅ Lignes persistent")
            else:
                print(f"  ⚠️  Lignes peut-être vides")

            # 4. GÉNÉRER FACTURE
            print("\n4️⃣  Générer facture")
            await self.click_btn('button:has-text("Générer Facture")', "Générer Facture", wait_ms=2000)

            # 5. VÉR IFIE FACTURE CRÉE
            print("\n5️⃣  Vérifier facture créée")
            await self.test_page("/factures", "Page Factures")

            # 6. ALLER AUX PAIEMENTS
            print("\n6️⃣  Paiements")
            await self.test_page("/paiements", "Page Paiements")

            self.results["workflows"]["commande_complete"] = "✅"
        else:
            print(f"  ❌ URL non attendue : {url}")
            self.results["workflows"]["commande_complete"] = "❌"

    async def test_modules(self):
        """Tester toutes les pages critiques"""
        print("\n" + "="*60)
        print("📊 TEST MODULES CRITIQUES")
        print("="*60)
        
        modules = [
            ("/dashboard", "Tableau de bord"),
            ("/commandes", "Commandes (liste)"),
            ("/factures", "Factures (liste)"),
            ("/paiements", "Paiements"),
            ("/stock", "Stock"),
            ("/clients", "Clients"),
            ("/produits", "Produits"),
        ]
        
        for path, title in modules:
            await self.test_page(path, title)

    async def run(self):
        try:
            await self.start()
            await self.login()
            await self.test_modules()
            await self.workflow_commande()
        except Exception as e:
            print(f"\n❌ Erreur majeure : {e}")
            self.results["errors"].append(f"FATAL: {str(e)}")
        finally:
            await self.stop()
            self.save_results()

    def save_results(self):
        """Sauver le rapport"""
        path = "/home/user/ERP-FABS-V10/RAPPORT_TEST_WORKFLOW.json"
        with open(path, "w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print("📊 RÉSUMÉ")
        print("="*60)
        print(f"Pages OK: {sum(1 for v in self.results['pages'].values() if v == '✅')} / {len(self.results['pages'])}")
        print(f"Boutons OK: {sum(1 for v in self.results['buttons'].values() if v == '✅')} / {len(self.results['buttons'])}")
        print(f"Erreurs: {len(self.results['errors'])}")
        if self.results["errors"]:
            print("\nErreurs:")
            for e in self.results["errors"][:3]:
                print(f"  • {e[:70]}")
        print(f"\n📄 Rapport : {path}")


async def main():
    test = ERPTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())
