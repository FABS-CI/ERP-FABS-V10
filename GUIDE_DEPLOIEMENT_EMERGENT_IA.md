# GUIDE DE DÉPLOIEMENT - EMERGENT IA

**ERP FABS V7 - Éditions FABS-CI**  
**Date:** 5 juin 2026  
**Version:** 1.0

---

## PRÉREQUIS

- Compte Emergent IA actif
- Repository Git avec le code ERP FABS V7
- Fichiers .env générés (déjà créés)
- MongoDB accessible (local ou distant)

---

## ÉTAPE 1: PRÉPARATION DU PROJET

### 1.1 Vérifier les fichiers .env

Les fichiers .env ont été générés automatiquement:

- ✅ `backend/.env` - Configuration backend
- ✅ `frontend/.env` - Configuration frontend
- ✅ `.env` - Configuration Docker Compose

### 1.2 Vérifier les identifiants

**Identifiants générés:**
- Super Admin: `pissken@editionsfabsci.com` / `bNJgfSi*WWgO3Zso`
- DG: `ali.mamin@editionsfabsci.com` / `JBaXygtHnPCPY3FM`
- MongoDB Password: `4QV658HJaLfo9ZRJ...`
- JWT_SECRET: `nunvTys1yjkeeT-gEhXi...`

⚠️ **IMPORTANT:** Sauvegardez ces identifiants de manière sécurisée!

### 1.3 Vérifier la configuration Docker

- ✅ `docker-compose.yml` - Configuration Docker (valeurs par défaut supprimées)
- ✅ `Dockerfile.backend` - Configuration backend
- ✅ `Dockerfile.frontend` - Configuration frontend
- ✅ `nginx.conf` - Configuration Nginx

### 1.4 Commit et Push

```bash
git add .
git commit -m "Production ready - Security fixes + Tests + Migration"
git push
```

---

## ÉTAPE 2: DÉPLOIEMENT SUR EMERGENT IA

### 2.1 Connexion à Emergent IA

1. Connectez-vous à votre compte Emergent IA
2. Accédez au tableau de bord

### 2.2 Import du Repository

1. Cliquez sur "New Project" ou "Import Repository"
2. Sélectionnez "Git"
3. Entrez l'URL de votre repository GitHub
4. Cliquez sur "Import"

### 2.3 Configuration des Variables d'Environnement

Dans l'interface Emergent IA, configurez les variables suivantes:

**Variables Backend:**
```
ENVIRONMENT=production
MONGO_URL=mongodb://admin:4QV658HJaLfo9ZRJ...@mongodb:27017
DB_NAME=fabsci_erp
REDIS_URL=redis://redis:6379
JWT_SECRET=nunvTys1yjkeeT-gEhXi...
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7
CORS_ORIGINS=https://fabs-emergent.preview.emergentagent.com
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
FORCE_HTTPS=false
```

**Variables Docker:**
```
MONGO_ROOT_PASSWORD=4QV658HJaLfo9ZRJ...
JWT_SECRET=nunvTys1yjkeeT-gEhXi...
CORS_ORIGINS=https://fabs-emergent.preview.emergentagent.com
```

### 2.4 Configuration du Build

**Backend:**
- Build Context: `.`
- Dockerfile: `Dockerfile.backend`
- Port: `8001`

**Frontend:**
- Build Context: `.`
- Dockerfile: `Dockerfile.frontend`
- Port: `80`

### 2.5 Lancement du Déploiement

1. Cliquez sur "Deploy"
2. Attendez que le build se termine
3. Vérifiez que tous les services sont en cours d'exécution

---

## ÉTAPE 3: VÉRIFICATION POST-DÉPLOIEMENT

### 3.1 Vérifier les Services

Dans l'interface Emergent IA:
- ✅ MongoDB: En cours d'exécution
- ✅ Redis: En cours d'exécution
- ✅ Backend: En cours d'exécution
- ✅ Frontend: En cours d'exécution

### 3.2 Vérifier l'URL de Production

L'URL de production sera:
```
https://fabs-emergent.preview.emergentagent.com
```

### 3.3 Tester le Frontend

1. Ouvrez l'URL de production dans un navigateur
2. Vérifiez que la page de connexion s'affiche
3. Vérifiez que le design est correct

### 3.4 Tester l'Authentification

1. Connectez-vous avec:
   - Email: `pissken@editionsfabsci.com`
   - Password: `bNJgfSi*WWgO3Zso`

2. Vérifiez que:
   - La connexion fonctionne
   - Le dashboard s'affiche
   - Les KPIs sont visibles

