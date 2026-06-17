"""
Simulation d'activité réelle — Éditions FABSCI.
Teste les flux métier de bout en bout via l'API et capture les erreurs réelles.
"""
import asyncio
import httpx
import json
import random
from datetime import datetime, timezone, timedelta

BASE = "http://localhost:8001/api"
RESULTS = {"ok": [], "fail": [], "warn": []}


def log_ok(msg): RESULTS["ok"].append(msg); print(f"  ✅ {msg}")
def log_fail(msg): RESULTS["fail"].append(msg); print(f"  ❌ {msg}")
def log_warn(msg): RESULTS["warn"].append(msg); print(f"  ⚠️  {msg}")


async def login(c):
    r = await c.post(f"{BASE}/auth/login", json={"email": "pissken@editionsfabsci.com", "password": "Fabs@2026"})
    if r.status_code != 200:
        raise SystemExit(f"LOGIN FAIL: {r.status_code} {r.text}")
    return r.json()["access_token"]


async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        token = await login(c)
        H = {"Authorization": f"Bearer {token}"}

        # ============== 1. STOCK — approvisionner produits ==============
        print("\n=== 1. APPROVISIONNEMENT STOCK ===")
        r = await c.get(f"{BASE}/produits?limit=10", headers=H)
        prods = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        prods = [p for p in prods if p.get("actif")][:5]
        stock_ok = 0
        for p in prods:
            # Mouvement d'entrée stock
            mv = {
                "produit_id": p["product_id"],
                "type_mouvement": "entree",
                "quantite": 500,
                "motif": "Réapprovisionnement initial simulation",
            }
            rr = await c.post(f"{BASE}/stock/mouvements", json=mv, headers=H)
            if rr.status_code in (200, 201):
                stock_ok += 1
            else:
                log_fail(f"Stock entrée {p['titre'][:20]}: {rr.status_code} {rr.text[:120]}")
        if stock_ok: log_ok(f"{stock_ok}/{len(prods)} produits approvisionnés (+500 chacun)")

        # Vérifier que le stock a bien augmenté
        r = await c.get(f"{BASE}/produits/{prods[0]['product_id']}", headers=H)
        new_stock = r.json().get("stock_actuel", 0)
        if new_stock >= 500:
            log_ok(f"Stock mis à jour correctement: {prods[0]['titre'][:20]} = {new_stock}")
        else:
            log_fail(f"Stock NON mis à jour: attendu >=500, obtenu {new_stock}")

        # ============== 2. CLIENT — créer une école ==============
        print("\n=== 2. CRÉATION ÉCOLE CLIENTE ===")
        ecole = {
            "nom": "Groupe Scolaire La Colombe " + str(random.randint(1000, 9999)),
            "type_client": "groupe_scolaire",
            "representant": "M. KOUASSI Jean",
            "telephone": "0707080910",
            "email": f"colombe{random.randint(1,9999)}@ecole.ci",
            "adresse": "Cocody Angré 8e tranche",
            "ville": "Abidjan",
            "plafond_credit": 5000000,
            "notes": "École partenaire, commandes trimestrielles",
        }
        r = await c.post(f"{BASE}/clients?force=true", json=ecole, headers=H)
        if r.status_code in (200, 201):
            client = r.json()
            client_id = client["client_id"]
            log_ok(f"École créée: {client['nom']} (ref {client.get('reference')})")
        else:
            log_fail(f"Création école: {r.status_code} {r.text[:150]}")
            return finalize()

        # ============== 3. COMMANDE — passer commande de livres ==============
        print("\n=== 3. COMMANDE DE LIVRES ===")
        lignes = [{"produit_id": p["product_id"], "quantite": random.randint(20, 80), "prix_unitaire": p["prix_vente"]} for p in prods[:3]]
        cmd = {
            "client_id": client_id,
            "lignes": lignes,
            "notes": "Commande rentrée scolaire 2026",
        }
        # Créer DIRECTEMENT en soumission (submit=true) → statut en_attente
        r = await c.post(f"{BASE}/commandes?submit=true", json=cmd, headers=H)
        if r.status_code in (200, 201):
            commande = r.json()
            cmd_id = commande["commande_id"]
            log_ok(f"Commande créée: {commande.get('reference')} — {commande.get('montant_total','?')} FCFA — statut {commande.get('statut')}")
        else:
            log_fail(f"Création commande: {r.status_code} {r.text[:200]}")
            return finalize()

        # ============== 4. WORKFLOW COMMANDE ==============
        print("\n=== 4. WORKFLOW COMMANDE (en_attente → valider → préparer → livrer) ===")
        # NOTE BUG: pas d'endpoint /soumettre — une commande créée en brouillon est bloquée.
        # Test garde-fou: créer un brouillon séparé et tenter de le valider.
        r_b = await c.post(f"{BASE}/commandes", json=cmd, headers=H)
        if r_b.status_code in (200, 201):
            bid = r_b.json()["commande_id"]
            rr = await c.post(f"{BASE}/commandes/{bid}/valider", headers=H)
            if rr.status_code == 400 and "brouillon" in rr.text.lower():
                log_warn("BUG WORKFLOW: brouillon bloqué — message renvoie vers /soumettre QUI N'EXISTE PAS")
            await c.delete(f"{BASE}/commandes/{bid}", headers=H)

        # Valider la commande en_attente proprement
        rr = await c.post(f"{BASE}/commandes/{cmd_id}/valider", headers=H)
        if rr.status_code in (200, 201):
            log_ok(f"Commande validée — statut {rr.json().get('statut')}")
            rr = await c.post(f"{BASE}/commandes/{cmd_id}/preparer", headers=H)
            if rr.status_code in (200, 201):
                log_ok(f"Commande préparée — statut {rr.json().get('statut')}")
                # Livraison via Bon de Livraison (le workflow auto-crée un BL à la préparation)
                rbl = await c.get(f"{BASE}/bons-livraison?commande_id={cmd_id}", headers=H)
                if rbl.status_code == 200:
                    bls = rbl.json() if isinstance(rbl.json(), list) else rbl.json().get("items", [])
                    bls = [b for b in bls if b.get("commande_id") == cmd_id]
                    if bls:
                        bl_id = bls[0].get("bl_id") or bls[0].get("bon_livraison_id")
                        log_ok(f"Bon de livraison auto-créé: {bls[0].get('reference')}")
                        rliv = await c.post(f"{BASE}/bons-livraison/{bl_id}/livrer", headers=H)
                        if rliv.status_code in (200, 201):
                            log_ok("Livraison confirmée via BL")
                        else:
                            log_warn(f"Livrer BL: {rliv.status_code} {rliv.text[:100]}")
                    else:
                        log_warn("Aucun BL trouvé pour la commande")
            else:
                log_warn(f"Préparer: {rr.status_code} {rr.text[:100]}")
        else:
            log_fail(f"Valider: {rr.status_code} {rr.text[:150]}")

        # ============== 5. FACTURE depuis commande ==============
        print("\n=== 5. FACTURATION ===")
        fact_id = None
        # La facture peut être auto-générée pendant le workflow — la retrouver d'abord
        r = await c.get(f"{BASE}/factures?commande_id={cmd_id}", headers=H)
        if r.status_code == 200:
            data = r.json()
            facs = data if isinstance(data, list) else data.get("items", [])
            facs = [f for f in facs if f.get("commande_id") == cmd_id]
            if facs:
                facture = facs[0]
                fact_id = facture.get("facture_id")
                log_ok(f"Facture trouvée (auto): {facture.get('reference')} — {facture.get('montant_ttc', facture.get('montant_total','?'))} FCFA")
        if not fact_id:
            r = await c.post(f"{BASE}/factures/generer-depuis-commande", json={"commande_id": cmd_id}, headers=H)
            if r.status_code in (200, 201):
                facture = r.json()
                fact_id = facture.get("facture_id")
                log_ok(f"Facture générée: {facture.get('reference')} — {facture.get('montant_ttc', facture.get('montant_total','?'))} FCFA")
            else:
                log_warn(f"Génération facture: {r.status_code} {r.text[:150]}")

        # ============== 6. ENCAISSEMENT ==============
        print("\n=== 6. ENCAISSEMENT ===")
        if fact_id:
            r = await c.get(f"{BASE}/factures/{fact_id}", headers=H)
            mt = r.json().get("montant_ttc", r.json().get("montant_total", 0))
            import datetime as _dt
            pay = {
                "client_id": client_id,
                "date_paiement": _dt.date.today().isoformat(),
                "mode_paiement": "especes",
                "montant_total": mt,
                "factures": [{"facture_id": fact_id, "montant_affecte": mt}],
                "notes": "Encaissement simulation rentrée scolaire",
            }
            r = await c.post(f"{BASE}/paiements", json=pay, headers=H)
            if r.status_code in (200, 201):
                log_ok(f"Encaissement enregistré: {mt} FCFA")
            else:
                log_fail(f"Encaissement: {r.status_code} {r.text[:150]}")

        # ============== 7. FOURNISSEUR + APPRO ==============
        print("\n=== 7. FOURNISSEUR & APPRO ===")
        fourn = {"nom": "Imprimerie ROTOPRINT " + str(random.randint(100, 999)), "telephone": "0102030405", "email": "rotoprint@fourn.ci", "adresse": "Zone 4"}
        r = await c.post(f"{BASE}/fournisseurs", json=fourn, headers=H)
        if r.status_code in (200, 201):
            log_ok(f"Fournisseur créé: {fourn['nom']}")
        else:
            log_warn(f"Fournisseur: {r.status_code} {r.text[:120]}")

        # ============== 8. FLOTTE — véhicule + chauffeur ==============
        print("\n=== 8. FLOTTE & CHAUFFEURS ===")
        veh = {
            "reference": f"VEH-{random.randint(1000,9999)}",
            "immatriculation": f"{random.randint(1000,9999)}-CI-0{random.randint(1,9)}",
            "marque": "Toyota",
            "modele": "Hiace",
            "type": "fourgonnette",
            "annee": 2022,
            "capacite_kg": 1500,
            "capacite_m3": 12,
            "kilometrage": 45000,
            "statut": "disponible",
        }
        r = await c.post(f"{BASE}/fleet/vehicules", json=veh, headers=H)
        if r.status_code in (200, 201):
            log_ok(f"Véhicule ajouté: {veh['immatriculation']} {veh['marque']} {veh['modele']}")
        else:
            log_warn(f"Véhicule: {r.status_code} {r.text[:150]}")

        # ============== 9. COMPTABILITÉ ==============
        print("\n=== 9. COMPTABILITÉ ===")
        r = await c.get(f"{BASE}/comptabilite-avancee/journaux", headers=H)
        if r.status_code == 200 and len(r.json()) > 0:
            log_ok(f"Journaux comptables: {len(r.json())} disponibles")
        else:
            log_fail(f"Journaux: {r.status_code} {str(r.text)[:100]}")
        r = await c.get(f"{BASE}/comptabilite-avancee/plan-comptable", headers=H)
        if r.status_code == 200 and len(r.json()) > 0:
            log_ok(f"Plan comptable: {len(r.json())} comptes")
        else:
            log_warn(f"Plan comptable: {r.status_code}")
        # Génération auto écriture depuis facture
        if fact_id:
            r = await c.post(f"{BASE}/comptabilite-avancee/ecritures/auto/facture/{fact_id}", headers=H)
            if r.status_code in (200, 201):
                log_ok("Écriture comptable auto générée depuis facture")
            else:
                log_warn(f"Écriture auto facture: {r.status_code} {r.text[:120]}")
        r = await c.get(f"{BASE}/comptabilite/balance", headers=H)
        if r.status_code == 200:
            log_ok("Balance comptable accessible")
        else:
            log_warn(f"Balance: {r.status_code}")

        # ============== 10. RH ==============
        print("\n=== 10. RH ===")
        r = await c.get(f"{BASE}/rh/employes", headers=H)
        if r.status_code == 200:
            emps = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
            log_ok(f"Module RH employés accessible ({len(emps)} employés)")
        else:
            log_warn(f"RH employés: {r.status_code}")
        r = await c.get(f"{BASE}/rh/dashboard", headers=H)
        log_ok("RH dashboard OK") if r.status_code == 200 else log_warn(f"RH dashboard: {r.status_code}")

        # ============== 11. BACKUP & SÉCURITÉ ==============
        print("\n=== 11. BACKUP & SÉCURITÉ ===")
        r = await c.get(f"{BASE}/backup/backups", headers=H)
        log_ok("Module backup accessible") if r.status_code == 200 else log_warn(f"Backup: {r.status_code}")
        r = await c.get(f"{BASE}/auth/2fa/status", headers=H)
        log_ok("2FA status accessible") if r.status_code == 200 else log_warn(f"2FA: {r.status_code}")

        # ============== 12. DASHBOARD & BI ==============
        print("\n=== 12. DASHBOARDS & BI ===")
        for ep, lbl in [("/dashboard/stats", "Dashboard principal"), ("/bi-analytics/dashboard", "BI dashboard"), ("/analytics/dashboard", "Analytics")]:
            r = await c.get(f"{BASE}{ep}", headers=H)
            log_ok(f"{lbl} OK") if r.status_code == 200 else log_warn(f"{lbl}: {r.status_code} {r.text[:80]}")

    finalize()


def finalize():
    print("\n" + "=" * 50)
    print(f"RÉSULTATS: {len(RESULTS['ok'])} OK | {len(RESULTS['warn'])} WARN | {len(RESULTS['fail'])} FAIL")
    if RESULTS["fail"]:
        print("\nÉCHECS:")
        for f in RESULTS["fail"]: print("  ❌", f)
    if RESULTS["warn"]:
        print("\nAVERTISSEMENTS:")
        for w in RESULTS["warn"]: print("  ⚠️ ", w)
    json.dump(RESULTS, open("/tmp/sim_results.json", "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
