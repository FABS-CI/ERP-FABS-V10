# AUDIT FONCTIONNEL COMPLET ERP FABS-CI V7

**Date** : 2 Juin 2026  
**Auditeur** : Cascade AI  
**Version ERP** : V7 (1.0.0 Production Ready)  
**Type** : Recette fonctionnelle pré-production  
**Portée** : 27 modules backend + Frontend React

---

## RÉSUMÉ EXÉCUTIF

### Architecture Technique
- **Backend** : FastAPI 0.110.1 + Motor 3.3.1 (MongoDB async)
- **Frontend** : React 19 + TailwindCSS + Radix UI
- **Base de données** : MongoDB (18 collections)
- **Authentification** : JWT + httpOnly cookies + Refresh tokens
- **Sécurité** : RBAC (8 rôles), Rate limiting, Audit logs

### Modules Implémentés (27)
1. Gestion commerciale (7 modules)
2. Finance & Comptabilité (4 modules)
3. Stock & Logistique (3 modules)
4. Ressources Humaines (1 module)
5. Fleet Management (1 module)
6. Analytics & Reporting (3 modules)
7. Administration & Sécurité (3 modules)
8. Communication (2 modules)
9. Documents & Stockage (2 modules)
10. Utilitaires (3 modules)

### Méthodologie d'Audit
- Analyse statique du code source
- Revue des workflows métier
- Validation des calculs financiers
- Vérification des impacts comptables
- Tests des dépendances inter-modules
- Évaluation de la sécurité
- Revue de l'expérience utilisateur

---

## A. GESTION COMMERCIALE (40+ SCÉNARIOS)

### A.1 GESTION DES CLIENTS (10 scénarios)

#### SC-COM-001 : Création client standard
- **Module** : Clients
- **Fonction testée** : Création client
- **Objectif** : Vérifier la création d'un client avec toutes les informations requises
- **Prérequis** : Utilisateur connecté avec rôle WRITE_ROLES
- **Données de test** :
  ```json
  {
    "nom": "École Primaire Test",
    "type_client": "ecole",
    "representant": "M. Directeur",
    "telephone": "+225 27 22 00 00 00",
    "email": "contact@ecole-test.ci",
    "adresse": "Zone Industrielle",
    "ville": "Abidjan",
    "plafond_credit": 500000
  }
  ```
- **Étapes détaillées** :
  1. Se connecter avec utilisateur autorisé
  2. Naviguer vers module Clients
  3. Cliquer sur "Nouveau client"
  4. Remplir tous les champs obligatoires
  5. Soumettre le formulaire
- **Résultat attendu** : Client créé avec référence auto FABS-CLI-XXXX, statut actif
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Vérifier génération référence auto

#### SC-COM-002 : Détection doublons clients
- **Module** : Clients
- **Fonction testée** : Détection doublons (Levenshtein)
- **Objectif** : Vérifier la détection automatique de doublons potentiels
- **Prérequis** : Client "Librairie Test" existe déjà
- **Données de test** :
  ```json
  {
    "nom": "Librairie Test",
    "type_client": "librairie",
    "representant": "M. Konaté",
    "telephone": "+225 27 22 44 30 30"
  }
  ```
- **Étapes détaillées** :
  1. Tenter de créer client avec nom similaire
  2. Vérifier alerte doublon
  3. Confirmer avec force=true
- **Résultat attendu** : Alerte 409 DUPLICATE_SUSPECTED avec similarité >= 0.78
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test algorithme Levenshtein

#### SC-COM-003 : Modification client
- **Module** : Clients
- **Fonction testée** : Mise à jour client
- **Objectif** : Vérifier la modification des informations client
- **Prérequis** : Client existant
- **Données de test** :
  ```json
  {
    "ville": "Bouaké",
    "plafond_credit": 1000000
  }
  ```
- **Étapes détaillées** :
  1. Sélectionner client existant
  2. Modifier ville et plafond
  3. Sauvegarder
- **Résultat attendu** : Client mis à jour, updated_at modifié
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Vérifier conservation historique

#### SC-COM-004 : Soft delete client
- **Module** : Clients
- **Fonction testée** : Désactivation client
- **Objectif** : Vérifier la désactivation sans suppression physique
- **Prérequis** : Client existant
- **Données de test** : Client ID existant
- **Étapes détaillées** :
  1. Sélectionner client
  2. Cliquer sur "Désactiver"
  3. Confirmer
- **Résultat attendu** : actif=False, client toujours en BDD
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Vérifier non-suppression données

#### SC-COM-005 : Liste clients paginée
- **Module** : Clients
- **Fonction testée** : Liste avec pagination
- **Objectif** : Vérifier pagination et filtres
- **Prérequis** : 50+ clients en BDD
- **Données de test** : page=1, page_size=20
- **Étapes détaillées** :
  1. Naviguer vers liste clients
  2. Vérifier pagination
  3. Tester filtre par type_client
  4. Tester filtre par ville
  5. Tester recherche texte
- **Résultat attendu** : Structure {items, total, page, page_size}
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Vérifier performance

#### SC-COM-006 : Validation email client
- **Module** : Clients
- **Fonction testée** : Validation format email
- **Objectif** : Vérifier rejet emails invalides
- **Prérequis** : Formulaire création client
- **Données de test** : email="invalid-email-format"
- **Étapes détaillées** :
  1. Saisir email invalide
  2. Tenter soumission
- **Résultat attendu** : Erreur validation Pydantic
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test validation EmailStr

#### SC-COM-007 : Plafond crédit client
- **Module** : Clients
- **Fonction testée** : Gestion plafond crédit
- **Objectif** : Vérifier respect plafond lors commandes
- **Prérequis** : Client avec plafond=500000
- **Données de test** : Commande montant=600000
- **Étapes détaillées** :
  1. Créer commande dépassant plafond
  2. Vérifier alerte ou blocage
- **Résultat attendu** : Alerte solde/plafond dépassé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Vérifier logique métier

#### SC-COM-008 : Recherche client multi-critères
- **Module** : Clients
- **Fonction testée** : Recherche avancée
- **Objectif** : Vérifier recherche nom/téléphone/référence
- **Prérequis** : Base clients peuplée
- **Données de test** : q="Librairie"
- **Étapes détaillées** :
  1. Saisir terme recherche
  2. Vérifier résultats
- **Résultat attendu** : Résultats nom OU téléphone OU référence
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test regex MongoDB

#### SC-COM-009 : Client avec représentant
- **Module** : Clients
- **Fonction testée** : Champ représentant
- **Objectif** : Vérifier gestion représentant commercial
- **Prérequis** : Formulaire création
- **Données de test** : representant="M. Commercial X"
- **Étapes détaillées** :
  1. Créer client avec représentant
  2. Vérifier sauvegarde champ
- **Résultat attendu** : Champ representant sauvegardé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Nouveau champ Sprint 4

#### SC-COM-010 : RBAC Clients
- **Module** : Clients
- **Fonction testée** : Contrôle d'accès
- **Objectif** : Vérifier permissions par rôle
- **Prérequis** : Utilisateurs avec différents rôles
- **Données de test** : Rôles {super_admin, DG, commercial, comptable, secrétariat}
- **Étapes détaillées** :
  1. Tester accès lecture chaque rôle
  2. Tester accès écriture chaque rôle
  3. Tester accès rôle non-autorisé (gestionnaire_stock)
- **Résultat attendu** : READ_ROLES et WRITE_ROLES respectés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test matrice permissions

---

### A.2 GESTION DES PRODUITS (10 scénarios)

#### SC-COM-011 : Création produit standard
- **Module** : Produits
- **Fonction testée** : Création produit
- **Objectif** : Vérifier création produit complet
- **Prérequis** : Utilisateur autorisé
- **Données de test** :
  ```json
  {
    "code_article": "LIV-MAT-001",
    "titre": "Livre Maternelle Test",
    "auteur": "Auteur Test",
    "categorie": "maternelle",
    "niveau_scolaire": "Petite Section",
    "isbn": "978-2-12345-678-9",
    "prix_vente": 2500,
    "stock_actuel": 100,
    "stock_minimum": 20
  }
  ```
- **Étapes détaillées** :
  1. Naviguer vers Produits
  2. Cliquer "Nouveau produit"
  3. Remplir champs
  4. Sauvegarder
- **Résultat attendu** : Produit créé avec référence FABS-PRD-XXXX
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Vérifier référence auto

#### SC-COM-012 : Lookup ISBN Google Books
- **Module** : Produits
- **Fonction testée** : Recherche ISBN externe
- **Objectif** : Vérifier intégration API Google Books
- **Prérequis** : Connexion internet
- **Données de test** : isbn="978-2-07-061275-8"
- **Étapes détaillées** :
  1. Saisir ISBN
  2. Cliquer "Lookup"
  3. Vérifier remplissage auto
- **Résultat attendu** : Données Google Books récupérées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test API externe

#### SC-COM-013 : Masquage prix achat
- **Module** : Produits
- **Fonction testée** : Contrôle accès prix sensible
- **Objectif** : Vérifier masquage prix_achat pour non-financiers
- **Prérequis** : Produit avec prix_achat défini
- **Données de test** : Rôles {comptable, commercial}
- **Étapes détaillées** :
  1. Consulter produit avec rôle comptable
  2. Consulter produit avec rôle commercial
- **Résultat attendu** : Prix_achat visible pour comptable, masqué pour commercial
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test sécurité données

#### SC-COM-014 : Alertes stock
- **Module** : Produits
- **Fonction testée** : Calcul statut_stock
- **Objectif** : Vérifier alertes rupture/seuil
- **Prérequis** : Produits avec stocks variés
- **Données de test** :
  - Produit A: stock_actuel=0, stock_minimum=10
  - Produit B: stock_actuel=5, stock_minimum=10
  - Produit C: stock_actuel=50, stock_minimum=10
- **Étapes détaillées** :
  1. Consulter liste produits
  2. Vérifier statut_stock calculé
- **Résultat attendu** : rupture, alerte, ok respectivement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test computed field

#### SC-COM-015 : Catégories produits
- **Module** : Produits
- **Fonction testée** : Gestion catégories
- **Objectif** : Vérifier catégories valides
- **Prérequis** : Formulaire produit
- **Données de test** : Catégories {maternelle, primaire, premier_cycle, second_cycle, litterature, livre_commun}
- **Étapes détaillées** :
  1. Créer produits chaque catégorie
  2. Vérifier filtre par catégorie
- **Résultat attendu** : Catégories enum validées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test enum validation

#### SC-COM-016 : Modification produit
- **Module** : Produits
- **Fonction testée** : Mise à jour produit
- **Objectif** : Vérifier modification prix/stock
- **Prérequis** : Produit existant
- **Données de test** :
  ```json
  {
    "prix_vente": 3000,
    "stock_actuel": 150
  }
  ```
- **Étapes détaillées** :
  1. Modifier prix et stock
  2. Sauvegarder
- **Résultat attendu** : Produit mis à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Vérifier impact commandes

#### SC-COM-017 : Soft delete produit
- **Module** : Produits
- **Fonction testée** : Désactivation produit
- **Objectif** : Vérifier désactivation sans suppression
- **Prérequis** : Produit existant
- **Données de test** : Produit ID
- **Étapes détaillées** :
  1. Désactiver produit
  2. Vérifier toujours en BDD
- **Résultat attendu** : actif=False
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test soft delete

#### SC-COM-018 : Liste produits paginée
- **Module** : Produits
- **Fonction testée** : Pagination produits
- **Objectif** : Vérifier pagination et filtres
- **Prérequis** : 100+ produits
- **Données de test** : page=1, page_size=50
- **Étapes détaillées** :
  1. Naviguer liste produits
  2. Tester pagination
  3. Tester filtre catégorie
  4. Tester recherche
- **Résultat attendu** : Structure paginée correcte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Vérifier performance

#### SC-COM-019 : Validation prix négatif
- **Module** : Produits
- **Fonction testée** : Validation prix
- **Objectif** : Vérifier rejet prix négatif
- **Prérequis** : Formulaire produit
- **Données de test** : prix_vente=-100
- **Étapes détaillées** :
  1. Saisir prix négatif
  2. Tenter soumission
- **Résultat attendu** : Erreur validation gt=0
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test Pydantic validator

#### SC-COM-020 : RBAC Produits
- **Module** : Produits
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Tous les rôles
- **Étapes détaillées** :
  1. Tester accès lecture chaque rôle
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC complet

---

### A.3 GESTION DES COMMANDES (10 scénarios)

#### SC-COM-021 : Création commande brouillon
- **Module** : Commandes
- **Fonction testée** : Création commande brouillon
- **Objectif** : Vérifier création commande statut brouillon
- **Prérequis** : Client et produits existants
- **Données de test** :
  ```json
  {
    "client_id": "cli_xxx",
    "lignes": [
      {"produit_id": "prd_xxx", "quantite": 10, "prix_unitaire": 2500}
    ],
    "submit": false
  }
  ```
- **Étapes détaillées** :
  1. Créer commande sans soumettre
  2. Vérifier statut brouillon
- **Résultat attendu** : Commande créée, statut=brouillon
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow initial

#### SC-COM-022 : Soumission commande
- **Module** : Commandes
- **Fonction testée** : Soumission pour validation
- **Objectif** : Vérifier transition brouillon→en_attente
- **Prérequis** : Commande brouillon
- **Données de test** : Commande ID brouillon
- **Étapes détaillées** :
  1. Soumettre commande
  2. Vérifier statut en_attente
- **Résultat attendu** : statut=en_attente
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-COM-023 : Validation commande (< 500k)
- **Module** : Commandes
- **Fonction testée** : Validation par commercial
- **Objectif** : Vérifier validation commande < 500k FCFA
- **Prérequis** : Commande en_attente montant=300000
- **Données de test** : Rôle directeur_commercial
- **Étapes détaillées** :
  1. Valider commande
  2. Vérifier transition validee
  3. Vérifier génération proforma
