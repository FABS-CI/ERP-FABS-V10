# FEUILLE DE ROUTE - APPROCHE PAR LOTS
## ERP FABS-CI V7 - Estimation Réaliste

**Date** : 2 juin 2026  
**Version ERP** : V7  
**Approche** : Minimum Viable Product (MVP) → Renforcement → Optimisation

---

## SYNTHÈSE EXÉCUTIVE

**Décision** : NO-GO PRODUCTION (actuel)

**Nouvelle estimation** :
- **LOT 1 - GO PRODUCTION MINIMUM VIABLE** : 8 semaines (2 mois)
- **LOT 2 - RENFORCEMENT FONCTIONNEL** : 10 semaines (2.5 mois)
- **LOT 3 - OPTIMISATIONS AVANCÉES** : 12 semaines (3 mois)

**Délai total pour maturité complète** : 30 semaines (7.5 mois)

**Délai pour première mise en production** : 8 semaines (2 mois)

---

## CLASSIFICATION DES DÉVELOPPEMENTS

### Critères de Classification

| Type | Définition | Impact sur GO PROD |
|------|------------|-------------------|
| **Bloquant Production** | Indispensable pour mise en production | OBLIGATOIRE |
| **Critique Métier** | Essentiel pour exploitation ERP | LOT 1 ou 2 |
| **Confort Utilisateur** | Améliore l'expérience | LOT 2 ou 3 |
| **Évolution Future** | Fonctionnalités avancées | LOT 3 |

---

## LOT 1 - GO PRODUCTION MINIMUM VIABLE ERP

**Objectif** : Exploitation réelle de l'ERP  
**Délai estimé** : 8 semaines (2 mois)  
**Effort total** : 40 jours

### Développements Bloquants Production

#### DR-001 : Génération Automatique Écritures Comptables (Simplifiée)
**Type** : Bloquant Production  
**Module** : Comptabilité, Factures, Paiements  
**Effort estimé** : 10 jours  
**Délai** : 2 semaines  

**Description** :
Implémenter la génération automatique d'écritures comptables depuis :
- Factures émises (vente - compte 411, 701)
- Avoirs émis (retour - compte 411, 701)
- Paiements reçus (encaissement - compte 512, 411)

**Portée réduite** :
- ❌ Pas d'intégration BL/BR pour l'instant
- ❌ Pas de lettrage automatique complexe
- ✅ Génération basique écritures
- ✅ Balance vérifiée

**Dépendances** :
- Module comptabilité existant
- Module factures existant
- Module paiements existant

**Tests de validation** :
- Scénario : Facture → Écriture comptable générée
- Scénario : Paiement → Écriture comptable générée
- Scénario : Avoir → Écriture comptable générée
- Scénario : Balance vérifiée

**Acceptation** :
- ✅ Écritures générées automatiquement
- ✅ Balance équilibrée
- ✅ Audit logs implémentés

---

#### DR-002 : Intégration BL → Commande et Stock
**Type** : Bloquant Production  
**Module** : Bons Livraison, Commandes, Stock  
**Effort estimé** : 8 jours  
**Délai** : 2 semaines  

**Description** :
Implémenter l'intégration automatique :
- BL validé → Mise à jour statut commande (livree)
- BL validé → Génération mouvement stock (sortie)

**Dépendances** :
- Module BL existant
- Module commandes existant
- Module stock existant

**Tests de validation** :
- Scénario : BL validé → Statut commande mis à jour
- Scénario : BL validé → Mouvement stock généré
- Scénario : Stock actuel recalculé
- Scénario : Audit logs implémentés

**Acceptation** :
- ✅ Statut commande mis à jour automatiquement
- ✅ Mouvement stock généré automatiquement
- ✅ Stock recalculé correctement
- ✅ Audit logs implémentés

---

#### DR-003 : Intégration BR → Stock
**Type** : Bloquant Production  
**Module** : Bons Retour, Stock  
**Effort estimé** : 5 jours  
**Délai** : 1 semaine  

**Description** :
Implémenter l'intégration automatique :
- BR validé → Génération mouvement stock (entrée)

**Portée réduite** :
- ❌ Pas de lien automatique avec facture originale (manuel pour LOT 1)
- ✅ Mouvement stock généré
- ✅ Avoir généré (déjà implémenté)

