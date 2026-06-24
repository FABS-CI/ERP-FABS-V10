"""
TOUR 3: Enhanced Backend with Security, Monitoring, Error Handling
Integrates: security_config, monitoring_setup, error_handlers, logging_config
"""

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from passlib.context import CryptContext
import os
import json
import time
import uuid
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Any

# TOUR 3 Imports
from security_config import (
    PasswordValidator, JWTTokenManager, APIKeyManager,
    RateLimiter, InputValidator, AuditLogger as SecurityAuditLogger,
    RBAC
)
from monitoring_setup import (
    prometheus_metrics, request_tracer, performance_logger,
    health_checker, setup_default_alerts
)
from error_handlers import (
    AppException, ValidationError, AuthenticationError,
    AuthorizationError, NotFoundError, ErrorHandler
)
from logging_config import (
    initialize_logging, LogLevel, RequestLogger, AuditLogger
)
from database_schema import DatabaseSchema

# ==================== INITIALIZATION ====================

app = FastAPI(title="ERP FABS V10 (TOUR 3)", version="10.0-hardened")

# Initialize logging (TOUR 3)
logging_setup = initialize_logging(
    app_name="erp-fabs-v10",
    level=LogLevel.INFO,
    console=True,
    json_format=True
)
logger = logging_setup.get_logger("backend.app_simple")
request_logger = RequestLogger(logger)
audit_logger = AuditLogger(logger)

# CORS — Whitelist only in production
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# MongoDB
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/fabs_ci')
client = MongoClient(MONGO_URI)
db = client['fabs_ci']

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('JWT_SECRET', 'dev-secret-key-2026-UNSAFE')

# ==================== TOUR 3: SECURITY INITIALIZATION ====================

# Initialize security components (TOUR 3)
password_validator = PasswordValidator()
jwt_manager = JWTTokenManager(secret_key=SECRET_KEY, exp_hours=24, refresh_exp_hours=12)
api_key_manager = APIKeyManager()
rate_limiter = RateLimiter(requests_per_minute=60)
input_validator = InputValidator()
security_audit_logger = SecurityAuditLogger()
rbac = RBAC()
error_handler = ErrorHandler(include_debug=False)

# Setup database schema reference
db_schema = DatabaseSchema()

# Setup monitoring alerts
setup_default_alerts()

# Setup health checks
def check_mongodb():
    try:
        db.admin.command('ping')
        return (True, "MongoDB healthy")
    except Exception as e:
        return (False, str(e))

health_checker.register_check("mongodb", check_mongodb)

# ==================== MIDDLEWARE ====================

@app.middleware("http")
async def security_and_monitoring_middleware(request: Request, call_next):
    """
    TOUR 3: Combined security and monitoring middleware
    - Request tracing (request_id)
    - Rate limiting
    - Input validation
    - Error handling
    - Performance monitoring
    """
    
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Create trace
    trace = request_tracer.start_trace(request_id, request.method, request.url.path)
    
    # Set logging context
    logger.set_context(request_id=request_id, remote_ip=request.client.host if request.client else "unknown")
    
    try:
        # Rate limiting check
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.allow_request(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            request_tracer.end_trace(trace, 429)
            return JSONResponse(
                {"error": {"code": "RATE_001", "message": "Too many requests"}},
                status_code=429
            )
        
        # Proceed with request
        response = await call_next(request)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        request_logger.log_request(
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            remote_ip=client_ip
        )
        
        # Update metrics
        performance_logger.log_api_call(request.method, request.url.path, response.status_code, duration_ms)
        
        # Complete trace
        request_tracer.end_trace(trace, response.status_code)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    except AppException as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"AppException: {exc.message}", status_code=exc.status_code)
        request_tracer.end_trace(trace, exc.status_code, str(exc))
        
        return JSONResponse(
            exc.to_dict(include_debug=False),
            status_code=exc.status_code,
            headers={"X-Request-ID": request_id}
        )
    
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(f"Unhandled exception: {str(exc)}")
        request_tracer.end_trace(trace, 500, str(exc))
        
        result = error_handler.handle_exception(exc, request.url.path)
        return JSONResponse(
            result["response"],
            status_code=result["status_code"],
            headers={"X-Request-ID": request_id}
        )

# ==================== UTILITY: JWT TOKEN VERIFICATION ====================

