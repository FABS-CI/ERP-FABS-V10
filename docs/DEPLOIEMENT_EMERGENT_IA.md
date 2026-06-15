# Guide de Déploiement sur Emergent IA - ERP FABS-CI V7

**Date:** 2026-06-02  
**Version:** V7  
**Objectif:** Déploiement complet sur Emergent IA

---

## Prérequis

### 1. Compte Emergent IA
- Compte actif sur Emergent IA
- Accès au dashboard de déploiement
- Permissions pour créer des ressources

### 2. Configuration Locale
- Docker installé
- Docker Compose installé
- Git installé
- Accès au code source du projet

---

## Architecture de Déploiement

### Services Déployés

1. **Frontend** (React + Nginx)
   - Port: 80
   - Sert l'application React statique
   - Proxy les requêtes API vers le backend

2. **Backend** (FastAPI + Python)
   - Port: 8001
   - API REST
   - Connexion MongoDB et Redis

3. **MongoDB** (Base de données)
   - Port: 27017
   - Stockage des données de l'ERP

4. **Redis** (Cache)
   - Port: 6379
   - Cache pour les sessions et données temporaires

---

## Étape 1: Configuration des Variables d'Environnement

### 1.1 Modifier le fichier de configuration

Ouvrir le fichier `scripts/production-env-config.json` et modifier les valeurs suivantes:

**Variables obligatoires à modifier:**

```json
{
  "MONGO_URL": {
    "value": "mongodb://admin:VOTRE_MOT_DE_PASSE_FORT@mongodb:27017"
  },
  "JWT_SECRET": {
    "value": "GENERER_AVEC_PYTHON_SECRETS"
  },
  "CORS_ORIGINS": {
    "value": "https://VOTRE_DOMAINE_EMERGENT_IA.com"
  },
  "SUPER_ADMIN_PASSWORD": {
    "value": "VOTRE_MOT_DE_PASSE_FORT"
  },
  "DG_PASSWORD": {
    "value": "VOTRE_MOT_DE_PASSE_FORT"
  }
}
```

### 1.2 Générer un JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copier le résultat et le coller dans la variable `JWT_SECRET`.

### 1.3 Configurer les mots de passe

Les mots de passe doivent respecter les critères suivants:
- Minimum 8 caractères
- Au moins une majuscule
- Au moins une minuscule
- Au moins un chiffre
- Au moins un caractère spécial (@$!%*?&)

---

## Étape 2: Déploiement sur Emergent IA

### 2.1 Préparer le déploiement

1. Connectez-vous au dashboard Emergent IA
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Importez le code source du projet depuis Git

### 2.2 Configurer les variables d'environnement

Dans l'interface Emergent IA:

1. Allez dans la section "Environment Variables"
2. Ajoutez chaque variable du fichier `scripts/production-env-config.json`
3. Assurez-vous que toutes les variables obligatoires sont configurées

