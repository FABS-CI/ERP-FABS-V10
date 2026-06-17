"""
ERP EDITIONS FABS-CI — Backend Server
FastAPI + Motor (MongoDB) + JWT Auth + RBAC
"""

import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import jwt
import bcrypt
import re
import html

from fastapi import FastAPI, APIRouter, HTTPException, Header, Request, Response, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, Field, field_validator
from dotenv import load_dotenv
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator

# Import all ERP modules
from clients_module import build_clients_router, seed_clients
from products_module import build_products_router, seed_real_products
from commandes_module import build_commandes_router, seed_commandes
from factures_module import build_factures_router, seed_factures
from paiements_module import build_paiements_router, seed_paiements
from stock_module import build_stock_router, seed_mouvements_stock
from bons_livraison_module import build_bons_livraison_router, seed_bons_livraison
from bons_retour_module import build_bons_retour_router, seed_bons_retour
from comptabilite_module import build_comptabilite_router, seed_comptabilite
from administration_module import build_utilisateurs_router, build_parametres_router, seed_parametres
from recherche_module import build_recherche_router
from documents_ai_module import build_documents_ai_router, seed_documents_demo
from analytics_module import build_analytics_router
from colisage_module import build_colisage_router
from notifications_module import build_notifications_router
from logistique_module import build_logistique_router
from comptabilite_avancee_module import build_comptabilite_avancee_router
from fleet_module import build_fleet_router
from logistics_costs_module import build_logistics_costs_router
from multi_channel_notifications_module import build_multi_channel_notifications_router
from bi_analytics_module import build_bi_analytics_router
from workflow_approvals_module import build_workflow_approvals_router
from file_storage_module import build_file_storage_router
from backup_module import build_backup_router
from twofa_module import build_twofa_router
from dashboard_data import build_dashboard_payload
from rh_module import build_rh_router, seed_rh_data
from document_settings_module import router as document_settings_router
from fne_module import router as fne_router
from fournisseurs_module import router as fournisseurs_router
from approvisionnement_module import router as approvisionnement_router
from proformas_module import build_proformas_router
from rapports_module import build_rapports_router
from paie_module import router as paie_router
from scripts.seed_comptabilite import seed_journaux_et_plan_comptable

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fabsci.server")

# MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'fabsci_erp')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Redis Config
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

