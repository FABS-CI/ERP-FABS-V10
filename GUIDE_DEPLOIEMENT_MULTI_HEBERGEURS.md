# Guide de Déploiement Multi-Hébergeurs - ERP FABS-CI V7

Ce guide fournit toutes les informations nécessaires pour déployer l'ERP sur n'importe quel hébergeur (Vercel, Railway, Render, Heroku, etc.).

---

## Architecture du Projet

L'ERP FABS-CI V7 est composé de 4 services:

1. **Frontend** - React + Nginx (port 80)
2. **Backend** - FastAPI + Python (port 8001)
3. **MongoDB** - Base de données (port 27017)
4. **Redis** - Cache (port 6379)

---

## 1. Déploiement Frontend sur Vercel

### Prérequis
- Compte Vercel (https://vercel.com)
- Repository Git (GitHub, GitLab, Bitbucket)

### Étapes de déploiement

#### 1.1 Préparer le frontend pour Vercel

Créer un fichier `vercel.json` à la racine du projet:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    },
    {
      "src": "/api/(.*)",
      "dest": "https://VOTRE_BACKEND_URL/$1"
    }
  ]
}
```

#### 1.2 Déployer sur Vercel

1. Connectez-vous sur https://vercel.com
2. Cliquez sur "Add New Project"
3. Importez votre repository Git
4. Configurez les paramètres:
   - **Framework Preset:** Create React App
   - **Root Directory:** `frontend`
   - **Build Command:** `yarn build`
   - **Output Directory:** `build`
5. Ajoutez les variables d'environnement:
   - `REACT_APP_API_URL=https://VOTRE_BACKEND_URL`
6. Cliquez sur "Deploy"

#### 1.3 Configuration du proxy API

Dans `frontend/src/config/api.js`, modifiez:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://VOTRE_BACKEND_URL';
```

---

## 2. Déploiement Backend sur Railway/Render/Heroku

### Option A: Railway

#### Prérequis
- Compte Railway (https://railway.app)
- Repository Git

#### Étapes

1. Connectez-vous sur https://railway.app
2. Cliquez sur "New Project"
3. "Deploy from GitHub repo"
4. Sélectionnez votre repository
5. Configurez le service:
   - **Root Directory:** `backend`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.11
6. Ajoutez les variables d'environnement (voir section 5)
7. Cliquez sur "Deploy"

### Option B: Render

#### Prérequis
- Compte Render (https://render.com)
- Repository Git

#### Étapes

1. Connectez-vous sur https://render.com
2. Cliquez sur "New +"
3. "Web Service"
4. Connectez votre repository Git
5. Configurez:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.11
6. Ajoutez les variables d'environnement (voir section 5)
7. Cliquez sur "Create Web Service"

### Option C: Heroku

#### Prérequis
- Compte Heroku (https://heroku.com)
- Heroku CLI installé

#### Étapes

1. Connectez-vous sur https://heroku.com
2. Créez une nouvelle app:
   ```bash
   heroku create votre-app-name
   ```
3. Configurez le buildpack:
   ```bash
   heroku buildpacks:set heroku/python
   ```
4. Déployez:
   ```bash
   git push heroku main
   ```
5. Configurez les variables d'environnement:
   ```bash
   heroku config:set ENVIRONMENT=production
   heroku config:set MONGO_URL=votre_mongo_url
   heroku config:set REDIS_URL=votre_redis_url
   heroku config:set JWT_SECRET=votre_secret
   heroku config:set CORS_ORIGINS=https://votre-frontend-url.vercel.app
   ```

---

## 3. Déploiement MongoDB sur MongoDB Atlas

### Prérequis
- Compte MongoDB Atlas (https://www.mongodb.com/cloud/atlas)

### Étapes

1. Connectez-vous sur https://www.mongodb.com/cloud/atlas
2. Cliquez sur "Build a Database"
3. Choisissez "Free" (M0)
4. Sélectionnez la région la plus proche de votre backend
5. Créez un cluster
6. Configurez l'accès réseau:
   - "Network Access" → "Add IP Address"
   - Choisissez "Allow Access from Anywhere" (0.0.0.0/0)
7. Configurez l'accès base de données:
   - "Database Access" → "Create Database User"
   - Username: `admin`
   - Password: (générez un mot de passe fort)
8. Obtenez la connection string:
   - "Connect" → "Connect your application"
   - Driver: Python
   - Copy the connection string

**Format de la connection string:**
```
mongodb+srv://admin:MOT_DE_PASSE@cluster0.xxxxx.mongodb.net/fabsci_erp?retryWrites=true&w=majority
```

---

## 4. Déploiement Redis sur Redis Cloud

### Option A: Redis Cloud (Officiel)

#### Prérequis
- Compte Redis Cloud (https://redis.com/try-free/)

#### Étapes

1. Connectez-vous sur https://redis.com/try-free/
2. Cliquez sur "Create Database"
3. Choisissez "Free" (30MB)
4. Sélectionnez la région la plus proche de votre backend
5. Configurez la sécurité:
   - Décochez "TLS" si nécessaire
   - Notez le mot de passe généré
6. Obtenez la connection string:
   - Format: `redis://:MOT_DE_PASSE@HOST:PORT`

### Option B: Upstash (Alternative gratuite)

