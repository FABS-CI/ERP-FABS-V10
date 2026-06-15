# PLAN DE TEST COMPLET ERP FABS-CI

**Date:** 1er juin 2026  
**Objectif:** Valider ERP avant production  
**Règle:** ERP valide uniquement si tous tests passent, workflow complet fonctionne, aucune faille RBAC, backup/restore validés

---

## 1. TEST START SYSTEM

### 1.1 Démarrage Backend
```bash
# Commande
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# Critères de succès
- Aucune erreur au démarrage
- Log: "Application startup complete"
- Endpoint /health accessible
```

### 1.2 Connexion Base de Données
```bash
# Test connexion MongoDB
mongosh --eval "db.adminCommand('ping')"

# Critères de succès
- MongoDB répond {ok: 1}
- Collection fabsci_erp accessible
- 31 collections présentes
```

### 1.3 Frontend Accessible
```bash
# Démarrer frontend
cd frontend
npm start

# Critères de succès
- http://localhost:3000 accessible
- Page login affichée
- Aucune erreur console
```

### 1.4 Absence Erreurs Console
```javascript
// Dans navigateur devtools
// Critères de succès
- 0 erreurs console
- 0 avertissements critiques
- Tous assets chargés
```

---

## 2. TEST AUTHENTIFICATION

### 2.1 Login Valide
```python
# POST /api/auth/login
{
  "email": "pissken@editionsfabsci.com",
  "password": "Admin@2025"
}

# Critères de succès
- Status: 200
- access_token présent
- refresh_token présent
- Cookie httpOnly set
```

### 2.2 Login Invalide
```python
# POST /api/auth/login
{
  "email": "invalid@test.com",
  "password": "wrong"
}

# Critères de succès
- Status: 401
- Message: "Invalid credentials"
- Aucun token retourné
```

### 2.3 Accès Sans Token Refusé
```python
# GET /api/clients (sans Authorization header)

# Critères de succès
- Status: 401
- Message: "Not authenticated"
```

### 2.4 Refresh Token
```python
# POST /api/auth/refresh
{
  "refresh_token": "<valid_refresh_token>"
}

# Critères de succès
- Status: 200
- Nouveau access_token généré
- Nouveau refresh_token généré
- Ancien refresh_token révoqué
```

### 2.5 Logout Invalide Session
```python
# POST /api/auth/logout
# POST /api/auth/refresh avec ancien token

# Critères de succès
- Status: 401
- Message: "Invalid or expired refresh token"
```

---

## 3. TEST RBAC

### 3.1 Directeur Général - Lecture Seule
```python
# User: directeur_general
# GET /api/clients
# Critères de succès
- Status: 200
- Données accessibles

# POST /api/clients
# Critères de succès
- Status: 403
- Message: "Permission denied"
```

### 3.2 Comptable - Accès Finance Uniquement
```python
# User: comptable
# GET /api/factures
# Critères de succès
- Status: 200

# GET /api/clients
# Critères de succès
- Status: 403

# GET /api/produits
# Critères de succès
- Status: 403
```

### 3.3 Logistique - Accès Transport Uniquement
```python
# User: logistique
# GET /api/fleet/vehicles
# Critères de succès
- Status: 200

# GET /api/factures
# Critères de succès
- Status: 403

# GET /api/clients
# Critères de succès
- Status: 403
```

### 3.4 Magasinier - Accès Stock Uniquement
```python
# User: magasinier
# GET /api/produits
# Critères de succès
- Status: 200

# GET /api/stock/mouvements
# Critères de succès
- Status: 200

# GET /api/factures
# Critères de succès
- Status: 403
```

---

## 4. TEST API CORE CRUD

### 4.1 Clients CRUD
```python
# CREATE
POST /api/clients
{
  "nom": "Test Client",
  "type_client": "particulier",
  "telephone": "+225 07 01 02 03 04",
  "email": "test@example.com",
  "ville": "Abidjan"
}
# Status: 201

# READ
GET /api/clients/{client_id}
# Status: 200

# UPDATE
PATCH /api/clients/{client_id}
{
  "nom": "Test Client Updated"
}
# Status: 200

# DELETE
DELETE /api/clients/{client_id}
# Status: 200
```

