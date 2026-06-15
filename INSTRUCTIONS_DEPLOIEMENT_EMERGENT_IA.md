# Instructions de Déploiement sur Emergent IA - ERP FABS-CI V7

## 1. Configuration des Variables d'Environnement

Ouvrir `scripts/production-env-config.json` et modifier:

**Variables obligatoires à modifier:**

```json
{
  "MONGO_URL": "mongodb://admin:VOTRE_MOT_DE_PASSE_FORT@mongodb:27017",
  "JWT_SECRET": "GENERER_AVEC_PYTHON_SECRETS",
  "CORS_ORIGINS": "https://VOTRE_DOMAINE_EMERGENT_IA.com",
  "SUPER_ADMIN_PASSWORD": "VOTRE_MOT_DE_PASSE_FORT",
  "DG_PASSWORD": "VOTRE_MOT_DE_PASSE_FORT"
}
```

**Générer JWT_SECRET:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Critères mots de passe:** Minimum 8 caractères, majuscule, minuscule, chiffre, caractère spécial

## 2. Déploiement sur Emergent IA

### Étape 1: Importer le projet
1. Connectez-vous au dashboard Emergent IA
2. Créez un nouveau projet
3. Importez le code depuis Git

### Étape 2: Configurer les variables d'environnement
Dans l'interface Emergent IA, ajoutez chaque variable du fichier `scripts/production-env-config.json`

**Variables critiques:**
- ENVIRONMENT=production
- JWT_SECRET (généré à l'étape 1)
- CORS_ORIGINS (votre domaine Emergent IA)
- SUPER_ADMIN_PASSWORD
- DG_PASSWORD

### Étape 3: Déployer
1. Cliquez sur "Deploy"
2. Attendez que le déploiement soit terminé
3. Vérifiez les logs pour confirmer que tous les services sont démarrés

## 3. Seed des Données de Démonstration

Après déploiement, exécutez dans le terminal du container backend:

```bash
python seed_demo_data.py
```

Cela créera:
- 4 utilisateurs (super_admin, dg, commercial, comptable)
- 3 clients
- 5 produits
- 2 commandes

## 4. Vérification et Tests

### Vérifier les services:
- Frontend: `https://VOTRE_DOMAINE.com`
- Backend: `https://VOTRE_DOMAINE.com/api/health`
- Documentation API: `https://VOTRE_DOMAINE.com/api/docs`

### Se connecter:
- Email: pissken@editionsfabsci.com
- Password: celui configuré dans SUPER_ADMIN_PASSWORD

### Tests fonctionnels à effectuer:
1. Créer un client
2. Créer un produit
3. Créer une commande
4. Valider la commande (vérifier génération automatique de facture)
5. Créer un bon de livraison
6. Enregistrer un paiement

## 5. Services Déployés

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | React + Nginx |
| Backend | 8001 | FastAPI |
| MongoDB | 27017 | Base de données |
| Redis | 6379 | Cache |

## 6. Support

Pour toute question ou problème:
- Consultez les logs dans l'interface Emergent IA
- Consultez le fichier `RAPPORT_AUDIT_FINAL.json` pour l'audit statique
