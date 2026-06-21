#!/usr/bin/env bash
# =============================================================================
# ERP FABS-CI — Script de démarrage tout-en-un
# Lance MongoDB + Redis + Backend + Frontend et importe les données
# (clients, produits, utilisateurs) si la base est vide.
#
# Usage:
#   ./start.sh             # démarrage normal (import auto si base vide)
#   ./start.sh --reimport  # force le réimport (purge + import des données)
# =============================================================================
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
MONGO_DATA="$HOME/mongodb_data"
MONGO_LOG="$HOME/mongodb_logs/mongod.log"

REIMPORT=false
[ "$1" == "--reimport" ] && REIMPORT=true

echo "════════════════════════════════════════════════"
echo "   ERP FABS-CI — Démarrage"
echo "════════════════════════════════════════════════"

# ── 1. MongoDB ───────────────────────────────────────────────────────────────
if ! pgrep -x mongod >/dev/null; then
  echo "▶ Démarrage MongoDB..."
  mkdir -p "$MONGO_DATA" "$(dirname "$MONGO_LOG")"
  if command -v tmux >/dev/null; then
    tmux kill-session -t mongo 2>/dev/null || true
    tmux new-session -d -s mongo "mongod --dbpath '$MONGO_DATA' --bind_ip 127.0.0.1 --port 27017 --logpath '$MONGO_LOG'"
  else
    mongod --dbpath "$MONGO_DATA" --bind_ip 127.0.0.1 --port 27017 --logpath "$MONGO_LOG" --fork
  fi
  sleep 5
else
  echo "✓ MongoDB déjà actif"
fi

# ── 2. Redis ─────────────────────────────────────────────────────────────────
if ! pgrep -x redis-server >/dev/null; then
  echo "▶ Démarrage Redis..."
  if command -v tmux >/dev/null; then
    tmux kill-session -t redis 2>/dev/null || true
    tmux new-session -d -s redis "redis-server --port 6379"
  else
    redis-server --port 6379 --daemonize yes
  fi
  sleep 2
else
  echo "✓ Redis déjà actif"
fi

# ── 3. Fichiers .env ─────────────────────────────────────────────────────────
if [ ! -f "$BACKEND/.env" ]; then
  echo "▶ Création backend/.env..."
  cat > "$BACKEND/.env" <<'EOF'
ENVIRONMENT=development
MONGO_URL=mongodb://localhost:27017
DB_NAME=fabsci_erp
REDIS_URL=redis://localhost:6379
JWT_SECRET=dev_secret_fabsci_local_2026_change_me
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7
CORS_ORIGINS=http://localhost:3000
SUPER_ADMIN_EMAIL=pissken@editionsfabsci.com
SUPER_ADMIN_PASSWORD=Admin@2024
EOF
fi
if [ ! -f "$FRONTEND/.env" ]; then
  echo "▶ Création frontend/.env..."
  # Pas de REACT_APP_BACKEND_URL : le proxy /api (setupProxy.js) pointe vers :8001
  echo "WDS_SOCKET_PORT=0" > "$FRONTEND/.env"
fi

# ── 4. Backend : venv + dépendances ──────────────────────────────────────────
cd "$BACKEND"
if [ ! -d venv ]; then
  echo "▶ Création venv backend + installation des dépendances..."
  python3 -m venv venv
  ./venv/bin/pip install --upgrade pip -q
  ./venv/bin/pip install -r requirements.txt -q
else
  echo "✓ venv backend déjà présent"
fi

# ── 5. Lancement du backend (port 8001) ──────────────────────────────────────
echo "▶ Démarrage backend (port 8001)..."
tmux kill-session -t backend 2>/dev/null || true
tmux new-session -d -s backend "cd '$BACKEND' && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001"
# Attente que l'API réponde
for i in $(seq 1 30); do
  if curl -s -o /dev/null http://localhost:8001/api/ 2>/dev/null; then break; fi
  sleep 1
done
echo "✓ Backend prêt"

# ── 6. Import des données (clients, produits, utilisateurs) ──────────────────
echo "▶ Vérification / import des données..."
cd "$BACKEND"
source venv/bin/activate

NB_CLIENTS=$(python3 -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017')['fabsci_erp']['clients'].count_documents({}))" 2>/dev/null || echo 0)
NB_PRODUITS=$(python3 -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017')['fabsci_erp']['produits'].count_documents({}))" 2>/dev/null || echo 0)

if [ "$REIMPORT" == "true" ]; then
  echo "  ↻ Réimport forcé (purge + import)..."
  python import_clients_json.py --purge --apply  || true
  python import_produits_json.py --purge --apply || true
  python import_users_roles.py --apply           || true
else
  # Clients : importer seulement si peu/pas de données réelles
  if [ "$NB_CLIENTS" -lt 100 ]; then
    echo "  • Import clients (base = $NB_CLIENTS)..."
    python import_clients_json.py --purge --apply || true
  else
    echo "  ✓ Clients déjà présents ($NB_CLIENTS)"
  fi
  # Produits
  if [ "$NB_PRODUITS" -lt 50 ]; then
    echo "  • Import produits (base = $NB_PRODUITS)..."
    python import_produits_json.py --purge --apply || true
  else
    echo "  ✓ Produits déjà présents ($NB_PRODUITS)"
  fi
  # Utilisateurs : script idempotent (skip si existant)
  echo "  • Vérification utilisateurs..."
  python import_users_roles.py --apply || true
fi

# ── 7. Frontend : dépendances + lancement (port 3000) ────────────────────────
cd "$FRONTEND"
if [ ! -d node_modules ]; then
  echo "▶ Installation des dépendances frontend (npm)..."
  npm install --legacy-peer-deps
else
  echo "✓ node_modules frontend déjà présent"
fi
echo "▶ Démarrage frontend (port 3000)..."
tmux kill-session -t frontend 2>/dev/null || true
tmux new-session -d -s frontend "cd '$FRONTEND' && PORT=3000 npm start"

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ ERP FABS-CI lancé"
echo "  • Frontend : http://localhost:3000"
echo "  • Backend  : http://localhost:8001/api/"
echo "  • Login    : pissken@editionsfabsci.com / Admin@2024"
echo "════════════════════════════════════════════════"
echo "  (le frontend met ~30-45s à compiler la 1ère fois)"
