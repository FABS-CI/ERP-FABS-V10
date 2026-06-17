# Audit intégral ERP-FABS-V10 — Plan

## Méthode
Audit statique exhaustif du code source (backend FastAPI + frontend React) +
analyse git + tentative de lancement local. Pas de prod live accessible →
tests = analyse statique des routes/workflows/règles métier + lint/structure.

## Phases
1. [ ] Extraction routes API (toutes, par module)
2. [ ] Extraction modèles/collections MongoDB (tables, relations)
3. [ ] Rôles, permissions, RBAC, menus
4. [ ] Workflows commerciaux (devis→commande→BL→facture→paiement→avoir)
5. [ ] Frontend: pages, routes, menus, boutons
6. [ ] Modules transverses: FNE, compta, stock, RH/paie, notifications, docs PDF
7. [ ] Git: commits récents, branches, migrations, nouveautés
8. [ ] Données seed: clients, produits, rôles
9. [ ] Tests existants + tentative run
10. [ ] Bugs & incohérences
11. [ ] Rapport final (content.md) avec 10 inventaires

## Sortie
AUDIT_RUNABLE_2026/audit.report/content.md
