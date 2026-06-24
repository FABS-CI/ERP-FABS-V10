#!/bin/bash
# Run Complete Business Validation

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "ERP FABS-CI — VALIDATION RUNNER"
echo "=========================================="

# Check if backend is already running
echo "[1/3] Checking backend..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend already running on port 8000"
    BACKEND_RUNNING=true
else
    echo "⚠️  Backend not running. Attempting to start..."
    BACKEND_RUNNING=false
fi

# Start backend if needed
if [ "$BACKEND_RUNNING" = false ]; then
    echo "[2/3] Starting backend..."
    cd backend
    python3 app_simple.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to be ready
    echo "⏳ Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Backend failed to start"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
fi

# Run validation
echo "[3/3] Running validation tests..."
python3 complete_business_validation.py

echo ""
echo "=========================================="
echo "✅ Validation Complete!"
echo "Check VALIDATION_REPORT.md for results"
echo "=========================================="

# Cleanup
if [ "$BACKEND_RUNNING" = false ] && [ -n "$BACKEND_PID" ]; then
    echo "Shutting down backend..."
    kill $BACKEND_PID 2>/dev/null || true
fi
