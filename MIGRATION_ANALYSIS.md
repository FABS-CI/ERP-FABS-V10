# Rapport d'Analyse de Migration : ERP FABS-CI vers Managed App

**Date d'Analyse**: 2026-06-19  
**État du Projet Actuel**: Unmanaged (Custom Stack)  
**Destination**: Managed App Runable  

---

## 1. ARCHITECTURE ACTUELLE

### Stack Technique
```
Frontend:    React 18 + Vite + Tailwind CSS + Shadcn/ui
Backend:     FastAPI (Python) + Gunicorn + PM2
Database:    MongoDB Atlas / MongoDB Local
Storage:     File system / Cloud storage
PDF:         ReportLab
Hosting:     Custom server (Debian)
Auth:        JWT + Roles/Permissions
```

### Infrastructure Actuelle
```
- MongoDB: Port 27017 (56 produits, multilingue)
- Backend: Port 8000 (FastAPI + Gunicorn)
- Frontend: Port 3000 (React Dev Server)
- PM2: Gestion des processus
```

---

## 2. INVENTORY COMPLET - FRONTEND

### Pages (64 pages)
```
1. Dashboard.jsx               - Tableau de bord principal
2. Login.jsx                   - Authentification
3. Utilisateurs.jsx            - Gestion des utilisateurs
4. Parametres.jsx              - Configuration système

VENTES & COMMANDES:
5. Commandes.jsx               - Liste commandes (avec pagination, filtre)
6. CommandeDetail.jsx          - Détail commande (lignes, PDF, enrichissement)
7. Factures.jsx                - Liste factures
8. FactureDetail.jsx           - Détail facture (lignes, PDF)
9. Proformas.jsx               - Devis/Proformas
10. ProformaDetail.jsx         - Détail proforma
11. BonsLivraison.jsx          - Bons de livraison
12. BonsRetour.jsx             - Bons de retour
13. Paiements.jsx              - Gestion paiements
14. PaiementDetail.jsx         - Détail paiement
15. EtatCompteClients.jsx      - État compte client

PRODUITS & STOCK:
16. Produits.jsx               - Catalogue produits (56 articles)
17. ProduitDetail.jsx          - Détail produit (avec matiere, niveau)
18. ProduitsInventaire.jsx     - Inventaire & stock
19. Stock.jsx                  - Gestion stock
20. CategoriesPro.jsx          - Catégories produits

CLIENTS:
21. Clients.jsx                - Base clients
22. ClientDetail.jsx           - Détail client (contacts, adresses, historique)
23. FournisseurDetail.jsx      - Détail fournisseur
24. Fournisseurs.jsx           - Base fournisseurs

LOGISTIQUE:
25. Logistique.jsx             - Module logistique
26. LogistiqueHub.jsx          - Hub logistique
27. Expeditions.jsx            - Gestion expéditions
28. LivraisonsDirectes.jsx     - Livraisons directes
29. LogisticsCosts.jsx         - Coûts logistiques
30. Incidents.jsx              - Gestion incidents
31. Colis.jsx                  - Suivi colis
32. OrdresColisage.jsx         - Ordres de colisage
33. OrdreColisageDetail.jsx    - Détail ordre colisage
34. HistoriqueEnvois.jsx       - Historique envois
35. Fleet.jsx                  - Gestion flotte

APPROVISIONNEMENT:
36. Approvisionnements.jsx     - Gestion approvisions
37. ApprovisionnementDetail.jsx - Détail approvisionnement

RH & PAIE:
38. Employes.jsx               - Gestion employés
39. Paie.jsx                   - Gestion paie
40. RHDashboard.jsx            - Dashboard RH
41. Absences.jsx               - Gestion absences
42. Conges.jsx                 - Gestion congés
43. Contrats.jsx               - Gestion contrats
44. Departements.jsx           - Départements
45. Evaluations.jsx            - Évaluations
46. Fonctions.jsx              - Fonctions/métiers
47. RapportsRH.jsx             - Rapports RH

COMPTABILITÉ:
48. Comptabilite.jsx           - Module comptabilité
49. ComptabiliteAvancee.jsx    - Comptabilité avancée

DOCUMENTS & RAPPORTS:
50. Documents.jsx              - Gestion documents
51. DocumentDetail.jsx         - Détail document
52. DocumentsImpression.jsx    - Modèles impression
53. Rapports.jsx               - Rapports divers
54. AnalyticsReports.jsx       - Rapports analytiques
55. BIAnalytics.jsx            - Business Intelligence

NOTIFICATIONS:
56. Notifications.jsx          - Notifications
57. MultiChannelNotifications.jsx - Notifications multi-canal

INTÉGRATIONS:
58. FNE.jsx                    - Module FNE (DGI)
59. FNEInvoiceDetail.jsx       - Détail facture FNE
60. FNEInvoiceNew.jsx          - Nouvelle facture FNE
61. FNELogs.jsx                - Logs FNE
62. FNESettings.jsx            - Config FNE

AUTRES:
63. FileStorage.jsx            - Stockage fichiers
64. WorkflowApprovals.jsx      - Workflows d'approbation
65. Backup.jsx                 - Sauvegarde/Restore
66. Missions.jsx               - Gestion missions
67. ModulePlaceholder.jsx      - Placeholder template
68. NotFound.jsx               - Page 404
```

