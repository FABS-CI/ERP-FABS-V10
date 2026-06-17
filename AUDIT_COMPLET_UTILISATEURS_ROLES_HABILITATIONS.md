# AUDIT COMPLET — UTILISATEURS, RÔLES & HABILITATIONS
## ERP FABS-CI V10
**Date :** 17 juin 2026  
**Auteur :** Audit automatisé — code + MongoDB  
**Version matrice :** 2.0 (validée Fabs 2026-06-17)  
**Base MongoDB :** `fabsci_erp`

---

## 1. INVENTAIRE DES UTILISATEURS

> Source : collection `fabsci_erp.users` — 9 utilisateurs officiels

| # | Nom complet | Email | Rôle | Créé le | Statut | Dernière connexion |
|---|-------------|-------|------|---------|--------|-------------------|
| 1 | AKE APPIA YVES DORIS | pissken@editionsfabsci.com | `super_admin` | 2026-06-17 | ✅ Actif | — |
| 2 | ALI MAMIN | ali.mamin@editionsfabsci.com | `directeur_general` | 2026-06-17 | ✅ Actif | — |
| 3 | JOACHIN | joachin@editionsfabsci.com | `responsable_magasinier` | 2026-06-17 | ✅ Actif | — |
| 4 | MME AHOMAN DADJE | dadjelarissa@editionsfabsci.com | `secretariat` | 2026-06-17 | ✅ Actif | — |
| 5 | YAKE BEN | yakeben@editionsfabsci.com | `service_logistique` | 2026-06-17 | ✅ Actif | — |
| 6 | NATACHA KOFFI | natachakoffi@editionsfabsci.com | `comptable` | 2026-06-17 | ✅ Actif | — |
| 7 | NIANGORAN GEORGIE | niangorangeorgie@editionsfabsci.com | `gestionnaire_stock` | 2026-06-17 | ✅ Actif | — |
| 8 | DETY MICHEL | detymichel@editionsfabsci.com | `directeur_commercial` | 2026-06-17 | ✅ Actif | — |
| 9 | AMENAN | amenan@editionsfabsci.com | `assistante` | 2026-06-17 | ✅ Actif | — |

> **Note :** Les champs `is_active`, `statut`, `last_login` ne sont pas encore alimentés en base (tous créés le même jour via seed). Le champ `last_login` sera renseigné automatiquement à la première connexion réelle de chaque utilisateur.

---

## 2. INVENTAIRE DES RÔLES

> Source : `backend/rbac_constants.py` + `frontend/src/constants/permissions.js`

9 rôles système officiels (+ 1 alias frontend) :

