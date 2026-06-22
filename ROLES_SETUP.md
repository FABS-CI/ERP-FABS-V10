# ERP FABS-CI — Configuration des Rôles

## 9 Rôles Configurés

| Rôle | Email | Mot de passe | Accès |
|------|-------|--------------|-------|
| Super Admin | `pissken@editionsfabsci.com` | `Admin@2024` | **Tous les modules** |
| Directeur Général | `directeur@editionsfabsci.com` | `Directeur@2025` | Dashboard, Paiements, RH, Notifications |
| Comptable | `comptable@editionsfabsci.com` | `Compta@2025` | Rapports, Comptabilité, Factures, Clients (L), Commandes (L), RH |
| Directeur Commercial | `commercial@editionsfabsci.com` | `Commercial@2025` | Clients, Commandes, Factures, Livraisons, Retours, Produits, Inventaire |
| Gestionnaire Stock | `gestionnaire@editionsfabsci.com` | `Gestion@2025` | Stock, Produits, Approvisionnements, Fournisseurs, Retours, Notifications |
| Responsable Magasinier | `joachin@editionsfabsci.com` | `Fabs@2025` | Colisage, Colis, Commandes (L), Stock (L), Dashboard, Notifications |
| Secrétariat | Test créé | Test | Clients, Commandes, Proformas, Produits, RH (lecture) |
| Assistante | Test créé | Test | Clients, Commandes, Proformas, Produits (lecture) |
| Service Logistique | Test créé | Test | Livraisons, Colis, Expéditions, Incidents, Hub Logistique, Fleet, Coûts Logistiques |

## Matrice des Permissions

Source: `/frontend/src/constants/permissions.js`

**Légende:**
- `1` = Accès autorisé
- `0` = Accès refusé
- `L` = Lecture seule
- `E/L` = Écriture & Lecture

### Modules Financiers (Comptable)
- **Comptabilité**: 1
- **Comptabilité Avancée**: 1
- **FNE**: 1
- **Rapports**: 1
- **Facturesï**: 1
- **Paiements**: 1

### Modules Commerciaux (Directeur Commercial)
- **Clients**: 1
- **Commandes**: 1
- **Factures**: 1 (L)
- **Livraisons**: 1
- **Retours**: 1
- **Produits Inventaire**: 1
- **Produits**: 1

### Modules RH (Directeur Général)
- **Tous les modules RH**: 1
- **Paiements**: 1
- **Dashboard**: 1

### Modules Stock (Gestionnaire Stock + Responsable Magasinier)

**Gestionnaire Stock:**
- Stock: 1 (E/L)
- Produits: 1 (E/L)
- Approvisionnements: 1
- Fournisseurs: 1
- Retours: 1
- Inventaire: 1
- Notifications: 1

**Responsable Magasinier:**
- Colisage: 1 (E/L)
- Colis: 1 (E/L)
- Stock: 1 (L, lecture seule)
- Commandes: 1 (L, lecture seule)
- Dashboard: 1
- Notifications: 1

## Tests Réalisés [date: 2026-06-22]

✅ **Comptable** — Login + Accès Commandes (200)
✅ **Directeur Commercial** — Login + Accès Commandes (200)
✅ **Directeur Général** — Login + Blocage Commandes (403, attendu)

## Backend RBAC

Fichier: `/backend/rbac_constants.py`

Chaque module a des `READ_ROLES` et `WRITE_ROLES` :
- `super_admin` : dans tous les rôles
- `directeur_general` : paiements, RH
- `comptable` : compta, rapports, factures
- `directeur_commercial` : clients, commandes, livraisons
- `gestionnaire_stock` : stock, produits, approvisionnements, fournisseurs, retours
- `responsable_magasinier` : colisage (E/L), colis, stock (L)
- Autres : accès restreints via rôles

## Frontend Permissions

Fichier: `/frontend/src/constants/permissions.js`

Matrice `PERMISSIONS[module_key][role_name]` = 1|0

Source de vérité ERP FABS-CI V10 (Matrice validée 2026-06-17).

