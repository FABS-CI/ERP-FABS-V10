#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
export PYTHONUNBUFFERED=1
export PORT=${PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-production}

source ../.env 2>/dev/null || true

exec gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "server:app"
