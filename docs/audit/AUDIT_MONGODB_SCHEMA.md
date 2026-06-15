# AUDIT MONGODB SCHEMA
## ERP EDITIONS FABS-CI - Phase 0 Sprint 0.1

**Date**: 31 Mai 2026  
**Auditeur**: Cascade AI  
**Version Analyse**: 1.0.0 Production Ready  
**Base de données**: MongoDB (via Motor async driver)

---

## 1. COLLECTIONS MONGODB IDENTIFIÉES

### 1.1 Collections Principales

| Collection | Description | Statut |
|------------|-------------|--------|
| `users` | Utilisateurs et authentification | ✅ Implémenté |
| `clients` | Gestion des clients | ✅ Implémenté |
| `produits` | Catalogue produits | ✅ Implémenté |
| `commandes` | En-tête des commandes | ✅ Implémenté |
| `commande_lignes` | Lignes de commande | ✅ Implémenté |
| `factures` | En-tête des factures/avoirs | ✅ Implémenté |
| `facture_lignes` | Lignes de facture | ✅ Implémenté |
| `paiements` | Paiements clients | ✅ Implémenté |
| `affectations_paiement` | Affectation paiements aux factures | ✅ Implémenté |
| `mouvements_stock` | Mouvements de stock | ✅ Implémenté |
| `bons_livraison` | Bons de livraison | ✅ Implémenté |
| `bl_lignes` | Lignes de bon de livraison | ✅ Implémenté |
| `bons_retour` | Bons de retour | ✅ Implémenté |
| `br_lignes` | Lignes de bon de retour | ✅ Implémenté |
| `parametres` | Paramètres système | ✅ Implémenté |
| `counters` | Compteurs auto-incrémentés | ✅ Implémenté |
| `documents_intelligents` | Documents AI parsés | ✅ Implémenté |
| `ecritures_comptables` | Écritures comptables | ✅ Implémenté |

**Total collections**: 18

---

## 2. SCHÉMA DÉTAILLÉ PAR COLLECTION

### 2.1 Collection `users`

**Champs**:
- `user_id` (string, unique) - Identifiant unique
- `email` (string, unique) - Email de connexion
- `nom_complet` (string) - Nom complet
- `role` (enum) - Rôle parmi: super_admin, directeur_general, directeur_commercial, comptable, gestionnaire_stock, responsable_magasinier, secretariat, service_logistique
- `actif` (boolean) - Statut du compte
- `password_hash` (string, nullable) - Hash bcrypt du mot de passe
- `picture` (string, nullable) - URL avatar
- `created_at` (ISO datetime) - Date de création
- `updated_at` (ISO datetime) - Date de modification

**Index**:
- `user_id` (unique)
- `email` (unique)

**Observations**:
- ✅ Password hashé avec bcrypt
- ✅ Soft delete via `actif`
- ✅ Timestamps présents
- ⚠️ Pas de champ `deletedAt` explicite (utilise `actif`)

---

### 2.2 Collection `clients`