### Composants Réutilisables
```
- LignesTable.jsx              - Affichage lignes (Niveau + Matière ✅)
- IdleWarningModal.jsx         - Modal inactivité
- Logo.jsx                     - Branding
- ProtectedRoute.jsx           - Authentification routes
- UI Components (Shadcn)       - 40+ composants UI standard
```

### Fonctionnalités Frontend Clés
```
✅ Authentification JWT
✅ Rôles & Permissions (admin, manager, employee)
✅ Tableaux paginés/filtrés/triés
✅ Formulaires réactifs
✅ Génération/Aperçu PDF
✅ Export données (CSV, Excel)
✅ Notifications temps réel
✅ Recherche multi-champs
✅ Dark mode / Light mode
✅ Responsive design (Mobile + Desktop)
✅ Confirmation avant actions
✅ Validation formulaires côté client
✅ Affichage Niveau + Matière dans commandes/factures
```

---

## 3. INVENTORY COMPLET - BACKEND

### Modules API (36 modules)
```
VENTES & COMMANDES:
1. commandes_module.py          - API commandes (GET, POST, PUT, DELETE, PDF)
2. factures_module.py           - API factures (génération, PDF)
3. proformas_module.py          - API proformas/devis
4. bons_livraison_module.py     - API bons livraison
5. bons_retour_module.py        - API bons retour

PRODUITS & STOCK:
6. products_module.py           - API produits (56 articles, matiere, niveau)
7. stock_module.py              - API gestion stock

PAIEMENTS:
8. paiements_module.py          - API paiements
9. comptabilite_module.py       - API comptabilité basique
10. comptabilite_avancee_module.py - API comptabilité avancée

CLIENTS & FOURNISSEURS:
11. clients_module.py           - API clients (CRUD + détails)
12. fournisseurs_module.py      - API fournisseurs

LOGISTIQUE:
13. logistique_module.py        - API logistique
14. logistics_costs_module.py    - API coûts logistique
15. colisage_module.py          - API colisage (complexe, 105 KB)
16. fleet_module.py             - API gestion flotte

APPROVISIONNEMENT:
17. approvisionnement_module.py - API approvisionnement

RH & PAIE:
18. rh_module.py                - API RH
19. paie_module.py              - API gestion paie

NOTIFICATIONS:
20. notifications_module.py     - API notifications
21. multi_channel_notifications_module.py - Notifications multi-canal
22. notification_service.py     - Service notifications

DOCUMENTS:
23. document_settings_module.py - Configuration documents
24. document_templates.py       - Templates PDF
25. documents_ai_module.py      - Documents + IA
26. compte_client_pdf_generator.py - Générateur PDF état compte

RAPPORTS:
27. rapports_module.py          - API rapports
28. analytics_module.py         - API analytics
29. analytics_service.py        - Service analytics
30. bi_analytics_module.py      - Business Intelligence

INTÉGRATIONS:
31. fne_module.py               - Module FNE (Côte d'Ivoire)
32. fne_dgi_service.py          - Service intégration DGI

AUTRES:
33. file_storage_module.py      - Stockage fichiers
34. administration_module.py    - Administration système
35. workflow_approvals_module.py - Workflows d'approbation
36. twofa_module.py             - Two-factor authentication
37. backup_module.py            - Backup/Restore

UTILITAIRES:
38. pdf_generator.py            - Générateur PDF central (enrich_lignes_for_pdf ✅)
39. create_indexes.py           - Création indexes MongoDB
40. create_super_admin.py       - Script création super admin
41. dashboard_data.py           - Données dashboard
42. recherche_module.py         - Module recherche
```