**Dépendances** :
- Module BR existant
- Module stock existant

**Tests de validation** :
- Scénario : BR validé → Mouvement stock généré
- Scénario : Stock actuel recalculé
- Scénario : Audit logs implémentés

**Acceptation** :
- ✅ Mouvement stock généré automatiquement
- ✅ Stock recalculé correctement
- ✅ Audit logs implémentés

---

#### DR-006 : Correction Sécurité JWT
**Type** : Bloquant Production  
**Module** : Authentification  
**Effort estimé** : 2 jours  
**Délai** : 1 semaine  

**Description** :
- Exiger JWT_SECRET en production
- Renforcer validation mot de passe (min 8, majuscule, chiffre, spécial)

**Portée réduite** :
- ❌ Pas de rotation secrets (LOT 2)
- ❌ Pas de blacklist access tokens (LOT 2)
- ✅ JWT_SECRET obligatoire
- ✅ Mot de passe renforcé

**Dépendances** :
- Module auth existant

**Tests de validation** :
- Scénario : JWT_SECRET obligatoire en production
- Scénario : Validation mot de passe renforcée

**Acceptation** :
- ✅ JWT_SECRET obligatoire
- ✅ Mot de passe renforcé

---

#### DR-007 : Correction Sécurité CORS
**Type** : Bloquant Production  
**Module** : Sécurité  
**Effort estimé** : 1 jour  
**Délai** : 1 semaine  

**Description** :
- Supprimer fallback "*" en production
- Lister méthodes autorisées explicitement (GET, POST, PUT, DELETE)
- Lister headers autorisés explicitement

**Dépendances** :
- Middleware CORS existant

**Tests de validation** :
- Scénario : CORS restreint en production
- Scénario : Méthodes limitées
- Scénario : Headers limités

**Acceptation** :
- ✅ Fallback "*" supprimé
- ✅ Méthodes limitées
- ✅ Headers limités

---

#### DR-009 : Audit Logs Modules Métier (Simplifié)
**Type** : Bloquant Production  
**Module** : Global  
**Effort estimé** : 6 jours  
**Délai** : 2 semaines  

**Description** :
Implémenter audit logs sur modules critiques :
- Commandes (CREATE, UPDATE, VALIDATE, PREPARE, DELIVER)
- Factures (CREATE, UPDATE)
- Stock (CREATE, UPDATE)
- Paiements (CREATE)

**Portée réduite** :
- ❌ Pas d'audit logs sur clients/produits (LOT 2)
- ❌ Pas d'audit logs RH (LOT 2)
- ✅ Audit logs modules critiques

**Dépendances** :
- Fonction log_audit_event existante
- Collection audit_logs existante

**Tests de validation** :
- Scénario : Audit logs commandes
- Scénario : Audit logs factures
- Scénario : Audit logs stock
- Scénario : Audit logs paiements

**Acceptation** :
- ✅ Audit logs implémentés sur modules critiques
- ✅ Actions critiques logguées

---

#### DR-016 : Audit Frontend React (Simplifié)
**Type** : Bloquant Production  
**Module** : Frontend  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Auditer code React (validation XSS basique)
- Vérifier intégration backend
- Tests frontend critiques (login, création commande, création facture)

**Portée réduite** :
- ❌ Pas de tests frontend complets (LOT 2)
- ✅ Audit XSS basique
- ✅ Tests critiques

**Dépendances** :
- Frontend React existant

**Tests de validation** :
- Scénario : Audit code
- Scénario : Validation XSS
- Scénario : Tests critiques

**Acceptation** :
- ✅ Code audité
- ✅ XSS validé
- ✅ Tests critiques implémentés

---

#### DR-017 : Tests de Charge Minimum
**Type** : Bloquant Production  
**Module** : Performance  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Tests de charge basiques (100 utilisateurs simultanés)
- Tests de performance endpoints critiques
- Tests de concurrence (10 commandes simultanées)

**Portée réduite** :
- ❌ Pas de tests de charge avancés (LOT 3)
- ❌ Pas de tests de scalabilité (LOT 3)
- ✅ Tests de charge basiques
- ✅ Tests performance critiques