**Variables critiques:**
- `ENVIRONMENT=production`
- `JWT_SECRET` (généré à l'étape 1.2)
- `CORS_ORIGINS` (votre domaine Emergent IA)
- `SUPER_ADMIN_PASSWORD`
- `DG_PASSWORD`

### 2.3 Configurer les ports

Assurez-vous que les ports suivants sont ouverts:
- Port 80: Frontend
- Port 8001: Backend API
- Port 27017: MongoDB (interne seulement)
- Port 6379: Redis (interne seulement)

### 2.4 Déployer

1. Cliquez sur "Deploy" dans l'interface Emergent IA
2. Attendez que le déploiement soit terminé
3. Vérifiez les logs pour confirmer que tous les services sont démarrés

---

## Étape 3: Vérification du Déploiement

### 3.1 Vérifier le Frontend

Ouvrez votre navigateur et accédez à:
```
https://VOTRE_DOMAINE_EMERGENT_IA.com
```

Vous devriez voir la page de login de l'ERP.

### 3.2 Vérifier le Backend API

Testez l'endpoint de santé:
```bash
curl https://VOTRE_DOMAINE_EMERGENT_IA.com/api/health
```

Résultat attendu:
```json
{
  "status": "healthy",
  "timestamp": "2026-06-02T..."
}
```

### 3.3 Vérifier la Documentation API

Accédez à la documentation Swagger:
```
https://VOTRE_DOMAINE_EMERGENT_IA.com/api/docs
```

### 3.4 Vérifier la Connexion MongoDB

Dans les logs du backend, vérifiez:
```
INFO: Connected to MongoDB successfully
```

### 3.5 Vérifier la Connexion Redis

Dans les logs du backend, vérifiez:
```
INFO: Connected to Redis successfully
```

---

## Étape 4: Test des Fonctionnalités

### 4.1 Connexion Admin

1. Utilisez les identifiants du super admin configurés:
   - Email: `pissken@editionsfabsci.com`
   - Mot de passe: celui configuré dans `SUPER_ADMIN_PASSWORD`

2. Connectez-vous et vérifiez que vous accédez au dashboard

### 4.2 Test des Modules

Testez les modules suivants:
- ✅ Dashboard
- ✅ Clients
- ✅ Produits
- ✅ Commandes
- ✅ Factures
- ✅ Paiements
- ✅ Stock
- ✅ Livraisons
- ✅ Comptabilité

### 4.3 Test du Workflow

Testez le workflow complet:
1. Créer un client
2. Créer une commande
3. Valider la commande (vérifier la génération automatique de facture)
4. Créer un bon de livraison
5. Enregistrer un paiement

---

## Étape 5: Monitoring et Maintenance

### 5.1 Monitoring

- Vérifiez les logs régulièrement dans l'interface Emergent IA
- Surveillez l'utilisation des ressources (CPU, RAM, Stockage)
- Configurez des alertes pour les erreurs critiques

### 5.2 Sauvegardes

Les sauvegardes sont configurées par défaut:
- Fréquence: Tous les jours à 2h du matin
- Rétention: 30 jours
- Emplacement: Volume Docker persistant

### 5.3 Mises à jour

Pour mettre à jour l'application:
1. Pushez les modifications sur Git
2. Cliquez sur "Redeploy" dans l'interface Emergent IA
3. Attendez que le déploiement soit terminé

---

## Dépannage

### Problème: Frontend inaccessible

**Cause:** Nginx ne démarre pas

**Solution:**
1. Vérifiez les logs du frontend
2. Vérifiez que le port 80 est ouvert
3. Vérifiez la configuration nginx.conf

### Problème: Backend inaccessible

**Cause:** Backend ne démarre pas

**Solution:**
1. Vérifiez les logs du backend
2. Vérifiez que MongoDB et Redis sont démarrés
3. Vérifiez les variables d'environnement

### Problème: Connexion MongoDB échoue

**Cause:** Mot de passe incorrect ou MongoDB non démarré

**Solution:**
1. Vérifiez que MongoDB est démarré
2. Vérifiez le mot de passe dans MONGO_URL
3. Vérifiez que le volume MongoDB est monté

### Problème: Erreur JWT

**Cause:** JWT_SECRET non configuré ou incorrect

**Solution:**
1. Vérifiez que JWT_SECRET est configuré
2. Régénérez le JWT_SECRET si nécessaire
3. Redémarrez le backend

---

## Sécurité

### Recommandations

1. **Mots de passe forts**
   - Utilisez des mots de passe forts pour tous les comptes
   - Changez les mots de passe par défaut

2. **HTTPS**
   - Assurez-vous que HTTPS est activé
   - Utilisez des certificats SSL valides

3. **Firewall**
   - Limitez l'accès aux ports critiques
   - MongoDB et Redis ne doivent pas être accessibles publiquement

4. **Mises à jour**
   - Maintenez les dépendances à jour
   - Appliquez les correctifs de sécurité

---

## Support

Pour toute question ou problème:
- Consultez les logs dans l'interface Emergent IA
- Consultez la documentation technique
- Contactez l'équipe de support

---

**Document créé par:** Cascade AI Assistant  
**Version:** 1.0
