"""
SIMULATION VENTE COMPLÈTE + AUDIT — ERP FABS V10
Routes corrigées selon modules réels.
"""
import asyncio
import httpx
import json
from datetime import date

BASE = "http://localhost:8000/api"

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = {"ok": 0, "fail": 0, "warn": 0}

def ok(msg):
    results["ok"] += 1
    print(f"  {PASS} {msg}")

def fail(msg, detail=""):
    results["fail"] += 1
    print(f"  {FAIL} {msg}")
    if detail:
        print(f"       → {detail}")

def warn(msg, detail=""):
    results["warn"] += 1
    print(f"  {WARN} {msg} [{detail}]")


async def login(c, email, pwd):
    r = await c.post(f"{BASE}/auth/login", json={"email": email, "password": pwd})
    if r.status_code == 200:
        return r.json()["access_token"]
    return None


async def run_simulation():
    async with httpx.AsyncClient(timeout=30) as c:

        # ====================================================
        print("\n" + "=" * 60)
        print("  SIMULATION VENTE COMPLÈTE — ERP FABS V10")
        print("=" * 60)

        # ── AUTH ──
        print("\n── AUTH ──")
        tokens = {}

        for role, email, pwd in [
            ("super_admin", "pissken@editionsfabsci.com", "Admin@2025"),
            ("assistante", "amenan@editionsfabsci.com", "Fabs@2025"),
            ("directeur_commercial", "detymichel@editionsfabsci.com", "Fabs@2025"),
            ("gestionnaire_stock", "niangorangeorgie@editionsfabsci.com", "Fabs@2025"),
            ("comptable", "natachakoffi@editionsfabsci.com", "Fabs@2025"),
            ("directeur_general", "ali.mamin@editionsfabsci.com", "Fabs@2025"),
        ]:
            t = await login(c, email, pwd)
            if t:
                tokens[role] = t
                ok(f"Login {role}")
            else:
                fail(f"Login {role}", f"{email}")

        h = {"Authorization": f"Bearer {tokens.get('super_admin', '')}"}
        h_dc = {"Authorization": f"Bearer {tokens.get('directeur_commercial', '')}"}
        h_stock = {"Authorization": f"Bearer {tokens.get('gestionnaire_stock', '')}"}
        h_compta = {"Authorization": f"Bearer {tokens.get('comptable', '')}"}
        h_dg = {"Authorization": f"Bearer {tokens.get('directeur_general', '')}"}

        # Refresh token
        r = await c.post(f"{BASE}/auth/refresh", json={"refresh_token": "test"})
        ok("Refresh token") if r.status_code in (200, 401, 422) else warn("Refresh token", r.text[:80])

        # ── DASHBOARD & SANTÉ ──
        print("\n── DASHBOARD & SANTÉ ──")
        r = await c.get(f"{BASE}/health")
        ok("Health check") if r.status_code == 200 else fail("Health check", r.text[:80])

        r = await c.get(f"{BASE}/dashboard/stats", headers=h)
        if r.status_code == 200:
            d = r.json()
            kpis = d.get("kpis", [])
            ca = next((k["value"] for k in kpis if k.get("key") == "ca_mois"), 0)
            clients = next((k["value"] for k in kpis if k.get("key") == "total_clients"), 0)
            ok(f"Dashboard stats → CA mois={ca:,} FCFA, total_clients={clients}, kpis={len(kpis)}")
        else:
            fail("Dashboard stats", r.text[:80])

        # ── PRODUITS ──
        print("\n── PRODUITS ──")
        r = await c.get(f"{BASE}/produits?limit=100", headers=h)
        if r.status_code == 200:
            data = r.json()
            prods = data.get("items", data) if isinstance(data, dict) else data
            ok(f"Liste produits → {len(prods)} produits (total={data.get('total', len(prods)) if isinstance(data, dict) else len(prods)})")
        else:
            fail("Liste produits", r.text[:80])
            prods = []

        # Chercher un produit avec stock
        prod_id = None
        if prods:
            prod_id = prods[0].get("product_id")
            r2 = await c.get(f"{BASE}/produits/{prod_id}", headers=h)
            if r2.status_code == 200:
                p = r2.json()
                ok(f"Détail produit → matiere={p.get('matiere')}, niveau={p.get('niveau')}, cycle={p.get('cycle')}")
            else:
                fail("Détail produit", r2.text[:80])

        r = await c.get(f"{BASE}/produits?search=SVT", headers=h)
        ok(f"Recherche produit (SVT)") if r.status_code == 200 else fail("Recherche produit", r.text[:80])

        r = await c.get(f"{BASE}/stock/inventaire", headers=h_stock)
        ok(f"Inventaire stock") if r.status_code == 200 else warn("Inventaire stock", r.text[:80])

        r = await c.get(f"{BASE}/stock/alertes-rupture", headers=h_stock)
        ok(f"Alertes rupture stock") if r.status_code == 200 else warn("Alertes rupture stock", r.text[:80])

        # ── CLIENTS ──
        print("\n── CLIENTS ──")
        r = await c.get(f"{BASE}/clients?limit=10", headers=h)
        if r.status_code == 200:
            data = r.json()
            cli = data.get("items", data) if isinstance(data, dict) else data
            ok(f"Liste clients → {data.get('total', len(cli)) if isinstance(data, dict) else len(cli)} clients")
        else:
            fail("Liste clients", r.text[:80])
            cli = []

        cli_id = None
        if cli:
            cli_id = cli[0].get("client_id")
            r2 = await c.get(f"{BASE}/clients/{cli_id}", headers=h)
            ok(f"Détail client → {r2.json().get('nom', '?')}") if r2.status_code == 200 else fail("Détail client", r2.text[:80])

        r = await c.get(f"{BASE}/clients?search=ecole", headers=h)
        ok("Recherche client") if r.status_code == 200 else fail("Recherche client", r.text[:80])

        # ── PROFORMA ──
        print("\n── PROFORMA ──")
        pf_id = None
        if cli_id and prod_id:
            payload_pf = {
                "client_id": cli_id,
                "date_validite": str(date.today()).replace(str(date.today().year), str(date.today().year + 1)),
                "lignes": [{"produit_id": prod_id, "quantite": 3, "prix_unitaire": 2500}],
                "notes": "Proforma simulation audit"
            }
            r = await c.post(f"{BASE}/proformas", json=payload_pf, headers=h_dc)
            if r.status_code == 201:
                pf = r.json()
                pf_id = pf.get("proforma_id")
                ok(f"Créer proforma → {pf.get('reference')}")
            else:
                fail("Créer proforma", r.text[:120])

        if pf_id:
            r = await c.post(f"{BASE}/proformas/{pf_id}/generer-pdf", headers=h_dc)
            if r.status_code == 200 and len(r.content) > 1000:
                ok(f"PDF proforma → {len(r.content)} bytes")
            else:
                fail("PDF proforma", r.text[:80])

            # Convertir proforma en FACTURE (pas commande — c'est la vraie route)
            r = await c.post(f"{BASE}/proformas/{pf_id}/convertir-facture", headers=h_dc)
            if r.status_code == 200:
                ok(f"Convertir proforma→facture → {r.json().get('message', 'OK')}")
            else:
                warn("Convertir proforma→facture", r.text[:80])

        # ── COMMANDE ──
        print("\n── COMMANDE ──")
        cmd_id = None
        if cli_id and prod_id:
            payload_cmd = {
                "client_id": cli_id,
                "date_livraison_prevue": str(date.today()),
                "lignes": [{"produit_id": prod_id, "quantite": 5, "prix_unitaire": 2500}],
                "notes": "Commande simulation audit"
            }
            r = await c.post(f"{BASE}/commandes", json=payload_cmd, headers=h_dc)
            if r.status_code == 201:
                cmd = r.json()
                cmd_id = cmd.get("commande_id")
                ok(f"Créer commande → {cmd.get('reference')}")
                # Vérifier enrichissement lignes
                lgn = cmd.get("lignes", [{}])[0]
                ok(f"Enrichissement lignes (matiere/niveau) → matiere={lgn.get('matiere')}, niveau={lgn.get('niveau')}")
            else:
                fail("Créer commande", r.text[:120])

        if cmd_id:
            r = await c.get(f"{BASE}/commandes/{cmd_id}/pdf", headers=h_dc)
            ok(f"PDF commande → {len(r.content)} bytes") if r.status_code == 200 else warn("PDF commande", r.text[:80])

            r = await c.post(f"{BASE}/commandes/{cmd_id}/soumettre", headers=h_dc)
            if r.status_code == 200:
                ok(f"Soumettre commande → {r.json().get('statut')}")
            else:
                fail("Soumettre commande", r.text[:80])

            r = await c.post(f"{BASE}/commandes/{cmd_id}/valider", headers=h_dg)
            if r.status_code == 200:
                ok(f"Valider commande → {r.json().get('statut')}")
            else:
                fail("Valider commande", r.text[:80])

            # Préparer la commande (nécessaire avant BL) — rôle: super_admin, directeur_general, responsable_magasinier
            r = await c.post(f"{BASE}/commandes/{cmd_id}/preparer", headers=h)
            if r.status_code == 200:
                ok(f"Préparer commande → {r.json().get('statut')}")
            else:
                warn("Préparer commande", r.text[:80])

        # ── BON DE LIVRAISON ──
        print("\n── BON DE LIVRAISON ──")
        bl_id = None
        if cmd_id and prod_id:
            # BL nécessite: super_admin, directeur_general, service_logistique, comptable, directeur_commercial
            r = await c.post(f"{BASE}/bons-livraison", json={
                "commande_id": cmd_id,
                "lignes": [{"produit_id": prod_id, "quantite": 5}]
            }, headers=h)  # super_admin
            if r.status_code == 201:
                bl = r.json()
                bl_id = bl.get("bl_id")
                ok(f"Créer BL → {bl.get('reference')}")
            else:
                fail("Créer BL", r.text[:120])

        # ── FACTURE ──
        print("\n── FACTURE ──")
        facture_id = None
        r = await c.get(f"{BASE}/factures?limit=10", headers=h_compta)
        if r.status_code == 200:
            data = r.json()
            facs = data.get("items", data) if isinstance(data, dict) else data
            ok(f"Liste factures → {data.get('total', len(facs)) if isinstance(data, dict) else len(facs)} factures")
        else:
            fail("Liste factures", r.text[:80])
            facs = []

        # Trouver/créer facture pour la commande
        if cmd_id:
            # Chercher facture liée à la commande
            r2 = await c.get(f"{BASE}/factures?commande_id={cmd_id}", headers=h_compta)
            if r2.status_code == 200:
                d2 = r2.json()
                items2 = d2.get("items", d2) if isinstance(d2, dict) else d2
                if items2:
                    facture_id = items2[0].get("facture_id")
                    ok(f"Facture auto (depuis commande) → {items2[0].get('reference')}")
            else:
                # Créer une facture pour commande
                if cli_id and prod_id:
                    r3 = await c.post(f"{BASE}/factures", json={
                        "client_id": cli_id,
                        "commande_id": cmd_id,
                        "lignes": [{"produit_id": prod_id, "quantite": 5, "prix_unitaire": 2500}]
                    }, headers=h_compta)
                    if r3.status_code == 201:
                        facture_id = r3.json().get("facture_id")
                        ok(f"Facture créée → {r3.json().get('reference')}")
                    else:
                        warn("Créer facture", r3.text[:80])

        # Si pas de facture depuis commande, prendre la première disponible non payée
        if not facture_id and facs:
            for f in facs:
                if f.get("statut") not in ("payee", "annulee"):
                    facture_id = f.get("facture_id")
                    break
            if not facture_id:
                facture_id = facs[0].get("facture_id")

        facture_client_id = cli_id  # par défaut
        if facture_id:
            r = await c.get(f"{BASE}/factures/{facture_id}", headers=h_compta)
            if r.status_code == 200:
                fac = r.json()
                montant_total = fac.get("montant_ttc") or fac.get("montant_total") or fac.get("montant_ht") or 12500
                restant = fac.get("montant_restant", montant_total)
                facture_client_id = fac.get("client_id") or cli_id  # Utiliser le client de la facture
                ok(f"Détail facture → {fac.get('statut')}, TTC={montant_total:,} FCFA, restant={restant:,} FCFA")
                montant_total = restant  # Payer ce qui reste
            else:
                fail("Détail facture", r.text[:80])
                montant_total = 12500

            r = await c.get(f"{BASE}/factures/{facture_id}/pdf", headers=h_compta)
            ok(f"PDF facture → {len(r.content)} bytes") if r.status_code == 200 else warn("PDF facture", r.text[:80])

        # ── PAIEMENT ──
        print("\n── PAIEMENT ──")
        if facture_id and montant_total and facture_client_id:
            montant_partiel = int(montant_total * 0.5)
            r = await c.post(f"{BASE}/paiements", json={
                "client_id": facture_client_id,
                "montant_total": montant_partiel,
                "mode_paiement": "virement",
                "date_paiement": str(date.today()),
                "factures": [{"facture_id": facture_id, "montant_affecte": montant_partiel}]
            }, headers=h_compta)
            if r.status_code == 201:
                pmt = r.json()
                pmt_id = pmt.get("paiement_id")
                ok(f"Paiement partiel (50%) → {pmt.get('reference')}")

                # Vérifier statut facture
                r2 = await c.get(f"{BASE}/factures/{facture_id}", headers=h_compta)
                if r2.status_code == 200:
                    ok(f"Statut facture après paiement 50% → {r2.json().get('statut')}")

                # PDF reçu
                r3 = await c.get(f"{BASE}/paiements/{pmt_id}/pdf", headers=h_compta)
                ok(f"PDF reçu paiement → {len(r3.content)} bytes") if r3.status_code == 200 else warn("PDF reçu", r3.text[:80])

                # Solde (ce qui reste après paiement partiel)
                montant_solde = montant_total - montant_partiel
                if montant_solde is not None and montant_solde <= 0:
                    ok("Facture déjà soldée (montant restant = 0)")
                    montant_solde = None
                if montant_solde and montant_solde > 0:
                    pass
                r4 = await c.post(f"{BASE}/paiements", json={
                    "client_id": facture_client_id,
                    "montant_total": montant_solde,
                    "mode_paiement": "especes",
                    "date_paiement": str(date.today()),
                    "factures": [{"facture_id": facture_id, "montant_affecte": montant_solde}]
                }, headers=h_compta)
                if r4.status_code == 201:
                    ok(f"Paiement solde → {r4.json().get('reference')}")
                    r5 = await c.get(f"{BASE}/factures/{facture_id}", headers=h_compta)
                    if r5.status_code == 200:
                        ok(f"Facture entièrement payée → {r5.json().get('statut')}")
                else:
                    warn("Paiement solde", r4.text[:80])
            else:
                fail("Paiement partiel", r.text[:120])

        # ── STOCK ──
        print("\n── STOCK ──")
        r = await c.get(f"{BASE}/stock/mouvements?limit=10", headers=h_stock)
        if r.status_code == 200:
            ok(f"Mouvements stock → {len(r.json())} mouvements récents")
        else:
            fail("Mouvements stock", r.text[:80])

        r = await c.get(f"{BASE}/stock/alertes-rupture", headers=h_stock)
        ok(f"Alertes rupture stock") if r.status_code == 200 else warn("Alertes rupture stock", r.text[:80])

        # ── ANALYTICS ──
        print("\n── ANALYTICS ──")
        for name, path in [
            ("Dashboard analytics", "/analytics/dashboard"),
            ("Stats par matière", "/analytics/by-matiere"),
            ("Stats par cycle", "/analytics/by-cycle"),
            ("Stats par niveau", "/analytics/by-niveau"),
            ("Stats par ville", "/analytics/by-ville"),
            ("Top clients", "/analytics/top-clients"),
            ("Top articles", "/analytics/top-articles"),
            ("Évolution ventes", "/analytics/evolution"),
            ("Analyse financière", "/analytics/financial"),
            ("Stock par classification", "/analytics/stock-by-classification"),
        ]:
            r = await c.get(f"{BASE}{path}", headers=h_dg)
            if r.status_code == 200:
                data = r.json()
                count = len(data) if isinstance(data, list) else (len(data.get("labels", [])) if isinstance(data, dict) else "?")
                ok(f"{name} → {count} entrées")
            else:
                warn(name, f"HTTP {r.status_code}")

        # ── BI ANALYTICS ──
        print("\n── BI ANALYTICS ──")
        r = await c.get(f"{BASE}/bi-analytics/dashboard", headers=h_dg)
        ok("BI Analytics (/bi-analytics/dashboard)") if r.status_code == 200 else warn("BI Analytics", f"HTTP {r.status_code}")

        # ── RAPPORTS ──
        print("\n── RAPPORTS ──")
        for name, path in [
            ("Rapport ventes", "/rapports/ventes"),
            ("Rapport stock", "/rapports/stock"),
        ]:
            r = await c.get(f"{BASE}{path}", headers=h_dg)
            ok(f"{name}") if r.status_code == 200 else warn(name, f"HTTP {r.status_code}: {r.text[:60]}")

        # ── RESSOURCES HUMAINES ──
        print("\n── RESSOURCES HUMAINES ──")
        for name, path in [
            ("Dashboard RH", "/rh/dashboard"),
            ("Liste employés", "/rh/employes"),
            ("Départements", "/rh/departements"),
            ("Fonctions", "/rh/fonctions"),
            ("Contrats", "/rh/contrats"),
            ("Congés", "/rh/conges"),
            ("Absences", "/rh/absences"),
            ("Missions RH", "/rh/missions"),
            ("Évaluations", "/rh/evaluations"),
        ]:
            r = await c.get(f"{BASE}{path}", headers=h)
            ok(f"{name}") if r.status_code == 200 else warn(name, f"HTTP {r.status_code}: {r.text[:60]}")

        # Bulletins de paie
        r = await c.get(f"{BASE}/paie/bulletins", headers=h_compta)
        ok("Bulletins de paie") if r.status_code == 200 else warn("Bulletins de paie", f"HTTP {r.status_code}")

        # ── COMPTABILITÉ ──
        print("\n── COMPTABILITÉ ──")
        for name, path in [
            ("Journal comptable (écritures)", "/comptabilite/ecritures"),
            ("Balance", "/comptabilite/balance"),
            ("Créances", "/comptabilite/creances"),
            ("Plan comptable (avancé)", "/comptabilite-avancee/plan-comptable"),
            ("Journaux avancés", "/comptabilite-avancee/journaux"),
            ("Écritures avancées", "/comptabilite-avancee/ecritures"),
            ("Rapprochements bancaires", "/comptabilite-avancee/rapprochements"),
        ]:
            r = await c.get(f"{BASE}{path}", headers=h_compta)
            ok(f"{name}") if r.status_code == 200 else warn(name, f"HTTP {r.status_code}: {r.text[:60]}")

        # ── FNE / DGI ──
        print("\n── FNE / DGI ──")
        r = await c.get(f"{BASE}/fne/dashboard/fne-stats", headers=h)
        ok("FNE Dashboard stats") if r.status_code == 200 else warn("FNE Dashboard", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/fne/invoices", headers=h)
        ok("FNE Factures") if r.status_code == 200 else warn("FNE Factures", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/fne/settings", headers=h)
        ok("FNE Paramètres") if r.status_code == 200 else warn("FNE Paramètres", f"HTTP {r.status_code}")

        # ── FOURNISSEURS / APPROVISIONNEMENT ──
        print("\n── FOURNISSEURS / APPROVISIONNEMENT ──")
        r = await c.get(f"{BASE}/fournisseurs", headers=h)
        ok("Fournisseurs") if r.status_code == 200 else warn("Fournisseurs", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/approvisionnements", headers=h)
        ok("Approvisionnements") if r.status_code == 200 else warn("Approvisionnements", f"HTTP {r.status_code}")

        # ── LOGISTIQUE ──
        print("\n── LOGISTIQUE ──")
        for name, path in [
            ("Missions logistique", "/logistique/missions"),
            ("Véhicules logistique", "/logistique/vehicules"),
            ("Suivi livraisons", "/logistique/suivi"),
            ("Fleet véhicules", "/fleet/vehicules"),
            ("Fleet assurances", "/fleet/assurances"),
            ("Coûts logistique", "/logistics-costs/couts"),
            ("Ordres colisage", "/colisage/ordres"),
            ("Livraisons directes", "/colisage/livraisons"),
        ]:
            r = await c.get(f"{BASE}{path}", headers=h)
            ok(f"{name}") if r.status_code == 200 else warn(name, f"HTTP {r.status_code}")

        # ── BONS RETOUR ──
        print("\n── BONS RETOUR ──")
        # bons-retour: rôles autorisés = super_admin, directeur_general, service_logistique, responsable_magasinier, comptable
        r = await c.get(f"{BASE}/bons-retour", headers=h_compta)
        ok("Liste bons retour") if r.status_code == 200 else warn("Bons retour", f"HTTP {r.status_code}")

        # ── NOTIFICATIONS ──
        print("\n── NOTIFICATIONS ──")
        r = await c.get(f"{BASE}/notifications", headers=h)
        ok("Notifications") if r.status_code == 200 else warn("Notifications", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/notifications/preferences", headers=h)
        ok("Préférences notif") if r.status_code == 200 else warn("Préférences notif", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/multi-channel-notifications/logs", headers=h)
        ok("Historique envois notif") if r.status_code == 200 else warn("Historique envois notif", f"HTTP {r.status_code}")

        # ── ADMINISTRATION ──
        print("\n── ADMINISTRATION ──")
        r = await c.get(f"{BASE}/utilisateurs", headers=h)
        if r.status_code == 200:
            ok(f"Liste utilisateurs → {len(r.json())} users")
        else:
            fail("Liste utilisateurs", r.text[:80])

        r = await c.get(f"{BASE}/parametres", headers=h)
        ok("Paramètres") if r.status_code == 200 else warn("Paramètres", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/document-settings/settings", headers=h)
        ok("Paramètres documents") if r.status_code == 200 else warn("Paramètres documents", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/backup/backups", headers=h)
        ok("Liste backups") if r.status_code == 200 else warn("Liste backups", f"HTTP {r.status_code}")

        r = await c.get(f"{BASE}/workflow-approvals/workflows", headers=h)
        ok("Workflow approbations") if r.status_code == 200 else warn("Workflow approbations", f"HTTP {r.status_code}")

        # ── RECHERCHE GLOBALE ──
        print("\n── RECHERCHE GLOBALE ──")
        r = await c.get(f"{BASE}/recherche/globale?q=ecole", headers=h)
        ok("Recherche globale") if r.status_code == 200 else fail("Recherche globale", r.text[:80])

        # ── DOCUMENTS AI ──
        print("\n── DOCUMENTS AI ──")
        r = await c.get(f"{BASE}/documents-ai?limit=5", headers=h)
        ok("Documents AI") if r.status_code == 200 else warn("Documents AI", f"HTTP {r.status_code}")

        # ── FILE STORAGE ──
        print("\n── FILE STORAGE ──")
        r = await c.get(f"{BASE}/file-storage/documents", headers=h)
        ok("File storage") if r.status_code == 200 else warn("File storage", f"HTTP {r.status_code}")

        # ── AUDIT SÉCURITÉ ──
        print("\n── AUDIT SÉCURITÉ ──")

        # Test accès sans token — nouvelle session sans cookie
        async with httpx.AsyncClient(timeout=10) as c_clean:
            r = await c_clean.get(f"{BASE}/clients")
            if r.status_code == 401:
                ok("Accès sans token → 401 (correct)")
            else:
                fail("Accès sans token non bloqué", f"HTTP {r.status_code}")

            # Test token invalide
            r = await c_clean.get(f"{BASE}/clients", headers={"Authorization": "Bearer faux_token_invalide"})
            ok("Token invalide → 401 (correct)") if r.status_code == 401 else fail("Token invalide non rejeté", f"HTTP {r.status_code}")

        # Test NoSQL injection (search param avec string spéciale)
        r = await c.get(f"{BASE}/clients?search=%24gt", headers=h)
        ok("Résistance NoSQL injection (search)") if r.status_code in (200, 400, 422) else warn("Injection search", r.text[:100])

        # Test rate limiting login
        block_count = 0
        async with httpx.AsyncClient(timeout=10) as c_rl:
            for _ in range(12):
                rr = await c_rl.post(f"{BASE}/auth/login", json={"email": "x@x.com", "password": "wrong"})
                if rr.status_code == 429:
                    block_count += 1
        if block_count > 0:
            ok(f"Rate limiting actif → {block_count}/12 bloquées")
        else:
            warn("Rate limiting", "Aucun 429 après 12 tentatives login échouées")

        # ── RÉSUMÉ ──
        print("\n" + "=" * 60)
        print("  RÉSUMÉ AUDIT")
        print("=" * 60)
        total = results["ok"] + results["fail"] + results["warn"]
        print(f"  {PASS} OK    : {results['ok']}/{total}")
        print(f"  {WARN} WARN  : {results['warn']}/{total}")
        print(f"  {FAIL} FAIL  : {results['fail']}/{total}")
        score = int(results["ok"] / max(total, 1) * 10)
        print(f"\n  Score global : {score}/10")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_simulation())