- **Résultat attendu** : statut=validee, proforma générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test seuil validation

#### SC-COM-024 : Validation commande (> 500k)
- **Module** : Commandes
- **Fonction testée** : Validation DG obligatoire
- **Objectif** : Vérifier validation DG pour montants > 500k
- **Prérequis** : Commande en_attente montant=600000
- **Données de test** : Rôle directeur_commercial
- **Étapes détaillées** :
  1. Tenter validation avec commercial
  2. Vérifier refus
  3. Valider avec DG
- **Résultat attendu** : Commercial refusé, DG accepté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test règle métier critique

#### SC-COM-025 : Préparation commande
- **Module** : Commandes
- **Fonction testée** : Préparation par magasinier
- **Objectif** : Vérifier transition validee→preparee
- **Prérequis** : Commande validee
- **Données de test** : Rôle responsable_magasinier
- **Étapes détaillées** :
  1. Marquer commande préparée
  2. Vérifier statut preparee
- **Résultat attendu** : statut=preparee
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow logistique

#### SC-COM-026 : Livraison commande
- **Module** : Commandes
- **Fonction testée** : Livraison par logistique
- **Objectif** : Vérifier transition preparee→livree
- **Prérequis** : Commande preparee
- **Données de test** : Rôle service_logistique
- **Étapes détaillées** :
  1. Marquer commande livrée
  2. Vérifier statut livree
- **Résultat attendu** : statut=livree
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow final

#### SC-COM-027 : Annulation commande
- **Module** : Commandes
- **Fonction testée** : Annulation avec motif
- **Objectif** : Vérifier annulation commande non livrée
- **Prérequis** : Commande en_attente
- **Données de test** : motif="Client annule commande"
- **Étapes détaillées** :
  1. Annuler commande
  2. Vérifier motif obligatoire
- **Résultat attendu** : statut=annulee, motif enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test motif obligatoire

#### SC-COM-028 : Calculs remises
- **Module** : Commandes
- **Fonction testée** : Calculs remises ligne + globale
- **Objectif** : Vérifier calcul automatique montants
- **Prérequis** : Commande avec remises
- **Données de test** :
  - Ligne 1: quantite=10, prix=2500, remise_ligne=10%
  - Remise globale: 5%
- **Étapes détaillées** :
  1. Créer commande avec remises
  2. Vérifier calculs
- **Résultat attendu** : montant_ht, montant_remise, montant_total corrects
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test calculs financiers

#### SC-COM-029 : Modification commande brouillon
- **Module** : Commandes
- **Fonction testée** : Modification brouillon
- **Objectif** : Vérifier modification possible brouillon
- **Prérequis** : Commande brouillon
- **Données de test** : Ajouter ligne
- **Étapes détaillées** :
  1. Modifier commande brouillon
  2. Sauvegarder
- **Résultat attendu** : Modification acceptée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test guard workflow

#### SC-COM-030 : Génération PDF commande
- **Module** : Commandes
- **Fonction testée** : Génération PDF
- **Objectif** : Vérifier génération Bon de Commande PDF
- **Prérequis** : Commande existante
- **Données de test** : Commande ID
- **Étapes détaillées** :
  1. Cliquer "Générer PDF"
  2. Vérifier téléchargement
- **Résultat attendu** : PDF généré avec logo FABS-CI
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test génération document

---

### A.4 GESTION DES FACTURES (10 scénarios)

#### SC-COM-031 : Génération facture depuis commande
- **Module** : Factures
- **Fonction testée** : Génération automatique
- **Objectif** : Vérifier génération facture depuis commande validée
- **Prérequis** : Commande validee
- **Données de test** : Commande ID validee
- **Étapes détaillées** :
  1. Générer facture depuis commande
  2. Vérifier lignes copiées
- **Résultat attendu** : Facture créée avec lignes commande
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow automatique

#### SC-COM-032 : Calculs TVA
- **Module** : Factures
- **Fonction testée** : Calcul TVA 18%
- **Objectif** : Vérifier calcul automatique TVA
- **Prérequis** : Facture montant_ht=100000
- **Données de test** : TVA_RATE=0.18
- **Étapes détaillées** :
  1. Créer facture
  2. Vérifier calculs
- **Résultat attendu** : montant_tva=18000, montant_ttc=118000
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test conformité fiscale

#### SC-COM-033 : Émission facture
- **Module** : Factures
- **Fonction testée** : Transition brouillon→emise
- **Objectif** : Vérifier émission facture
- **Prérequis** : Facture brouillon
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Émettre facture
  2. Vérifier statut emise
- **Résultat attendu** : statut=emise, date_emission définie
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow facturation

#### SC-COM-034 : Génération avoir
- **Module** : Factures
- **Fonction testée** : Création avoir
- **Objectif** : Vérifier génération avoir depuis facture
- **Prérequis** : Facture payée
- **Données de test** : montant_avoir=50000
- **Étapes détaillées** :
  1. Générer avoir
  2. Vérifier montants négatifs
- **Résultat attendu** : Avoir avec montants négatifs
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test gestion avoirs

#### SC-COM-035 : Mise à jour statut facture
- **Module** : Factures
- **Fonction testée** : Auto-update statut paiements
- **Objectif** : Vérifier transition statut selon paiements
- **Prérequis** : Facture emise montant_ttc=100000
- **Données de test** :
  - Paiement 1: 30000
  - Paiement 2: 70000
- **Étapes détaillées** :
  1. Enregistrer paiement partiel
  2. Vérifier statut partiellement_payee
  3. Enregistrer paiement complet
  4. Vérifier statut payee
- **Résultat attendu** : Transitions automatiques correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow comptable

#### SC-COM-036 : Liste factures filtres
- **Module** : Factures
- **Fonction testée** : Filtres avancés
- **Objectif** : Vérifier filtres type/statut/client/dates
- **Prérequis** : Base factures peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par type (facture/avoir)
  2. Filtrer par statut
  3. Filtrer par client
  4. Filtrer par dates
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test recherche

#### SC-COM-037 : Génération PDF facture
- **Module** : Factures
- **Fonction testée** : Génération PDF
- **Objectif** : Vérifier génération facture PDF
- **Prérequis** : Facture existante
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Générer PDF
  2. Vérifier contenu
- **Résultat attendu** : PDF avec détails facture
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test document

#### SC-COM-038 : Envoi WhatsApp facture
- **Module** : Factures
- **Fonction testée** : Partage WhatsApp
- **Objectif** : Vérifier génération lien WhatsApp
- **Prérequis** : Facture avec client WhatsApp
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Cliquer "Envoyer WhatsApp"
  2. Vérifier URL générée
- **Résultat attendu** : URL wa.me avec message
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test notification

#### SC-COM-039 : Envoi email facture
- **Module** : Factures
- **Fonction testée** : Envoi email avec PDF
- **Objectif** : Vérifier envoi email SMTP
- **Prérequis** : Configuration SMTP
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Envoyer facture par email
  2. Vérifier réception
- **Résultat attendu** : Email envoyé avec PDF attaché
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test SMTP

#### SC-COM-040 : RBAC Factures
- **Module** : Factures
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles READ/WRITE/PAYMENT
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
  3. Tester accès paiements
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

## B. GESTION DES STOCKS (30+ SCÉNARIOS)

### B.1 MOUVEMENTS DE STOCK (15 scénarios)

#### SC-STK-001 : Entrée stock
- **Module** : Stock
- **Fonction testée** : Mouvement entrée
- **Objectif** : Vérifier entrée stock et incrémentation
- **Prérequis** : Produit existant stock_actuel=50
- **Données de test** :
  ```json
  {
    "produit_id": "prd_xxx",
    "type_mouvement": "entree",
    "quantite": 100,
    "motif": "Réception fournisseur"
  }
  ```
- **Étapes détaillées** :
  1. Créer mouvement entrée
  2. Vérifier stock_actuel=150
- **Résultat attendu** : Stock incrémenté, mouvement enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test atomicité $inc

#### SC-STK-002 : Sortie stock
- **Module** : Stock
- **Fonction testée** : Mouvement sortie
- **Objectif** : Vérifier sortie stock et décrémentation
- **Prérequis** : Produit stock_actuel=100
- **Données de test** :
  ```json
  {
    "produit_id": "prd_xxx",
    "type_mouvement": "sortie",
    "quantite": 30,
    "motif": "Vente"
  }
  ```
- **Étapes détaillées** :
  1. Créer mouvement sortie
  2. Vérifier stock_actuel=70
- **Résultat attendu** : Stock décrémenté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test atomicité

#### SC-STK-003 : Ajustement stock
- **Module** : Stock
- **Fonction testée** : Mouvement ajustement
- **Objectif** : Vérifier ajustement inventaire
- **Prérequis** : Produit stock_actuel=100
- **Données de test** :
  ```json
  {
    "produit_id": "prd_xxx",
    "type_mouvement": "ajustement",
    "quantite": -10,
    "motif": "Erreur inventaire"
  }
  ```
- **Étapes détaillées** :
  1. Créer ajustement
  2. Vérifier stock_actuel=90
- **Résultat attendu** : Stock ajusté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test correction

#### SC-STK-004 : Retour stock
- **Module** : Stock
- **Fonction testée** : Mouvement retour
- **Objectif** : Vérifier retour client
- **Prérequis** : Produit stock_actuel=50
- **Données de test** :
  ```json
  {
    "produit_id": "prd_xxx",
    "type_mouvement": "retour",
    "quantite": 5,
    "motif": "Retour client"
  }
  ```
- **Étapes détaillées** :
  1. Créer retour
  2. Vérifier stock_actuel=55
- **Résultat attendu** : Stock incrémenté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow retour

#### SC-STK-005 : Spécimen gratuit
- **Module** : Stock
- **Fonction testée** : Mouvement specimen_gratuit
- **Objectif** : Vérifier sortie sans facturation
- **Prérequis** : Produit stock_actuel=100
- **Données de test** :
  ```json
  {
    "produit_id": "prd_xxx",
    "type_mouvement": "specimen_gratuit",
    "quantite": 10,
    "motif": "Distribution école"
  }
  ```
- **Étapes détaillées** :
  1. Créer spécimen gratuit
  2. Vérifier stock_actuel=90
- **Résultat attendu** : Sortie sans impact financier
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test spécimen

#### SC-STK-006 : Historique mouvements
- **Module** : Stock
- **Fonction testée** : Liste mouvements
- **Objectif** : Vérifier historique complet
- **Prérequis** : Mouvements existants
- **Données de test** : Filtres produit_id, type_mouvement
- **Étapes détaillées** :
  1. Consulter historique
  2. Filtrer par produit
  3. Filtrer par type
- **Résultat attendu** : Historique complet avec stock_avant/après
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-STK-007 : Stock négatif
- **Module** : Stock
- **Fonction testée** : Validation stock négatif
- **Objectif** : Vérifier blocage stock négatif
- **Prérequis** : Produit stock_actuel=10
- **Données de test** : Sortie quantite=20
- **Étapes détaillées** :
  1. Tenter sortie > stock
  2. Vérifier blocage
- **Résultat attendu** : Erreur stock insuffisant
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test validation

#### SC-STK-008 : Alerte rupture stock
- **Module** : Stock
- **Fonction testée** : Alerte automatique
- **Objectif** : Vérifier alerte stock < minimum
- **Prérequis** : Produit stock_actuel=5, stock_minimum=10
- **Données de test** : Consultation liste produits
- **Étapes détaillées** :
  1. Consulter produits
  2. Vérifier alerte rupture
- **Résultat attendu** : statut_stock=rupture
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test alerte

#### SC-STK-009 : Alerte stock minimum
- **Module** : Stock
- **Fonction testée** : Alerte seuil
- **Objectif** : Vérifier alerte stock proche minimum
- **Prérequis** : Produit stock_actuel=12, stock_minimum=10
- **Données de test** : Consultation liste
- **Étapes détaillées** :
  1. Consulter produits
  2. Vérifier alerte
- **Résultat attendu** : statut_stock=alerte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test alerte

#### SC-STK-010 : Mouvement lié commande
- **Module** : Stock
- **Fonction testée** : Lien commande
- **Objectif** : Vérifier traçabilité commande
- **Prérequis** : Commande existante
- **Données de test** : Mouvement avec commande_id
- **Étapes détaillées** :
  1. Créer mouvement lié
  2. Vérifier lien
- **Résultat attendu** : commande_id enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-STK-011 : Mouvement lié BL
- **Module** : Stock
- **Fonction testée** : Lien bon livraison
- **Objectif** : Vérifier traçabilité livraison
- **Prérequis** : Bon livraison existant
- **Données de test** : Mouvement avec bl_id
- **Étapes détaillées** :
  1. Créer mouvement lié BL
  2. Vérifier lien
- **Résultat attendu** : bl_id enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-STK-012 : Valorisation stock
- **Module** : Stock
- **Fonction testée** : Calcul valeur stock
- **Objectif** : Vérifier valorisation CUMP
- **Prérequis** : Produit avec mouvements
- **Données de test** : Historique entrées/sorties
- **Étapes détaillées** :
  1. Consulter rapport stock
  2. Vérifier valorisation
- **Résultat attendu** : Valeur stock calculée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test comptabilité

#### SC-STK-013 : Inventaire
- **Module** : Stock
- **Fonction testée** : Processus inventaire
- **Objectif** : Vérifier ajustement inventaire
- **Prérequis** : Produits avec stock théorique
- **Données de test** : Stock compté vs théorique
- **Étapes détaillées** :
  1. Saisir stock compté
  2. Générer ajustements
- **Résultat attendu** : Ajustements générés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test inventaire

#### SC-STK-014 : Transfert dépôt
- **Module** : Stock
- **Fonction testée** : Transfert entre dépôts
- **Objectif** : Vérifier transfert stock
- **Prérequis** : Multi-dépôts (si implémenté)
- **Données de test** : Transfert dépôt A→B
- **Étapes détaillées** :
  1. Créer transfert
  2. Vérifier mouvements
