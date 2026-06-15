"""
Script de configuration pour l'environnement de production ERP FABS V7

Ce script génère les fichiers .env nécessaires pour le backend et le frontend
avec des valeurs sécurisées pour la production.

Usage:
    python scripts/setup_production_env.py --domain votre-domaine.com
"""

import secrets
import sys
import os
from pathlib import Path

def generate_jwt_secret():
    """Génère un secret JWT fort"""
    return secrets.token_urlsafe(32)

def generate_strong_password(length=16):
    """Génère un mot de passe fort"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def setup_backend_env(domain):
    """Configure le fichier .env pour le backend"""
    backend_dir = Path(__file__).parent.parent / "backend"
    env_file = backend_dir / ".env"
    
    jwt_secret = generate_jwt_secret()
    mongo_password = generate_strong_password()
    super_admin_password = generate_strong_password()
    dg_password = generate_strong_password()
    
    env_content = f"""# ERP FABS-CI - Environment Variables Configuration
# AUTO-GENERATED FOR PRODUCTION - {domain}
# Date: {os.popen('date /t').read().strip()}

# ============================================================================
# ENVIRONMENT
# ============================================================================
ENVIRONMENT=production

# ============================================================================
# DATABASE - MongoDB
# ============================================================================
MONGO_URL=mongodb://admin:{mongo_password}@mongodb:27017
DB_NAME=fabsci_erp

# ============================================================================
# REDIS - Cache
# ============================================================================
REDIS_URL=redis://redis:6379

# ============================================================================
# JWT - Authentication
# ============================================================================
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7

# ============================================================================
# CORS - Cross-Origin Resource Sharing
# ============================================================================
CORS_ORIGINS=https://{domain},https://www.{domain}

# ============================================================================
# DEFAULT USER CREDENTIALS (SEEDING)
# ============================================================================
SUPER_ADMIN_EMAIL=pissken@editionsfabsci.com
SUPER_ADMIN_PASSWORD={super_admin_password}
SUPER_ADMIN_NAME=AKE APPIA YVES DORIS

DG_EMAIL=ali.mamin@editionsfabsci.com
DG_PASSWORD={dg_password}
DG_NAME=ALI MAMIN

# ============================================================================
# BACKUP - MongoDB Backup
# ============================================================================
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=./backups

# ============================================================================
# S3 - External Backup (Optional)
# ============================================================================
S3_ENABLED=false
S3_BUCKET=your-backup-bucket
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-1

# ============================================================================
# EMAIL - SMTP Configuration (Optional)
# ============================================================================
SMTP_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@editionsfabsci.com

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO

# ============================================================================
# MONITORING
# ============================================================================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# ============================================================================
# SECURITY
# ============================================================================
FORCE_HTTPS=true
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Backend .env créé: {env_file}")
    print(f"   JWT_SECRET: {jwt_secret[:20]}...")
    print(f"   MongoDB Password: {mongo_password[:20]}...")
    print(f"   Super Admin Password: {super_admin_password[:20]}...")
    print(f"   DG Password: {dg_password[:20]}...")
    
    return {
        "jwt_secret": jwt_secret,
        "mongo_password": mongo_password,
        "super_admin_password": super_admin_password,
        "dg_password": dg_password
    }

def setup_frontend_env(domain):
    """Configure le fichier .env pour le frontend"""
    frontend_dir = Path(__file__).parent.parent / "frontend"
    env_file = frontend_dir / ".env"
    
    env_content = f"""# ERP FABS-CI - Frontend Environment Variables
# AUTO-GENERATED FOR PRODUCTION - {domain}
# Date: {os.popen('date /t').read().strip()}

REACT_APP_API_BASE_URL=https://{domain}/api
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Frontend .env créé: {env_file}")
    print(f"   API Base URL: https://{domain}/api")

def setup_docker_env(domain, secrets):
    """Configure le fichier .env pour Docker Compose"""
    root_dir = Path(__file__).parent.parent
    env_file = root_dir / ".env"
    
    env_content = f"""# ERP FABS-CI - Docker Compose Environment Variables
# AUTO-GENERATED FOR PRODUCTION - {domain}
# Date: {os.popen('date /t').read().strip()}

MONGO_ROOT_PASSWORD={secrets['mongo_password']}
JWT_SECRET={secrets['jwt_secret']}
CORS_ORIGINS=https://{domain},https://www.{domain}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Docker .env créé: {env_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_production_env.py --domain votre-domaine.com")
        sys.exit(1)
    
    if sys.argv[1] != "--domain":
        print("Usage: python setup_production_env.py --domain votre-domaine.com")
        sys.exit(1)
    
    domain = sys.argv[2]
    
    print("=" * 60)
    print("Configuration Production ERP FABS V7")
    print(f"Domaine: {domain}")
    print("=" * 60)
    print()
    
    # Configuration backend
    secrets = setup_backend_env(domain)
    print()
    
    # Configuration frontend
    setup_frontend_env(domain)
    print()
    
    # Configuration Docker
    setup_docker_env(domain, secrets)
    print()
    
    print("=" * 60)
    print("✅ Configuration terminée avec succès!")
    print("=" * 60)
    print()
    print("📝 IMPORTANT: Sauvegardez les mots de passe suivants:")
    print(f"   Super Admin: pissken@editionsfabsci.com / {secrets['super_admin_password']}")
    print(f"   DG: ali.mamin@editionsfabsci.com / {secrets['dg_password']}")
    print()
    print("🔒 Ces mots de passe ne seront plus affichés!")
    print()
    print("🚀 Prochaine étape: Exécutez la migration MongoDB")
    print("   python backend/migrations/create_fournisseurs_approvisionnements.py")

if __name__ == "__main__":
    main()