**Champs**:
- `client_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-CLI-XXXX
- `nom` (string) - Nom du client
- `type_client` (enum) - librairie, ecole, particulier, distributeur, representant
- `representant` (string) - Nom du représentant commercial
- `representative_id` (string, nullable) - ID du représentant (legacy)
- `representative_nom` (string, nullable) - Nom du représentant (legacy lookup)
- `telephone` (string, nullable) - Téléphone
- `email` (string, nullable) - Email
- `adresse` (string, nullable) - Adresse
- `ville` (string, nullable) - Ville
- `solde` (float) - Solde client
- `plafond_credit` (float) - Plafond de crédit
- `actif` (boolean) - Statut
- `notes` (string, nullable) - Notes
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `client_id` (unique)
- `reference` (unique)
- `nom` (pour recherche)
- `ville` (pour filtre)

**Observations**:
- ✅ Détection de doublons via Levenshtein
- ✅ Soft delete via `actif`
- ✅ Référence auto-incrémentée via `counters`
- ⚠️ Champs legacy `representative_id` et `representative_nom` (duplication avec `representant`)

---

### 2.3 Collection `produits`

**Champs**:
- `product_id` (string, unique) - Identifiant unique
- `produit_id` (string, nullable) - Legacy field
- `reference` (string, unique) - Référence FABS-PRD-XXXX
- `code_article` (string) - Code article
- `titre` (string) - Titre du produit
- `auteur` (string, nullable) - Auteur
- `collection` (string, nullable) - Collection
- `categorie` (enum) - maternelle, primaire, premier_cycle, second_cycle, litterature, livre_commun
- `niveau_scolaire` (string, nullable) - Niveau scolaire
- `isbn` (string, nullable) - ISBN
- `prix_achat` (float, nullable) - Prix d'achat (visible seulement pour rôles financiers)
- `prix_vente` (float) - Prix de vente
- `stock_actuel` (int) - Stock actuel
- `stock_minimum` (int) - Stock minimum (legacy: `seuil_alerte`)
- `statut_stock` (computed) - ok, alerte, rupture
- `actif` (boolean) - Statut
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `product_id` (unique)
- `reference` (unique)
- `isbn` (pour recherche)
- `categorie` (pour filtre)
- `stock_actuel` (pour alertes)

**Observations**:
- ✅ Computed field `statut_stock`
- ✅ Lookup ISBN via Google Books API
- ✅ Prix_achat masqué pour non-financiers
- ⚠️ Champs legacy: `produit_id`, `seuil_alerte`
- ⚠️ Normalisation catégorie legacy → littéral

---

### 2.4 Collection `commandes`

**Champs**:
- `commande_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-CMD-26-27-XXXX
- `client_id` (string) - ID client
- `client_nom` (string, computed) - Nom client (enrichi)
- `statut` (enum) - brouillon, en_attente, validee, preparee, livree, annulee
- `date_commande` (date) - Date commande
- `date_livraison_prevue` (date, nullable) - Date livraison prévue
- `date_validation` (date, nullable) - Date validation
- `date_preparation` (date, nullable) - Date préparation
- `date_livraison` (date, nullable) - Date livraison
- `remise_globale` (float) - Remise globale %
- `montant_ht` (float) - Montant HT
- `montant_remise` (float) - Montant remise
- `montant_total` (float) - Montant total
- `notes` (string, nullable) - Notes
- `motif_annulation` (string, nullable) - Motif annulation
- `created_by` (string) - ID créateur
- `validated_by` (string, nullable) - ID validateur
- `prepared_by` (string, nullable) - ID préparateur
- `delivered_by` (string, nullable) - ID livreur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `commande_id` (unique)
- `reference` (unique)
- `client_id` (pour jointure)
- `statut` (pour filtre)
- `date_commande` (pour tri)

**Workflow**: brouillon → en_attente → validee → preparee → livree → annulee

**Règles métier**:
- Validation DG obligatoire si montant > 500 000 FCFA
- Modification possible uniquement sur statut brouillon
- Annulation impossible si livrée

**Observations**:
- ✅ Workflow complet avec guards RBAC
- ✅ Génération automatique facture à validation
- ✅ Référence auto-incrémentée
- ⚠️ Pas de champ `deletedAt` (soft delete via annulation)

---

### 2.5 Collection `commande_lignes`

**Champs**:
- `ligne_id` (string, unique) - Identifiant unique
- `commande_id` (string) - ID commande parent
- `produit_id` (string) - ID produit
- `produit_reference` (string, computed) - Référence produit (enrichi)
- `produit_titre` (string, computed) - Titre produit (enrichi)
- `quantite` (int) - Quantité
- `prix_unitaire` (float) - Prix unitaire
- `remise_ligne` (float) - Remise ligne %
- `montant_ligne` (float) - Montant ligne (calculé)

**Index**:
- `ligne_id` (unique)
- `commande_id` (pour jointure)
- `produit_id` (pour jointure)

**Observations**:
- ✅ Calcul automatique montant_ligne
- ✅ Enrichissement avec infos produit
- ⚠️ Pas de contrainte d'intégrité référentielle (MongoDB)

---

### 2.6 Collection `factures`