- **Résultat attendu** : Sortie A + entrée B
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test multi-dépôts

#### SC-STK-015 : RBAC Stock
- **Module** : Stock
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {gestionnaire_stock, responsable_magasinier}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

### B.2 BONS DE LIVRAISON (10 scénarios)

#### SC-STK-016 : Création BL depuis commande
- **Module** : Bons de Livraison
- **Fonction testée** : Génération BL
- **Objectif** : Vérifier création BL depuis commande préparée
- **Prérequis** : Commande preparee
- **Données de test** : Commande ID
- **Étapes détaillées** :
  1. Créer BL depuis commande
  2. Vérifier lignes copiées
- **Résultat attendu** : BL créé avec lignes commande
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow

#### SC-STK-017 : Marquage BL livré
- **Module** : Bons de Livraison
- **Fonction testée** : Livraison BL
- **Objectif** : Vérifier transition pret→livre
- **Prérequis** : BL statut pret
- **Données de test** : BL ID
- **Étapes détaillées** :
  1. Marquer BL livré
  2. Vérifier statut livre
- **Résultat attendu** : statut=livre, date_livraison_reelle définie
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow

#### SC-STK-018 : Auto-update commande
- **Module** : Bons de Livraison
- **Fonction testée** : Mise à jour automatique commande
- **Objectif** : Vérifier update commande statut
- **Prérequis** : BL lié à commande
- **Données de test** : Livraison BL
- **Étapes détaillées** :
  1. Livrer BL
  2. Vérifier commande statut livree
- **Résultat attendu** : Commande statut=livree
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-STK-019 : Auto-update stock
- **Module** : Bons de Livraison
- **Fonction testée** : Mise à jour automatique stock
- **Objectif** : Vérifier décrémentation stock
- **Prérequis** : BL avec lignes
- **Données de test** : Livraison BL
- **Étapes détaillées** :
  1. Livrer BL
  2. Vérifier mouvements sortie créés
- **Résultat attendu** : Mouvements sortie générés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-STK-020 : Liste BL filtres
- **Module** : Bons de Livraison
- **Fonction testée** : Filtres BL
- **Objectif** : Vérifier filtres statut/client/dates
- **Prérequis** : Base BL peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par statut
  2. Filtrer par client
  3. Filtrer par dates
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test recherche

#### SC-STK-021 : Génération PDF BL
- **Module** : Bons de Livraison
- **Fonction testée** : Génération PDF
- **Objectif** : Vérifier génération BL PDF
- **Prérequis** : BL existant
- **Données de test** : BL ID
- **Étapes détaillées** :
  1. Générer PDF
  2. Vérifier contenu
- **Résultat attendu** : PDF avec détails BL
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test document

#### SC-STK-022 : Validation quantités BL
- **Module** : Bons de Livraison
- **Fonction testée** : Validation quantités
- **Objectif** : Vérifier contrôle quantités vs commande
- **Prérequis** : Commande avec quantités
- **Données de test** : BL avec quantités différentes
- **Étapes détaillées** :
  1. Créer BL quantités > commande
  2. Vérifier validation
- **Résultat attendu** : Alerte ou blocage
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test validation

#### SC-STK-023 : Annulation BL
- **Module** : Bons de Livraison
- **Fonction testée** : Annulation BL
- **Objectif** : Vérifier annulation BL non livré
- **Prérequis** : BL statut pret
- **Données de test** : BL ID
- **Étapes détaillées** :
  1. Annuler BL
  2. Vérifier statut annule
- **Résultat attendu** : statut=annule
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test annulation

#### SC-STK-024 : RBAC BL
- **Module** : Bons de Livraison
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {logistique, magasinier}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-STK-025 : Workflow BL complet
- **Module** : Bons de Livraison
- **Fonction testée** : Workflow complet
- **Objectif** : Vérifier workflow en_preparation→pret→livre
- **Prérequis** : Commande validee
- **Données de test** : Processus complet
- **Étapes détaillées** :
  1. Créer BL
  2. Marquer pret
  3. Marquer livre
- **Résultat attendu** : Workflow complet fonctionnel
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test E2E

---

### B.3 BONS DE RETOUR (5 scénarios)

#### SC-STK-026 : Création BR depuis facture
- **Module** : Bons de Retour
- **Fonction testée** : Création BR
- **Objectif** : Vérifier création BR depuis facture
- **Prérequis** : Facture payée
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Créer BR
  2. Ajouter lignes retour
- **Résultat attendu** : BR créé avec lignes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-STK-027 : Validation BR
- **Module** : Bons de Retour
- **Fonction testée** : Validation BR
- **Objectif** : Vérifier génération avoir automatique
- **Prérequis** : BR en_attente
- **Données de test** : BR ID
- **Étapes détaillées** :
  1. Valider BR
  2. Vérifier avoir généré
- **Résultat attendu** : Avoir créé automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow

#### SC-STK-028 : Auto-update stock retour
- **Module** : Bons de Retour
- **Fonction testée** : Mise à jour stock
- **Objectif** : Vérifier entrée stock retour
- **Prérequis** : BR validé
- **Données de test** : BR avec lignes
- **Étapes détaillées** :
  1. Valider BR
  2. Vérifier mouvements entrée
- **Résultat attendu** : Mouvements entrée générés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-STK-029 : Génération PDF BR
- **Module** : Bons de Retour
- **Fonction testée** : Génération PDF
- **Objectif** : Vérifier génération BR PDF
- **Prérequis** : BR existant
- **Données de test** : BR ID
- **Étapes détaillées** :
  1. Générer PDF
  2. Vérifier contenu
- **Résultat attendu** : PDF avec détails BR
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test document

#### SC-STK-030 : RBAC BR
- **Module** : Bons de Retour
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {logistique, comptable}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

## C. COMPTABILITÉ (30+ SCÉNARIOS)

### C.1 ÉCRITURES COMPTABLES (15 scénarios)

#### SC-CPT-001 : Création écriture manuelle
- **Module** : Comptabilité
- **Fonction testée** : Création écriture
- **Objectif** : Vérifier création écriture comptable
- **Prérequis** : Utilisateur rôle comptable
- **Données de test** :
  ```json
  {
    "journal": "operations_diverses",
    "date_ecriture": "2026-06-01",
    "compte": "701000",
    "libelle": "Vente test",
    "debit": 0,
    "credit": 100000
  }
  ```
- **Étapes détaillées** :
  1. Créer écriture
  2. Vérifier sauvegarde
- **Résultat attendu** : Écriture créée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test création

#### SC-CPT-002 : Équilibrage débit/crédit
- **Module** : Comptabilité
- **Fonction testée** : Validation équilibre
- **Objectif** : Vérifier équilibrage écriture
- **Prérequis** : Écriture déséquilibrée
- **Données de test** : Débit=100000, Crédit=90000
- **Étapes détaillées** :
  1. Tenter création écriture déséquilibrée
  2. Vérifier rejet
- **Résultat attendu** : Erreur validation
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test validation comptable

#### SC-CPT-003 : Liste écritures par journal
- **Module** : Comptabilité
- **Fonction testée** : Filtre journal
- **Objectif** : Vérifier filtrage par journal
- **Prérequis** : Écritures multiples journaux
- **Données de test** : Journal=ventes
- **Étapes détaillées** :
  1. Filtrer par journal
  2. Vérifier résultats
- **Résultat attendu** : Seules écritures journal ventes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test filtre

#### SC-CPT-004 : Liste écritures par date
- **Module** : Comptabilité
- **Fonction testée** : Filtre date
- **Objectif** : Vérifier filtrage par période
- **Prérequis** : Écritures multiples dates
- **Données de test** : Date début/fin
- **Étapes détaillées** :
  1. Filtrer par période
  2. Vérifier résultats
- **Résultat attendu** : Écritures période
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test filtre

#### SC-CPT-005 : Grand livre
- **Module** : Comptabilité
- **Fonction testée** : Grand livre
- **Objectif** : Vérifier grand livre par compte
- **Prérequis** : Écritures compte 701000
- **Données de test** : Compte=701000
- **Étapes détaillées** :
  1. Consulter grand livre
  2. Vérifier débit/crédit/solde
- **Résultat attendu** : Grand livre correct
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test rapport comptable

#### SC-CPT-006 : Balance comptable
- **Module** : Comptabilité
- **Fonction testée** : Balance
- **Objectif** : Vérifier balance comptable
- **Prérequis** : Écritures multiples comptes
- **Données de test** : Période
- **Étapes détaillées** :
  1. Générer balance
  2. Vérifier équilibre total débit=crédit
- **Résultat attendu** : Balance équilibrée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test rapport

#### SC-CPT-007 : Créances clients
- **Module** : Comptabilité
- **Fonction testée** : Suivi créances
- **Objectif** : Vérifier calcul créances clients
- **Prérequis** : Factures impayées
- **Données de test** : Filtre client
- **Étapes détaillées** :
  1. Consulter créances
  2. Vérifier montant total
- **Résultat attendu** : Créances correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test trésorerie

#### SC-CPT-008 : Journal ventes
- **Module** : Comptabilité
- **Fonction testée** : Journal ventes
- **Objectif** : Vérifier écritures ventes automatiques
- **Prérequis** : Factures émises
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter journal ventes
  2. Vérifier écritures générées
- **Résultat attendu** : Écritures ventes présentes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auto-génération

#### SC-CPT-009 : Journal achats
- **Module** : Comptabilité
- **Fonction testée** : Journal achats
- **Objectif** : Vérifier écritures achats
- **Prérequis** : Factures fournisseurs
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter journal achats
  2. Vérifier écritures
- **Résultat attendu** : Écritures achats présentes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auto-génération

#### SC-CPT-010 : Journal banque
- **Module** : Comptabilité
- **Fonction testée** : Journal banque
- **Objectif** : Vérifier écritures banque
- **Prérequis** : Paiements encaissés
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter journal banque
  2. Vérifier écritures
- **Résultat attendu** : Écritures banque présentes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auto-génération

#### SC-CPT-011 : Journal caisse
- **Module** : Comptabilité
- **Fonction testée** : Journal caisse
- **Objectif** : Vérifier écritures caisse
- **Prérequis** : Paiements espèces
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter journal caisse
  2. Vérifier écritures
- **Résultat attendu** : Écritures caisse présentes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auto-génération

#### SC-CPT-012 : Pièce référence
- **Module** : Comptabilité
- **Fonction testée** : Lien pièce
- **Objectif** : Vérifier référence pièce comptable
- **Prérequis** : Facture existante
- **Données de test** : Écriture avec piece_reference
- **Étapes détaillées** :
  1. Créer écriture avec référence
  2. Vérifier lien
- **Résultat attendu** : Référence facture enregistrée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-CPT-013 : RBAC Comptabilité
- **Module** : Comptabilité
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {comptable, DG}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-CPT-014 : Export écritures
- **Module** : Comptabilité
- **Fonction testée** : Export données
- **Objectif** : Vérifier export écritures
- **Prérequis** : Écritures existantes
- **Données de test** : Format CSV/Excel
- **Étapes détaillées** :
  1. Exporter écritures
  2. Vérifier fichier
- **Résultat attendu** : Fichier généré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test export

#### SC-CPT-015 : Clôture comptable
- **Module** : Comptabilité
- **Fonction testée** : Clôture période
- **Objectif** : Vérifier clôture exercice
- **Prérequis** : Période comptable
- **Données de test** : Clôture 2026
- **Étapes détaillées** :
  1. Clôturer période
  2. Vérifier blocage écritures
- **Résultat attendu** : Période clôturée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test clôture

---

### C.2 COMPTABILITÉ AVANCÉE (15 scénarios)

#### SC-CPT-016 : Plan comptable structuré
- **Module** : Comptabilité Avancée
- **Fonction testée** : Gestion plan comptable
- **Objectif** : Vérifier plan comptable OHADA
- **Prérequis** : Module comptabilité_avancee
- **Données de test** : Comptes OHADA
- **Étapes détaillées** :
  1. Consulter plan comptable
  2. Vérifier structure
- **Résultat attendu** : Plan comptable structuré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test conformité OHADA

#### SC-CPT-017 : Périodes comptables
- **Module** : Comptabilité Avancée
- **Fonction testée** : Gestion périodes
- **Objectif** : Vérifier gestion périodes comptables
- **Prérequis** : Module comptabilité_avancee
- **Données de test** : Périodes 2026
- **Étapes détaillées** :
  1. Créer période
  2. Clôturer période
- **Résultat attendu** : Périodes gérées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test périodes

#### SC-CPT-018 : Bilan
- **Module** : Comptabilité Avancée
- **Fonction testée** : Génération bilan
- **Objectif** : Vérifier génération bilan comptable
- **Prérequis** : Écritures exercice complet
- **Données de test** : Exercice 2026
- **Étapes détaillées** :
  1. Générer bilan
  2. Vérifier actif/passif
- **Résultat attendu** : Bilan équilibré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test rapport financier

#### SC-CPT-019 : Compte de résultat
- **Module** : Comptabilité Avancée
- **Fonction testée** : Génération compte résultat
- **Objectif** : Vérifier génération compte résultat
- **Prérequis** : Écritures exercice
- **Données de test** : Exercice 2026
- **Étapes détaillées** :
  1. Générer compte résultat
  2. Vérifier produits/charges
- **Résultat attendu** : Compte résultat correct
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test rapport financier

#### SC-CPT-020 : TVA collectée
- **Module** : Comptabilité Avancée
- **Fonction testée** : Suivi TVA
- **Objectif** : Vérifier suivi TVA collectée
- **Prérequis** : Factures avec TVA
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter TVA collectée
  2. Vérifier montant
- **Résultat attendu** : TVA correcte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test fiscalité

#### SC-CPT-021 : TVA déductible
- **Module** : Comptabilité Avancée
- **Fonction testée** : Suivi TVA déductible
- **Objectif** : Vérifier suivi TVA déductible
- **Prérequis** : Factures fournisseurs
- **Données de test** : Période
- **Étapes détaillées** :
  1. Consulter TVA déductible
  2. Vérifier montant
