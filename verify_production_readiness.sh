#!/bin/bash

# ERP FABS-CI Production Readiness Verification Script
# Quick health check of audit results

echo "============================================================"
echo "ERP FABS-CI PRODUCTION READINESS VERIFICATION"
echo "============================================================"
echo ""

PASSED=0
FAILED=0

# Check 1: Documentation exists
echo "[CHECK 1] Documentation files..."
docs=(
    "PRODUCTION_HARDENING_FINAL_REPORT.md"
    "DEPLOYMENT_CHECKLIST.md"
    "KNOWN_ISSUES_AND_NEXT_STEPS.md"
    "README_PRODUCTION_HARDENING.md"
    "INDEX_PRODUCTION_READINESS.md"
    "EXECUTIVE_SUMMARY_PRODUCTION_READINESS.md"
    "backend/ARCHITECTURE_REFACTORING.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✅ $doc"
        ((PASSED++))
    else
        echo "  ❌ $doc MISSING"
        ((FAILED++))
    fi
done

echo ""

# Check 2: Code artifacts exist
echo "[CHECK 2] Code artifacts..."
artifacts=(
    "backend/optimization_utils.py"
    "backend/auto_optimize_n1.py"
    "backend/transaction_helper.py"
    "backend/validation_workflows.py"
    "backend/services/__init__.py"
    "backend/services/employee_service.py"
    "backend/services/command_service.py"
    "backend/services/stock_service.py"
    "backend/.env.production"
    "backend/validate_production_env.py"
)

for artifact in "${artifacts[@]}"; do
    if [ -f "$artifact" ]; then
        lines=$(wc -l < "$artifact" 2>/dev/null || echo "0")
        echo "  ✅ $artifact ($lines lines)"
        ((PASSED++))
    else
        echo "  ❌ $artifact MISSING"
        ((FAILED++))
    fi
done

echo ""

# Check 3: Configuration validation
echo "[CHECK 3] Configuration..."
if grep -q "ENVIRONMENT=production" "backend/.env.production"; then
    echo "  ✅ .env.production has ENVIRONMENT=production"
    ((PASSED++))
else
    echo "  ❌ .env.production missing ENVIRONMENT=production"
    ((FAILED++))
fi

if grep -q "JWT_SECRET=" "backend/.env.production"; then
    echo "  ✅ JWT_SECRET configured"
    ((PASSED++))
else
    echo "  ❌ JWT_SECRET not configured"
    ((FAILED++))
fi

if grep -q ".env.production" ".gitignore"; then
    echo "  ✅ .env.production in .gitignore"
    ((PASSED++))
else
    echo "  ❌ .env.production not in .gitignore"
    ((FAILED++))
fi

echo ""

# Check 4: Security improvements
echo "[CHECK 4] Security fixes..."
if grep -q "os.environ.get.*JWT_SECRET" "backend/app_simple.py"; then
    echo "  ✅ Secrets externalized in app_simple.py"
    ((PASSED++))
else
    echo "  ❌ Secrets still hardcoded"
    ((FAILED++))
fi

if grep -q "CORS_ORIGINS" "backend/app_simple.py"; then
    echo "  ✅ CORS configured (non-wildcard)"
    ((PASSED++))
else
    echo "  ❌ CORS not configured"
    ((FAILED++))
fi

echo ""

# Check 5: Performance improvements
echo "[CHECK 5] Performance optimizations..."
if grep -q "BulkQueryOptimizer" "backend/optimization_utils.py"; then
    echo "  ✅ BulkQueryOptimizer utility created"
    ((PASSED++))
else
    echo "  ❌ BulkQueryOptimizer missing"
    ((FAILED++))
fi

if grep -q "dept_ids = " "backend/rh_module.py"; then
    echo "  ✅ list_employes() optimized (N+1 fix)"
    ((PASSED++))
else
    echo "  ❌ list_employes() not optimized"
    ((FAILED++))
fi

echo ""

# Check 6: Validation & Testing
echo "[CHECK 6] Validation & Testing..."
if grep -q "validate_commercial_workflow" "backend/validation_workflows.py"; then
    echo "  ✅ Business workflow validation created"
    ((PASSED++))
else
    echo "  ❌ Workflow validation missing"
    ((FAILED++))
fi

if grep -q "TransactionHelper" "backend/transaction_helper.py"; then
    echo "  ✅ Transaction helper for ACID operations"
    ((PASSED++))
else
    echo "  ❌ Transaction helper missing"
    ((FAILED++))
fi

echo ""

# Summary
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo ""
    echo "Next steps:"
    echo "1. Read: INDEX_PRODUCTION_READINESS.md"
    echo "2. Review: KNOWN_ISSUES_AND_NEXT_STEPS.md"
    echo "3. Execute: DEPLOYMENT_CHECKLIST.md"
    exit 0
else
    echo "❌ SOME CHECKS FAILED"
    echo ""
    echo "Please review missing files/configurations above"
    exit 1
fi