**Champs**:
- `facture_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-FC-26-27-XXXX (facture) ou FABS-AV-26-27-XXXX (avoir)
- `type_facture` (enum) - facture, avoir
- `client_id` (string) - ID client
- `client_nom` (string, computed) - Nom client (enrichi)
- `commande_id` (string, nullable) - ID commande source
- `commande_reference` (string, computed) - Référence commande (enrichi)
- `statut` (enum) - brouillon, emise, partiellement_payee, payee, annulee
- `date_facture` (date) - Date facture
- `date_echeance` (date, nullable) - Date échéance
- `date_emission` (date, nullable) - Date émission
- `remise_globale` (float) - Remise globale %
- `montant_ht` (float) - Montant HT
- `montant_tva` (float) - Montant TVA (18%)
- `montant_ttc` (float) - Montant TTC
- `montant_regle` (float) - Montant réglé
- `montant_restant` (float) - Montant restant
- `notes` (string, nullable) - Notes
- `facture_origine_id` (string, nullable) - ID facture origine (pour avoirs)
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `facture_id` (unique)
- `reference` (unique)
- `client_id` (pour jointure)
- `commande_id` (pour jointure)
- `statut` (pour filtre)
- `date_facture` (pour tri)

**Workflow**: brouillon → emise → partiellement_payee → payee

**Observations**:
- ✅ TVA 18% configurée
- ✅ Génération avoirs automatique
- ✅ Statut auto-update selon paiements
- ✅ Références distinctes facture/avoir
- ⚠️ Avoirs avec montants négatifs (design choice)

---

### 2.7 Collection `facture_lignes`

**Champs**:
- `ligne_id` (string, unique) - Identifiant unique
- `facture_id` (string) - ID facture parent
- `produit_id` (string) - ID produit
- `designation` (string) - Désignation produit
- `quantite` (int) - Quantité
- `prix_unitaire` (float) - Prix unitaire
- `remise_ligne` (float) - Remise ligne %
- `montant_ht` (float) - Montant HT

**Index**:
- `ligne_id` (unique)
- `facture_id` (pour jointure)
- `produit_id` (pour jointure)

**Observations**:
- ✅ Montants négatifs pour avoirs
- ✅ Calcul automatique montant_ht

---

### 2.8 Collection `paiements`

**Champs**:
- `paiement_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-REG-2026-XXXX
- `client_id` (string) - ID client
- `client_nom` (string, computed) - Nom client (enrichi)
- `date_paiement` (date) - Date paiement
- `mode_paiement` (enum) - especes, cheque, virement, mobile_money
- `montant_total` (float) - Montant total
- `montant_affecte` (float) - Montant affecté aux factures
- `montant_non_affecte` (float) - Montant non affecté
- `banque` (string, nullable) - Banque (chèque)
- `numero_cheque` (string, nullable) - Numéro chèque
- `reference_virement` (string, nullable) - Référence virement
- `operateur` (string, nullable) - Opérateur mobile money
- `numero_transaction` (string, nullable) - Numéro transaction
- `notes` (string, nullable) - Notes
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `paiement_id` (unique)
- `reference` (unique)
- `client_id` (pour jointure)
- `date_paiement` (pour tri)
- `mode_paiement` (pour filtre)

**Observations**:
- ✅ 4 modes de paiement
- ✅ Affectation multiple factures
- ✅ Auto-update factures après paiement
- ✅ Référence avec année courante

---

### 2.9 Collection `affectations_paiement`

**Champs**:
- `affectation_id` (string, unique) - Identifiant unique
- `paiement_id` (string) - ID paiement
- `facture_id` (string) - ID facture
- `montant_affecte` (float) - Montant affecté
- `created_at` (ISO datetime) - Date création

**Index**:
- `affectation_id` (unique)
- `paiement_id` (pour jointure)
- `facture_id` (pour jointure)

**Observations**:
- ✅ Table d'association paiement-facture
- ✅ Supporte affectation partielle
- ⚠️ Pas de contrainte d'unicité (même paiement peut affecter plusieurs fois même facture)

---

### 2.10 Collection `mouvements_stock`

**Champs**:
- `mouvement_id` (string, unique) - Identifiant unique
- `produit_id` (string) - ID produit
- `produit_reference` (string, computed) - Référence produit (enrichi)
- `produit_titre` (string, computed) - Titre produit (enrichi)
- `type_mouvement` (enum) - entree, sortie, ajustement, retour, specimen_gratuit
- `quantite` (int) - Quantité
- `stock_avant` (int) - Stock avant mouvement
- `stock_apres` (int) - Stock après mouvement
- `commande_id` (string, nullable) - ID commande liée
- `bl_id` (string, nullable) - ID bon de livraison lié
- `motif` (string, nullable) - Motif
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création

