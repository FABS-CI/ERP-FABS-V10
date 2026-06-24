"""
TOUR 3: Production Hardened Backend
Integrates: security_config + monitoring_setup + error_handlers + logging_config + database_schema
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from passlib.context import CryptContext
import os
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

# TOUR 3: Import all new modules
from security_config import (
    PasswordValidator, JWTTokenManager, APIKeyManager,
    RateLimiter, InputValidator, AuditLogger as SecurityAuditLogger, RBAC,
    initialize_security
)
from monitoring_setup import initialize_monitoring, get_monitoring_components
from error_handlers import (
    initialize_error_handlers, BaseERPError, ValidationError, AuthenticationError,
    AuthorizationError, NotFoundError, DatabaseError
)
from logging_config import initialize_logging, create_structured_logger
from database_schema import SchemaOptimizer, BackupConfiguration, AuditLogSchema

# ==================== APP INITIALIZATION ====================

app = FastAPI(
    title="ERP FABS V10 - Production Hardened",
    version="10.0.0",
    description="Production-grade ERP with security, monitoring, error handling"
)

# Environment configuration
ENV = os.getenv("ENV", "development")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/fabs_ci")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# ==================== LOGGING SETUP ====================

logger_config = initialize_logging(
    app_name="ERP-FABS",
    environment=ENV,
    sentry_dsn=os.getenv("SENTRY_DSN"),
    log_file="/tmp/erp_fabs" if ENV == "production" else None
)

app_logger = logger_config.get_app_logger()
request_logger = logger_config.get_request_logger()
security_logger = logger_config.get_security_logger()
error_logger = logger_config.get_error_logger()

app_logger.info(f"Starting ERP FABS (Environment: {ENV})")

# ==================== MONITORING SETUP ====================

monitoring = initialize_monitoring(app_logger)
metrics = monitoring["metrics"]
tracer = monitoring["tracer"]
health_checker = monitoring["health_checker"]
alert_manager = monitoring["alert_manager"]
dashboard = monitoring["dashboard"]

# Register health checks
def check_mongodb() -> bool:
    try:
        client.admin.command('ping')
        return True
    except:
        return False

def check_redis() -> bool:
    # Placeholder for Redis if used
    return True

health_checker.register_component("mongodb", check_mongodb, critical=True)
health_checker.register_component("redis", check_redis, critical=False)

# Register alerts
alert_manager.register_alert(
    "high_error_rate",
    lambda: (metrics.get_counter("http_errors_total") / max(metrics.get_counter("http_requests_total"), 1)) > 0.05,
    severity="high"
)
alert_manager.register_alert(
    "high_response_time",
    lambda: metrics.get_histogram_stats("http_request_duration_ms")["avg"] > 1000,
    severity="warning"
)

# ==================== ERROR HANDLING SETUP ====================

error_handlers = initialize_error_handlers(error_logger)
error_logger_instance = error_handlers["error_logger"]
retry_decorator = error_handlers["retry_decorator"]
graceful_degradation = error_handlers["graceful_degradation"]

# ==================== SECURITY SETUP ====================

security_components = initialize_security(security_logger)
password_validator = security_components["password_validator"]
jwt_manager = security_components["jwt_manager"]
api_key_manager = security_components["api_key_manager"]
rate_limiter = security_components["rate_limiter"]
input_validator = security_components["input_validator"]
audit_logger = security_components["audit_logger"]
rbac = security_components["rbac"]

app_logger.info("Security components initialized")

# ==================== DATABASE SETUP ====================

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['fabs_ci']
    client.admin.command('ping')
    app_logger.info(f"MongoDB connected: {MONGO_URI}")
except Exception as e:
    app_logger.error(f"MongoDB connection failed: {e}")
    if ENV == "production":
        raise

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================== MIDDLEWARE ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Custom middleware for request tracking & rate limiting
@app.middleware("http")
async def middleware_security_and_monitoring(request: Request, call_next):
    """
    Middleware for:
    - Request tracking (tracing)
    - Rate limiting
    - Security headers
    - Performance monitoring
    """
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Skip health check and metrics endpoints
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response
    
    try:
        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if rate_limiter.is_rate_limited(client_ip):
            metrics.increment_counter("http_rate_limit_exceeded")
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Max 60 requests per minute."}
            )
        
        # Start tracing
        span_idx = tracer.start_span(trace_id, f"{request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        metrics.increment_counter("http_requests_total", labels={"method": request.method, "status": status_code})
        metrics.observe_histogram("http_request_duration_ms", duration_ms, labels={"method": request.method})
        
        if status_code >= 400:
            metrics.increment_counter("http_errors_total", labels={"status": status_code})
        
        # Log request
        request_logger.info(
            f"HTTP {request.method} {request.url.path}",
            extra={
                "trace_id": trace_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip
            }
        )
        
        # End tracing
        tracer.end_span(trace_id, span_idx, status="success" if status_code < 400 else "error")
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Trace-Id"] = trace_id
        
        return response
    
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.increment_counter("http_errors_total")
        
        error_logger_instance.log_error(
            e,
            context={"trace_id": trace_id, "path": request.url.path},
            endpoint=request.url.path
        )
        
        tracer.end_span(trace_id, span_idx if 'span_idx' in locals() else 0, 
                       status="error", error=str(e))
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "trace_id": trace_id}
        )


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(BaseERPError)
async def erp_error_handler(request: Request, exc: BaseERPError):
    """Handle ERP-specific errors"""
    error_logger_instance.log_error(exc, user_id=getattr(request.state, "user_id", None))
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    error = ValidationError(str(exc))
    return JSONResponse(status_code=400, content=error.to_dict())


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions"""
    error_logger_instance.log_unhandled_exception(type(exc), exc, None)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error" if ENV == "production" else str(exc)}
    )


# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain, hashed)


def create_jwt_token(user_id: str, role: str) -> Dict[str, str]:
    """Create JWT token"""
    return jwt_manager.create_token(user_id, role)


async def get_current_user(request: Request):
    """Dependency: Get current authenticated user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Missing Authorization header")
    
    try:
        token = auth_header.replace("Bearer ", "")
        payload = jwt_manager.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token")
        
        request.state.user_id = user_id
        return user_id
    except Exception as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def require_role(required_role: str):
    """Dependency: Require specific role"""
    async def role_checker(user_id: str = Depends(get_current_user)):
        user = db["utilisateurs"].find_one({"_id": user_id})
        if not user or user.get("role") != required_role:
            raise AuthorizationError(f"Role '{required_role}' required", required_role)
        return user
    return role_checker


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/health")
async def health():
    """Health check with component status"""
    health_status = health_checker.check_all()
    return {
        "status": health_status["overall_status"],
        "timestamp": health_status["timestamp"],
        "components": health_status["components"]
    }


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return metrics.export_metrics()


@app.get("/dashboard")
async def get_dashboard():
    """Get monitoring dashboard"""
    return dashboard.generate_dashboard()


@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Login endpoint"""
    metrics.increment_counter("auth_login_attempts")
    
    try:
        input_validator.validate_email(email)
        
        user = db["utilisateurs"].find_one({"email": email})
        if not user or not verify_password(password, user.get("password_hash", "")):
            metrics.increment_counter("auth_login_failures")
            audit_logger.log_action(
                user_id="unknown",
                action="LOGIN_FAILED",
                resource_type="auth",
                severity="high",
                status="failed"
            )
            raise AuthenticationError("Invalid email or password")
        
        token = create_jwt_token(user["_id"], user["role"])
        
        metrics.increment_counter("auth_login_success")
        audit_logger.log_action(
            user_id=user["_id"],
            action="LOGIN",
            resource_type="auth",
            severity="low",
            status="success"
        )
        
        app_logger.info(f"User logged in: {email}")
        
        return {
            "access_token": token["access_token"],
            "refresh_token": token["refresh_token"],
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    
    except ValidationError as e:
        raise e
    except Exception as e:
        raise AuthenticationError(str(e))


@app.get("/api/utilisateurs/me")
async def get_current_user_info(user_id: str = Depends(get_current_user)):
    """Get current user info"""
    try:
        user = db["utilisateurs"].find_one({"_id": user_id})
        if not user:
            raise NotFoundError("User", user_id)
        
        return {
            "id": user["_id"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user.get("created_at")
        }
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise


@app.get("/api/clients")
async def list_clients(skip: int = 0, limit: int = 20, user_id: str = Depends(get_current_user)):
    """List clients with pagination"""
    try:
        clients = list(db["clients"].find().skip(skip).limit(limit))
        total = db["clients"].count_documents({})
        
        return {
            "data": clients,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise DatabaseError("Failed to list clients", operation="find", collection="clients")


@app.get("/api/products")
async def list_products(skip: int = 0, limit: int = 20, user_id: str = Depends(get_current_user)):
    """List products with pagination"""
    try:
        products = list(db["products"].find().skip(skip).limit(limit))
        total = db["products"].count_documents({})
        
        return {
            "data": products,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise DatabaseError("Failed to list products", operation="find", collection="products")


@app.get("/api/orders")
async def list_orders(skip: int = 0, limit: int = 20, user_id: str = Depends(get_current_user)):
    """List orders"""
    try:
        orders = list(db["orders"].find().skip(skip).limit(limit))
        total = db["orders"].count_documents({})
        
        return {
            "data": orders,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise DatabaseError("Failed to list orders")


@app.get("/api/invoices")
async def list_invoices(skip: int = 0, limit: int = 20, user_id: str = Depends(get_current_user)):
    """List invoices"""
    try:
        invoices = list(db["invoices"].find().skip(skip).limit(limit))
        total = db["invoices"].count_documents({})
        
        return {
            "data": invoices,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise DatabaseError("Failed to list invoices")


# ==================== SECURITY/AUDIT ENDPOINTS ====================

@app.get("/api/security/audit")
async def get_audit_logs(limit: int = 100, user_id: str = Depends(get_current_user)):
    """Get audit logs (admin only)"""
    try:
        user = db["utilisateurs"].find_one({"_id": user_id})
        if user.get("role") not in ["super_admin", "admin"]:
            raise AuthorizationError("Admin access required")
        
        logs = list(db["audit_logs"].find().sort("_id", -1).limit(limit))
        return {"data": logs}
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise


@app.get("/api/security/rbac")
async def get_rbac_config(user_id: str = Depends(get_current_user)):
    """Get RBAC configuration"""
    return rbac.get_all_roles()


# ==================== ADMIN ENDPOINTS ====================

@app.post("/api/admin/create-indexes")
async def create_indexes(user_id: str = Depends(get_current_user)):
    """Create all database indexes (admin only)"""
    try:
        user = db["utilisateurs"].find_one({"_id": user_id})
        if user.get("role") != "super_admin":
            raise AuthorizationError("Super admin required")
        
        indexes_created = 0
        for idx in SchemaOptimizer.get_all_indexes():
            try:
                db[idx.collection].create_index(
                    idx.fields,
                    **idx.to_dict()["options"]
                )
                indexes_created += 1
            except Exception as e:
                app_logger.warning(f"Index creation failed for {idx.collection}: {e}")
        
        audit_logger.log_action(
            user_id=user_id,
            action="CREATE_INDEXES",
            resource_type="database",
            severity="high"
        )
        
        return {"indexes_created": indexes_created, "total": len(SchemaOptimizer.get_all_indexes())}
    except Exception as e:
        error_logger_instance.log_error(e, user_id=user_id)
        raise


# ==================== STARTUP & SHUTDOWN ====================

@app.on_event("startup")
async def startup():
    """App startup"""
    app_logger.info("ERP FABS startup complete")
    metrics.increment_counter("app_startups")


@app.on_event("shutdown")
async def shutdown():
    """App shutdown"""
    app_logger.info("ERP FABS shutting down")
    client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
