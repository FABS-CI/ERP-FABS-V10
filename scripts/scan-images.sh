#!/bin/bash

# Phase 3.6: Container Image Security Scanning
# Scans Docker images for vulnerabilities using Trivy

set -e

IMAGE_REGISTRY="${1:-docker.io}"
IMAGE_NAME="${2:-fabsci/backend}"
IMAGE_TAG="${3:-latest}"
FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🔍 Container Image Security Scanning"
echo "=================================="
echo "Image: $FULL_IMAGE"
echo ""

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "❌ Trivy not found. Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
    exit 1
fi

TRIVY_VERSION=$(trivy --version | grep -oP '(\d+\.\d+\.\d+)')
echo "✅ Trivy version: $TRIVY_VERSION"
echo ""

# ====================================================================
# Scan 1: Configuration Scanning
# ====================================================================
echo "📋 Scanning Docker configuration..."
trivy config Dockerfile.prod \
    --severity HIGH,CRITICAL \
    --exit-code 1 \
    --format json \
    --output trivy-config-report.json || true

# ====================================================================
# Scan 2: Image Scanning
# ====================================================================
echo "📦 Scanning container image for vulnerabilities..."
trivy image \
    "$FULL_IMAGE" \
    --severity HIGH,CRITICAL \
    --skip-files "**/requirements.txt" \
    --format json \
    --output trivy-image-report.json

# ====================================================================
# Scan 3: Detect secrets
# ====================================================================
echo "🔐 Scanning for secrets..."
trivy fs . \
    --scanners secret \
    --format json \
    --output trivy-secrets-report.json || true

# ====================================================================
# Generate Summary
# ====================================================================
echo ""
echo "📊 Scan Summary"
echo "==============="

CONFIG_ISSUES=$(jq '.Results | length' trivy-config-report.json 2>/dev/null || echo 0)
echo "Configuration issues: $CONFIG_ISSUES"

IMAGE_VULNS=$(jq '.Results[0].Misconfigurations | length' trivy-image-report.json 2>/dev/null || echo 0)
echo "Image vulnerabilities: $IMAGE_VULNS"

SECRETS=$(jq '.Results | length' trivy-secrets-report.json 2>/dev/null || echo 0)
echo "Secrets detected: $SECRETS"

# ====================================================================
# Fail if critical vulnerabilities found
# ====================================================================
if [ "$IMAGE_VULNS" -gt 0 ]; then
    echo ""
    echo "❌ CRITICAL: Vulnerabilities found in image"
    echo "Review report: trivy-image-report.json"
    exit 1
fi

if [ "$SECRETS" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Secrets detected in codebase"
    echo "Review report: trivy-secrets-report.json"
fi

echo ""
echo "✅ Image scanning complete"
echo "Reports:"
echo "  - trivy-config-report.json"
echo "  - trivy-image-report.json"
echo "  - trivy-secrets-report.json"
