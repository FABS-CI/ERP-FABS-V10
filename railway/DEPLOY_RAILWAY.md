# Guide déploiement Railway — ERP FABS-CI V10

## Architecture sur Railway
```
Project FABS-ERP
├── Service: mongodb      (plugin Railway)
├── Service: redis        (plugin Railway)
├── Service: backend      (Dockerfile.backend.railway)
└── Service: frontend     (Dockerfile.frontend.railway)
```

---

## ÉTAPE 1 — Créer le projet Railway

1. Aller sur https://railway.app → **New Project**
2. Choisir **Empty Project**
3. Nommer le projet : `fabs-erp-v10`

---

## ÉTAPE 2 — Ajouter MongoDB

1. Dans le projet → **+ New Service** → **Database** → **MongoDB**
2. Railway crée MongoDB automatiquement
3. Cliquer sur le service MongoDB → onglet **Variables**
4. Copier la valeur de `MONGO_URL` (ex: `mongodb://mongo:xxx@mongodb.railway.internal:27017`)

---

## ÉTAPE 3 — Ajouter Redis

1. **+ New Service** → **Database** → **Redis**
2. Cliquer sur Redis → onglet **Variables**
3. Copier la valeur de `REDIS_URL`

---

## ÉTAPE 4 — Déployer le Backend

1. **+ New Service** → **GitHub Repo** → sélectionner `FABS-CI/ERP-FABS-V10`
2. Nommer le service : `backend`
3. Onglet **Settings** → **Build** :
   - Dockerfile Path : `Dockerfile.backend.railway`
4. Onglet **Variables** → ajouter toutes ces variables :

```
ENVIRONMENT=production
MONGO_URL=<copier depuis service MongoDB>
DB_NAME=fabsci_erp
REDIS_URL=<copier depuis service Redis>
JWT_SECRET=<générer: python3 -c "import secrets; print(secrets.token_hex(64))">
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRY_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRY_DAYS=7
CORS_ORIGINS=https://<url-frontend>.railway.app
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=false
```

5. **Deploy** → attendre que le build soit vert ✅
6. Onglet **Settings** → copier l'URL publique du backend
   Ex: `https://backend-production-xxxx.up.railway.app`

---

## ÉTAPE 5 — Déployer le Frontend

1. **+ New Service** → **GitHub Repo** → même repo `FABS-CI/ERP-FABS-V10`
2. Nommer le service : `frontend`
3. Onglet **Settings** → **Build** :
   - Dockerfile Path : `Dockerfile.frontend.railway`
4. Onglet **Variables** → ajouter :

```
BACKEND_URL=https://<url-backend>.up.railway.app
```

5. **Deploy** → attendre ✅
6. Copier l'URL publique du frontend

---

## ÉTAPE 6 — Mettre à jour CORS_ORIGINS dans le backend

1. Retourner sur le service **backend** → Variables
2. Mettre à jour :
```
CORS_ORIGINS=https://<url-frontend>.up.railway.app
```
3. Railway redéploie automatiquement

---

## ÉTAPE 7 — Importer les données

Depuis la sandbox Runable, exporter et importer la DB :

```bash
# Sur la sandbox (exporter)
mongodump --db fabsci_erp --out /tmp/fabsci_dump
# Puis utiliser mongorestore vers le MongoDB Railway via l'URL publique
mongorestore --uri "<MONGO_URL_PUBLIC_RAILWAY>" /tmp/fabsci_dump/fabsci_erp
```

> L'URL publique MongoDB Railway se trouve dans Variables du service MongoDB → `MONGO_PUBLIC_URL`

---

## ÉTAPE 8 — Vérification finale

```bash
# Health check backend
curl https://<url-backend>.up.railway.app/api/health

# Login test
curl -X POST https://<url-backend>.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pissken@editionsfabsci.com","password":"Admin@2025"}'
```

---

## Résumé des URLs

| Service | URL |
|---|---|
| Frontend | `https://frontend-xxxx.up.railway.app` |
| Backend API | `https://backend-xxxx.up.railway.app/api` |

---

## Coût estimé Railway

| Service | Coût/mois |
|---|---|
| Backend (FastAPI) | ~$1-2 |
| Frontend (nginx) | ~$0.5 |
| MongoDB | ~$1-2 |
| Redis | ~$0.5 |
| **Total** | **~$3-5/mois** |

Avec $5 de crédit gratuit à l'inscription → **2-4 semaines de test gratuit**.