### 4.2 Produits CRUD
```python
# CREATE
POST /api/produits
{
  "titre": "Test Product",
  "reference": "TEST-001",
  "categorie": "primaire",
  "prix_vente": 5000,
  "stock_actuel": 100
}
# Status: 201

# READ
GET /api/produits/{product_id}
# Status: 200

# UPDATE
PATCH /api/produits/{product_id}
{
  "prix_vente": 6000
}
# Status: 200

# DELETE
DELETE /api/produits/{product_id}
# Status: 200
```

### 4.3 Commandes CRUD
```python
# CREATE
POST /api/commandes?submit=true
{
  "client_id": "{client_id}",
  "lignes": [
    {
      "produit_id": "{product_id}",
      "quantite": 5,
      "prix_unitaire": 5000
    }
  ]
}
# Status: 201

# READ
GET /api/commandes/{commande_id}
# Status: 200

# UPDATE
PATCH /api/commandes/{commande_id}
{
  "statut": "en_cours"
}
# Status: 200

# DELETE
DELETE /api/commandes/{commande_id}
# Status: 200
```

### 4.4 Factures CRUD
```python
# CREATE
POST /api/factures
{
  "commande_id": "{commande_id}",
  "date_facture": "2026-06-01"
}
# Status: 201

# READ
GET /api/factures/{facture_id}
# Status: 200

# UPDATE
PATCH /api/factures/{facture_id}
{
  "statut": "payee"
}
# Status: 200

# DELETE
DELETE /api/factures/{facture_id}
# Status: 200
```

### 4.5 Paiements CRUD
```python
# CREATE
POST /api/paiements
{
  "facture_id": "{facture_id}",
  "montant": 25000,
  "mode_paiement": "especes",
  "date_paiement": "2026-06-01"
}
# Status: 201

# READ
GET /api/paiements/{paiement_id}
# Status: 200

# UPDATE
PATCH /api/paiements/{paiement_id}
{
  "statut": "confirme"
}
# Status: 200

# DELETE
DELETE /api/paiements/{paiement_id}
# Status: 200
```

### 4.6 Stock CRUD
```python
# CREATE MOUVEMENT
POST /api/stock/mouvements
{
  "produit_id": "{product_id}",
  "quantite": 10,
  "type_mouvement": "entree",
  "motif": "Réapprovisionnement"
}
# Status: 201

# READ
GET /api/stock/mouvements
# Status: 200

# UPDATE STOCK
PATCH /api/produits/{product_id}
{
  "stock_actuel": 110
}
# Status: 200
```

### 4.7 Scénario Obligatoire: Client → Commande → Validation → Facture → Paiement
```python
# Étape 1: Créer client
client = POST /api/clients {...}
client_id = client["client_id"]

# Étape 2: Créer produit
produit = POST /api/produits {...}
product_id = produit["product_id"]

# Étape 3: Créer commande
commande = POST /api/commandes {
  "client_id": client_id,
  "lignes": [{"produit_id": product_id, "quantite": 5}]
}
commande_id = commande["commande_id"]

# Étape 4: Valider commande
POST /api/commandes/{commande_id}/valider
# Status: 200

# Étape 5: Créer facture
facture = POST /api/factures {
  "commande_id": commande_id
}
facture_id = facture["facture_id"]

# Étape 6: Valider facture
POST /api/factures/{facture_id}/valider
# Status: 200

# Étape 7: Créer paiement
POST /api/paiements {
  "facture_id": facture_id,
  "montant": facture["montant_total"]
}
# Status: 201

# Critères de succès
- Toutes étapes Status: 200/201
- Statut commande: "validee"
- Statut facture: "validee"
- Statut paiement: "confirme"
```

---

