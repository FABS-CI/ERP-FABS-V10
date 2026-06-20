# 🔧 PLAN DE CORRECTION AUDIT COMPLET

## Issues à corriger:

### 1. POST /api/clients validation (422)
- **Cause:** Schema utilise `nom` + `type_client` mais tests envoient `nom_client` + `categorie`
- **Fix:** Vérifier endpoint accepte les deux formats ou ajuster tests

### 2. POST /api/utilisateurs (405)
- **Cause:** Endpoint n'existe pas ou est bloqué
- **Fix:** Implémenter POST /api/utilisateurs

### 3. Module achats manquant
- **Cause:** Endpoints `/api/fournisseurs`, `/api/achats/commandes` n'existent pas
- **Fix:** Implémenter ou exposer endpoints achat

### 4. GET /api/audit (404)
- **Cause:** Endpoint n'existe pas
- **Fix:** Ajouter GET /api/audit pour lire audit_logs

### 5. Endpoints logistique manquants
- **Cause:** Bons livraison, inventaires, avoirs pas d'endpoints
- **Fix:** Vérifier si modules existent, les exposer ou implémenter

---

## Priorité de correction:

### 🔴 CRITIQUE (jour 1):
- [ ] Fix clients POST validation
- [ ] Implémenter utilisateurs POST
- [ ] Exposer endpoints fournisseurs/achats

### 🟡 IMPORTANT (jour 2):
- [ ] Ajouter audit GET
- [ ] Endpoints livraison
- [ ] Endpoints inventaire

### 🟢 NICE (après):
- [ ] Avoirs
- [ ] Rapports comptables
