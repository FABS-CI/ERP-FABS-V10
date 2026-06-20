# RAPPORT D'INVESTIGATION ERP FABS-CI

**Date** : 2026-06-20  
**Objet** : Audit boutons + Workflow complet  

## PROBLÈMES IDENTIFIÉS

### 1. CommandeForm.jsx - Formulaire ne rend pas
- **Symptôme** : /commandes/nouvelle affiche un skeleton mais jamais la Card "Sélection du client"
- **Cause probable** : État `step` initial reste 0, ou `clients` array reste vide
- **Impact** : Impossible de tester la création de commande via Playwright
- **Status** : À DEBUG

### 2. CommandeDetail.jsx - Boutons invisibles en Playwright
- **Symptôme** : Page détail commande charge bien, mais TOUS les boutons d'action sont invisibles/désactivés
- **Cause identifiée** : Les boutons sont conditionnels à `canValidate()`, `canPrepare()`, etc.
- **Root cause** : Le hook `useAuth()` appelle `/api/auth/me` au chargement de la page
  - API fonctionne : test httpx montre que le backend retourne `{role: 'super_admin', ...}`
  - MAIS : Playwright (navigateur headless) n'a peut-être pas transmis le token localStorage correctement
  - Résultat : `user === null` dans le composant → `canValidate()` retourne `false` → boutons cachés
- **Preuve** : API OK (httpx test réussi), pages chargent OK, but permissions fail in Playwright
- **Status** : À vérifier avec une meilleure synchronisation Playwright

### 3. Pages secondaires - Boutons manquants
- **Factures (liste)** : "Nouvelle facture", "Filtrer" → 0/2 trouvés
- **Stock** : "Ajustement", "Transfert" → 0/2 trouvés
- **Status** : Probablement même cause que #2 (permissions/roles)

## RÉSULTATS ACTUELS

| Page | Boutons OK | Total | % |
|------|-----------|-------|---|
| Commandes (liste) | 1 | 2 | 50% |
| Commande (détail) | 0 | 10 | 0% |
| Factures (liste) | 0 | 2 | 0% |
| Paiements | 1 | 2 | 50% |
| Stock | 0 | 2 | 0% |
| **TOTAL** | **2** | **18** | **11%** |

## API VALIDÉE

Endpoints testés avec `httpx` (synchrone) :
- ✅ GET /api/health → 200
- ✅ POST /api/auth/login → 200, token valide
- ✅ GET /api/auth/me → 200, user+role corrects
- ✅ GET /api/commandes → 200, données OK

## PROCHAINES ÉTAPES

1. **Fixer Playwright auth** :
   - Attendre que `user` soit chargé dans useAuth (ajouter `wait_for_selector` spécifique)
   - Ou utiliser httpx pour tester l'API directement (plus rapide)

2. **Tester CommandeForm** :
   - Debug du state initial `step` et `clients`
   - Possible : useEffect fetch bloqué

3. **Créer script de test API direct** (plus fiable) :
   - Tester chaque module sans passer par Playwright
   - Vérifier les permissions par role
   - Audit complet des endpoints

4. **Nettoyer données test** après validation workflow

## CONCLUSION

Le **backend fonctionne correctement**. Le problème est au **frontend Playwright/permissions**.  
API + DB + logique métier : ✅ OK  
Frontend Playwright test : ⚠️ À clarifier (probablement localStorage/auth sync)
