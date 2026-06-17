#!/usr/bin/env python3
"""Audit ERP FABS V10 — tests fonctionnels réels contre le backend live."""
import requests, json, sys, uuid
BASE = "http://localhost:8000/api"
PWD = "Fabs@2026"
USERS = {
    "super_admin": "pissken@editionsfabsci.com",
    "directeur_general": "ali.mamin@editionsfabsci.com",
    "comptable": "natachakoffi@editionsfabsci.com",
    "directeur_commercial": "detymichel@editionsfabsci.com",
    "gestionnaire_stock": "niangorangeorgie@editionsfabsci.com",
    "responsable_magasinier": "joachin@editionsfabsci.com",
    "secretariat": "dadjelarissa@editionsfabsci.com",
    "service_logistique": "yakeben@editionsfabsci.com",
}
results = []
def rec(cat, name, ok, detail=""):
    results.append({"cat": cat, "name": name, "ok": ok, "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {cat} :: {name} {('- '+detail) if detail else ''}")

def login(email, pwd=PWD):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pwd}, timeout=15)
    if r.status_code == 200:
        return r.json().get("access_token") or r.json().get("token"), r.json()
    return None, {"status": r.status_code, "body": r.text[:300]}

def H(tok): return {"Authorization": f"Bearer {tok}"}

# ---------- 1. AUTH: login tous rôles ----------
tokens = {}
for role, email in USERS.items():
    tok, info = login(email)
    rec("AUTH", f"login {role}", tok is not None, "" if tok else json.dumps(info)[:200])
    if tok: tokens[role] = tok

sa = tokens.get("super_admin")
if not sa:
    print("!! Pas de token super_admin — arrêt"); 
# ---------- 2. AUTH: mauvais mot de passe ----------
tok, info = login(USERS["comptable"], "WrongPass!1")
rec("AUTH", "rejet mauvais mot de passe", tok is None, f"status={info.get('status')}")

# ---------- 3. /auth/me ----------
if sa:
    r = requests.get(f"{BASE}/auth/me", headers=H(sa), timeout=10)
    rec("AUTH", "/auth/me super_admin", r.status_code==200, f"role={r.json().get('role') if r.ok else r.status_code}")

# ---------- 4. Accès sans token (doit 401/403) ----------
r = requests.get(f"{BASE}/auth/me", timeout=10)
rec("SECURITY", "accès /auth/me sans token rejeté", r.status_code in (401,403), f"status={r.status_code}")

# ---------- helper GET ----------
def get(path, role="super_admin"):
    t = tokens.get(role)
    if not t: return None
    return requests.get(f"{BASE}{path}", headers=H(t), timeout=20)

# ---------- 5. Dashboards ----------
for p,name in [("/dashboard/stats","dashboard général"),("/analytics/dashboard","analytics"),
               ("/bi-analytics/dashboard","BI analytics"),("/rh/dashboard","RH"),
               ("/fne/dashboard/fne-stats","FNE"),("/proformas/stats/dashboard","proformas")]:
    r = get(p)
    rec("DASHBOARD", name, r is not None and r.status_code==200, f"status={r.status_code if r else 'n/a'}")

# ---------- 6. Listes principales ----------
for p,name in [("/clients","clients"),("/produits","produits"),("/commandes","commandes"),
               ("/factures","factures"),("/paiements","paiements"),("/proformas","proformas"),
               ("/fournisseurs","fournisseurs"),("/stock/mouvements","mouvements stock"),
               ("/rh/employes","employés"),("/notifications/non-lues","notifications"),
               ("/comptabilite/ecritures","écritures compta"),("/fne/invoices","FNE invoices"),
               ("/colisage/ordres","ordres colisage"),("/fleet/vehicules","véhicules")]:
    r = get(p)
    n = None
    if r is not None and r.status_code==200:
        try:
            j = r.json(); n = len(j) if isinstance(j,list) else (len(j.get("items",j.get("data",[]))) if isinstance(j,dict) else "?")
        except: n="?"
    rec("LISTES", name, r is not None and r.status_code==200, f"status={r.status_code if r else 'n/a'} count={n}")

# ---------- 7. RBAC: comptable ne doit pas écrire produits (perm 0) ----------
ct = tokens.get("comptable")
if ct:
    r = requests.post(f"{BASE}/produits", headers=H(ct), json={"titre":"X","prix_vente":1000,"categorie":"primaire"}, timeout=10)
    rec("RBAC", "comptable bloqué création produit", r.status_code in (401,403), f"status={r.status_code}")
# service_logistique ne doit pas lire clients (perm 0)
sl = tokens.get("service_logistique")
if sl:
    r = requests.get(f"{BASE}/clients", headers=H(sl), timeout=10)
    rec("RBAC", "service_logistique bloqué lecture clients", r.status_code in (401,403), f"status={r.status_code}")