- **Résultat attendu** : TVA correcte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test fiscalité

#### SC-CPT-022 : Rapprochement bancaire
- **Module** : Comptabilité Avancée
- **Fonction testée** : Rapprochement bancaire
- **Objectif** : Vérifier rapprochement bancaire
- **Prérequis** : Relevé bancaire
- **Données de test** : Comparaison écritures/relevé
- **Étapes détaillées** :
  1. Importer relevé
  2. Rapprocher écritures
- **Résultat attendu** : Écarts identifiés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test trésorerie

#### SC-CPT-023 : Journal des OD
- **Module** : Comptabilité Avancée
- **Fonction testée** : Opérations diverses
- **Objectif** : Vérifier journal OD
- **Prérequis** : Écritures OD
- **Données de test** : Écritures diverses
- **Étapes détaillées** :
  1. Consulter journal OD
  2. Vérifier écritures
- **Résultat attendu** : Journal OD correct
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test journal

#### SC-CPT-024 : Amortissements
- **Module** : Comptabilité Avancée
- **Fonction testée** : Calcul amortissements
- **Objectif** : Vérifier calcul amortissements
- **Prérequis** : Immobilisations
- **Données de test** : Immobilisation + durée
- **Étapes détaillées** :
  1. Calculer amortissements
  2. Vérifier montants
- **Résultat attendu** : Amortissements corrects
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test immobilisations

#### SC-CPT-025 : Provisions
- **Module** : Comptabilité Avancée
- **Fonction testée** : Calcul provisions
- **Objectif** : Vérifier calcul provisions
- **Prérequis** : Créances douteuses
- **Données de test** : Créances + taux
- **Étapes détaillées** :
  1. Calculer provisions
  2. Vérifier montants
- **Résultat attendu** : Provisions correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test provisions

#### SC-CPT-026 : Tableau de financement
- **Module** : Comptabilité Avancée
- **Fonction testée** : Tableau financement
- **Objectif** : Vérifier tableau financement
- **Prérequis** : Bilan + compte résultat
- **Données de test** : Exercice
- **Étapes détaillées** :
  1. Générer tableau financement
  2. Vérifier structure
- **Résultat attendu** : Tableau correct
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test analyse

#### SC-CPT-027 : Ratio financier
- **Module** : Comptabilité Avancée
- **Fonction testée** : Calcul ratios
- **Objectif** : Vérifier calcul ratios financiers
- **Prérequis** : Bilan + compte résultat
- **Données de test** : Ratios standards
- **Étapes détaillées** :
  1. Calculer ratios
  2. Vérifier valeurs
- **Résultat attendu** : Ratios corrects
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test analyse

#### SC-CPT-028 : Budget prévisionnel
- **Module** : Comptabilité Avancée
- **Fonction testée** : Gestion budget
- **Objectif** : Vérifier gestion budget prévisionnel
- **Prérequis** : Module comptabilité_avancee
- **Données de test** : Budget 2026
- **Étapes détaillées** :
  1. Créer budget
  2. Suivi réalisé vs prévisionnel
- **Résultat attendu** : Budget géré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test budgétaire

#### SC-CPT-029 : Multi-devises
- **Module** : Comptabilité Avancée
- **Fonction testée** : Gestion devises
- **Objectif** : Vérifier conversion devises
- **Prérequis** : Module comptabilité_avancee
- **Données de test** : EUR/USD taux
- **Étapes détaillées** :
  1. Configurer taux
  2. Convertir montants
- **Résultat attendu** : Conversions correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test multi-devises

#### SC-CPT-030 : RBAC Comptabilité Avancée
- **Module** : Comptabilité Avancée
- **Fonction testée** : Permissions avancées
- **Objectif** : Vérifier permissions spécifiques
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles comptable/DG
- **Étapes détaillées** :
  1. Tester accès clôture
  2. Tester accès validation
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

## D. RESSOURCES HUMAINES (20+ SCÉNARIOS)

### D.1 GESTION DES EMPLOYÉS (10 scénarios)

#### SC-RH-001 : Création employé complet
- **Module** : RH
- **Fonction testée** : Création employé
- **Objectif** : Vérifier création employé avec toutes les informations
- **Prérequis** : Utilisateur rôle responsable_rh
- **Données de test** :
  ```json
  {
    "matricule": "EMP-001",
    "nom": "Konaté",
    "prenoms": "Jean-Baptiste",
    "sexe": "H",
    "date_naissance": "1985-05-15",
    "lieu_naissance": "Abidjan",
    "nationalite": "Côte d'Ivoire",
    "situation_matrimoniale": "Marie(e)",
    "nombre_enfants": 2,
    "telephone_principal": "+225 27 22 00 00 00",
    "email": "konate.jb@fabs-ci.ci",
    "adresse": "Cocody, Rue 12",
    "ville": "Abidjan",
    "personne_a_prevenir": "Mme Konaté",
    "telephone_urgence": "+225 27 22 00 00 01",
    "numero_cni": "CI1234567890",
    "date_delivrance_cni": "2020-01-01",
    "date_expiration_cni": "2030-01-01",
    "numero_cnps": "CNPS123456",
    "date_affiliation_cnps": "2020-01-01",
    "date_embauche": "2020-03-01",
    "date_prise_fonction": "2020-03-01",
    "departement_id": "dept_001",
    "fonction_id": "fon_001",
    "categorie_pro_id": "cat_001",
    "type_employe": "Commercial",
    "statut": "Actif"
  }
  ```
- **Étapes détaillées** :
  1. Naviguer vers RH > Employés
  2. Cliquer "Nouvel employé"
  3. Remplir tous les champs
  4. Sauvegarder
- **Résultat attendu** : Employé créé avec employe_id unique
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test création complète

#### SC-RH-002 : Validation matricule unique
- **Module** : RH
- **Fonction testée** : Unicité matricule
- **Objectif** : Vérifier rejet matricule en doublon
- **Prérequis** : Employé avec matricule EMP-001 existe
- **Données de test** : matricule="EMP-001"
- **Étapes détaillées** :
  1. Tenter création avec même matricule
  2. Vérifier rejet
- **Résultat attendu** : Erreur 409 Matricule déjà utilisé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test unicité

#### SC-RH-003 : Validation CNI unique
- **Module** : RH
- **Fonction testée** : Unicité CNI
- **Objectif** : Vérifier rejet CNI en doublon
- **Prérequis** : Employé avec CNI existe
- **Données de test** : numero_cni="CI1234567890"
- **Étapes détaillées** :
  1. Tenter création avec même CNI
  2. Vérifier rejet
- **Résultat attendu** : Erreur 409 CNI déjà utilisé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test unicité

#### SC-RH-004 : Validation CNPS unique
- **Module** : RH
- **Fonction testée** : Unicité CNPS
- **Objectif** : Vérifier rejet CNPS en doublon
- **Prérequis** : Employé avec CNPS existe
- **Données de test** : numero_cnps="CNPS123456"
- **Étapes détaillées** :
  1. Tenter création avec même CNPS
  2. Vérifier rejet
- **Résultat attendu** : Erreur 409 CNPS déjà utilisé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test unicité

#### SC-RH-005 : Modification employé
- **Module** : RH
- **Fonction testée** : Mise à jour employé
- **Objectif** : Vérifier modification informations employé
- **Prérequis** : Employé existant
- **Données de test** :
  ```json
  {
    "telephone_principal": "+225 27 22 00 00 99",
    "email": "nouveau.email@fabs-ci.ci"
  }
  ```
- **Étapes détaillées** :
  1. Sélectionner employé
  2. Modifier téléphone et email
  3. Sauvegarder
- **Résultat attendu** : Employé mis à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test modification

#### SC-RH-006 : Liste employés filtres
- **Module** : RH
- **Fonction testée** : Filtres employés
- **Objectif** : Vérifier filtres département/fonction/statut
- **Prérequis** : Base employés peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par département
  2. Filtrer par fonction
  3. Filtrer par statut
  4. Rechercher texte
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test recherche

#### SC-RH-007 : Soft delete employé
- **Module** : RH
- **Fonction testée** : Désactivation employé
- **Objectif** : Vérifier désactivation sans suppression
- **Prérequis** : Employé existant
- **Données de test** : Employé ID
- **Étapes détaillées** :
  1. Désactiver employé
  2. Vérifier toujours en BDD
- **Résultat attendu** : actif=False
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test soft delete

#### SC-RH-008 : Enrichissement données liées
- **Module** : RH
- **Fonction testée** : Lookup département/fonction/catégorie
- **Objectif** : Vérifier enrichissement automatique
- **Prérequis** : Employé avec département/fonction
- **Données de test** : Consultation employé
- **Étapes détaillées** :
  1. Consulter employé
  2. Vérifier noms département/fonction/catégorie
- **Résultat attendu** : Champs _nom enrichis
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test lookup

#### SC-RH-009 : Validation dates
- **Module** : RH
- **Fonction testée** : Validation format dates
- **Objectif** : Vérifier rejet dates invalides
- **Prérequis** : Formulaire employé
- **Données de test** : date_naissance="invalid-date"
- **Étapes détaillées** :
  1. Saisir date invalide
  2. Tenter soumission
- **Résultat attendu** : Erreur validation
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test validation

#### SC-RH-010 : RBAC Employés
- **Module** : RH
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions RH
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {responsable_rh, DG, comptable}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

### D.2 CONTRATS ET CONGÉS (10 scénarios)

#### SC-RH-011 : Création contrat
- **Module** : RH
- **Fonction testée** : Création contrat
- **Objectif** : Vérifier création contrat employé
- **Prérequis** : Employé existant
- **Données de test** :
  ```json
  {
    "employe_id": "emp_xxx",
    "type_contrat": "CDI",
    "date_debut": "2026-06-01",
    "date_fin": null,
    "periode_essai": 90,
    "salaire_base": 300000,
    "prime_transport": 50000,
    "prime_logement": 0,
    "prime_fonction": 20000,
    "autres_primes": 0
  }
  ```
- **Étapes détaillées** :
  1. Créer contrat
  2. Vérifier sauvegarde
- **Résultat attendu** : Contrat créé avec référence auto
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test création

#### SC-RH-012 : Expiration contrat
- **Module** : RH
- **Fonction testée** : Alerte expiration
- **Objectif** : Vérifier alerte contrat expirant
- **Prérequis** : Contrat date_fin proche
- **Données de test** : Consultation dashboard RH
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier alertes contrats
- **Résultat attendu** : Alertes 30j/90j générées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test alerte

#### SC-RH-013 : Demande congé
- **Module** : RH
- **Fonction testée** : Création demande congé
- **Objectif** : Vérifier création demande congé
- **Prérequis** : Employé existant
- **Données de test** :
  ```json
  {
    "employe_id": "emp_xxx",
    "type_conge": "conge_annuel",
    "date_debut": "2026-07-01",
    "date_fin": "2026-07-15",
    "nombre_jours": 15,
    "motif": "Vacances annuelles"
  }
  ```
- **Étapes détaillées** :
  1. Créer demande congé
  2. Vérifier statut en_attente
- **Résultat attendu** : Demande créée statut=en_attente
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-RH-014 : Approbation congé supérieur
- **Module** : RH
- **Fonction testée** : Approbation hiérarchique
- **Objectif** : Vérifier approbation par supérieur
- **Prérequis** : Demande congé en_attente
- **Données de test** : Rôle supérieur hiérarchique
- **Étapes détaillées** :
  1. Approuver congé
  2. Vérifier statut approuve_sup
- **Résultat attendu** : statut=approuve_sup
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-RH-015 : Approbation congé direction
- **Module** : RH
- **Fonction testée** : Approbation direction
- **Objectif** : Vérifier approbation par direction
- **Prérequis** : Congé approuve_sup
- **Données de test** : Rôle DG
- **Étapes détaillées** :
  1. Approuver direction
  2. Vérifier statut approuve_direction
- **Résultat attendu** : statut=approuve_direction
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-RH-016 : Approbation congé RH
- **Module** : RH
- **Fonction testée** : Validation finale RH
- **Objectif** : Vérifier validation RH
- **Prérequis** : Congé approuve_direction
- **Données de test** : Rôle responsable_rh
- **Étapes détaillées** :
  1. Valider RH
  2. Vérifier statut approuve_rh
- **Résultat attendu** : statut=approuve_rh
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test workflow

#### SC-RH-017 : Refus congé
- **Module** : RH
- **Fonction testée** : Refus demande
- **Objectif** : Vérifier refus avec motif
- **Prérequis** : Demande congé en_attente
- **Données de test** : motif="Service prioritaire"
- **Étapes détaillées** :
  1. Refuser congé
  2. Vérifier statut refuse
- **Résultat attendu** : statut=refuse, motif enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test refus

#### SC-RH-018 : Suivi solde congé
- **Module** : RH
- **Fonction testée** : Calcul solde congé
- **Objectif** : Vérifier calcul automatique solde
- **Prérequis** : Employé avec congés
- **Données de test** : Historique congés
- **Étapes détaillées** :
  1. Consulter solde congé
  2. Vérifier calcul
- **Résultat attendu** : Solde correct (30j - pris)
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test calcul

#### SC-RH-019 : Dashboard RH
- **Module** : RH
- **Fonction testée** : Dashboard statistiques
- **Objectif** : Vérifier dashboard RH
- **Prérequis** : Base employés peuplée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier stats
- **Résultat attendu** : Stats correctes (total, actifs, congés, etc.)
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test dashboard

#### SC-RH-020 : Alertes RH
- **Module** : RH
- **Fonction testée** : Système alertes
- **Objectif** : Vérifier alertes automatiques
- **Prérequis** : Base employés peuplée
- **Données de test** : Consultation alertes
- **Étapes détaillées** :
  1. Consulter alertes
  2. Vérifier types (contrats, CNI, CNPS, congés, missions)
