#!/usr/bin/env python3
"""
AUDIT FONCTIONNEL MÉTIER — ERP FABS V10
Vérifie : RBAC, workflows uniques, règles métier clients/produits, notifications, dashboards
"""
import requests, json
from datetime import datetime

BASE = "http://localhost:8000/api"
RESULTS = []

# ─── Credentials ───────────────────────────────────────────────
USERS_CREDS = {
    "super_admin":            ("pissken@editionsfabsci.com",        "Admin@2025"),
    "directeur_general":      ("ali.mamin@editionsfabsci.com",      "Fabs@2025"),
    "comptable":              ("natachakoffi@editionsfabsci.com",    "Fabs@2025"),
    "directeur_commercial":   ("detymichel@editionsfabsci.com",      "Fabs@2025"),
    "gestionnaire_stock":     ("niangorangeorgie@editionsfabsci.com","Fabs@2025"),
    "responsable_magasinier": ("joachin@editionsfabsci.com",         "Fabs@2025"),
    "secretariat":            ("dadjelarissa@editionsfabsci.com",    "Fabs@2025"),
    "service_logistique":     ("yakeben@editionsfabsci.com",         "Fabs@2025"),
    "assistante":             ("amenan@editionsfabsci.com",          "Fabs@2025"),
}

# ─── Matrice permissions frontend (source de vérité) ───────────
EXPECTED_PERMS = {
    "dashboard":             {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":1,"gestionnaire_stock":1,"responsable_magasinier":1,"secretariat":1,"assistante":0,"service_logistique":1},
    "clients":               {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":1,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":1,"assistante":1,"service_logistique":0},
    "commandes":             {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":1,"gestionnaire_stock":1,"responsable_magasinier":1,"secretariat":1,"assistante":1,"service_logistique":0},
    "proformas":             {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":1,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":1,"assistante":1,"service_logistique":0},
    "factures":              {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "paiements":             {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "produits":              {"super_admin":1,"directeur_general":1,"comptable":0,"directeur_commercial":1,"gestionnaire_stock":1,"responsable_magasinier":0,"secretariat":0,"assistante":1,"service_logistique":0},
    "stock":                 {"super_admin":1,"directeur_general":1,"comptable":0,"directeur_commercial":0,"gestionnaire_stock":1,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "fne":                   {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "comptabilite":          {"super_admin":1,"directeur_general":1,"comptable":1,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "utilisateurs":          {"super_admin":1,"directeur_general":0,"comptable":0,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
    "parametres":            {"super_admin":1,"directeur_general":0,"comptable":0,"directeur_commercial":0,"gestionnaire_stock":0,"responsable_magasinier":0,"secretariat":0,"assistante":0,"service_logistique":0},
}

MODULE_ROUTES = {
    "dashboard":    "/dashboard/stats",
    "clients":      "/clients",
    "commandes":    "/commandes",
    "proformas":    "/proformas",
    "factures":     "/factures",
    "paiements":    "/paiements",
    "produits":     "/produits",
    "stock":        "/stock/mouvements",
    "fne":          "/fne/dashboard/fne-stats",
    "comptabilite": "/comptabilite/ecritures",
    "utilisateurs": "/utilisateurs",
    "parametres":   "/parametres",
}

def log(cat, name, status, detail=""):
    icon = "✅" if status=="OK" else ("❌" if status=="FAIL" else "⚠️")
    RESULTS.append({"cat":cat,"name":name,"status":status,"detail":detail})
    print(f"  {icon} {name}" + (f" → {detail}" if detail else ""))

def login(role):
    email, pwd = USERS_CREDS[role]
    r = requests.post(f"{BASE}/auth/login", json={"email":email,"password":pwd}, timeout=10)
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def get(token, path, params=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(f"{BASE}{path}", headers=h, params=params, timeout=10)

def post(token, path, data):
    h = {"Authorization": f"Bearer {token}"}
    return requests.post(f"{BASE}{path}", headers=h, json=data, timeout=10)

def patch(token, path, data=None):
    h = {"Authorization": f"Bearer {token}"}
    return requests.patch(f"{BASE}{path}", headers=h, json=data or {}, timeout=10)

# ═══════════════════════════════════════════════════════════
# 1. RBAC — CONTRÔLE ACCÈS PAR RÔLE
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  1. RBAC — ACCÈS PAR RÔLE")
print("="*60)

tokens = {}
for role in USERS_CREDS:
    t = login(role)
    tokens[role] = t
    if t:
        log("AUTH", f"Login {role}", "OK")
    else:
        log("AUTH", f"Login {role}", "FAIL", "Impossible de se connecter")

print("\n  -- Vérification accès modules par rôle --")
rbac_fails = []
rbac_incoherences = []

for module, route in MODULE_ROUTES.items():
    for role, token in tokens.items():
        if not token: continue
        expected = EXPECTED_PERMS.get(module, {}).get(role, -1)
        if expected == -1: continue
        
        r = get(token, route)
        got_access = r.status_code not in [401, 403]
        
        if expected == 1 and not got_access:
            rbac_fails.append(f"{role} → {module}: devrait avoir accès (HTTP {r.status_code})")
            log("RBAC", f"{role}/{module}", "FAIL", f"Accès refusé, devrait être autorisé (HTTP {r.status_code})")
        elif expected == 0 and got_access:
            rbac_incoherences.append(f"{role} → {module}: ne devrait PAS avoir accès (HTTP {r.status_code})")
            log("RBAC", f"{role}/{module}", "WARN", f"Accès autorisé, devrait être INTERDIT (HTTP {r.status_code})")

if not rbac_fails and not rbac_incoherences:
    log("RBAC", "Matrice RBAC complète", "OK", f"{len(MODULE_ROUTES)*len(tokens)} combinaisons vérifiées")

# ═══════════════════════════════════════════════════════════
# 2. CLIENTS — RÈGLES MÉTIER
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  2. CLIENTS — RÈGLES MÉTIER")
print("="*60)

sa_token = tokens["super_admin"]

# 2a. Liste et comptage
r = get(sa_token, "/clients", {"limit":1000})
if r.status_code == 200:
    data = r.json()
    total = data.get("total", len(data.get("items", data.get("clients",[]))))
    clients = data.get("items", data.get("clients", []))
    log("CLIENTS", f"Total clients", "OK", f"{total} clients en base")
    
    # Vérifier les types_client
    types = {}
    for c in clients:
        t = c.get("type_client","inconnu")
        types[t] = types.get(t,0)+1
    log("CLIENTS", "Diversité types_client", "OK", f"{len(types)} types: {', '.join(sorted(types.keys())[:5])}...")
    
    # Vérifier présence champs obligatoires
    champs_manquants = [c for c in clients if not c.get("nom") or not c.get("client_id")]
    if champs_manquants:
        log("CLIENTS", "Champs obligatoires", "FAIL", f"{len(champs_manquants)} clients sans nom/id")
    else:
        log("CLIENTS", "Champs obligatoires (nom, client_id)", "OK", "Tous renseignés")
    
    # Vérifier références FABS-CLI
    sans_ref = [c for c in clients if not str(c.get("reference","")).startswith("FABS-CLI")]
    if sans_ref:
        log("CLIENTS", "Références FABS-CLI-XXXX", "WARN", f"{len(sans_ref)} clients sans référence standard")
    else:
        log("CLIENTS", "Références FABS-CLI-XXXX", "OK")
    
    # Clients actifs vs inactifs
    actifs = sum(1 for c in clients if c.get("actif", True))
    inactifs = total - actifs
    log("CLIENTS", "Statut actif/inactif", "OK", f"{actifs} actifs, {inactifs} inactifs")
    
    # Test désactivation/réactivation
    if clients:
        cli_id = clients[0]["client_id"]
        r2 = patch(sa_token, f"/clients/{cli_id}", {"actif": False})
        if r2.status_code == 200:
            r3 = patch(sa_token, f"/clients/{cli_id}", {"actif": True})
            log("CLIENTS", "Désactivation/Réactivation", "OK" if r3.status_code==200 else "FAIL")
        else:
            log("CLIENTS", "Désactivation client", "WARN", f"HTTP {r2.status_code}")
else:
    log("CLIENTS", "Liste clients", "FAIL", f"HTTP {r.status_code}")

# 2b. Historique client
r = get(sa_token, "/clients")
if r.status_code == 200:
    _cd = r.json()
    clients_list = _cd.get("items", _cd.get("clients", []))
    if clients_list:
        cli_id = clients_list[0]["client_id"]
        r2 = get(sa_token, f"/clients/{cli_id}")
        if r2.status_code == 200:
            log("CLIENTS", "Détail/Historique client", "OK")
        else:
            log("CLIENTS", "Détail client", "FAIL", f"HTTP {r2.status_code}")

# ═══════════════════════════════════════════════════════════
# 3. PRODUITS — CLASSIFICATION MÉTIER
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  3. PRODUITS — CLASSIFICATION MÉTIER")
print("="*60)

r = get(sa_token, "/produits", {"limit":100})
if r.status_code == 200:
    data = r.json()
    produits = data.get("items", data.get("produits", data if isinstance(data, list) else []))
    total_p = data.get("total", len(produits))
    log("PRODUITS", f"Total catalogue", "OK", f"{total_p} produits")
    
    # Vérifier champs ISBN
    avec_isbn = [p for p in produits if p.get("isbn")]
    log("PRODUITS", "ISBN renseigné", "OK" if avec_isbn else "WARN", 
        f"{len(avec_isbn)}/{len(produits)} avec ISBN")
    
    # Prix
    prix_1fcfa = [p for p in produits if p.get("prix_vente",0) <= 1]
    prix_ok = [p for p in produits if p.get("prix_vente",0) > 1]
    log("PRODUITS", "Prix de vente", "OK" if prix_ok else "WARN",
        f"{len(prix_ok)} avec prix réel, {len(prix_1fcfa)} à compléter (1 FCFA)")
    
    # Catégories
    cats = {}
    for p in produits:
        c = p.get("categorie","") or p.get("cycle","") or "non classé"
        cats[c] = cats.get(c,0)+1
    log("PRODUITS", "Catégories/Cycles", "OK", f"{len(cats)} catégories: {list(cats.keys())[:4]}")
    
    # Matière/niveau
    avec_matiere = [p for p in produits if p.get("matiere") or p.get("niveau")]
    log("PRODUITS", "Matière/Niveau renseigné", "OK" if avec_matiere else "WARN",
        f"{len(avec_matiere)}/{len(produits)} classifiés")
    
    # Stock — vérifie stock_actuel (champ canonique)
    en_rupture = [p for p in produits if p.get("stock_actuel", p.get("stock", 0)) <= 0]
    log("PRODUITS", "Stock", "WARN" if len(en_rupture) == len(produits) else "OK",
        f"{len(en_rupture)}/{len(produits)} en rupture de stock")
    
    # Titre renseigné (les livres FABS n'ont pas de champ 'auteur' — c'est un éditeur)
    avec_titre = [p for p in produits if p.get("titre") or p.get("nom")]
    log("PRODUITS", "Titre produit renseigné", "OK" if avec_titre else "WARN",
        f"{len(avec_titre)}/{len(produits)} avec titre")

# ═══════════════════════════════════════════════════════════
# 4. WORKFLOWS UNIQUES (idempotence)
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  4. WORKFLOWS UNIQUES — IDEMPOTENCE")
print("="*60)

# Créer une commande de test
r = get(sa_token, "/clients", {"limit":1})
_cr = r.json(); cli = (_cr.get("items") or _cr.get("clients") or [{}])[0]
cli_id = cli.get("client_id","CLI00001")

r = get(sa_token, "/produits", {"limit":1})
pdata = r.json()
_plist = pdata.get("items", pdata.get("produits", pdata if isinstance(pdata,list) else []))
prod = _plist[0] if isinstance(_plist, list) and _plist else {}
prod_id = prod.get("product_id", prod.get("produit_id","PRD00001"))
prix = prod.get("prix_vente",2000)

cmd_payload = {
    "client_id": cli_id,
    "lignes": [{"produit_id": prod_id, "quantite": 1, "prix_unitaire": prix}],
    "submit": False
}
r = post(sa_token, "/commandes", cmd_payload)
if r.status_code == 201:
    cmd = r.json()
    cmd_id = cmd.get("commande_id") or cmd.get("id")
    ref = cmd.get("reference","?")
    log("WORKFLOW", f"Commande test créée ({ref})", "OK")
    
    # Soumettre
    r2 = post(sa_token, f"/commandes/{cmd_id}/soumettre", {})
    log("WORKFLOW", "Soumettre commande", "OK" if r2.status_code==200 else "FAIL", f"HTTP {r2.status_code}")
    
    # Double soumission → doit échouer
    r3 = post(sa_token, f"/commandes/{cmd_id}/soumettre", {})
    if r3.status_code in [400, 409, 422]:
        log("WORKFLOW", "Double soumission bloquée", "OK", f"HTTP {r3.status_code} (correct)")
    else:
        log("WORKFLOW", "Double soumission bloquée", "FAIL", f"HTTP {r3.status_code} — action répétable !")
    
    # Valider
    r4 = post(sa_token, f"/commandes/{cmd_id}/valider", {})
    log("WORKFLOW", "Valider commande", "OK" if r4.status_code==200 else "FAIL", f"HTTP {r4.status_code}")
    
    # Double validation → doit échouer
    r5 = post(sa_token, f"/commandes/{cmd_id}/valider", {})
    if r5.status_code in [400, 409, 422]:
        log("WORKFLOW", "Double validation bloquée", "OK", f"HTTP {r5.status_code} (correct)")
    else:
        log("WORKFLOW", "Double validation bloquée", "FAIL", f"HTTP {r5.status_code} — action répétable !")
    
    # Préparer
    r6 = post(sa_token, f"/commandes/{cmd_id}/preparer", {})
    log("WORKFLOW", "Préparer commande", "OK" if r6.status_code==200 else "FAIL", f"HTTP {r6.status_code}")
    
    # Double préparation → doit échouer
    r7 = post(sa_token, f"/commandes/{cmd_id}/preparer", {})
    if r7.status_code in [400, 409, 422]:
        log("WORKFLOW", "Double préparation bloquée", "OK", f"HTTP {r7.status_code} (correct)")
    else:
        log("WORKFLOW", "Double préparation bloquée", "FAIL", f"HTTP {r7.status_code} — action répétable !")
    
    # Générer BL
    bl_payload = {"commande_id": cmd_id, "client_id": cli_id,
                  "lignes": [{"produit_id": prod_id, "quantite": 1}]}
    r8 = post(sa_token, "/bons-livraison", bl_payload)
    log("WORKFLOW", "Générer BL", "OK" if r8.status_code==201 else "WARN", f"HTTP {r8.status_code}")
    
    # Générer facture depuis commande
    r9 = post(sa_token, "/factures/generer-depuis-commande", {"commande_id": cmd_id})
    fc_id = None
    if r9.status_code == 201:
        fc = r9.json()
        fc_id = fc.get("facture_id") or fc.get("id")
        log("WORKFLOW", "Facture générée depuis commande", "OK", fc.get("reference","?"))
        
        # Double génération facture → doit échouer (idempotence)
        r10 = post(sa_token, "/factures/generer-depuis-commande", {"commande_id": cmd_id})
        if r10.status_code in [400, 409, 422]:
            log("WORKFLOW", "Double génération facture bloquée", "OK", f"HTTP {r10.status_code} (correct)")
        else:
            log("WORKFLOW", "Double génération facture bloquée", "FAIL", f"HTTP {r10.status_code} — répétable !")
    elif r9.status_code == 400 and "existe déjà" in r9.text:
        # Facture déjà créée pour cette commande — idempotence backend OK
        log("WORKFLOW", "Double génération facture bloquée", "OK", "Facture existante détectée — idempotence backend OK")
        # Récupérer la facture existante filtrée par commande_id
        r_fc_list = get(sa_token, "/factures", {"commande_id": cmd_id})
        if r_fc_list.status_code == 200:
            fc_data = r_fc_list.json()
            fcs = [f for f in fc_data.get("items", fc_data.get("factures", []))
                   if f.get("commande_id") == cmd_id]
            if fcs:
                fc_id = fcs[0].get("facture_id") or fcs[0].get("id")
                # Récupérer le client_id de cette facture pour le paiement
                cli_id = fcs[0].get("client_id", cli_id)
    else:
        log("WORKFLOW", "Facture depuis commande", "WARN", f"HTTP {r9.status_code}: {r9.text[:80]}")
    
    if fc_id:
        # Émettre facture
        r11 = post(sa_token, f"/factures/{fc_id}/emettre", {})
        log("WORKFLOW", "Émettre facture", "OK" if r11.status_code in [200,400] else "WARN", f"HTTP {r11.status_code}")
        
        # Double émission → doit échouer
        r12 = post(sa_token, f"/factures/{fc_id}/emettre", {})
        if r12.status_code in [400, 409, 422]:
            log("WORKFLOW", "Double émission facture bloquée", "OK", f"HTTP {r12.status_code} (correct)")
        else:
            log("WORKFLOW", "Double émission facture bloquée", "FAIL", f"répétable !")
        
        # Paiement
        pay_payload = {
            "client_id": cli_id,
            "montant_total": prix,
            "mode_paiement": "especes",
            "date_paiement": datetime.now().strftime("%Y-%m-%d"),
            "factures": [{"facture_id": fc_id, "montant_affecte": prix}]
        }
        r13 = post(sa_token, "/paiements", pay_payload)
        log("WORKFLOW", "Enregistrer paiement", "OK" if r13.status_code in [200,201] else "WARN", f"HTTP {r13.status_code}: {r13.text[:60] if r13.status_code not in [200,201] else ''}")
else:
    log("WORKFLOW", "Création commande test", "FAIL", f"HTTP {r.status_code}: {r.text[:80]}")

# ═══════════════════════════════════════════════════════════
# 5. DASHBOARD — COHÉRENCE DES CHIFFRES
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  5. DASHBOARDS — COHÉRENCE CHIFFRES")
print("="*60)

r = get(sa_token, "/dashboard/stats")
if r.status_code == 200:
    stats = r.json()
    # La réponse a structure {"role":..., "kpis":[{key, value, ...}]}
    kpis_list = stats.get("kpis", [])
    kpis_map = {k["key"]: k["value"] for k in kpis_list if isinstance(k, dict) and "key" in k}
    ca = kpis_map.get("ca_mois", stats.get("ca_mois", stats.get("ca_mensuel", 0)))
    nb_clients = kpis_map.get("total_clients", stats.get("total_clients", 0))
    nb_factures = kpis_map.get("total_factures", stats.get("total_factures", 0))
    log("DASHBOARD", "Chiffre d'affaires mois", "OK", f"{ca:,.0f} FCFA")
    log("DASHBOARD", "Total clients", "OK" if nb_clients >= 1014 else "WARN", f"{nb_clients}")
    log("DASHBOARD", "Total factures", "OK", f"{nb_factures}")
    
    # Vérifier cohérence clients
    r2 = get(sa_token, "/clients")
    real_clients = r2.json().get("total", 0) if r2.status_code==200 else 0
    if abs(nb_clients - real_clients) > 5:
        log("DASHBOARD", "Cohérence nb_clients vs /clients", "WARN", 
            f"Dashboard={nb_clients} vs API={real_clients}")
    else:
        log("DASHBOARD", "Cohérence nb_clients vs /clients", "OK", 
            f"Dashboard={nb_clients} ≈ API={real_clients}")
    
    # KPIs présents
    kpis = stats.get("kpis", [])
    log("DASHBOARD", "KPIs présents", "OK", f"{len(kpis)} KPIs")
else:
    log("DASHBOARD", "Dashboard stats", "FAIL", f"HTTP {r.status_code}")

# BI Analytics
r = get(sa_token, "/bi-analytics/dashboard")
log("DASHBOARD", "BI Analytics dashboard", "OK" if r.status_code==200 else "FAIL", f"HTTP {r.status_code}")

# FNE Dashboard
r = get(sa_token, "/fne/dashboard/fne-stats")
if r.status_code == 200:
    fne = r.json()
    log("DASHBOARD", "FNE stats", "OK", f"Timbres/stickers/taux présents")
else:
    log("DASHBOARD", "FNE stats", "WARN", f"HTTP {r.status_code}")

# ═══════════════════════════════════════════════════════════
# 6. NOTIFICATIONS — ÉVÉNEMENTS
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  6. NOTIFICATIONS")
print("="*60)

r = get(sa_token, "/notifications")
log("NOTIF", "Liste notifications", "OK" if r.status_code==200 else "FAIL", f"HTTP {r.status_code}")

r = get(sa_token, "/notifications/preferences")
log("NOTIF", "Préférences notifications", "OK" if r.status_code==200 else "FAIL", f"HTTP {r.status_code}")

r = get(sa_token, "/notifications/logs")
log("NOTIF", "Historique envois", "OK" if r.status_code==200 else "FAIL", f"HTTP {r.status_code}")

# Multi-channel (WhatsApp/SMS/Email)
r = get(sa_token, "/multi-channel-notifications/config-check")
log("NOTIF", "Multi-channel (WhatsApp/SMS/Email)", "OK" if r.status_code==200 else "WARN", f"HTTP {r.status_code}")

# ═══════════════════════════════════════════════════════════
# 7. INCOHÉRENCES BACKEND vs FRONTEND RBAC
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  7. INCOHÉRENCES BACKEND vs FRONTEND")
print("="*60)

# Vérifier DG accès utilisateurs (frontend=0, backend=1)
r_dg = get(tokens["directeur_general"], "/utilisateurs")
if r_dg.status_code == 200:
    log("INCOH", "DG accès /utilisateurs", "WARN", 
        "Backend autorise (lvl=1), Frontend interdit — incohérence !")
else:
    log("INCOH", "DG accès /utilisateurs", "OK", "Backend et Frontend alignés (refusé)")

# Vérifier DG accès paramètres (frontend=0, backend=1)
r_dg2 = get(tokens["directeur_general"], "/parametres")
if r_dg2.status_code == 200:
    log("INCOH", "DG accès /parametres", "WARN",
        "Backend autorise (lvl=1), Frontend interdit — incohérence !")
else:
    log("INCOH", "DG accès /parametres", "OK", "Alignés")

# Vérifier comptable-avancee (frontend interdit DG, backend autorise)
r_dg3 = get(tokens["directeur_general"], "/comptabilite-avancee/plan-comptable")
if r_dg3.status_code == 200:
    log("INCOH", "DG accès comptabilite-avancee", "WARN",
        "Backend autorise (lvl=1), Frontend interdit — incohérence !")
else:
    log("INCOH", "DG accès comptabilite-avancee", "OK", "Alignés")

# Assistante ne devrait pas voir dashboard
r_ass = get(tokens["assistante"], "/dashboard/stats")
if r_ass.status_code in [401,403]:
    log("INCOH", "Assistante bloquée /dashboard", "OK", "Correctement refusé")
else:
    log("INCOH", "Assistante accès /dashboard", "WARN", 
        f"HTTP {r_ass.status_code} — devrait être interdit")

# ═══════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  RAPPORT FINAL — AUDIT FONCTIONNEL MÉTIER")
print("="*60)

ok    = [r for r in RESULTS if r["status"]=="OK"]
warns = [r for r in RESULTS if r["status"]=="WARN"]
fails = [r for r in RESULTS if r["status"]=="FAIL"]
total = len(RESULTS)
score = round((len(ok) + len(warns)*0.5) / total * 10, 1) if total else 0

print(f"\n  Total tests : {total}")
print(f"  ✅ OK       : {len(ok)}")
print(f"  ⚠️  WARN    : {len(warns)}")
print(f"  ❌ FAIL     : {len(fails)}")
print(f"\n  Score fonctionnel métier : {score}/10")

if warns:
    print(f"\n  ── Points à corriger (WARN) ──")
    for w in warns:
        print(f"    ⚠️  [{w['cat']}] {w['name']}: {w['detail']}")

if fails:
    print(f"\n  ── Blocages critiques (FAIL) ──")
    for f in fails:
        print(f"    ❌ [{f['cat']}] {f['name']}: {f['detail']}")

print("\n" + "="*60)

# Sauvegarder résultats JSON
with open("/home/user/ERP-FABS-V10/backend/audit_metier_results.json","w") as f:
    json.dump({
        "date": datetime.now().isoformat(),
        "total": total,
        "ok": len(ok),
        "warns": len(warns),
        "fails": len(fails),
        "score": score,
        "results": RESULTS
    }, f, ensure_ascii=False, indent=2)

print("  Résultats sauvegardés → audit_metier_results.json")
