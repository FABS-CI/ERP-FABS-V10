#!/bin/bash
# Quick Deploy Script for ERP FABS V10 (TOUR 3)

set -e

echo "======================================"
echo "ERP FABS V10 - PRODUCTION DEPLOYMENT"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Validate Environment
echo -e "${YELLOW}1. Validating environment...${NC}"
if [ -z "$JWT_SECRET" ]; then
    echo -e "${RED}ERROR: JWT_SECRET not set${NC}"
    exit 1
fi

if [ -z "$MONGODB_URI" ]; then
    echo -e "${RED}ERROR: MONGODB_URI not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables OK${NC}"

# 2. Validate Code
echo -e "${YELLOW}2. Validating code...${NC}"
cd /home/user/ERP-FABS-V10
python3 validate_tour_3.py > /tmp/validation.log 2>&1

if grep -q "10/10 tests passed" /tmp/validation.log; then
    echo -e "${GREEN}✓ All tests passing (10/10)${NC}"
else
    echo -e "${RED}✗ Validation failed${NC}"
    cat /tmp/validation.log
    exit 1
fi

# 3. Create Database Indexes
echo -e "${YELLOW}3. Creating database indexes...${NC}"
python3 << 'PYTHON_END'
import sys
sys.path.insert(0, 'backend')
from database_schema import SchemaOptimizer
from pymongo import MongoClient
import os

try:
    client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
    db = client['fabs_ci']
    client.admin.command('ping')
    
    count = 0
    for idx in SchemaOptimizer.get_all_indexes():
        try:
            db[idx.collection].create_index(idx.fields)
            count += 1
        except:
            pass
    
    print(f"✓ Created {count} indexes")
    client.close()
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)
PYTHON_END

# 4. Start Application
echo -e "${YELLOW}4. Starting application...${NC}"
nohup python3 -m uvicorn backend.app_production:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    > /var/log/erp/app.log 2>&1 &

PID=$!
echo "Started with PID: $PID"
sleep 3

# 5. Health Check
echo -e "${YELLOW}5. Running health check...${NC}"
HEALTH=$(curl -s http://localhost:8000/health | grep -o '"overall_status":"[^"]*"' || echo 'failed')

if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Health check PASSED${NC}"
else
    echo -e "${YELLOW}⚠ Health check returned: $HEALTH${NC}"
fi

# 6. Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "======================================"
echo "App running on: http://localhost:8000"
echo "Health: http://localhost:8000/health"
echo "Metrics: http://localhost:8000/metrics"
echo "Dashboard: http://localhost:8000/dashboard"
echo ""
echo "Logs: /var/log/erp/app.log"
echo "PID: $PID"
echo ""
echo "To stop: kill $PID"
echo "======================================"
