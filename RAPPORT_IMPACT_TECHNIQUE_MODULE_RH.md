# RAPPORT D'IMPACT TECHNIQUE - MODULE RH
## ERP FABS-CI - ÉDITIONS FABS-CI

**Date:** 1er Juin 2026  
**Objectif:** Analyse d'impact technique pour l'ajout du module RH  
**Statut:** ANALYSE TERMINÉE

---

## 1. RÉSUMÉ EXÉCUTIF

L'ajout du module RH à ERP FABS-CI aura un impact **MODÉRÉ** sur le système existant. L'architecture modulaire actuelle permet une intégration sans risque de rupture des fonctionnalités existantes.

**Impact global:** 
- **Backend:** 1 fichier nouveau, 3 fichiers à modifier
- **Frontend:** 10 fichiers nouveaux, 3 fichiers à modifier
- **MongoDB:** 13 nouvelles collections
- **API:** ~50 nouvelles routes
- **Risque:** FAIBLE

**Aucune donnée existante ne sera modifiée ou supprimée.**

---

## 2. FICHIERS À CRÉER

### 2.1 Backend - Nouveaux Fichiers (1)

**Fichier principal:**
```
backend/rh_module.py
```

**Description:** Module RH complet avec tous les sous-modules
- Taille estimée: ~2000 lignes
- Contient: Pydantic schemas, router factory, CRUD operations
- Pattern: Identique aux modules existants

**Sous-modules inclus dans rh_module.py:**
- Employés (employes)
- Départements (departements)
- Fonctions (fonctions)
- Catégories professionnelles (categories_pro)
- Contrats (contrats)
- Congés (conges)
- Absences (absences)
- Missions (missions)
- Documents RH (documents_rh)
- Signatures RH (signatures_rh)
- Habilitations ERP (habilitations_erp)
- Évaluations (evaluations)
- Délégations (delegations)
- Dashboard RH (dashboard_rh)
- Rapports RH (rapports_rh)

### 2.2 Frontend - Nouveaux Fichiers (10)

**Pages (10):**
```
frontend/src/pages/RHDashboard.jsx
frontend/src/pages/Employes.jsx
frontend/src/pages/Departements.jsx
frontend/src/pages/Fonctions.jsx
frontend/src/pages/CategoriesPro.jsx
frontend/src/pages/Contrats.jsx
frontend/src/pages/Conges.jsx
frontend/src/pages/Absences.jsx
frontend/src/pages/MissionsRH.jsx
frontend/src/pages/Evaluations.jsx
frontend/src/pages/RapportsRH.jsx
```

**Services (1):**
```
frontend/src/services/rhApi.js
```

**Description:**
- Taille estimée par page: ~500-800 lignes
- Pattern: Identique aux pages existantes
- Utilisation de shadcn/ui components
- Intégration avec React Hook Form + Zod

---

## 3. FICHIERS À MODIFIER

### 3.1 Backend - Fichiers à Modifier (3)

**1. backend/server.py**
- **Ligne à ajouter:** Import du module RH
- **Emplacement:** Après les imports existants (ligne ~56)
- **Code:**
```python
from rh_module import build_rh_router, seed_rh_data
```

- **Ligne à ajouter:** Enregistrement du router RH
- **Emplacement:** Dans la section "REGISTER ALL MODULE ROUTERS" (ligne ~810)
- **Code:**
```python
api_router.include_router(build_rh_router(db, resolve_user))
```

- **Ligne à ajouter:** Seed des données RH au startup
- **Emplacement:** Dans la fonction startup_event() (ligne ~818)
- **Code:**
```python
await seed_rh_data(db)
```

**Impact:** MINIMAL - 3 lignes à ajouter

**2. backend/rbac_constants.py**
- **Modification:** Ajout du rôle "responsable_rh"
- **Emplacement:** Dans ROLES (ligne ~9)
- **Code:**
```python
ROLES = {
    "super_admin",
    "directeur_general",
    "comptable",
    "directeur_commercial",
    "gestionnaire_stock",
    "responsable_magasinier",
    "secretariat",
    "service_logistique",
    "responsable_rh",  # NOUVEAU
}
```

- **Modification:** Ajout de la hiérarchie du rôle RH
- **Emplacement:** Dans ROLE_HIERARCHY (ligne ~23)
- **Code:**
```python
ROLE_HIERARCHY = {
    "super_admin": 8,
    "directeur_general": 7,
    "comptable": 6,
    "directeur_commercial": 5,
    "gestionnaire_stock": 4,
    "responsable_magasinier": 3,
    "secretariat": 2,
    "service_logistique": 1,
    "responsable_rh": 5,  # NOUVEAU - même niveau que directeur_commercial
}
```