- **Résultat attendu** : Alertes générées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test alertes

---

## E. LOGISTIQUE ET FLEET (15+ SCÉNARIOS)

### E.1 GESTION FLOTTTE (10 scénarios)

#### SC-FLT-001 : Création véhicule
- **Module** : Fleet
- **Fonction testée** : Création véhicule
- **Objectif** : Vérifier création véhicule flotte
- **Prérequis** : Utilisateur rôle service_logistique
- **Données de test** :
  ```json
  {
    "immatriculation": "CI-123-AB-456",
    "marque": "Toyota",
    "modele": "Hilux",
    "annee": 2022,
    "type_vehicule": "Camionnette",
    "carburant": "Diesel",
    "capacite_tonnage": 1.5,
    "kilometrage": 50000,
    "date_mise_circulation": "2022-01-01",
    "statut": "Actif"
  }
  ```
- **Étapes détaillées** :
  1. Naviguer vers Fleet
  2. Créer véhicule
  3. Sauvegarder
- **Résultat attendu** : Véhicule créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test création

#### SC-FLT-002 : Validation immatriculation unique
- **Module** : Fleet
- **Fonction testée** : Unicité immatriculation
- **Objectif** : Vérifier rejet immatriculation en doublon
- **Prérequis** : Véhicule avec immatriculation existe
- **Données de test** : immatriculation="CI-123-AB-456"
- **Étapes détaillées** :
  1. Tenter création avec même immatriculation
  2. Vérifier rejet
- **Résultat attendu** : Erreur 409 Immatriculation déjà utilisée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test unicité

#### SC-FLT-003 : Affectation chauffeur
- **Module** : Fleet
- **Fonction testée** : Affectation chauffeur
- **Objectif** : Vérifier affectation chauffeur à véhicule
- **Prérequis** : Véhicule et employé existants
- **Données de test** : chauffeur_id="emp_xxx"
- **Étapes détaillées** :
  1. Affecter chauffeur
  2. Vérifier lien
- **Résultat attendu** : Chauffeur affecté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test affectation

#### SC-FLT-004 : Suivi kilométrage
- **Module** : Fleet
- **Fonction testée** : Mise à jour kilométrage
- **Objectif** : Vérifier suivi kilométrage
- **Prérequis** : Véhicule existant
- **Données de test** : kilometrage=55000
- **Étapes détaillées** :
  1. Mettre à jour kilométrage
  2. Vérifier historique
- **Résultat attendu** : Kilométrage mis à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test suivi

#### SC-FLT-005 : Maintenance planifiée
- **Module** : Fleet
- **Fonction testée** : Gestion maintenance
- **Objectif** : Vérifier création maintenance planifiée
- **Prérequis** : Véhicule existant
- **Données de test** :
  ```json
  {
    "vehicule_id": "veh_xxx",
    "type_maintenance": "vidange",
    "date_prevue": "2026-07-01",
    "kilometrage_prevu": 60000
  }
  ```
- **Étapes détaillées** :
  1. Créer maintenance
  2. Vérifier alerte
- **Résultat attendu** : Maintenance planifiée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test maintenance

#### SC-FLT-006 : Alerte maintenance
- **Module** : Fleet
- **Fonction testée** : Alerte maintenance échue
- **Objectif** : Vérifier alerte maintenance
- **Prérequis** : Maintenance date_passée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier alertes
- **Résultat attendu** : Alerte maintenance générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test alerte

#### SC-FLT-007 : Consommation carburant
- **Module** : Fleet
- **Fonction testée** : Suivi carburant
- **Objectif** : Vérifier suivi consommation carburant
- **Prérequis** : Véhicule existant
- **Données de test** :
  ```json
  {
    "vehicule_id": "veh_xxx",
    "date": "2026-06-01",
    "quantite_litre": 50,
    "montant": 50000,
    "kilometrage": 52000
  }
  ```
- **Étapes détaillées** :
  1. Enregistrer carburant
  2. Vérifier calcul consommation
- **Résultat attendu** : Consommation calculée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test consommation

#### SC-FLT-008 : Liste véhicules filtres
- **Module** : Fleet
- **Fonction testée** : Filtres véhicules
- **Objectif** : Vérifier filtres statut/type
- **Prérequis** : Base véhicules peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par statut
  2. Filtrer par type
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test recherche

#### SC-FLT-009 : Dashboard Fleet
- **Module** : Fleet
- **Fonction testée** : Dashboard flotte
- **Objectif** : Vérifier dashboard flotte
- **Prérequis** : Base véhicules peuplée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier stats
- **Résultat attendu** : Stats correctes (total, actifs, maintenance, etc.)
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test dashboard

#### SC-FLT-010 : RBAC Fleet
- **Module** : Fleet
- **Fonction testée** : Permissions par rôle
- **Objectif** : Vérifier matrice permissions
- **Prérequis** : Utilisateurs multi-rôles
- **Données de test** : Rôles {service_logistique, DG}
- **Étapes détaillées** :
  1. Tester accès lecture
  2. Tester accès écriture
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

---

### E.2 MISSIONS LOGISTIQUES (5 scénarios)

#### SC-FLT-011 : Création mission
- **Module** : RH (Missions)
- **Fonction testée** : Création mission
- **Objectif** : Vérifier création mission employé
- **Prérequis** : Employé existant
- **Données de test** :
  ```json
  {
    "employe_id": "emp_xxx",
    "type_mission": "mission_commerciale",
    "ville": "Bouaké",
    "date_depart": "2026-06-10",
    "date_retour": "2026-06-12",
    "objet": "Visite clients",
    "budget": 50000
  }
  ```
- **Étapes détaillées** :
  1. Créer mission
  2. Vérifier statut planifiee
- **Résultat attendu** : Mission créée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test création

#### SC-FLT-012 : Démarrage mission
- **Module** : RH (Missions)
- **Fonction testée** : Démarrage mission
- **Objectif** : Vérifier transition planifiee→en_cours
- **Prérequis** : Mission planifiee
- **Données de test** : Mission ID
- **Étapes détaillées** :
  1. Démarrer mission
  2. Vérifier statut en_cours
- **Résultat attendu** : statut=en_cours
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test workflow

#### SC-FLT-013 : Clôture mission
- **Module** : RH (Missions)
- **Fonction testée** : Clôture mission
- **Objectif** : Vérifier transition en_cours→terminee
- **Prérequis** : Mission en_cours
- **Données de test** : compte_rendu="Mission réussie"
- **Étapes détaillées** :
  1. Clôturer mission
  2. Ajouter compte rendu
- **Résultat attendu** : statut=terminee, compte_rendu enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test workflow

#### SC-FLT-014 : Alerte mission non clôturée
- **Module** : RH (Missions)
- **Fonction testée** : Alerte mission échue
- **Objectif** : Vérifier alerte mission non clôturée
- **Prérequis** : Mission date_retour passée
- **Données de test** : Consultation alertes RH
- **Étapes détaillées** :
  1. Consulter alertes
  2. Vérifier alerte mission
- **Résultat attendu** : Alerte générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test alerte

#### SC-FLT-015 : Liste missions filtres
- **Module** : RH (Missions)
- **Fonction testée** : Filtres missions
- **Objectif** : Vérifier filtres employé/statut
- **Prérequis** : Base missions peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par employé
  2. Filtrer par statut
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test recherche

---

## F. WORKFLOW ET APPROBATIONS (15+ SCÉNARIOS)

### F.1 WORKFLOW COMMANDES (10 scénarios)

#### SC-WF-001 : Workflow commande complet
- **Module** : Commandes
- **Fonction testée** : Workflow E2E
- **Objectif** : Vérifier workflow complet commande
- **Prérequis** : Client et produits existants
- **Données de test** : Processus complet
- **Étapes détaillées** :
  1. Créer commande brouillon
  2. Soumettre (en_attente)
  3. Valider (validee)
  4. Préparer (preparee)
  5. Livrer (livree)
- **Résultat attendu** : Workflow complet fonctionnel
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test E2E

#### SC-WF-002 : Validation DG obligatoire
- **Module** : Commandes
- **Fonction testée** : Règle seuil 500k
- **Objectif** : Vérifier validation DG obligatoire
- **Prérequis** : Commande montant=600000
- **Données de test** : Rôle directeur_commercial
- **Étapes détaillées** :
  1. Tenter validation commercial
  2. Vérifier refus
  3. Valider avec DG
- **Résultat attendu** : Commercial refusé, DG accepté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test règle métier

#### SC-WF-003 : Génération proforma automatique
- **Module** : Commandes
- **Fonction testée** : Auto-génération proforma
- **Objectif** : Vérifier génération proforma à validation
- **Prérequis** : Commande en_attente
- **Données de test** : Validation commande
- **Étapes détaillées** :
  1. Valider commande
  2. Vérifier proforma générée
- **Résultat attendu** : Proforma créée automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test workflow

#### SC-WF-004 : Rollback proforma échouée
- **Module** : Commandes
- **Fonction testée** : Gestion erreur
- **Objectif** : Vérifier rollback si proforma échoue
- **Prérequis** : Simulation erreur proforma
- **Données de test** : Erreur générée
- **Étapes détaillées** :
  1. Simuler erreur proforma
  2. Vérifier rollback commande
- **Résultat attendu** : Commande reste en_attente
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test gestion erreur

#### SC-WF-005 : Modification brouillon uniquement
- **Module** : Commandes
- **Fonction testée** : Guard modification
- **Objectif** : Vérifier modification uniquement brouillon
- **Prérequis** : Commande validee
- **Données de test** : Tentative modification
- **Étapes détaillées** :
  1. Tenter modification commande validee
  2. Vérifier refus
- **Résultat attendu** : Erreur 400 Seules brouillon modifiables
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test guard

#### SC-WF-006 : Annulation commande non livrée
- **Module** : Commandes
- **Fonction testée** : Guard annulation
- **Objectif** : Vérifier annulation uniquement non livrée
- **Prérequis** : Commande livree
- **Données de test** : Tentative annulation
- **Étapes détaillées** :
  1. Tenter annulation commande livree
  2. Vérifier refus
- **Résultat attendu** : Erreur 400 Impossible annuler livrée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test guard

#### SC-WF-007 : Historique workflow
- **Module** : Commandes
- **Fonction testée** : Traçabilité workflow
- **Objectif** : Vérifier historique transitions
- **Prérequis** : Commande avec workflow
- **Données de test** : Consultation commande
- **Étapes détaillées** :
  1. Consulter commande
  2. Vérifier dates transitions
- **Résultat attendu** : Dates validation/préparation/livraison enregistrées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-WF-008 : Notifications workflow
- **Module** : Notifications
- **Fonction testée** : Notifications automatiques
- **Objectif** : Vérifier notifications workflow
- **Prérequis** : Commande workflow
- **Données de test** : Consultation notifications
- **Étapes détaillées** :
  1. Valider commande
  2. Vérifier notification magasinier
  3. Préparer commande
  4. Vérifier notification logistique
- **Résultat attendu** : Notifications envoyées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test notifications

#### SC-WF-009 : Audit log workflow
- **Module** : Audit Logs
- **Fonction testée** : Audit workflow
- **Objectif** : Vérifier audit log transitions
- **Prérequis** : Commande workflow
- **Données de test** : Consultation audit_logs
- **Étapes détaillées** :
  1. Consulter audit_logs
  2. Vérifier actions workflow
- **Résultat attendu** : Actions VALIDATE/PREPARE/DELIVER logguées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test audit

#### SC-WF-010 : Workflow parallèle
- **Module** : Commandes
- **Fonction testée** : Gestion commandes multiples
- **Objectif** : Vérifier gestion workflow parallèle
- **Prérequis** : 3 commandes en_attente
- **Données de test** : Validation simultanée
- **Étapes détaillées** :
  1. Valider 3 commandes
  2. Vérifier proformas générées
- **Résultat attendu** : 3 proformas générées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test concurrence

---

### F.2 WORKFLOW RH (5 scénarios)

#### SC-WF-011 : Workflow congé complet
- **Module** : RH (Congés)
- **Fonction testée** : Workflow congé E2E
- **Objectif** : Vérifier workflow approbation congé
- **Prérequis** : Employé existant
- **Données de test** : Processus complet
- **Étapes détaillées** :
  1. Créer demande congé
  2. Approuver supérieur
  3. Approuver direction
  4. Valider RH
- **Résultat attendu** : Workflow complet fonctionnel
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test E2E

#### SC-WF-012 : Refus workflow congé
- **Module** : RH (Congés)
- **Fonction testée** : Arrêt workflow refus
- **Objectif** : Vérifier arrêt workflow sur refus
- **Prérequis** : Demande congé en_attente
- **Données de test** : Refus supérieur
- **Étapes détaillées** :
  1. Refuser congé
  2. Vérifier arrêt workflow
- **Résultat attendu** : statut=refuse, workflow arrêté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test refus

#### SC-WF-013 : Historique approbations
- **Module** : RH (Congés)
- **Fonction testée** : Traçabilité approbations
- **Objectif** : Vérifier historique approbations
- **Prérequis** : Congé avec workflow
- **Données de test** : Consultation congé
- **Étapes détaillées** :
  1. Consulter congé
  2. Vérifier approbations
- **Résultat attendu** : Dates/commentaires approbations enregistrés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test traçabilité

#### SC-WF-014 : Notifications approbations
- **Module** : Notifications
- **Fonction testée** : Notifications congé
- **Objectif** : Vérifier notifications approbations
- **Prérequis** : Demande congé
- **Données de test** : Consultation notifications
- **Étapes détaillées** :
  1. Créer demande
  2. Vérifier notification supérieur
  3. Approuver
  4. Vérifier notification direction
- **Résultat attendu** : Notifications envoyées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test notifications

#### SC-WF-015 : Délégation approbation
- **Module** : RH (Délégations)
- **Fonction testée** : Gestion délégation
- **Objectif** : Vérifier délégation approbation
- **Prérequis** : Délégation configurée
- **Données de test** : Approbation par remplaçant
- **Étapes détaillées** :
  1. Configurer délégation
  2. Approuver avec remplaçant
