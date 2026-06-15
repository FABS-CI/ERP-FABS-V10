# PRD — ERP EDITIONS FABS-CI V10 ENTERPRISE

## Référentiel
**Source de vérité absolue** : `PROMPT_MAITRE_ERP_FABS_CI_V10.md` (V10 > toutes versions antérieures)

## Architecture
- **Backend** : FastAPI (Python 3.11+) + Motor (MongoDB async) + JWT/RBAC + slowapi + Redis + Prometheus
- **Frontend** : React 19 + JavaScript (CRACO) + TailwindCSS + Radix UI + lucide-react + sonner
- **Database** : MongoDB (DB `fabsci_erp`)
- **Cache/Queue/PubSub** : Redis 7 (sous supervisor, port 6379)
- **Temps réel** : WebSocket natif FastAPI/Starlette

## Palette officielle FABS-CI (confirmée utilisateur)
| Token Tailwind | Hex | Usage |
|---|---|---|
| `fabs.orange` | `#FF6200` | Primaire — boutons, menus actifs, KPI |
| `fabs.blue` | `#0A2540` | Secondaire — badges, cartes secondaires |
| `fabs.success` | `#10B981` | Validations |
| `fabs.warning` | `#F59E0B` | Alertes |
| `fabs.error` | `#EF4444` | Erreurs / Suppression |
| `fabs.bg` | `#F9FAFB` | Background |

## 9 Rôles RBAC officiels V10
super_admin · directeur_general · comptable · directeur_commercial · gestionnaire_stock · responsable_magasinier · secretariat · **assistante** · service_logistique

## Suivi des sprints

### ✅ Sprint 15 — Login fullscreen background officiel (11 juin 2026)

**Demande utilisateur** : Remplacer l'arrière-plan de la page Login par le nouveau visuel officiel FABS-CI et centrer la carte de connexion au milieu.

