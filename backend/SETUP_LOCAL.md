# Setup local ERP FABS-CI

## Stack
- **Backend**: FastAPI + uvicorn, port **8000**
- **Frontend**: React (CRA/craco), port **3000** (proxy `/api` → 8000 via `src/setupProxy.js`)
- **Database**: MongoDB 7.0 sur `mongodb://localhost:27017`, db `fabsci_erp`

## Démarrage

### 1. MongoDB
```bash
mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017 --fork --logpath /tmp/mongod.log
```

### 2. Backend (port 8000 pour matcher le proxy frontend)
```bash
cd backend && source venv/bin/activate
setsid nohup python -m uvicorn server:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 < /dev/null &
# health: curl http://localhost:8000/api/health → {"status":"ok"}
```

### 3. Frontend
```bash
cd frontend && npm start  # → http://localhost:3000
```

## Import des données réelles
```bash
cd backend && source venv/bin/activate
python import_clients_json.py --apply --purge   # 1014 clients depuis data_import/clients.json
python import_produits_json.py --apply --purge  # 56 produits depuis data_import/articles.json
```

## Compte admin (auto-seedé au démarrage)
- Email: `pissken@editionsfabsci.com`
- Password: `Admin@2025`
- Rôle: super_admin

## État vérifié (Session 6)
- ✅ Login E2E → /dashboard
- ✅ Dashboard: 1014 clients affichés
- ✅ Page Clients: 1014 clients réels (écoles, librairies, particuliers, distributeurs)
- ✅ Commandes: 3 commandes, CA 88 500 FCFA
- ✅ Factures, Produits (56): pages OK