### Endpoints API Principaux
```
COMMANDES:
GET     /api/commandes                    - Liste (paginated)
GET     /api/commandes/{id}               - Détail + enrichissement Niveau/Matière
POST    /api/commandes                    - Créer
PUT     /api/commandes/{id}               - Modifier
DELETE  /api/commandes/{id}               - Supprimer
GET     /api/commandes/{id}/pdf           - Générer PDF
GET     /api/commandes/{id}/preview-pdf   - Aperçu PDF
GET     /api/commandes/{id}/print         - Imprimer

FACTURES:
GET     /api/factures                     - Liste
GET     /api/factures/{id}                - Détail
POST    /api/factures                     - Créer
GET     /api/factures/{id}/pdf            - Générer PDF
POST    /api/factures/{id}/email          - Envoyer par email

PRODUITS:
GET     /api/produits                     - Liste (56 articles, pagination 20+20+16)
GET     /api/produits/{id}                - Détail (matiere, niveau_scolaire)
POST    /api/produits                     - Créer
PUT     /api/produits/{id}                - Modifier
DELETE  /api/produits/{id}                - Supprimer
GET     /api/produits/search              - Recherche multi-champs

CLIENTS:
GET     /api/clients                      - Liste
GET     /api/clients/{id}                 - Détail complet
POST    /api/clients                      - Créer
PUT     /api/clients/{id}                 - Modifier
DELETE  /api/clients/{id}                 - Supprimer

... (50+ autres endpoints)
```

### Schémas de Données Clés

#### LigneCommandeOut (Enrichissement ✅)
```python
class LigneCommandeOut(BaseModel):
    ligne_id: str
    commande_id: str
    produit_id: str
    produit_reference: Optional[str]           # Code article
    produit_titre: Optional[str]               # Désignation
    produit_matiere: Optional[str]             # ← MATIÈRE ✅
    produit_niveau_scolaire: Optional[str]     # ← NIVEAU ✅
    produit_cycle: Optional[str]               # Groupement (Primaire, 1er Cycle)
    produit_categorie: Optional[str]
    quantite: int
    prix_unitaire: float
    remise_ligne: float
    montant_ligne: float
```

#### Commande
```python
class Commande:
    commande_id: str
    reference: str
    date_commande: datetime
    client_id: str
    statut: str                # nouveau, confirmée, expediée, livree
    lignes: List[LigneCommande]
    montant_ht: float
    montant_ttc: float
    remise_globale: float
    notes: Optional[str]
    createdAt: datetime
    updatedAt: datetime
```

#### Produit
```python
class Produit:
    _id: ObjectId
    produit_id: str
    reference: str             # Code FABS-CI
    titre: str
    description: Optional[str]
    matiere: str              # ← FRANÇAIS, ANGLAIS, etc.
    niveau_scolaire: str      # ← CP1, CP2, CE1, 6ème, etc.
    categorie: str            # primaire, premier_cycle, deuxieme_cycle
    cycle: str                # Regroupement pour PDF
    prix_unitaire: float
    quantite_stock: int
    image_url: Optional[str]
    createdAt: datetime
```

---

## 4. INVENTORY - BASE DE DONNÉES

### Collections MongoDB

