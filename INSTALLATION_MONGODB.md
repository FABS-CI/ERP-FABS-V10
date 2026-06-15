# GUIDE D'INSTALLATION MONGODB - WINDOWS

## PRÉREQUIS CRITIQUE

MongoDB est requis pour le fonctionnement de l'ERP FABS-CI. Sans MongoDB, aucun module ne peut fonctionner.

## OPTION 1: INSTALLATION MONGODB COMMUNITY SERVER (RECOMMANDÉ)

### Étape 1: Télécharger MongoDB

1. Aller sur: https://www.mongodb.com/try/download/community
2. Sélectionner:
   - Version: 7.0.x (ou dernière stable)
   - Platform: Windows
   - Package: msi
3. Cliquer sur "Download"

### Étape 2: Installer MongoDB

1. Exécuter le fichier `.msi` téléchargé
2. Dans l'assistant d'installation:
   - Cocher "Install MongoDB as a Service"
   - Cocher "Install MongoDB Compass" (optionnel mais recommandé)
   - Cocher "Add MongoDB to system PATH"
3. Cliquer sur "Install"

### Étape 3: Démarrer MongoDB

MongoDB devrait démarrer automatiquement comme service. Vérifier:

```powershell
# Vérifier le service MongoDB
Get-Service -Name MongoDB

# Démarrer le service si nécessaire
Start-Service -Name MongoDB

# Vérifier la version
mongod --version
```

### Étape 4: Tester la connexion

```powershell
# Se connecter à MongoDB
mongosh

# Dans mongosh, tester:
show dbs
exit
```

## OPTION 2: UTILISER DOCKER (ALTERNATIVE)

### Étape 1: Installer Docker Desktop

1. Télécharger Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Installer Docker Desktop
3. Redémarrer l'ordinateur

### Étape 2: Démarrer MongoDB avec Docker

```powershell
# Démarrer MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Vérifier que le conteneur tourne
docker ps

# Se connecter à MongoDB
docker exec -it mongodb mongosh
```

## OPTION 3: UTILISER MONGODB ATLAS (CLOUD)

### Étape 1: Créer un compte gratuit

1. Aller sur: https://www.mongodb.com/cloud/atlas
2. Créer un compte gratuit
3. Créer un cluster gratuit (M0)

### Étape 2: Obtenir la connection string

1. Dans MongoDB Atlas, aller à "Database Access"
2. Créer un utilisateur database avec mot de passe
3. Aller à "Clusters" → "Connect"
4. Copier la connection string

### Étape 3: Configurer l'application

Modifier `backend/.env`:
```
MONGO_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/fabsci_erp?retryWrites=true&w=majority
```

## VÉRIFICATION APRÈS INSTALLATION

Une fois MongoDB installé et démarré, vérifier:

```powershell
# Vérifier que MongoDB répond
mongosh --eval "db.adminCommand('ping')"

# Créer la base de données
mongosh fabsci_erp --eval "db.createCollection('test')"
```

## CONFIGURATION ERP FABS-CI

Créer ou modifier `backend/.env`:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=fabsci_erp
```

## DÉMARRAGE DE L'APPLICATION

Après installation de MongoDB:

```powershell
cd backend
python -m uvicorn server:app --reload
```

## PROBLÈMES COURANTS

### MongoDB ne démarre pas
- Vérifier les logs: `C:\Program Files\MongoDB\Server\7.0\log\mongod.log`
- Vérifier que le port 27017 n'est pas utilisé par une autre application

### Permission refusée
- Exécuter PowerShell en tant qu'Administrateur

### Service MongoDB introuvable
- Réinstaller MongoDB en cochant "Install as Service"

## SUIVI

Une fois MongoDB installé:
1. Marquer la tâche "CORRECTION BLOCAGE CRITIQUE 1 - Installer et démarrer MongoDB" comme terminée
2. Continuer avec les corrections de blocages critiques suivantes
