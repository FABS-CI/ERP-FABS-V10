"""
TOUR 3: Production Backend - Minimal Integration
Uses: monitoring_setup + error_handlers + logging_config + database_schema
(Simplified version - no security_config yet)
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from passlib.context import CryptContext
import os
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Import TOUR 3 modules
from monitoring_setup import initialize_monitoring, get_monitoring_components
from error_handlers import initialize_error_handlers, BaseERPError, ValidationError, AuthenticationError
from logging_config import initialize_logging, create_structured_logger
from database_schema import SchemaOptimizer, AuditLogSchema

# ==================== CONFIG ====================

ENV = os.getenv("ENV", "development")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/fabs_ci")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-2026")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# ==================== APP ====================

app = FastAPI(
    title="ERP FABS V10 - Production",
    version="10.0.0"
)

# ==================== LOGGING ====================

logger_config = initialize_logging(
    app_name="ERP-FABS",
    environment=ENV,
    sentry_dsn=os.getenv("SENTRY_DSN"),
    log_file=None
)

app_logger = logger_config.get_app_logger()
request_logger = logger_config.get_request_logger()
security_logger = logger_config.get_security_logger()
error_logger = logger_config.get_error_logger()

app_logger.info(f"ERP FABS V10 starting (ENV: {ENV})")

# ==================== MONITORING ====================

monitoring = initialize_monitoring(app_logger)
metrics = monitoring["metrics"]
tracer = monitoring["tracer"]
health_checker = monitoring["health_checker"]
alert_manager = monitoring["alert_manager"]
dashboard = monitoring["dashboard"]

app_logger.info("Monitoring initialized")

# ==================== ERROR HANDLING ====================

error_handlers = initialize_error_handlers(error_logger)
error_logger_inst = error_handlers["error_logger"]
circuit_breaker = error_handlers["circuit_breaker"]

app_logger.info("Error handling initialized")

# ==================== DATABASE ====================

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['fabs_ci']
    client.admin.command('ping')
    app_logger.info(f"✓ MongoDB connected")
except Exception as e:
    app_logger.error(f"✗ MongoDB failed: {e}")
    if ENV == "production":
        raise

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Register DB health check
def check_db():
    try:
        client.admin.command('ping')
        return True
    except:
        return False

health_checker.register_component("mongodb", check_db, critical=True)

# ==================== MIDDLEWARE ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware("http")
async def middleware_tracking(request: Request, call_next):
    """Track requests and monitor performance"""
    
    # Skip health/metrics
    if request.url.path in ["/health", "/metrics", "/docs"]:
        return await call_next(request)
    
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Metrics
        metrics.increment_counter("http_requests_total", labels={
            "method": request.method,
            "status": response.status_code
        })
        metrics.observe_histogram("http_request_duration_ms", duration_ms)
        
        if response.status_code >= 400:
            metrics.increment_counter("http_errors_total")
        
        # Headers
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        return response
    
    except Exception as e:
        error_logger_inst.log_error(e, endpoint=request.url.path)
        metrics.increment_counter("http_errors_total")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "trace_id": trace_id}
        )


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(BaseERPError)
async def handle_erp_error(request: Request, exc: BaseERPError):
    """Handle ERP errors"""
    return JSONResponse(status_code=exc.http_status, content=exc.to_dict())


@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    """Handle all exceptions"""
    error_logger_inst.log_error(exc, endpoint=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ==================== HELPERS ====================

def hash_pwd(pwd: str) -> str:
    return pwd_context.hash(pwd)


def verify_pwd(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_user(request: Request):
    """Get current user from token"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return {"user_id": "test_user"}


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {"app": "ERP FABS V10", "status": "running"}


@app.get("/health")
async def health():
    """Health check"""
    health_status = health_checker.check_all()
    return {
        "status": health_status["overall_status"],
        "components": health_status["components"]
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics"""
    return metrics.export_metrics()


@app.get("/dashboard")
async def get_dashboard():
    """Monitoring dashboard"""
    return dashboard.generate_dashboard()


@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Login"""
    metrics.increment_counter("auth_attempts")
    
    try:
        user = db["utilisateurs"].find_one({"email": email})
        if not user:
            metrics.increment_counter("auth_failures")
            raise AuthenticationError("Invalid credentials")
        
        metrics.increment_counter("auth_success")
        return {
            "access_token": "token_" + uuid.uuid4().hex[:16],
            "user": {"id": user["_id"], "email": user["email"]}
        }
    
    except Exception as e:
        raise AuthenticationError(str(e))


@app.get("/api/clients")
async def list_clients(skip: int = 0, limit: int = 20):
    """List clients"""
    try:
        clients = list(db["clients"].find().skip(skip).limit(limit))
        return {"data": clients, "count": len(clients)}
    except Exception as e:
        error_logger_inst.log_error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/products")
async def list_products(skip: int = 0, limit: int = 20):
    """List products"""
    try:
        products = list(db["products"].find().skip(skip).limit(limit))
        return {"data": products, "count": len(products)}
    except Exception as e:
        error_logger_inst.log_error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/orders")
async def list_orders(skip: int = 0, limit: int = 20):
    """List orders"""
    try:
        orders = list(db["orders"].find().skip(skip).limit(limit))
        return {"data": orders, "count": len(orders)}
    except Exception as e:
        error_logger_inst.log_error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/invoices")
async def list_invoices(skip: int = 0, limit: int = 20):
    """List invoices"""
    try:
        invoices = list(db["invoices"].find().skip(skip).limit(limit))
        return {"data": invoices, "count": len(invoices)}
    except Exception as e:
        error_logger_inst.log_error(e)
        raise HTTPException(status_code=500, detail="Database error")


@app.get("/api/utilisateurs/me")
async def get_me(user: Dict = Depends(get_user)):
    """Get current user"""
    return user


@app.post("/api/admin/indexes")
async def create_indexes():
    """Create database indexes"""
    try:
        count = 0
        for idx in SchemaOptimizer.get_all_indexes():
            try:
                db[idx.collection].create_index(idx.fields)
                count += 1
            except:
                pass
        
        app_logger.info(f"Created {count} indexes")
        return {"indexes_created": count}
    except Exception as e:
        error_logger_inst.log_error(e)
        raise HTTPException(status_code=500, detail="Index creation failed")


@app.on_event("startup")
async def startup():
    """Startup"""
    app_logger.info("ERP FABS V10 startup complete")
    metrics.increment_counter("app_starts")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown"""
    app_logger.info("ERP FABS V10 shutdown")
    client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