**Dépendances** :
- Backend existant

**Tests de validation** :
- Scénario : Test charge 100 utilisateurs
- Scénario : Test performance endpoints
- Scénario : Test concurrence

**Acceptation** :
- ✅ Tests charge implémentés
- ✅ Performance acceptable

---

#### RECETTE : Exécution Scénarios Critiques
**Type** : Bloquant Production  
**Module** : Recette  
**Effort estimé** : 2 jours  
**Délai** : 1 semaine  

**Description** :
Exécuter scénarios de recette critiques (47 scénarios) :
- Cycle Vente complet (10 scénarios)
- Gestion retours et avoirs (5 scénarios)
- Gestion stocks (8 scénarios)
- Workflows approbation (6 scénarios)
- Contrôle droits utilisateurs (5 scénarios)
- Écritures comptables (5 scénarios)
- Sécurité (8 scénarios)

**Dépendances** :
- Application en cours d'exécution
- Données de test préparées

**Acceptation** :
- ✅ 47 scénarios exécutés
- ✅ Résultats documentés
- ✅ Anomalies identifiées

---

### Synthèse LOT 1

| Développement | Type | Effort | Délai |
|---------------|------|--------|-------|
| DR-001 : Écritures comptables (simplifié) | Bloquant | 10 jours | 2 sem |
| DR-002 : Intégration BL | Bloquant | 8 jours | 2 sem |
| DR-003 : Intégration BR | Bloquant | 5 jours | 1 sem |
| DR-006 : Sécurité JWT | Bloquant | 2 jours | 1 sem |
| DR-007 : Sécurité CORS | Bloquant | 1 jour | 1 sem |
| DR-009 : Audit logs (simplifié) | Bloquant | 6 jours | 2 sem |
| DR-016 : Audit frontend (simplifié) | Bloquant | 3 jours | 1 sem |
| DR-017 : Tests charge (minimum) | Bloquant | 3 jours | 1 sem |
| RECETTE : Scénarios critiques | Bloquant | 2 jours | 1 sem |
| **TOTAL** | | **40 jours** | **8 sem** |

---

## LOT 2 - RENFORCEMENT FONCTIONNEL

**Objectif** : Enrichissement métier  
**Délai estimé** : 10 semaines (2.5 mois)  
**Effort total** : 50 jours

### Développements Critique Métier

#### DR-001-B : Génération Écritures Comptables (Complète)
**Type** : Critique Métier  
**Module** : Comptabilité  
**Effort estimé** : 5 jours  
**Délai** : 1 semaine  

**Description** :
Compléter la génération d'écritures comptables :
- Intégration BL (marchandises sorties)
- Intégration BR (marchandises entrées)
- Lettrage automatique

**Dépendances** :
- DR-001 (LOT 1) complété

**Acceptation** :
- ✅ Écritures BL/BR générées
- ✅ Lettrage automatique fonctionnel

---

#### DR-008 : Rate Limiting Étendu
**Type** : Critique Métier  
**Module** : Sécurité  
**Effort estimé** : 5 jours  
**Délai** : 2 semaines  

**Description** :
- Implémenter rate limiting sur create-user
- Implémenter rate limiting sur change-password
- Implémenter rate limiting sur endpoints CRUD sensibles
- Ajouter tracking tentatives échouées

**Dépendances** :
- slowapi existant

**Acceptation** :
- ✅ Rate limiting étendu
- ✅ Tracking implémenté

---

#### DR-009-B : Audit Logs Complet
**Type** : Critique Métier  
**Module** : Global  
**Effort estimé** : 4 jours  
**Délai** : 1 semaine  

**Description** :
Compléter audit logs sur tous les modules :
- Clients (CREATE, READ, UPDATE, DELETE)
- Produits (CREATE, READ, UPDATE, DELETE)
- RH (CREATE, READ, UPDATE, DELETE)

**Dépendances** :
- DR-009 (LOT 1) complété

**Acceptation** :
- ✅ Audit logs complets

---

#### DR-010 : Notifications Automatiques Workflows
**Type** : Critique Métier  
**Module** : Notifications, Workflows  
**Effort estimé** : 8 jours  
**Délai** : 2 semaines  

