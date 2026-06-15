# GUIDE COMPLET DE MISE EN PRODUCTION - ERP FABS V7

**Date:** 5 juin 2026  
**Version:** 1.0  
**Objectif:** Guide étape par étape pour déployer l'ERP FABS V7 en production

---

## TABLE DES MATIÈRES

1. [Prérequis](#prérequis)
2. [Configuration des Variables d'Environnement](#configuration-des-variables-denvironnement)
3. [Migration MongoDB](#migration-mongodb)
4. [Build Docker](#build-docker)
5. [Déploiement](#déploiement)
6. [Tests Post-Déploiement](#tests-post-déploiement)
7. [Monitoring et Maintenance](#monitoring-et-maintenance)
8. [Dépannage](#dépannage)

---

## PRÉREQUIS

### Système Requis

- **OS:** Linux (Ubuntu 20.04+ recommandé) ou Docker Compose compatible
- **Docker:** Version 20.10+
- **Docker Compose:** Version 2.0+
- **RAM:** Minimum 4 GB (recommandé 8 GB)
- **Disque:** Minimum 20 GB (recommandé 50 GB)
- **CPU:** Minimum 2 cœurs (recommandé 4 cœurs)

### Logiciels Requis

- Python 3.11+ (pour exécuter les scripts de configuration)
- Git (pour cloner le repository)
- MongoDB 7.0 (géré par Docker)
- Redis 7 (géré par Docker)

---

## CONFIGURATION DES VARIABLES D'ENVIRONNEMENT

### Étape 1: Générer les fichiers .env

Le projet inclut un script automatisé pour générer les fichiers de configuration sécurisés:

```bash
python scripts/setup_production_env.py --domain votre-domaine.com
```

**Remplacez `votre-domaine.com` par votre nom de domaine réel.**

Ce script va:
- Générer un JWT_SECRET fort (32 caractères aléatoires)
- Générer des mots de passe forts pour MongoDB et les utilisateurs
- Créer `backend/.env` avec la configuration backend
- Créer `frontend/.env` avec la configuration frontend
- Créer `.env` à la racine pour Docker Compose

### Étape 2: Sauvegarder les identifiants

Le script affichera les identifiants générés. **SAUVEGARDEZ-LES IMPÉRATIVEMENT:**

```
Super Admin: pissken@editionsfabsci.com / [MOT_DE_PASSE]
DG: ali.mamin@editionsfabsci.com / [MOT_DE_PASSE]
MongoDB Password: [MOT_DE_PASSE]
JWT_SECRET: [SECRET]
```

⚠️ **IMPORTANT:** Ces identifiants ne seront plus affichés. Si vous les perdez, vous devrez régénérer les fichiers.

### Étape 3: Vérifier les fichiers générés

**Backend (.env):**
```bash
cat backend/.env
```

Vérifiez que:
- `ENVIRONMENT=production`
- `JWT_SECRET` est une chaîne longue et aléatoire
- `MONGO_URL` contient un mot de passe fort
- `CORS_ORIGINS` contient votre domaine

**Frontend (.env):**
```bash
cat frontend/.env
```

Vérifiez que:
- `REACT_APP_API_BASE_URL` pointe vers votre domaine

**Docker (.env):**
```bash
cat .env
```

Vérifiez que:
- `MONGO_ROOT_PASSWORD` est un mot de passe fort
- `JWT_SECRET` correspond à celui du backend
- `CORS_ORIGINS` contient votre domaine

---

## MIGRATION MONGODB

### Étape 1: Démarrer MongoDB et Redis (temporairement)

```bash
docker-compose up -d mongodb redis
```

### Étape 2: Attendre que MongoDB soit prêt

```bash
docker-compose logs -f mongodb
```

Attendez de voir: `"MongoDB is ready"`

### Étape 3: Exécuter la migration principale

```bash
python backend/migrations/create_fournisseurs_approvisionnements.py
```

**Résultat attendu:**
```
🚀 Début de la migration Fournisseurs/Approvisionnements...
📦 Base de données: fabsci_erp
🔗 URI: mongodb://localhost:27017

📝 Collection: fournisseurs
  ✅ Fournisseur de test créé
  ✅ Indexes créés

📝 Collection: approvisionnements
  ✅ Approvisionnement de test créé
  ✅ Indexes créés

📝 Mise à jour collection: produits
  ✅ X produits mis à jour
  ✅ Indexes créés

📝 Initialisation compteurs
  ✅ Compteur fournisseurs initialisé
  ✅ Compteur approvisionnements initialisé

✅ Migration terminée avec succès!
```

### Étape 4: Vérifier les collections

```bash
docker exec -it fabsci-mongodb mongosh
```

Dans MongoDB shell:
```javascript
use fabsci_erp
db.getCollectionNames()
```

Vous devriez voir:
- `fournisseurs`
- `approvisionnements`
- `produits` (mis à jour)
- `counters`

### Étape 5: Arrêter les services temporaires

```bash
docker-compose down
```

---

## BUILD DOCKER

### Étape 1: Nettoyer les anciennes images (optionnel)

```bash
docker system prune -a
```

### Étape 2: Construire les images

```bash
docker-compose build
```

**Temps estimé:** 5-10 minutes

### Étape 3: Vérifier les images construites

```bash
docker images | grep fabsci
```

Vous devriez voir:
- `fabsci-backend`
- `fabsci-frontend`

---

## DÉPLOIEMENT

### Option 1: Déploiement Local avec Docker Compose

#### Étape 1: Démarrer tous les services

```bash
docker-compose up -d
```

#### Étape 2: Vérifier le statut des services

```bash
docker-compose ps
```

Tous les services doivent être "Up" et "healthy".

#### Étape 3: Vérifier les logs

```bash
docker-compose logs -f
```

#### Étape 4: Vérifier les healthchecks

```bash
# Backend health
curl http://localhost:8001/health

# Frontend health
curl http://localhost/
```

### Option 2: Déploiement sur Emergent IA

#### Étape 1: Préparer le repository

```bash
git add .
git commit -m "Production ready - ERP FABS V7"
git push
```

#### Étape 2: Configurer dans Emergent IA

1. Connectez-vous à votre compte Emergent IA
2. Importez le repository depuis Git
3. Configurez les variables d'environnement dans l'interface:
   - `MONGO_ROOT_PASSWORD` (votre mot de passe)
   - `JWT_SECRET` (votre secret)
   - `CORS_ORIGINS` (votre domaine)

#### Étape 3: Déployer

Cliquez sur "Deploy" dans l'interface Emergent IA.

#### Étape 4: Vérifier le déploiement

- Frontend: `https://VOTRE_DOMAINE.com`
- Backend: `https://VOTRE_DOMAINE.com/api/health`

### Option 3: Déploiement sur Serveur VPS

#### Étape 1: Préparer le serveur

```bash
# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Installer Nginx (pour reverse proxy)
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

#### Étape 2: Transférer les fichiers

```bash
scp -r . user@votre-serveur:/var/www/erp-fabs-v7
```

#### Étape 3: Configurer Nginx

Créez `/etc/nginx/sites-available/erp-fabs`:

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Activer le site:
```bash
sudo ln -s /etc/nginx/sites-available/erp-fabs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Étape 4: Obtenir le certificat SSL

```bash
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

#### Étape 5: Démarrer l'application

```bash
cd /var/www/erp-fabs-v7
docker-compose up -d
```

---

## TESTS POST-DÉPLOIEMENT

### Étape 1: Test de connexion

1. Ouvrez votre navigateur sur `https://VOTRE_DOMAINE.com`
2. Connectez-vous avec:
   - Email: `pissken@editionsfabsci.com`
   - Password: `[MOT_DE_PASSE_GENERÉ]`

### Étape 2: Test des modules critiques

#### Dashboard
- Vérifiez que le dashboard s'affiche
- Vérifiez les KPIs
- Vérifiez les graphiques

#### Produits
- Allez sur `/produits-inventaire`
- Vérifiez que la liste des produits s'affiche
- Testez les filtres et la recherche
- Testez l'onglet "Fournisseurs"
- Testez l'onglet "Approvisionnement"

#### Stock
- Allez sur `/stock` (si disponible)
- Vérifiez les mouvements de stock
- Testez la création d'un mouvement

#### Factures
- Allez sur `/factures`
- Vérifiez la liste des factures
- Testez la génération PDF

### Étape 3: Test de l'API

```bash
# Health check
curl https://VOTRE_DOMAINE.com/api/health

# Test authentification
curl -X POST https://VOTRE_DOMAINE.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pissken@editionsfabsci.com","password":"VOTRE_MOT_DE_PASSE"}'
```

### Étape 4: Test de performance

```bash
# Temps de chargement frontend
curl -o /dev/null -s -w "%{time_total}\n" https://VOTRE_DOMAINE.com

# Temps de réponse API
curl -o /dev/null -s -w "%{time_total}\n" https://VOTRE_DOMAINE.com/api/health
```

**Objectifs:**
- Frontend: < 2 secondes
- API: < 500 ms

---

## MONITORING ET MAINTENANCE

### Monitoring avec Prometheus

L'application inclut Prometheus pour le monitoring:

```bash
# Accéder à Prometheus
http://VOTRE_DOMAINE.com:9090
```

### Logs

```bash
# Voir tous les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Sauvegardes

#### Sauvegarde MongoDB

```bash
# Sauvegarde manuelle
docker exec fabsci-mongodb mongodump --out /backup

# Sauvegarde automatique (configurée dans .env)
# Les sauvegardes sont stockées dans ./backups
```

#### Restauration MongoDB

```bash
# Restauration manuelle
docker exec fabsci-mongodb mongorestore /backup
```

### Mises à jour

```bash
# Arrêter les services
docker-compose down

# Mettre à jour le code
git pull

# Reconstruire les images
docker-compose build

# Redémarrer
docker-compose up -d
```

---

## DÉPANNAGE

### Problème: Backend ne démarre pas

**Symptôme:** Container backend en "Restarting"

**Solution:**
```bash
# Vérifier les logs
docker-compose logs backend

# Vérifier MongoDB
docker-compose logs mongodb

# Vérifier Redis
docker-compose logs redis
```

**Causes communes:**
- MongoDB non prêt
- Variables d'environnement incorrectes
- Port déjà utilisé

### Problème: Frontend ne se connecte pas à l'API

**Symptôme:** Erreur 502 ou CORS

**Solution:**
```bash
# Vérifier nginx.conf
cat nginx.conf

# Vérifier que le nom du service backend est correct
# Doit être: fabsci-backend
```

### Problème: Erreur de connexion MongoDB

**Symptôme:** "MongoDB connection failed"

**Solution:**
```bash
# Vérifier que MongoDB est en cours d'exécution
docker-compose ps mongodb

# Vérifier les logs MongoDB
docker-compose logs mongodb

# Vérifier les variables d'environnement
cat backend/.env | grep MONGO_URL
```

### Problème: Erreur JWT

**Symptôme:** "Invalid token" ou "Token expired"

**Solution:**
```bash
# Vérifier JWT_SECRET
cat backend/.env | grep JWT_SECRET

# Régénérer les fichiers .env
python scripts/setup_production_env.py --domain votre-domaine.com
```

### Problème: Migration échoue

**Symptôme:** Erreur lors de l'exécution de la migration

**Solution:**
```bash
# Vérifier que MongoDB est en cours d'exécution
docker-compose ps mongodb

# Vérifier les variables d'environnement
cat backend/.env | grep MONGO

# Exécuter la migration avec rollback
python backend/migrations/create_fournisseurs_approvisionnements.py rollback

# Réexécuter la migration
python backend/migrations/create_fournisseurs_approvisionnements.py
```

---

## CHECKLIST FINALE

Avant de considérer le déploiement comme terminé, vérifiez:

- [ ] Fichiers .env créés avec des secrets forts
- [ ] Identifiants sauvegardés de manière sécurisée
- [ ] Migration MongoDB exécutée avec succès
- [ ] Images Docker construites sans erreur
- [ ] Services Docker démarrés et healthy
- [ ] Frontend accessible via HTTPS
- [ ] Backend API accessible et fonctionnel
- [ ] Authentification fonctionnelle
- [ ] Modules critiques testés (Dashboard, Produits, Stock)
- [ ] Sauvegardes configurées
- [ ] Monitoring Prometheus accessible
- [ ] Logs consultables
- [ ] Performance acceptable (< 2s frontend, < 500ms API)

---

## SUPPORT

Pour toute question ou problème:

1. Consultez les logs: `docker-compose logs -f`
2. Consultez ce guide
3. Consultez le rapport d'audit: `AUDIT_PRODUCTION_COMPLET_V7.md`

---

**Document créé par:** Cascade AI Assistant  
**Version:** 1.0  
**Date:** 5 juin 2026
