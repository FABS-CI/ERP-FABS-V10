# 🚀 FIXES PRE-PRODUCTION - ERIP FABS-CI

## 📋 BUGS À FIXER

### ✅ BUG 1: GET /api/stock endpoint manquant
**Status:** IN PROGRESS
**Fichier:** backend/stock_module.py
**Problem:** No simple GET /api/stock route (only sub-routes)
**Fix:** Add GET /api/stock route returning global stock summary
- Ajouter route GET "/" (racine) dans build_stock_router
- Retourner: total_articles, stock_total, valeur_stock, mouvements_aujourd'hui

### 🔴 BUG 2: total_encaisse = 0 dans /api/analytics/financial
**Status:** INVESTIGATING
**Fichier:** backend/analytics_module.py ligne ~264
**Problem:** Pipeline paiements cherche field "montant" qui n'existe pas
**Observation:** paiements_module.py utilise "montant_total", "montant_affecte"
**Fix:** Mettre à jour le field name dans le pipeline (probably "montant_total")

### 🔴 BUG 3: audit user_email = None
**Status:** INVESTIGATING
**Fichier:** backend/server.py log_audit_event() ligne 200
**Problem:** Enregistre user_id mais pas user_email
**Fix:** 
- Ajouter paramètre user_email à log_audit_event()
- Ou résoudre l'email depuis la DB en récupérant le user_id
- Ajouter user_email au audit_doc

## 📊 MONITORING SETUP
**Status:** TODO
- Créer health check endpoint
- Centraliser logs
- Alerts sur erreurs

## 📝 CHECKLIST DÉPLOIEMENT
**Status:** TODO
- Créer document déploiement
- Pre-flight checks

## 🏷️ GIT TAG + DB SNAPSHOT
**Status:** TODO
- Créer tag release-1.0.0
- Snapshot MongoDB

## PROGRESS
- [ ] Fix bug 1 (5 min)
- [ ] Fix bug 2 (5 min)
- [ ] Fix bug 3 (5 min)
- [ ] Commit fixes
- [ ] Setup monitoring
- [ ] Create deployment checklist
- [ ] Tag + snapshot
- [ ] Push
