#!/usr/bin/env python3
"""
AUDIT FINAL DE CERTIFICATION ERP FABS-CI v3
Avec VRAIS endpoints de l'API (validés contre /openapi.json)
"""

import sys, json, requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/audit_final_v3.log'), logging.StreamHandler()]
)
log = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
REPORT_FILE = "/home/user/ERP-FABS-V10/RAPPORT_CERTIFICATION_FINAL.md"

TOKENS = {}
USERS = {}
AUDIT_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "scenarios": {},
    "rbac": {},
    "conformite_globale": 0.0,
    "modules_valides": [],
    "modules_invalides": [],
    "niveau_risque": "CRITIQUE"
}

# ============================================================================
# HELPERS
# ============================================================================
def req(method, endpoint, token=None, data=None, desc=""):
    """HTTP request with auto-logging"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=10)
        
        ok = resp.status_code < 400
        status_emoji = "✅" if ok else "❌"
        log.info(f"{status_emoji} {method:6} {endpoint:50} → {resp.status_code:3} | {desc}")
        
        return {"ok": ok, "status": resp.status_code, "data": resp.json() if resp.text else None}
    except Exception as e:
        log.error(f"❌ {method:6} {endpoint:50} → ERROR: {str(e)}")
        return {"ok": False, "status": 0, "data": None, "error": str(e)}

def get_id(obj):
    """Extract ID from response"""
    if not obj:
        return None
    return obj.get("_id") or obj.get("id") or obj.get("user_id") or obj.get("commande_id")

# ============================================================================
# SETUP USERS
# ============================================================================
def setup_users():
    """Create 5 test users"""
    log.info("\n" + "="*80)
    log.info("PHASE 1 : CRÉATION UTILISATEURS")
    log.info("="*80)
    
    roles = [
        {"email": "dir@fabs.ci", "role": "directeur_general"},
        {"email": "com@fabs.ci", "role": "directeur_commercial"},
        {"email": "cpt@fabs.ci", "role": "comptable"},
        {"email": "mag@fabs.ci", "role": "gestionnaire_stock"},
        {"email": "ass@fabs.ci", "role": "assistante"}
    ]
    
    # Login admin
    admin_resp = req("POST", "/api/auth/login", data={
        "email": "pissken@editionsfabsci.com",
        "password": "Admin@2025"
    }, desc="Login admin")
    
    if not admin_resp["ok"]:
        return False
    
    admin_token = admin_resp["data"]["access_token"]
    TOKENS["admin"] = admin_token
    
    # Create roles
    for role_info in roles:
        req("POST", "/api/utilisateurs",
            token=admin_token,
            data={
                "email": role_info["email"],
                "password": "Test@2025",
                "nom_complet": f"User {role_info['role']}",
                "role": role_info["role"]
            },
            desc=f"Create {role_info['role']}")
        
        login_resp = req("POST", "/api/auth/login", data={
            "email": role_info["email"],
            "password": "Test@2025"
        }, desc=f"Login {role_info['role']}")
        
        if login_resp["ok"]:
            TOKENS[role_info["role"]] = login_resp["data"]["access_token"]
    
    log.info(f"✅ {len(TOKENS)} tokens acquired")
    return True

# ============================================================================
# SCENARIO 1: VENTE COMPLÈTE
# ============================================================================
def scenario_1():
    """Prospect→Client→Devis→Commande→Validation→BL→Facture→Paiement"""
    log.info("\n" + "="*80)
    log.info("SCÉNARIO 1 : VENTE COMPLÈTE")
    log.info("="*80)
    
    scenario = {"nom": "Vente Complète", "etapes": []}
    token_com = TOKENS.get("directeur_commercial")
    token_cpt = TOKENS.get("comptable")
    token_mag = TOKENS.get("gestionnaire_stock")
    
    # 1. Create client
    log.info("\n→ Créer client")
    c_resp = req("POST", "/api/clients",
        token=token_com,
        data={
            "nom": f"Client Vente {datetime.now().timestamp()}",
            "type_client": "librairie",
            "representant": "Test",
            "telephone": "0701234567",
            "email": f"vente{datetime.now().timestamp()}@fabs.ci"
        },
        desc="Create client")
    
    if not c_resp["ok"]:
        scenario["etapes"].append({"etape": "Client", "ok": False})
        AUDIT_RESULTS["scenarios"]["s1"] = scenario
        return False
    
    client_id = get_id(c_resp["data"])
    scenario["etapes"].append({"etape": "Client créé", "ok": True})
    
    # 2. Create commande
    log.info("\n→ Créer commande")
    cmd_resp = req("POST", "/api/commandes",
        token=token_com,
        data={
            "client_id": client_id,
            "lignes": [{"produit_id": "prod_001", "quantite": 10, "prix_unitaire": 5000}],
            "date_commande": datetime.now().isoformat()
        },
        desc="Create commande")
    
    if not cmd_resp["ok"]:
        scenario["etapes"].append({"etape": "Commande", "ok": False})
        AUDIT_RESULTS["scenarios"]["s1"] = scenario
        return False
    
    commande_id = get_id(cmd_resp["data"])
    scenario["etapes"].append({"etape": "Commande créée", "ok": True})
    
    # 3. Valider commande
    log.info("\n→ Valider commande")
    val_resp = req("POST", f"/api/commandes/{commande_id}/valider",
        token=token_com,
        data={},
        desc="Valider commande")
    
    scenario["etapes"].append({"etape": "Commande validée", "ok": val_resp["ok"]})
    
    # 4. Create BL
    log.info("\n→ Créer bon de livraison")
    bl_resp = req("POST", "/api/bons-livraison",
        token=token_mag,
        data={
            "commande_id": commande_id,
            "date_livraison": datetime.now().isoformat(),
            "lignes": [{"produit_id": "prod_001", "quantite_livree": 10}]
        },
        desc="Create BL")
    
    if not bl_resp["ok"]:
        scenario["etapes"].append({"etape": "BL", "ok": False})
        AUDIT_RESULTS["scenarios"]["s1"] = scenario
        return False
    
    bl_id = get_id(bl_resp["data"])
    scenario["etapes"].append({"etape": "BL créé", "ok": True})
    
    # 5. Create facture
    log.info("\n→ Créer facture")
    fac_resp = req("POST", "/api/factures",
        token=token_cpt,
        data={
            "commande_id": commande_id,
            "bl_id": bl_id,
            "date_facture": datetime.now().isoformat()
        },
        desc="Create facture")
    
    if not fac_resp["ok"]:
        scenario["etapes"].append({"etape": "Facture", "ok": False})
        AUDIT_RESULTS["scenarios"]["s1"] = scenario
        return False
    
    facture_id = get_id(fac_resp["data"])
    scenario["etapes"].append({"etape": "Facture créée", "ok": True})
    
    # 6. Paiement
    log.info("\n→ Enregistrer paiement")
    pay_resp = req("POST", "/api/paiements",
        token=token_cpt,
        data={
            "facture_id": facture_id,
            "montant": 50000,
            "date_paiement": datetime.now().isoformat(),
            "mode": "VIREMENT"
        },
        desc="Create paiement")
    
    scenario["etapes"].append({"etape": "Paiement enregistré", "ok": pay_resp["ok"]})
    
    AUDIT_RESULTS["scenarios"]["s1"] = scenario
    return True

# ============================================================================
# SCENARIO 2: LIVRAISON PARTIELLE
# ============================================================================
def scenario_2():
    """Commande 100 → Livraison 50 → Facturation 50 → Paiement partiel → Reliquat"""
    log.info("\n" + "="*80)
    log.info("SCÉNARIO 2 : LIVRAISON PARTIELLE")
    log.info("="*80)
    
    scenario = {"nom": "Livraison Partielle", "etapes": []}
    token_com = TOKENS.get("directeur_commercial")
    token_mag = TOKENS.get("gestionnaire_stock")
    token_cpt = TOKENS.get("comptable")
    
    # Create client
    c_resp = req("POST", "/api/clients",
        token=token_com,
        data={
            "nom": f"Client Partiel {datetime.now().timestamp()}",
            "type_client": "ecole",
            "representant": "Dir Partiel",
            "telephone": "0702345678",
            "email": f"partiel{datetime.now().timestamp()}@fabs.ci"
        },
        desc="Create client (s2)")
    
    if not c_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s2"] = scenario
        return False
    
    client_id = get_id(c_resp["data"])
    
    # Commande 100
    log.info("\n→ Commande 100 unités")
    cmd_resp = req("POST", "/api/commandes",
        token=token_com,
        data={
            "client_id": client_id,
            "lignes": [{"produit_id": "prod_001", "quantite": 100, "prix_unitaire": 5000}],
            "date_commande": datetime.now().isoformat()
        },
        desc="Create commande 100")
    
    if not cmd_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s2"] = scenario
        return False
    
    commande_id = get_id(cmd_resp["data"])
    scenario["etapes"].append({"etape": "Commande 100 unités", "ok": True})
    
    # Valider
    req("POST", f"/api/commandes/{commande_id}/valider",
        token=token_com, data={}, desc="Validate")
    
    # Livraison 50
    log.info("\n→ Livraison 50 unités")
    bl1_resp = req("POST", "/api/bons-livraison",
        token=token_mag,
        data={
            "commande_id": commande_id,
            "date_livraison": datetime.now().isoformat(),
            "lignes": [{"produit_id": "prod_001", "quantite_livree": 50}]
        },
        desc="BL 50")
    
    scenario["etapes"].append({"etape": "Livraison 50", "ok": bl1_resp["ok"]})
    
    if bl1_resp["ok"]:
        bl1_id = get_id(bl1_resp["data"])
        
        # Facture 50
        fac1_resp = req("POST", "/api/factures",
            token=token_cpt,
            data={"commande_id": commande_id, "bl_id": bl1_id, "date_facture": datetime.now().isoformat()},
            desc="Facture 50")
        
        if fac1_resp["ok"]:
            fac1_id = get_id(fac1_resp["data"])
            
            # Paiement partiel
            pay1_resp = req("POST", "/api/paiements",
                token=token_cpt,
                data={
                    "facture_id": fac1_id,
                    "montant": 125000,
                    "date_paiement": datetime.now().isoformat(),
                    "mode": "CHEQUE"
                },
                desc="Paiement partiel")
            
            scenario["etapes"].append({"etape": "Paiement partiel", "ok": pay1_resp["ok"]})
    
    # Livraison reliquat
    log.info("\n→ Livraison reliquat 50")
    bl2_resp = req("POST", "/api/bons-livraison",
        token=token_mag,
        data={
            "commande_id": commande_id,
            "date_livraison": (datetime.now() + timedelta(days=5)).isoformat(),
            "lignes": [{"produit_id": "prod_001", "quantite_livree": 50}]
        },
        desc="BL reliquat")
    
    scenario["etapes"].append({"etape": "Livraison reliquat", "ok": bl2_resp["ok"]})
    
    AUDIT_RESULTS["scenarios"]["s2"] = scenario
    return True

# ============================================================================
# SCENARIO 3: AVOIR CLIENT
# ============================================================================
def scenario_3():
    """Facture→Retour→Avoir"""
    log.info("\n" + "="*80)
    log.info("SCÉNARIO 3 : AVOIR CLIENT")
    log.info("="*80)
    
    scenario = {"nom": "Avoir Client", "etapes": []}
    token_com = TOKENS.get("directeur_commercial")
    token_mag = TOKENS.get("gestionnaire_stock")
    token_cpt = TOKENS.get("comptable")
    
    # Create client
    c_resp = req("POST", "/api/clients",
        token=token_com,
        data={
            "nom": f"Client Avoir {datetime.now().timestamp()}",
            "type_client": "particulier",
            "representant": "Mr Avoir",
            "telephone": "0703456789",
            "email": f"avoir{datetime.now().timestamp()}@fabs.ci"
        },
        desc="Create client (s3)")
    
    if not c_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s3"] = scenario
        return False
    
    client_id = get_id(c_resp["data"])
    
    # Commande → BL → Facture
    cmd_resp = req("POST", "/api/commandes",
        token=token_com,
        data={
            "client_id": client_id,
            "lignes": [{"produit_id": "prod_002", "quantite": 20, "prix_unitaire": 10000}],
            "date_commande": datetime.now().isoformat()
        },
        desc="Create commande (s3)")
    
    if not cmd_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s3"] = scenario
        return False
    
    commande_id = get_id(cmd_resp["data"])
    req("POST", f"/api/commandes/{commande_id}/valider",
        token=token_com, data={}, desc="Validate")
    
    # BL
    bl_resp = req("POST", "/api/bons-livraison",
        token=token_mag,
        data={
            "commande_id": commande_id,
            "date_livraison": datetime.now().isoformat(),
            "lignes": [{"produit_id": "prod_002", "quantite_livree": 20}]
        },
        desc="BL (s3)")
    
    if not bl_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s3"] = scenario
        return False
    
    bl_id = get_id(bl_resp["data"])
    
    # Facture
    fac_resp = req("POST", "/api/factures",
        token=token_cpt,
        data={"commande_id": commande_id, "bl_id": bl_id, "date_facture": datetime.now().isoformat()},
        desc="Facture (s3)")
    
    if not fac_resp["ok"]:
        AUDIT_RESULTS["scenarios"]["s3"] = scenario
        return False
    
    facture_id = get_id(fac_resp["data"])
    scenario["etapes"].append({"etape": "Facture créée", "ok": True})
    
    # Avoir
    log.info("\n→ Créer avoir")
    avoir_resp = req("POST", "/api/factures/generer-avoir",
        token=token_cpt,
        data={
            "facture_id": facture_id,
            "motif": "Retour marchandise",
            "lignes": [{"produit_id": "prod_002", "quantite": 5, "prix_unitaire": 10000}],
            "date_avoir": datetime.now().isoformat()
        },
        desc="Create avoir")
    
    scenario["etapes"].append({"etape": "Avoir créé", "ok": avoir_resp["ok"]})
    
    AUDIT_RESULTS["scenarios"]["s3"] = scenario
    return True

# ============================================================================
# SCENARIO 4: INVENTAIRE
# ============================================================================
def scenario_4():
    """Créer inventaire→Constater écarts→Valider→Régulariser"""
    log.info("\n" + "="*80)
    log.info("SCÉNARIO 4 : INVENTAIRE")
    log.info("="*80)
    
    scenario = {"nom": "Inventaire", "etapes": []}
    token_mag = TOKENS.get("gestionnaire_stock")
    
    # Create inventaire
    log.info("\n→ Créer inventaire")
    inv_resp = req("POST", "/api/stock/inventaire",
        token=token_mag,
        data={
            "date_inventaire": datetime.now().isoformat(),
            "observations": "Audit certification"
        },
        desc="Create inventaire")
    
    if not inv_resp["ok"]:
        scenario["etapes"].append({"etape": "Inventaire", "ok": False})
        AUDIT_RESULTS["scenarios"]["s4"] = scenario
        return False
    
    inventaire_id = get_id(inv_resp["data"])
    scenario["etapes"].append({"etape": "Inventaire créé", "ok": True})
    
    # Regulariser (ajustement)
    log.info("\n→ Régulariser inventaire")
    reg_resp = req("POST", f"/api/stock/inventaire/{inventaire_id}/regulariser",
        token=token_mag,
        data={
            "lignes": [
                {"produit_id": "prod_001", "quantite_physique": 98, "quantite_theorique": 100},
                {"produit_id": "prod_002", "quantite_physique": 205, "quantite_theorique": 200}
            ]
        },
        desc="Regulariser inventaire")
    
    scenario["etapes"].append({"etape": "Inventaire régularisé", "ok": reg_resp["ok"]})
    
    AUDIT_RESULTS["scenarios"]["s4"] = scenario
    return True

# ============================================================================
# SCENARIO 5: FOURNISSEURS
# ============================================================================
def scenario_5():
    """Fournisseur→Approvisionnement"""
    log.info("\n" + "="*80)
    log.info("SCÉNARIO 5 : FOURNISSEURS & APPROVISIONNEMENT")
    log.info("="*80)
    
    scenario = {"nom": "Achat Fournisseur", "etapes": []}
    token_mag = TOKENS.get("gestionnaire_stock")
    token_cpt = TOKENS.get("comptable")
    
    # Create fournisseur
    log.info("\n→ Créer fournisseur")
    fourn_resp = req("POST", "/api/fournisseurs",
        token=token_mag,
        data={
            "nom": f"Fournisseur Audit {datetime.now().timestamp()}",
            "contact": "Monsieur Fourni",
            "adresse": "Ghana",
            "telephone": "0704567890",
            "email": f"fourn{datetime.now().timestamp()}@fabs.ci",
            "conditions_paiement": "NET 30"
        },
        desc="Create fournisseur")
    
    if not fourn_resp["ok"]:
        scenario["etapes"].append({"etape": "Fournisseur", "ok": False})
        AUDIT_RESULTS["scenarios"]["s5"] = scenario
        return False
    
    fournisseur_id = get_id(fourn_resp["data"])
    scenario["etapes"].append({"etape": "Fournisseur créé", "ok": True})
    
    # Approvisionnement
    log.info("\n→ Créer approvisionnement")
    approv_resp = req("POST", "/api/approvisionnements",
        token=token_mag,
        data={
            "fournisseur_id": fournisseur_id,
            "lignes": [{"produit_id": "prod_001", "quantite": 50, "prix_unitaire": 3000}],
            "date_commande": datetime.now().isoformat()
        },
        desc="Create approvisionnement")
    
    if not approv_resp["ok"]:
        scenario["etapes"].append({"etape": "Approvisionnement", "ok": False})
        AUDIT_RESULTS["scenarios"]["s5"] = scenario
        return False
    
    approv_id = get_id(approv_resp["data"])
    scenario["etapes"].append({"etape": "Approvisionnement créé", "ok": True})
    
    # Valider approvisionnement
    log.info("\n→ Valider approvisionnement")
    val_resp = req("POST", f"/api/approvisionnements/{approv_id}/valider",
        token=token_mag,
        data={},
        desc="Valider approvisionnement")
    
    scenario["etapes"].append({"etape": "Approvisionnement validé", "ok": val_resp["ok"]})
    
    AUDIT_RESULTS["scenarios"]["s5"] = scenario
    return True

# ============================================================================
# RBAC TEST
# ============================================================================
def test_rbac():
    """Test access control"""
    log.info("\n" + "="*80)
    log.info("PHASE : TEST RBAC")
    log.info("="*80)
    
    tests = {
        "admin": [("/api/utilisateurs", "GET"), ("/api/parametres", "GET")],
        "directeur_general": [("/api/clients", "GET"), ("/api/commandes", "GET")],
        "directeur_commercial": [("/api/clients", "GET"), ("/api/commandes", "POST")],
        "comptable": [("/api/factures", "GET"), ("/api/paiements", "GET")],
        "gestionnaire_stock": [("/api/stock", "GET"), ("/api/bons-livraison", "GET")],
        "assistante": [("/api/clients", "GET"), ("/api/commandes", "GET")]
    }
    
    rbac = {}
    for role, endpoints in tests.items():
        token = TOKENS.get(role)
        if not token:
            continue
        
        passed = 0
        for endpoint, method in endpoints:
            resp = req(method, endpoint, token=token, desc=f"{role}: {method} {endpoint}")
            if resp["ok"]:
                passed += 1
        
        score = (passed / len(endpoints) * 100) if endpoints else 0
        rbac[role] = {"score": score, "tests": len(endpoints), "passed": passed}
    
    AUDIT_RESULTS["rbac"] = rbac
    return True

# ============================================================================
# CALCULATE & REPORT
# ============================================================================
def calculate_conformity():
    """Calculate global score"""
    scenarios = AUDIT_RESULTS.get("scenarios", {})
    total = 0
    ok = 0
    
    for scenario in scenarios.values():
        for etape in scenario.get("etapes", []):
            total += 1
            if etape.get("ok"):
                ok += 1
    
    rbac = AUDIT_RESULTS.get("rbac", {})
    rbac_scores = [t.get("score", 0) for t in rbac.values()]
    rbac_avg = sum(rbac_scores) / len(rbac_scores) if rbac_scores else 0
    
    conform = (ok / total * 100 if total > 0 else 0)
    global_score = (conform + rbac_avg) / 2
    
    AUDIT_RESULTS["conformite_globale"] = global_score
    AUDIT_RESULTS["etapes_ok"] = ok
    AUDIT_RESULTS["etapes_total"] = total
    
    if global_score >= 90:
        AUDIT_RESULTS["niveau_risque"] = "FAIBLE"
        AUDIT_RESULTS["certification"] = "🟢 CONFORME"
    elif global_score >= 80:
        AUDIT_RESULTS["niveau_risque"] = "MODÉRÉ"
        AUDIT_RESULTS["certification"] = "🟡 CONFORME AVEC RÉSERVE"
    elif global_score >= 70:
        AUDIT_RESULTS["niveau_risque"] = "ÉLEVÉ"
        AUDIT_RESULTS["certification"] = "🟡 CONFORME AVEC RÉSERVE"
    else:
        AUDIT_RESULTS["niveau_risque"] = "CRITIQUE"
        AUDIT_RESULTS["certification"] = "🔴 NON CONFORME"

def generate_report():
    """Generate final report"""
    calculate_conformity()
    
    report = f"""# 🔐 AUDIT FINAL DE CERTIFICATION - ERP FABS-CI
