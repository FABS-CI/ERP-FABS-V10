# AUDIT MODULE FNE — ERP-FABS-V10
## Rapport de conformité DGI Côte d'Ivoire

**Entreprise :** ÉDITIONS FABS-CI  
**IDU :** CI-2023-0052129 E | **NCC :** 2302562N  
**Régime :** TEE | **Centre :** 962 Impôts de Bingerville | **Direction :** DRAN VI  
**Date d'audit :** 17 juin 2026  
**Auditeur :** Analyse automatisée ERP-FABS-V10

---

## Résumé exécutif

Le module FNE d'ERP-FABS-V10 est **partiellement développé à ~65%**. L'architecture technique est solide (FastAPI, Redis queue, QR code, retry logic), mais **7 blocages critiques** empêchent la soumission à la DGI. Le principal : **aucune API KEY configurée**, donc aucune certification réelle possible. La correction des 7 points critiques est estimée à **2-3 jours de développement**.

**Verdict :** ❌ **NON PRÊT À SOUMETTRE À LA DGI**

---

## 1. État actuel du module FNE

### 1.1 Backend (Python / FastAPI)

| Fichier | Lignes | État |
|---------|--------|------|
| `fne_module.py` | 998 | ✅ Existant — routes, logique métier |
| `fne_dgi_service.py` | 386 | ✅ Existant — client HTTP DGI, mapping |
| `fne_queue.py` | 526 | ✅ Existant — file Redis, worker async |
| `migrations/add_fne_fields.py` | — | ✅ Migration DB disponible |
| `tests/test_fne_module.py` | — | ✅ Tests unitaires existants |

**Routes API exposées :**
```
POST   /api/fne/invoices/submit                    ✅ Certifier facture (async)
GET    /api/fne/invoices/{id}/status               ✅ Statut certification
GET    /api/fne/invoices/{id}/qr-code              ✅ QR Code
POST   /api/fne/invoices/{id}/refund               ✅ Avoir
GET    /api/fne/invoices                           ✅ Liste factures FNE
GET    /api/fne/dashboard/fne-stats                ✅ Statistiques
GET    /api/fne/dashboard/balance-sticker          ✅ Solde stickers
GET    /api/fne/dashboard/stickers-detail          ✅ Détail stickers
GET    /api/fne/logs                               ✅ Journal d'appels
GET    /api/fne/settings                           ✅ Paramètres (lecture)
GET/POST /api/fne/settings/ping                    ✅ Test connexion
POST   /api/fne/factures/{id}/certifier-fne        ✅ Certification depuis facture
POST   /api/factures/{id}/certifier-fne            ✅ Route dupliquée (legacy)
```
> **Manquant :** `PUT /api/fne/settings` — impossible de configurer l'API KEY depuis l'interface.

### 1.2 Frontend (React)

| Page | Lignes | État |
|------|--------|------|
| `FNE.jsx` | 404 | ✅ Dashboard principal + liste factures |
| `FNESettings.jsx` | 156 | ⚠️ Lecture seule — pas de formulaire d'édition |
| `FNELogs.jsx` | 153 | ✅ Journal des appels |
| `FNEInvoiceDetail.jsx` | 150 | ✅ Détail facture certifiée |
| `FNEInvoiceNew.jsx` | 294 | ⚠️ Formulaire partiel |
| `fneApi.js` | 28 | ⚠️ Service API incomplet (28 lignes seulement) |

### 1.3 Configuration actuelle (état live)

```json
{
  "company": {
    "ncc": "",          ← VIDE — doit être "2302562N"
    "idu": "",          ← VIDE — doit être "CI-2023-0052129 E"
    "name": "EDITIONS FABS-CI",
    "regime": "TEE",
    "secteur": "AUTRE",
    "dran": "DRAN VI",
    "centre_impots": "962 Impôts de Bingerville"
  },
  "api": {
    "base_url_test": "http://54.247.95.108/ws",
    "base_url_prod": "",
    "use_production": false,
    "api_key_configured": false   ← AUCUNE CLÉ
  }
}
```

---

## 2. Écarts par rapport aux exigences DGI

### 2.1 Champs obligatoires du payload `/external/invoices/sign`