# JWT Config
# In production, JWT_SECRET must be set via environment variable
env = os.environ.get('ENVIRONMENT', 'development')
JWT_SECRET = os.environ.get('JWT_SECRET')
if env == 'production' and not JWT_SECRET:
    raise ValueError(
        "JWT_SECRET environment variable is required in production. "
        "Set a strong secret using: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
if not JWT_SECRET:
    JWT_SECRET = 'fabsci-secret-key-change-in-development-only'
    logger.warning("⚠️  Using default JWT_SECRET for development. Set JWT_SECRET in production!")
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRY_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRY_MINUTES', '30'))
JWT_REFRESH_TOKEN_EXPIRY_DAYS = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRY_DAYS', '7'))

# Password validation regex (min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit, 1 special)
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

# CORS - Use environment-based whitelist
# Default to localhost for development, restrict in production
if env == 'production':
    cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    if not cors_origins:
        logger.error("❌ CORS_ORIGINS not set in production. No CORS origins allowed!")
        cors_origins = []  # Empty list = no CORS allowed
else:
    # Development: allow localhost + all Runable preview domains
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

# ============================================================================
# INPUT SANITIZATION
# ============================================================================
def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS and injection attacks"""
    if not value:
        return value
    
    # HTML escape to prevent XSS
    sanitized = html.escape(value)
    
    # Remove potentially dangerous patterns
    # Remove script tags and event handlers
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    # Remove SQL injection patterns (basic)
    sanitized = re.sub(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE|TRUNCATE)\b)', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def sanitize_dict(data: dict) -> dict:
    """Recursively sanitize all string values in a dictionary"""
    if not data:
        return data
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_string(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Remove server information
        response.headers["Server"] = "ERP-FABS-CI"
        
        return response

# ============================================================================
# AUTH UTILITIES
# ============================================================================
async def log_audit_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """
    Log audit event to database
    """
    try:
        audit_doc = {
            "audit_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user_id[:8]}",
            "user_id": user_id,
            "action": action,  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, etc.
            "resource_type": resource_type,  # user, client, produit, commande, etc.
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await db.audit_logs.insert_one(audit_doc)
        logger.info(f"AUDIT: {action} on {resource_type} by {user_id}")
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")


# ============================================================================
# CACHE UTILITIES
# ============================================================================
async def get_cached(key: str) -> Optional[str]:
    """Get value from Redis cache"""
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None


async def set_cached(key: str, value: str, ttl: int = 300) -> None:
    """Set value in Redis cache with TTL (default 5 minutes)"""
    try:
        await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.error(f"Redis set error: {e}")


async def invalidate_cache(pattern: str) -> None:
    """Invalidate cache keys matching pattern"""
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.error(f"Redis invalidate error: {e}")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    """Create JWT access token"""
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRY_MINUTES)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": exp
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_preauth_token(user_id: str, email: str, role: str) -> str:
    """Token temporaire 2FA pré-auth (5 min, scope limité)"""
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "scope": "2fa_pending",
        "exp": exp
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    exp = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRY_DAYS)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": exp
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

async def resolve_user(request: Request, authorization: Optional[str] = None) -> dict:
    """
    Resolve current user from Authorization header or cookie
    Returns user dict with: user_id, email, nom_complet, role, actif
    """
    token = None
    
    # Try Authorization header first (Bearer token)
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ')[1]
    
    # Fallback to cookie
    if not token:
        token = request.cookies.get('session_token')
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    # Decode JWT
    payload = decode_jwt_token(token)
    
    # Fetch user from database
    user = await db.users.find_one(
        {"user_id": payload['user_id']},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    if not user.get('actif', True):
        raise HTTPException(status_code=403, detail="Compte désactivé")

    # Injecter le scope du token (ex: "2fa_pending") dans le dict retourné
    if payload.get("scope"):
        user = dict(user)
        user["scope"] = payload["scope"]

    return user

# ============================================================================
# PYDANTIC MODELS
# ============================================================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def sanitize_email(cls, v):
        return sanitize_string(v)

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    twofa_pending: Optional[bool] = None        # True → saisir le code OTP
    twofa_setup_required: Optional[bool] = None  # True → activer le 2FA d'abord

class UserProfile(BaseModel):
    user_id: str
    email: EmailStr
    nom_complet: str
    role: str
    actif: bool
    picture: Optional[str] = None
    created_at: str
    updated_at: Any  # peut être str ou datetime selon le driver

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context) -> None:
        # Normalise updated_at en str ISO si c'est un datetime
        if hasattr(self.updated_at, 'isoformat'):
            object.__setattr__(self, 'updated_at', self.updated_at.isoformat())


VALID_ROLES = {
    "super_admin", "directeur_general", "comptable",
    "directeur_commercial", "gestionnaire_stock",
    "responsable_magasinier", "secretariat", "assistante",
    "service_logistique",
}


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    nom_complet: str = Field(..., min_length=2, max_length=120)
    role: str = Field(..., description="Un des rôles valides")
    actif: bool = True

    @field_validator('email', 'nom_complet')
    @classmethod
    def sanitize_strings(cls, v):
        return sanitize_string(v)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if env == 'production':
            import re
            if not re.match(PASSWORD_REGEX, v):
                raise ValueError(
                    "Le mot de passe doit contenir au moins 8 caractères, "
                    "une majuscule, une minuscule, un chiffre et un caractère spécial (@$!%*?&)"
                )
        return v


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if env == 'production':
            import re
            if not re.match(PASSWORD_REGEX, v):
                raise ValueError(
                    "Le mot de passe doit contenir au moins 8 caractères, "
                    "une majuscule, une minuscule, un chiffre et un caractère spécial (@$!%*?&)"
                )
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ============================================================================
# FASTAPI APP
# ============================================================================
# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ERP EDITIONS FABS-CI API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add GZip middleware for compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Prometheus metrics — désactivé en production (faille sécurité : exposition publique)
# Pour activer en dev uniquement : PROMETHEUS_ENABLED=true dans .env
PROMETHEUS_ENABLED = os.environ.get("PROMETHEUS_ENABLED", "false").lower() == "true"
if PROMETHEUS_ENABLED:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics actif sur /metrics (dev uniquement)")
else:
    logger.info("Prometheus metrics désactivé (production)")

# CORS Middleware — fix E2: refuser par défaut si ENVIRONMENT non défini
# En dev uniquement (explicitement), ouvrir tout; sinon whitelist stricte
_cors_allow_all = (env == "development")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_allow_all else cors_origins,
    allow_credentials=False if _cors_allow_all else True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Main API router with /api prefix
api_router = APIRouter(prefix="/api")

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================
# Constantes lockout
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 900  # 15 minutes

@api_router.post("/auth/login")
@limiter.limit("20/minute")  # Limit login attempts
async def login(request: Request, response: Response, credentials: LoginRequest = Body(...)):
    """
    Login with email/password
    Sets JWT token in httpOnly cookie
    """
    lockout_key = f"lockout:{credentials.email}"
    attempts_key = f"login_attempts:{credentials.email}"

    # Vérifier si le compte est verrouillé
    try:
        is_locked = await redis_client.get(lockout_key)
        if is_locked:
            ttl = await redis_client.ttl(lockout_key)
            raise HTTPException(
                status_code=429,
                detail=f"Compte temporairement bloqué après trop de tentatives. Réessayez dans {ttl // 60} min {ttl % 60} sec."
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis indisponible — on continue sans lockout

    # Find user
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    async def record_failed_attempt():
        try:
            attempts = await redis_client.incr(attempts_key)
            await redis_client.expire(attempts_key, LOGIN_LOCKOUT_SECONDS)
            if int(attempts) >= LOGIN_MAX_ATTEMPTS:
                await redis_client.setex(lockout_key, LOGIN_LOCKOUT_SECONDS, "1")
                await redis_client.delete(attempts_key)
        except Exception:
            pass

    if not user:
        await record_failed_attempt()
        await log_audit_event(
            user_id="anonymous",
            action="LOGIN_FAILED",
            resource_type="auth",
            details={"email": credentials.email},
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    # Verify password (if password field exists)
    if 'password_hash' in user:
        if not verify_password(credentials.password, user['password_hash']):
            await record_failed_attempt()
            await log_audit_event(
                user_id=user['user_id'],
                action="LOGIN_FAILED",
                resource_type="auth",
                details={"email": credentials.email},
                ip_address=request.client.host if request.client else None
            )
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    else:
        # For backward compatibility - allow login without password hash
        # This is for Google OAuth users
        pass

    # Connexion réussie — réinitialiser le compteur
    try:
        await redis_client.delete(attempts_key)
        await redis_client.delete(lockout_key)
    except Exception:
        pass
    
    if not user.get('actif', True):
        raise HTTPException(status_code=403, detail="Compte désactivé")
    
    # Create JWT access token and refresh token
    access_token = create_jwt_token(user['user_id'], user['email'], user['role'])
    refresh_token = create_refresh_token(user['user_id'])
    
    # Store refresh token in database
    refresh_token_doc = {
        "refresh_token": refresh_token,
        "user_id": user['user_id'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRY_DAYS)).isoformat(),
        "revoked": False
    }
    await db.refresh_tokens.insert_one(refresh_token_doc)
    
    # Set httpOnly cookie (secure in production)
    is_production = os.environ.get('ENVIRONMENT', 'development') == 'production'
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=JWT_ACCESS_TOKEN_EXPIRY_MINUTES * 60  # Convert minutes to seconds
    )
    
    # Log successful login
    await log_audit_event(
        user_id=user['user_id'],
        action="LOGIN_SUCCESS",
        resource_type="auth",
        details={"email": user['email'], "role": user['role']},
        ip_address=request.client.host if request.client else None
    )
    
    # Return user info with tokens
    user_info = {
        "user_id": user['user_id'],
        "email": user['email'],
        "nom_complet": user['nom_complet'],
        "role": user['role'],
        "actif": user['actif'],
        "picture": user.get('picture'),
    }

    # ── Vérification 2FA obligatoire ────────────────────────────────────────
    from twofa_module import ROLES_2FA_REQUIRED
    if user['role'] in ROLES_2FA_REQUIRED:
        db_user = await db.users.find_one({"user_id": user['user_id']}, {"_id": 0})
        twofa_enabled = db_user.get("twofa_enabled", False) if db_user else False

        if not twofa_enabled:
            # 2FA obligatoire mais pas encore configuré → forcer le setup
            # On retourne quand même le vrai token pour accéder à /parametres uniquement
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=JWT_ACCESS_TOKEN_EXPIRY_MINUTES * 60,
                user=user_info,
                twofa_setup_required=True
            )
        else:
            # 2FA activé → retourner un token pré-auth, pas de cookie complet
            preauth_token = create_preauth_token(user['user_id'], user['email'], user['role'])
            # Supprimer le cookie complet — session pas encore validée
            response.delete_cookie("session_token")
            return LoginResponse(
                access_token=preauth_token,
                refresh_token="",
                token_type="bearer",
                expires_in=300,
                user=user_info,
                twofa_pending=True
            )
    # ────────────────────────────────────────────────────────────────────────

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRY_MINUTES * 60,
        user=user_info
    )

@api_router.get("/auth/me", response_model=UserProfile)
async def get_me(
    request: Request,
    authorization: Optional[str] = Header(default=None)
):
    """Get current user profile"""
    user = await resolve_user(request, authorization)
    return UserProfile(**user)

@api_router.post("/auth/refresh", response_model=LoginResponse)
@limiter.limit("10/minute")  # P5 — brute-force refresh token
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request
):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        decoded = decode_jwt_token(payload.refresh_token)
        
        # Verify it's a refresh token
        if decoded.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail="Token invalide")
        
        user_id = decoded.get('user_id')
        
        # Check if refresh token exists and is not revoked
        refresh_doc = await db.refresh_tokens.find_one({
            "refresh_token": payload.refresh_token,
            "user_id": user_id,
            "revoked": False
        })
        
        if not refresh_doc:
            raise HTTPException(status_code=401, detail="Refresh token invalide ou révoqué")
        
        # Check if refresh token is expired
        expires_at = datetime.fromisoformat(refresh_doc['expires_at'])
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expiré")
        
        # Get user
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if not user or not user.get('actif', True):
            raise HTTPException(status_code=401, detail="Utilisateur introuvable ou inactif")
        
        # Create new access token and refresh token
        new_access_token = create_jwt_token(user['user_id'], user['email'], user['role'])
        new_refresh_token = create_refresh_token(user['user_id'])
        
        # Revoke old refresh token
        await db.refresh_tokens.update_one(
            {"refresh_token": payload.refresh_token},
            {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Store new refresh token
        new_refresh_token_doc = {
            "refresh_token": new_refresh_token,
            "user_id": user['user_id'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRY_DAYS)).isoformat(),
            "revoked": False
        }
        await db.refresh_tokens.insert_one(new_refresh_token_doc)
        
        # Log token refresh
        await log_audit_event(
            user_id=user['user_id'],
            action="TOKEN_REFRESH",
            resource_type="auth",
            details={"email": user['email']},
            ip_address=request.client.host if request.client else None
        )
        
        # Return user info with new tokens
        user_info = {
            "user_id": user['user_id'],
            "email": user['email'],
            "nom_complet": user['nom_complet'],
            "role": user['role'],
            "actif": user['actif'],
            "picture": user.get('picture'),
        }
        
        return LoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRY_MINUTES * 60,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Erreur lors du rafraîchissement du token")

@api_router.post("/auth/logout")
@limiter.limit("30/minute")  # P5 — anti-flood logout
async def logout(response: Response, request: Request, authorization: Optional[str] = Header(default=None)):
    """Logout - clears httpOnly cookie"""
    try:
        user = await resolve_user(request, authorization)
        # Log logout
        await log_audit_event(
            user_id=user['user_id'],
            action="LOGOUT",
            resource_type="auth",
            details={"email": user['email']},
            ip_address=request.client.host if request.client else None
        )
    except:
        # Log anonymous logout attempt
        await log_audit_event(
            user_id="anonymous",
            action="LOGOUT",
            resource_type="auth",
            ip_address=request.client.host if request.client else None
        )
    
    response.delete_cookie(key="session_token")
    return {"message": "Déconnecté avec succès"}

@api_router.post("/auth/create-user", response_model=UserProfile, status_code=201)
@limiter.limit("10/minute")  # Limit user creation to 10 per minute per IP
async def create_user(
    request: Request,
    payload: CreateUserRequest = Body(...),
    authorization: Optional[str] = Header(default=None),
):
    """Create a new user (super_admin only). Email must be unique."""
    me = await resolve_user(request, authorization)
    if me["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Réservé au super_admin")

    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Rôle invalide. Valeurs autorisées : {sorted(VALID_ROLES)}",
        )

    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    import uuid
    now = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": payload.email.lower(),
        "nom_complet": payload.nom_complet.strip(),
        "role": payload.role,
        "actif": payload.actif,
        "password_hash": hash_password(payload.password),
        "picture": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(user_doc)
    
    # Log user creation
    await log_audit_event(
        user_id=me['user_id'],
        action="CREATE_USER",
        resource_type="user",
        resource_id=user_doc['user_id'],
        details={
            "target_email": payload.email,
            "target_role": payload.role,
            "created_by": me['email']
        },
        ip_address=request.client.host if request.client else None
    )
    
    logger.info("✅ User %s created by %s", payload.email, me["email"])
    return UserProfile(**{k: v for k, v in user_doc.items() if k != "password_hash"})


@api_router.post("/auth/change-password/{user_id}")
@limiter.limit("5/minute")  # Limit password changes to 5 per minute per IP
async def change_password(
    user_id: str,
    request: Request,
    payload: ChangePasswordRequest = Body(...),
    authorization: Optional[str] = Header(default=None),
):
    """Reset a user's password (super_admin only)."""
    me = await resolve_user(request, authorization)
    if me["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Réservé au super_admin")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": now}},
    )
    
    # Log password change
    await log_audit_event(
        user_id=me['user_id'],
        action="CHANGE_PASSWORD",
        resource_type="user",
        resource_id=user_id,
        details={
            "target_email": target["email"],
            "changed_by": me['email']
        },
        ip_address=request.client.host if request.client else None
    )
    
    logger.info("🔑 Password reset for %s by %s", target["email"], me["email"])
    return {"message": "Mot de passe mis à jour avec succès"}

