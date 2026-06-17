#!/bin/sh
# Injecte BACKEND_URL dans la config nginx au démarrage du container
# Railway fournit BACKEND_URL comme variable d'environnement

set -e

if [ -z "$BACKEND_URL" ]; then
  echo "❌ ERREUR: BACKEND_URL non définie. Ex: https://backend-xxx.railway.app"
  exit 1
fi

echo "🔧 Injection BACKEND_URL=$BACKEND_URL dans nginx..."

# Substituer ${BACKEND_URL} dans le template nginx
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf.rendered
cp /tmp/nginx.conf.rendered /etc/nginx/conf.d/default.conf

echo "✅ Config nginx prête"
nginx -t && exec nginx -g "daemon off;"