## Éditions FABS-CI - ERP V10

**Date:** {AUDIT_RESULTS['timestamp']}
**Environnement:** Production (fabsci_erp)

---

## 📊 RÉSUMÉ EXÉCUTIF

| Métrique | Résultat |
|----------|----------|
| **Conformité** | {AUDIT_RESULTS['conformite_globale']:.1f}% |
| **Étapes réussies** | {AUDIT_RESULTS['etapes_ok']}/{AUDIT_RESULTS['etapes_total']} |
| **Certification** | {AUDIT_RESULTS.get('certification', '?')} |
| **Risque** | {AUDIT_RESULTS['niveau_risque']} |
| **Production** | {'✅ AUTORISÉE' if AUDIT_RESULTS['conformite_globale'] >= 80 else '❌ BLOCAGE'} |

---

## ✅ SCÉNARIOS MÉTIER

"""
    
    for s_name, scenario in AUDIT_RESULTS.get("scenarios", {}).items():
        ok = sum(1 for e in scenario.get("etapes", []) if e.get("ok"))
        total = len(scenario.get("etapes", []))
        emoji = "🟢" if ok == total else "🟡" if ok > 0 else "🔴"
        report += f"\n### {emoji} {scenario['nom']} ({ok}/{total})\n\n"
        for etape in scenario.get("etapes", []):
            status = "✅" if etape.get("ok") else "❌"
            report += f"- {status} {etape.get('etape')}\n"
    
    # RBAC
    report += f"\n---\n\n## 🔐 RBAC\n\n"
    for role, result in AUDIT_RESULTS.get("rbac", {}).items():
        emoji = "✅" if result.get("score", 0) >= 80 else "⚠️"
        report += f"{emoji} {role}: {result.get('score', 0):.0f}%\n"
    
    # Conclusion
    report += f"""

---

## 🎯 CONCLUSION

{AUDIT_RESULTS.get('certification', '?')}

**Risque global:** {AUDIT_RESULTS['niveau_risque']}

**Logs complets:** `/tmp/audit_final_v3.log`
**Rapport:** {REPORT_FILE}

---

Généré le {datetime.now().isoformat()}
"""
    
    return report

# ============================================================================
# MAIN
# ============================================================================
def main():
    log.info("🚀 AUDIT FINAL DE CERTIFICATION V3")
    log.info("="*80)
    
    if not setup_users():
        log.error("❌ Setup failed")
        sys.exit(1)
    
    # Run scenarios
    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    scenario_5()
    
    # RBAC
    test_rbac()
    
    # Report
    report = generate_report()
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    
    log.info("\n" + "="*80)
    log.info(f"✅ AUDIT TERMINÉ | Conformité: {AUDIT_RESULTS['conformite_globale']:.1f}%")
    log.info(f"📄 {REPORT_FILE}")
    log.info("="*80 + "\n")
    
    print(report)

if __name__ == "__main__":
    main()