# ============================================================================
# DASHBOARD ENDPOINT
# ============================================================================
DASHBOARD_ROLES = {
    "super_admin", "directeur_general", "comptable", "directeur_commercial",
    "gestionnaire_stock", "responsable_magasinier", "secretariat", "service_logistique",
}  # assistante exclue — matrice frontend

@api_router.get("/dashboard/stats")
async def dashboard_stats(
    request: Request,
    authorization: Optional[str] = Header(default=None)
):
    """Get dashboard stats for current user role (cached for 5 minutes)"""
    user = await resolve_user(request, authorization)
    if user["role"] not in DASHBOARD_ROLES:
        raise HTTPException(status_code=403, detail="Accès au dashboard non autorisé pour ce rôle")
    
    # Try cache first
    cache_key = f"dashboard_stats:{user['role']}"
    cached = await get_cached(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # Build payload
    payload = await build_dashboard_payload(user['role'], db)
    
    # Cache the result
    import json
    await set_cached(cache_key, json.dumps(payload), ttl=300)  # 5 minutes
    
    return payload

# ============================================================================
# HEALTH CHECK
# ============================================================================
@api_router.get("/")
async def root():
    return {"message": "ERP EDITIONS FABS-CI API v1.0.0", "status": "running"}

@api_router.get("/health")
async def health():
    """Health check public — réponse minimale sans infos infra (fix C3)."""
    # Vérification rapide MongoDB sans exposer les détails
    try:
        await db.command("ping")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "unhealthy"})


