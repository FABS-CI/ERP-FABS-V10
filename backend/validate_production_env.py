#!/usr/bin/env python3
"""
Validate Production Environment Configuration
Ensures all required secrets are properly externalized.
"""

import os
import sys
from pathlib import Path

# Required production environment variables
REQUIRED_VARS = {
    'ENVIRONMENT': 'production',
    'JWT_SECRET': (64, 'string'),  # (min_length, type)
    'MONGO_URL': 'string',
    'REDIS_URL': 'string',
    'CORS_ORIGINS': 'string',
    'LOG_LEVEL': 'string',
    'PROMETHEUS_ENABLED': 'bool',
}

DANGEROUS_DEFAULTS = {
    'Admin@2025',
    'DG@2025',
    'dev-secret-key-2026',
    'localhost',
    '127.0.0.1',
    'mongodb://localhost',
    'redis://localhost',
    'allow_origins=["*"]',
}

def validate_env():
    """Validate production environment."""
    
    print("=" * 60)
    print("PRODUCTION ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    env = os.environ.get('ENVIRONMENT', 'development')
    
    if env != 'production':
        warnings.append(f"⚠️  ENVIRONMENT={env} (not production mode)")
    
    # Check required variables
    for var, spec in REQUIRED_VARS.items():
        value = os.environ.get(var)
        
        if not value:
            errors.append(f"🔴 MISSING: {var}")
            continue
        
        # Type and length checks
        if isinstance(spec, tuple):
            min_len, var_type = spec
            if var_type == 'string' and len(value) < min_len:
                errors.append(f"🔴 {var}: Too short (min {min_len} chars, got {len(value)})")
        
        # Check for dangerous values
        for danger in DANGEROUS_DEFAULTS:
            if danger in value:
                errors.append(f"🔴 {var}: Contains dangerous default value '{danger}'")
    
    # Specific checks
    
    # 1. JWT Secret must be random
    jwt_secret = os.environ.get('JWT_SECRET', '')
    if jwt_secret and not any(c in jwt_secret for c in '0123456789abcdef'):
        warnings.append("⚠️  JWT_SECRET looks short on entropy")
    
    # 2. CORS must not be wildcard
    cors = os.environ.get('CORS_ORIGINS', '')
    if cors == '*' or '*' in cors:
        errors.append("🔴 CORS_ORIGINS: Wildcard not allowed in production")
    
    # 3. MongoDB URL must NOT be localhost
    mongo_url = os.environ.get('MONGO_URL', '')
    if 'localhost' in mongo_url or '127.0.0.1' in mongo_url:
        errors.append("🔴 MONGO_URL: Localhost not allowed in production")
    
    # 4. Redis URL must NOT be localhost
    redis_url = os.environ.get('REDIS_URL', '')
    if 'localhost' in redis_url or '127.0.0.1' in redis_url:
        errors.append("🔴 REDIS_URL: Localhost not allowed in production")
    
    # 5. HTTPS must be enforced
    if env == 'production':
        hsts = os.environ.get('SECURE_HSTS_SECONDS')
        if not hsts:
            warnings.append("⚠️  SECURE_HSTS_SECONDS not set (HTTPS hardening)")
    
    # 6. Rate limiting must be enabled
    rate_limit = os.environ.get('RATE_LIMIT_ENABLED', 'false').lower()
    if rate_limit != 'true':
        warnings.append("⚠️  RATE_LIMIT_ENABLED not enabled")
    
    # Print results
    print()
    if errors:
        print("❌ CRITICAL ERRORS:")
        for err in errors:
            print(f"  {err}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warn in warnings:
            print(f"  {warn}")
        print()
    
    if not errors and not warnings:
        print("✅ Production environment is properly configured!")
    
    # Return status
    if errors:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED — Fix errors before deploying")
        print("=" * 60)
        return False
    
    print("\n" + "=" * 60)
    if warnings:
        print("⚠️  VALIDATION PASSED with warnings")
    else:
        print("✅ VALIDATION PASSED")
    print("=" * 60)
    return True


if __name__ == '__main__':
    load_env_file = '.env.production'
    if Path(load_env_file).exists():
        from dotenv import load_dotenv
        load_dotenv(load_env_file)
        print(f"Loaded {load_env_file}")
    
    success = validate_env()
    sys.exit(0 if success else 1)
