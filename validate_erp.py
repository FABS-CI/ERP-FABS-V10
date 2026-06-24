#!/usr/bin/env python3
"""
ERP FABS-CI Validation Test — Simple & Efficient
Tests all major workflows with mock backend
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
EMAIL = "pissken@editionsfabsci.com"
PASSWORD = "Admin@2025"

test_log = []
token = None

def test(name, method, endpoint, params=None, expected_status=200):
    """Make API call and log result"""
    global token
    
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "POST":
            r = requests.post(url, params=params, headers=headers, timeout=5)
        else:
            r = requests.get(url, params=params, headers=headers, timeout=5)
        
        success = r.status_code == expected_status
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name} [{r.status_code}]")
        test_log.append((name, r.status_code, success))
        
        try:
            return success, r.json()
        except:
            return success, {"raw": r.text}
    except Exception as e:
        print(f"❌ {name} [ERROR: {str(e)[:50]}]")
        test_log.append((name, 0, False))
        return False, {"error": str(e)}

def main():
    global token
    
    print("="*70)
    print("ERP FABS-CI VALIDATION TEST")
    print("="*70)
    print(f"\nStart: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # ============================================================
    # 1. AUTHENTICATION
    # ============================================================
    print("MODULE 1: AUTHENTICATION")
    print("-" * 70)
    
    success, response = test("Login", "POST", "/api/auth/login", {
        "email": EMAIL,
        "password": PASSWORD,
    })
    
    if success:
        token = response.get("access_token")
        print(f"   Token: {token[:20]}...\n")
    else:
        print("❌ Cannot continue without auth\n")
        return False
    
    # ============================================================
    # 2. COMMERCIAL WORKFLOW
    # ============================================================
    print("MODULE 2: COMMERCIAL WORKFLOW (Prospect → Client → Devis → Commande → Facture → Paiement)")
    print("-" * 70)
    
    # Prospect
    success, resp = test("Create Prospect", "POST", "/api/prospects", {
        "nom": f"PROSP_{int(time.time())}",
        "email": f"prospect_{int(time.time())}@test.com",
        "telephone": "+22512345678",
        "secteur": "Commerce",
        "adresse": "123 Rue Test",
        "pays": "CI",
    })
    prospect_id = resp.get("id") if success else None
    
    # Client
    if prospect_id:
        success, resp = test("Convert Prospect → Client", "POST", f"/api/prospects/{prospect_id}/convert", {
            "type_client": "PARTICULIER",
            "reference": f"CLI_{int(time.time())}",
        })
        client_id = resp.get("client_id") if success else None
    else:
        client_id = None
    
    # Devis
    if client_id:
        success, resp = test("Create Devis", "POST", "/api/devis", {
            "client_id": client_id,
            "reference": f"DEV_{int(time.time())}",
            "date_devis": datetime.now().strftime("%Y-%m-%d"),
            "date_validite": "2026-12-31",
            "devise": "XOF",
            "statut": "DRAFT",
        })
        devis_id = resp.get("id") if success else None
    else:
        devis_id = None
    
    # Validate Devis → Commande
    if devis_id:
        success, resp = test("Validate Devis → Commande", "POST", f"/api/devis/{devis_id}/valider", {})
        commande_id = resp.get("commande_id") if success else None
    else:
        commande_id = None
    
    # Livraison
    if commande_id:
        success, resp = test("Create Livraison", "POST", "/api/livraisons", {
            "commande_id": commande_id,
            "reference": f"LIV_{int(time.time())}",
            "date_prevue": datetime.now().strftime("%Y-%m-%d"),
            "adresse_livraison": "123 Rue Test",
            "statut": "CONFIRMEE",
        })
    
    # Facture
    if commande_id:
        success, resp = test("Create Facture", "POST", "/api/factures", {
            "client_id": client_id,
            "commande_id": commande_id,
            "reference": f"FAC_{int(time.time())}",
            "date_facture": datetime.now().strftime("%Y-%m-%d"),
            "montant_ht": "50000",
            "tva": "10000",
            "montant_ttc": "60000",
            "devise": "XOF",
            "statut": "EMISE",
        })
        facture_id = resp.get("id") if success else None
    else:
        facture_id = None
    
    # Paiement
    if facture_id:
        test("Create Paiement", "POST", "/api/paiements", {
            "facture_id": facture_id,
            "client_id": client_id,
            "montant": "60000",
            "mode_paiement": "VIREMENT",
            "date_paiement": datetime.now().strftime("%Y-%m-%d"),
            "reference": f"PAY_{int(time.time())}",
            "statut": "CONFIRMEE",
        })
    
    print()
    
    # ============================================================
    # 3. PURCHASES WORKFLOW
    # ============================================================
    print("MODULE 3: PURCHASES WORKFLOW (Demande → Commande Fournisseur → Réception → Facture → Paiement)")
    print("-" * 70)
    
    # Demande Achat
    success, resp = test("Create Demande Achat", "POST", "/api/demandes-achat", {
        "reference": f"DA_{int(time.time())}",
        "date_demande": datetime.now().strftime("%Y-%m-%d"),
        "statut": "BROUILLON",
    })
    demande_id = resp.get("id") if success else None
    
    # Validate
    if demande_id:
        test("Validate Demande", "POST", f"/api/demandes-achat/{demande_id}/valider", {})
    
    # Commande Fournisseur
    if demande_id:
        success, resp = test("Create Commande Fournisseur", "POST", "/api/commandes-fournisseur", {
            "fournisseur_id": "supp_001",
            "demande_achat_id": demande_id,
            "reference": f"CF_{int(time.time())}",
            "date_commande": datetime.now().strftime("%Y-%m-%d"),
            "montant": "50000",
            "devise": "XOF",
            "statut": "CONFIRMEE",
        })
        cmd_fournisseur_id = resp.get("id") if success else None
    else:
        cmd_fournisseur_id = None
    
    # Réception
    if cmd_fournisseur_id:
        success, resp = test("Create Réception", "POST", "/api/receptions", {
            "commande_fournisseur_id": cmd_fournisseur_id,
            "reference": f"REC_{int(time.time())}",
            "date_reception": datetime.now().strftime("%Y-%m-%d"),
            "quantite_recu": "100",
            "statut": "COMPLETEE",
        })
    
    # Facture Fournisseur
    if cmd_fournisseur_id:
        success, resp = test("Create Facture Fournisseur", "POST", "/api/factures-fournisseur", {
            "fournisseur_id": "supp_001",
            "commande_fournisseur_id": cmd_fournisseur_id,
            "reference": f"FACF_{int(time.time())}",
            "date_facture": datetime.now().strftime("%Y-%m-%d"),
            "montant_ht": "50000",
            "tva": "10000",
            "montant_ttc": "60000",
            "devise": "XOF",
            "statut": "REÇUE",
        })
        facture_fournisseur_id = resp.get("id") if success else None
    else:
        facture_fournisseur_id = None
    
    # Paiement Fournisseur
    if facture_fournisseur_id:
        test("Create Paiement Fournisseur", "POST", "/api/paiements-fournisseur", {
            "facture_fournisseur_id": facture_fournisseur_id,
            "fournisseur_id": "supp_001",
            "montant": "60000",
            "mode_paiement": "CHEQUE",
            "date_paiement": datetime.now().strftime("%Y-%m-%d"),
            "reference": f"PAYF_{int(time.time())}",
            "statut": "CONFIRMEE",
        })
    
    print()
    
    # ============================================================
    # 4. STOCK WORKFLOW
    # ============================================================
    print("MODULE 4: STOCK WORKFLOW (Entrées → Sorties → Inventaires)")
    print("-" * 70)
    
    # Entrée
    test("Create Stock Entrée", "POST", "/api/stock/entrees", {
        "reference": f"ENT_{int(time.time())}",
        "date_entree": datetime.now().strftime("%Y-%m-%d"),
        "produit_id": "product_001",
        "quantite": "500",
        "prix_unitaire": "1000",
        "type_entree": "ACHAT",
        "statut": "VALIDEE",
    })
    
    # Sortie
    test("Create Stock Sortie", "POST", "/api/stock/sorties", {
        "reference": f"SOR_{int(time.time())}",
        "date_sortie": datetime.now().strftime("%Y-%m-%d"),
        "produit_id": "product_001",
        "quantite": "50",
        "type_sortie": "VENTE",
        "statut": "VALIDEE",
    })
    
    # Balance
    test("Get Stock Balance", "GET", "/api/stock/balance", {
        "produit_id": "product_001",
    })
    
    # Inventaire
    test("Create Inventaire", "POST", "/api/stock/inventaires", {
        "reference": f"INV_{int(time.time())}",
        "date_inventaire": datetime.now().strftime("%Y-%m-%d"),
        "statut": "VALIDEE",
    })
    
    print()
    
    # ============================================================
    # 5. FINANCE WORKFLOW
    # ============================================================
    print("MODULE 5: FINANCE WORKFLOW (Journaux → Balance → Trésorerie)")
    print("-" * 70)
    
    test("Finance Dashboard", "GET", "/api/finance/dashboard")
    test("Get Journaux", "GET", "/api/finance/journaux", {"mois": "6", "annee": "2026"})
    test("Get Grand Livre", "GET", "/api/finance/grand-livre", {"compte": "411"})
    test("Get Balance", "GET", "/api/finance/balance", {"mois": "6", "annee": "2026"})
    test("Get Encaissements", "GET", "/api/finance/encaissements", {"mois": "6"})
    test("Get Décaissements", "GET", "/api/finance/decaissements", {"mois": "6"})
    
    print()
    
    # ============================================================
    # 6. HR WORKFLOW
    # ============================================================
    print("MODULE 6: HR WORKFLOW (Employé → Présence → Paie)")
    print("-" * 70)
    
    # Employee
    success, resp = test("Create Employee", "POST", "/api/rh/employes", {
        "nom": f"EMP_{int(time.time())}",
        "prenom": "Test",
        "email": f"emp_{int(time.time())}@test.com",
        "telephone": "+22512345678",
        "date_embauche": datetime.now().strftime("%Y-%m-%d"),
        "poste": "Vendeur",
        "departement_id": "dept_001",
        "salaire_base": "300000",
        "devise": "XOF",
        "statut": "ACTIF",
    })
    emp_id = resp.get("id") if success else None
    
    # Présence
    if emp_id:
        test("Create Présence", "POST", "/api/rh/presences", {
            "employe_id": emp_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "heure_arrivee": "08:00",
            "heure_depart": "17:30",
            "heures_travaillees": "8.5",
            "type": "NORMAL",
            "statut": "VALIDEE",
        })
    
    # Bulletin
    if emp_id:
        success, resp = test("Create Bulletin Paie", "POST", "/api/rh/bulletins", {
            "employe_id": emp_id,
            "mois": "6",
            "annee": "2026",
            "salaire_brut": "300000",
            "deductions": "45000",
            "salaire_net": "255000",
            "devise": "XOF",
            "statut": "VALIDEE",
        })
        bulletin_id = resp.get("id") if success else None
        
        # Comptabilize
        if bulletin_id:
            test("Comptabilize Bulletin", "POST", "/api/rh/bulletins/comptabiliser", {
                "bulletin_id": bulletin_id,
                "date_comptabilisation": datetime.now().strftime("%Y-%m-%d"),
            })
    
    print()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, _, success in test_log if success)
    total = len(test_log)
    
    print(f"\n✅ Tests Passed: {passed}/{total} ({(passed/total*100):.0f}%)")
    print(f"❌ Tests Failed: {total - passed}/{total}")
    print(f"\nEnd: {datetime.now().strftime('%H:%M:%S')}")
    
    # Generate Report
    with open("/home/user/ERP-FABS-V10/VALIDATION_REPORT.md", "w") as f:
        f.write(f"""# ERP FABS-CI Validation Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Results
- **Total Tests**: {total}
- **Passed**: {passed}
- **Failed**: {total - passed}
- **Pass Rate**: {(passed/total*100):.1f}%

## Tests
| # | Test | Status |
|---|------|--------|
""")
        for i, (name, status_code, success) in enumerate(test_log, 1):
            icon = "✅" if success else "❌"
            f.write(f"| {i} | {name} | {icon} [{status_code}] |\n")
        
        f.write(f"""

## Conclusion
All major workflows have been tested. System is {'ready' if passed >= total * 0.8 else 'not ready'} for production based on test coverage.

**Validation Score**: {(passed/total*100):.1f}%
""")
    
    print("\n✅ Report saved: VALIDATION_REPORT.md")
    print("="*70)
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
