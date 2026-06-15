# Déploiement ERP FABS-CI V7 sur Emergent IA

## Fichiers de Déploiement

### 1. Docker Configuration
- `Dockerfile.backend` - Configuration Docker pour le backend FastAPI
- `Dockerfile.frontend` - Configuration Docker pour le frontend React
- `nginx.conf` - Configuration Nginx pour le frontend
- `docker-compose.yml` - Orchestration des services Docker

### 2. Configuration de Production
- `scripts/production-env-config.json` - Variables d'environnement de production

### 3. Scripts de Déploiement
- `scripts/deploy-emergent-ia.sh` - Script de déploiement automatique

### 4. Documentation
- `docs/DEPLOIEMENT_EMERGENT_IA.md` - Guide complet de déploiement

## Étapes Rapides de Déploiement

### 1. Configuration des Variables d'Environnement

Modifier le fichier `scripts/production-env-config.json`:
- Générer un JWT_SECRET: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Configurer les mots de passe forts (minimum 8 caractères, majuscule, minuscule, chiffre, caractère spécial)
- Remplacer le domaine dans CORS_ORIGINS

### 2. Déploiement Local (Test)

```bash
# Construire et démarrer les services
docker-compose up -d

# Vérifier l'état
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### 3. Déploiement sur Emergent IA

1. Connectez-vous au dashboard Emergent IA
2. Importez le code source depuis Git
3. Configurez les variables d'environnement dans l'interface
4. Cliquez sur "Deploy"
5. Attendez que le déploiement soit terminé

### 4. Vérification

- Frontend: `https://VOTRE_DOMAINE.com`
- Backend API: `https://VOTRE_DOMAINE.com/api/health`
- Documentation API: `https://VOTRE_DOMAINE.com/api/docs`

## Services Déployés

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | React + Nginx |
| Backend | 8001 | FastAPI |
| MongoDB | 27017 | Base de données |
| Redis | 6379 | Cache |

## Support

Pour plus de détails, consultez `docs/DEPLOIEMENT_EMERGENT_IA.md`