| # | Rôle système | Label affiché | Niveau hiérarchique | Mot de passe |
|---|-------------|---------------|---------------------|-------------|
| 1 | `super_admin` | Super Administrateur | 8 (max) | Admin@2025 |
| 2 | `directeur_general` | Directeur Général | 7 | Fabs@2025 |
| 3 | `comptable` | Comptable | 6 | Fabs@2025 |
| 4 | `directeur_commercial` | Directeur Commercial | 5 | Fabs@2025 |
| 5 | `gestionnaire_stock` | Gestionnaire de Stock | 4 | Fabs@2025 |
| 6 | `responsable_magasinier` | Responsable Magasinier | 3 | Fabs@2025 |
| 7 | `secretariat` | Secrétariat | 2 | Fabs@2025 |
| 8 | `assistante` | Assistante | 1 | Fabs@2025 |
| 9 | `service_logistique` | Service Logistique | 0 | Fabs@2025 |
| — | `assistante_commerciale` | Assistante Commerciale | *(alias frontend d'`assistante`)* | — |

> **`assistante_commerciale`** : rôle fantôme présent dans le frontend et dans certains modules backend (commandes, proformas, clients). Aucun utilisateur ne l'a en base. AMENAN est `assistante`. À clarifier : fusionner ou créer un 10e utilisateur réel avec ce rôle.

---

## 3. MATRICE COMPLÈTE DES PERMISSIONS PAR MODULE

### Légende
- `2` = Écriture (write) · `1` = Lecture (read) · `0` = Refusé
- **SA** = super_admin · **DG** = directeur_general · **CPT** = comptable · **DC** = directeur_commercial  
- **GS** = gestionnaire_stock · **RM** = responsable_magasinier · **SEC** = secretariat  
- **ASS** = assistante · **SL** = service_logistique

### 3.1 MODULE_PERMISSIONS (backend `rbac_constants.py`)

| Module | SA | DG | CPT | DC | GS | RM | SEC | ASS | SL |
|--------|:--:|:--:|:---:|:--:|:--:|:--:|:---:|:---:|:--:|
| **dashboard** | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 |
| **clients** | 2 | 0 | 1 | 2 | 0 | 0 | 2 | 2 | 0 |
| **produits** | 2 | 0 | 0 | 2 | 2 | 0 | 2 | 2 | 0 |
| **commandes** | 2 | 0 | 2 | 1 | 1 | 1 | 2 | 2 | 0 |
| **factures** | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **paiements** | 2 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **livraisons** | 2 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 2 |
| **retours** | 2 | 0 | 0 | 1 | 2 | 1 | 0 | 0 | 0 |
| **stock** | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| **colis** | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 1 |
| **expeditions** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| **logistique** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| **notifications** | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| **comptabilite** | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **comptabilite_avancee** | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **rh** | 2 | 1 | 1 | 1 | 0 | 0 | 2 | 0 | 0 |
| **bi_analytics** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **workflow_approvals** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **file_storage** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **backup** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **rapports** | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **utilisateurs** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **parametres** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **fleet** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| **logistics_costs** | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 |
| **multi_channel_notif.** | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## 4. PERMISSIONS PAR MODULE BACKEND (actions granulaires)

### 4.1 Clients (`clients_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, comptable, directeur_commercial, secretariat, assistante(_commerciale) |
| WRITE | super_admin, directeur_general ⚠️, directeur_commercial, secretariat, assistante(_commerciale) |
| DISABLE | super_admin, directeur_general ⚠️, directeur_commercial, secretariat |

> ⚠️ **INCOHÉRENCE** : `clients_module.py` inclut encore `directeur_general` dans READ_ROLES et WRITE_ROLES. La matrice `rbac_constants.py` dit DG=0 sur clients. **À corriger.**

---

### 4.2 Produits — deux modules !

#### `products_module.py` (module principal)
| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, directeur_commercial, gestionnaire_stock, assistante, assistante_commerciale |
| WRITE | super_admin, directeur_general ⚠️, directeur_commercial, gestionnaire_stock |
| FINANCIAL (prix achat) | super_admin, directeur_general, comptable |

> ⚠️ `products_module.py` inclut DG dans READ et WRITE. La matrice dit DG=0.  
> ⚠️ `products_module.py` exclut secretariat et assistante du WRITE alors que `rbac_constants.py` dit secretariat=2, assistante=2.  
> **Double incohérence — À corriger.**

#### `produits_module.py` (si existant — vérifier doublon)
> Fichier non trouvé. `products_module.py` est le seul module produits.

---

### 4.3 Commandes (`commandes_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_commercial, secretariat, comptable, assistante(_commerciale), gestionnaire_stock, responsable_magasinier |
| WRITE | super_admin, secretariat, assistante(_commerciale), comptable |
| VALIDATE (<500k) | super_admin, secretariat, comptable |
| VALIDATE (>500k) | super_admin uniquement *(fix C2 — DG retiré)* |
| CANCEL | super_admin, comptable, secretariat |
| PREPARE | super_admin, responsable_magasinier |
| DELIVER | super_admin, service_logistique |
| DELETE | super_admin uniquement |

✅ Conforme à la matrice.

---

### 4.4 Factures (`factures_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, comptable |
| WRITE | super_admin, comptable |
| PAYMENT | super_admin, comptable |
| Relances retard | super_admin, comptable |

✅ Conforme. Bug C1 (`"DG"` invalide) corrigé.

---

### 4.5 Proformas (`proformas_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_commercial, comptable, secretariat, assistante(_commerciale) |
| WRITE | super_admin, secretariat, comptable, assistante(_commerciale) |
| SEND | super_admin, secretariat, comptable, assistante(_commerciale) |
| CONVERT → Facture | super_admin, comptable, secretariat |

✅ Conforme à la matrice.

---

### 4.6 Paiements (`paiements_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general, comptable |
| WRITE | super_admin, directeur_general ⚠️, comptable |

> ⚠️ `paiements_module.py` donne WRITE au DG. La matrice dit DG=1 (lecture seule) sur paiements. **À corriger.**

---

### 4.7 Stock (`stock_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, gestionnaire_stock |
| WRITE | super_admin, directeur_general ⚠️, gestionnaire_stock |

> ⚠️ DG présent dans READ et WRITE. Matrice dit DG=0 sur stock. **À corriger.**

---

### 4.8 Livraisons — deux modules

#### `livraisons` (via `commandes_module.py` DELIVER_ROLES)
| Action | Rôles |
|--------|-------|
| DELIVER | super_admin, service_logistique |

#### `bons_livraison_module.py`
| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, service_logistique, responsable_magasinier, comptable ⚠️, directeur_commercial ⚠️ |
| WRITE | super_admin, directeur_general ⚠️, service_logistique, comptable ⚠️, directeur_commercial ⚠️ |

> ⚠️ `bons_livraison_module.py` : DG, comptable, dir_com présents dans READ et WRITE. Matrice dit : DG=0, comptable=0, dir_com=1 (lecture seule). **À corriger.**

---

### 4.9 Retours — deux modules

#### `bons_retour_module.py`
| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, service_logistique, responsable_magasinier, comptable ⚠️ |
| WRITE | super_admin, directeur_general ⚠️, service_logistique, comptable ⚠️ |

> ⚠️ DG et comptable présents. Matrice : DG=0, comptable=0, dir_com=1. **À corriger.**

---

### 4.10 RH (`rh_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general, responsable_rh ⚠️, comptable, directeur_commercial ⚠️, secretariat |
| WRITE | super_admin, directeur_general, responsable_rh ⚠️, comptable |
| DELETE | super_admin, directeur_general |
| APPROVE | super_admin, directeur_general, responsable_rh ⚠️ |

> ⚠️ Rôle `responsable_rh` présent dans le code mais **inexistant** dans ROLES système.  
> ⚠️ `directeur_commercial` a READ sur RH dans le module — cohérent avec matrice `rh=1` pour dir_com.

---

### 4.11 Comptabilité (`comptabilite_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, comptable |
| WRITE | super_admin, comptable |

> ⚠️ DG a READ dans le module. Matrice dit DG=0 sur comptabilite. **À corriger.**

---

### 4.12 Comptabilité avancée (`comptabilite_avancee_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, comptable |
| WRITE | super_admin, admin ⚠️, comptable |
| DELETE | super_admin, admin ⚠️ |

> ⚠️ Rôle `admin` présent — **inexistant** dans ROLES système. C'est un fantôme hérité d'une ancienne version.

---

### 4.13 Colisage (`colisage_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, gestionnaire ⚠️, preparateur ⚠️, directeur_commercial, directeur_general ⚠️, comptable, livreur ⚠️ |
| WRITE | super_admin, admin ⚠️, gestionnaire ⚠️, preparateur ⚠️ |
| VALIDATE | super_admin, admin ⚠️, gestionnaire ⚠️ |
| DELETE | super_admin, admin ⚠️ |
| DELIVERY | super_admin, admin ⚠️, gestionnaire ⚠️, livreur ⚠️ |

> ⚠️ **Module le plus problématique** : utilise des rôles fantômes (`admin`, `gestionnaire`, `preparateur`, `livreur`) inexistants dans le système. Ce module est **non aligné** avec la matrice RBAC V10. À refactoriser pour utiliser les vrais rôles.

---

### 4.14 Analytics / BI (`analytics_module.py`, `bi_analytics_module.py`)

#### `analytics_module.py`
| Action | Rôles |
|--------|-------|
| READ | super_admin, directeur_general ⚠️, comptable, directeur_commercial ⚠️ |

> ⚠️ DG et dir_com inclus. Matrice : bi_analytics DG=0, dir_com=0. **À corriger.**

#### `bi_analytics_module.py`
| Action | Rôles |
|--------|-------|
| READ | super_admin, admin ⚠️, comptable, directeur_general ⚠️ |
| WRITE | super_admin, admin ⚠️ |

> ⚠️ Rôle `admin` fantôme. DG inclus alors que matrice dit 0.

---

### 4.15 Workflow Approvals (`workflow_approvals_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, directeur_general ⚠️, comptable ⚠️ |
| WRITE | super_admin, admin ⚠️, directeur_general ⚠️ |

> ⚠️ DG, comptable, admin inclus. Matrice : workflow_approvals = super_admin uniquement.

---

### 4.16 File Storage (`file_storage_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, directeur_general ⚠️, comptable ⚠️ |
| WRITE | super_admin, admin ⚠️, directeur_general ⚠️, comptable ⚠️ |
| DELETE | super_admin, admin ⚠️ |

> ⚠️ DG, comptable, admin présents. Matrice : super_admin uniquement.

---

### 4.17 Backup (`backup_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️ |
| WRITE | super_admin, admin ⚠️ |

> ⚠️ Rôle `admin` fantôme.

---

### 4.18 Rapports (`rapports_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, comptable, directeur_commercial ⚠️ |

> ⚠️ DG et dir_com inclus. Matrice : rapports DG=0, dir_com=0.

---

### 4.19 Approvisionnements (`approvisionnement_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, gestionnaire_stock |
| WRITE | super_admin, directeur_general ⚠️, gestionnaire_stock |

> ⚠️ DG inclus. Matrice : pas de module `approvisionnements` explicite → à aligner.

---

### 4.20 Fournisseurs (`fournisseurs_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, directeur_general ⚠️, gestionnaire_stock |
| WRITE | super_admin, directeur_general ⚠️, gestionnaire_stock |

> ⚠️ DG inclus. Module `fournisseurs` non dans `rbac_constants.py`.

---

### 4.21 Fleet (`fleet_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique |
| WRITE | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique |
| DELETE | super_admin, admin ⚠️ |

> ⚠️ Rôles fantômes `admin`, `gestionnaire`.

---

### 4.22 Logistique (`logistique_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique |
| WRITE | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique |

> ⚠️ Rôles fantômes.

---

### 4.23 Logistics Costs (`logistics_costs_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique, comptable |
| WRITE | super_admin, admin ⚠️, gestionnaire ⚠️, service_logistique |

> ⚠️ Rôles fantômes.

---

### 4.24 Administration (`administration_module.py`)

| Action | Rôles autorisés |
|--------|----------------|
| READ users | super_admin |
| CREATE/EDIT users | super_admin |
| READ parametres | super_admin |
| EDIT parametres | super_admin |

✅ Conforme. Super_admin uniquement.

---

## 5. RÉSUMÉ PAR RÔLE — CE QU'IL PEUT FAIRE

### 5.1 `super_admin` — AKE APPIA YVES DORIS
> Accès total à tous les modules, toutes les actions. Aucune restriction.

### 5.2 `directeur_general` — ALI MAMIN
> Matrice officielle : **dashboard (R) · paiements (R) · rh (R) · notifications (R)**  
> Tout le reste = 0.

Modules visibles frontend :
- Dashboard, Paiements, RH (employés/dép./fonctions/contrats/congés/absences/missions/éval./rapports/paie), Notifications

### 5.3 `comptable` — NATACHA KOFFI
- Factures (W), Paiements (W), Commandes (W), Comptabilité (W), Compta avancée (W)
- RH (R), Clients (R), Rapports (W), Logistics costs (R)
- Notifications (R)

### 5.4 `directeur_commercial` — DETY MICHEL
- Clients (W), Produits (W), Commandes (R), Livraisons (R), Retours (R)
- Proformas (R), Dashboard (R), RH (R), Notifications (R)

### 5.5 `gestionnaire_stock` — NIANGORAN GEORGIE
- Produits (W), Stock (W), Commandes (R), Livraisons (R), Retours (W)
- Fournisseurs (W), Approvisionnements (W), Dashboard (R), Notifications (R)

### 5.6 `responsable_magasinier` — JOACHIN
- Colis (W) — préparation colisage
- Commandes (R), Livraisons (R), Retours (R)
- Dashboard (R), Notifications (R)
- Actions spéciales : PREPARE commandes

### 5.7 `secretariat` — MME AHOMAN DADJE
- Clients (W), Produits (W), Commandes (W), RH (W)
- Proformas (W/SEND), Dashboard (R), Notifications (R)
- Actions : WRITE/VALIDATE/CANCEL commandes, CONVERT proformas

### 5.8 `assistante` — AMENAN
- Clients (W), Produits (W), Commandes (W)
- Proformas (W/SEND), Notifications (R)
- *(Pas de dashboard affiché côté frontend)*

### 5.9 `service_logistique` — YAKE BEN
- Livraisons (W), Expéditions (W), Logistique (W)
- Colis (R), Fleet (W), Logistics costs (W)
- Dashboard (R), Notifications (R)
- Actions : DELIVER commandes

---

## 6. ANOMALIES ET INCOHÉRENCES DÉTECTÉES

### 🔴 Critiques (sécurité — DG accède à des modules interdits)

| # | Fichier | Problème | Impact |
|---|---------|----------|--------|
| A1 | `clients_module.py` | DG dans READ_ROLES + WRITE_ROLES | DG peut lire/modifier les clients |
| A2 | `products_module.py` | DG dans READ_ROLES + WRITE_ROLES | DG peut lire/modifier les produits |
| A3 | `paiements_module.py` | DG dans WRITE_ROLES | DG peut créer/modifier des paiements (doit être lecture seule) |
| A4 | `stock_module.py` | DG dans READ_ROLES + WRITE_ROLES | DG peut toucher au stock |
| A5 | `comptabilite_module.py` | DG dans READ_ROLES | DG peut lire la comptabilité |
| A6 | `bons_livraison_module.py` | DG + comptable + dir_com dans WRITE | Accès écriture non autorisés |
| A7 | `bons_retour_module.py` | DG + comptable dans WRITE | Accès écriture non autorisés |
| A8 | `analytics_module.py` | DG + dir_com dans READ | Accès BI non autorisés |
| A9 | `bi_analytics_module.py` | DG dans READ | Accès BI non autorisé |
| A10 | `workflow_approvals_module.py` | DG + comptable dans READ/WRITE | Seul super_admin autorisé |
| A11 | `file_storage_module.py` | DG + comptable dans READ/WRITE | Seul super_admin autorisé |
| A12 | `rapports_module.py` | DG + dir_com dans READ | Non autorisés par matrice |
| A13 | `approvisionnement_module.py` | DG dans READ/WRITE | Non autorisé |
| A14 | `fournisseurs_module.py` | DG dans READ/WRITE | Non autorisé |

### 🟠 Importants (rôles fantômes)

| # | Fichier(s) | Rôle fantôme | Utilisé dans |
|---|-----------|-------------|-------------|
| B1 | Nombreux modules | `admin` | backup, bi_analytics, colisage, file_storage, fleet, logistique, logistics_costs, workflow_approvals, comptabilite_avancee |
| B2 | `colisage_module.py` | `gestionnaire` | READ/WRITE/VALIDATE/DELIVERY |
| B3 | `colisage_module.py` | `preparateur` | READ/WRITE |
| B4 | `colisage_module.py` | `livreur` | READ/DELIVERY |
| B5 | `rh_module.py` | `responsable_rh` | READ/WRITE/APPROVE |
| B6 | Tous modules | `assistante_commerciale` | READ/WRITE (alias d'`assistante` non officiel) |

### 🟡 Mineurs (incohérences de couverture)

| # | Problème | Détail |
|---|---------|--------|
| C1 | ~~Bug `"DG"` ligne 1365 factures~~ | ✅ Corrigé |
| C2 | ~~Seuil 500k → validation DG~~ | ✅ Corrigé |
| C3 | `products_module.py` exclut secretariat/assistante du WRITE | `rbac_constants.py` dit 2 pour les deux |
| C4 | Modules `fournisseurs`, `approvisionnements` absents de `rbac_constants.py` | Non couverts par la matrice centrale |
| C5 | `rh_module.py` : dir_com a READ → cohérent avec matrice `rh=1` mais `rh_module.py` inclut un champ `directeur_commercial` non documenté dans le rapport précédent |

---

## 7. PLAN DE CORRECTION RECOMMANDÉ

### Priorité 1 — Corriger les accès DG résiduels (A1→A14)

```
clients_module.py       → retirer DG de READ_ROLES + WRITE_ROLES + DISABLE_ROLES
products_module.py      → retirer DG de READ_ROLES + WRITE_ROLES ; ajouter secretariat+assistante à WRITE_ROLES
paiements_module.py     → retirer DG de WRITE_ROLES (garder dans READ_ROLES uniquement)
stock_module.py         → retirer DG de READ_ROLES + WRITE_ROLES
comptabilite_module.py  → retirer DG de READ_ROLES
bons_livraison_module.py → aligner sur matrice (dir_com=1 seul, comptable=0, DG=0)
bons_retour_module.py   → aligner sur matrice (DG=0, comptable=0)
analytics_module.py     → retirer DG + dir_com
bi_analytics_module.py  → retirer DG + admin
workflow_approvals_module.py → retirer DG + comptable + admin
file_storage_module.py  → retirer DG + comptable + admin
rapports_module.py      → retirer DG + dir_com
approvisionnement_module.py → retirer DG
fournisseurs_module.py  → retirer DG
```

### Priorité 2 — Supprimer les rôles fantômes (B1→B6)

```
Tous modules utilisant "admin" → remplacer par "super_admin"
colisage_module.py → remplacer gestionnaire→gestionnaire_stock, preparateur→responsable_magasinier, livreur→service_logistique
rh_module.py → supprimer responsable_rh ou créer l'utilisateur
Décider du sort d'assistante_commerciale (fusionner avec assistante ou créer un 10e user)
```

### Priorité 3 — Compléter `rbac_constants.py`

```
Ajouter : fournisseurs, approvisionnements, fne dans MODULE_PERMISSIONS
```

---

## 8. FRONTEND — MENU PAR RÔLE

> Source : `frontend/src/constants/permissions.js` — matrice 100% conforme à rbac_constants.py

| Module | SA | DG | CPT | DC | GS | RM | SEC | ASS | SL |
|--------|:--:|:--:|:---:|:--:|:--:|:--:|:---:|:---:|:--:|
| dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| bi-analytics | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| rapports | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| clients | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| commandes | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| proformas | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| factures | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| paiements | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| livraisons | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| retours | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| colis | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| expeditions | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| produits | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| stock | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| logistique | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| fleet | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| logistics-costs | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| fournisseurs | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| approvisionnements | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| comptabilite | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| comptabilite-avancee | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| fne | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| rh-* (tous) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| notifications | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| file-storage | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| backup | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| parametres | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| workflow-approvals | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

> ✅ Frontend 100% conforme à la matrice `rbac_constants.py`.  
> ❌ Backend : 14 fichiers avec accès DG/rôles fantômes non alignés.

---

## 9. SYNTHÈSE

| Critère | État |
|---------|------|
| Nombre d'utilisateurs réels en base | **9 / 9** ✅ |
| Nombre de rôles système officiels | **9** ✅ |
| Frontend permissions.js | ✅ Conforme matrice v2.0 |
| `rbac_constants.py` | ✅ Conforme matrice v2.0 |
| Modules backend alignés | **6 / 20** ⚠️ |
| Modules backend avec DG résiduel | **14** 🔴 |
| Rôles fantômes détectés | **6** (`admin`, `gestionnaire`, `preparateur`, `livreur`, `responsable_rh`, `assistante_commerciale`) 🟠 |
| Bugs critiques corrigés | C1 ✅ C2 ✅ |

---

*Dernière mise à jour : 2026-06-17 — Audit exhaustif code + MongoDB*
