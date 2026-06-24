# TOUR 1 — ACTION RAPIDE

## Objectif
**Établir la baseline de validation métier** (actuellement 0/10)

## État Actuel
✅ Tous les fichiers sont prêts  
✅ Test script complètement configuré  
✅ Runner script avec auto-start backend  

## Prêt pour Exécution ?

**Oui. Execute MAINTENANT:**

```bash
cd /home/user/ERP-FABS-V10 && bash run_validation.sh
```

**Cet commande va**:
1. Vérifier si backend tourne sur port 8000
2. Lancer backend si nécessaire
3. Attendre que l'API soit prête
4. Exécuter 26 tests sur 6 modules
5. Générer `VALIDATION_REPORT.md`
6. Afficher résumé final

**Durée**: ~3-5 minutes

---

## Après Exécution: Vérification

**Fichier à vérifier**:
```bash
cat /home/user/ERP-FABS-V10/VALIDATION_REPORT.md
```

**Cherche**:
- ✅ Authentication: COMPLETED
- ✅ Commercial: COMPLETED (7 tests min)
- ✅ Purchases: COMPLETED (6 tests min)
- ✅ Stock: COMPLETED (4 tests min)
- ✅ Finance: COMPLETED (6 tests min)
- ✅ HR: COMPLETED (4 tests min)

**Si tous = COMPLETED** → TOUR 1 SUCCESS  
**Si quelques failures** → Documenté, continue TOUR 2  
**Si backend fail** → Vérifier MongoDB, dépendances

---

## Après Validation: Prochaine Étape

**TOUR 2: Performance Optimization**
- Identifier endpoints lents dans rapport
- Fixer top 20 N+1 queries
- Ajouter Redis caching
- Target: Performance 4/10 → 8/10

**Commande TOUR 2** (après TOUR 1 réussi):
```bash
# À préparer après résultats de TOUR 1
```

---

## En Cas de Problème

**Problème**: Backend cannot connect  
**Fix**: 
```bash
cd /home/user/ERP-FABS-V10/backend
python3 app_simple.py
# Dans autre terminal: python3 ../complete_business_validation.py
```

**Problème**: MongoDB not running  
**Fix**: 
```bash
docker run -d -p 27017:27017 mongo:latest
# Ou utiliser MongoDB existante
```

**Problème**: Port 8000 déjà utilisé  
**Fix**:
```bash
lsof -i :8000  # Voir quel process
kill -9 <PID>  # Tuer le process
```

---

## Status: READY FOR EXECUTION ✅

**Files Created**:
- ✅ `complete_business_validation.py` — 584 lines, 26 tests
- ✅ `run_validation.sh` — Test runner with auto-start
- ✅ `TOUR_1_AUDIT_FRAMEWORK.md` — Scoring criteria
- ✅ `TOUR_1_EXECUTION_SUMMARY.md` — Detailed plan

**Blockers**: None  
**Manual Steps Needed**: Just run the script  

**PROCEED TO EXECUTION** →

```bash
cd /home/user/ERP-FABS-V10 && bash run_validation.sh
```