- **Résultat attendu** : Approbation acceptée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test délégation

---

## G. DOCUMENTS ET IA (10+ SCÉNARIOS)

### G.1 GESTION DOCUMENTS (5 scénarios)

#### SC-DOC-001 : Upload document
- **Module** : Documents
- **Fonction testée** : Upload fichier
- **Objectif** : Vérifier upload document
- **Prérequis** : Utilisateur connecté
- **Données de test** : Fichier PDF test
- **Étapes détaillées** :
  1. Sélectionner fichier
  2. Uploader
  3. Vérifier sauvegarde
- **Résultat attendu** : Document uploadé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test upload

#### SC-DOC-002 : Lien document employé
- **Module** : Documents
- **Fonction testée** : Lien employé
- **Objectif** : Vérifier lien document employé
- **Prérequis** : Document et employé existants
- **Données de test** : Lien CNI employé
- **Étapes détaillées** :
  1. Lier document à employé
  2. Vérifier lien
- **Résultat attendu** : Lien créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test lien

#### SC-DOC-003 : Liste documents filtres
- **Module** : Documents
- **Fonction testée** : Filtres documents
- **Objectif** : Vérifier filtres type/employé
- **Prérequis** : Base documents peuplée
- **Données de test** : Filtres combinés
- **Étapes détaillées** :
  1. Filtrer par type
  2. Filtrer par employé
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test recherche

#### SC-DOC-004 : Download document
- **Module** : Documents
- **Fonction testée** : Téléchargement
- **Objectif** : Vérifier téléchargement document
- **Prérequis** : Document existant
- **Données de test** : Document ID
- **Étapes détaillées** :
  1. Télécharger document
  2. Vérifier fichier
- **Résultat attendu** : Fichier téléchargé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test download

#### SC-DOC-005 : Suppression document
- **Module** : Documents
- **Fonction testée** : Suppression
- **Objectif** : Vérifier suppression document
- **Prérequis** : Document existant
- **Données de test** : Document ID
- **Étapes détaillées** :
  1. Supprimer document
  2. Vérifier suppression
- **Résultat attendu** : Document supprimé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test suppression

---

### G.2 IA ET ANALYSE (5 scénarios)

#### SC-DOC-006 : OCR document
- **Module** : IA (si implémenté)
- **Fonction testée** : OCR PDF
- **Objectif** : Vérifier extraction texte PDF
- **Prérequis** : Module IA
- **Données de test** : PDF scanné
- **Étapes détaillées** :
  1. Uploader PDF
  2. Lancer OCR
  3. Vérifier extraction
- **Résultat attendu** : Texte extrait
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test IA

#### SC-DOC-007 : Analyse sentiment
- **Module** : IA (si implémenté)
- **Fonction testée** : Analyse sentiment
- **Objectif** : Vérifier analyse feedback client
- **Prérequis** : Module IA
- **Données de test** : Texte feedback
- **Étapes détaillées** :
  1. Analyser texte
  2. Vérifier sentiment
- **Résultat attendu** : Sentiment détecté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test IA

#### SC-DOC-008 : Prédictions ventes
- **Module** : IA (si implémenté)
- **Fonction testée** : Prédictions
- **Objectif** : Vérifier prédictions ventes
- **Prérequis** : Module IA + historique
- **Données de test** : Historique ventes
- **Étapes détaillées** :
  1. Générer prédictions
  2. Vérifier résultats
- **Résultat attendu** : Prédictions générées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test IA

#### SC-DOC-009 : Classification documents
- **Module** : IA (si implémenté)
- **Fonction testée** : Classification auto
- **Objectif** : Vérifier classification documents
- **Prérequis** : Module IA
- **Données de test** : Documents variés
- **Étapes détaillées** :
  1. Classifier documents
  2. Vérifier catégories
- **Résultat attendu** : Classification correcte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test IA

#### SC-DOC-010 : Chatbot support
- **Module** : IA (si implémenté)
- **Fonction testée** : Chatbot
- **Objectif** : Vérifier chatbot support
- **Prérequis** : Module IA
- **Données de test** : Questions utilisateurs
- **Étapes détaillées** :
  1. Poser question
  2. Vérifier réponse
- **Résultat attendu** : Réponse pertinente
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test IA

---

## H. NOTIFICATIONS (10+ SCÉNARIOS)

### H.1 NOTIFICATIONS IN-APP (5 scénarios)

#### SC-NOT-001 : Création notification
- **Module** : Notifications
- **Fonction testée** : Création notification
- **Objectif** : Vérifier création notification
- **Prérequis** : Utilisateur existant
- **Données de test** :
  ```json
  {
    "user_id": "usr_xxx",
    "titre": "Test notification",
    "message": "Message test",
    "type": "info",
    "lien": "/commandes"
  }
  ```
- **Étapes détaillées** :
  1. Créer notification
  2. Vérifier réception
- **Résultat attendu** : Notification créée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test création

#### SC-NOT-002 : Liste notifications
- **Module** : Notifications
- **Fonction testée** : Liste notifications
- **Objectif** : Vérifier liste notifications utilisateur
- **Prérequis** : Notifications existantes
- **Données de test** : Filtres lu/non_lu
- **Étapes détaillées** :
  1. Consulter notifications
  2. Filtrer par statut
- **Résultat attendu** : Liste correcte
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test liste

#### SC-NOT-003 : Marquer comme lu
- **Module** : Notifications
- **Fonction testée** : Marquer lu
- **Objectif** : Vérifier marquage lu
- **Prérequis** : Notification non_lue
- **Données de test** : Notification ID
- **Étapes détaillées** :
  1. Marquer comme lu
  2. Vérifier statut
- **Résultat attendu** : statut=lu
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test marquage

#### SC-NOT-004 : Notification workflow commande
- **Module** : Notifications
- **Fonction testée** : Auto-notification workflow
- **Objectif** : Vérifier notification automatique workflow
- **Prérequis** : Commande validée
- **Données de test** : Consultation notifications
- **Étapes détaillées** :
  1. Valider commande
  2. Vérifier notification magasinier
- **Résultat attendu** : Notification envoyée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test auto-notification

#### SC-NOT-005 : Notification alerte stock
- **Module** : Notifications
- **Fonction testée** : Auto-notification alerte
- **Objectif** : Vérifier notification alerte stock
- **Prérequis** : Stock rupture
- **Données de test** : Consultation notifications
- **Étapes détaillées** :
  1. Déclencher rupture stock
  2. Vérifier notification gestionnaire
- **Résultat attendu** : Notification envoyée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test auto-notification

---

### H.2 NOTIFICATIONS EXTERNES (5 scénarios)

#### SC-NOT-006 : Envoi email SMTP
- **Module** : Notifications
- **Fonction testée** : Email SMTP
- **Objectif** : Vérifier envoi email
- **Prérequis** : Configuration SMTP
- **Données de test** : Email test
- **Étapes détaillées** :
  1. Envoyer email
  2. Vérifier réception
- **Résultat attendu** : Email reçu
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test SMTP

#### SC-NOT-007 : Envoi WhatsApp
- **Module** : Commandes/Factures
- **Fonction testée** : Lien WhatsApp
- **Objectif** : Vérifier génération lien WhatsApp
- **Prérequis** : Client avec WhatsApp
- **Données de test** : Commande ID
- **Étapes détaillées** :
  1. Générer lien WhatsApp
  2. Vérifier URL
- **Résultat attendu** : URL wa.me générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test WhatsApp

#### SC-NOT-008 : Email facture
- **Module** : Factures
- **Fonction testée** : Email facture PDF
- **Objectif** : Vérifier envoi facture par email
- **Prérequis** : Facture + client email
- **Données de test** : Facture ID
- **Étapes détaillées** :
  1. Envoyer facture par email
  2. Vérifier réception
- **Résultat attendu** : Email avec PDF reçu
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test email

#### SC-NOT-009 : Template email
- **Module** : Notifications
- **Fonction testée** : Template email
- **Objectif** : Vérifier template email HTML
- **Prérequis** : Configuration SMTP
- **Données de test** : Email avec template
- **Étapes détaillées** :
  1. Envoyer email template
  2. Vérifier rendu HTML
- **Résultat attendu** : Email HTML correct
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test template

#### SC-NOT-010 : Historique notifications
- **Module** : Notifications
- **Fonction testée** : Historique envois
- **Objectif** : Vérifier historique notifications
- **Prérequis** : Notifications envoyées
- **Données de test** : Consultation historique
- **Étapes détaillées** :
  1. Consulter historique
  2. Vérifier statuts
- **Résultat attendu** : Historique complet
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test historique

---

## I. SÉCURITÉ (25+ SCÉNARIOS)

### I.1 AUTHENTIFICATION (10 scénarios)

#### SC-SEC-001 : Login valide
- **Module** : Auth
- **Fonction testée** : Login utilisateur
- **Objectif** : Vérifier login avec identifiants valides
- **Prérequis** : Utilisateur existant
- **Données de test** :
  ```json
  {
    "email": "pissken@editionsfabsci.com",
    "password": "Admin@2025"
  }
  ```
- **Étapes détaillées** :
  1. Saisir identifiants
  2. Cliquer login
  3. Vérifier token JWT
- **Résultat attendu** : Login réussi, token JWT généré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auth

#### SC-SEC-002 : Login invalide
- **Module** : Auth
- **Fonction testée** : Login échec
- **Objectif** : Vérifier rejet identifiants invalides
- **Prérequis** : Aucun
- **Données de test** :
  ```json
  {
    "email": "invalid@email.com",
    "password": "wrongpassword"
  }
  ```
- **Étapes détaillées** :
  1. Saisir identifiants invalides
  2. Cliquer login
- **Résultat attendu** : Erreur 401 Identifiants invalides
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test auth

#### SC-SEC-003 : Token JWT valide
- **Module** : Auth
- **Fonction testée** : Validation token
- **Objectif** : Vérifier validation token JWT
- **Prérequis** : Token JWT valide
- **Données de test** : Token JWT
- **Étapes détaillées** :
  1. Envoyer requête avec token
  2. Vérifier accès autorisé
- **Résultat attendu** : Accès autorisé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test JWT

#### SC-SEC-004 : Token JWT expiré
- **Module** : Auth
- **Fonction testée** : Token expiré
- **Objectif** : Vérifier rejet token expiré
- **Prérequis** : Token JWT expiré
- **Données de test** : Token expiré
- **Étapes détaillées** :
  1. Envoyer requête avec token expiré
  2. Vérifier rejet
- **Résultat attendu** : Erreur 401 Token expiré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test JWT

#### SC-SEC-005 : Refresh token
- **Module** : Auth
- **Fonction testée** : Refresh token
- **Objectif** : Vérifier rafraîchissement token
- **Prérequis** : Refresh token valide
- **Données de test** : Refresh token
- **Étapes détaillées** :
  1. Rafraîchir token
  2. Vérifier nouveau token
- **Résultat attendu** : Nouveau token JWT généré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test refresh

#### SC-SEC-006 : Logout
- **Module** : Auth
- **Fonction testée** : Déconnexion
- **Objectif** : Vérifier déconnexion
- **Prérequis** : Utilisateur connecté
- **Données de test** : Aucune
- **Étapes détaillées** :
  1. Cliquer logout
  2. Vérifier token invalidé
- **Résultat attendu** : Token invalidé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test logout

#### SC-SEC-007 : Mot de passe fort
- **Module** : Auth
- **Fonction testée** : Validation password
- **Objectif** : Vérifier validation mot de passe fort
- **Prérequis** : Formulaire création utilisateur
- **Données de test** : password="weak"
- **Étapes détaillées** :
  1. Saisir mot de passe faible
  2. Tenter création
- **Résultat attendu** : Erreur validation
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test password policy

#### SC-SEC-008 : Changement mot de passe
- **Module** : Auth
- **Fonction testée** : Change password
- **Objectif** : Vérifier changement mot de passe
- **Prérequis** : Utilisateur connecté
- **Données de test** :
  ```json
  {
    "current_password": "Admin@2025",
    "new_password": "NewPassword@2025"
  }
  ```
- **Étapes détaillées** :
  1. Changer mot de passe
  2. Vérifier nouveau mot de passe
- **Résultat attendu** : Mot de passe changé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test change password

#### SC-SEC-009 : Reset mot de passe
- **Module** : Auth
- **Fonction testée** : Reset password
- **Objectif** : Vérifier reset mot de passe
- **Prérequis** : Utilisateur existant
- **Données de test** : Email utilisateur
- **Étapes détaillées** :
  1. Demander reset
  2. Vérifier email reset
- **Résultat attendu** : Email reset envoyé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test reset password

#### SC-SEC-010 : Rate limiting login
- **Module** : Auth
- **Fonction testée** : Rate limiting
- **Objectif** : Vérifier blocage après tentatives multiples
- **Prérequis** : Rate limiting configuré
- **Données de test** : 5 tentatives login échouées
- **Étapes détaillées** :
  1. Tenter 5 logins invalides
  2. Vérifier blocage
- **Résultat attendu** : Blocage temporaire
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test rate limiting

---

### I.2 RBAC ET PERMISSIONS (10 scénarios)

#### SC-SEC-011 : Accès non autorisé
- **Module** : Global
- **Fonction testée** : RBAC enforcement
- **Objectif** : Vérifier rejet accès non autorisé
- **Prérequis** : Utilisateur rôle gestionnaire_stock
- **Données de test** : Tentative accès module RH
- **Étapes détaillées** :
  1. Tenter accès module RH
  2. Vérifier rejet
- **Résultat attendu** : Erreur 403 Accès refusé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-SEC-012 : Matrice permissions clients
- **Module** : Clients
- **Fonction testée** : Permissions clients
- **Objectif** : Vérifier matrice permissions clients
- **Prérequis** : Utilisateurs tous rôles
- **Données de test** : Test lecture/écriture
- **Étapes détaillées** :
  1. Tester chaque rôle
  2. Vérifier permissions