### 3.5 Tester l'API Backend

Exécutez les tests automatisés:

```bash
python scripts/test_auth_api.py --base-url https://fabs-emergent.preview.emergentagent.com/api --email pissken@editionsfabsci.com --password bNJgfSi*WWgO3Zso
```

### 3.6 Tester les Modules Critiques

1. **Dashboard:** Vérifiez que les KPIs et graphiques s'affichent
2. **Produits:** Vérifiez que la liste des produits s'affiche
3. **Fournisseurs:** Vérifiez que le module fournisseurs fonctionne
4. **Approvisionnement:** Vérifiez que le module approvisionnement fonctionne
5. **Factures:** Vérifiez que le module facturation fonctionne

---

## ÉTAPE 4: MONITORING

### 4.1 Prometheus

Prometheus est activé par défaut:
- Port: `9090`
- URL: `https://fabs-emergent.preview.emergentagent.com:9090`

### 4.2 Logs

Les logs sont disponibles dans l'interface Emergent IA:
- Logs Backend
- Logs Frontend
- Logs MongoDB
- Logs Redis

### 4.3 Health Checks

Les health checks sont configurés:
- Backend: `/health`
- Frontend: `/`
- MongoDB: `mongosh --eval "db.adminCommand('ping')"`
- Redis: `redis-cli ping`

---

## ÉTAPE 5: SÉCURITÉ

### 5.1 HTTPS

Pour activer HTTPS:
1. Configurez un certificat SSL dans Emergent IA
2. Modifiez `FORCE_HTTPS=true` dans les variables d'environnement
3. Redéployez

### 5.2 Firewall

Configurez les règles de firewall:
- Autoriser le port 80 (HTTP)
- Autoriser le port 443 (HTTPS)
- Autoriser le port 8001 (API interne)

### 5.3 Backup

Configurez les backups automatiques:
- Backup MongoDB quotidien
- Backup des fichiers statiques
- Rétention: 30 jours

---

## ÉTAPE 6: MAINTENANCE

### 6.1 Mises à jour

Pour mettre à jour l'application:
1. Faites les modifications dans le code
2. Commit et Push vers Git
3. Cliquez sur "Redeploy" dans Emergent IA

### 6.2 Monitoring Continu

Surveillez:
- Temps de réponse API (<500ms)
- Temps de chargement frontend (<2s)
- Erreurs 500
- Erreurs 401/403
- Utilisation CPU/Mémoire

### 6.3 Scalabilité

Pour scaler l'application:
1. Augmentez le nombre de replicas dans Emergent IA
2. Configurez un load balancer
3. Utilisez Redis pour le cache distribué

---

## ÉTAPE 7: SUPPORT

### 7.1 Documentation

Documentation disponible:
- `GUIDE_MISE_EN_PRODUCTION_V7.md` - Guide de mise en production
- `AUDIT_PRODUCTION_COMPLET_V7.md` - Audit de production
- `RAPPORT_TEST_DEPLOIEMENT_FINAL.md` - Rapport de tests

### 7.2 Scripts de Test

Scripts de test disponibles:
- `scripts/test_auth_api.py` - Tests authentification et API
- `scripts/test_frontend_complete.py` - Tests frontend
- `scripts/test_performance_security.py` - Tests performance et sécurité

### 7.3 Contact

Pour le support technique:
- Email: support@editionsfabsci.com
- Documentation: docs.editionsfabsci.com

---

## CHECKLIST FINALE

### Pré-Déploiement
- [x] Fichiers .env générés
- [x] Identifiants sauvegardés
- [x] Configuration Docker vérifiée
- [x] Migration MongoDB exécutée
- [x] Code commit et push

### Déploiement
- [ ] Repository importé dans Emergent IA
- [ ] Variables d'environnement configurées
- [ ] Build Docker réussi
- [ ] Services démarrés

### Post-Déploiement
- [ ] Frontend accessible
- [ ] Authentification fonctionnelle
- [ ] Dashboard testé
- [ ] Modules testés
- [ ] API testée
- [ ] Performance vérifiée
- [ ] Sécurité vérifiée

---

## CONCLUSION

L'ERP FABS V7 est prêt pour le déploiement sur Emergent IA. Suivez ce guide étape par étape pour un déploiement réussi.

**Estimation temps total:** 30-60 minutes

**URL de production:** `https://fabs-emergent.preview.emergentagent.com`

---

**Guide généré par:** Cascade AI Assistant (Expert DevOps & QA)  
**Version:** 1.0  
**Date:** 5 juin 2026