#### Prérequis
- Compte Upstash (https://upstash.com)

#### Étapes

1. Connectez-vous sur https://upstash.com
2. Cliquez sur "Create Database"
3. Choisissez la région
4. Copiez la connection string:
   - Format: `redis://default:MOT_DE_PASSE@HOST:PORT`

---

## 5. Configuration des Variables d'Environnement

### Variables obligatoires pour tous les hébergeurs

```bash
# Environnement
ENVIRONMENT=production

# MongoDB
MONGO_URL=mongodb+srv://admin:MOT_DE_PASSE@cluster0.xxxxx.mongodb.net/fabsci_erp?retryWrites=true&w=majority
DB_NAME=fabsci_erp

# Redis
REDIS_URL=redis://:MOT_DE_PASSE@HOST:PORT

# JWT
JWT_SECRET=GENERER_AVEC_PYTHON_SECRETS
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRY_DAYS=7

# CORS
CORS_ORIGINS=https://votre-frontend-url.vercel.app

# Logging
LOG_LEVEL=INFO

# Utilisateurs par défaut
SUPER_ADMIN_EMAIL=pissken@editionsfabsci.com
SUPER_ADMIN_PASSWORD=MOT_DE_PASSE_FORT
DG_EMAIL=ali.mamin@editionsfabsci.com
DG_PASSWORD=MOT_DE_PASSE_FORT
```

### Générer JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Critères mots de passe

Minimum 8 caractères:
- Au moins une majuscule
- Au moins une minuscule
- Au moins un chiffre
- Au moins un caractère spécial (@$!%*?&)

---

## 6. Configuration du Frontend pour les Hébergeurs

### Pour Vercel

Dans `frontend/.env.production`:

```bash
REACT_APP_API_URL=https://votre-backend-url.railway.app
```

### Pour Netlify

Dans `frontend/.env.production`:

```bash
REACT_APP_API_URL=https://votre-backend-url.render.com
```

---

## 7. Seed des Données de Démonstration

Après déploiement, exécutez dans le terminal du backend:

```bash
python seed_demo_data.py
```

Cela créera:
- 4 utilisateurs (super_admin, dg, commercial, comptable)
- 3 clients
- 5 produits
- 2 commandes

---

## 8. Vérification et Tests

### Vérifier les services

- **Frontend:** `https://votre-frontend-url.vercel.app`
- **Backend:** `https://votre-backend-url.railway.app/api/health`
- **Documentation API:** `https://votre-backend-url.railway.app/api/docs`

### Se connecter

- Email: `pissken@editionsfabsci.com`
- Password: celui configuré dans SUPER_ADMIN_PASSWORD

### Tests fonctionnels

1. Créer un client
2. Créer un produit
3. Créer une commande
4. Valider la commande
5. Créer un bon de livraison
6. Enregistrer un paiement

---

## 9. Exemple de Configuration Complète

### Exemple avec Vercel + Railway + MongoDB Atlas + Redis Cloud

**Frontend (Vercel):**
- URL: `https://erp-fabs-ci.vercel.app`
- Variables: `REACT_APP_API_URL=https://erp-fabs-ci-backend.railway.app`

**Backend (Railway):**
- URL: `https://erp-fabs-ci-backend.railway.app`
- Variables:
  - `MONGO_URL=mongodb+srv://admin:password@cluster0.xxxxx.mongodb.net/fabsci_erp`
  - `REDIS_URL=redis://:password@redis-xxxxx.c1.us-east1-2.gcp.cloud.redislabs.com:6379`
  - `JWT_SECRET=xyz123...`
  - `CORS_ORIGINS=https://erp-fabs-ci.vercel.app`

**MongoDB (Atlas):**
- Cluster: `cluster0.xxxxx.mongodb.net`
- Database: `fabsci_erp`

**Redis (Redis Cloud):**
- Host: `redis-xxxxx.c1.us-east1-2.gcp.cloud.redislabs.com`
- Port: `6379`

---

## 10. Dépannage

### Erreurs courantes

**CORS Error:**
- Vérifiez que `CORS_ORIGINS` contient l'URL exacte du frontend
- Assurez-vous qu'il n'y a pas de slash final

**MongoDB Connection Error:**
- Vérifiez que l'IP 0.0.0.0/0 est autorisée dans MongoDB Atlas
- Vérifiez que le mot de passe est correct dans la connection string

**Redis Connection Error:**
- Vérifiez que TLS est désactivé si nécessaire
- Vérifiez que le mot de passe est correct

**Build Error:**
- Vérifiez que toutes les dépendances sont dans requirements.txt
- Vérifiez que la version Python est compatible (3.11+)

---

## 11. Coûts Estimés

### Option Gratuite (Recommandée pour tests)

- Vercel: Gratuit (frontend)
- Railway: $5/mois (backend) ou gratuit avec Render
- MongoDB Atlas: Gratuit (M0)
- Redis Cloud: Gratuit (30MB)

**Total: $0-5/mois**

### Option Production

- Vercel: $20/mois (Pro)
- Railway: $20/mois
- MongoDB Atlas: $57/mois (M10)
- Redis Cloud: $7/mois

**Total: ~$104/mois**

---

## 12. Support

Pour toute question:
- Consultez les logs de votre hébergeur
- Consultez le fichier `RAPPORT_AUDIT_FINAL.json`
- Vérifiez la documentation de chaque hébergeur
