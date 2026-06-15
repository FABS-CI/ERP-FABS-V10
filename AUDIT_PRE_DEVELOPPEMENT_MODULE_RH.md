# RAPPORT D'AUDIT PRÉ-DÉVELOPPEMENT - MODULE RH
## ERP FABS-CI - ÉDITIONS FABS-CI

**Date:** 1er Juin 2026  
**Objectif:** Audit complet avant ajout du module RH  
**Statut:** AUDIT TERMINÉ

---

## 1. RÉSUMÉ EXÉCUTIF

L'ERP FABS-CI est une application métier complète et fonctionnelle dédiée à une maison d'édition scolaire ivoirienne. L'audit révèle une architecture solide, modulaire et bien structurée, prête pour l'ajout du module RH sans risque de rupture des fonctionnalités existantes.

**Points forts identifiés:**
- Architecture modulaire cohérente (pattern router factory)
- Système RBAC mature et centralisé
- Audit trail intégré
- Système de notifications fonctionnel
- Module documentaire existant
- Sécurité robuste (JWT, httpOnly cookies, rate limiting)
- Code production-ready avec tests

**Aucun conflit majeur détecté** - Le module RH peut être ajouté en suivant les patterns existants.

---

## 2. ARCHITECTURE BACKEND FASTAPI

### 2.1 Structure Générale

**Fichier principal:** `backend/server.py` (943 lignes)

**Stack technique:**
- FastAPI 0.110.1
- Motor 3.3.1 (MongoDB async driver)
- Pydantic 2.6.4 (validation)
- JWT + bcrypt (authentification)
- Redis 5.0.0 (caching)
- slowapi (rate limiting)
- Prometheus (monitoring)

**Pattern architectural:**
```
server.py (main app)
├── Auth endpoints (/auth/*)
├── Dashboard endpoint (/dashboard/stats)
├── Health check (/health)
└── Module routers (build_*_router pattern)
    ├── build_clients_router(db, resolve_user)
    ├── build_products_router(db, resolve_user)
    ├── build_commandes_router(db, resolve_user)
    └── ... (24+ modules)
```

### 2.2 Authentification & Sécurité

**JWT Token Management:**
- Access token: 30 minutes expiry
- Refresh token: 7 days expiry
- Stockage: httpOnly cookie (secure)
- Secret: configurable via environment variable

**Security Headers:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000
- Referrer-Policy: strict-origin-when-cross-origin

**Rate Limiting:**
- Login: 5 tentatives/minute/IP
- User creation: 10 tentatives/minute
- Password change: 5 tentatives/minute

**Input Sanitization:**
- Fonction `sanitize_string()` pour XSS prevention
- Fonction `sanitize_dict()` pour récursion
- HTML escaping + pattern removal

### 2.3 Audit Trail

**Fonction:** `log_audit_event()` dans server.py

**Collections MongoDB:**
- `audit_logs` - Journal des actions

**Champs audités:**
- audit_id (généré automatiquement)
- user_id
- action (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT)
- resource_type (client, produit, commande, etc.)
- resource_id
- details (dict)
- ip_address
- timestamp (ISO format)

### 2.4 Caching Redis

**Fonctions:**
- `get_cached(key)` - Récupérer valeur
- `set_cached(key, value, ttl=300)` - Stocker avec TTL
- `invalidate_cache(pattern)` - Invalider par pattern

**Utilisation actuelle:** Dashboard stats (5 minutes TTL)

### 2.5 Pattern Module Router

**Structure type d'un module:**
```python
def build_xxx_router(db, resolve_user):
    router = APIRouter(prefix="/xxx", tags=["xxx"])
    
    READ_ROLES = {...}
    WRITE_ROLES = {...}
    
    @router.get("", response_model=List[xxxOut])
    async def list_xxx(...):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        # ...
    
    @router.post("", response_model=xxxOut)
    async def create_xxx(...):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès refusé")
        # ...
    
    return router
```

**Modules existants (24+):**
1. clients_module.py
2. products_module.py
3. commandes_module.py
4. factures_module.py
5. paiements_module.py
6. stock_module.py
7. bons_livraison_module.py
8. bons_retour_module.py
9. comptabilite_module.py
10. comptabilite_avancee_module.py
11. administration_module.py
12. recherche_module.py
13. documents_ai_module.py
14. analytics_module.py
15. colisage_module.py
16. notifications_module.py
17. logistique_module.py
18. fleet_module.py
19. logistics_costs_module.py
20. multi_channel_notifications_module.py
21. bi_analytics_module.py
22. workflow_approvals_module.py
23. file_storage_module.py
24. backup_module.py