# ---------- 8. CRUD Produit (super_admin) ----------
prod_id=None
if sa:
    payload={"titre":f"AUDIT TEST {uuid.uuid4().hex[:6]}","prix_vente":2500,"prix_achat":1200,
             "categorie":"primaire","niveau_scolaire":"CP1","stock_actuel":100}
    r=requests.post(f"{BASE}/produits",headers=H(sa),json=payload,timeout=10)
    ok=r.status_code in (200,201)
    if ok:
        prod_id=r.json().get("product_id") or r.json().get("id")
    rec("CRUD","création produit",ok,f"status={r.status_code} id={prod_id}")
    if prod_id:
        r=requests.patch(f"{BASE}/produits/{prod_id}",headers=H(sa),json={"prix_vente":2800},timeout=10)
        rec("CRUD","modif produit",r.status_code==200,f"status={r.status_code}")

# ---------- 9. CRUD Client ----------
client_id=None
if sa:
    payload={"nom":f"ECOLE AUDIT {uuid.uuid4().hex[:5]}","telephone":"0700000000","ville":"Abidjan","type":"ecole"}
    r=requests.post(f"{BASE}/clients",headers=H(sa),json=payload,timeout=10)
    ok=r.status_code in (200,201)
    if ok: client_id=r.json().get("client_id") or r.json().get("id")
    rec("CRUD","création client",ok,f"status={r.status_code} id={client_id}")

# ---------- 10. WORKFLOW VENTE complet ----------
cmd_id=None
if sa and client_id and prod_id:
    cmd={"client_id":client_id,"lignes":[{"produit_id":prod_id,"quantite":10,"prix_unitaire":2800}]}
    r=requests.post(f"{BASE}/commandes",headers=H(sa),json=cmd,timeout=15)
    ok=r.status_code in (200,201)
    if ok: cmd_id=r.json().get("commande_id") or r.json().get("id")
    rec("WORKFLOW","création commande",ok,f"status={r.status_code} id={cmd_id} body={r.text[:150] if not ok else ''}")
    if cmd_id:
        r=requests.post(f"{BASE}/commandes/{cmd_id}/soumettre",headers=H(sa),timeout=10)
        rec("WORKFLOW","soumettre commande",r.status_code in (200,201),f"status={r.status_code}")
        r=requests.post(f"{BASE}/commandes/{cmd_id}/valider",headers=H(sa),timeout=10)
        rec("WORKFLOW","valider commande",r.status_code in (200,201),f"status={r.status_code} {r.text[:120] if r.status_code not in (200,201) else ''}")
        # anti-rejeu: re-valider doit échouer
        r2=requests.post(f"{BASE}/commandes/{cmd_id}/valider",headers=H(sa),timeout=10)
        rec("WORKFLOW","anti-rejeu re-valider bloqué",r2.status_code==400,f"status={r2.status_code}")
        # préparer
        r=requests.post(f"{BASE}/commandes/{cmd_id}/preparer",headers=H(sa),timeout=10)
        rec("WORKFLOW","préparer commande",r.status_code in (200,201),f"status={r.status_code} {r.text[:120] if r.status_code not in (200,201) else ''}")
        # générer facture depuis commande
        r=requests.post(f"{BASE}/factures/generer-depuis-commande",headers=H(sa),json={"commande_id":cmd_id},timeout=15)
        fok=r.status_code in (200,201)
        fid=r.json().get("facture_id") if fok else None
        rec("WORKFLOW","générer facture depuis commande",fok,f"status={r.status_code} {r.text[:150] if not fok else fid}")
        if fid:
            r=requests.post(f"{BASE}/factures/{fid}/emettre",headers=H(sa),timeout=10)
            rec("WORKFLOW","émettre facture",r.status_code in (200,201),f"status={r.status_code} {r.text[:120] if r.status_code not in(200,201) else ''}")
            # PDF facture
            r=requests.get(f"{BASE}/factures/{fid}/pdf",headers=H(sa),timeout=20)
            rec("DOCUMENTS","PDF facture",r.status_code==200 and r.headers.get('content-type','').startswith('application/pdf'),f"status={r.status_code} ct={r.headers.get('content-type')}")

# ---------- 11. Recherche globale ----------
r=get("/recherche/globale?q=test")
rec("RECHERCHE","recherche globale",r is not None and r.status_code==200,f"status={r.status_code if r else 'n/a'}")

# ---------- 12. Health details ----------
r=get("/health/details")
rec("INFRA","health details",r is not None and r.status_code==200,f"status={r.status_code if r else 'n/a'}")

# ---------- SUMMARY ----------
total=len(results); passed=sum(1 for x in results if x["ok"])
print(f"\n===== RÉSUMÉ: {passed}/{total} PASS, {total-passed} FAIL =====")
json.dump(results, open("/home/user/ERP-FABS-V10/AUDIT_RUNABLE_2026/test_results.json","w"), ensure_ascii=False, indent=2)
print("Résultats -> test_results.json")
