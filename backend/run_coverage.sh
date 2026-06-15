#!/bin/bash
# ERP FABS-CI - Test Coverage Script
# Measures test coverage for backend code

echo "Running test coverage analysis..."

# Install pytest-cov if not installed
pip install pytest-cov pytest-asyncio -q

# Run tests with coverage
pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    -v \
    --tb=short \
    --ignore=tests/test_sprints_8_15_fabsci.py \
    --ignore=tests/test_full_audit_iter8.py \
    --ignore=tests/test_full_audit_iter12.py

echo "Coverage report generated in htmlcov/"
echo "Open htmlcov/index.html in browser to view detailed report"
