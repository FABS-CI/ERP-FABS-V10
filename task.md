# TASK TRACKER : Audit complet ERP FABS-CI

## OBJECTIF
- Analyser tous les boutons des pages de vente
- Tester tous les workflows complets
- Corriger les bugs
- Reporter à l'user en français

## PROGRESSION

### ✅ FAIT
1. [20:53] Backend relancé (venv activate, uvicorn server:app)
2. [20:55] API endpoints validés (httpx test: login, /api/auth/me, listes OK)
3. [21:00] Rapports générés :
   - RAPPORT_INVESTIGATION.md : Root cause analysée
   - RAPPORT_AUDIT_FINAL.json : Test Playwright partiel
   - RAPPORT_API_TEST.py : Script test API créé (en cours de fix)

### 🔄 EN COURS
1. Fix test_api_direct.py :
   - Issue : Réponses API au format {items: [...]} pas [...]
   - Fix appliqué : Parse items + fallback
   - Prochaine : Exécuter et collecter résultats

### ⏳ TODO

**Immédiat** (avant 21:30)
1. [ ] Exécuter test_api_direct.py → workflow complet
2. [ ] Documenter résultats
3. [ ] Commander les bugs identifiés
4. [ ] Rapporter à l'user

**Bugs à corriger**
1. CommandeForm.jsx : formulaire ne rend pas (BUG CRITIQUE)
   - Suspect : useEffect clients/produits fetch bloqué
   - À DEBUG : step state, clients array init
2. CommandeDetail buttons invisible en Playwright
   - ROOT CAUSE : Playwright localStorage/auth sync issue
   - SOLUTION : Test par API directement (plus fiable)
3. Factures, Stock : Endpoints 404 ou permissions fail

**À Valider**
- Tous les endpoints GET : ✅ OK (commandes, factures, paiements, clients, produits, stock=404)
- Création commande : EN TEST
- Workflow validation/préparation/livraison : EN TEST
- Facture auto-generation : EN TEST
- Paiements/Lettrage : À tester

## ENVIRONNEMENT

**Frontend** : http://localhost:3000  
PID node: 3527, port 3000, logs: /tmp/frontend.log  

**Backend** : http://localhost:8000  
PID python: (actif), port 8000, venv: /home/user/ERP-FABS-V10/backend/venv  

**DB** : MongoDB fabsci_erp (localhost:27017)  
- Clients: 1014+
- Produits: 56
- Commandes: 2 (test)

**Test User** : pissken@editionsfabsci.com / Admin@2025 (super_admin)

## RAPPORTS À PRODUIRE

À la fin :
1. JSON audit complet (tous endpoints + boutons)
2. Markdown rapport bugs + solutions
3. Liste des fixes appliqués
4. Recommandations pour futur

## NOTES

- Playwright auth issue = localStorage/context pas synchronisé après login
- Solution = tester API directement (plus rapide + fiable)
- CommandeForm bug = bloqueur pour test création, mais backend OK
- Règle 80/20 : documenter, ne pas recoder sauf critiques