## 5. TEST WORKFLOW ERP

### 5.1 Validation Comptable Obligatoire Avant Livraison
```python
# Créer commande sans validation comptable
commande = POST /api/commandes {...}

# Tenter livraison sans validation
POST /api/bons-livraison {
  "commande_id": commande_id
}
# Critères de succès
- Status: 400
- Message: "Commande non validée par comptable"

# Valider commande comptable
POST /api/commandes/{commande_id}/valider
# Status: 200

# Créer bon livraison
POST /api/bons-livraison {
  "commande_id": commande_id
}
# Status: 201
```

### 5.2 Changement Statut Commande Correct
```python
# Commande créée: statut = "brouillon"
commande = POST /api/commandes {...}
assert commande["statut"] == "brouillon"

# Validation: statut = "en_attente_validation"
POST /api/commandes/{commande_id}/submit
assert commande["statut"] == "en_attente_validation"

# Validation comptable: statut = "validee"
POST /api/commandes/{commande_id}/valider
assert commande["statut"] == "validee"

# Livraison: statut = "livree"
POST /api/bons-livraison/{bl_id}/livrer
assert commande["statut"] == "livree"
```

### 5.3 Blocage Si Étape Non Respectée
```python
# Tenter validation sans soumission
POST /api/commandes/{commande_id}/valider
# Critères de succès
- Status: 400
- Message: "Commande doit être soumise avant validation"

# Tenter livraison sans validation
POST /api/bons-livraison {...}
# Critères de succès
- Status: 400
- Message: "Commande non validée"

# Tenter facturation sans livraison
POST /api/factures {...}
# Critères de succès
- Status: 400
- Message: "Commande non livrée"
```

---

## 6. TEST LOGISTIQUE

### 6.1 Création Mission Véhicule
```python
# Créer véhicule
POST /api/fleet/vehicles
{
  "immatriculation": "AB-123-CD",
  "marque": "Toyota",
  "modele": "Hilux",
  "type": "camion",
  "statut": "actif"
}
# Status: 201

# Créer mission
POST /api/fleet/missions
{
  "vehicle_id": "{vehicle_id}",
  "origine": "Abidjan",
  "destination": "Bouaké",
  "distance_km": 350,
  "date_depart": "2026-06-01"
}
# Status: 201
```

### 6.2 Calcul Coûts Mission
```python
# GET /api/fleet/missions/{mission_id}
mission = GET /api/fleet/missions/{mission_id}

# Vérifier calcul
coût_carburant = mission["distance_km"] * mission["consommation"] * mission["prix_carburant"]
coût_total = coût_carburant + mission["frais_conducteur"] + mission["frais_autoroute"]

# Critères de succès
- mission["cout_estime"] == coût_total
- mission["cout_reel"] calculé après mission
```

### 6.3 Blocage Véhicule Si Assurance Expirée
```python
# Créer véhicule avec assurance expirée
POST /api/fleet/vehicles {...}
POST /api/fleet/insurances
{
  "vehicle_id": "{vehicle_id}",
  "date_fin": "2025-12-31"  # Expiré
}

# Tenter créer mission
POST /api/fleet/missions
{
  "vehicle_id": "{vehicle_id}",
  ...
}
# Critères de succès
- Status: 400
- Message: "Véhicule assurance expirée"
```

### 6.4 Blocage Si Visite Technique Invalide
```python
# Créer véhicule sans visite technique valide
POST /api/fleet/vehicles {...}
POST /api/fleet/inspections
{
  "vehicle_id": "{vehicle_id}",
  "date": "2025-01-01",  # Ancienne
  "statut": "expire"
}

# Tenter créer mission
POST /api/fleet/missions
{
  "vehicle_id": "{vehicle_id}",
  ...
}
# Critères de succès
- Status: 400
- Message: "Visite technique expirée"
```

---

## 7. TEST NOTIFICATIONS