```
1. commandes           - Orders with status, dates, client info
2. commande_lignes    - Order lines (produit_id, qty, price)
3. factures           - Invoices (linked to commandes)
4. facture_lignes     - Invoice lines
5. bons_livraison     - Delivery notes
6. bons_retour        - Return notes
7. produits           - Products catalog (56 items with matiere, niveau)
8. clients            - Customer database
9. client_adresses    - Customer addresses
10. client_contacts   - Customer contacts
11. fournisseurs      - Supplier database
12. commande_fournisseurs - Supplier orders
13. stock             - Stock/inventory
14. paiements         - Payments
15. factures_fne      - FNE invoices (Côte d'Ivoire integration)
16. employes          - Employee records
17. paie              - Payroll
18. absences          - Absences
19. conges            - Leave/vacation
20. contrats          - Contracts
21. departements      - Departments
22. evaluations       - Performance evaluations
23. fonctions         - Job functions/roles
24. logistique        - Logistics data
25. colis             - Parcels/shipments
26. ordres_colisage   - Packing orders
27. expeditions       - Shipments
28. incidents         - Incident tracking
29. livraisons_directes - Direct deliveries
30. approvisionnements - Supplies/replenishment
31. notifications     - User notifications
32. utilisateurs      - User accounts (with roles, permissions)
33. audit_log         - Audit trail
34. document_settings - Document configuration
35. parameters        - System parameters
36. backup_jobs       - Backup history
37. workflows         - Workflow definitions
38. approvals         - Approval requests
39. fleet             - Vehicle fleet
40. missions          - Missions/tasks
41. files             - File storage metadata
... (20+ other collections)
```

### Collections Clés pour Migration