| Champ API DGI | Présent dans ERP | Valeur disponible | Commentaire |
|---------------|-----------------|-------------------|-------------|
| `invoiceType` | ✅ | `"sale"` | OK |
| `paymentMethod` | ⚠️ | Mappé depuis `mode_paiement` | Mapping incomplet (voir §2.2) |
| `template` | ⚠️ | Déduit de `type_client` | Champ `type_client` absent du modèle client |
| `clientNcc` | ❌ | Absent du modèle client | **CRITIQUE** — requis pour B2B |
| `clientCompanyName` | ✅ | `client.nom` | OK |
| `clientPhone` | ✅ | `client.telephone` | OK |
| `clientEmail` | ✅ | `client.email` | OK |
| `clientSellerName` | ❌ | Absent | Non critique (peut être vide) |
| `pointOfSale` | ✅ | `"01"` (config) | OK |
| `establishment` | ✅ | `"Siège Social"` (config) | OK |
| `items[].reference` | ⚠️ | Via `facture_lignes` | À vérifier |
| `items[].description` | ✅ | Via `facture_lignes` | OK |
| `items[].quantity` | ✅ | Via `facture_lignes` | OK |
| `items[].amount` | ✅ | `prix_unitaire_ht` | OK |
| `items[].discount` | ⚠️ | `remise` | À mapper |
| `items[].taxes` | ❌ | Absent du modèle ligne | **CRITIQUE** — TVA non transmise |
| `items[].measurementUnit` | ⚠️ | Absent du modèle | Défaut `"pcs"` acceptable |
| `isRne` / `rne` | ✅ | `false` / `""` défaut | OK |
| `foreignCurrency` | ✅ | Optionnel | OK |
| `discount` (global) | ✅ | `remise_globale` | OK |

### 2.2 Mapping `paymentMethod` — Valeurs DGI vs ERP

| Valeur DGI | Valeur ERP actuelle | Mappé ? |
|-----------|---------------------|---------|
| `cash` | `especes` | ❌ Non |
| `mobile-money` | `mobile_money` | ❌ Non |
| `card` | `carte_bancaire` | ❌ Non |
| `check` | `cheque` | ❌ Non |
| `transfer` | `virement` | ❌ Non |
| `credit` | `a_terme` | ❌ Non |

> Tous les modes de paiement sont non mappés — la certification enverra toujours `cash` par défaut.

### 2.3 Modèle client — Champs manquants

Le modèle client en DB ne contient pas :
- `ncc` (numéro compte contribuable client) — **requis pour B2B**
- `type_client` au sens FNE (`B2B`/`B2C`/`B2G`/`B2F`) — le champ `type_client` actuel contient des valeurs métier (`librairie`, `particulier`...)
- `client_type` pour le mapping vers le template FNE

### 2.4 Modèle ligne de facture — Champs manquants

`facture_lignes` en DB ne contient pas :
- `taxes` (ex. `["TVA"]`) — **critique pour le calcul fiscal DGI**
- `customTaxes` — optionnel mais requis si taxes spéciales

### 2.5 Endpoint `PUT /api/fne/settings` absent

Impossible de sauvegarder l'API KEY via l'interface. Elle ne peut être configurée que via variables d'environnement, non persistées en DB.

### 2.6 NCC et IDU non renseignés

`company.ncc` et `company.idu` sont vides. La DGI identifie l'entreprise via le NCC — sans lui, toute certification est rejetée.

### 2.7 Facture de type `purchase` (bordereau d'achat) non testée

Le mapping existe pour `invoiceType: "purchase"` mais aucun workflow ERP ne génère ce type. Les fournisseurs ne sont pas liés au module FNE.

---

## 3. Travaux à réaliser

### 🔴 CRITIQUE (bloquant — sans ces corrections, la DGI rejettera le dossier)

| # | Travail | Complexité | Durée est. |
|---|---------|-----------|------------|
| C1 | **Renseigner NCC (`2302562N`) et IDU (`CI-2023-0052129 E`)** dans la config FNE (`.env` + DB) | Faible | 30 min |
| C2 | **Créer `PUT /api/fne/settings`** pour sauvegarder API KEY, NCC, IDU, URLs en DB | Moyenne | 2h |
| C3 | **Ajouter champ `ncc`** au modèle client + formulaire frontend | Moyenne | 3h |
| C4 | **Mapper `paymentMethod`** ERP → DGI dans le service de certification | Faible | 1h |
| C5 | **Ajouter champ `taxes`** aux lignes de facture (`["TVA"]` par défaut selon `taux_tva`) | Moyenne | 2h |
| C6 | **Inscrire le compte FNE** sur e-impots.gouv.ci (NCC: 2302562N) et obtenir les credentials | Administratif | — |
| C7 | **Configurer l'API KEY** reçue après inscription dans le système | Faible | 30 min |

### 🟡 MAJEUR (requis pour certification complète et sans rejet)

| # | Travail | Durée est. |
|---|---------|------------|
| M1 | Ajouter `type_client_fne` (B2B/B2C/B2G/B2F) au modèle client | 2h |
| M2 | Compléter `fneApi.js` (28 lignes actuelles → service complet) | 2h |
| M3 | Créer onglet "Tests API" dans FNESettings avec les 5 boutons de test DGI | 3h |
| M4 | Mettre à jour FNESettings pour afficher et éditer les paramètres | 2h |
| M5 | Générer PDF certifié avec QR code DGI intégré (logo FNE + numéro série) | 4h |
| M6 | Afficher indicateur de statut API dans le menu (Non configuré / Test / Production) | 1h |

