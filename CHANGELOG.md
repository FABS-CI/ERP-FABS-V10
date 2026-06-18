# CHANGELOG — ERP FABS V10

## [1.0.0] — 2026-06-18 — Mise en production initiale

### Ajouté
- Export PDF état des stocks (ReportLab, thème classique_professionnel, groupé par catégorie)
- Endpoint GET /api/stock/export-etat-stock
- Module FNE/DGI pour certification fiscale
- Module Fleet (véhicules, coûts logistiques)
- Module BI Analytics (tableaux de bord avancés)
- Multi-channel notifications (email, SMS, in-app)
- Module colisage et bons de livraison
- RBAC complet (rôles, habilitations, délégations)
- Rate limiter (SlowAPI, 20 req/min sur login)
- Sanitization XSS (bleach)

### Corrigé (pré-prod — 2026-06-18)
- nginx.conf : port proxy corrigé 8001 → 8000
- Index MongoDB ajoutés sur clients, produits, commandes, factures
- Tests d'intégration : URL corrigées vers localhost:8000

### Infrastructure
- docker-compose.prod.yml configuré (MongoDB 7.0, Redis 7, backend FastAPI, nginx)
- Prometheus + monitoring configurés
- Backup MongoDB automatique