- **Modification:** Ajout du module RH dans MODULE_PERMISSIONS
- **Emplacement:** Dans MODULE_PERMISSIONS (ligne ~39)
- **Code:**
```python
MODULE_PERMISSIONS = {
    # ... modules existants ...
    "rh": {
        "super_admin": 2,
        "directeur_general": 2,
        "responsable_rh": 2,
        "comptable": 1,
        "directeur_commercial": 1,
        "secretariat": 1,
        "gestionnaire_stock": 0,
        "responsable_magasinier": 0,
        "service_logistique": 0,
    },
}
```

**Impact:** FAIBLE - Ajout de permissions pour un nouveau module

**3. backend/dashboard_data.py**
- **Modification:** Ajout des stats RH dans build_dashboard_payload()
- **Emplacement:** Dans la fonction build_dashboard_payload()
- **Code:**
```python
# Ajout des stats RH pour les rôles autorisés
if role in ["super_admin", "directeur_general", "responsable_rh"]:
    payload["rh"] = {
        "total_employes": await db.employes.count_documents({"actif": True}),
        "employes_actifs": await db.employes.count_documents({"statut": "Actif"}),
        "employes_conge": await db.employes.count_documents({"statut": "En congé"}),
        "contrats_actifs": await db.contrats.count_documents({"statut": "Actif"}),
        "contrats_expirant": await db.contrats.count_documents({
            "date_fin": {"$lte": (datetime.now() + timedelta(days=90)).isoformat()}
        }),
    }
```

**Impact:** FAIBLE - Ajout de stats conditionnelles

### 3.2 Frontend - Fichiers à Modifier (3)

**1. frontend/src/constants/permissions.js**
- **Modification:** Ajout du module RH dans MODULES
- **Emplacement:** Dans MODULES array (ligne ~4)
- **Code:**
```javascript
export const MODULES = [
  { key: "dashboard", path: "/dashboard", label: "Tableau de bord", icon: "LayoutDashboard" },
  { key: "rh", path: "/rh", label: "Ressources Humaines", icon: "Users" },
  // ... autres modules ...
];
```

- **Modification:** Ajout des permissions RH dans PERMISSIONS
- **Emplacement:** Dans PERMISSIONS object (ligne ~33)
- **Code:**
```javascript
export const PERMISSIONS = {
  // ... modules existants ...
  rh: { 
    super_admin: 1, 
    directeur_general: 1, 
    responsable_rh: 1, 
    comptable: 1, 
    directeur_commercial: 1, 
    secretariat: 1, 
    gestionnaire_stock: 0, 
    responsable_magasinier: 0, 
    service_logistique: 0 
  },
};
```

- **Modification:** Ajout du rôle RH dans ROLES
- **Emplacement:** Dans ROLES object (ligne ~19)
- **Code:**
```javascript
export const ROLES = {
  super_admin: "Super Administrateur",
  directeur_general: "Directeur Général",
  comptable: "Comptable",
  directeur_commercial: "Directeur Commercial",
  gestionnaire_stock: "Gestionnaire de Stock",
  responsable_magasinier: "Responsable Magasinier",
  secretariat: "Secrétariat",
  service_logistique: "Service Logistique",
  responsable_rh: "Responsable RH",  // NOUVEAU
};
```

**Impact:** FAIBLE - Ajout d'un module dans la matrice de permissions

**2. frontend/src/components/layout/Sidebar.jsx**
- **Modification:** Ajout de l'icône Users si non présente
- **Emplacement:** Dans ICONS import (ligne ~2)
- **Code:**
```javascript
import {
  LayoutDashboard,
  Users,  // Déjà présent
  // ... autres icônes ...
} from "lucide-react";
```

**Impact:** NÉGLIGEABLE - L'icône Users est déjà importée

**3. frontend/src/App.js**
- **Modification:** Ajout des routes RH
- **Emplacement:** Dans la section Routes (ligne ~60)
- **Code:**
```javascript
// Lazy load
const RHDashboard = lazy(() => import("./pages/RHDashboard"));
const Employes = lazy(() => import("./pages/Employes"));
const Departements = lazy(() => import("./pages/Departements"));
const Fonctions = lazy(() => import("./pages/Fonctions"));
const CategoriesPro = lazy(() => import("./pages/CategoriesPro"));
const Contrats = lazy(() => import("./pages/Contrats"));
const Conges = lazy(() => import("./pages/Conges"));
const Absences = lazy(() => import("./pages/Absences"));
const MissionsRH = lazy(() => import("./pages/MissionsRH"));
const Evaluations = lazy(() => import("./pages/Evaluations"));
const RapportsRH = lazy(() => import("./pages/RapportsRH"));

// Routes
<Route
  path="/rh"
  element={
    <ProtectedRoute moduleKey="rh">
      <RHDashboard />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/employes"
  element={
    <ProtectedRoute moduleKey="rh">
      <Employes />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/departements"
  element={
    <ProtectedRoute moduleKey="rh">
      <Departements />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/fonctions"
  element={
    <ProtectedRoute moduleKey="rh">
      <Fonctions />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/categories-pro"
  element={
    <ProtectedRoute moduleKey="rh">
      <CategoriesPro />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/contrats"
  element={
    <ProtectedRoute moduleKey="rh">
      <Contrats />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/conges"
  element={
    <ProtectedRoute moduleKey="rh">
      <Conges />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/absences"
  element={
    <ProtectedRoute moduleKey="rh">
      <Absences />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/missions"
  element={
    <ProtectedRoute moduleKey="rh">
      <MissionsRH />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/evaluations"
  element={
    <ProtectedRoute moduleKey="rh">
      <Evaluations />
    </ProtectedRoute>
  }
/>
<Route
  path="/rh/rapports"
  element={
    <ProtectedRoute moduleKey="rh">
      <RapportsRH />
    </ProtectedRoute>
  }
/>
```

