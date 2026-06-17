import httpx, sys

B = "http://localhost:8000/api"
c = httpx.Client(base_url=B, timeout=30)

# login super_admin
r = c.post("/auth/login", json={"email": "pissken@editionsfabsci.com", "password": "Admin@2025"})
print("login", r.status_code)
tok = r.json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

# pick 2 produits + 1 client
prods = c.get("/produits", headers=H, params={"limit": 5}).json()
items = prods.get("items") or prods.get("data") or prods
plist = items if isinstance(items, list) else items.get("items", [])
print("nb produits page:", len(plist))
p1, p2 = plist[0], plist[1]
print("p1 classif:", p1.get("product_id"), p1.get("matiere"), p1.get("niveau_scolaire"), p1.get("cycle"))

cli = c.get("/clients", headers=H, params={"limit": 1}).json()
clist = cli.get("items") or cli.get("data") or cli
client = (clist if isinstance(clist, list) else clist.get("items", []))[0]
print("client:", client.get("client_id"), client.get("nom"), "ville=", client.get("ville"))

pid1 = p1["product_id"]; pid2 = p2["product_id"]
# assurer du stock pour le test E2E
from pymongo import MongoClient
_db = MongoClient('mongodb://localhost:27017')['fabsci_erp']
_db.produits.update_many({"product_id": {"$in": [pid1, pid2]}}, {"$set": {"stock_actuel": 100}})
pu1 = p1.get("prix_vente") or 1; pu2 = p2.get("prix_vente") or 1

# create commande
cmd_payload = {
    "client_id": client["client_id"],
    "lignes": [
        {"produit_id": pid1, "designation": p1.get("titre","P1"), "quantite": 3, "prix_unitaire": pu1, "remise_ligne": 0, "montant_ligne": 3*pu1},
        {"produit_id": pid2, "designation": p2.get("titre","P2"), "quantite": 2, "prix_unitaire": pu2, "remise_ligne": 0, "montant_ligne": 2*pu2},
    ],
    "remise_globale": 0,
}
r = c.post("/commandes", headers=H, json=cmd_payload)
print("create commande", r.status_code, r.text[:300] if r.status_code>=400 else "")
cmd = r.json()
cmd_id = cmd.get("commande_id")
print("commande_id:", cmd_id)

# get commande with lignes (check enrichment)
r = c.get(f"/commandes/{cmd_id}", headers=H)
cmdf = r.json()
for l in cmdf.get("lignes", []):
    print("  LIGNE:", l.get("produit_titre"), "| mat:", l.get("produit_matiere"), "| niv:", l.get("produit_niveau_scolaire"), "| cyc:", l.get("produit_cycle"))

# commande PDF (BUG-02 check)
r = c.get(f"/commandes/{cmd_id}/pdf", headers=H)
print("commande PDF:", r.status_code, len(r.content), "bytes" if r.status_code==200 else r.text[:200])

# create facture from commande
# soumettre puis valider commande
rs = c.post(f"/commandes/{cmd_id}/soumettre", headers=H)
print("soumettre", rs.status_code, rs.text[:150] if rs.status_code>=400 else "")
rv = c.post(f"/commandes/{cmd_id}/valider", headers=H)
print("valider commande", rv.status_code, rv.text[:150] if rv.status_code>=400 else "")
r = c.post("/factures/generer-depuis-commande", headers=H, json={"commande_id": cmd_id})
print("create facture", r.status_code, r.text[:300] if r.status_code>=400 else "")
fac = r.json() if r.status_code<400 else {}
fac_id = fac.get("facture_id")
print("facture_id:", fac_id)
if fac_id:
    r = c.get(f"/factures/{fac_id}/pdf", headers=H)
    print("facture PDF:", r.status_code, len(r.content), "bytes" if r.status_code==200 else r.text[:200])
    if r.status_code == 200:
        open("/tmp/facture_test.pdf","wb").write(r.content)

# stats
for ep in ["by-matiere","by-niveau","by-cycle","by-ville"]:
    r = c.get(f"/analytics/{ep}", headers=H)
    print(f"stats {ep}:", r.status_code, str(r.json())[:250] if r.status_code<400 else r.text[:150])

r = c.get("/analytics/stock-by-classification", headers=H, params={"group_by":"matiere"})
print("stock-by-classification matiere:", r.status_code, str(r.json())[:300] if r.status_code<400 else r.text[:150])