---

## 3. ARCHITECTURE FRONTEND REACT

### 3.1 Structure Générale

**Stack technique:**
- React 19.0.0
- TypeScript 5.7.3
- Tailwind CSS 3.4.17
- React Router v7.5.1
- Axios 1.8.4
- shadcn/ui (Radix UI components)
- Lucide React 0.507.0 (icons)
- Recharts 3.6.0 (charts)
- React Hook Form 7.56.2
- Zod 3.24.4 (validation)

**Structure des dossiers:**
```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── DashboardLayout.jsx
│   │   ├── Sidebar.jsx
│   │   └── Topbar.jsx
│   └── ui/ (46 shadcn/ui components)
├── pages/ (36 pages)
├── services/ (25 API services)
├── hooks/ (useAuth, useToast, useDarkMode, useDebouncedValue)
├── constants/
│   ├── company.js
│   └── permissions.js
└── config/
    └── api.js
```

### 3.2 Routing & Navigation

**Fichier:** `frontend/src/App.js` (390 lignes)

**Pattern:**
- Lazy loading pour code splitting
- Protected routes avec RBAC
- Module key pour permissions

**Exemple de route:**
```jsx
<Route
  path="/clients"
  element={
    <ProtectedRoute moduleKey="clients">
      <Clients />
    </ProtectedRoute>
  }
/>
```

### 3.3 Authentification Frontend

**Hook:** `useAuth()` dans `frontend/src/hooks/useAuth.jsx`

**Fonctionnalités:**
- Vérification automatique au mount
- Login avec email/password
- Logout (clear cookie)
- Token stocké en httpOnly cookie (inaccessible via JS)
- User state dans Context API

### 3.4 Système de Permissions

**Fichier:** `frontend/src/constants/permissions.js`

**Modules définis (26):**
```javascript
export const MODULES = [
  { key: "dashboard", path: "/dashboard", label: "Tableau de bord", icon: "LayoutDashboard" },
  { key: "clients", path: "/clients", label: "Clients", icon: "Users" },
  { key: "produits", path: "/produits", label: "Produits", icon: "BookOpen" },
  // ... 23 autres modules
];
```

**Matrice de permissions:**
```javascript
export const PERMISSIONS = {
  dashboard: { super_admin: 1, directeur_general: 1, comptable: 1, ... },
  clients: { super_admin: 1, directeur_general: 1, comptable: 1, ... },
  // ...
};
```

**Fonction helper:**
```javascript
export function can(role, moduleKey) {
  return PERMISSIONS[moduleKey]?.[role] === 1;
}

export function visibleModulesFor(role) {
  return MODULES.filter((m) => can(role, m.key));
}
```

### 3.5 Sidebar Navigation

**Fichier:** `frontend/src/components/layout/Sidebar.jsx`

**Fonctionnement:**
- Utilise `visibleModulesFor(role)` pour filtrer les modules
- Icons Lucide React
- Responsive (mobile/desktop)
- Active state styling

### 3.6 Service Layer Pattern

**Exemple:** `frontend/src/services/clientsApi.js`

**Pattern:**
```javascript
import axios from "axios";
import API_BASE_URL from "../config/api";
const API = API_BASE_URL;

export async function listClients({ q, type_client, ville, actif, page, page_size } = {}) {
  const params = { page, page_size };
  if (q) params.q = q;
  // ...
  const r = await axios.get(`${API}/clients`, { params });
  return r.data;
}
```

**Services existants (25):**
- clientsApi.js
- produitsApi.js
- commandesApi.js
- facturesApi.js
- paiementsApi.js
- stockApi.js
- bonsLivraisonApi.js
- bonsRetourApi.js
- comptabiliteApi.js
- comptabiliteAvanceeService.js
- documentsAiApi.js
- analyticsService.js
- colisageService.js
- notificationsService.js
- logistiqueService.js
- fleetService.js
- logisticsCostsService.js
- multiChannelNotificationsService.js
- biAnalyticsService.js
- workflowApprovalsService.js
- fileStorageService.js
- backupService.js
- parametresApi.js
- utilisateursApi.js
- rechercheApi.js
- rapportsApi.js

---

## 4. SYSTÈME RBAC

### 4.1 Backend RBAC