**Description** :
- Notification approbation requise
- Notification approbation accordée/refusée
- Notification commande validée
- Notification seuil stock atteint

**Dépendances** :
- Module notifications existant
- Module workflows existant

**Acceptation** :
- ✅ Notifications automatiques
- ✅ Intégration workflows

---

#### DR-011 : Délégation Approbation (Basique)
**Type** : Critique Métier  
**Module** : Workflows  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Délégation temporaire
- Historique délégations

**Dépendances** :
- Module workflows existant

**Acceptation** :
- ✅ Délégation basique
- ✅ Historique fonctionnel

---

#### DR-012 : Module Inventaire
**Type** : Critique Métier  
**Module** : Stock  
**Effort estimé** : 8 jours  
**Délai** : 2 semaines  

**Description** :
- Création inventaire
- Saisie écarts
- Validation inventaire
- Régularisation stock

**Dépendances** :
- Module stock existant

**Acceptation** :
- ✅ Inventaire fonctionnel
- ✅ Écarts gérés

---

#### DR-013 : Module Alertes Stock (Basique)
**Type** : Critique Métier  
**Module** : Stock  
**Effort estimé** : 4 jours  
**Délai** : 1 semaine  

**Description** :
- Seuils alertes
- Notifications rupture stock

**Portée réduite** :
- ❌ Pas de réapprovisionnement automatique (LOT 3)
- ✅ Seuils alertes
- ✅ Notifications

**Dépendances** :
- Module stock existant
- Module notifications existant

**Acceptation** :
- ✅ Alertes fonctionnelles
- ✅ Notifications envoyées

---

#### DR-014 : Module Gestion Absences (Basique)
**Type** : Critique Métier  
**Module** : RH  
**Effort estimé** : 5 jours  
**Délai** : 2 semaines  

**Description** :
- Saisie absences
- Validation absences
- Rapport absences

**Portée réduite** :
- ❌ Pas de calcul solde automatique (LOT 3)
- ✅ Saisie absences
- ✅ Validation
- ✅ Rapports

**Dépendances** :
- Module RH existant

**Acceptation** :
- ✅ Absences gérées
- ✅ Rapports générés

---

#### DR-018 : Calcul Automatique Solde Congé
**Type** : Critique Métier  
**Module** : RH  
**Effort estimé** : 4 jours  
**Délai** : 1 semaine  

**Description** :
- Calcul droits acquis
- Calcul congés pris
- Calcul solde restant

**Dépendances** :
- Module RH existant
- Module congés existant

**Acceptation** :
- ✅ Solde calculé automatiquement
- ✅ Historique maintenu

---

#### DR-016-B : Tests Frontend Complet
**Type** : Critique Métier  
**Module** : Frontend  
**Effort estimé** : 4 jours  
**Délai** : 2 semaines  

**Description** :
- Tests frontend complets (Jest, React Testing Library)
- Couverture > 80%

**Dépendances** :
- DR-016 (LOT 1) complété

**Acceptation** :
- ✅ Tests frontend complets
- ✅ Couverture > 80%

---

#### RECETTE-B : Exécution Scénarios Majeurs
**Type** : Critique Métier  
**Module** : Recette  
**Effort estimé** : 4 jours  
**Délai** : 2 semaines  

**Description** :
Exécuter scénarios de recette majeurs (178 scénarios) :
- Gestion stocks avancés (10 scénarios)
- Processus RH complets (15 scénarios)
- Workflows avancés (10 scénarios)
- Sécurité avancée (10 scénarios)
- Intégrations (133 scénarios)

**Dépendances** :
- Application en cours d'exécution
- Données de test préparées

**Acceptation** :
- ✅ 178 scénarios exécutés
- ✅ Résultats documentés

---

### Synthèse LOT 2

