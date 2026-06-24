# SCRATCHPAD EXÉCUTION — ERP FABS-CI PRODUCTION HARDENING

**Date**: 2026-06-24 | **Tours**: 8 max | **Score Global Target**: ≥8.0

---

## PROGRESS

### ✅ TOUR 1 — SÉCURITÉ + PRODUCTION (COMPLÉTÉ)
- **Score Initial**: 4.0/10
- **Score Final**: 5.6/10 (+1.6)
- **Fichiers Modifiés**: 4
  - `app_simple.py`: Secrets externalisés
  - `.env.production`: Config prod créée
  - `.gitignore`: Secrets non-commitables
  - NEW `validate_production_env.py`: Validation script
- **Gains**: Sécurité 4→8, Production 5→8
- **Documentation**: TOUR_1_AUDIT_INITIAL.md + TOUR_1_RESULTS.md

### 🔄 TOUR 2 — PERFORMANCE (EN COURS)

#### Phase 1: Audit Détaillé N+1 (✅ COMPLÉTÉ)
- Identifié 5 modules critiques
- N+1 patterns détaillé dans rh_module.py
- Créé TOUR_2_PLAN_PERFORMANCE.md

#### Phase 2: Utils Optimisation (✅ COMPLÉTÉ)
- NEW `optimization_utils.py`:
  - BulkQueryOptimizer: enrich_documents_bulk()
  - PaginationHelper: paginate_query()
  - CacheHelper: get_or_fetch()
  - AggregationHelper: create_join_pipeline()

#### Phase 3: Refactorer RH Module (IN PROGRESS)
- [ ] Corriger list_employes() ligne 666
- [ ] Corriger enrichissement lignes 710-740
- [ ] Tests
- [ ] Mesurer improvement

#### Phase 4: Refactorer Commandes + Stock
- [ ] commandes_module.py
- [ ] stock_module.py

#### Phase 5: Analytics + Colisage
- [ ] bi_analytics_module.py
- [ ] colisage_module.py

#### Phase 6: Pagination Globale
- [ ] Ajouter endpoint par endpoint

#### Phase 7: Caching Redis
- [ ] Cache reads fréquentes

#### Phase 8: Test Charge
- [ ] Simuler 200+ users

---

## MODULES CRITIQUES À CORRIGER

| Module | Lignes | Zones N+1 | Priorité | Status |
|--------|--------|-----------|----------|--------|
| rh_module.py | 2321 | 24 | 1️⃣ | 🔄 In Progress |
| commandes_module.py | 1863 | 16 | 2️⃣ | ⏳ Waiting |
| stock_module.py | 1242 | 15 | 3️⃣ | ⏳ Waiting |
| bi_analytics_module.py | 515 | 13 | 4️⃣ | ⏳ Waiting |
| colisage_module.py | 2454 | 13 | 5️⃣ | ⏳ Waiting |

---

## DÉTAIL RH MODULE FIX

### N+1 Pattern Identifié
**Location**: `rh_module.py` lignes 710-740

```python
# AVANT (N+1):
for doc in docs:  # 20 docs
    dept = await db.departements.find_one(...) # Query 1-20
    fonc = await db.fonctions.find_one(...)     # Query 21-40
    cat = await db.categories_pro.find_one(...) # Query 41-60
    sup = await db.employes.find_one(...)       # Query 61-80
# Total: 1 + 80 = 81 queries!

# APRÈS (Bulk):
enrichments = {
    "departement": {...},
    "fonction": {...},
    "categorie_pro": {...},
    "superieur": {...}
}
docs = await BulkQueryOptimizer.enrich_documents_bulk(docs, db, enrichments)
# Total: 1 + 4 = 5 queries!
```

### Impact Estimé
- **Before**: 81 queries pour 20 docs
- **After**: 5 queries pour 20 docs
- **Speedup**: ~16x faster!

---

## NEXT STEPS (IMMEDIATE)

1. ✏️ Copier rh_module.py → rh_module.py.bak
2. ✏️ Ajouter `from optimization_utils import BulkQueryOptimizer` au top
3. ✏️ Remplacer boucle lines 710-740 avec bulk query
4. ✏️ Tester import + syntaxe
5. 🧪 Tester endpoint list_employes
6. ⏱️ Mesurer before/after

---

## SCORES À TRACKER

| Critère | Avant T1 | Après T1 | Target T2 | Après T2 |
|---------|----------|----------|-----------|----------|
| Performance | 3 | 4 | 7 | ? |
| Database | 6 | 6 | 7 | ? |
| Sécurité | 4 | 8 | 8 | ✓ |
| Stabilité | 7 | 7 | 8 | ? |
| Code Quality | 3 | 3 | 6 | ? |
| Production | 5 | 8 | 8 | ✓ |
| Validation Métier | 0 | 0 | 1 | ? |
| **TOTAL** | **4.0** | **5.6** | **6.4** | ? |

---

## RISQUES TRACKER

- [ ] Casser logique métier RH
- [ ] Nouvelle perf pire que avant
- [ ] Redis connection failures
- [ ] Aggregate pipeline complexity

---

## DÉCISIONS PRISES

1. **Secrets**: Externalisé, pas hardcodé ✅
2. **Utils**: Créer reusable optimization module ✅
3. **RH First**: Commencer par module le plus critique ✅
4. **Bulk Query**: Strategy A pour N+1 ✅
5. **Measurement**: Avant/après required ✅

---

## FICHIERS CRÉÉS/MODIFIÉS T2

- [x] `TOUR_2_PLAN_PERFORMANCE.md` — Plan d'attaque
- [x] `optimization_utils.py` — Utils réutilisables
- [ ] `rh_module.py` — Correction N+1 (EN COURS)
- [ ] `commandes_module.py` — À faire après RH
- [ ] `stock_module.py` — À faire après RH

---

## DÉPENDANCES/BLOCKERS

Aucun. Prêt à continuer refactoring RH.

---

## NOTES POUR TOUR 3

Après Tour 2 (si Performance < 7):
- Refactoring massif routers (Code Quality)
  - colisage_module: 2454→<500 lignes
  - rh_module: 2321→<500 lignes
  - commandes_module: 1863→<500 lignes

Créer:
- `routers/` subdir avec micro-routers
- `services/` pour logique métier partagée
- `middleware/` pour pagination/cache/etc