**Index**:
- `mouvement_id` (unique)
- `produit_id` (pour jointure)
- `type_mouvement` (pour filtre)
- `created_at` (pour tri)

**Observations**:
- ✅ Historique complet stock
- ✅ Auto-update stock produit
- ✅ 5 types de mouvements
- ✅ Utilisation $inc pour éviter race conditions

---

### 2.11 Collection `bons_livraison`

**Champs**:
- `bl_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-BL-26-27-XXXX
- `commande_id` (string) - ID commande source
- `commande_reference` (string, computed) - Référence commande (enrichi)
- `client_id` (string) - ID client
- `client_nom` (string, computed) - Nom client (enrichi)
- `statut` (enum) - en_preparation, pret, livre, annule
- `date_creation` (date) - Date création
- `date_livraison_prevue` (date, nullable) - Date livraison prévue
- `date_livraison_reelle` (date, nullable) - Date livraison réelle
- `notes` (string, nullable) - Notes
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `bl_id` (unique)
- `reference` (unique)
- `commande_id` (pour jointure)
- `statut` (pour filtre)

**Workflow**: en_preparation → pret → livre

**Observations**:
- ✅ Auto-update commande statut à livraison
- ✅ Auto-update stock à livraison
- ✅ Génération mouvements stock automatique
- ✅ Référence auto-incrémentée

---

### 2.12 Collection `bl_lignes`

**Champs**:
- `ligne_id` (string, unique) - Identifiant unique
- `bl_id` (string) - ID bon de livraison parent
- `produit_id` (string) - ID produit
- `quantite` (int) - Quantité

**Index**:
- `ligne_id` (unique)
- `bl_id` (pour jointure)
- `produit_id` (pour jointure)

**Observations**:
- ✅ Structure simple
- ⚠️ Pas de champs enrichis (computed)

---

### 2.13 Collection `bons_retour`

**Champs**:
- `br_id` (string, unique) - Identifiant unique
- `reference` (string, unique) - Référence FABS-BR-26-27-XXXX
- `facture_id` (string) - ID facture source
- `facture_reference` (string, computed) - Référence facture (enrichi)
- `client_id` (string) - ID client
- `client_nom` (string, computed) - Nom client (enrichi)
- `statut` (enum) - en_attente, valide, avoir_genere, annule
- `date_retour` (date) - Date retour
- `date_validation` (date, nullable) - Date validation
- `montant_total_ht` (float) - Montant total HT
- `montant_total_ttc` (float) - Montant total TTC
- `avoir_id` (string, nullable) - ID avoir généré
- `avoir_reference` (string, computed) - Référence avoir (enrichi)
- `motif_global` (string) - Motif global
- `created_by` (string) - ID créateur
- `validated_by` (string, nullable) - ID validateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `br_id` (unique)
- `reference` (unique)
- `facture_id` (pour jointure)
- `statut` (pour filtre)

**Workflow**: en_attente → valide → avoir_genere

**Observations**:
- ✅ Génération automatique avoir à validation
- ✅ Auto-update stock (entrée retour)
- ✅ Auto-update facture (avoir)
- ✅ Référence auto-incrémentée

---

### 2.14 Collection `br_lignes`

**Champs**:
- `ligne_id` (string, unique) - Identifiant unique
- `br_id` (string) - ID bon de retour parent
- `produit_id` (string) - ID produit
- `quantite` (int) - Quantité
- `prix_unitaire` (float) - Prix unitaire
- `motif` (string) - Motif

**Index**:
- `ligne_id` (unique)
- `br_id` (pour jointure)
- `produit_id` (pour jointure)

**Observations**:
- ✅ Motif par ligne
- ✅ Prix unitaire pour calcul avoir

---

### 2.15 Collection `parametres`

**Champs**:
- `cle` (string, unique) - Clé du paramètre
- `valeur` (string) - Valeur
- `description` (string, nullable) - Description
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `cle` (unique)

**Paramètres par défaut**:
- entreprise_nom
- entreprise_slogan
- entreprise_telephone
- entreprise_email
- entreprise_adresse
- tva_taux (18%)
- banque_principale
- banque_iban
- seuil_validation_dg (500000 FCFA)

**Observations**:
- ✅ Configuration centralisée
- ✅ Valeurs stockées en string (conversion au runtime)
- ✅ DG en lecture seule sur paramètres

---

### 2.16 Collection `counters`

**Champs**:
- `_id` (string, unique) - Identifiant du compteur
- `seq` (int) - Séquence actuelle

**Compteurs**:
- `clients` - Pour FABS-CLI-XXXX
- `produits` - Pour FABS-PRD-XXXX
- `commandes` - Pour FABS-CMD-26-27-XXXX
- `factures` - Pour FABS-FC-26-27-XXXX
- `avoirs` - Pour FABS-AV-26-27-XXXX
- `paiements` - Pour FABS-REG-2026-XXXX
- `bons_livraison` - Pour FABS-BL-26-27-XXXX
- `bons_retour` - Pour FABS-BR-26-27-XXXX

**Observations**:
- ✅ Atomic increment via find_one_and_update
- ✅ Persistance des séquences
- ✅ Upsert automatique

---

### 2.17 Collection `documents_intelligents`

**Champs**:
- `document_id` (string, unique) - Identifiant unique
- `nom_fichier` (string) - Nom du fichier
- `type_document` (enum) - BON_LIVRAISON, FACTURE, COMMANDE, LISTE_CLIENTS, AUTRE
- `reference` (string, nullable) - Référence extraite
- `statut` (enum) - en_attente, traite, erreur
- `donnees_extraites` (object) - Données extraites (JSON)
- `tags` (array) - Tags
- `taille_fichier` (int) - Taille fichier
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création
- `updated_at` (ISO datetime) - Date modification

**Index**:
- `document_id` (unique)
- `type_document` (pour filtre)
- `statut` (pour filtre)

**Observations**:
- ✅ Détection automatique type document
- ✅ Parsing intelligent contenu
- ✅ Extraction référence FABS
- ✅ Analytics dashboard intégré

---

### 2.18 Collection `ecritures_comptables`

**Champs**:
- `ecriture_id` (string, unique) - Identifiant unique
- `journal` (enum) - ventes, achats, banque, caisse, operations_diverses
- `date_ecriture` (date) - Date écriture
- `compte` (string) - Numéro de compte
- `libelle` (string) - Libellé
- `debit` (float) - Débit
- `credit` (float) - Crédit
- `piece_reference` (string, nullable) - Référence pièce
- `created_by` (string) - ID créateur
- `created_at` (ISO datetime) - Date création

**Index**:
- `ecriture_id` (unique)
- `journal` (pour filtre)
- `date_ecriture` (pour tri)
- `compte` (pour agrégation)

**Observations**:
- ✅ 5 types de journaux
- ✅ Balance et grand livre
- ✅ Créances clients agrégées
- ⚠️ Pas de plan comptable structuré (comptes libres)

---

## 3. CARTOGRAPHIE MODÈLES VS ATTENDUS (PROMPT)

### 3.1 Modèles Présents et Corrects ✅

| Modèle Prompt | Collection MongoDB | Statut |
|---------------|-------------------|--------|
| users | `users` | ✅ |
| clients | `clients` | ✅ |
| products | `produits` | ✅ |
| orders | `commandes` + `commande_lignes` | ✅ |
| invoices | `factures` + `facture_lignes` | ✅ |
| payments | `paiements` + `affectations_paiement` | ✅ |
| inventory | `produits` (stock_actuel) + `mouvements_stock` | ✅ |
| packaging | Non implémenté | ❌ |
| shipping | `bons_livraison` + `bl_lignes` | ✅ |
| delivery | Intégré dans `bons_livraison` | ✅ |
| logistics | `bons_livraison` | ✅ |
| logistics-costs | Non implémenté | ❌ |
| logistics-missions | Non implémenté | ❌ |
| fleet | Non implémenté | ❌ |
| vehicles | Non implémenté | ❌ |
| insurances | Non implémenté | ❌ |
| technical-inspections | Non implémenté | ❌ |
| vehicle-assignments | Non implémenté | ❌ |
| maintenance | Non implémenté | ❌ |
| fuel | Non implémenté | ❌ |
| accounting | `ecritures_comptables` | ✅ |
| general-ledger | Agrégation `ecritures_comptables` | ✅ |
| journal-entries | `ecritures_comptables` | ✅ |
| chart-of-accounts | Non implémenté (comptes libres) | ❌ |
| accounting-periods | Non implémenté | ❌ |
| bank-transactions | Non implémenté | ❌ |
| bank-reconciliation | Non implémenté | ❌ |
| internal-expenses | Non implémenté | ❌ |
| reports | `rapports_module.py` | ✅ |
| notifications | Non implémenté | ❌ |
| notification-events | Non implémenté | ❌ |
| notification-templates | Non implémenté | ❌ |
| notification-channels | Non implémenté | ❌ |
| realtime-gateway | Non implémenté | ❌ |
| audit | Non implémenté | ❌ |
| settings | `parametres` | ✅ |
| file-storage | Non implémenté | ❌ |
| business-intelligence | `analytics_module.py` | ✅ |
| mobile | Non implémenté | ❌ |
| pwa | Non implémenté | ❌ |

### 3.2 Modèles Présents mais Incomplets ⚠️

| Modèle | Champs Manquants | Priorité |
|--------|-----------------|----------|
| `produits` | - Champs logistique (poids, dimensions) | Moyenne |
| `commandes` | - Champs logistique (adresse livraison) | Moyenne |
| `factures` | - Champs avancés (conditions paiement) | Faible |
| `ecritures_comptables` | - Plan comptable structuré | Haute |
| `users` | - Profil utilisateur étendu | Faible |

### 3.3 Modèles Manquants ❌

| Modèle Prompt | Description | Priorité |
|---------------|-------------|----------|
| Vehicle | Gestion véhicules flotte | Haute (Phase 10) |
| Insurance | Assurances véhicules | Haute (Phase 10) |
| TechnicalInspection | Visites techniques | Haute (Phase 10) |
| LogisticsMission | Missions logistiques | Haute (Phase 10) |
| LogisticsCost | Coûts logistiques | Haute (Phase 10) |
| ChartOfAccounts | Plan comptable structuré | Haute (Phase 17) |
| AccountingPeriod | Périodes comptables | Moyenne (Phase 17) |
| BankTransaction | Transactions bancaires | Moyenne (Phase 17) |
| NotificationEvent | Événements notifications | Haute (Phase 12) |
| NotificationTemplate | Templates notifications | Moyenne (Phase 12) |
| AuditLog | Logs d'audit | Critique (Sécurité) |
| Packaging | Colisage détaillé | Moyenne (Phase 9) |

### 3.4 Modèles Obsolètes à Nettoyer 🗑️

| Collection | Raison | Action |
|------------|--------|--------|
| `produits.produit_id` | Legacy field | Supprimer après migration |
| `produits.seuil_alerte` | Remplacé par `stock_minimum` | Supprimer après migration |
| `clients.representative_id` | Legacy field | Supprimer après migration |
| `clients.representative_nom` | Legacy lookup | Supprimer après migration |

---

## 4. CHECKLIST QUALITÉ MONGODB

### 4.1 Conventions de Nommage ✅

- ✅ Collections en snake_case
- ✅ Champs en snake_case
- ✅ IDs avec suffixe explicite (`_id`)
- ✅ Enums en snake_case
- ✅ Dates ISO 8601
- ✅ Timestamps `created_at`, `updated_at` présents

### 4.2 Sécurité des Données ✅

- ✅ Mots de passe hashés avec bcrypt
- ✅ Données sensibles identifiées (`prix_achat` masqué)
- ✅ Soft delete via `actif` sur collections principales
- ✅ Timestamps présents sur tous les modèles
- ⚠️ Pas de chiffrement au repos (MongoDB)
- ⚠️ Pas de champ `deletedAt` explicite

### 4.3 Performance ⚠️

- ✅ Index sur clés étrangères principales
- ✅ Index sur champs de recherche (nom, reference, email)
- ✅ Index sur filtres fréquents (statut, type, date)
- ⚠️ Pas d'index composite optimisés
- ⚠️ Pas d'index sur `created_at` pour toutes les collections
- ⚠️ Potentiels N+1 sur enrichissements (client_nom, produit_titre)

### 4.4 Intégrité ⚠️

- ✅ Contraintes d'unicité sur IDs et références
- ⚠️ Pas de contraintes d'intégrité référentielle (MongoDB)
- ⚠️ Pas de cascades delete/update (géré manuellement)
- ✅ Enums pour statuts
- ✅ Valeurs par défaut définies
- ⚠️ Pas de transactions multi-documents (sauf atomic $inc)

---

## 5. ISSUES IDENTIFIÉES

### 5.1 Issues Critiques 🔴

| ID | Issue | Impact | Solution |
|----|-------|--------|----------|
| CRIT-001 | Pas de logs d'audit système | Sécurité | Créer collection `audit_logs` |
| CRIT-002 | Pas de contraintes d'intégrité référentielle | Intégrité données | Implémenter validation applicative stricte |
| CRIT-003 | Pas de chiffrement au repos | Sécurité | Configurer MongoDB encryption ou application-level |

### 5.2 Issues Élevées 🟠

| ID | Issue | Impact | Solution |
|----|-------|--------|----------|
| HIGH-001 | Modules flotte/logistique manquants | Fonctionnalité | Implémenter Phase 10 |
| HIGH-002 | Notifications manquantes | Fonctionnalité | Implémenter Phase 12 |
| HIGH-003 | Plan comptable non structuré | Comptabilité | Créer collection `chart_of_accounts` |
| HIGH-004 | Potentiels N+1 sur enrichissements | Performance | Optimiser avec $lookup ou cache |

### 5.3 Issues Moyennes 🟡

| ID | Issue | Impact | Solution |
|----|-------|--------|----------|
| MED-001 | Champs legacy à migrer | Maintenance | Script migration nettoyage |
| MED-002 | Index composites manquants | Performance | Ajouter index composites |
| MED-003 | Pas de transactions multi-documents | Intégrité | Utiliser MongoDB sessions transactions |
| MED-004 | Périodes comptables manquantes | Comptabilité | Créer collection `accounting_periods` |

### 5.4 Issues Faibles 🟢

| ID | Issue | Impact | Solution |
|----|-------|--------|----------|
| LOW-001 | Pas de champ `deletedAt` explicite | Audit | Ajouter `deletedAt` aux soft deletes |
| LOW-002 | Index `created_at` manquant sur certaines collections | Performance | Ajouter index uniforme |
| LOW-003 | Profil utilisateur limité | UX | Étendre collection `users` |

---

## 6. RECOMMANDATIONS PRIORITAIRES

### 6.1 Immédiat (Sprint 0.2)

1. **Créer collection `audit_logs`** pour tracer toutes les actions sensibles
2. **Ajouter index composites** sur les requêtes fréquentes
3. **Nettoyer champs legacy** après vérification compatibilité

### 6.2 Court Terme (Phase 1-2)

1. **Implémenter modules flotte/logistique** (Phase 10)
2. **Implémenter système notifications** (Phase 12)
3. **Structurer plan comptable** (Phase 17)

### 6.3 Moyen Terme (Phase 3+)

1. **Optimiser N+1** avec $lookup MongoDB ou cache Redis
2. **Implémenter transactions** pour opérations multi-documents
3. **Ajouter chiffrement au repos** si requis

---

## 7. CONCLUSION

**État Global**: 🟡 **BON** - Schéma fonctionnel mais extensions requises

**Score**: 7/10

**Points Forts**:
- ✅ Schéma cohérent et bien structuré
- ✅ Conventions de nommage respectées
- ✅ Workflow métier complet (commandes → factures → paiements)
- ✅ RBAC implémenté
- ✅ Soft delete sur collections principales
- ✅ Références auto-incrémentées
- ✅ Timestamps systématiques

**Points Faibles**:
- ❌ Modules flotte/logistique manquants (critique pour Phase 10)
- ❌ Notifications manquantes (critique pour Phase 12)
- ❌ Audit logs manquants (critique sécurité)
- ⚠️ Pas de contraintes d'intégrité référentielle
- ⚠️ Champs legacy à nettoyer
- ⚠️ Optimisations performance possibles

**Prochaine Action**: Passer au Sprint 0.2 - Audit Architecture Backend NestJS (adapté FastAPI)