| Développement | Type | Effort | Délai |
|---------------|------|--------|-------|
| DR-001-B : Écritures comptables (complète) | Critique | 5 jours | 1 sem |
| DR-008 : Rate limiting étendu | Critique | 5 jours | 2 sem |
| DR-009-B : Audit logs complet | Critique | 4 jours | 1 sem |
| DR-010 : Notifications workflows | Critique | 8 jours | 2 sem |
| DR-011 : Délégation approbation (basique) | Critique | 3 jours | 1 sem |
| DR-012 : Module inventaire | Critique | 8 jours | 2 sem |
| DR-013 : Alertes stock (basique) | Critique | 4 jours | 1 sem |
| DR-014 : Gestion absences (basique) | Critique | 5 jours | 2 sem |
| DR-018 : Solde congé | Critique | 4 jours | 1 sem |
| DR-016-B : Tests frontend complet | Critique | 4 jours | 2 sem |
| RECETTE-B : Scénarios majeurs | Critique | 4 jours | 2 sem |
| **TOTAL** | | **50 jours** | **10 sem** |

---

## LOT 3 - OPTIMISATIONS ET FONCTIONNALITÉS AVANCÉES

**Objectif** : Maturité complète de la plateforme  
**Délai estimé** : 12 semaines (3 mois)  
**Effort total** : 60 jours

### Développements Confort Utilisateur

#### DR-006-B : Rotation Secrets JWT
**Type** : Confort Utilisateur  
**Module** : Authentification  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Rotation automatique secrets JWT
- Blacklist access tokens

**Dépendances** :
- DR-006 (LOT 1) complété

**Acceptation** :
- ✅ Rotation implémentée
- ✅ Blacklist implémentée

---

#### DR-005 : Valorisation Stock (FIFO, PMP, CUMP)
**Type** : Confort Utilisateur  
**Module** : Stock  
**Effort estimé** : 12 jours  
**Délai** : 3 semaines  

**Description** :
- Calcul FIFO
- Calcul PMP
- Calcul CUMP
- Valorisation stock total

**Dépendances** :
- Module stock existant

**Acceptation** :
- ✅ Calculs FIFO/PMP/CUMP
- ✅ Valorisation stock

---

#### DR-004 : Module Paie Complet
**Type** : Confort Utilisateur  
**Module** : RH  
**Effort estimé** : 20 jours  
**Délai** : 5 semaines  

**Description** :
- Calcul salaires
- Calcul cotisations sociales
- Calcul impôts
- Gestion bulletins de paie
- Versements
- Déclarations sociales

**Dépendances** :
- Module RH existant

**Acceptation** :
- ✅ Module paie complet
- ✅ Calculs corrects

---

#### DR-011-B : Délégation Approbation (Avancée)
**Type** : Confort Utilisateur  
**Module** : Workflows  
**Effort estimé** : 2 jours  
**Délai** : 1 semaine  

**Description** :
- Délégation permanente
- Workflows personnalisables

**Dépendances** :
- DR-011 (LOT 2) complété

**Acceptation** :
- ✅ Délégation avancée
- ✅ Workflows personnalisables

---

#### DR-013-B : Réapprovisionnement Automatique
**Type** : Confort Utilisateur  
**Module** : Stock  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Réapprovisionnement automatique basé sur seuils
- Génération commandes fournisseurs

**Dépendances** :
- DR-013 (LOT 2) complété

**Acceptation** :
- ✅ Réapprovisionnement automatique
- ✅ Commandes fournisseurs générées

---

#### DR-015 : Module Habilitations
**Type** : Confort Utilisateur  
**Module** : Sécurité  
**Effort estimé** : 10 jours  
**Délai** : 3 semaines  

**Description** :
- Permissions granulaires
- Gestion groupes
- Délégation droits
- Audit permissions

**Dépendances** :
- RBAC existant

**Acceptation** :
- ✅ Habilitations fonctionnelles
- ✅ Groupes gérés

---

#### DR-017-B : Tests de Charge Avancés
**Type** : Confort Utilisateur  
**Module** : Performance  
**Effort estimé** : 5 jours  
**Délai** : 2 semaines  

**Description** :
- Tests de charge avancés (1000 utilisateurs)
- Tests de scalabilité
- Tests de stress

**Dépendances** :
- DR-017 (LOT 1) complété

**Acceptation** :
- ✅ Tests charge avancés
- ✅ Scalabilité validée

---

### Développements Évolution Future

#### DR-014-B : Gestion Absences (Avancée)
**Type** : Évolution Future  
**Module** : RH  
**Effort estimé** : 3 jours  
**Délai** : 1 semaine  

