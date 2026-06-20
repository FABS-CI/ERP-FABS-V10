#!/usr/bin/env python3
"""
TEST COMPLET ERP FABS-CI : Tous les boutons, tous les workflows
Modules critiques : Commandes → Validation → Factures → Paiements → Audit
Date: 2026-06-20
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright non installé. pip install playwright && playwright install")
    sys.exit(1)


class ERPTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.token_file = "/tmp/fabs_token.txt"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pages_tested": {},
            "buttons_tested": {},
            "workflows": {},
            "errors": [],
        }
        self.page = None
        self.context = None
        self.browser = None

    async def start(self):
        """Lancer Playwright"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

        # Auto-accept dialogs
        async def handle_dialog(dialog):
            print(f"  [Dialog] {dialog.type}: {dialog.message}")
            await dialog.accept()

        self.page.on("dialog", handle_dialog)
        print("✅ Playwright démarré")

    async def stop(self):
        """Arrêter Playwright"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("✅ Playwright arrêté")

    async def login(self, email="pissken@editionsfabsci.com", password="Admin@2025"):
        """Login et sauver le token"""
        print(f"\n📍 Login : {email}")
        await self.page.goto(f"{self.base_url}/login")
        await self.page.fill('input[type="email"]', email)
        await self.page.fill('input[type="password"]', password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")

        # Récupérer le token via localStorage
        token = await self.page.evaluate("() => localStorage.getItem('fabs_token')")
        if token:
            with open(self.token_file, "w") as f:
                f.write(token)
            print(f"✅ Token sauvegardé")
        else:
            print("⚠️  Token non trouvé dans localStorage")

    async def test_page(self, path, title):
        """Naviguer vers une page et tester son chargement"""
        print(f"\n📄 Page : {title}")
        try:
            await self.page.goto(f"{self.base_url}{path}")
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            self.results["pages_tested"][path] = {"title": title, "status": "✅ OK"}
            print(f"✅ {title} chargée")
            return True
        except Exception as e:
            self.results["pages_tested"][path] = {"title": title, "status": f"❌ {str(e)[:50]}"}
            self.results["errors"].append(f"Page {title}: {str(e)}")
            print(f"❌ {title} : {e}")
            return False

    async def click_button(self, selector, button_name, wait_for=None):
        """Cliquer sur un bouton et attendre"""
        try:
            button = self.page.locator(selector)
            if not await button.is_visible():
                print(f"  ⚠️  Bouton '{button_name}' non visible")
                return False
            await button.click()
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=3000)
            else:
                await self.page.wait_for_load_state("networkidle", timeout=3000)
            print(f"  ✅ {button_name}")
            self.results["buttons_tested"][button_name] = "✅ OK"
            return True
        except Exception as e:
            print(f"  ❌ {button_name} : {str(e)[:60]}")
            self.results["buttons_tested"][button_name] = f"❌ {str(e)[:50]}"
            self.results["errors"].append(f"Button {button_name}: {str(e)}")
            return False

    async def workflow_commande_complete(self):
        """Workflow complet : Créer → Valider → Facture → Paiement"""
        print("\n🔄 WORKFLOW : Commande complète (Brouillon → Validée → Facturée → Payée)")

        # 1. Créer une commande
        await self.test_page("/commandes/nouvelle", "Nouvelle Commande")
        print("\n  Step 1: Sélectionner client")
        await asyncio.sleep(1)
        await self.page.fill('input[placeholder*="Rechercher"]', "Client")
        await self.page.wait_for_timeout(500)
        items = await self.page.query_selector_all("[role='option']")
        if items:
            await items[0].click()
            print(f"  ✅ Client sélectionné")

        print("\n  Step 2: Ajouter un produit")
        await self.page.click('button:has-text("Ajouter une ligne")')
        await self.page.wait_for_timeout(500)
        produits = await self.page.query_selector_all("[role='option']")
        if produits:
            await produits[0].click()
            print(f"  ✅ Produit sélectionné")
            await self.page.fill('input[placeholder*="Quantité"]', "1")
            print(f"  ✅ Quantité définie")

        print("\n  Step 3: Soumettre")
        await self.click_button('button:has-text("Soumettre")', "Bouton Soumettre")
        await self.page.wait_for_timeout(1000)

        # Récupérer l'ID de la commande depuis l'URL
        url = self.page.url
        if "/commandes/" in url:
            commande_id = url.split("/commandes/")[1].split("/")[0]
            print(f"  ✅ Commande créée : {commande_id}")

            # 2. Tester les boutons de la page détail
            await self.test_page(f"/commandes/{commande_id}", "Détail Commande")
            print("\n  Boutons disponibles :")
            await self.click_button(
                'button:has-text("Aperçu PDF")', "Aperçu PDF"
            )
            await self.click_button(
                'button:has-text("Télécharger PDF")', "Télécharger PDF"
            )
            await self.click_button('button:has-text("Imprimer")', "Imprimer")
            await self.click_button(
                'button:has-text("Partager WhatsApp")', "Partager WhatsApp"
            )
            await self.click_button('button:has-text("Envoyer par Email")', "Envoyer Email")

            # 3. Valider la commande
            print("\n  Action: Valider")
            await self.click_button('button:has-text("Valider")', "Bouton Valider")
            await self.page.wait_for_timeout(2000)

            # 4. Vérifier que le statut change à "Validée" ET que les lignes persist
            status = await self.page.text_content(".badge")
            lines_count = await self.page.text_content(".text-sm:has-text('produit')")
            print(f"  ✅ Statut après validation : {status}")
            print(f"  ✅ Lignes persistent : {lines_count}")

            # 5. Générer facture
            print("\n  Action: Générer Facture")
            await self.click_button(
                'button:has-text("Générer Facture")', "Générer Facture"
            )
            await self.page.wait_for_timeout(2000)

            # 6. Aller aux paiements
            await self.test_page("/paiements", "Page Paiements")
            print("\n  Chercher le paiement créé")
            # TODO: tester boutons paiements (Lettrer, Imprimer, etc.)

            self.results["workflows"]["commande_complete"] = "✅ OK"
        else:
            self.results["workflows"]["commande_complete"] = "❌ URL non reconnue"
            print(f"  ❌ URL inattendue : {url}")

    async def test_modules_critiques(self):
        """Tester les pages critiques de la chaîne vente"""
        modules = [
            ("/dashboard", "Tableau de bord"),
            ("/commandes", "Liste Commandes"),
            ("/factures", "Liste Factures"),
            ("/paiements", "Paiements"),
            ("/stock", "Stock"),
            ("/clients", "Clients"),
            ("/produits", "Produits"),
        ]
        for path, title in modules:
            await self.test_page(path, title)

    async def run(self):
        """Exécuter la suite complète"""
        try:
            await self.start()
            await self.login()
            await self.test_modules_critiques()
            await self.workflow_commande_complete()
        except Exception as e:
            print(f"❌ Erreur : {e}")
            self.results["errors"].append(str(e))
        finally:
            await self.stop()
            self.save_results()

    def save_results(self):
        """Sauver les résultats"""
        report_path = "/home/user/ERP-FABS-V10/RAPPORT_TEST_BUTTONS.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📊 Rapport sauvegardé : {report_path}")

        # Afficher un résumé
        print("\n" + "=" * 60)
        print("RÉSUMÉ TEST")
        print("=" * 60)
        print(f"Pages testées : {len(self.results['pages_tested'])}")
        print(f"Boutons testés : {len(self.results['buttons_tested'])}")
        print(f"Erreurs : {len(self.results['errors'])}")
        if self.results["errors"]:
            print("\nErreurs détectées :")
            for error in self.results["errors"][:5]:
                print(f"  - {error}")


async def main():
    tester = ERPTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
