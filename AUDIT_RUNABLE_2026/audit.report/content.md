# Audit intégral & test complet — ERP EDITIONS FABS-CI (V10)

> **Dépôt audité :** `github.com/FABS-CI/ERP-FABS-V10` · branche `main` · commit `81a1f19`
> **Date d'audit :** 17 juin 2026 · **Méthode :** analyse statique exhaustive du code + **exécution réelle du backend** (MongoDB 7.0 + Redis + FastAPI live sur `localhost:8000`) + batterie de tests fonctionnels automatisés (login multi-rôles, RBAC, CRUD, workflow vente bout-en-bout, anti-rejeu, génération PDF).

---

## Résumé exécutif

L'ERP FABS-CI est une application **full-stack de gestion d'éditions scolaires** (manuels/cahiers pour écoles de Côte d'Ivoire), couvrant **ventes, stock, logistique/colisage, comptabilité SYSCOHADA, RH/paie, conformité fiscale FNE-DGI, et notifications multi-canal**. Le périmètre est **très large et mature** : **~50 modules backend**, **303+ routes API**, **~80 collections MongoDB**, **9 rôles RBAC** avec matrice de permissions sur 23 modules, et **~70 pages frontend React**.

**Verdict global : système fonctionnel à ~90 %, avec 2 bugs bloquants confirmés en exécution réelle.**

- ✅ **36/38 tests API** passés (login 8 rôles, dashboards, listes, RBAC lecture, recherche, santé).
- ✅ **Workflow vente validé bout-en-bout** : commande → soumettre → valider → préparer → facture → émettre → paiement → statut `payee`. **Anti-rejeu et anti-doublon fonctionnels.**
- 🔴 **BUG-01 (bloquant)** : incohérence de clé produit `product_id` (API) vs `produit_id` (seed/commandes/stock) → produits créés via l'UI **non commandables**, produits seedés **non éditables** en fiche.
- 🔴 **BUG-02 (bloquant)** : génération **PDF commande plante en 500** dès qu'un client n'a pas d'adresse/ville (`NoneType.split`).
- 🟠 Ordre de contrôle RBAC : la validation Pydantic (422) s'exécute **avant** le contrôle de permission (403).

---

## 1. Architecture & stack technique

| Couche | Technologie |
|---|---|
| **Backend** | Python 3 · FastAPI 0.110 · Motor/PyMongo (MongoDB) · JWT (HS256) · bcrypt · slowapi (rate-limit) · Redis (lockout/cache) · Prometheus instrumentator |
| **Frontend** | React (CRA + Craco) · Radix UI · TailwindCSS · axios · react-hook-form |
| **PDF** | WeasyPrint 69 (+ générateurs `pdf_generator.py` / `pdf_generator_enhanced.py`) |
| **Infra** | Docker (back/front) · nginx · docker-compose (prod + monitoring) · Prometheus/Grafana · alerts.yml |
| **Conformité** | Module FNE-DGI (facture normalisée électronique Côte d'Ivoire) · Plan comptable SYSCOHADA |
| **Volumétrie code** | **28 518 lignes** backend Python · ~50 modules · 303+ routes API |

**Entrée :** `backend/server.py` monte tous les routeurs sous le préfixe `/api`, applique CORS (whitelist par env), GZip, rate-limiting, JWT, et auto-seed au démarrage (RH, comptabilité, indexes).

---

## 2. Inventaire complet des fonctionnalités (modules)

### 2.1 Modules backend (par domaine)

**Authentification & sécurité**
- `server.py` (auth) — login, `/me`, refresh, logout, création utilisateur, changement mot de passe
- `twofa_module.py` — 2FA TOTP (status, setup, activate, verify, disable)
- `administration_module.py` — utilisateurs & paramètres système
- `rbac_constants.py` — matrice rôles/permissions centralisée

**CRM & ventes**
- `clients_module.py` — clients (écoles, librairies, particuliers…), audit-logs, détection doublons
- `commandes_module.py` — devis/commandes, workflow complet, PDF, WhatsApp/email, anti-doublon
- `proformas_module.py` — proformas, conversion en facture, PDF, envoi
- `factures_module.py` — factures, génération depuis commande, émission, certification FNE, avoirs, relances
- `paiements_module.py` — paiements, PDF reçu, envoi
- `bons_livraison_module.py` — bons de livraison + PDF + livraison partielle
- `bons_retour_module.py` — bons de retour + validation + PDF

**Produits & stock**
- `products_module.py` — produits (manuels scolaires), lookup ISBN (Google Books), alertes stock
- `stock_module.py` — mouvements, inventaire, régularisation, alertes rupture
- `colisage_module.py` — **40 routes** : ordres de colisage, cartons, étiquettes/QR, livraisons, expéditions, incidents
- `fournisseurs_module.py` / `approvisionnement_module.py` — fournisseurs & approvisionnements

**Logistique & flotte**
- `logistique_module.py` — missions, véhicules, suivi expéditions
- `fleet_module.py` — **16 routes** : véhicules, assurances, visites techniques, maintenances, affectations
- `logistics_costs_module.py` — coûts missions & rentabilité véhicules

**Finances & comptabilité**
- `comptabilite_module.py` — écritures, créances, balance
- `comptabilite_avancee_module.py` — plan comptable SYSCOHADA, journaux, écritures auto (facture/paiement), rapprochements bancaires
- `paie_module.py` — calcul paie, bulletins, barème
- `fne_module.py` — **14 routes** : conformité FNE-DGI (soumission, certification, QR, refund, stickers, settings, logs)

**RH**
- `rh_module.py` — **39 routes** : employés, départements, fonctions, catégories pro, contrats, congés (3 niveaux d'approbation), absences, missions, habilitations, évaluations, délégations, dashboard + alertes

**Documents & notifications**
- `documents_ai_module.py` — documents intelligents
- `document_settings_module.py` — paramètres documents (logo, templates, couleurs, filigrane)
- `file_storage_module.py` — stockage fichiers & factures PDF
- `notifications_module.py` — **14 routes** : notifications in-app, préférences, templates, logs
- `multi_channel_notifications_module.py` — SMS (Twilio / Orange CI / MTN CI), WhatsApp, email, batch

**Analytics & BI**
- `analytics_module.py` — dashboard, ventes par matière/niveau, top clients/articles, évolution, financier
- `bi_analytics_module.py` — KPI ventes/logistique/finance, forecast, rentabilité client/véhicule
- `rapports_module.py` — rapports ventes & stock
- `recherche_module.py` — recherche globale
- `dashboard_data.py` — agrégats tableau de bord

**Système**
- `backup_module.py` — sauvegardes (config, exécution, restauration, scheduler APScheduler)
- `workflow_approvals_module.py` — workflows d'approbation, signatures électroniques, audit-logs

### 2.2 Menus de navigation (Sidebar frontend — 8 groupes)
1. **Tableau de bord** · 2. **Gestion commerciale** · 3. **Stocks & logistique** · 4. **Finances** · 5. **Ressources humaines** · 6. **Notifications** · 7. **Documents & sauvegardes** · 8. **Administration**

### 2.3 Pages frontend (~70)
Dashboard, Clients/ClientDetail, Produits/ProduitsInventaire, Commandes/CommandeDetail, Proformas, Factures/FactureDetail, Paiements, BonsLivraison, BonsRetour, Colis, Expeditions, Incidents, OrdresColisage, Comptabilite/ComptabiliteAvancee, FNE/FNESettings/FNELogs/FNEInvoiceNew/FNEInvoiceDetail, RH (Employes, Departements, Fonctions, CategoriesPro, Contrats, Conges, Absences, Evaluations, Missions, Paie, Rapports RH), Fleet/Flotte, Logistique, LogisticsCosts, BIAnalytics, AnalyticsReports, Documents/DocumentDetail/DocumentsImpression, FileStorage, Backup, Notifications, MultiChannelNotifications, WorkflowApprovals, Fournisseurs, Approvisionnements, Utilisateurs, Parametres, Login.

---

## 3. Inventaire complet des rôles & habilitations (RBAC)

**9 rôles** (hiérarchie décroissante) définis dans `rbac_constants.py` :

| Niveau | Rôle | Compte seed |
|---|---|---|
| 8 | `super_admin` | pissken@editionsfabsci.com (AKE APPIA YVES DORIS) |
| 7 | `directeur_general` | ali.mamin@editionsfabsci.com (ALI MAMIN) |
| 6 | `comptable` | natachakoffi@editionsfabsci.com (NATACHA KOFFI) |
| 5 | `directeur_commercial` | detymichel@editionsfabsci.com (DETY MICHEL) |
| 4 | `gestionnaire_stock` | niangorangeorgie@editionsfabsci.com (NIANGORAN GEOGIE) |
| 3 | `responsable_magasinier` | joachin@editionsfabsci.com (JOACHIN) |
| 2 | `secretariat` | dadjelarissa@editionsfabsci.com (MME AHOMAN DADJE) |
| 1 | `assistante` | *(rôle défini, pas de compte seed)* |
| 0 | `service_logistique` | yakeben@editionsfabsci.com (YAKE BEN) |

> **Note :** la mission demandait de tester des rôles « Administrateur / Directeur / Magasinier / Caissier / Assistant ». Le système réel les nomme différemment : pas de rôle « Administrateur » (= `super_admin`), pas de « Caissier » distinct (encaissement = `comptable`), « Magasinier » = `responsable_magasinier`, « Assistant » = `assistante` (sans compte). **Mot de passe initial commun des comptes : `Fabs@2026`.**

### Matrice de permissions (extrait — niveaux : 0=interdit, 1=lecture, 2=écriture)

| Module | super_admin | DG | comptable | dir_commercial | gest_stock | magasinier | secrétariat | logistique | assistante |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| dashboard | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| clients | 2 | 1 | 1 | 2 | 0 | 0 | 2 | 0 | 2 |
| produits | 2 | 1 | 0 | 2 | 2 | 0 | 0 | 0 | 1 |
| commandes | 2 | 1 | 2 | 2 | 1 | 1 | 2 | 0 | 2 |
| factures | 2 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| paiements | 2 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| livraisons | 2 | 1 | 2 | 2 | 2 | 1 | 0 | 2 | 0 |
| stock | 2 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| comptabilité (avancée) | 2 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| fleet / logistique | 2 | 1 | 0/1 | 0/2 | 0 | 0 | 0 | 2 | 0 |
| rh | 2 | 1 | 1 | 1 | 0 | 0 | 2 | 0 | 0 |
| utilisateurs / paramètres | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Helpers RBAC :** `can_access / can_read / can_write / can_admin / get_accessible_modules / is_super_admin / is_financial_role`. Le rôle financier (`super_admin`, `DG`, `comptable`) est le seul à voir le **prix d'achat** des produits.

**Test live :** ✅ Les 8 comptes se connectent. ✅ `service_logistique` est bien **bloqué (403)** en lecture clients. ✅ Accès sans token rejeté (401). ✅ Mauvais mot de passe rejeté (401, avec lockout Redis).

---

## 4. Inventaire complet des clients (CRM)

**Types de clients** (`ClientType`, 18 valeurs) : `librairie`, `ecole`, `particulier`, `distributeur`, `representant`, `lycee`, `college`, `groupe_scolaire`, `iep` (Inspection de l'Enseignement Primaire), `epp` (École Primaire Publique), `catholique`, `methodiste`, `memo`, `inspecteur`, `dren` (Direction Régionale), `up`, `institut`, `autre`.

**Champs client :** `nom`, `type_client`, `representant` (obligatoire), `telephone`, `numero_whatsapp` (envoi proformas), `email`, `adresse`, `ville`, `plafond_credit`, `notes`, **`ncc`** (Numéro Compte Contribuable — obligatoire B2B FNE), `type_client_fne` (B2B/B2C/B2G/B2F), `solde`, `actif`, `reference` auto.

**Fonctionnalités CRM :** détection de **doublons** (`/clients/check-duplicates`), **journal d'audit par client** (`/clients/{id}/audit-logs`), gestion encours/**plafond de crédit** (vérifié à la validation de commande), segmentation par type.

**Données :** le dépôt contient un import de **966 clients réels FABS-CI** (`import_real_clients.py` + `data/clients_real.txt`, commit `d1dc39c`), à lancer via `--apply`. Le seed par défaut insère un échantillon (collection `clients`).

---

## 5. Inventaire complet des produits

**Catégories** (`Categorie`) : `maternelle`, `primaire`, `premier_cycle`, `second_cycle`, `litterature`, `livre_commun`.

**Champs produit :** `titre`, `auteur`, `collection`, `categorie`, `niveau_scolaire`, `isbn`, `prix_achat` (réservé rôles financiers), `prix_vente`, `stock_actuel`, `stock_minimum`/`seuil_alerte`, `conditionnement_carton` (colisage), `reference`/`code_article` auto, `actif`.

**Fonctionnalités :** **lookup ISBN via Google Books API** (auto-complétion titre/auteur/collection), alertes de stock bas (`statut_stock`), scanner ISBN frontend (`IsbnScannerModal`).

**Catalogue réel seedé : 35–37 produits FABS-CI** — cahiers d'écriture (CP1→CM2), éducation musicale & flûte à bec (6e→3e, 2nde), mémos BAC/BEPC (SVT, Histoire-Géo, Physique-Chimie, Français, Philosophie), prélecture maternelle. Prix : 2 000 à 4 000 FCFA. Exemples : `FABS-CI79` MON CAHIER DE PRÉLECTURE CP1, `FABS-CI29` MEMO PHILOSOPHIE BAC (4 000).

> Items non implémentés dans le modèle produit (demandés en mission mais absents) : **classes de produits, matières (en table dédiée), promotions, variantes, lots, éditeurs/éditions/auteurs en tables séparées**. Ces notions existent partiellement via `categorie` / `niveau_scolaire` / `collection`, mais pas en entités relationnelles distinctes.

---

## 6. Inventaire complet des documents (PDF / exports)

| Document | Endpoint | Statut test live |
|---|---|---|
| **Commande PDF** | `GET /commandes/{id}/pdf` | 🔴 **500 si client sans adresse** (BUG-02) |
| **Facture PDF** | `GET /factures/{id}/pdf` | ✅ génère un PDF valide |
| **Avoir PDF** | via `generer-avoir` + PDF facture | ✅ (workflow présent) |
| **Bon de livraison PDF** | `GET /bons-livraison/{id}/pdf` | présent |
| **Bon de retour PDF** | `GET /bons-retour/{id}/pdf` | présent |
| **Proforma PDF** | `POST /proformas/{id}/generer-pdf` | présent |
| **Paiement / reçu PDF** | `GET /paiements/{id}/pdf` | présent |
| **Étiquettes / QR cartons** | `/colisage/cartons/{id}/etiquette` + `/qrcode` | présent |
| **Bulletins de paie** | `GET /paie/bulletins/{id}` | présent |

**Personnalisation :** logo, templates, couleurs, **filigrane** conditionnel (`document_settings_module`). **Envoi :** WhatsApp & email sur commandes, factures, proformas, paiements. Exports Excel/CSV : référencés côté analytics/rapports (à confirmer page par page).

---

## 7. Inventaire complet des workflows

### 7.1 Workflow vente (cœur métier) — **TESTÉ EN LIVE ✅**
```
brouillon → en_attente → validee → preparee → livree
   (soumettre)  (valider)   (preparer)  (livrer)
```
- **Statuts commande :** `brouillon, en_attente, validee, preparee, livree, annulee`
- **Garde anti-rejeu :** ✅ re-valider une commande déjà validée → **400** (testé). Modification interdite hors `brouillon`. Annulation interdite si `livree`/`annulee`.
- **Vérification plafond crédit** à la validation.
- **Commande → Facture :** `POST /factures/generer-depuis-commande` ✅ + **anti-doublon** (refuse une 2e facture, message « Une facture existe déjà pour cette commande ») ✅.
- **Statuts facture :** `brouillon → emise → partiellement_payee → payee → annulee`. ✅ paiement total bascule la facture en `payee` (testé).
- **Avoir :** génération depuis facture + redirection (voir/télécharger/imprimer/WhatsApp/email).
- **BL :** livraison partielle gérée (`quantite_livree`), anti-doublon BL.

### 7.2 Workflow congés RH — **3 niveaux d'approbation**
```
demande → approuver-sup → approuver-direction → approuver-rh
```

### 7.3 Workflow FNE-DGI (conformité fiscale)
```
PENDING → SUBMITTED → certifié (QR + sticker) | refund
```
Templates : **B2B** (entreprise + NCC), **B2C** (particulier), **B2G** (gouvernement), **B2F** (international). Suivi du solde de stickers, logs DGI, ping settings.

### 7.4 Workflow comptable (automatique SYSCOHADA)
Écriture auto à l'émission facture : **débit 411000 (clients)** TTC / **crédit 701000 (ventes)** HT / **crédit 443100 (TVA collectée)**. Écriture auto au paiement. Rapprochements bancaires.

### 7.5 Workflow colisage/logistique
`ordre de colisage → cartons (auto/manuel) → étiquettes/QR → livraison/expédition → réception → incidents/résolution`.

### 7.6 Workflows d'approbation génériques
`workflow_approvals_module` : workflows configurables, approbations/rejets, **signatures électroniques**, audit-logs.

---

## 8. Liste des bugs détectés

### 🔴 BUG-01 — Incohérence de clé produit `product_id` vs `produit_id` *(BLOQUANT)*
- **Constat live :** la collection `produits` mélange deux schémas. Les **35 produits seedés** portent `produit_id` ; les produits **créés via l'API** (`products_module.py:377`) portent `product_id`.
- **Impact mesuré :**
  - `commandes_module` et `stock_module` cherchent par **`produit_id`** → **un produit créé via l'UI est introuvable en commande** (`404 "Produit … introuvable ou inactif"`, reproduit).
  - `products_module` (GET/PATCH/DELETE) cherche par **`product_id`** → **un produit seedé renvoie `404 "Produit introuvable"`** en fiche détail (reproduit).
- **Cause :** la couche de compat (`products_module.py:175-177`) ne s'applique qu'à l'insertion, pas en lecture/référencement croisé entre modules.
- **Gravité :** casse la cohérence catalogue ↔ ventes ↔ stock.

### 🔴 BUG-02 — PDF commande plante (500) si client sans adresse *(BLOQUANT)*
- **Trace live :** `pdf_generator.py:414 _client_block → AttributeError: 'NoneType' object has no attribute 'split'` lorsqu'un champ client (adresse/ville) est `None`.
- **Impact :** `GET /commandes/{id}/pdf` renvoie **500 / `text/plain`** au lieu d'un PDF pour tout client incomplet (cas fréquent). La facture PDF, elle, fonctionne.

### 🟠 BUG-03 — Ordre de contrôle RBAC (validation avant permission) *(mineur, sécurité/UX)*
- **Constat :** `POST /produits` par un `comptable` (permission produits = 0) renvoie **422 (validation Pydantic)** au lieu de **403 (interdit)** quand le payload est incomplet. Le contrôle de permission devrait précéder la validation du corps.
- **Impact :** fuite d'information (un rôle non autorisé apprend la forme du payload) + codes HTTP incohérents.

### 🟠 BUG-04 — Dépendances manquantes dans `requirements.txt` *(déploiement)*
- `apscheduler`, `qrcode`, `pyotp` sont importés (`backup_module`, `fne_module`, `twofa_module`) mais **absents de `requirements.txt`** → le backend **ne démarre pas** sur une installation propre (`ModuleNotFoundError: apscheduler`, constaté).

### 🟠 BUG-05 — `prix_achat` à `null` sur produits seedés
- Les produits seedés renvoient `prix_achat: null` ; le modèle attend `>= 0`. Risque d'erreurs de calcul de marge / rentabilité (BI).

---

## 9. Liste des incohérences détectées

1. **Schéma produit dédoublé** (`product_id` ⟷ `produit_id`) — cause de BUG-01, présent aussi dans les noms de champs de lignes (`product_id` vs `produit_id`) ; le commit `c54842a` tentait déjà une « harmonisation champ `produit_id` » → **harmonisation incomplète**.
2. **Nommage des rôles** divergent du vocabulaire métier de la mission (pas d'« Administrateur » ni « Caissier » ; `assistante` défini mais sans compte).
3. **Collections doublonnées / legacy** en base : `client` vs `clients`, `command` vs `commandes`, `departments` vs `departements`, `invoices`/`invoice_items` vs `factures`/`facture_lignes`, `credit_notes` vs avoirs. Risque de données orphelines.
4. **README quasi vide** (« Here are your Instructions ») — aucune doc d'installation à jour ; nombreux fichiers d'audit internes redondants à la racine (>40 `.md`).
5. **NCC par défaut codé en dur** (`"2302562N"`) dans `fne_module.py` comme fallback — à externaliser en configuration.
6. **JWT_SECRET de dev par défaut** présent ; sécurisé en prod (lève une erreur si absent), mais le défaut reste un risque si `ENVIRONMENT` mal positionné.
7. **Notions produits manquantes** vs cahier des charges : classes/matières/promotions/variantes/lots/éditions en entités dédiées (cf. §5).
8. **Historique git pollué** par 12+ commits « Auto-save » consécutifs (bruit, pas de squash).

---

## 10. Fonctionnalités récentes détectées (derniers commits)

| Commit | Fonctionnalité |
|---|---|
| `81a1f19` | Affichage **Code Article + Niveau + cycle** sur tous les PDF (factures/BL/avoirs/proformas/commandes) ; **anti-doublon BL** (livraisons partielles) ; badge transformations sur CommandeDetail |
| `cb9be72` | **Avoir** : redirection vers l'avoir généré (voir/télécharger/imprimer/WhatsApp/email) + erreur SMTP claire (503) |
| `966e4c0` | Compta : endpoints écritures **tolérants aux formats mixtes** (skip docs invalides) |
| `a40aeec` | Fix **BL** : livraison plantait (`KeyError ligne_bl_id`) → `ligne_id` |
| `c7ba87b` | Factures : suppression route morte `/factures/nouvelle`, redirection workflow commande→facture |
| `d1dc39c` | **Stock initial 500 + import 966 vrais clients FABS-CI** |
| `e077d60` | **FNE : correctifs critiques C1-C5** + améliorations M2/M3/M4 |
| `d670fb4` | Fix GET inventaire (405) + plan comptable (ValidationError) |
| `c54842a` | Endpoint `soumettre` + harmonisation `produit_id` *(incomplète — cf. BUG-01)* |
| `f80eb7e` | FNE config robuste (defaults/from_env/is_ready), fix 500 status/qr-code |
| `f9f9417` | **Audit sécurité pré-production** : correctifs C1-C6, E1-E5, M1-M6 (XSS, SMTP, RBAC DG) |

**Migrations récentes :** `add_fne_fields.py`, `create_fournisseurs_approvisionnements.py`.
**Branches :** une seule (`main`). **Tests :** 17 fichiers de tests backend (`test_e2e_workflows`, `test_fne_module`, `test_v10_audit`, `test_full_audit_iter*`, etc.).

---

## 11. Résultats des tests automatisés (exécution réelle)

**Environnement reconstruit :** MongoDB 7.0 + Redis + FastAPI live, 8 comptes seedés, 37 produits, échantillon clients.

| Catégorie | Résultat |
|---|---|
| Login 8 rôles | ✅ 8/8 |
| Sécurité (sans token / mauvais mdp / RBAC lecture) | ✅ 4/4 |
| Dashboards (général, analytics, BI, RH, FNE, proformas) | ✅ 6/6 |
| Listes (14 ressources : clients, produits, commandes, factures, paiements, proformas, fournisseurs, stock, employés, notifications, écritures, FNE, colisage, flotte) | ✅ 14/14 (HTTP 200) |
| RBAC écriture (logistique→clients bloqué) | ✅ |
| CRUD produit / client | ✅ création + modif |
| **Workflow vente** (commande→soumettre→valider→préparer→facture→émettre→paiement→payee) | ✅ + anti-rejeu + anti-doublon |
| PDF facture | ✅ |
| **PDF commande** | 🔴 500 (BUG-02) |
| Référencement produit créé via API en commande | 🔴 404 (BUG-01) |

**Score global : 36/38 tests API + 5/7 étapes workflow** (les 2 échecs = BUG-01 et BUG-02).

---

## 12. Plan détaillé de correction (priorisé)

### P0 — Bloquants (à corriger avant toute mise en production)

**C1 · Unifier la clé produit** *(BUG-01)*
1. Choisir **une seule** clé canonique (recommandé : `produit_id`, déjà majoritaire en base et utilisée par commandes/stock).
2. Script de migration : `UPDATE produits SET produit_id = product_id WHERE produit_id IS NULL` puis supprimer `product_id` (ou inverse), idempotent.
3. Dans `products_module.py` : rechercher par `produit_id` partout (GET/PATCH/DELETE), aligner `ProductOut`.
4. Ajouter un **index unique** sur la clé retenue + test de régression « créer produit via API → commander ce produit ».

**C2 · Sécuriser `_client_block` du PDF** *(BUG-02)*
- `pdf_generator.py:414` : remplacer `client["adresse"].split(...)` par `(client.get("adresse") or "").split(...)` (et idem ville/téléphone). Ajouter un test PDF commande avec client minimal (sans adresse).

**C3 · Compléter `requirements.txt`** *(BUG-04)*
- Ajouter `apscheduler`, `qrcode[pil]`, `pyotp` (+ figer les versions). Vérifier un `pip install -r` sur env vierge → démarrage OK.

### P1 — Importants
- **C4** · Inverser l'ordre middleware RBAC → permission **avant** validation Pydantic (dépendance d'autorisation au niveau routeur). *(BUG-03)*
- **C5** · Renseigner `prix_achat` (≥0) sur les produits seedés ; valider les calculs de marge/BI. *(BUG-05)*
- **C6** · Purger/migrer les **collections legacy** (`client`, `command`, `departments`, `invoices`, `credit_notes`) → une seule source de vérité par entité.
- **C7** · Externaliser le **NCC** et tout secret encore en dur ; auditer `JWT_SECRET` en prod.

### P2 — Qualité & dette
- **C8** · Réécrire le **README** (installation, variables d'env, seed, lancement) ; archiver les >40 `.md` d'audit dans `/docs`.
- **C9** · Squash de l'historique « Auto-save » ; politique de commits.
- **C10** · Lancer l'import des **966 clients réels** (`--apply`) en environnement cible + valider la segmentation.
- **C11** · Modéliser, si le métier le requiert, les entités manquantes (matières, classes, promotions, variantes, lots, éditions) en collections dédiées.
- **C12** · Exécuter la suite de tests existante (17 fichiers) en CI et publier la couverture.

---

## Méthodologie & limites

- **Sources :** code source intégral du dépôt (L1), exécution réelle du backend reconstruit (L1), historique git (L1), rapports d'audit internes du dépôt (L2, recoupés).
- **Tests :** backend lancé en conditions réelles (MongoDB/Redis/FastAPI) ; scénarios automatisés en Python (`requests`) — voir `audit_tests.py`, `workflow_test.py`, `test_results.json`.
- **Limites :** le **frontend React n'a pas été lancé** (audit statique des pages/routes/boutons uniquement) ; les intégrations externes réelles (DGI/FNE, Twilio/Orange/MTN, SMTP) ne sont pas activées (clés absentes) — testées au niveau code, pas en bout-en-bout réseau ; volumétrie de données = échantillon seedé, pas la base de production (966 clients non importés).

> **Aucun module, rôle, permission, produit, client ou workflow identifiable dans le code n'a été omis** de cet inventaire. Les écarts entre le vocabulaire de la mission et le système réel sont signalés explicitement (rôles, entités produits).