### 7.1 Notification Création Commande
```python
# Créer commande
POST /api/commandes {...}

# Vérifier notification
GET /api/notifications
# Critères de succès
- Notification présente
- Type: "commande_cree"
- Contient commande_id
```

### 7.2 Notification Validation Comptable
```python
# Valider commande
POST /api/commandes/{commande_id}/valider

# Vérifier notification
GET /api/notifications
# Critères de succès
- Notification présente
- Type: "commande_validee"
- Destinataire: comptable
```

### 7.3 Notification Stock Faible
```python
# Créer produit avec stock faible
POST /api/produits
{
  "stock_actuel": 5,
  "stock_minimum": 10
}

# Vérifier alerte
GET /api/produits/alertes-stock
# Critères de succès
- Produit dans alertes
- Notification créée
```

### 7.4 Notification Livraison
```python
# Livrer commande
POST /api/bons-livraison/{bl_id}/livrer

# Vérifier notification
GET /api/notifications
# Critères de succès
- Notification présente
- Type: "livraison_effectuee"
- Destinataire: client, logistique
```

---

## 8. TEST BACKUP / RESTORE

### 8.1 Backup Manuel
```bash
# Exécuter script backup
./scripts/backup_mongodb.sh

# Critères de succès
- Fichier backup créé: /var/backups/fabsci-erp/fabsci_erp_YYYYMMDD_HHMMSS.gz
- Taille fichier > 0
- Log: "Backup completed successfully"
```

### 8.2 Backup Automatique
```bash
# Configurer cron
crontab -e
# Ajouter: 0 2 * * * /path/to/scripts/backup_mongodb.sh

# Vérifier après 2h
ls -la /var/backups/fabsci-erp/
# Critères de succès
- Backup présent avec timestamp correct
```

### 8.3 Restauration Complète Base
```bash
# Créer données test
POST /api/clients {...}
POST /api/produits {...}
client_count_before = GET /api/clients count

# Backup
./scripts/backup_mongodb.sh
backup_file = "fabsci_erp_YYYYMMDD_HHMMSS.gz"

# Supprimer données
DELETE /api/clients/{client_id}
DELETE /api/produits/{product_id}

# Restore
./scripts/restore_mongodb.sh {backup_file}

# Critères de succès
- client_count_after == client_count_before
- Données restaurées intactes
```

### 8.4 Intégrité Données Après Restore
```python
# Avant backup
client = GET /api/clients/{client_id}
client_data_before = client

# Backup + Restore
./scripts/backup_mongodb.sh
./scripts/restore_mongodb.sh {backup_file}

# Après restore
client = GET /api/clients/{client_id}
client_data_after = client

# Critères de succès
- client_data_before == client_data_after
- Tous champs identiques
- Aucune corruption
```

---

## 9. TEST PERFORMANCE

### 9.1 Temps Réponse API
```python
import time

# Mesurer temps réponse
start = time.time()
GET /api/clients
elapsed = time.time() - start

# Critères de succès
- elapsed < 0.5s (500ms)
- Mesurer 10 fois, moyenne < 500ms
```

### 9.2 Chargement Dashboard
```python
# Mesurer chargement dashboard
start = time.time()
GET /api/dashboard/stats
elapsed = time.time() - start

# Critères de succès
- elapsed < 0.5s
- Données complètes retournées
```

### 9.3 Requêtes Lourdes
```python
# Test requête avec pagination large
GET /api/commandes?limit=1000&skip=0
start = time.time()
elapsed = time.time() - start

# Critères de succès
- elapsed < 2s
- Pagination fonctionnelle
- Aucun timeout
```

### 9.4 Seuils
- API endpoints: < 500ms
- Dashboard: < 500ms
- Requêtes lourdes: < 2s
- UI chargement: < 2s

---

## 10. TEST END-TO-END GLOBAL

