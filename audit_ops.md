# AUDIT OPÉRATIONNEL ERP FABS-CI V10 — Simulation entreprise réelle

## Objectif
Évaluer si l'ERP peut gérer Éditions FABSCI (maison d'édition scolaire) dès demain, multi-utilisateurs.

## Méthode
1. Vérifier infra (front/back/db) ✅ en cours
2. Cartographier TOUS les endpoints réels (openapi)
3. Créer données démo réalistes (écoles, livres, commerciaux, chauffeurs, flotte...)
4. Simuler plusieurs jours d'activité (commandes → livraisons → encaissements → compta)
5. Tester chaque module sous 7 angles métier
6. Note /100 + verdict

## Rôles d'évaluation
- DSI : infra, sécurité, perf, backups
- Auditeur ERP : cohérence des flux, intégrité données
- Directeur Commercial : clients/écoles, commandes, commerciaux
- Comptable : encaissements, dépenses, compta SYSCOHADA, fournisseurs
- Magasinier : stocks, dépôts, inventaires
- RH : employés, permissions
- Logistique : livraisons, chauffeurs, flotte

## Progression
- [ ] Étape 1 — Infra
- [ ] Étape 2 — Cartographie endpoints
- [ ] Étape 3 — Données démo
- [ ] Étape 4 — Simulation activité
- [ ] Étape 5 — Tests par module
- [ ] Étape 6 — Rapport final