@api_router.get("/health/details")
async def health_details(
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Health check détaillé — réservé super_admin (fix C3)."""
    me = await resolve_user(request, authorization)
    if me.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Accès réservé au super_admin")
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    try:
        await db.command("ping")
        health_status["checks"]["mongodb"] = {"status": "connected"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["mongodb"] = {"status": "disconnected", "error": str(e)}
        logger.error(f"MongoDB health check failed: {e}")
    try:
        await redis_client.ping()
        health_status["checks"]["redis"] = {"status": "connected"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = {"status": "disconnected", "error": str(e)}
        logger.error(f"Redis health check failed: {e}")
    try:
        collections = await db.list_collection_names()
        health_status["checks"]["collections"] = {"status": "ok", "count": len(collections)}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["collections"] = {"status": "error", "error": str(e)}
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    return health_status

# ============================================================================
# REGISTER ALL MODULE ROUTERS
# ============================================================================
api_router.include_router(build_clients_router(db, resolve_user, log_audit_event))
api_router.include_router(build_products_router(db, resolve_user, log_audit_event))
api_router.include_router(build_commandes_router(db, resolve_user, log_audit_event))
_factures_router = build_factures_router(db, resolve_user, log_audit_event)
api_router.include_router(_factures_router)
api_router.include_router(build_paiements_router(db, resolve_user, log_audit_event))
api_router.include_router(build_stock_router(db, resolve_user, log_audit_event))
api_router.include_router(build_bons_livraison_router(db, resolve_user, log_audit_event))
api_router.include_router(build_bons_retour_router(db, resolve_user, log_audit_event))
api_router.include_router(build_comptabilite_router(db, resolve_user, log_audit_event))
api_router.include_router(build_utilisateurs_router(db, resolve_user))
api_router.include_router(build_parametres_router(db, resolve_user))
api_router.include_router(build_recherche_router(db, resolve_user))
api_router.include_router(build_documents_ai_router(db, resolve_user))
api_router.include_router(build_analytics_router(db, resolve_user))
api_router.include_router(build_colisage_router(db, resolve_user, log_audit_event))
api_router.include_router(build_notifications_router(db, resolve_user))
api_router.include_router(build_logistique_router(db, resolve_user))
api_router.include_router(build_comptabilite_avancee_router(db, resolve_user))
api_router.include_router(build_fleet_router(db, resolve_user))
api_router.include_router(build_logistics_costs_router(db, resolve_user))
api_router.include_router(build_multi_channel_notifications_router(db, resolve_user))
api_router.include_router(build_bi_analytics_router(db, resolve_user))
api_router.include_router(build_workflow_approvals_router(db, resolve_user))
api_router.include_router(build_file_storage_router(db, resolve_user))
api_router.include_router(build_backup_router(db, resolve_user))
api_router.include_router(build_twofa_router(
    db, resolve_user, log_audit_event,
    create_jwt_token=create_jwt_token,
    create_refresh_token=create_refresh_token,
    JWT_ACCESS_TOKEN_EXPIRY_MINUTES=JWT_ACCESS_TOKEN_EXPIRY_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRY_DAYS=JWT_REFRESH_TOKEN_EXPIRY_DAYS
))
api_router.include_router(build_rh_router(db, resolve_user))

# Include document settings router
api_router.include_router(document_settings_router)

# Include FNE router
api_router.include_router(fne_router)
api_router.include_router(fournisseurs_router)
api_router.include_router(approvisionnement_router)
api_router.include_router(build_proformas_router(db, resolve_user, log_audit_event))
api_router.include_router(build_rapports_router(db, resolve_user))
api_router.include_router(paie_router)


# ============================================================================
# ENDPOINT : Journal des envois (cross-documents)
# ============================================================================
@api_router.get("/envois-historique")
async def get_envois_historique(
    request: Request,
    date_debut: Optional[str] = Query(default=None),
    date_fin: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    type_document: Optional[str] = Query(default=None),
    canal: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    authorization: Optional[str] = Header(default=None),
):
    """Journal des envois (WhatsApp + Email) pour tous les documents."""
    user = await resolve_user(request, authorization)
    ALLOWED = {
        "super_admin", "directeur_general", "directeur_commercial",
        "comptable", "secretariat",
    }
    if user["role"] not in ALLOWED:
        raise HTTPException(status_code=403, detail="Accès refusé")

    query: dict = {}
    if type_document:
        query["type_document"] = type_document
    if canal:
        query["canal"] = canal
    if user_id:
        query["user_id"] = user_id
    if date_debut or date_fin:
        query["created_at"] = {}
        if date_debut:
            query["created_at"]["$gte"] = date_debut
        if date_fin:
            query["created_at"]["$lte"] = date_fin + "T23:59:59Z"

    total = await db.envoi_logs.count_documents(query)
    skip = (page - 1) * page_size
    cursor = db.envoi_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


# Include API router in main app
app.include_router(api_router)

# ============================================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Seed database on startup"""
    logger.info("🚀 Starting ERP EDITIONS FABS-CI backend...")

    # Sprint 2 V10 — exposer db & redis dans app.state pour modules type fne_module
    app.state.db = db
    try:
        import redis.asyncio as _redis_async
        app.state.redis = _redis_async.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=False,
        )
        logger.info("✅ Redis client (app.state.redis) ready")
    except Exception as exc:
        logger.warning("Redis init failed: %s", exc)
        app.state.redis = None
    
    # Seed super admin if not exists
    super_admin_email = os.environ.get('SUPER_ADMIN_EMAIL', 'pissken@editionsfabsci.com')
    super_admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')
    if env == 'production' and super_admin_password == 'Admin@2025':
        logger.warning("⚠️  [F4] SUPER_ADMIN_PASSWORD non défini — fallback hardcodé actif en production. Définissez SUPER_ADMIN_PASSWORD dans l'environnement.")
    super_admin_name = os.environ.get('SUPER_ADMIN_NAME', 'AKE APPIA YVES DORIS')
    
    admin_exists = await db.users.find_one({"email": super_admin_email})
    if not admin_exists:
        logger.info("Creating super admin...")
        if env == 'production' and super_admin_password == 'Admin@2025':
            logger.warning("⚠️  Using default SUPER_ADMIN_PASSWORD in production. Please change it!")
        now = datetime.now(timezone.utc).isoformat()
        admin_doc = {
            "user_id": "admin_super_001",
            "email": super_admin_email,
            "nom_complet": super_admin_name,
            "role": "super_admin",
            "actif": True,
            "password_hash": hash_password(super_admin_password),
            "picture": None,
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(admin_doc)
        logger.info(f"✅ Super admin created: {super_admin_email}")
    
    # Seed DG if not exists
    dg_email = os.environ.get('DG_EMAIL', 'ali.mamin@editionsfabsci.com')
    dg_password = os.environ.get('DG_PASSWORD', 'DG@2025')
    dg_name = os.environ.get('DG_NAME', 'ALI MAMIN')
    
    dg_exists = await db.users.find_one({"email": dg_email})
    if not dg_exists:
        logger.info("Creating DG...")
        if env == 'production' and dg_password == 'DG@2025':
            logger.warning("⚠️  Using default DG_PASSWORD in production. Please change it!")
        now = datetime.now(timezone.utc).isoformat()
        dg_doc = {
            "user_id": "dg_001",
            "email": dg_email,
            "nom_complet": dg_name,
            "role": "directeur_general",
            "actif": True,
            "password_hash": hash_password(dg_password),
            "picture": None,
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(dg_doc)
        logger.info(f"✅ DG created: {dg_email}")
    
    # Seed system parameters if not exists
    param_count = await db.parametres.count_documents({})
    if param_count == 0:
        count = await seed_parametres(db)
        logger.info(f"✅ {count} system parameters seeded")
    
    # Seed clients if not exists
    client_count = await db.clients.count_documents({})
    if client_count == 0:
        logger.info("Seeding clients...")
        count = await seed_clients(db, "admin_super_001")
        logger.info(f"✅ {count} clients seeded")
    
    # Seed products if not exists
    product_count = await db.produits.count_documents({})
    if product_count == 0:
        logger.info("Seeding products...")
        count = await seed_real_products(db, "admin_super_001")
        logger.info(f"✅ {count} real products seeded")
    
    # Seed commandes if not exists
    commande_count = await db.commandes.count_documents({})
    if commande_count == 0:
        logger.info("Seeding commandes...")
        count = await seed_commandes(db, "admin_super_001")
        logger.info(f"✅ {count} commandes seeded")
    
    # Seed factures if not exists
    facture_count = await db.factures.count_documents({})
    if facture_count == 0:
        logger.info("Seeding factures...")
        count = await seed_factures(db, "admin_super_001")
        logger.info(f"✅ {count} factures seeded")
    
    # Seed paiements if not exists
    paiement_count = await db.paiements.count_documents({})
    if paiement_count == 0:
        logger.info("Seeding paiements...")
        count = await seed_paiements(db, "admin_super_001")
        logger.info(f"✅ {count} paiements seeded")
    
    # Seed mouvements stock if not exists
    mouvement_count = await db.mouvements_stock.count_documents({})
    if mouvement_count == 0:
        logger.info("Seeding stock movements...")
        count = await seed_mouvements_stock(db, "admin_super_001")
        logger.info(f"✅ {count} stock movements seeded")
    
    # Seed documents demo if not exists
    doc_count = await db.documents_intelligents.count_documents({})
    if doc_count == 0:
        logger.info("Seeding demo documents...")
        count = await seed_documents_demo(db, "admin_super_001")
        logger.info(f"✅ {count} demo documents seeded")
    
    # Seed RH data if not exists
    dept_count = await db.departements.count_documents({})
    if dept_count == 0:
        logger.info("Seeding RH data...")
        await seed_rh_data(db)
        logger.info("✅ RH data seeded")

    # Sprint 1 V10 — Indexes notifications
    try:
        await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.notifications.create_index([("user_id", 1), ("lue", 1)])
        await db.notifications.create_index([("categorie", 1)])
        await db.notification_logs.create_index([("notification_id", 1)])
        await db.notification_logs.create_index([("user_id", 1), ("ts", -1)])
        # P6-002 — TTL 90 jours sur notification_logs (purge automatique)
        await db.notification_logs.create_index(
            [("ts", 1)],
            expireAfterSeconds=90 * 24 * 3600,  # 90 jours
            name="idx_notification_logs_ttl_90d"
        )
        await db.notification_preferences.create_index([("user_id", 1)], unique=True)
        logger.info("✅ Notifications indexes ensured (TTL 90j sur notification_logs)")
    except Exception as exc:
        logger.warning("Notifications indexes failed: %s", exc)

    # Index unicité : 1 facture par commande (type "facture" uniquement)
    try:
        await db.factures.create_index(
            [("commande_id", 1), ("type_facture", 1)],
            unique=True,
            partialFilterExpression={
                "commande_id": {"$exists": True, "$type": "string"},
                "type_facture": {"$eq": "facture"}
            },
            name="unique_facture_par_commande"
        )
        logger.info("✅ Factures uniqueness index ensured")
    except Exception as exc:
        logger.warning("Factures uniqueness index failed: %s", exc)

    # M1/M2 fix: Index manquants — users, refresh_tokens, bons_livraison, proformas, etc.
    try:
        await db.users.create_index("email", unique=True, name="idx_users_email_unique")
        await db.refresh_tokens.create_index("user_id", name="idx_refresh_tokens_user_id")
        await db.refresh_tokens.create_index(
            "expires_at",
            expireAfterSeconds=0,
            name="idx_refresh_tokens_ttl"
        )
        await db.bons_livraison.create_index([("statut", 1), ("date_creation", -1)], name="idx_bl_statut_date")
        await db.bons_livraison.create_index("commande_id", name="idx_bl_commande_id")
        await db.proformas.create_index([("client_id", 1), ("statut", 1)], name="idx_proformas_client_statut")
        await db.proformas.create_index("date_creation", name="idx_proformas_date")
        await db.audit_logs.create_index([("user_id", 1), ("created_at", -1)], name="idx_audit_user_date")
        await db.audit_logs.create_index("resource_type", name="idx_audit_resource_type")
        await db.facture_lignes.create_index("facture_id", name="idx_facture_lignes_facture_id")
        await db.commande_lignes.create_index("commande_id", name="idx_commande_lignes_commande_id")
        await db.bl_lignes.create_index("bl_id", name="idx_bl_lignes_bl_id")
        await db.affectations_paiement.create_index("paiement_id", name="idx_affectations_paiement_id")
        # Colisage v2 indexes
        await db.ordres_colisage.create_index("ordre_colisage_id", unique=True, name="idx_oc_id_unique")
        await db.ordres_colisage.create_index("facture_id", name="idx_oc_facture_id")
        await db.ordres_colisage.create_index([("statut", 1), ("created_at", -1)], name="idx_oc_statut_date")
        await db.ordres_colisage.create_index("client_id", name="idx_oc_client_id")
        await db.cartons_colisage.create_index("carton_id", unique=True, name="idx_carton_id_unique")
        await db.cartons_colisage.create_index("ordre_colisage_id", name="idx_carton_ordre_id")
        await db.cartons_colisage.create_index("facture_id", name="idx_carton_facture_id")
        await db.cartons_colisage.create_index([("ordre_colisage_id", 1), ("numero_carton", 1)], name="idx_carton_ordre_num")
        await db.livraisons_directes.create_index("livraison_id", unique=True, name="idx_liv_id_unique")
        await db.livraisons_directes.create_index("ordre_colisage_id", name="idx_liv_ordre_id")
        await db.livraisons_directes.create_index([("statut", 1), ("created_at", -1)], name="idx_liv_statut_date")
        await db.expeditions_colisage.create_index("expedition_id", unique=True, name="idx_exp_id_unique")
        await db.expeditions_colisage.create_index("ordre_colisage_id", name="idx_exp_ordre_id")
        await db.expeditions_colisage.create_index([("statut", 1), ("created_at", -1)], name="idx_exp_statut_date")
        logger.info("✅ Security/performance indexes ensured (M1/M2/E4 fix)")
    except Exception as exc:
        logger.warning("Security/performance indexes failed: %s", exc)

    # TICKET-015 — Job relances factures toutes les 24h
    async def _relances_job():
        import asyncio as _asyncio
        while True:
            try:
                result = await _factures_router.run_relances_once()
                logger.info("TICKET-015 relances job: %s", result)
            except Exception as _e:
                logger.error("TICKET-015 relances job error: %s", _e)
            await _asyncio.sleep(86400)  # 24h

    asyncio.create_task(_relances_job())
    logger.info("✅ TICKET-015 — job relances factures démarré (24h interval)")

    # Seed journaux comptables + plan SYSCOHADA
    try:
        seed_result = await seed_journaux_et_plan_comptable(db)
        logger.info(f"✅ Comptabilité seed: {seed_result['journaux']} journaux, {seed_result['comptes']} comptes insérés")
    except Exception as exc:
        logger.warning("Comptabilité seed failed: %s", exc)

    logger.info("✅ ERP EDITIONS FABS-CI backend ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    logger.info("Shutting down ERP backend...")
    client.close()
    logger.info("✅ MongoDB connection closed")

# ============================================================================
# RUN SERVER (for development)
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