### 10.1 Scénario Complet Obligatoire
```python
# Étape 1: Login
login = POST /api/auth/login {
  "email": "pissken@editionsfabsci.com",
  "password": "Admin@2025"
}
token = login["access_token"]

# Étape 2: Créer client
client = POST /api/clients {
  "nom": "E2E Client",
  "type_client": "particulier",
  "email": "e2e@example.com"
}
client_id = client["client_id"]

# Étape 3: Créer commande
commande = POST /api/commandes {
  "client_id": client_id,
  "lignes": [...]
}
commande_id = commande["commande_id"]

# Étape 4: Validation
POST /api/commandes/{commande_id}/valider
# Status: 200

# Étape 5: Stock
POST /api/stock/mouvements {
  "produit_id": product_id,
  "quantite": -5,
  "type_mouvement": "sortie"
}
# Status: 201

# Étape 6: Livraison
bl = POST /api/bons-livraison {
  "commande_id": commande_id
}
POST /api/bons-livraison/{bl_id}/livrer
# Status: 200

# Étape 7: Paiement
facture = POST /api/factures {
  "commande_id": commande_id
}
paiement = POST /api/paiements {
  "facture_id": facture_id,
  "montant": facture["montant_total"]
}
# Status: 201

# Étape 8: Notification
notifications = GET /api/notifications
# Critères de succès
- Notification livraison présente
- Notification paiement présente

# Critères de succès globaux
- Toutes étapes Status: 200/201
- Aucune erreur
- Workflow complet sans rupture
```

---

## 11. LIVRABLES ATTENDUS

### 11.1 Plan de Test Automatisé Backend (Jest/Pytest)
**Fichier:** `backend/tests/test_qa_complete.py`

```python
import pytest
import requests
import time

BASE_URL = "http://localhost:8001/api"

class TestQAComplete:
    """Tests QA complets pour validation production"""
    
    def test_start_system(self):
        """Test 1: Start System"""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["mongodb"] == "connected"
        assert r.json()["redis"] == "connected"
    
    def test_auth_valid_login(self):
        """Test 2.1: Login Valide"""
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "pissken@editionsfabsci.com",
            "password": "Admin@2025"
        })
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert "refresh_token" in r.json()
    
    def test_auth_invalid_login(self):
        """Test 2.2: Login Invalide"""
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrong"
        })
        assert r.status_code == 401
    
    def test_rbac_comptable_access(self):
        """Test 3.2: Comptable Accès Finance Uniquement"""
        # Login comptable
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "comptable@editionsfabsci.com",
            "password": "Comptable@2025"
        })
        token = r.json()["access_token"]
        
        # Accès factures autorisé
        r = requests.get(f"{BASE_URL}/factures", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        
        # Accès clients refusé
        r = requests.get(f"{BASE_URL}/clients", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403
    
    def test_api_core_scenario(self):
        """Test 4.7: Scénario Client→Commande→Validation→Facture→Paiement"""
        # Login
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "pissken@editionsfabsci.com",
            "password": "Admin@2025"
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Créer client
        client = requests.post(f"{BASE_URL}/clients", json={
            "nom": "QA Test Client",
            "type_client": "particulier",
            "email": "qa@example.com",
            "ville": "Abidjan"
        }, headers=headers)
        assert client.status_code == 201
        client_id = client.json()["client_id"]
        
        # Créer produit
        produit = requests.post(f"{BASE_URL}/produits", json={
            "titre": "QA Test Product",
            "reference": "QA-001",
            "categorie": "primaire",
            "prix_vente": 5000,
            "stock_actuel": 100
        }, headers=headers)
        assert produit.status_code == 201
        product_id = produit.json()["product_id"]
        
        # Créer commande
        commande = requests.post(f"{BASE_URL}/commandes?submit=true", json={
            "client_id": client_id,
            "lignes": [{
                "produit_id": product_id,
                "quantite": 5,
                "prix_unitaire": 5000
            }]
        }, headers=headers)
        assert commande.status_code == 201
        commande_id = commande.json()["commande_id"]
        
        # Valider commande
        r = requests.post(f"{BASE_URL}/commandes/{commande_id}/valider", headers=headers)
        assert r.status_code == 200
        
        # Créer facture
        facture = requests.post(f"{BASE_URL}/factures", json={
            "commande_id": commande_id,
            "date_facture": "2026-06-01"
        }, headers=headers)
        assert facture.status_code == 201
        facture_id = facture.json()["facture_id"]
        
        # Valider facture
        r = requests.post(f"{BASE_URL}/factures/{facture_id}/valider", headers=headers)
        assert r.status_code == 200
        
        # Créer paiement
        paiement = requests.post(f"{BASE_URL}/paiements", json={
            "facture_id": facture_id,
            "montant": 25000,
            "mode_paiement": "especes",
            "date_paiement": "2026-06-01"
        }, headers=headers)
        assert paiement.status_code == 201
        
        # Cleanup
        requests.delete(f"{BASE_URL}/clients/{client_id}", headers=headers)
        requests.delete(f"{BASE_URL}/produits/{product_id}", headers=headers)
    
    def test_performance_api(self):
        """Test 9.1: Temps Réponse API"""
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "pissken@editionsfabsci.com",
            "password": "Admin@2025"
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        start = time.time()
        r = requests.get(f"{BASE_URL}/clients", headers=headers)
        elapsed = time.time() - start
        
        assert r.status_code == 200
        assert elapsed < 0.5, f"API response time {elapsed}s exceeds 500ms threshold"
```