**Description** :
- Calcul solde automatique
- Gestion heures supplémentaires
- Gestion notes de frais

**Dépendances** :
- DR-014 (LOT 2) complété

**Acceptation** :
- ✅ Absences avancées
- ✅ Solde automatique

---

#### DR-019 : Fonctionnalités Fleet Avancées
**Type** : Évolution Future  
**Module** : Logistique  
**Effort estimé** : 8 jours  
**Délai** : 2 semaines  

**Description** :
- Gestion carburant
- Gestion conducteurs
- Gestion itinéraires
- Géolocalisation

**Dépendances** :
- Module fleet existant

**Acceptation** :
- ✅ Fleet avancé
- ✅ Géolocalisation

---

#### DR-020 : Dashboard Avancé
**Type** : Évolution Future  
**Module** : Dashboard  
**Effort estimé** : 4 jours  
**Délai** : 1 semaine  

**Description** :
- Graphiques avancés
- Export données
- Personnalisation dashboard

**Dépendances** :
- Dashboard existant

**Acceptation** :
- ✅ Dashboard avancé
- ✅ Export fonctionnel

---

### Synthèse LOT 3

| Développement | Type | Effort | Délai |
|---------------|------|--------|-------|
| DR-006-B : Rotation JWT | Confort | 3 jours | 1 sem |
| DR-005 : Valorisation stock | Confort | 12 jours | 3 sem |
| DR-004 : Module paie | Confort | 20 jours | 5 sem |
| DR-011-B : Délégation avancée | Confort | 2 jours | 1 sem |
| DR-013-B : Réapprovisionnement | Confort | 3 jours | 1 sem |
| DR-015 : Habilitations | Confort | 10 jours | 3 sem |
| DR-017-B : Tests charge avancés | Confort | 5 jours | 2 sem |
| DR-014-B : Absences avancées | Évolution | 3 jours | 1 sem |
| DR-019 : Fleet avancé | Évolution | 8 jours | 2 sem |
| DR-020 : Dashboard avancé | Évolution | 4 jours | 1 sem |
| **TOTAL** | | **60 jours** | **12 sem** |

---

## SYNTHÈSE GLOBALE

### Récapitulatif par Lot

| Lot | Objectif | Développements | Effort | Délai | Décision |
|-----|----------|---------------|--------|-------|----------|
| LOT 1 | GO PRODUCTION MINIMUM VIABLE | 9 | 40 jours | 8 sem (2 mois) | GO après LOT 1 |
| LOT 2 | RENFORCEMENT FONCTIONNEL | 11 | 50 jours | 10 sem (2.5 mois) | Amélioration |
| LOT 3 | OPTIMISATIONS AVANCÉES | 10 | 60 jours | 12 sem (3 mois) | Maturité |
| **TOTAL** | | **30** | **150 jours** | **30 sem (7.5 mois)** | |

### Récapitulatif par Type

| Type | LOT 1 | LOT 2 | LOT 3 | Total |
|------|-------|-------|-------|-------|
| Bloquant Production | 9 | 0 | 0 | 9 |
| Critique Métier | 0 | 11 | 0 | 11 |
| Confort Utilisateur | 0 | 0 | 7 | 7 |
| Évolution Future | 0 | 0 | 3 | 3 |
| **TOTAL** | **9** | **11** | **10** | **30** |

---

## PLANNING RECOMMANDÉ

### Phase 1 - LOT 1 (Semaines 1-8)

**Semaine 1-2** :
- DR-006 : Sécurité JWT (2 jours)
- DR-007 : Sécurité CORS (1 jour)
- DR-003 : Intégration BR (5 jours)

**Semaine 3-4** :
- DR-002 : Intégration BL (8 jours)

**Semaine 5-6** :
- DR-001 : Écritures comptables simplifiées (10 jours)

**Semaine 7** :
- DR-009 : Audit logs simplifiés (6 jours)
- DR-016 : Audit frontend simplifié (3 jours)

**Semaine 8** :
- DR-017 : Tests charge minimum (3 jours)
- RECETTE : Scénarios critiques (2 jours)

**Milestone** : GO PRODUCTION MINIMUM VIABLE

---

### Phase 2 - LOT 2 (Semaines 9-18)