**Collection: produits** (56 documents)
```json
{
  "_id": ObjectId("..."),
  "produit_id": "PROD-001",
  "reference": "FABS-CI001",
  "titre": "Cahier D'Exercices CP1",
  "description": "...",
  "matiere": "Français",
  "niveau_scolaire": "CP1",
  "categorie": "primaire",
  "cycle": "Primaire",
  "prix_unitaire": 2500,
  "quantite_stock": 150,
  "image_url": "...",
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

**Collection: commandes** (hundreds of records)
```json
{
  "_id": ObjectId("..."),
  "commande_id": "CMN-20250101001",
  "reference": "CMN-2025-001",
  "date_commande": ISODate("..."),
  "client_id": "CLI-001",
  "statut": "confirmée",
  "montant_ht": 125000,
  "montant_ttc": 150000,
  "remise_globale": 5,
  "notes": "...",
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

**Collection: commande_lignes** (thousands of records)
```json
{
  "_id": ObjectId("..."),
  "ligne_id": "LGN-001",
  "commande_id": "CMN-20250101001",
  "produit_id": "PROD-001",
  "quantite": 100,
  "prix_unitaire": 2500,
  "remise_ligne": 0,
  "montant_ligne": 250000,
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

### Indexes
```
- produits: {reference: 1}, {matiere: 1}, {niveau_scolaire: 1}
- commandes: {client_id: 1}, {statut: 1}, {date_commande: -1}
- commande_lignes: {commande_id: 1}, {produit_id: 1}
- clients: {email: 1}, {telephone: 1}
- utilisateurs: {username: 1}, {email: 1}
... (20+ indexes)
```

---

## 5. AUTHENTIFICATION & RÔLES

### Rôles Système
```
1. admin            - Accès complet à tout
2. manager          - Gestion commandes, factures, clients, stock
3. employee         - Lecture seule + actions limitées
4. accountant       - Accès comptabilité + rapports
5. logistic         - Gestion logistique + expéditions
6. rh               - Gestion RH + paie
7. customer_support - Gestion clients + tickets
8. viewer           - Lecture seule (dashboard, rapports)
```

### Permissions
```
- create_order, read_order, update_order, delete_order
- create_invoice, read_invoice, generate_invoice_pdf
- manage_products, manage_stock
- manage_clients, manage_suppliers
- manage_users, manage_roles
- access_accounting, access_rh, access_logistics
- export_data, generate_reports
- manage_system_settings
... (50+ permissions)
```

### Authentification
```
- JWT Token (Bearer)
- Refresh tokens
- 2FA support (twofa_module.py)
- Role-based access control (RBAC)
- Permission-based access control (PBAC)
```

---

## 6. FONCTIONNALITÉS MÉTIER PRINCIPALES

### Module Ventes
```
✅ Gestion complète des commandes
✅ Génération factures (avec Niveau + Matière)
✅ Bons de livraison
✅ Bons de retour
✅ Gestion paiements
✅ État de compte client
✅ Proformas/Devis
✅ PDF generation (ReportLab)
✅ Email integration
```

### Module Produits
```
✅ Catalogue 56 produits
✅ Matière (Français, Anglais, Mathématiques, etc.)
✅ Niveau Scolaire (CP1-CP2, CE1-CE2, CM1-CM2, 6ème-Terminale)
✅ Catégories (Primaire, 1er Cycle, 2ème Cycle)
✅ Gestion stock
✅ Pricing
✅ Images produits
```

### Module Clients
```
✅ Base client complète
✅ Adresses multiples par client
✅ Contacts multiples
✅ Historique commandes
✅ État compte détaillé
✅ Crédits/Débits
✅ Segmentation client
```

### Module Logistique
```
✅ Gestion expéditions
✅ Suivi colis
✅ Ordres de colisage
✅ Flotte véhicules
✅ Coûts logistiques
✅ Incidents/problèmes
✅ Livraisons directes
```

### Module RH
```
✅ Gestion employés
✅ Paie
✅ Absences
✅ Congés
✅ Contrats
✅ Évaluations
✅ Départements
✅ Fonctions
```

### Module Comptabilité
```
✅ Comptabilité basique
✅ Comptabilité avancée
✅ Factures FNE (DGI Côte d'Ivoire)
✅ Rapports comptables
```

### Module Rapports & Analytics
```
✅ Rapports ventes
✅ Rapports stock
✅ Rapports RH
✅ Business Intelligence
✅ Graphiques analytiques
✅ Export données
```

### Module Notifications
```
✅ Notifications système
✅ Notifications multi-canal (email, SMS, in-app)
✅ Webhooks
✅ Alertes
```

### Intégrations
```
✅ FNE/DGI (Côte d'Ivoire tax system)
✅ Email (SMTP)
✅ File storage
✅ Backup/Restore
✅ Audit logging
```

---

## 7. CONSIDÉRATIONS TECHNIQUES CRITIQUES

### Comportements Spécifiques à Préserver

1. **Enrichissement Niveau & Matière** ✅
   - Backend: `_get_commande_with_lignes()` enrichit chaque ligne
   - PDF: `enrich_lignes_for_pdf()` peuple matiere + niveau
   - Frontend: `LignesTable.jsx` affiche les deux champs
   - **ACTION**: Assurer que Managed App preserve cette logique

2. **Génération PDF Complexe**
   - ReportLab for PDF generation
   - Groupement par cycle (Primaire, 1er Cycle, 2ème Cycle)
   - Calcul sous-totaux par cycle
   - Headers avec Niveau + Matière
   - **ACTION**: Vérifier compatibilité PDF generation dans Managed App

3. **Pagination Produits**
   - API retourne 56 produits sur 3 pages (20+20+16)
   - **ACTION**: Assurer pagination personnalisée compatible

4. **FNE/DGI Integration**
   - Intégration spécifique Côte d'Ivoire
   - Factures FNE avec numéros de série
   - Format export spécifique
   - **ACTION**: Préserver tous les paramètres FNE

5. **Multi-Langue/Multi-Devise**
   - Devise: FCFA (Franc CFA)
   - Langue: Français principal
   - **ACTION**: Assurer support multi-devise/langue

6. **Complex Colisage Module**
   - 105 KB de logique métier
   - Ordre de colisage → Picking → Packing
   - **ACTION**: Tester exhaustivement lors de migration

---

## 8. DÉCISIONS DE MIGRATION REQUISES

### Points de Compatibilité à Vérifier

1. **PDF Generation**
   - [ ] ReportLab compatible avec Managed App?
   - [ ] Peut-on générer PDF côté serveur?
   - [ ] Images produits: où stockées?

2. **Base de Données**
   - [ ] MongoDB cloud compatible?
   - [ ] Collections peuvent migrer 1-to-1?
   - [ ] Indexes préservés?

3. **Authentication**
   - [ ] JWT compatible avec Managed App?
   - [ ] Rôles/permissions peuvent se mapper?
   - [ ] 2FA compatible?

4. **File Storage**
   - [ ] Où stocker images produits, documents, fichiers?
   - [ ] API file upload/download compatible?

5. **Email Integration**
   - [ ] SMTP integration compatible?
   - [ ] Templates email préservés?

6. **Custom Business Logic**
   - [ ] Workflows d'approbation?
   - [ ] Calculs comptabilité?
   - [ ] Logique colisage?

---

## 9. RISQUES & LIMITATIONS IDENTIFIÉES

### Risques Élevés
```
🔴 PDF Generation: ReportLab peut nécessiter refonte
🔴 Colisage Module: Logique très spécifique, 105 KB de code
🔴 FNE/DGI: Intégration très spécifique Côte d'Ivoire
🔴 Custom Workflows: Pas standard, peut nécessiter refonte
```

### Risques Moyens
```
🟡 File Storage: Dépend de solution Managed App
🟡 Email Integration: Dépend de service disponible
🟡 Analytics: Peut nécessiter réimplémentation
🟡 Audit Logging: Logique custom, peut nécessiter adaptation
```

### Risques Bas
```
🟢 CRUD Operations: Straightforward migration
🟢 Authentication: Standard RBAC
🟢 UI/UX: React/Tailwind compatible
🟢 Produits/Clients/Stock: Standard data entities
```

---

## 10. CHECKLIST DE VÉRIFICATION

### Avant Migration
- [ ] Backup complet du projet actuel
- [ ] Export base de données MongoDB
- [ ] Documentation des rôles/permissions actuels
- [ ] Liste des endpoints API actifs
- [ ] Configuration des paramètres système
- [ ] Variables d'environnement documentées

### Phase 1: Setup Managed App
- [ ] Créer nouvel app "ERP FABS CI"
- [ ] Configurer MongoDB connection
- [ ] Setup authentication system
- [ ] Configurer variables d'environnement

### Phase 2: Migration Base de Données
- [ ] Analyser structure collections actuelles
- [ ] Créer schémas compatibles Managed App
- [ ] Import données
- [ ] Vérifier intégrité données
- [ ] Valider 56 produits avec matiere/niveau

### Phase 3: Migration Frontend
- [ ] Reproduire 64 pages
- [ ] Reproduire composants réutilisables
- [ ] Tester navigation
- [ ] Tester formulaires
- [ ] Tester responsive design

### Phase 4: Migration Backend/API
- [ ] 36 modules → endpoints Managed App
- [ ] Tester chaque endpoint
- [ ] Vérifier enrichissement Niveau/Matière
- [ ] Tester PDF generation
- [ ] Vérifier paginatio/filtres

### Phase 5: Testing & Validation
- [ ] Test complet commande → facture → PDF
- [ ] Test tous les rôles/permissions
- [ ] Test export données
- [ ] Test notifications
- [ ] Test FNE/DGI integration
- [ ] Performance testing

### Phase 6: Déploiement
- [ ] Backup base actuelle
- [ ] Migration données
- [ ] Redirection URLs
- [ ] Monitoring logs
- [ ] Support utilisateurs

---

## 11. RESSOURCES REQUISES

### Code à Migrer
- ~64 fichiers JSX (frontend)
- ~40 fichiers Python (backend)
- ~50 collections MongoDB
- Configuration documents (templates PDF)

### Données à Migrer
- 56 produits avec matiere, niveau, prix
- Milliers de lignes (commandes, factures)
- Base clients (centaines)
- Base employés
- Tous les paramètres système

### Services à Reconfigurer
- MongoDB Atlas connection
- Email SMTP
- File storage
- PDF generation
- FNE/DGI API

---

## STATUT: PRÊT POUR ANALYSE PAR L'UTILISATEUR

**Attendant validation avant migration...**

