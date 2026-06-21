# 🚀 Démarrage rapide — ERP FABS-CI

## Lancer l'ERP (tout-en-un)

Après avoir cloné le projet, une seule commande suffit :

```bash
./start.sh
```

Ce script fait **tout automatiquement** :

1. ✅ Démarre **MongoDB** (port 27017) et **Redis** (port 6379)
2. ✅ Crée les fichiers `.env` (backend + frontend) s'ils manquent
3. ✅ Installe les dépendances **backend** (venv Python) et **frontend** (npm)
4. ✅ Lance le **backend** (port 8001) et le **frontend** (port 3000)
5. ✅ **Importe les données** si la base est vide :
   - 👥 **1014 clients** (depuis `backend/data_import/clients.json`)
   - 📚 **56 produits** (depuis `backend/data_import/articles.json`)
   - 🔐 **9 utilisateurs** + rôles (gestion idempotente, pas de doublon)

> Le premier lancement prend quelques minutes (installation des dépendances + compilation du frontend ~30-45s).

## Forcer un réimport complet des données

Pour repartir de zéro avec les données du repo (purge + réimport) :

```bash
./start.sh --reimport
```

## Accès

- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8001/api/

## Comptes de connexion

| Rôle | Email | Mot de passe |
|---|---|---|
| Super Admin | pissken@editionsfabsci.com | `Admin@2024` |
| Directeur Général | ali.mamin@editionsfabsci.com | `DG@2024` |
| Directeur Commercial | detymichel@editionsfabsci.com | `Fabs@2025` |
| Comptable | natachakoffi@editionsfabsci.com | `Fabs@2025` |
| Gestionnaire Stock | niangorangeorgie@editionsfabsci.com | `Fabs@2025` |
| Resp. Magasinier | joachin@editionsfabsci.com | `Fabs@2025` |
| Service Logistique | yakeben@editionsfabsci.com | `Fabs@2025` |
| Secrétariat | dadjelarissa@editionsfabsci.com | `Fabs@2025` |
| Assistante | amenan@editionsfabsci.com | `Fabs@2025` |

## Prérequis (installés une seule fois sur la machine)

- **MongoDB 7** (`mongod` dans le PATH)
- **Redis** (`redis-server` dans le PATH)
- **Python 3** + venv
- **Node.js** + npm
- **tmux** (recommandé, pour faire tourner les services en arrière-plan)