**Impact:** FAIBLE - Ajout de routes standard

---

## 4. NOUVELLES COLLECTIONS MONGODB

### 4.1 Collections à Créer (13)

**1. employes**
- **Description:** Fiches employés complets
- **Champs principaux:**
  - employe_id (string, unique)
  - matricule (string, unique)
  - nom (string)
  - prenoms (string)
  - photo (string, optional)
  - sexe (enum: H, F)
  - date_naissance (date)
  - lieu_naissance (string)
  - nationalite (string)
  - situation_matrimoniale (enum)
  - nombre_enfants (int)
  - groupe_sanguin (string, optional)
  - telephone_principal (string)
  - telephone_secondaire (string, optional)
  - email (string, optional)
  - adresse (string)
  - ville (string)
  - commune (string)
  - personne_a_prevenir (string)
  - telephone_urgence (string)
  - numero_cni (string)
  - date_delivrance_cni (date)
  - date_expiration_cni (date)
  - numero_cnps (string)
  - date_affiliation_cnps (date)
  - numero_cmu (string, optional)
  - numero_compte_bancaire (string)
  - banque (string)
  - numero_permis (string, optional)
  - date_expiration_permis (date, optional)
  - date_embauche (date)
  - date_prise_fonction (date)
  - departement_id (string, ref: departements)
  - fonction_id (string, ref: fonctions)
  - categorie_pro_id (string, ref: categories_pro)
  - echelon (string)
  - superieur_hierarchique_id (string, ref: employes, optional)
  - type_employe (enum)
  - statut (enum: Actif, En congé, Suspendu, Démissionnaire, Licencié, Retraité)
  - zone_commerciale (string, optional)
  - portefeuille_clients (list, optional)
  - objectif_mensuel (float, optional)
  - objectif_annuel (float, optional)
  - commission (float, optional)
  - montant_ventes (float, optional)
  - montant_encaisse (float, optional)
  - creances_clients (float, optional)
  - depot_principal (string, optional)
  - responsable_inventaire (bool, optional)
  - responsable_reapprovisionnement (bool, optional)
  - responsable_controle_stock (bool, optional)
  - user_id (string, ref: users, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** employe_id (unique), matricule (unique), email, numero_cni, numero_cnps

**2. departements**
- **Description:** Départements de l'entreprise
- **Champs principaux:**
  - departement_id (string, unique)
  - nom (string, unique)
  - description (string, optional)
  - responsable_id (string, ref: employes, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** departement_id (unique), nom (unique)
- **Données initiales:** Direction Générale, Secrétariat & Administration, Informatique, Comptabilité, Commercial, Logistique, Magasin & Stock

**3. fonctions**
- **Description:** Fonctions/Postes
- **Champs principaux:**
  - fonction_id (string, unique)
  - nom (string, unique)
  - description (string, optional)
  - departement_id (string, ref: departements, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** fonction_id (unique), nom (unique)
- **Données initiales:** Directeur Général, Directeur Général Adjoint, Responsable Informatique, Comptable, Assistante Comptable, Assistante de Direction, Secrétaire, Assistante Administrative, Commercial, Commerciale, Responsable Logistique Commerciale, Gestionnaire de Stock, Chef Magasinier, Magasinier, Livreur, Chauffeur-Livreur, Agent Logistique, Stagiaire, Consultant

**4. categories_pro**
- **Description:** Catégories professionnelles
- **Champs principaux:**
  - categorie_pro_id (string, unique)
  - nom (string, unique)
  - description (string, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** categorie_pro_id (unique), nom (unique)
- **Données initiales:** Direction, Cadre Supérieur, Cadre, Agent de Maîtrise, Employé, Ouvrier, Stagiaire, Prestataire

**5. contrats**
- **Description:** Contrats de travail
- **Champs principaux:**
  - contrat_id (string, unique)
  - reference (string, unique, auto: FABS-CTR-XXXX)
  - employe_id (string, ref: employes)
  - type_contrat (enum: CDI, CDD, Stage, Consultant, Prestataire)
  - date_debut (date)
  - date_fin (date, optional)
  - periode_essai (int, optional, jours)
  - salaire_base (float)
  - prime_transport (float, default: 0)
  - prime_logement (float, default: 0)
  - prime_fonction (float, default: 0)
  - autres_primes (float, default: 0)
  - observations (string, optional)
  - statut (enum: Actif, Expiré, Résilié)
  - document_id (string, ref: file_storage, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** contrat_id (unique), reference (unique), employe_id, date_fin
- **Alertes:** Contrat expirant dans 90/60/30 jours

**6. conges**
- **Description:** Demandes de congés
- **Champs principaux:**
  - conge_id (string, unique)
  - employe_id (string, ref: employes)
  - type_conge (enum: conge_annuel, conge_maladie, conge_maternite, permission, conge_exceptionnel)
  - date_debut (date)
  - date_fin (date)
  - nombre_jours (int)
  - motif (string)
  - piece_jointe_id (string, ref: file_storage, optional)
  - statut (enum: en_attente, approuve_sup, approuve_direction, approuve_rh, refuse, annule)
  - superieur_hierarchique_id (string, ref: employes, optional)
  - approbation_sup_date (datetime, optional)
  - approbation_sup_commentaire (string, optional)
  - approbation_direction_id (string, ref: employes, optional)
  - approbation_direction_date (datetime, optional)
  - approbation_direction_commentaire (string, optional)
  - approbation_rh_id (string, ref: employes, optional)
  - approbation_rh_date (datetime, optional)
  - approbation_rh_commentaire (string, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** conge_id (unique), employe_id, statut, date_debut
- **Workflow:** Employé → Supérieur → Direction → RH

**7. absences**
- **Description:** Enregistrement des absences
- **Champs principaux:**
  - absence_id (string, unique)
  - employe_id (string, ref: employes)
  - type_absence (enum: retard, absence_justifiee, absence_non_justifiee, sortie_autorisee)
  - date (date)
  - heure_debut (time, optional)
  - heure_fin (time, optional)
  - duree_minutes (int)
  - motif (string, optional)
  - justifie (bool)
  - piece_jointe_id (string, ref: file_storage, optional)
  - enregistre_par_id (string, ref: employes)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** absence_id (unique), employe_id, date
- **Calcul automatique:** Nombre d'absences, nombre de retards

**8. missions**
- **Description:** Missions professionnelles
- **Champs principaux:**
  - mission_id (string, unique)
  - reference (string, unique, auto: FABS-MIS-XXXX)
  - employe_id (string, ref: employes)
  - type_mission (enum: mission_commerciale, mission_logistique, mission_administrative, mission_inventaire)
  - ville (string)
  - date_depart (date)
  - date_retour (date)
  - objet (string)
  - budget (float, optional)
  - compte_rendu (string, optional)
  - statut (enum: planifiee, en_cours, terminee, annulee)
  - document_id (string, ref: file_storage, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** mission_id (unique), reference (unique), employe_id, statut
- **Alertes:** Mission non clôturée

**9. documents_rh**
- **Description:** Documents RH des employés
- **Note:** Utilisation de la collection file_storage existante
- **Type document:** "rh_document"
- **Sous-types:** cni, contrat, cv, diplome, photo_identite, attestation_cnps, attestation_cmu, permis_conduire, certificat_medical, autorisation_parentale
- **Association:** entite_type = "employe", entite_id = employe_id
- **Aucune nouvelle collection nécessaire** - Réutilisation de file_storage

**10. signatures_rh**
- **Description:** Signatures des employés
- **Note:** Utilisation de la collection signatures_electroniques existante
- **Type entité:** "employe"
- **Types signature:** dessin, texte, image
- **Aucune nouvelle collection nécessaire** - Réutilisation de signatures_electroniques

**11. habilitations_erp**
- **Description:** Habilitations ERP des employés
- **Champs principaux:**
  - habilitation_id (string, unique)
  - employe_id (string, ref: employes)
  - role_erp (string, ref: rbac_constants.ROLES)
  - modules_autorises (list of strings)
  - date_debut (date)
  - date_fin (date, optional)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** habilitation_id (unique), employe_id, role_erp
- **Relation:** employe.user_id → users.user_id (optionnel)

**12. evaluations**
- **Description:** Évaluations des employés
- **Champs principaux:**
  - evaluation_id (string, unique)
  - employe_id (string, ref: employes)
  - type_evaluation (enum: commercial, magasinier, gestionnaire_stock, administratif)
  - periode_debut (date)
  - periode_fin (date)
  - criteres (dict)
  - note_globale (float)
  - commentaire (string, optional)
  - evaluateur_id (string, ref: employes)
  - statut (enum: brouillon, soumis, approuve, refuse)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** evaluation_id (unique), employe_id, periode_fin
- **Critères par type:**
  - Commercial: nombre_clients, nombre_commandes, montant_ventes, montant_encaisse, creances, objectif_atteint
  - Magasinier: preparation_commandes, inventaires, erreurs_stock, receptions
  - Gestionnaire Stock: exactitude_stock, inventaires_realises, ecarts_detectes
  - Administration: respect_delais, gestion_courrier, gestion_documents

**13. delegations**
- **Description:** Délégations et intérim
- **Champs principaux:**
  - delegation_id (string, unique)
  - titulaire_id (string, ref: employes)
  - remplaçant_id (string, ref: employes)
  - date_debut (date)
  - date_fin (date)
  - motif (string)
  - actif (bool)
  - created_at (datetime)
  - updated_at (datetime)
- **Indexes:** delegation_id (unique), titulaire_id, remplaçant_id, date_debut

### 4.2 Collection Counters (Modification)

**Modification de la collection existante `counters`:**
- Ajout de compteurs pour les références auto-incrémentées
- Nouveaux compteurs: contrats, missions
- Structure existante conservée

---

## 5. NOUVELLES ROUTES API

### 5.1 Routes Backend (~50 routes)

**Prefix:** `/api/rh`

**Routes par sous-module:**

**1. Dashboard RH (4 routes)**
- `GET /api/rh/dashboard` - Stats dashboard RH
- `GET /api/rh/dashboard/alertes` - Alertes RH
- `GET /api/rh/dashboard/graphiques` - Données graphiques
- `GET /api/rh/dashboard/kpi` - KPIs RH

**2. Employés (8 routes)**
- `GET /api/rh/employes` - Liste employés (pagination, filtres)
- `GET /api/rh/employes/{employe_id}` - Détail employé
- `POST /api/rh/employes` - Créer employé
- `PATCH /api/rh/employes/{employe_id}` - Modifier employé
- `DELETE /api/rh/employes/{employe_id}` - Désactiver employé (soft delete)
- `GET /api/rh/employes/{employe_id}/contrats` - Contrats de l'employé
- `GET /api/rh/employes/{employe_id}/conges` - Congés de l'employé
- `GET /api/rh/employes/{employe_id}/evaluations` - Évaluations de l'employé

**3. Départements (5 routes)**
- `GET /api/rh/departements` - Liste départements
- `GET /api/rh/departements/{departement_id}` - Détail département
- `POST /api/rh/departements` - Créer département
- `PATCH /api/rh/departements/{departement_id}` - Modifier département
- `DELETE /api/rh/departements/{departement_id}` - Désactiver département

**4. Fonctions (5 routes)**
- `GET /api/rh/fonctions` - Liste fonctions
- `GET /api/rh/fonctions/{fonction_id}` - Détail fonction
- `POST /api/rh/fonctions` - Créer fonction
- `PATCH /api/rh/fonctions/{fonction_id}` - Modifier fonction
- `DELETE /api/rh/fonctions/{fonction_id}` - Désactiver fonction

**5. Catégories Professionnelles (5 routes)**
- `GET /api/rh/categories-pro` - Liste catégories
- `GET /api/rh/categories-pro/{categorie_pro_id}` - Détail catégorie
- `POST /api/rh/categories-pro` - Créer catégorie
- `PATCH /api/rh/categories-pro/{categorie_pro_id}` - Modifier catégorie
- `DELETE /api/rh/categories-pro/{categorie_pro_id}` - Désactiver catégorie

**6. Contrats (7 routes)**
- `GET /api/rh/contrats` - Liste contrats
- `GET /api/rh/contrats/{contrat_id}` - Détail contrat
- `POST /api/rh/contrats` - Créer contrat
- `PATCH /api/rh/contrats/{contrat_id}` - Modifier contrat
- `DELETE /api/rh/contrats/{contrat_id}` - Désactiver contrat
- `GET /api/rh/contrats/alertes` - Alertes contrats expirants
- `GET /api/rh/contrats/employe/{employe_id}` - Contrats d'un employé

**7. Congés (8 routes)**
- `GET /api/rh/conges` - Liste congés
- `GET /api/rh/conges/{conge_id}` - Détail congé
- `POST /api/rh/conges` - Créer demande de congé
- `PATCH /api/rh/conges/{conge_id}` - Modifier congé
- `DELETE /api/rh/conges/{conge_id}` - Annuler congé
- `POST /api/rh/conges/{conge_id}/approuver-sup` - Approuver par supérieur
- `POST /api/rh/conges/{conge_id}/approuver-direction` - Approuver par direction
- `POST /api/rh/conges/{conge_id}/approuver-rh` - Approuver par RH

**8. Absences (6 routes)**
- `GET /api/rh/absences` - Liste absences
- `GET /api/rh/absences/{absence_id}` - Détail absence
- `POST /api/rh/absences` - Enregistrer absence
- `PATCH /api/rh/absences/{absence_id}` - Modifier absence
- `DELETE /api/rh/absences/{absence_id}` - Supprimer absence
- `GET /api/rh/absences/employe/{employe_id}` - Absences d'un employé

**9. Missions (7 routes)**
- `GET /api/rh/missions` - Liste missions
- `GET /api/rh/missions/{mission_id}` - Détail mission
- `POST /api/rh/missions` - Créer mission
- `PATCH /api/rh/missions/{mission_id}` - Modifier mission
- `DELETE /api/rh/missions/{mission_id}` - Annuler mission
- `POST /api/rh/missions/{mission_id}/cloturer` - Clôturer mission
- `GET /api/rh/missions/alertes` - Alertes missions non clôturées

**10. Documents RH (4 routes)**
- `GET /api/rh/documents` - Liste documents RH
- `POST /api/rh/documents` - Upload document RH
- `GET /api/rh/documents/{document_id}` - Télécharger document
- `DELETE /api/rh/documents/{document_id}` - Supprimer document
- **Note:** Utilisation de file_storage_module existant

**11. Signatures RH (4 routes)**
- `GET /api/rh/signatures` - Liste signatures
- `POST /api/rh/signatures` - Enregistrer signature
- `GET /api/rh/signatures/{signature_id}` - Récupérer signature
- `DELETE /api/rh/signatures/{signature_id}` - Supprimer signature
- **Note:** Utilisation de workflow_approvals_module existant

**12. Habilitations ERP (5 routes)**
- `GET /api/rh/habilitations` - Liste habilitations
- `GET /api/rh/habilitations/{habilitation_id}` - Détail habilitation
- `POST /api/rh/habilitations` - Créer habilitation
- `PATCH /api/rh/habilitations/{habilitation_id}` - Modifier habilitation
- `DELETE /api/rh/habilitations/{habilitation_id}` - Désactiver habilitation

**13. Évaluations (6 routes)**
- `GET /api/rh/evaluations` - Liste évaluations
- `GET /api/rh/evaluations/{evaluation_id}` - Détail évaluation
- `POST /api/rh/evaluations` - Créer évaluation
- `PATCH /api/rh/evaluations/{evaluation_id}` - Modifier évaluation
- `DELETE /api/rh/evaluations/{evaluation_id}` - Supprimer évaluation
- `GET /api/rh/evaluations/employe/{employe_id}` - Évaluations d'un employé

**14. Délégations (5 routes)**
- `GET /api/rh/delegations` - Liste délégations
- `GET /api/rh/delegations/{delegation_id}` - Détail délégation
- `POST /api/rh/delegations` - Créer délégation
- `PATCH /api/rh/delegations/{delegation_id}` - Modifier délégation
- `DELETE /api/rh/delegations/{delegation_id}` - Supprimer délégation

**15. Rapports RH (6 routes)**
- `GET /api/rh/rapports/employes` - Rapport employés
- `GET /api/rh/rapports/contrats` - Rapport contrats
- `GET /api/rh/rapports/conges` - Rapport congés
- `GET /api/rh/rapports/absences` - Rapport absences
- `GET /api/rh/rapports/evaluations` - Rapport évaluations
- `GET /api/rh/rapports/export` - Export (PDF, Excel, CSV)

**Total estimé:** ~50 routes

### 5.2 Routes Frontend (11 routes)

**Routes React Router:**
- `/rh` - Dashboard RH
- `/rh/employes` - Liste employés
- `/rh/employes/:id` - Détail employé
- `/rh/departements` - Départements
- `/rh/fonctions` - Fonctions
- `/rh/categories-pro` - Catégories professionnelles
- `/rh/contrats` - Contrats
- `/rh/conges` - Congés
- `/rh/absences` - Absences
- `/rh/missions` - Missions
- `/rh/evaluations` - Évaluations
- `/rh/rapports` - Rapports RH

---

## 6. NOUVEAUX ÉCRANS REACT

### 6.1 Pages à Créer (11 pages)

**1. RHDashboard.jsx**
- **Description:** Tableau de bord RH
- **Contenu:**
  - KPIs: Total employés, Actifs, En congé, Absents, Contrats actifs, Contrats expirants, Missions en cours
  - Graphiques: Employés par service, par fonction, par catégorie, Répartition H/F
  - Alertes: Contrats expirants, CNI expirées, CNPS manquantes, Congés en attente, Missions non clôturées
- **Composants:** Cards, Charts (Recharts), Alertes, Tables

**2. Employes.jsx**
- **Description:** Gestion des employés
- **Contenu:**
  - Tableau liste employés avec filtres (département, fonction, statut)
  - Recherche avancée
  - Actions: Voir, Modifier, Désactiver
  - Bouton "Nouvel employé"
- **Composants:** Table, Dialog, Form, Filters

**3. Departements.jsx**
- **Description:** Gestion des départements
- **Contenu:**
  - Liste départements
  - CRUD complet
  - Association responsable
- **Composants:** Table, Dialog, Form

**4. Fonctions.jsx**
- **Description:** Gestion des fonctions
- **Contenu:**
  - Liste fonctions
  - CRUD complet
  - Association département
- **Composants:** Table, Dialog, Form

**5. CategoriesPro.jsx**
- **Description:** Gestion des catégories professionnelles
- **Contenu:**
  - Liste catégories
  - CRUD complet
- **Composants:** Table, Dialog, Form

**6. Contrats.jsx**
- **Description:** Gestion des contrats
- **Contenu:**
  - Liste contrats avec alertes d'expiration
  - CRUD complet
  - Workflow de validation
- **Composants:** Table, Dialog, Form, Alerts

**7. Conges.jsx**
- **Description:** Gestion des congés
- **Contenu:**
  - Liste demandes de congé
  - Workflow d'approbation (Supérieur → Direction → RH)
  - Calendrier des congés
- **Composants:** Table, Dialog, Form, Calendar, Workflow

**8. Absences.jsx**
- **Description:** Gestion des absences
- **Contenu:**
  - Liste absences
  - Enregistrement rapide
  - Statistiques (nombre absences, retards)
- **Composants:** Table, Dialog, Form, Stats

**9. MissionsRH.jsx**
- **Description:** Gestion des missions
- **Contenu:**
  - Liste missions
  - CRUD complet
  - Clôture de mission
  - Compte rendu
- **Composants:** Table, Dialog, Form, Status

**10. Evaluations.jsx**
- **Description:** Évaluations des employés
- **Contenu:**
  - Liste évaluations
  - Formulaire d'évaluation par type
  - Historique
- **Composants:** Table, Dialog, Form, Charts

**11. RapportsRH.jsx**
- **Description:** Rapports RH
- **Contenu:**
  - Liste des rapports disponibles
  - Génération de rapports
  - Export (PDF, Excel, CSV)
- **Composants:** Cards, Buttons, Export

---

## 7. DÉPENDANCES CONCERNÉES

### 7.1 Backend Dependencies

**Aucune nouvelle dépendance requise**

**Dépendances existantes utilisées:**
- fastapi (routes)
- pydantic (schemas)
- motor (MongoDB)
- datetime (dates)
- typing (types)

**Impact:** NUL - Aucune nouvelle dépendance

### 7.2 Frontend Dependencies

**Aucune nouvelle dépendance requise**

**Dépendances existantes utilisées:**
- react (components)
- react-router-dom (routing)
- axios (API calls)
- recharts (charts)
- react-hook-form (forms)
- zod (validation)
- lucide-react (icons)
- @radix-ui/* (UI components)
- date-fns (dates)

**Impact:** NUL - Aucune nouvelle dépendance

---

## 8. RISQUES ÉVENTUELS

### 8.1 Risques Identifiés

**Risque global:** FAIBLE

**Risques spécifiques:**

**1. Conflit avec collection `users`**
- **Risque:** FAIBLE
- **Description:** La collection `users` existe déjà pour l'authentification
- **Mitigation:** Créer une collection séparée `employes` avec une relation optionnelle vers `users`
- **Impact:** NUL si mitigation appliquée

**2. Performance MongoDB**
- **Risque:** FAIBLE
- **Description:** Ajout de 13 collections pourrait impacter légèrement les performances
- **Mitigation:** Indexation appropriée, utilisation de cache Redis
- **Impact:** NÉGLIGEABLE

**3. Complexité RBAC**
- **Risque:** FAIBLE
- **Description:** Ajout d'un nouveau rôle et permissions
- **Mitigation:** Suivre le pattern existant, tests de permissions
- **Impact:** NÉGLIGEABLE

**4. Frontend Bundle Size**
- **Risque:** FAIBLE
- **Description:** Ajout de 11 pages pourrait augmenter le bundle size
- **Mitigation:** Lazy loading déjà implémenté, code splitting
- **Impact:** NÉGLIGEABLE

**5. Données de seed**
- **Risque:** FAIBLE
- **Description:** Besoin de peupler les données initiales (départements, fonctions, etc.)
- **Mitigation:** Script de seed avec les données fournies dans le cahier des charges
- **Impact:** NÉGLIGEABLE

### 8.2 Risques Rejetés

**Risque de rupture de fonctionnalités existantes:**
- **Évaluation:** REJETÉ
- **Justification:** Architecture modulaire, isolation des modules, soft delete, tests existants

**Risque de conflit de noms de collections:**
- **Évaluation:** REJETÉ
- **Justification:** Préfixe spécifique RH, vérification des collections existantes

**Risque de conflit de routes:**
- **Évaluation:** REJETÉ
- **Justification:** Préfixe `/api/rh` distinct, vérification des routes existantes

---

## 9. PLAN DE MIGRATION

### 9.1 Phase 1: Préparation (Backend)

**Tâches:**
1. Créer le fichier `backend/rh_module.py`
2. Implémenter les Pydantic schemas
3. Implémenter les router functions
4. Ajouter l'import dans `server.py`
5. Ajouter le router dans `server.py`
6. Modifier `rbac_constants.py`
7. Modifier `dashboard_data.py`
8. Créer le script de seed `seed_rh_data()`

**Durée estimée:** 4-6 heures

### 9.2 Phase 2: Préparation (Frontend)

**Tâches:**
1. Créer le service `frontend/src/services/rhApi.js`
2. Modifier `frontend/src/constants/permissions.js`
3. Modifier `frontend/src/App.js` (routes)
4. Créer les 11 pages React
5. Tester la navigation

**Durée estimée:** 8-10 heures

### 9.3 Phase 3: Intégration

**Tâches:**
1. Intégrer avec le système de notifications
2. Intégrer avec le module documentaire
3. Intégrer avec l'audit trail
4. Tester les workflows (congés, évaluations)
5. Tester les alertes

**Durée estimée:** 4-6 heures

### 9.4 Phase 4: Tests

**Tâches:**
1. Tests unitaires backend
2. Tests d'intégration
3. Tests frontend
4. Tests RBAC
5. Tests de performance
6. Tests de sécurité

**Durée estimée:** 4-6 heures

**Durée totale estimée:** 20-28 heures

---

## 10. PLAN DE ROLLBACK

### 10.1 Rollback Backend

**Si problème détecté:**
1. Commenter l'import dans `server.py`
2. Commenter l'enregistrement du router dans `server.py`
3. Commenter le seed dans `server.py`
4. Restaurer `rbac_constants.py` (git checkout)
5. Restaurer `dashboard_data.py` (git checkout)
6. Redémarrer le serveur

**Durée:** < 5 minutes

### 10.2 Rollback Frontend

**Si problème détecté:**
1. Commenter les routes RH dans `App.js`
2. Restaurer `permissions.js` (git checkout)
3. Rebuild frontend

**Durée:** < 10 minutes

### 10.3 Rollback MongoDB

**Si problème détecté:**
1. Supprimer les collections RH (drop)
2. Restaurer la collection counters (si modifiée)

**Durée:** < 5 minutes

**Rollback total:** < 20 minutes

---

## 11. VALIDATION

### 11.1 Checklist Pré-Déploiement

**Backend:**
- [ ] Module RH créé et testé
- [ ] Router enregistré dans server.py
- [ ] RBAC mis à jour
- [ ] Dashboard data mis à jour
- [ ] Seed data créé
- [ ] Tests backend passés
- [ ] Documentation Swagger générée

**Frontend:**
- [ ] Service RH créé
- [ ] Permissions mises à jour
- [ ] Routes ajoutées
- [ ] Pages créées
- [ ] Navigation testée
- [ ] Tests frontend passés

**MongoDB:**
- [ ] Collections créées
- [ ] Index créés
- [ ] Seed data inséré
- [ ] Données validées

**Intégration:**
- [ ] Notifications intégrées
- [ ] Documents intégrés
- [ ] Audit trail intégré
- [ ] Workflows testés

### 11.2 Checklist Post-Déploiement

**Fonctionnalités:**
- [ ] Dashboard RH accessible
- [ ] CRUD employés fonctionnel
- [ ] CRUD départements fonctionnel
- [ ] CRUD fonctions fonctionnel
- [ ] CRUD catégories fonctionnel
- [ ] CRUD contrats fonctionnel
- [ ] Workflow congés fonctionnel
- [ ] CRUD absences fonctionnel
- [ ] CRUD missions fonctionnel
- [ ] CRUD évaluations fonctionnel
- [ ] Rapports RH fonctionnels

**Sécurité:**
- [ ] RBAC fonctionnel
- [ ] Permissions respectées
- [ ] Audit trail fonctionnel
- [ ] Input sanitization fonctionnel

**Performance:**
- [ ] Temps de réponse acceptable
- [ ] Cache Redis fonctionnel
- [ ] Index MongoDB utilisés

---

## 12. CONCLUSION

### 12.1 Impact Global

**Niveau d'impact:** MODÉRÉ

**Justification:**
- 1 fichier backend nouveau
- 3 fichiers backend à modifier (modifications mineures)
- 10 fichiers frontend nouveaux
- 3 fichiers frontend à modifier (modifications mineures)
- 13 nouvelles collections MongoDB
- ~50 nouvelles routes API
- 11 nouvelles pages React

**Risque:** FAIBLE

**Justification:**
- Architecture modulaire éprouvée
- Patterns réutilisables établis
- Aucune dépendance nouvelle
- Rollback simple et rapide
- Tests existants

### 12.2 Recommandation

**PROCÉDER AU DÉVELOPPEMENT**

L'analyse d'impact technique confirme que l'ajout du module RH est:
- Techniquement faisable
- Sans risque majeur
- Conforme à l'architecture existante
- Réversible en cas de problème

### 12.3 Prochaines Étapes

1. Développer le module RH backend
2. Développer le module RH frontend
3. Intégrer avec les systèmes existants
4. Tests complets
5. Audit post-développement
6. Déploiement

---

**Rapport généré automatiquement par Cascade AI**  
**ERP FABS-CI - ÉDITIONS FABS-CI**  
**Date: 1er Juin 2026**