**Fichier:** `backend/rbac_constants.py` (342 lignes)

**Rôles définis (8):**
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
}
```

**Hiérarchie des rôles:**
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
}
```

**Matrice de permissions (26 modules):**
```python
MODULE_PERMISSIONS = {
    "dashboard": {
        "super_admin": 2,
        "directeur_general": 2,
        "comptable": 1,
        # ...
    },
    "clients": {
        "super_admin": 2,
        "directeur_general": 2,
        "comptable": 1,
        "directeur_commercial": 2,
        # ...
    },
    # ... 24 autres modules
}
```

**Niveaux de permission:**
- 0 = denied
- 1 = read
- 2 = write
- 3 = admin (non utilisé actuellement)

**Helper functions:**
```python
def can_access(role: str, module: str, required_level: int = 1) -> bool
def can_read(role: str, module: str) -> bool
def can_write(role: str, module: str) -> bool
def can_admin(role: str, module: str) -> bool
def get_accessible_modules(role: str) -> list
def is_super_admin(role: str) -> bool
def is_directeur_general(role: str) -> bool
def is_financial_role(role: str) -> bool
```

### 4.2 Frontend RBAC

**Fichier:** `frontend/src/constants/permissions.js`

**Rôles définis (8):**
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
};
```

**Matrice de permissions (26 modules):**
- 1 = autorisé
- 0 = refusé

**Synchronisation:** Les permissions frontend sont synchronisées avec le backend RBAC.

---

## 5. MONGODB - COLLECTIONS EXISTANTES

### 5.1 Collections Identifiées

**Collections principales:**
1. `users` - Utilisateurs système
2. `clients` - Clients
3. `produits` - Produits/Livres
4. `commandes` - Commandes
5. `commande_lignes` - Lignes de commande
6. `factures` - Factures
7. `facture_lignes` - Lignes de facture
8. `paiements` - Paiements
9. `mouvements_stock` - Mouvements de stock
10. `bons_livraison` - Bons de livraison
11. `bons_retour` - Bons de retour
12. `ecritures_comptables` - Écritures comptables
13. `parametres` - Paramètres système
14. `notifications` - Notifications
15. `notification_preferences` - Préférences de notification
16. `documents_ai` - Documents AI
17. `email_templates` - Templates email
18. `email_logs` - Logs d'envoi d'emails
19. `colis` - Colis
20. `expeditions` - Expéditions
21. `logistique` - Logistique
22. `fleet_vehicles` - Véhicules de flotte
23. `logistics_costs` - Coûts logistiques
24. `approval_workflows` - Workflows d'approbation
25. `approval_steps` - Étapes d'approbation
26. `signatures_electroniques` - Signatures électroniques
27. `file_storage` - Stockage de fichiers
28. `backup_configs` - Configurations de backup
29. `backup_logs` - Logs de backup
30. `counters` - Compteurs auto-incrémentés
31. `refresh_tokens` - Tokens de rafraîchissement
32. `audit_logs` - Logs d'audit

### 5.2 Patterns de Collections

**Pattern référence auto-incrémentée:**
```python
async def next_xxx_reference(db: AsyncIOMotorDatabase) -> str:
    doc = await db.counters.find_one_and_update(
        {"_id": "xxx"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    return f"FABS-XXX-{seq:04d}"
```

**Pattern soft delete:**
```python
# Au lieu de DELETE physique
await db.collection.update_one(
    {"_id": id},
    {"$set": {"actif": False, "updated_at": _now_iso()}}
)
```

**Pattern timestamps:**
```python
{
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}
```

---

## 6. SYSTÈME DE NOTIFICATIONS

### 6.1 Backend Notifications

**Module:** `backend/notifications_module.py`

**Collections:**
- `notifications` - Notifications
- `notification_preferences` - Préférences utilisateur
- `email_templates` - Templates d'emails
- `email_logs` - Logs d'envoi

**Types de notifications:**
- info
- warning
- error
- success

**Catégories:**
- stock
- commande
- paiement
- livraison
- système

**Fonctionnalités:**
- Création de notifications
- Marquage comme lu
- Préférences par utilisateur
- Templates d'emails
- Logs d'envoi

### 6.2 Multi-Channel Notifications

**Module:** `backend/multi_channel_notifications_module.py`

**Canaux supportés:**
- Email
- SMS
- WhatsApp
- In-app

**Fonctionnalités:**
- Configuration des canaux
- Templates multi-canal
- Historique d'envoi
- Statuts de livraison

---

## 7. MODULE DOCUMENTAIRE

### 7.1 Documents AI

**Module:** `backend/documents_ai_module.py`

**Collection:** `documents_ai`

**Types de documents:**
- BON_LIVRAISON
- FACTURE
- COMMANDE
- LISTE_CLIENTS
- AUTRE

**Fonctionnalités:**
- Upload de PDFs
- Parsing automatique
- Extraction de données
- Détection automatique du type
- Export (PDF, WhatsApp)

### 7.2 File Storage

**Module:** `backend/file_storage_module.py`

**Collection:** `file_storage`

**Types de documents:**
- facture
- contrat
- bon_livraison
- bon_commande
- autre

**Fonctionnalités:**
- Upload de fichiers
- Stockage local ou S3/MinIO
- Métadonnées
- Association avec entités

---

## 8. WORKFLOW APPROVALS & SIGNATURES

### 8.1 Workflow Approvals

**Module:** `backend/workflow_approvals_module.py`

**Collections:**
- `approval_workflows` - Workflows d'approbation
- `approval_steps` - Étapes d'approbation
- `signatures_electroniques` - Signatures

**Types d'entités:**
- commande
- facture
- paiement
- mission
- achat

**Fonctionnalités:**
- Workflows multi-niveaux
- Approbateurs configurables
- Signatures électroniques
- Audit trail intégré

### 8.2 Signatures Électroniques

**Types de signature:**
- dessin
- texte
- image

**Validation:**
- Signature data stockée
- Date de signature
- Validité vérifiée

---

## 9. ANALYSE DES DÉPENDANCES

### 9.1 Backend Dependencies

**Fichier:** `backend/requirements.txt`

**Packages principaux:**
- fastapi==0.110.1
- uvicorn==0.25.0
- motor==3.3.1 (MongoDB async)
- pydantic>=2.6.4
- pyjwt>=2.10.1
- bcrypt==4.1.3
- redis>=5.0.0
- prometheus-fastapi-instrumentator>=7.0.0
- slowapi>=0.1.9
- boto3>=1.34.129 (S3)
- cryptography>=42.0.8
- pandas>=2.2.0
- numpy>=1.26.0

**Aucune dépendance conflictuelle identifiée** pour le module RH.

### 9.2 Frontend Dependencies

**Fichier:** `frontend/package.json`

**Packages principaux:**
- react@19.0.0
- react-dom@19.0.0
- react-router-dom@7.5.1
- axios@1.8.4
- tailwindcss@3.4.17
- lucide-react@0.507.0
- recharts@3.6.0
- react-hook-form@7.56.2
- zod@3.24.4
- @radix-ui/* (UI components)

**Aucune dépendance conflictuelle identifiée** pour le module RH.

---

## 10. IDENTIFICATION DES CONFLITS POTENTIELS

### 10.1 Conflits Identifiés

**AUCUN CONFLIT MAJEUR DÉTECTÉ**

L'architecture modulaire existante permet l'ajout du module RH sans risque de rupture.

### 10.2 Points d'Attention

**1. Collection `users` existante:**
- La collection `users` contient les utilisateurs système (authentification)
- Le module RH devra créer une collection séparée `employes` pour éviter les conflits
- Relation: employe.user_id → users.user_id (optionnel)

**2. Système RBAC:**
- Le module RH nécessitera l'ajout de permissions dans `rbac_constants.py`
- Ajout d'un nouveau rôle potentiel: "responsable_rh"
- Mise à jour de la matrice de permissions

**3. Frontend Sidebar:**
- Ajout du module RH dans `frontend/src/constants/permissions.js`
- Ajout de l'icône RH dans `frontend/src/components/layout/Sidebar.jsx`
- Mise à jour des routes dans `frontend/src/App.js`

**4. Dashboard:**
- Le module RH devra contribuer aux stats du dashboard
- Mise à jour de `backend/dashboard_data.py`

### 10.3 Risques Évalués

**Risque: FAIBLE**

**Justification:**
- Architecture modulaire bien établie
- Pattern router factory réutilisable
- RBAC extensible
- Système de notifications intégré
- Module documentaire existant
- Audit trail fonctionnel
- Tests existants

---

## 11. RECOMMANDATIONS

### 11.1 Recommandations Architecture

**1. Structure du module RH:**
- Suivre le pattern `build_rh_router(db, resolve_user)`
- Créer un fichier `backend/rh_module.py` unique ou modularisé
- Utiliser les mêmes patterns de validation (Pydantic)
- Implémenter soft delete systématique

**2. Collections MongoDB:**
- `employes` - Employés
- `departements` - Départements
- `fonctions` - Fonctions
- `categories_pro` - Catégories professionnelles
- `contrats` - Contrats
- `conges` - Congés
- `absences` - Absences
- `missions` - Missions
- `documents_rh` - Documents RH (ou utiliser file_storage)
- `signatures_rh` - Signatures RH (ou utiliser signatures_electroniques)
- `habilitations_erp` - Habilitations ERP
- `evaluations` - Évaluations
- `delegations` - Délégations & intérim

**3. Intégration RBAC:**
- Ajouter "responsable_rh" aux rôles dans `rbac_constants.py`
- Ajouter le module "rh" dans `MODULE_PERMISSIONS`
- Définir les permissions par rôle pour le module RH

**4. Intégration Notifications:**
- Utiliser le système de notifications existant
- Catégorie "rh" à ajouter
- Types: conge, absence, mission, contrat, evaluation

**5. Intégration Documentaire:**
- Utiliser `file_storage_module.py` pour les documents RH
- Type document: "rh_document"
- Sous-types: cni, contrat, cv, diplome, etc.

**6. Intégration Audit:**
- Utiliser `log_audit_event()` pour toutes les actions RH
- Resource types: employe, contrat, conge, absence, mission, evaluation

### 11.2 Recommandations Frontend

**1. Structure:**
- `frontend/src/pages/RHDashboard.jsx` - Tableau de bord RH
- `frontend/src/pages/Employes.jsx` - Gestion des employés
- `frontend/src/pages/Contrats.jsx` - Gestion des contrats
- `frontend/src/pages/Conges.jsx` - Gestion des congés
- `frontend/src/pages/Absences.jsx` - Gestion des absences
- `frontend/src/pages/MissionsRH.jsx` - Gestion des missions
- `frontend/src/pages/DocumentsRH.jsx` - Documents RH
- `frontend/src/pages/Evaluations.jsx` - Évaluations
- `frontend/src/pages/RapportsRH.jsx` - Rapports RH

**2. Services:**
- `frontend/src/services/rhApi.js` - API RH

**3. Permissions:**
- Ajouter module "rh" dans `frontend/src/constants/permissions.js`
- Définir la matrice de permissions RH

**4. Navigation:**
- Ajouter l'icône RH dans Sidebar (User ou Briefcase)
- Ajouter les routes dans App.js

---

## 12. CONCLUSION DE L'AUDIT

### 12.1 État Actuel

**Statut:** ERP FABS-CI est fonctionnel et opérationnel

**Qualité du code:**
- Architecture modulaire cohérente
- Patterns réutilisables établis
- Sécurité robuste
- Tests existants
- Documentation Swagger

**Maturité:**
- 24+ modules opérationnels
- Système RBAC mature
- Audit trail intégré
- Notifications fonctionnelles
- Module documentaire existant

### 12.2 Prêt pour Module RH

**OUI** - L'ERP est prêt pour l'ajout du module RH

**Conditions remplies:**
- ✅ Architecture modulaire
- ✅ Système RBAC extensible
- ✅ Audit trail fonctionnel
- ✅ Notifications intégrées
- ✅ Module documentaire existant
- ✅ Patterns établis
- ✅ Aucun conflit détecté

### 12.3 Prochaines Étapes

1. **Générer le rapport d'impact technique** (rapport séparé)
2. **Développer le module RH backend**
3. **Développer le module RH frontend**
4. **Intégrer avec les systèmes existants**
5. **Tests complets**
6. **Audit post-développement**

---

## 13. MÉTRIQUES D'AUDIT

**Fichiers analysés:** 50+  
**Modules backend:** 24+  
**Pages frontend:** 36  
**Services frontend:** 25  
**Collections MongoDB:** 32  
**Rôles RBAC:** 8  
**Modules permissions:** 26  
**Lignes de code backend:** ~15,000  
**Lignes de code frontend:** ~20,000

**Durée de l'audit:** ~2 heures  
**Statut:** COMPLET  
**Recommandation:** PROCÉDER AU DÉVELOPPEMENT

---

**Rapport généré automatiquement par Cascade AI**  
**ERP FABS-CI - ÉDITIONS FABS-CI**  
**Date: 1er Juin 2026**