**Semaine 9-10** :
- DR-008 : Rate limiting étendu (5 jours)
- DR-011 : Délégation basique (3 jours)
- DR-018 : Solde congé (4 jours)

**Semaine 11-12** :
- DR-010 : Notifications workflows (8 jours)

**Semaine 13-14** :
- DR-012 : Module inventaire (8 jours)

**Semaine 15-16** :
- DR-014 : Gestion absences basique (5 jours)
- DR-013 : Alertes stock basique (4 jours)
- DR-009-B : Audit logs complet (4 jours)

**Semaine 17-18** :
- DR-001-B : Écritures comptables complètes (5 jours)
- DR-016-B : Tests frontend complet (4 jours)
- RECETTE-B : Scénarios majeurs (4 jours)

**Milestone** : RENFORCEMENT FONCTIONNEL

---

### Phase 3 - LOT 3 (Semaines 19-30)

**Semaine 19-20** :
- DR-005 : Valorisation stock (12 jours)

**Semaine 21-25** :
- DR-004 : Module paie (20 jours)

**Semaine 26-27** :
- DR-015 : Habilitations (10 jours)

**Semaine 28-29** :
- DR-017-B : Tests charge avancés (5 jours)
- DR-019 : Fleet avancé (8 jours)

**Semaine 30** :
- DR-006-B : Rotation JWT (3 jours)
- DR-011-B : Délégation avancée (2 jours)
- DR-013-B : Réapprovisionnement (3 jours)
- DR-014-B : Absences avancées (3 jours)
- DR-020 : Dashboard avancé (4 jours)

**Milestone** : MATURITÉ COMPLÈTE

---

## DÉCISION FINALE

### Critères GO PRODUCTION (LOT 1)

| Critère | Seuil | LOT 1 | Statut |
|---------|-------|-------|--------|
| Anomalies critiques | 0 | 0 | ✅ OK |
| Intégrations E2E basiques | 100% | 100% | ✅ OK |
| Sécurité basique | 100% | 100% | ✅ OK |
| Scénarios critiques exécutés | 100% | 100% | ✅ OK |
| Tests charge minimum | 100% | 100% | ✅ OK |
| Audit frontend basique | Complet | Complet | ✅ OK |

### Décision

**DÉCISION ACTUELLE** : **NO-GO PRODUCTION**

**DÉCISION APRÈS LOT 1** : **GO PRODUCTION MINIMUM VIABLE**

**Délai pour GO PRODUCTION** : 8 semaines (2 mois)

**Conditions GO PRODUCTION (LOT 1)** :
1. ✅ Génération automatique écritures comptables (simplifiée)
2. ✅ Intégration BL → Commande et Stock
3. ✅ Intégration BR → Stock
4. ✅ Sécurisation JWT
5. ✅ Correction CORS
6. ✅ Audit logs métier (simplifié)
7. ✅ Exécution recette fonctionnelle critique (47 scénarios)
8. ✅ Validation flux E2E basiques
9. ✅ Tests de charge minimum
10. ✅ Audit frontend (simplifié)

**Fonctionnalités reportées (LOT 2-3)** :
- Module paie complet
- Valorisation FIFO/PMP/CUMP
- Gestion absences avancée
- Habilitations granulaires
- Réapprovisionnement automatique
- Notifications évoluées
- Délégation avancée
- Fleet avancé
- Tests charge avancés

---

## CONCLUSION

L'approche par lots permet de réduire considérablement le délai avant la première mise en production :

- **LOT 1** : 8 semaines (2 mois) → GO PRODUCTION MINIMUM VIABLE
- **LOT 2** : 10 semaines (2.5 mois) → RENFORCEMENT FONCTIONNEL
- **LOT 3** : 12 semaines (3 mois) → MATURITÉ COMPLÈTE

**Délai total pour maturité complète** : 30 semaines (7.5 mois)

**Délai pour première mise en production** : 8 semaines (2 mois)

Cette approche réaliste permet de mettre l'ERP en exploitation rapidement tout en planifiant les améliorations futures de manière structurée.

---

**Document généré le** : 2 juin 2026  
**Version** : 1.0  
**Statut** : NO-GO PRODUCTION (actuel) → GO PRODUCTION après LOT 1