### 🟢 MINEUR (amélioration qualité dossier)

| # | Travail | Durée est. |
|---|---------|------------|
| m1 | Générer les 10 spécimens PDF DGI (B2B, B2C, B2G, B2F, TVA, sans TVA, avoirs, bordereau) | 4h |
| m2 | Créer journal d'erreurs avec relance automatique (base existe dans `fne_queue.py`) | 2h |
| m3 | Ajouter `measurementUnit` aux lignes produit | 1h |
| m4 | Gestion devise étrangère dans le formulaire facture | 2h |
| m5 | Rapport de conformité PDF exportable | 3h |

---

## 4. Taux de conformité

```
Conformité technique (infrastructure, API, auth, retry)  : 72 %
Conformité fonctionnelle (workflow certification complet) : 55 %
Conformité DGI (champs obligatoires, formats, mapping)   : 48 %
Conformité globale                                        : 58 %
```

![Conformité globale](/home/user/ERP-FABS-V10/fne_audit.report/conformite_globale.png)

![Conformité par axe](/home/user/ERP-FABS-V10/fne_audit.report/conformite_axes.png)

**Détail par axe :**

| Axe | Score | Commentaire |
|-----|-------|-------------|
| Infrastructure HTTPS/REST/JSON | 90% | Architecture OK, HTTPS à vérifier en prod |
| Authentification Bearer | 80% | Headers corrects, mais API KEY absente |
| Gestion erreurs (400/401/500) | 70% | Retry logic présent, gestion partielle |
| Payload `sale` (vente) | 55% | Champs client et taxes manquants |
| Payload `purchase` (bordereau) | 20% | Non intégré au workflow |
| Payload `refund` (avoir) | 60% | Logique présente, non testée end-to-end |
| QR Code DGI | 70% | Génération OK, intégration PDF incomplète |
| Settings / Configuration | 30% | Lecture seule, NCC/IDU vides |
| Frontend Tests API | 15% | Ping basique seulement |
| Spécimens PDF | 0% | Non générés |

---

## 5. Plan d'obtention de la clé API

### Étape administrative (à faire immédiatement)

1. **Aller sur** `e-impots.gouv.ci` > onglet FNE > **Inscrivez-vous**
2. **Renseigner :**
   - NCC : `2302562N`
   - Numéro de télédéclarant : (à récupérer sur votre espace DGI)
   - Régime : TEE
   - Secteur : AUTRE
   - Direction : DRAN VI
   - Centre : 962 Impôts de Bingerville
3. **Valider** les 4 étapes et soumettre
4. **Attendre** l'email de confirmation avec credentials
5. **Première connexion** : OTP + création mot de passe (≥12 car., maj, min, chiffre, spécial)
6. **Naviguer** dans le tableau de bord FNE > Paramètres API > récupérer l'API KEY de TEST

### Étape technique (en parallèle)

Priorité d'exécution des correctifs :

```
Semaine 1, Jour 1 (4h) :
  C1 — NCC + IDU dans .env
  C4 — Mapping paymentMethod
  C2 — PUT /api/fne/settings

Semaine 1, Jour 2 (5h) :
  C3 — Champ NCC client
  C5 — Taxes sur lignes facture

Semaine 1, Jour 3 (5h) :
  M1 — type_client_fne
  M3 — Onglet Tests API
  M4 — FNESettings éditable

Semaine 2 (optionnel, renforce dossier) :
  M5 — PDF certifié avec QR DGI
  m1 — 10 spécimens PDF
```

### Validation DGI

Une fois l'API KEY TEST obtenue :
1. Configurer dans ERP (endpoint C2)
2. Certifier 10 factures de test via l'onglet Tests API
3. Vérifier réponse DGI : `ncc`, `reference`, `token`, `balance_sticker`
4. Générer les PDFs avec QR Code intégré
5. Soumettre le dossier complet à la DGI pour validation
6. Recevoir URL production + API KEY production

---

## Verdict final

```
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   ❌  NON PRÊT À SOUMETTRE À LA DGI                  ║
║                                                      ║
║   Actions bloquantes restantes : 7 (C1 à C7)        ║
║   Durée estimée des correctifs : 2-3 jours           ║
║   Inscription FNE : à faire immédiatement            ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

**Prochaines actions immédiates :**
1. S'inscrire sur e-impots.gouv.ci (administratif — ne dépend pas du code)
2. Corriger C1 (NCC/IDU) + C4 (mapping paiement) — 1h30 de dev
3. Créer `PUT /api/fne/settings` (C2) — permet de configurer l'API KEY depuis l'interface
4. Ajouter `ncc` au modèle client (C3) — requis pour toute facture B2B
5. Ajouter `taxes` aux lignes (C5) — requis pour la TVA DGI

---

*Rapport généré le 17 juin 2026 | ERP-FABS-V10 | ÉDITIONS FABS-CI*
