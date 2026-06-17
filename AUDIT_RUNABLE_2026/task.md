# Audit ERP-FABS-V10 — Progression

## Fait
- [x] Clone + structure (28.5k l backend, ~50 modules, 303+ routes)
- [x] Extraction routes API par module
- [x] RBAC complet (9 rôles, 23 modules, matrice perms) — rbac_constants.py
- [x] ~80 collections MongoDB listées
- [x] Frontend: ~70 pages, routes React extraites
- [x] Git: 40 commits, branches, migrations, tests
- [x] Seed users (8 rôles), produits (37), clients
- [x] Backend LANCÉ en live (uvicorn:8000 + mongo + redis)
- [x] Tests API réels: 36/38 + workflow vente

## BUGS DÉTECTÉS (live)
1. CRITIQUE — Incohérence clé produit `product_id`(API) vs `produit_id`(seed/commandes/stock).
   → Produits seedés invisibles en fiche produit; produits créés via UI non commandables.
2. CRITIQUE — PDF commande 500 si client.adresse/ville=None (pdf_generator.py:414 _client_block .split sur None)
3. MINEUR — RBAC: 422 (validation) avant 403 (perm) sur POST produit par comptable
4. Anti-doublon facture OK; anti-rejeu commande OK; PDF facture OK; paiement->payee OK

## Reste à extraire
- [ ] FNE détail (workflow certif, stickers)
- [ ] Compta (écritures auto, plan SYSCOHADA)
- [ ] Notifications (canaux)
- [ ] Sidebar menus
- [ ] Rédiger content.md (10 inventaires + bugs + plan correction)

## Sortie
AUDIT_RUNABLE_2026/audit.report/content.md