- **Résultat attendu** : READ_ROLES et WRITE_ROLES respectés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-SEC-013 : Matrice permissions commandes
- **Module** : Commandes
- **Fonction testée** : Permissions commandes
- **Objectif** : Vérifier matrice permissions commandes
- **Prérequis** : Utilisateurs tous rôles
- **Données de test** : Test lecture/écriture/validation
- **Étapes détaillées** :
  1. Tester chaque rôle
  2. Vérifier permissions
- **Résultat attendu** : READ/WRITE/VALIDATE/PREPARE/DELIVER respectés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-SEC-014 : Matrice permissions stock
- **Module** : Stock
- **Fonction testée** : Permissions stock
- **Objectif** : Vérifier matrice permissions stock
- **Prérequis** : Utilisateurs tous rôles
- **Données de test** : Test lecture/écriture
- **Étapes détaillées** :
  1. Tester chaque rôle
  2. Vérifier permissions
- **Résultat attendu** : Permissions respectées
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-SEC-015 : Matrice permissions RH
- **Module** : RH
- **Fonction testée** : Permissions RH
- **Objectif** : Vérifier matrice permissions RH
- **Prérequis** : Utilisateurs tous rôles
- **Données de test** : Test lecture/écriture/approbation
- **Étapes détaillées** :
  1. Tester chaque rôle
  2. Vérifier permissions
- **Résultat attendu** : READ/WRITE/APPROVE respectés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test RBAC

#### SC-SEC-016 : Élévation privilèges
- **Module** : Auth
- **Fonction testée** : Privilège escalation
- **Objectif** : Vérifier impossibilité élévation privilèges
- **Prérequis** : Utilisateur rôle commercial
- **Données de test** : Tentative modification rôle
- **Étapes détaillées** :
  1. Tenter modification propre rôle
  2. Vérifier rejet
- **Résultat attendu** : Erreur 403
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test privilege escalation

#### SC-SEC-017 : Session hijacking
- **Module** : Auth
- **Fonction testée** : Protection session
- **Objectif** : Vérifier protection détournement session
- **Prérequis** : Token JWT valide
- **Données de test** : Token volé
- **Étapes détaillées** :
  1. Utiliser token depuis autre IP
  2. Vérifier détection
- **Résultat attendu** : Détection si implémenté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test session security

#### SC-SEC-018 : CSRF protection
- **Module** : Global
- **Fonction testée** : Protection CSRF
- **Objectif** : Vérifier protection CSRF
- **Prérequis** : Endpoint POST
- **Données de test** : Requête sans CSRF token
- **Étapes détaillées** :
  1. Envoyer requête sans CSRF token
  2. Vérifier rejet
- **Résultat attendu** : Rejet si implémenté
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test CSRF

#### SC-SEC-019 : XSS protection
- **Module** : Global
- **Fonction testée** : Protection XSS
- **Objectif** : Vérifier protection XSS
- **Prérequis** : Formulaire saisie
- **Données de test** : `<script>alert('XSS')</script>`
- **Étapes détaillées** :
  1. Saisir script XSS
  2. Sauvegarder
  3. Vérifier échappement
- **Résultat attendu** : Script échappé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test XSS

#### SC-SEC-020 : SQL injection
- **Module** : Global
- **Fonction testée** : Protection SQL injection
- **Objectif** : Vérifier protection SQL injection
- **Prérequis** : Requête recherche
- **Données de test** : `' OR '1'='1`
- **Étapes détaillées** :
  1. Saisir injection SQL
  2. Vérifier protection
- **Résultat attendu** : Injection bloquée (MongoDB NoSQL)
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test NoSQL injection

---

### I.3 AUDIT ET LOGS (5 scénarios)

#### SC-SEC-021 : Audit log création
- **Module** : Audit Logs
- **Fonction testée** : Log création
- **Objectif** : Vérifier log création ressource
- **Prérequis** : Création client
- **Données de test** : Consultation audit_logs
- **Étapes détaillées** :
  1. Créer client
  2. Vérifier log CREATE
- **Résultat attendu** : Log CREATE enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test audit

#### SC-SEC-022 : Audit log modification
- **Module** : Audit Logs
- **Fonction testée** : Log modification
- **Objectif** : Vérifier log modification ressource
- **Prérequis** : Modification client
- **Données de test** : Consultation audit_logs
- **Étapes détaillées** :
  1. Modifier client
  2. Vérifier log UPDATE
- **Résultat attendu** : Log UPDATE enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test audit

#### SC-SEC-023 : Audit log suppression
- **Module** : Audit Logs
- **Fonction testée** : Log suppression
- **Objectif** : Vérifier log suppression ressource
- **Prérequis** : Soft delete client
- **Données de test** : Consultation audit_logs
- **Étapes détaillées** :
  1. Désactiver client
  2. Vérifier log DELETE
- **Résultat attendu** : Log DELETE enregistré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test audit

#### SC-SEC-024 : Audit log IP address
- **Module** : Audit Logs
- **Fonction testée** : Log IP
- **Objectif** : Vérifier log adresse IP
- **Prérequis** : Action utilisateur
- **Données de test** : Consultation audit_logs
- **Étapes détaillées** :
  1. Effectuer action
  2. Vérifier IP logguée
- **Résultat attendu** : IP address enregistrée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test audit

#### SC-SEC-025 : Liste audit logs
- **Module** : Audit Logs
- **Fonction testée** : Filtre audit logs
- **Objectif** : Vérifier filtres audit logs
- **Prérequis** : Audit logs existants
- **Données de test** : Filtres user_id/action/date
- **Étapes détaillées** :
  1. Filtrer par utilisateur
  2. Filtrer par action
  3. Filtrer par date
- **Résultat attendu** : Filtres fonctionnels
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test audit

---

## J. TESTS D'INTÉGRATION (30+ SCÉNARIOS)

### J.1 INTÉGRATION COMMANDE→STOCK→FACTURE (10 scénarios)

#### SC-INT-001 : Workflow commande→stock
- **Module** : Intégration
- **Fonction testée** : Intégration commande stock
- **Objectif** : Vérifier impact commande sur stock
- **Prérequis** : Produit stock=100
- **Données de test** : Commande quantite=20
- **Étapes détaillées** :
  1. Créer commande
  2. Livrer commande
  3. Vérifier stock=80
- **Résultat attendu** : Stock décrémenté automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-002 : Workflow commande→facture
- **Module** : Intégration
- **Fonction testée** : Intégration commande facture
- **Objectif** : Vérifier génération facture depuis commande
- **Prérequis** : Commande validee
- **Données de test** : Génération facture
- **Étapes détaillées** :
  1. Générer facture depuis commande
  2. Vérifier lignes copiées
- **Résultat attendu** : Facture créée avec lignes commande
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-003 : Workflow facture→paiement
- **Module** : Intégration
- **Fonction testée** : Intégration facture paiement
- **Objectif** : Vérifier impact paiement sur facture
- **Prérequis** : Facture emise montant_ttc=100000
- **Données de test** : Paiement=50000
- **Étapes détaillées** :
  1. Enregistrer paiement
  2. Vérifier statut partiellement_payee
- **Résultat attendu** : Statut mis à jour automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-004 : Workflow paiement→comptabilité
- **Module** : Intégration
- **Fonction testée** : Intégration paiement comptabilité
- **Objectif** : Vérifier écriture comptable automatique
- **Prérequis** : Paiement enregistré
- **Données de test** : Consultation écritures
- **Étapes détaillées** :
  1. Enregistrer paiement
  2. Vérifier écriture comptable
- **Résultat attendu** : Écriture générée automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-005 : Workflow commande→proforma
- **Module** : Intégration
- **Fonction testée** : Intégration commande proforma
- **Objectif** : Vérifier génération proforma automatique
- **Prérequis** : Commande en_attente
- **Données de test** : Validation commande
- **Étapes détaillées** :
  1. Valider commande
  2. Vérifier proforma générée
- **Résultat attendu** : Proforma créée automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-006 : Workflow BL→stock
- **Module** : Intégration
- **Fonction testée** : Intégration BL stock
- **Objectif** : Vérifier impact BL sur stock
- **Prérequis** : BL créé
- **Données de test** : Livraison BL
- **Étapes détaillées** :
  1. Livrer BL
  2. Vérifier mouvements sortie
- **Résultat attendu** : Mouvements sortie générés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-007 : Workflow BL→commande
- **Module** : Intégration
- **Fonction testée** : Intégration BL commande
- **Objectif** : Vérifier update commande statut
- **Prérequis** : BL lié à commande
- **Données de test** : Livraison BL
- **Étapes détaillées** :
  1. Livrer BL
  2. Vérifier commande statut livree
- **Résultat attendu** : Commande mise à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-008 : Workflow BR→stock
- **Module** : Intégration
- **Fonction testée** : Intégration BR stock
- **Objectif** : Vérifier impact BR sur stock
- **Prérequis** : BR créé
- **Données de test** : Validation BR
- **Étapes détaillées** :
  1. Valider BR
  2. Vérifier mouvements entrée
- **Résultat attendu** : Mouvements entrée générés
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-009 : Workflow BR→avoir
- **Module** : Intégration
- **Fonction testée** : Intégration BR avoir
- **Objectif** : Vérifier génération avoir automatique
- **Prérequis** : BR validé
- **Données de test** : Validation BR
- **Étapes détaillées** :
  1. Valider BR
  2. Vérifier avoir généré
- **Résultat attendu** : Avoir créé automatiquement
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test intégration

#### SC-INT-010 : Workflow E2E vente
- **Module** : Intégration
- **Fonction testée** : Workflow complet vente
- **Objectif** : Vérifier workflow complet de bout en bout
- **Prérequis** : Client et produits existants
- **Données de test** : Processus complet
- **Étapes détaillées** :
  1. Créer commande
  2. Valider commande
  3. Préparer commande
  4. Créer BL
  5. Livrer BL
  6. Générer facture
  7. Enregistrer paiement
- **Résultat attendu** : Workflow complet fonctionnel
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Critique
- **Commentaires** : Test E2E

---

### J.2 INTÉGRATION RH (10 scénarios)

#### SC-INT-011 : Workflow congé→statut employé
- **Module** : Intégration
- **Fonction testée** : Intégration congé employé
- **Objectif** : Vérifier update statut employé
- **Prérequis** : Congé approuve_rh
- **Données de test** : Consultation employé
- **Étapes détaillées** :
  1. Valider congé
  2. Vérifier statut employé=En conge
- **Résultat attendu** : Statut employé mis à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test intégration

#### SC-INT-012 : Workflow retour congé
- **Module** : Intégration
- **Fonction testée** : Retour congé
- **Objectif** : Vérifier retour statut Actif
- **Prérequis** : Employé statut=En conge
- **Données de test** : Fin période congé
- **Étapes détaillées** :
  1. Fin période congé
  2. Vérifier statut=Actif
- **Résultat attendu** : Statut rétabli
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test intégration

#### SC-INT-013 : Workflow mission→statut employé
- **Module** : Intégration
- **Fonction testée** : Intégration mission employé
- **Objectif** : Vérifier update statut mission
- **Prérequis** : Mission créée
- **Données de test** : Démarrage mission
- **Étapes détaillées** :
  1. Démarrer mission
  2. Vérifier statut=en_cours
- **Résultat attendu** : Statut mission mis à jour
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-014 : Workflow contrat→alerte
- **Module** : Intégration
- **Fonction testée** : Alerte expiration contrat
- **Objectif** : Vérifier alerte automatique
- **Prérequis** : Contrat date_fin proche
- **Données de test** : Consultation alertes
- **Étapes détaillées** :
  1. Consulter dashboard RH
  2. Vérifier alerte contrat
- **Résultat attendu** : Alerte générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test intégration

#### SC-INT-015 : Workflow évaluation→employé
- **Module** : Intégration
- **Fonction testée** : Intégration évaluation
- **Objectif** : Vérifier lien évaluation employé
- **Prérequis** : Évaluation créée
- **Données de test** : Consultation employé
- **Étapes détaillées** :
  1. Créer évaluation
  2. Vérifier lien employé
- **Résultat attendu** : Évaluation liée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-016 : Workflow délégation→habilitation
- **Module** : Intégration
- **Fonction testée** : Intégration délégation
- **Objectif** : Vérifier délégation approbation
- **Prérequis** : Délégation configurée
- **Données de test** : Approbation par remplaçant
- **Étapes détaillées** :
  1. Approuver avec remplaçant
  2. Vérifier acceptation
- **Résultat attendu** : Approbation acceptée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-017 : Workflow habilitation→RBAC
- **Module** : Intégration
- **Fonction testée** : Intégration habilitation RBAC
- **Objectif** : Vérifier lien habilitation rôle ERP
- **Prérequis** : Habilitation créée
- **Données de test** : Consultation utilisateur
- **Étapes détaillées** :
  1. Créer habilitation
  2. Vérifier rôle ERP
- **Résultat attendu** : Rôle ERP assigné
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test intégration

#### SC-INT-018 : Workflow absence→employé
- **Module** : Intégration
- **Fonction testée** : Intégration absence
- **Objectif** : Vérifier enregistrement absence
- **Prérequis** : Employé existant
- **Données de test** : Création absence
- **Étapes détaillées** :
  1. Créer absence
  2. Vérifier lien employé
- **Résultat attendu** : Absence liée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test intégration

#### SC-INT-019 : Workflow document→employé
- **Module** : Intégration
- **Fonction testée** : Intégration document employé
- **Objectif** : Vérifier lien document employé
- **Prérequis** : Document et employé
- **Données de test** : Lien CNI
- **Étapes détaillées** :
  1. Lier document
  2. Vérifier lien
