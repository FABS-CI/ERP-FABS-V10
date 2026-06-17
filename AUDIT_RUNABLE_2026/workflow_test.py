#!/usr/bin/env python3
"""Test workflow vente complet bout-en-bout."""
import requests, json, uuid
BASE="http://localhost:8000/api"
def login(e,p="Fabs@2026"):
    r=requests.post(f"{BASE}/auth/login",json={"email":e,"password":p},timeout=15)
    return r.json().get("access_token") if r.ok else None
sa=login("pissken@editionsfabsci.com")
H={"Authorization":f"Bearer {sa}"}
res=[]
def rec(n,ok,d=""):
    res.append({"name":n,"ok":ok,"detail":d}); print(f"[{'PASS' if ok else 'FAIL'}] {n} {('- '+str(d)) if d else ''}")

# Client
cl={"nom":f"GROUPE SCOLAIRE AUDIT {uuid.uuid4().hex[:5]}","type_client":"ecole","representant":"M. KOUASSI","telephone":"0701020304","ville":"Abidjan","plafond_credit":5000000}
r=requests.post(f"{BASE}/clients",headers=H,json=cl,timeout=10)
cid=r.json().get("client_id") if r.ok else None
rec("création client école",r.status_code in(200,201),f"{r.status_code} {cid or r.text[:120]}")

# Produit
pr={"titre":f"MANUEL AUDIT {uuid.uuid4().hex[:5]}","categorie":"primaire","niveau_scolaire":"CE1","prix_vente":3000,"prix_achat":1500,"stock_actuel":500}
r=requests.post(f"{BASE}/produits",headers=H,json=pr,timeout=10)
pid=r.json().get("product_id") if r.ok else None
rec("création produit",r.status_code in(200,201),f"{r.status_code} {pid or r.text[:120]}")

if cid and pid:
    cmd={"client_id":cid,"taux_tva":18.0,"lignes":[{"produit_id":pid,"quantite":50,"prix_unitaire":3000}]}
    r=requests.post(f"{BASE}/commandes",headers=H,json=cmd,timeout=15)
    cmid=r.json().get("commande_id") if r.ok else None
    rec("création commande",r.status_code in(200,201),f"{r.status_code} {cmid or r.text[:150]}")
    if cmid:
        r=requests.post(f"{BASE}/commandes/{cmid}/soumettre",headers=H,timeout=10)
        rec("soumettre (brouillon->en_attente)",r.status_code in(200,201),r.status_code)
        r=requests.post(f"{BASE}/commandes/{cmid}/valider",headers=H,timeout=10)
        rec("valider (en_attente->validee)",r.status_code in(200,201),f"{r.status_code} {r.text[:120] if r.status_code not in(200,201) else ''}")
        r=requests.post(f"{BASE}/commandes/{cmid}/valider",headers=H,timeout=10)
        rec("ANTI-REJEU re-valider bloqué (400)",r.status_code==400,r.status_code)
        r=requests.post(f"{BASE}/commandes/{cmid}/preparer",headers=H,timeout=10)
        rec("préparer (validee->preparee)",r.status_code in(200,201),f"{r.status_code} {r.text[:120] if r.status_code not in(200,201) else ''}")
        # PDF commande
        r=requests.get(f"{BASE}/commandes/{cmid}/pdf",headers=H,timeout=20)
        rec("PDF commande",r.status_code==200,f"{r.status_code} ct={r.headers.get('content-type')}")
        # Facture
        r=requests.post(f"{BASE}/factures/generer-depuis-commande",headers=H,json={"commande_id":cmid},timeout=15)
        fid=r.json().get("facture_id") if r.ok else None
        rec("générer facture depuis commande",r.status_code in(200,201),f"{r.status_code} {fid or r.text[:150]}")
        # double génération facture (anti-doublon)
        r2=requests.post(f"{BASE}/factures/generer-depuis-commande",headers=H,json={"commande_id":cmid},timeout=15)
        rec("ANTI-DOUBLON double facture",r2.status_code in(400,409) or (r2.ok and r2.json().get("facture_id")==fid),f"{r2.status_code}")
        if fid:
            r=requests.post(f"{BASE}/factures/{fid}/emettre",headers=H,timeout=10)
            rec("émettre facture",r.status_code in(200,201),f"{r.status_code} {r.text[:120] if r.status_code not in(200,201) else ''}")
            r=requests.get(f"{BASE}/factures/{fid}/pdf",headers=H,timeout=20)
            rec("PDF facture",r.status_code==200 and 'pdf' in r.headers.get('content-type',''),f"{r.status_code} ct={r.headers.get('content-type')}")
            # paiement
            r=requests.get(f"{BASE}/factures/{fid}",headers=H,timeout=10)
            ttc=r.json().get("montant_ttc",0) if r.ok else 0
            pay={"facture_id":fid,"montant":ttc,"mode_paiement":"especes","date_paiement":"2026-06-17"}
            r=requests.post(f"{BASE}/paiements",headers=H,json=pay,timeout=10)
            rec("enregistrer paiement total",r.status_code in(200,201),f"{r.status_code} {r.text[:150] if r.status_code not in(200,201) else 'ttc='+str(ttc)}")
            # facture doit passer payee
            r=requests.get(f"{BASE}/factures/{fid}",headers=H,timeout=10)
            rec("facture statut payee après paiement",r.ok and r.json().get("statut")=="payee",f"statut={r.json().get('statut') if r.ok else '?'}")
            # avoir
            r=requests.post(f"{BASE}/factures/generer-avoir",headers=H,json={"facture_id":fid,"motif":"Retour audit"},timeout=15)
            rec("générer avoir",r.status_code in(200,201),f"{r.status_code} {r.text[:150] if r.status_code not in(200,201) else ''}")

tot=len(res);ok=sum(1 for x in res if x["ok"])
print(f"\n===== WORKFLOW: {ok}/{tot} PASS =====")
json.dump(res,open("/home/user/ERP-FABS-V10/AUDIT_RUNABLE_2026/workflow_results.json","w"),ensure_ascii=False,indent=2)
