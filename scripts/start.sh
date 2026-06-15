#!/bin/bash

# Script de démarrage pour Emergent IA - ERP FABS-CI V7

set -e

echo "Starting ERP FABS-CI V7 Backend..."

# Wait for MongoDB
echo "Waiting for MongoDB..."
until mongosh --eval "db.adminCommand('ping')" --quiet; do
  echo "MongoDB is unavailable - sleeping"
  sleep 2
done
echo "MongoDB is up"

# Wait for Redis
echo "Waiting for Redis..."
until redis-cli ping; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "Redis is up"

# Start the application
echo "Starting FastAPI server..."
cd /app
exec uvicorn server:app --host 0.0.0.0 --port 8001