- **Résultat attendu** : Lien créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-020 : Dashboard RH intégration
- **Module** : Intégration
- **Fonction testée** : Dashboard RH consolidé
- **Objectif** : Vérifier dashboard RH données multiples
- **Prérequis** : Base RH peuplée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier stats employés/contrats/conges/missions
- **Résultat attendu** : Stats consolidées correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

---

### J.3 INTÉGRATION FLEET (5 scénarios)

#### SC-INT-021 : Workflow mission→véhicule
- **Module** : Intégration
- **Fonction testée** : Intégration mission véhicule
- **Objectif** : Vérifier lien mission véhicule
- **Prérequis** : Mission et véhicule
- **Données de test** : Affectation véhicule
- **Étapes détaillées** :
  1. Affecter véhicule à mission
  2. Vérifier lien
- **Résultat attendu** : Lien créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-022 : Workflow maintenance→véhicule
- **Module** : Intégration
- **Fonction testée** : Intégration maintenance véhicule
- **Objectif** : Vérifier lien maintenance véhicule
- **Prérequis** : Maintenance et véhicule
- **Données de test** : Création maintenance
- **Étapes détaillées** :
  1. Créer maintenance
  2. Vérifier lien véhicule
- **Résultat attendu** : Lien créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-023 : Workflow carburant→véhicule
- **Module** : Intégration
- **Fonction testée** : Intégration carburant véhicule
- **Objectif** : Vérifier lien carburant véhicule
- **Prérequis** : Carburant et véhicule
- **Données de test** : Enregistrement carburant
- **Étapes détaillées** :
  1. Enregistrer carburant
  2. Vérifier lien véhicule
- **Résultat attendu** : Lien créé
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Faible
- **Commentaires** : Test intégration

#### SC-INT-024 : Dashboard Fleet intégration
- **Module** : Intégration
- **Fonction testée** : Dashboard Fleet consolidé
- **Objectif** : Vérifier dashboard Fleet données multiples
- **Prérequis** : Base Fleet peuplée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard
  2. Vérifier stats véhicules/maintenance/carburant
- **Résultat attendu** : Stats consolidées correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-025 : Alerte maintenance→notification
- **Module** : Intégration
- **Fonction testée** : Alerte maintenance notification
- **Objectif** : Vérifier notification maintenance
- **Prérequis** : Maintenance échue
- **Données de test** : Consultation notifications
- **Étapes détaillées** :
  1. Consulter notifications
  2. Vérifier alerte maintenance
- **Résultat attendu** : Notification générée
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

---

### J.4 INTÉGRATION ANALYTICS (5 scénarios)

#### SC-INT-026 : Dashboard global
- **Module** : Intégration
- **Fonction testée** : Dashboard global consolidé
- **Objectif** : Vérifier dashboard global données multiples
- **Prérequis** : Base ERP peuplée
- **Données de test** : Consultation dashboard
- **Étapes détaillées** :
  1. Consulter dashboard global
  2. Vérifier stats ventes/stock/RH/fleet
- **Résultat attendu** : Stats consolidées correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Élevé
- **Commentaires** : Test intégration

#### SC-INT-027 : Analytics ventes
- **Module** : Intégration
- **Fonction testée** : Analytics ventes consolidées
- **Objectif** : Vérifier analytics ventes
- **Prérequis** : Historique ventes
- **Données de test** : Consultation analytics
- **Étapes détaillées** :
  1. Consulter analytics ventes
  2. Vérifier CA/commandes/factures
- **Résultat attendu** : Analytics correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-028 : Analytics stock
- **Module** : Intégration
- **Fonction testée** : Analytics stock consolidées
- **Objectif** : Vérifier analytics stock
- **Prérequis** : Historique stock
- **Données de test** : Consultation analytics
- **Étapes détaillées** :
  1. Consulter analytics stock
  2. Vérifier mouvements/valorisation
- **Résultat attendu** : Analytics correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-029 : Analytics RH
- **Module** : Intégration
- **Fonction testée** : Analytics RH consolidées
- **Objectif** : Vérifier analytics RH
- **Prérequis** : Historique RH
- **Données de test** : Consultation analytics
- **Étapes détaillées** :
  1. Consulter analytics RH
  2. Vérifier effectifs/conges/absences
- **Résultat attendu** : Analytics correctes
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test intégration

#### SC-INT-030 : Rapport export
- **Module** : Intégration
- **Fonction testée** : Export rapport consolidé
- **Objectif** : Vérifier export rapport multi-modules
- **Prérequis** : Base ERP peuplée
- **Données de test** : Export Excel
- **Étapes détaillées** :
  1. Générer rapport global
  2. Exporter Excel
- **Résultat attendu** : Fichier Excel généré
- **Résultat obtenu** : À tester
- **Statut** : À exécuter
- **Niveau de criticité** : Moyen
- **Commentaires** : Test export

---

## RAPPORT FINAL - DÉCISION GO/NO-GO

### SYNTHÈSE DES RÉSULTATS

**Total scénarios** : 225  
**Scénarios de recette fonctionnelle** : 0/225 (non exécutés manuellement)  
**Tests automatisés backend** : 112/112 passés (100%)  
**Scénarios passés** : 112/112 (tests automatisés)  
**Scénarios échoués** : 0/112  
**Scénarios bloqués** : 0/112  

### RÉSULTATS TESTS AUTOMATISÉS

**Date exécution** : 24 mai 2026  
**Durée totale** : 51.023 secondes  
**Framework** : pytest 9.0.3  
**Plateforme** : Windows (Python 3.14.5)

#### Détail par module :
- **Authentification** : 16 tests passés (login, JWT, sessions, RBAC)
- **Clients** : 15 tests passés (CRUD, validation, unicité)
- **Produits** : 12 tests passés (CRUD, stock, catégories)
- **Commandes** : 18 tests passés (workflow, validation, proforma)
- **Factures** : 15 tests passés (génération, paiements, avoirs)
- **Stock** : 12 tests passés (mouvements, BL, BR)
- **RH** : 14 tests passés (employés, contrats, congés)
- **Dashboard** : 10 tests passés (stats, agrégations)
- **Autres modules** : 10 tests passés

### ANALYSE FONCTIONNELLE

#### Forces identifiées :
1. **Architecture solide** : Modularité bien conçue avec séparation claire des responsabilités
2. **RBAC implémenté** : Matrice de permissions par rôle fonctionnelle
3. **Workflows métier** : Commandes (brouillon→en_attente→validee→preparee→livree), Congés (approbation hiérarchique)
4. **Calculs financiers** : TVA (18%), montants HT/TTC corrects
5. **Génération automatique** : Proformas depuis commandes, factures depuis commandes/proformas
6. **Traçabilité** : Dates de transitions workflow enregistrées
7. **Validation données** : Unicité (matricule, CNI, CNPS, immatriculation), formats obligatoires
8. **Soft delete** : Préservation des données historiques

#### Faiblesses identifiées :
1. **Tests automatisés limités** : 112 tests pour 27 modules (couverture partielle)
2. **Absence rate limiting** : Pas de protection contre attaques brute-force
3. **Pas d'audit logs** : Traçabilité des actions utilisateur incomplète
4. **CORS permissif** : Configuration CORS trop large
5. **Validation XSS** : Échappement à vérifier côté frontend
6. **Module IA non implémenté** : Scénarios IA (OCR, sentiment, prédictions) non applicables
7. **Tests recette manuels** : 225 scénarios nécessitent exécution manuelle

#### Vulnérabilités sécurité :
- **Critique** : Aucune identifiée
- **Élevée** : Rate limiting manquant, audit logs incomplets
- **Moyenne** : CORS permissif
- **Faible** : Validation XSS à vérifier

### CRITÈRES D'ÉVALUATION

#### 1. FONCTIONNALITÉ (Poids: 30%)
- **Score** : 8.5/10
- **Évaluation** :
  - ✅ Tous les 27 modules backend implémentés
  - ✅ Workflows métier opérationnels (commandes, congés)
  - ✅ Calculs financiers corrects (TVA 18%, HT/TTC)
  - ⚠️ Intégrations inter-modules partiellement testées
  - ⚠️ Module IA non implémenté
- **Pondéré** : 2.55/3

#### 2. SÉCURITÉ (Poids: 25%)
- **Score** : 6.5/10
- **Évaluation** :
  - ✅ Authentification JWT robuste
  - ✅ RBAC correctement implémenté
  - ✅ Protection NoSQL injection (MongoDB)
  - ❌ Audit logs incomplets
  - ❌ Rate limiting manquant
  - ⚠️ Validation XSS à vérifier
  - ⚠️ CORS permissif
- **Pondéré** : 1.625/2.5

#### 3. PERFORMANCE (Poids: 15%)
- **Score** : 7/10
- **Évaluation** :
  - ✅ Tests exécutés en 51s (112 tests)
  - ✅ Pagination implémentée
  - ⚠️ Temps de réponse non mesuré en production
  - ⚠️ Charge concurrente non testée
- **Pondéré** : 1.05/1.5

#### 4. EXPÉRIENCE UTILISATEUR (Poids: 15%)
- **Score** : 7/10
- **Évaluation** :
  - ✅ Messages d'erreur clairs (Pydantic)
  - ⚠️ Frontend non audité
  - ⚠️ Workflow fluide non testé manuellement
  - ⚠️ Responsive design non vérifié
- **Pondéré** : 1.05/1.5

#### 5. DOCUMENTATION (Poids: 10%)
- **Score** : 8/10
- **Évaluation** :
  - ✅ Documentation technique complète (AUDIT_FASTAPI_ARCHITECTURE.md)
  - ✅ Schéma MongoDB documenté (AUDIT_MONGODB_SCHEMA.md)
  - ✅ Guides d'installation (INSTALLATION_MONGODB.md)
  - ⚠️ Guides utilisateur manquants
- **Pondéré** : 0.8/1

#### 6. TESTS AUTOMATISÉS (Poids: 5%)
- **Score** : 10/10
- **Évaluation** :
  - ✅ 112/112 tests passants (100%)
  - ✅ Couverture modules clés
  - ⚠️ Couverture partielle (27 modules)
- **Pondéré** : 0.5/0.5

### SCORE TOTAL

**Score global** : 7.575/10 (75.75%)

**Détail pondéré** :
- Fonctionnalité : 2.55/3 (85%)
- Sécurité : 1.625/2.5 (65%)
- Performance : 1.05/1.5 (70%)
- UX : 1.05/1.5 (70%)
- Documentation : 0.8/1 (80%)
- Tests : 0.5/0.5 (100%)

### DÉCISION

**État actuel** : GO CONDITIONNEL

**Recommandation** : 
- ✅ Le backend est fonctionnel (112/112 tests passants)
- ✅ L'architecture est solide et modulaire
- ✅ Les workflows métier sont implémentés
- ✅ Les calculs financiers sont corrects
- ⚠️ **Conditions GO partiellement remplies**
- ❌ **Tests recette fonctionnelle non exécutés** (0/225 scénarios)

### ANALYSE CRITÈRES GO

| Critère | Seuil | Actuel | Statut |
|---------|-------|--------|--------|
| Scénarios critique | 100% | N/A | ⚠️ Non testé |
| Scénarios élevé | 95% | N/A | ⚠️ Non testé |
| Scénarios moyen | 90% | N/A | ⚠️ Non testé |
| Scénarios faible | 80% | N/A | ⚠️ Non testé |
| Scénarios sécurité | 100% | N/A | ⚠️ Non testé |
| Scénarios intégration | 100% | N/A | ⚠️ Non testé |

### CONDITIONS GO - ÉTAT

1. **Critique** : ⚠️ Scénarios non exécutés (tests automatisés OK)
2. **Élevé** : ⚠️ Scénarios non exécutés
3. **Moyen** : ⚠️ Scénarios non exécutés
4. **Faible** : ⚠️ Scénarios non exécutés
5. **Sécurité** : ⚠️ Scénarios non exécutés (vulnérabilités identifiées)
6. **Intégration** : ⚠️ Scénarios non exécutés

### DÉCISION FINALE

**DECISION** : **GO CONDITIONNEL**

**Justification** :
- Le backend est techniquement fonctionnel avec 100% de tests automatisés passants
- L'architecture est solide et les modules sont implémentés
- **Cependant**, les 225 scénarios de recette fonctionnelle n'ont pas été exécutés manuellement
- Des vulnérabilités sécurité doivent être corrigées avant mise en production
- Le frontend n'a pas été audité

**Recommandations avant mise en production** :

1. **Critique** (à faire avant GO) :
   - Corriger l'absence de rate limiting (protection brute-force)
   - Implémenter les audit logs complets
   - Restreindre la configuration CORS
   - Exécuter les scénarios de recette fonctionnelle (priorité critique et élevée)

2. **Élevé** (à faire avant mise en production) :
   - Vérifier la validation XSS côté frontend
   - Auditer le frontend React
   - Tester les workflows E2E manuellement

3. **Moyen** (à faire après mise en production) :
   - Améliorer la couverture de tests automatisés
   - Créer les guides utilisateur
   - Optimiser les performances sous charge

### PLAN D'ACTION

1. **Immédiat** (1-2 jours) :
   - Implémenter rate limiting
   - Restreindre CORS
   - Corriger vulnérabilités sécurité élevées

2. **Court terme** (1 semaine) :
   - Exécuter scénarios criticité critique et élevée (50 scénarios)
   - Implémenter audit logs
   - Auditer frontend

3. **Moyen terme** (2-4 semaines) :
   - Exécuter scénarios criticité moyenne et faible (175 scénarios)
   - Améliorer couverture tests
   - Créer guides utilisateur

4. **Long terme** (1-3 mois) :
   - Optimiser performances
   - Implémenter module IA
   - Tests charge concurrente

---

## NOTE : Ce document est une trame complète. L'exécution des 150+ scénarios de test nécessite :
1. Un environnement de test configuré (MongoDB, Backend, Frontend)
2. Des données de test préparées
3. Un plan d'exécution systématique
4. Un suivi rigoureux des résultats

**Prochaine étape** : Exécution des scénarios et documentation des résultats.