async def get_current_user(authorization: Optional[str] = None) -> Dict:
    """
    Dependency for protected routes
    Verifies JWT token and returns user
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("No token provided")
    
    token = authorization[7:]
    
    try:
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token")
        
        # Fetch user from DB
        from bson.objectid import ObjectId
        user = db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise AuthenticationError("User not found")
        
        return {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "permissions": user.get("permissions", [])
        }
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

# ==================== ENDPOINTS ====================

@app.get("/api/health")
async def health_check():
    """Enhanced health check with component status"""
    health_status = health_checker.run_all_checks()
    status_code = health_checker.get_status_code()
    
    logger.info("Health check performed")
    
    return JSONResponse(
        health_status,
        status_code=status_code
    )

@app.get("/api/health/detailed")
async def health_check_detailed():
    """Detailed health and metrics"""
    return {
        "health": health_checker.last_check_results,
        "metrics": prometheus_metrics.export_json(),
        "recent_errors": error_handler.get_error_summary()
    }

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """
    TOUR 3: Enhanced login with security validations
    """
    
    try:
        # Input validation
        if not input_validator.validate_email(email):
            audit_logger.log_permission_denial(
                user_id=email,
                action="LOGIN",
                resource="auth",
                reason="Invalid email format"
            )
            raise ValidationError("Invalid email format", field="email")
        
        if not input_validator.validate_password(password):
            raise ValidationError("Invalid password format", field="password")
        
        # Find user
        user = db.users.find_one({"email": email})
        
        if not user:
            audit_logger.log_permission_denial(
                user_id=email,
                action="LOGIN",
                resource="auth",
                reason="User not found"
            )
            raise AuthenticationError("Invalid credentials")
        
        # Verify password
        if not pwd_context.verify(password, user['password']):
            audit_logger.log_permission_denial(
                user_id=email,
                action="LOGIN",
                resource="auth",
                reason="Password incorrect"
            )
            raise AuthenticationError("Invalid credentials")
        
        # Check user active status
        if not user.get("is_active", True):
            raise AuthenticationError("User account is inactive")
        
        # Generate tokens
        access_token = jwt_manager.generate_token({"user_id": str(user["_id"])})
        refresh_token = jwt_manager.generate_refresh_token({"user_id": str(user["_id"])})
        
        # Update last login
        from bson.objectid import ObjectId
        db.users.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Audit log
        audit_logger.log_action(
            user_id=str(user["_id"]),
            action="LOGIN",
            resource_type="auth",
            resource_id=email,
            result="success"
        )
        
        logger.info(f"User logged in: {email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "role": user["role"]
            }
        }
    
    except AppException:
        raise
    except Exception as e:
        logger.exception(f"Login error: {str(e)}")
        raise AppException(f"Login failed: {str(e)}", status_code=500)

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        payload = jwt_manager.verify_refresh_token(refresh_token)
        user_id = payload.get("user_id")
        
        new_access_token = jwt_manager.generate_token({"user_id": user_id})
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token
        }
    
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid refresh token")

@app.get("/api/utilisateurs/me")
async def get_current_user_info(authorization: Optional[str] = None):
    """Get current user information"""
    current_user = await get_current_user(authorization)
    
    from bson.objectid import ObjectId
    user = db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user:
        raise NotFoundError("User")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "last_login": user.get("last_login")
    }

@app.get("/api/security/audit")
async def get_audit_logs(
    limit: int = 100,
    authorization: Optional[str] = None
):
    """Get security audit logs (admin only)"""
    current_user = await get_current_user(authorization)
    
    # Check RBAC
    if current_user["role"] not in ["super_admin", "admin"]:
        raise AuthorizationError("Only admins can view audit logs")
    
    traces = request_tracer.get_recent_traces(limit)
    
    return {
        "total": len(traces),
        "traces": traces
    }

@app.get("/api/metrics/prometheus")
async def get_prometheus_metrics(authorization: Optional[str] = None):
    """Export Prometheus metrics (monitoring only)"""
    current_user = await get_current_user(authorization)
    
    # Check permission
    if "view_metrics" not in current_user.get("permissions", []):
        raise AuthorizationError("No permission to view metrics")
    
    return prometheus_metrics.export_json()

@app.get("/api/database/schema")
async def get_database_schema(authorization: Optional[str] = None):
    """Get database schema documentation"""
    current_user = await get_current_user(authorization)
    
    return {
        "collections": list(db_schema.schemas.keys()),
        "index_count": db_schema.get_index_statistics(),
        "capacity_estimate": {
            "recommendation": "Review database_schema.py for full details"
        }
    }

# ==================== ERROR HANDLERS ====================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Global handler for AppException"""
    return JSONResponse(
        exc.to_dict(include_debug=False),
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global handler for unhandled exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    result = error_handler.handle_exception(exc, request.url.path)
    return JSONResponse(result["response"], status_code=result["status_code"])