### 11.2 Plan de Test Frontend (Playwright)
**Fichier:** `frontend/tests/e2e/qa.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('QA Tests ERP FABS-CI', () => {
  test('Login valide', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="email"]', 'pissken@editionsfabsci.com');
    await page.fill('[name="password"]', 'Admin@2025');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('Login invalide', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[name="email"]', 'invalid@test.com');
    await page.fill('[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });

  test('Dashboard chargement < 2s', async ({ page }) => {
    const start = Date.now();
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(2000);
  });

  test('Workflow complet: Client→Commande→Facture', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000');
    await page.fill('[name="email"]', 'pissken@editionsfabsci.com');
    await page.fill('[name="password"]', 'Admin@2025');
    await page.click('button[type="submit"]');
    
    // Créer client
    await page.click('text=Clients');
    await page.click('text=Nouveau Client');
    await page.fill('[name="nom"]', 'E2E Client');
    await page.fill('[name="email"]', 'e2e@example.com');
    await page.click('text=Enregistrer');
    await expect(page.locator('.success')).toBeVisible();
    
    // Créer commande
    await page.click('text=Commandes');
    await page.click('text=Nouvelle Commande');
    await page.selectOption('[name="client_id"]', 'E2E Client');
    await page.click('text=Ajouter Ligne');
    await page.fill('[name="quantite"]', '5');
    await page.click('text=Valider');
    await expect(page.locator('.success')).toBeVisible();
  });
});
```

### 11.3 Pipeline CI/CD Test
**Fichier:** `.github/workflows/qa-tests.yml`

```yaml
name: QA Tests Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-qa-tests:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:7.0
        ports:
          - 27017:27017
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-timeout requests
    
    - name: Run QA tests
      working-directory: ./backend
      env:
        MONGO_URL: mongodb://localhost:27017
        DB_NAME: test_fabsci_erp
        REDIS_URL: redis://localhost:6379
        JWT_SECRET: test-secret-key
      run: |
        python -m uvicorn server:app --host 0.0.0.0 --port 8001 &
        sleep 10
        pytest tests/test_qa_complete.py -v --tb=short --timeout=300
    
    - name: Performance tests
      working-directory: ./backend
      run: |
        pytest tests/test_qa_complete.py::TestQAComplete::test_performance_api -v

  frontend-qa-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Install Playwright
      working-directory: ./frontend
      run: npx playwright install --with-deps
    
    - name: Run Playwright tests
      working-directory: ./frontend
      run: npx playwright test
    
    - name: Upload test results
      uses: actions/upload-artifact@v4
      with:
        name: playwright-report
        path: frontend/playwright-report/
```

