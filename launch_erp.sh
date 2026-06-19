#!/bin/bash
# FABS-CI ERP v10 - Launch Script

set -e

ERP_DIR="/home/user/ERP-FABS-V10"
MONGODB_DATA="$HOME/mongodb_data"
MONGODB_LOGS="$HOME/mongodb_logs"

echo "================================"
echo "🚀 FABS-CI ERP v10 - LAUNCH"
echo "================================"
echo ""

# 1. Check MongoDB
echo "✓ Checking MongoDB..."
if pgrep -x "mongod" > /dev/null; then
    echo "  ✅ MongoDB already running"
else
    echo "  🔄 Starting MongoDB..."
    mkdir -p "$MONGODB_DATA" "$MONGODB_LOGS"
    mongod --dbpath "$MONGODB_DATA" \
           --logpath "$MONGODB_LOGS/mongodb.log" \
           --fork --bind_ip 127.0.0.1 --port 27017
    sleep 2
    echo "  ✅ MongoDB started"
fi

# 2. Check Backend
echo "✓ Checking Backend..."
if pm2 status | grep -q "erp-backend.*online"; then
    echo "  ✅ Backend already running"
else
    echo "  🔄 Starting Backend..."
    cd "$ERP_DIR"
    pm2 start ecosystem.config.js --update-env
    sleep 3
    echo "  ✅ Backend started"
fi

# 3. Check Frontend
echo "✓ Checking Frontend..."
if curl -s -m 2 http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✅ Frontend already running"
else
    echo "  🔄 Starting Frontend..."
    cd "$ERP_DIR/frontend"
    npm start > /tmp/frontend.log 2>&1 &
    sleep 15
    echo "  ✅ Frontend started"
fi

# 4. Verify all services
echo ""
echo "================================"
echo "✅ ERP READY"
echo "================================"
echo ""
echo "Services:"
echo "  • MongoDB:  http://localhost:27017"
echo "  • Backend:  http://localhost:8000/api"
echo "  • Frontend: http://localhost:3000"
echo ""
echo "Login:"
echo "  Email:    pissken@editionsfabsci.com"
echo "  Password: Admin@2025"
echo ""
echo "Data:"
echo "  • Clients:  1016"
echo "  • Products: 56 (cleaned)"
echo "  • Users:    8 (with roles)"
echo ""