**Implémentation** :
- ✅ Nouvelle image officielle déposée : `/app/frontend/public/assets/login-bg.png` (1.6 Mo) — version sans mockup formulaire
- ✅ `Login.jsx` refondu : layout single-screen avec **background full-cover** + **carte de login centrée horizontalement et verticalement** (max-w-md, p-10, shadow-2xl)
- ✅ Overlay gradient subtil (left→right : `bg-gradient-to-r from-[#0A2540]/30 via-[#0A2540]/5 to-[#0A2540]/30`) pour améliorer la lisibilité de la carte sans dénaturer le visuel officiel
- ✅ Suppression du Logo + import inutilisé (l'image officielle inclut déjà le logo)
- ✅ Le visuel reste pleinement visible : logo FABS-CI, "Plateforme de gestion", description, slogan "Une innovation pour une école de qualité" avec icône chapeau diplômé, livre lumineux + icônes éducation

**Validation** :
- ✅ Login Super Admin → redirection `/dashboard` OK
- ✅ Affichage parfait en 1920×900 et 1366×768
- ✅ Carte de login bien centrée au milieu de l'écran


### ✅ Sprint 14 — Refonte page Login + Nouveau slogan (11 juin 2026)

**Nouveau slogan officiel** (mis à jour partout via `COMPANY.slogan` dans `/app/frontend/src/constants/company.js`) :
> **« Une innovation pour une école de qualité »**
> (remplace l'ancien « Les livres sont des fenêtres par lesquelles on regarde le monde »)

**Refonte page Login (`/app/frontend/src/pages/Login.jsx`)** :
- ✅ Layout split-screen : panneau gauche (illustration hero) + panneau droit (formulaire fonctionnel)
- ✅ Image hero officielle FABS-CI déposée dans `/app/frontend/public/assets/login-hero.png` (1.3 Mo)
- ✅ Image cadrée intelligemment (wrapper width 230% + object-cover/object-left) pour ne montrer que la partie "branding" du PNG et masquer le mockup formulaire du visuel source
- ✅ Formulaire à droite : 
  - Titre "Accédez à votre espace" (text-3xl extrabold) + barre orange décorative
  - Champs email/mot de passe redessinés (padding plus généreux, icônes mieux placées)
  - Toggle d'affichage du mot de passe (Eye/EyeOff)
  - Bouton "Se connecter" avec flèche → (orange FABS, plus large)
  - Footer ERP + année scolaire
- ✅ Responsive : sur mobile/tablette (< lg), seul le formulaire est visible, le logo FABS apparaît dessus + slogan en pied de page

**Tests validés** :
- ✅ Login Super Admin (`pissken@editionsfabsci.com / Admin@2025`) → redirection `/dashboard` OK
- ✅ Affichage identique à la maquette fournie (logo FABS-CI, "Plateforme de gestion complète de l'entreprise", slogan avec icône chapeau diplômé)
- ✅ Affichage testé en 1366×768 et 1920×900


### ✅ Sprint 13 — Intégration données officielles FABS-CI (11 juin 2026)

**Source** : 3 artefacts fournis par l'utilisateur :
- `utilisateurs_editionsfabsci.txt` (8 utilisateurs)
- `ARTICLES_FABS_CI_NUMEROTES.txt` (catalogue produits)
- `ROLES_ET_HABILITATIONS_ERP_FABS.md` (vérification rôles existants)

**Scripts de seed créés** :
- ✅ `/app/backend/scripts/seed_utilisateurs_fabs.py` — UPSERT idempotent par email, option `--reset-password`
- ✅ `/app/backend/scripts/seed_articles_fabs.py` — UPSERT idempotent par référence SKU
- ✅ `/app/backend/scripts/README.md` — Documentation des comptes & utilisation

**Résultats d'exécution** :
- 👤 **8 utilisateurs** officiels en base : 6 nouveaux créés (mot de passe initial `Fabs@2026`) + 2 conservés (Super Admin + DG)
- 📚 **56 articles** FABS-CI en base : tous les SKU FABS-CIxx du catalogue importés, avec catégorie mappée (primaire / premier_cycle / second_cycle / litterature), prix unitaire parsé en FCFA
- 🛡️ **9 rôles** : aucun changement nécessaire — la doc fournie correspond exactement aux `VALID_ROLES` déjà définis

**Validation** :
- ✅ Login Yake Ben (service_logistique) avec `Fabs@2026` → HTTP 200 + JWT renvoyé
- ✅ Login Natacha (comptable) avec `Fabs@2026` → HTTP 200
- ✅ `/produits` affiche bien "56 produits dans le catalogue"
- ✅ `/app/memory/test_credentials.md` mis à jour avec tous les comptes + mots de passe

**Mapping catégories (référence)** :
| Source                                | Cible backend     |
|---------------------------------------|-------------------|
| MATERNELLE / PRIMAIRE (CP/CE/CM/CEPE) | `primaire`        |
| PREMIER CYCLE - ÉDUCATION MUSICALE    | `premier_cycle`   |
| SECOND CYCLE - MÉMOS/TESTS BEPC       | `premier_cycle`   |
| SECOND CYCLE - MÉMOS/TESTS BAC        | `second_cycle`    |
| LITTÉRATURE / ROMANS                  | `litterature`     |

**Note** : 3 articles avec prix "N/A" (ANNALES MATH 6E, MANUEL ARTS PLASTIQUES 5E, JE ME PRÉPARE ANGLAIS BEPC) ont reçu un prix_vente=1 FCFA par défaut (champ `gt=0` obligatoire). À éditer manuellement via UI quand le prix réel sera connu.


### ✅ Sprint 12 — Audit régression V10 + Hot fixes (11 juin 2026)

**Bug Départements (CRITIQUE) — corrigé** :
- 🐛 RCA : `Departements.jsx` L3 importait `listDepartments` (anglais sans 'e') au lieu de `listDepartements` (français pluriel). `ReferenceError` silencieusement attrapé par le `try/catch`, état `departements` restait `[]`.
- ✅ Fix : import corrigé + uniformisation V10 (PageHeader + bouton orange) appliquée.
- ✅ Vérification UI : la page `/rh/departements` affiche maintenant les **7 départements** (Commercial, Comptabilité, Direction Générale, Informatique, Logistique, Magasin & Stock, Secrétariat & Administration).

**Bug Expeditions /api/colisage/expeditions (CRITIQUE) — corrigé** :
- 🐛 RCA : Modèle Pydantic `ExpeditionOut` (colisage_module.py) marquait 8 champs comme requis alors que les documents legacy en base n'ont qu'`expedition_id` + `created_at`. `ValidationError` → 500.
- ✅ Fix : tous les champs problématiques passés en `Optional[...] = None` avec défauts sûrs.
- ✅ Validation curl : `GET /api/colisage/expeditions` répond désormais **HTTP 200** au lieu de 500.

**Issues mineures résolues** :
- ✅ `RHDashboard.jsx` : `showBack` rétabli (était à `false`, manquait sur `/rh`) → 4 boutons V10 cohérents partout.
- ✅ `Fleet.jsx` modale "Nouveau Véhicule" : astérisques `*` ajoutés sur 9 champs obligatoires (Référence, Immatriculation, Marque, Modèle, Année, Type, Statut, Capacité kg, Kilométrage).

**Audit complet via testing_agent_v3_fork** :
- ✅ Backend : 22/22 endpoints PASS (health, login, départements, paie ITS/CNPS/CMU, notifications, FNE sandbox, workflow commercial, etc.)
- ✅ Frontend : 12/13 pages avec PageHeader V10 complet (la 13ème, /rh, est maintenant aussi conforme après fix)
- ✅ Sidebar accordéon 8 groupes + section ⭐ FAVORIS opérationnels
- ✅ Workflow commercial : conversion Proforma↔Facture et génération Facture depuis Commande validés
- ✅ Suite pytest `/app/backend/tests/test_v10_audit.py` : **22/22 PASS en 2.02s** (peut être rerun en régression)

**Issues informationnelles non bloquantes** :
- ℹ️ Redis disconnected dans preview env (WebSocket `/api/notifications/ws` warning) → impact uniquement sur notifications temps réel
- ℹ️ Page `/expeditions` : ajouter toast d'erreur en cas d'échec fetch (future amélioration UX)


### ✅ Sprint 11 — Uniformisation finale V10 + 3ème bouton "Tableau de Bord" (11 juin 2026)
**Périmètre V10** : Finaliser l'uniformisation totale des pages Logistique et Documents/Sauvegardes.

**Améliorations PageHeader** :
- ✅ Ajout du **3ème bouton "Tableau de Bord"** (icône `LayoutDashboard`) → distinct de "Accueil"
- ✅ Boutons "Accueil" et "Tableau de Bord" auto-masqués sur `/dashboard` et `/` (évite la redondance)
- ✅ **Icône principale agrandie** : `w-14 h-14` (mobile) → `w-16 h-16` (desktop), icône interne `w-7 h-7` → `w-8 h-8`
- ✅ Gradient orange (FF6200 → E65800) sur le wrapper d'icône + ring subtil
- ✅ **Titre agrandi** : `text-3xl` mobile → `text-4xl` desktop, `font-extrabold`
- ✅ Description plus visible : `text-sm` → `text-base` desktop
- ✅ Boutons nav avec bordures (variant `outline`) au lieu de `ghost` → plus visibles

**Pages uniformisées (PageHeader + DashboardLayout)** :
- ✅ `Fleet.jsx` — Gestion de Flotte (icône Car, 5 onglets)
- ✅ `LogisticsCosts.jsx` — Coûts Logistiques (icône DollarSign, 4 onglets)
- ✅ `Logistique.jsx` — Missions Logistiques (icône Truck, formulaire V10 standardisé)
- ✅ `FileStorage.jsx` — File Storage Enterprise (icône HardDrive, 3 onglets)
- ✅ `Backup.jsx` — Backup & Disaster Recovery (icône Database, action "Créer un Backup" dans header)

**Tests validés (smoke test)** :
- ✅ `/fleet`, `/logistics-costs`, `/logistique`, `/file-storage`, `/backup` : 4 boutons V10 présents (back/home/dashboard/favorite)
- ✅ Sidebar accordéon correctement déployée sur "STOCKS & LOGISTIQUE" pour ces pages
- ✅ Breadcrumb résolu correctement


### ✅ Sprint 10 — Workflow Commercial complet (11 juin 2026)
**Périmètre V10** : Brancher les boutons de conversion sur les pages détail Proforma et Commande.

**Backend (existant, validé)** :
- `POST /api/proformas/{proforma_id}/convertir-facture` → Proforma → Facture
- `POST /api/factures/generer-depuis-commande` body `{commande_id}` → Commande → Facture
- `POST /api/commandes/{commande_id}/valider` → Génère automatiquement une proforma au passage en statut "validée"

**Frontend** :
- ✅ `CommandeDetail.jsx` : nouveau bouton **"Générer Facture"** (orange FABS) visible si statut ∈ {validee, preparee, livree} pour rôles {super_admin, DG, directeur_commercial, comptable}
- ✅ `ProformaDetail.jsx` : bouton **"Convertir en Facture"** disponible sur TOUS les statuts sauf `convertie_facture` (élargi depuis avant qui excluait `brouillon`)
- ✅ `ProformaDetail.jsx` : nouveau bouton **"Voir la facture associée"** (bleu FABS) quand la proforma est déjà convertie
- ✅ Service `generateFactureFromCommande` déjà existant dans `facturesApi.js`

**Tests E2E** :
- ✅ API : commande `cmd_3c046e0861f8` (validée) → facture `FABS-FC-26-27-0002` 34 810 FCFA générée
- ✅ UI : screenshot CommandeDetail montre bien le bouton "Générer Facture" orange à côté des autres actions
- ✅ UI : screenshot ProformaDetail montre bien le bouton "Convertir en Facture" en statut Brouillon


### ✅ Sprint 9 — Uniformisation V10 + Favoris (11 juin 2026)
**Périmètre V10** : Uniformisation visuelle complète + mode Favoris pour accès rapide.

**Composant PageHeader (`/components/layout/PageHeader.jsx`)** :
- ✅ Composant uniforme : boutons Retour/Accueil/Favoris + icône + titre + description + slot actions
- ✅ Bouton Favoris (étoile) avec toggle persistant via `localStorage.fabs.favs`
- ✅ Event bus `fabs.favs.update` pour synchronisation avec Sidebar (pas de reload navigateur)
- ✅ `favoriteKey` par défaut = pathname courant

**Sidebar — Section Favoris** :
- ✅ Bloc "⭐ FAVORIS" affiché en haut quand au moins 1 favori est épinglé
- ✅ Affichage de l'étoile orange (#FF6200) + label de la page
- ✅ Bouton de suppression (X) visible au hover
- ✅ Écoute des événements `storage` et `fabs.favs.update` (sync inter-onglets)

**Pages uniformisées (PageHeader appliqué)** :
- ✅ `RHDashboard.jsx` — Tableau de Bord RH
- ✅ `Notifications.jsx` — Centre de Notifications (+ ajout `DashboardLayout` manquant)
- ✅ `Comptabilite.jsx` — Comptabilité (Écritures, Créances, Balance)
- ✅ `ComptabiliteAvancee.jsx` — Comptabilité Avancée (+ ajout `DashboardLayout` manquant)
- ✅ `Produits.jsx` — Catalogue livres
- ✅ `Expeditions.jsx` — Gestion des Expéditions
- ✅ `Missions.jsx` — Missions
- ✅ `Conges.jsx` — Congés
- ✅ `Absences.jsx` — Absences et retards

**Formulaires standardisés (V10 directive)** :
- ✅ "Nouvelle Expédition" : champs labellés avec astérisques, section "Adresse de livraison" en encart, bouton orange FABS, Textarea pour Notes, bouton Annuler outline
- ✅ "Nouvelle Mission" : champs labellés avec astérisques, layout 2 colonnes pour dates, bouton Créer orange FABS, bouton Annuler outline
- ✅ "Nouvelle Demande" Congé : harmonisé
- ✅ "Enregistrer Absence" : harmonisé

**Tests visuels validés** :
- ✅ Sidebar Favoris affiche bien les pages épinglées (testé avec Catalogue livres + Centre de Notifications)
- ✅ Breadcrumb correctement résolu sur toutes les pages testées
- ✅ Boutons Retour/Accueil/Favoris présents sur toutes les pages PageHeader
- ✅ Palette FABS-CI respectée (#FF6200 / #0A2540) partout


### ✅ Phase 0 — Audit complet (10 juin 2026)
Rapport d'audit complet livré et validé. Écarts identifiés et plan de normalisation produit.

### ✅ Pré-Sprint — Normalisations critiques (10 juin 2026)
- Intégration officielle module **Proformas** (backend monté, frontend liste + détail, RBAC)
- Correction RBAC frontend : `responsable_rh` → `assistante` (matrice V10 exacte)
- Correction RBAC backend `VALID_ROLES` (ajout `assistante`)
- Nettoyage 2 services frontend (URL `localhost:8000` → `API_BASE_URL`)
- Compte test créé : `assistante.test@editionsfabsci.com` (5 modules visibles : Clients, Commandes, Proformas, Produits, Notifications) ✅

### ✅ Sprint 8 — Stabilisation Gestion Commerciale (11 juin 2026)
**Objectif** : rendre 100 % fonctionnels les 9 modules commerciaux (Clients · Commandes · Proforma · Factures · Paiements · Livraisons · Retours · Colis · Expéditions).

**Phase 1 — DashboardLayout** :
- ✅ `Colis.jsx` et `Expeditions.jsx` patchés (bug sidebar invisible)
- ✅ `BonsLivraison.jsx` et `BonsRetour.jsx` déjà OK
- Toutes les pages commerciales ont maintenant la sidebar

**Phase 2 — Seed workflow démo end-to-end** :
- ✅ Proforma `PF-2026-000001` créée via API à partir de la commande existante (34 810 FCFA, client Librairie Carrefour Cocody)
- ✅ Bon de Livraison `BL-2026-000001` (collection `bons_livraison`)
- ✅ Bon de Retour `BR-2026-000001` (collection `bons_retour`, motif "Endommagé")
- ✅ Colis `COL-2026-000001` (15,5 kg, 10 articles, statut "prepare")
- ✅ Expédition `EXP-2026-000001` (transporteur GBO Express, statut "en_cours", 25 000 FCFA)

**Phase 3 — Vérification UI** :
- ✅ Page `/proformas` : affiche `PF-2026-000001` correctement, KPI fonctionnels
- ✅ Sidebar visible sur les 5 pages testées

**Constats** :
- ⚠️ **Désalignement endpoints↔pages** détecté pour Livraisons/Retours/Colis/Expéditions : les pages frontend lisent des routes différentes des collections seedées. À analyser au cas par cas (recommandation Sprint 9).

**Workflow commercial 100% fonctionnel sur les modules principaux** :
- Client (2 docs) → Proforma (1 doc) → Commande (3 docs) → Facture (1 doc) → Paiement (1 doc)
- Workflow logistique partiel : données seedées en DB, à brancher complètement dans l'UI au prochain sprint


### ✅ Sprint 6b + Sprint 7 (combinés) — Paie CI + Documents & Impression (11 juin 2026)

#### Sprint 6b — Paie Côte d'Ivoire
**Backend** :
- ✅ Nouveau module `paie_module.py` avec moteur de calcul ITS / CNPS / CMU
- ✅ Barème ITS progressif 6 tranches (0% → 32%)
- ✅ CNPS salarial 6,3% + plafond 1 647 315 FCFA · CMU forfait 1 000 FCFA
- ✅ Charges patronales détaillées (CNPS 7,7% + Accidents 2% + Prestations famille 5,75%)
- ✅ 5 endpoints : `/paie/calculer` (preview live) · `/paie/bulletins` (POST/GET) · `/paie/bulletins/{id}` · `/paie/bareme`

**Frontend** :
- ✅ Page `/rh/paie` avec liste bulletins + 4 KPI + modale création
- ✅ **Calcul temps réel** dans la modale (debounce 350ms) — affichage côte-à-côte du bulletin
- ✅ Card de prévisualisation en gradient bleu FABS avec NET en vert success

**Vérification calculs** :
- Brut 200 000 FCFA → CNPS 12 600 + ITS 17 984 + CMU 1 000 = **Net 168 416 FCFA** · Coût employeur 230 900
- Brut 400 000 FCFA → CNPS 25 200 + ITS 54 708 + CMU 1 000 = **Net 319 092 FCFA** · Coût employeur 461 800
- Brut 900 000 FCFA → CNPS 56 700 + ITS 154 392 = **Net 687 908 FCFA** · Coût employeur 1 039 050

⚠️ Les taux sont configurés dans `paie_module.py` (constantes en tête) — à valider avec un expert-comptable agréé avant production. Sources : CGI CI · CNPS 2024-2026.

#### Sprint 7 — Documents & Impression
- ✅ Bug critique : `document_settings_module.py` avait `prefix="/api/document-settings"` → double prefix `/api/api/document-settings`. **Fix** : `/document-settings`.
- ✅ Bug critique frontend : `DocumentsImpression.jsx` utilisait `REACT_APP_API_URL` (var inexistante) → fallback `localhost:8001` cassé en preview. **Fix** : `REACT_APP_BACKEND_URL`.
- ✅ Page enfin accessible via route `/parametres/documents-impression`
- ✅ **5 modèles facture** chargés : Classique Professionnel, Moderne Bleu, Premium, Corporate Orange, Élégant Administratif
- ✅ Onglets : Modèles · Logo · Filigranes · Entreprise
- ✅ Sélecteur visuel avec previews couleurs FABS-CI


### ✅ Sprint 6 — Module RH Complet (Phase A) (11 juin 2026)
**Périmètre V10** : Audit + complétion du module RH (16 sous-modules visés).

**Audit** :
- Backend `rh_module.py` était déjà très avancé : Dashboard, Alertes, Employés (CRUD), Départements/Fonctions/Catégories pro (CRUD), Contrats (CRUD), Congés (workflow 3 niveaux), Absences, Missions, Habilitations, Évaluations, Délégations
- 7 départements + 19 fonctions + 8 catégories pro déjà seedés
- Frontend : 11 pages existaient (RHDashboard, Employes, Departements, Fonctions, CategoriesPro, Contrats, Conges, Absences, Missions, Evaluations, RapportsRH)
- Service `rhApi.js` existant

**Bugs critiques corrigés** :
- ✅ **DashboardLayout absent sur 11 pages RH** (bug systémique → sidebar invisible) : script Python intelligent ajoutant l'import + wrapper sur les 11 pages
- ✅ **79 champs Pydantic `Optional[...]`** sans `= None` → ValidationErrors massifs en lecture. Fix groupé via regex sur tout `rh_module.py`
- ✅ **Schémas Employé** : valeurs Literal corrigées (`sexe: H/F`, `situation_matrimoniale: Marie(e)/Celibataire`, `type_employe: Administration/Commercial/...`)

**Seed démo** :
- ✅ 5 employés FABS-CI seedés (FABS-EMP-001 à 005) : AKE APPIA YVES DORIS (DG), ALI MAMIN (Commercial), KOUAME AYA SARAH, YAO BERNARD, TRAORE FATIM
- Tous avec matricule, CNI, CNPS, dates, dépt/fonction valides

**Tests** :
- ✅ Dashboard RH : 5 employés, 5 actifs (avec sidebar visible)
- ✅ Liste Employés : 5 lignes avec noms résolus (département + fonction)
- ✅ Liste Fonctions : 19 fonctions affichées (Agent Logistique, Comptable, DG, Magasinier, etc.)
- ⚠️ Liste Départements UI : affiche vide (probable bug service legacy → à corriger Sprint 6b)

**Sous-modules manquants (Sprint 6b à venir)** :
- Bulletins de paie + calculs ITS/CNPS/CR/CMU Côte d'Ivoire
- Primes & Retenues
- Déclarations CNPS/ITS
- Formations
- Documents RH + Signatures (modules dans collections mais sans endpoints)
- Postes (vs Fonctions à clarifier)


### ✅ Sprint 5 — Business Intelligence V10 Enterprise (11 juin 2026)
**Périmètre V10** : Dashboard exécutif consolidé pour DG / Super Admin avec KPI, graphiques et forecasting.

**Audit** :
- Backend `bi_analytics_module.py` était déjà très complet (KPI ventes/logistique/finance, dashboard, forecast moyenne mobile, rentabilité clients/véhicules) — **conservé tel quel** (Règle V10 N°3)
- Frontend `BIAnalytics.jsx` existait mais avec 4 défauts : pas de sidebar, pas de graphiques, IDs bruts affichés, palette non-FABS

**Refonte frontend (1 page)** :
- ✅ `BIAnalytics.jsx` réécrit en V10 Enterprise :
  - `DashboardLayout` wrapper → sidebar enfin visible
  - 3 onglets (Tabs shadcn) : Dashboard exécutif · Prévisions · Rentabilité clients
  - 4 KPI cards principaux (CA, Commandes, Panier moyen, Taux de marge) + indicateur de croissance trend
  - 3 KPI secondaires (Bénéfice, Missions logistiques, Factures impayées)
  - **Graphique BarChart horizontal "Top clients"** (Recharts) avec résolution des noms via `clientsMap`
  - **PieChart "Ventilation financière"** (Revenus / Dépenses / Bénéfice) avec palette FABS
  - **BarChart vertical "Top produits"** avec résolution des noms via `produitsMap`
  - Onglet Prévisions : AreaChart 3 mois avec gradient orange + cartes détail
  - Onglet Rentabilité clients : tableau top 10 contributeurs avec badges rang FABS
  - Sélecteur de période (7j · 30j · 90j · 6mois · 12mois)

**Tests** :
- ✅ Dashboard exécutif affiche les vraies données (88 500 FCFA · 3 commandes · 1 client)
- ✅ Top client résolu en "Librairie de France" (au lieu de `cli_dd536fc7d254`)
- ✅ Pie chart : Bénéfice 34 810 FCFA, Revenus 34 810 FCFA, Dépenses 0
- ✅ Sidebar visible et navigation OK
- ✅ Palette FABS-CI appliquée partout (orange #FF6200, bleu #0A2540, success #10B981)
- ✅ Onglets Prévisions et Rentabilité fonctionnels (états vides propres)

**Accès** : limité au **Super Admin** uniquement (matrice V10).


### ✅ Sprint 4 — Module Approvisionnements Frontend (10 juin 2026)
**Périmètre V10** : Bons de commande / réception fournisseurs avec mise à jour stock automatique à la validation.

**Backend** :
- ✅ Module `approvisionnement_module.py` existait déjà (CRUD + endpoint `/valider` qui incrémente le stock)
- ✅ Bug data migration : produits seedés avec clé legacy `produit_id` → `product_id` aliasé (35 docs migrés)
- ✅ Bug `ProductOut` : champ `reference` requis mais seed avait `code_article` → fallback dans `project_product`
- ✅ Le module `/produits` est désormais opérationnel (était cassé silencieusement avant)

**Frontend (2 pages créées)** :
- ✅ `/approvisionnements` — Liste + 4 KPI (Total, Brouillons, Validés, Montant total) + recherche + filtre statut + modale création
- ✅ Modale création complète : Fournisseur (dropdown) + Dépôt + Notes + Lignes produits (dropdown produits) + Total HT live
- ✅ `/approvisionnements/:id` — Fiche détaillée : 3 cards (Fournisseur lié, Dépôt, Total) + Notes + tableau lignes + bouton "Valider et recevoir" (vert success)
- ✅ Service `approvisionnementApi.js` (5 méthodes) — déjà existant, utilisé tel quel
- ✅ 2 routes ajoutées dans `App.js` protégées par RBAC `approvisionnements`

**Tests** :
- ✅ 2 approvisionnements seedés (`FABS-APP-0001` 2 lignes 236 000 FCFA, `FABS-APP-0002` 1 ligne 34 500 FCFA)
- ✅ UI Liste : 4 KPI + 2 lignes + badges Brouillon
- ✅ UI Fiche : navigation cliquable vers fournisseur, bouton Valider visible (statut brouillon)
- ✅ UI Modale : produits + fournisseurs chargés depuis l'API


### ✅ Sprint 3 — Module Fournisseurs Frontend (10 juin 2026)
**Périmètre V10** : Annuaire des partenaires d'approvisionnement + fiche détaillée + historique livraisons.

**Backend** :
- ✅ Module `fournisseurs_module.py` était déjà complet (CRUD + livraisons fournisseur)
- ✅ Bug critique corrigé : `resolve_user` exigeait header `Authorization` mais l'UI utilise cookies → fallback cookie `session_token` ajouté (idem `approvisionnement_module.py`)

**Frontend (2 pages créées)** :
- ✅ `/fournisseurs` — Liste + 4 KPI + recherche + modale création/édition (Dialog shadcn)
- ✅ `/fournisseurs/:fournisseurId` — Fiche détaillée avec onglets (Informations · Livraisons)
- ✅ 2 routes ajoutées dans `App.js` protégées par RBAC `fournisseurs`

**Tests** :
- ✅ 3 fournisseurs démo seedés (FABS-FRN-0001, 0002, 0003 — partenaires CI réels)
- ✅ UI Liste affiche 3 lignes, KPI corrects, palette FABS-CI respectée
- ✅ UI Fiche : tabs fonctionnent, liens téléphone/email cliquables
- ✅ Onglet Livraisons : état vide propre


### ✅ Sprint 2 — Dashboard FNE Enterprise (10 juin 2026)
**Périmètre V10** : Monitoring temps réel des certifications FNE — DGI Côte d'Ivoire.

**Backend** :
- ✅ 5 endpoints V10 ajoutés à `fne_module.py` : dashboard stats, balance sticker, logs, settings, ping
- ✅ Bug critique : `prefix="/api/fne"` → `"/fne"` (corrigé double prefix `/api/api/fne`)
- ✅ `app.state.db` + `app.state.redis` initialisés au startup
- ✅ Variables ENV officielles FABS-CI : `COMPANY_NCC=2302562N`, `IDU=CI-2023-0052129E`, `REGIME=TEE`, `SECTEUR=AUTRE`, `DRAN=DRAN VI`, `CENTRE=962 Impôts de Bingerville`, `FNE_BASE_URL=http://54.247.95.108/ws`

**Frontend (5 pages créées)** :
- ✅ `/fne` — Dashboard (6 KPI + Balance Sticker + Temps moyen + liste filtrable)
- ✅ `/fne/invoices/:invoiceId` — Détail (statut, QR code DGI, refund)
- ✅ `/fne/invoices/new` — Soumission (calcul TVA 18%, preview JSON, lignes dynamiques)
- ✅ `/fne/settings` — Configuration + Ping DGI live
- ✅ `/fne/logs` — Journal d'audit + recherche + export CSV
- ✅ Service `fneApi.js` (12 méthodes) + 5 routes dans `App.js`

**Tests** :
- ✅ Tous endpoints FNE → 200
- ✅ Ping DGI sandbox `http://54.247.95.108/ws` réussit (318 ms)
- ✅ UI : badge `MODE SANDBOX` affiché, alerte config DGI_API_KEY manquante, totaux calculés temps réel

**État** : 🟡 **SANDBOX** (en attente de `DGI_API_KEY` pour mode production)


### ✅ Sprint 1 — Moteur Central de Notifications ERP (10 juin 2026)
**Périmètre V10** : Notifications ERP internes uniquement (PAS email/SMS/WhatsApp/Push).

**Backend** :
- ✅ `NotificationConnectionManager` (singleton WS, par user_id, multi-session)
- ✅ Endpoint WebSocket `/api/notifications/ws` (auth cookie httpOnly OU query param)
- ✅ `_send_notification` enrichi → persiste + logue + push WS
- ✅ Helper `publish_notification(db, user_id, ...)` exporté pour autres modules métier
- ✅ Heartbeat WS (ping/pong) + push initial du compteur
- ✅ Indexes MongoDB créés au démarrage (`notifications`, `notification_logs`, `notification_preferences`)
- ✅ Redis installé sous supervisor (port 6379)

**Frontend** :
- ✅ Hook `useNotifications` (REST initial + WS + auto-reconnect backoff exponentiel + toast sonner)
- ✅ Topbar enrichi : cloche dynamique avec badge, dropdown avec liste live, indicateur WS vert
- ✅ Actions : marquer une notif lue, "Tout marquer lu", clic redirige vers `lien`
- ✅ Palette FABS-CI ajoutée à `tailwind.config.js` (tokens `fabs.*` — sans casser l'existant)

**Collections MongoDB** :
- `notifications` (notification_id, user_id, type, categorie, titre, message, lien, lue, created_at, expires_at)
- `notification_logs` (log_id, notification_id, user_id, channel, status, sessions_count, ts)
- `notification_preferences` (user_id, preferences{...})

**Vérifications** :
- ✅ `POST /api/notifications/test` → 200, message reçu en WS, badge UI passe de 1 → 2 sans refresh
- ✅ Log `channel:'websocket', status:'delivered', sessions_count:1` inséré
- ✅ Mark all as read → compteur 2 → 0

## Prochains sprints V10

- **Sprint 3** — Module Fournisseurs Frontend
- **Sprint 4** — Module Approvisionnements Frontend
- **Sprint 5** — Business Intelligence
- **Sprint 6** — Module RH Complet (audit préalable + 16 sous-modules)
- **Sprint 7** — Paramètres : Documents & Impression (5 modèles facture, filigranes)
- **Sprint 8** — ERP IA Native
- **Sprint 9** — Audit & Traçabilité globale
- **Sprint 10** — CI/CD & DevOps
- **Sprint 11** — Optimisation Performances
- **Sprint 12** — V10 Enterprise Final

## Choix techniques en attente
- **Stack frontend** : conservation JS + CRACO (pragmatique). Migration TS + Vite reportée (impact ~2-3 sprints).
- Toutes les autres décisions critiques sont prises et documentées.
