# TOUR 1 - AUDIT INITIAL ERP FABS-CI

**Date**: 2026-06-24 | **État**: Production Readiness Baseline

---

## SCORES INITIAUX (SUR 10)

| Critère | Score | Justification |
|---------|-------|---------------|
| **Performance** | **3/10** | 27 fichiers N+1 query risk, pagination partielle (21/82), cache Redis sous-utilisé (10/82), 49 fonctions >200 lignes |
| **Base de données** | **6/10** | Indexes créés (✅) mais transactions minimales (1), pas de optimisations spécifiques |
| **Sécurité** | **4/10** | CORS allow_origins=['*'] 🔴 CRITIQUE, secrets possiblement hardcodés (6 warnings) |
| **Stabilité** | **7/10** | Error handling OK (1.06 ratio try/except), logs présents, mais routers monolithiques = risque |
| **Qualité Code** | **3/10** | 7 fichiers >1000 lignes, 49 long functions >200 lignes, architecture monolithique |
| **Production** | **5/10** | .env.production.example existe, Dockerfile créé mais .env absent, monitoring partiel |
| **Validation Métier** | **0/10** | Pas de simulation effectuée |

**SCORE GLOBAL INITIAL: 4.0/10** ❌ Non production-ready

---

## DÉTAIL DES PROBLÈMES CRITIQUES

### 🔴 SÉCURITÉ CRITIQUE

1. **CORS Allow Origins**
   - Risque: XSS, CSRF, injection depuis n'importe quel domaine
   - Fichier: `backend/server.py`
   - Action: Remplacer `allow_origins=["*"]` par liste blanche

2. **Secrets Potentiellement Hardcodés**
   - Fichiers: app_simple.py, fne_module.py, fne_queue.py, secrets_rotation_service.py, server.py
   - Action: Auditer et externaliser tous les secrets

### ⚠️ PERFORMANCE CRITIQUE

1. **N+1 Queries (27 fichiers)**
   - Routers monolithiques qui récupèrent données en boucles
   - Exemple: `for item in items: db.find_one(...)`
   - Impact: Temps réponse O(n), timeout sur 200+ users
   - Fichiers critiques: colisage_module.py (2112 lignes), rh_module.py (1820), commandes_module.py (1540)

2. **Pagination Incomplète**
   - Seulement 21/82 fichiers implémentent pagination
   - Risque: Charger 1000+ documents = OOM + timeout
   - Action: Ajouter skip/limit partout

3. **Cache Redis Sous-utilisé**
   - Seulement 10/82 fichiers utilisent Redis
   - KPI dashboard, listes clients, produits = JAMAIS cachés
   - Impact: 10-20 requêtes DB par page reload
   - Action: Caching agressif pour lectures fréquentes

### 💥 CODE QUALITY CRITIQUE

1. **Routers Monolithiques**
   - 7 fichiers >1000 lignes
   - colisage_module.py: 2112 lignes (61 routes en 1 fonction!)
   - Risque: impossibilité de tester, maintenir, debugger
   - Action: Refactorer en micro-routers

2. **49 Fonctions >200 lignes**
   - Fonctions complexes, difficiles à tester
   - Cognitive load élevé
   - Action: Refactoring en fonctions < 100 lignes

3. **Duplication de Code**
   - Même logique de pagination/error handling répétée
   - Pas de utilitaires réutilisables
   - Action: Créer services partagés

### 📊 DONNÉES

- **Problèmes**:
  - Transactions minimales (1 seule)
  - Pas de rollback sur erreurs multi-step
  - Créations d'index OK mais pas vérifiées en prod

### 🔧 PRODUCTION

- **Problème**: .env manquant, config non validée
- **Action**: .env.production créer et vérifier

---

## FICHIERS À PRIORITISER

### Tier 1 (URGENT)
1. `backend/server.py` — CORS, secrets, config
2. `backend/colisage_module.py` — Refactoring 2112 lignes
3. `backend/rh_module.py` — Refactoring 1820 lignes

### Tier 2 (HAUTE)
4. `backend/commandes_module.py` — 1540 lignes + N+1
5. `backend/factures_module.py` — 1182 lignes
6. Tout module avec N+1 risk

### Tier 3 (MEDIUM)
7. Frontend — Supprimer 55 console.logs
8. Cache strategy pour lectures

---

## PLAN TOUR 1 IMMEDIATE

**ACTION PRIORITAIRE: Corriger CORS + Externaliser secrets**

C'est le goulot d'étranglement sécurité le plus critique.

**Impact estimé**:
- Sécurité: 4→6 (+2)
- Production: 5→6 (+1)

Reste à faire après: N+1 queries (performance), refactoring (code quality)

---

## PROCHAINS TOURS

**Tour 2**: N+1 Queries (Performance)
**Tour 3**: Router Refactoring (Code Quality)
**Tour 4**: Pagination + Caching (Performance)
**Tour 5**: Stability Hardening
**Tour 6**: Production Checklist
**Tour 7**: Validation Métier Simulation
**Tour 8**: Final Audit + Rapport

---

## MÉTRIQUES À TRACKER

- [ ] Temps moyen réponse API (target: <500ms)
- [ ] Nombre de requêtes par page (target: <10)
- [ ] Memory usage (target: <500MB)
- [ ] CPU usage (target: <30% avg)
- [ ] Error rate (target: <0.1%)
- [ ] Uptime (target: >99.9%)

---

**DÉCISION**: CONTINUER — Tous les critères < 8, lancer Tour 2