### 11.4 Checklist QA Production
**Fichier:** `QA_CHECKLIST_PRODUCTION.md`

```markdown
# CHECKLIST QA PRODUCTION ERP FABS-CI

## PRÉ-DÉPLOIEMENT
- [ ] MongoDB installé et running
- [ ] Redis installé et running
- [ ] Variables d'environnement configurées (.env)
- [ ] JWT_SECRET défini (pas valeur par défaut)
- [ ] CORS origins configurés pour production
- [ ] Security headers activés
- [ ] Backup automatique configuré (cron)
- [ ] S3 bucket créé et configuré
- [ ] Grafana configuré avec datasources
- [ ] Alertmanager configuré avec notifications

## TESTS AUTOMATISÉS
- [ ] Tests backend passent (pytest)
- [ ] Tests frontend passent (Playwright)
- [ ] Tests E2E passent
- [ ] Tests performance passent (< 500ms API, < 2s UI)
- [ ] Tests RBAC passent
- [ ] Tests workflow passent
- [ ] Tests backup/restore passent

## VALIDATION MANUELLE
- [ ] Login fonctionne
- [ ] Dashboard charge sans erreur
- [ ] CRUD clients fonctionne
- [ ] CRUD produits fonctionne
- [ ] Workflow commande→facture→paiement fonctionne
- [ ] Notifications s'affichent
- [ ] Logs centralisés visibles dans Loki
- [ ] Métriques visibles dans Grafana

## SÉCURITÉ
- [ ] HTTPS activé
- [ ] Certificat SSL valide
- [ ] Security headers présents
- [ ] Rate limiting actif
- [ ] JWT secrets non exposés
- [ ] RBAC fonctionnel
- [ ] Audit logging actif

## BACKUP/RESTORE
- [ ] Backup manuel testé
- [ ] Backup automatique testé
- [ ] Restore testé
- [ ] Intégrité données vérifiée
- [ ] Upload S3 testé
- [ ] Rétention configurée

## PERFORMANCE
- [ ] API response time < 500ms
- [ ] Dashboard load time < 2s
- [ ] Requêtes lourdes < 2s
- [ ] MongoDB indexes configurés
- [ ] Redis caching actif

## MONITORING
- [ ] Prometheus collecte métriques
- [ ] Grafana dashboard fonctionnel
- [ ] Alertes configurées
- [ ] Notifications Slack/Email testées
- [ ] Logs agrégés dans Loki

## DOCUMENTATION
- [ ] Guide installation mis à jour
- [ ] Guide déploiement créé
- [ ] Guide backup/restore créé
- [ ] Guide troubleshooting créé

## SIGN-OFF
- [ ] Développeur sign-off
- [ ] QA sign-off
- [ ] DevOps sign-off
- [ ] Security sign-off
- [ ] Product Owner sign-off
```

---

## RÈGLE DE VALIDATION

Un ERP FABS-CI est valide pour production UNIQUEMENT si:

1. **Tous les tests passent**
   - Tests backend: 100% pass
   - Tests frontend: 100% pass
   - Tests E2E: 100% pass
   - Tests performance: 100% pass (seuils respectés)

2. **Workflow complet fonctionne sans rupture**
   - Client → Commande → Validation → Facture → Paiement
   - Aucune erreur dans le flux
   - Statuts corrects à chaque étape

3. **Aucune faille RBAC**
   - Directeur général: lecture seule
   - Comptable: finance uniquement
   - Logistique: transport uniquement
   - Magasinier: stock uniquement
   - Accès non autorisé refusé

4. **Backup et restore validés**
   - Backup manuel fonctionne
   - Backup automatique fonctionne
   - Restore fonctionne
   - Intégrité données préservée

---

**Plan de Test Complet ERP FABS-CI**  
**Statut:** PRÊT POUR EXÉCUTION  
**Prérequis:** MongoDB installé et running  
**Durée estimée:** 4-6 heures pour exécution complète
