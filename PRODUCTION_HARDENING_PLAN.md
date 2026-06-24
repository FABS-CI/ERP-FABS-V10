# ERP FABS-CI — Plan de Production Hardening
**Date**: 2026-06-24 | **Objectif**: Production-Ready + Validation Métier Complète

---

## PHASE 0: AUDIT INITIAL (TOUR 1)

### État des lieux
- **Backend**: FastAPI + Motor (MongoDB async) + Redis cache
- **Frontend**: React + Tailwind (vanilla HTML fallback)
- **Infra**: Docker Compose (dev/prod) + K8s manifests
- **Données**: MongoDB (1014 clients, 56 produits, 9 users, Redis cache)
- **Security**: JWT auth, RBAC, encryption, audit logs, rate limiting présents
- **Modules**: 30+ modules métier (commerciaux, finances, RH, logistique, etc.)

### 7 Critères de Production
1. **Performance** — Pagination, lazy loading, caching, requêtes optimisées
2. **Base de Données** — Indexes, contraintes, intégrité, transactions
3. **Sécurité** — Validation, CSRF, XSS, secrets externalisés, permissions
4. **Stabilité** — 0 bug bloquant, exception handling, logs, pas de crashes
5. **Qualité Code** — Duplication réduite, composants réutilisables, nettoyage
6. **Production** — .env validé, build prod, déploiement, monitoring, backups
7. **Validation Métier** — Simulation complète de TOUS les workflows

---

## TOUR 1 ACTIONS PRIORITAIRES

### Action 1.1: Audit Performance Backend
- [ ] Analyser les requêtes MongoDB pour N+1 queries
- [ ] Vérifier les indexes manquants
- [ ] Mesurer response times actuels
- [ ] Identifier les routes lentes

### Action 1.2: Audit Sécurité Rapide
- [ ] Vérifier CORS, CSRF, XSS
- [ ] Contrôler .env (secrets externalisés)
- [ ] Vérifier JWT expiry et refresh
- [ ] Valider validation des inputs

### Action 1.3: Audit Code Quality
- [ ] Identifier les duplications massives
- [ ] Fonctions trop longues (>100 lignes)
- [ ] Code mort à nettoyer
- [ ] Structure incohérente

---

## TOUR 1 NOTES INITIALES (À REMPLIR)
```
Performance: /10
Base de données: /10
Sécurité: /10
Stabilité: /10
Qualité du code: /10
Production: /10
Validation métier: /10
```

---

## BOUCLE DE CORRECTION
Tant que un critère < 8:
1. **PLAN** — Une action pour le critère le plus faible
2. **FAIRE** — Correction réelle
3. **VÉRIFIER** — Noter le progrès
4. **DÉCIDER** — Continuer ou terminer

Max 8 tours → Rapport final obligatoire

---

## ARTEFACTS FINAUX REQUIS
1. Rapport d'audit complet
2. Rapport de simulation métier (TOUS les modules)
3. Liste des bugs corrigés
4. Liste des optimisations
5. Risques résiduels
6. Checklist mise en production
7. Checklist validation utilisateur
8. Résumé pour Direction
