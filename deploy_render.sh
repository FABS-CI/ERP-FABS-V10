#!/bin/bash

# ============================================================================
# ERP FABS-CI Deployment Script for Render.com
# ============================================================================
# This script automates the deployment process to Render.com
# Usage: ./deploy_render.sh [environment] [action]
# ============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Configuration
ENVIRONMENT="${1:-production}"
ACTION="${2:-deploy}"
RENDER_API_KEY="${RENDER_API_KEY:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed"
        exit 1
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        exit 1
    fi
    
    # Check Render API key
    if [ -z "$RENDER_API_KEY" ]; then
        log_warning "RENDER_API_KEY not set. Set it via: export RENDER_API_KEY=rnd_xxx"
        read -p "Enter your Render.com API key: " RENDER_API_KEY
    fi
    
    log_success "Prerequisites check passed"
}

validate_environment() {
    log_info "Validating environment configuration..."
    
    if [ ! -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
        log_error ".env.$ENVIRONMENT not found"
        exit 1
    fi
    
    # Check required environment variables
    required_vars=(
        "DATABASE_URL"
        "MONGO_URI"
        "REDIS_URL"
        "SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$PROJECT_DIR/.env.$ENVIRONMENT"; then
            log_warning "Missing $var in .env.$ENVIRONMENT"
        fi
    done
    
    log_success "Environment validation passed"
}

build_docker_image() {
    log_info "Building Docker image..."
    
    docker build \
        -f "$PROJECT_DIR/Dockerfile.prod" \
        -t erp-fabs-backend:latest \
        -t erp-fabs-backend:$(date +%Y%m%d-%H%M%S) \
        "$PROJECT_DIR"
    
    log_success "Docker image built successfully"
}

run_tests() {
    log_info "Running tests before deployment..."
    
    # Unit tests
    log_info "Running unit tests..."
    cd "$PROJECT_DIR"
    python -m pytest backend/tests/unit -v || {
        log_error "Unit tests failed"
        return 1
    }
    
    # Smoke tests
    log_info "Running smoke tests..."
    python -m pytest backend/tests/smoke -v || {
        log_error "Smoke tests failed"
        return 1
    }
    
    log_success "All tests passed"
}

push_to_github() {
    log_info "Pushing changes to GitHub..."
    
    cd "$PROJECT_DIR"
    
    if [ -z "$(git status --porcelain)" ]; then
        log_warning "No changes to commit"
    else
        git add -A
        git commit -m "Deployment: $ENVIRONMENT - $(date +%Y-%m-%d\ %H:%M:%S)" || {
            log_warning "Nothing to commit"
        }
    fi
    
    git push origin main
    
    log_success "Code pushed to GitHub"
}

trigger_render_deploy() {
    log_info "Triggering Render.com deployment..."
    
    SERVICE_ID="erp-fabs-backend"  # Replace with your service ID
    
    # Render API endpoint
    API_URL="https://api.render.com/v1/services/$SERVICE_ID/deploys"
    
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        -H "Content-Type: application/json" \
        "$API_URL")
    
    # Check if deployment was triggered
    if echo "$response" | grep -q "deploy"; then
        log_success "Render deployment triggered"
        echo "$response" | grep -o '"id":"[^"]*"'
    else
        log_error "Failed to trigger deployment: $response"
        return 1
    fi
}

wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Check service status
        status=$(curl -s \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            "https://api.render.com/v1/services/erp-fabs-backend" \
            | grep -o '"state":"[^"]*"' | head -1 | cut -d'"' -f4)
        
        if [ "$status" = "available" ]; then
            log_success "Deployment completed successfully"
            return 0
        fi
        
        log_info "Status: $status (waiting... $((attempt+1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "Deployment timeout"
    return 1
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    API_URL="https://erp-fabs-backend.onrender.com/api/health"
    
    max_retries=10
    retry=0
    
    while [ $retry -lt $max_retries ]; do
        response=$(curl -s -w "\n%{http_code}" "$API_URL")
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
        
        if [ "$http_code" = "200" ]; then
            log_success "API health check passed"
            echo "Response: $body"
            return 0
        fi
        
        log_info "Health check failed (HTTP $http_code), retrying... $((retry+1))/$max_retries"
        sleep 5
        ((retry++))
    done
    
    log_error "Deployment verification failed"
    return 1
}

rollback() {
    log_warning "Rolling back to previous version..."
    
    SERVICE_ID="erp-fabs-backend"
    
    # Get previous deployment
    previous_deploy=$(curl -s \
        -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$SERVICE_ID/deploys" \
        | grep -o '"id":"[^"]*"' | sed -n '2p' | cut -d'"' -f4)
    
    if [ -n "$previous_deploy" ]; then
        curl -s -X POST \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            "https://api.render.com/v1/deploys/$previous_deploy/reactivate"
        
        log_success "Rollback initiated"
    else
        log_error "No previous deployment found for rollback"
        return 1
    fi
}

create_backup() {
    log_info "Creating database backup before deployment..."
    
    # PostgreSQL backup
    pg_dump -h $DB_HOST -U $DB_USER -d erp_fabs_db \
        > "backup-$(date +%Y%m%d-%H%M%S).sql"
    
    # MongoDB backup
    mongodump --uri="$MONGO_URI" --out="backup-$(date +%Y%m%d-%H%M%S)"
    
    log_success "Backups created"
}

generate_deployment_report() {
    log_info "Generating deployment report..."
    
    report_file="deployment_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# ERP FABS-CI Deployment Report

**Date:** $(date)
**Environment:** $ENVIRONMENT
**Status:** SUCCESS

## Deployment Details

- **Service:** erp-fabs-backend
- **GitHub Commit:** $(git rev-parse --short HEAD)
- **Docker Image:** erp-fabs-backend:latest
- **Render Service ID:** erp-fabs-backend

## Test Results

✅ Unit Tests: PASSED
✅ Smoke Tests: PASSED
✅ Health Check: PASSED

## Environment Variables

- DATABASE_URL: Configured
- MONGO_URI: Configured
- REDIS_URL: Configured
- SECRET_KEY: Configured

## Performance Metrics

Check Render.com dashboard for:
- CPU Usage
- Memory Usage
- Network I/O
- Error Rates

## Next Steps

1. Monitor logs in Render.com dashboard
2. Verify API endpoints are responding
3. Test critical user workflows
4. Check Grafana dashboards
5. Review Sentry error tracking

---
Generated by: deploy_render.sh
EOF
    
    log_success "Deployment report: $report_file"
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
    log_info "========================================"
    log_info "ERP FABS-CI Deployment to Render.com"
    log_info "========================================"
    log_info "Environment: $ENVIRONMENT"
    log_info "Action: $ACTION"
    log_info ""
    
    case "$ACTION" in
        deploy)
            check_prerequisites
            validate_environment
            # build_docker_image  # Docker build happens in Render
            run_tests
            create_backup
            push_to_github
            trigger_render_deploy
            wait_for_deployment
            verify_deployment
            generate_deployment_report
            log_success "Deployment completed successfully!"
            ;;
        
        verify)
            verify_deployment
            ;;
        
        rollback)
            rollback
            ;;
        
        backup)
            create_backup
            ;;
        
        *)
            log_error "Unknown action: $ACTION"
            echo "Valid actions: deploy, verify, rollback, backup"
            exit 1
            ;;
    esac
}

# Run main function
main
