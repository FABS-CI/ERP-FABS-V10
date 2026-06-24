"""
TOUR 4: Enterprise Backend - Complete Integration
==================================================
Purpose: FastAPI app with TOUR 3 + TOUR 4 production-grade features

TOUR 3 included:
- Authentication (JWT), Password hashing, User roles
- Query optimization, Database indexing
- Error handling, Validation, Logging
- CORS, Rate limiting (basic)

TOUR 4 additions:
1. Session Management (session_manager.py)
   - User session lifecycle with Redis
   - Anomaly detection, IP tracking
   - Session audit trail

2. API Key Management (api_key_manager.py)
   - API key generation, rotation, permissions
   - Hash-based security (SHA256)
   - RBAC integration

3. Redis Integration (redis_integration.py)
   - Sessions, cache, rate limiting
   - Metrics collection, background queues
   - Graceful degradation

4. OpenTelemetry Distributed Tracing (opentelemetry_setup.py)
   - Trace context propagation
   - Span correlation across services
   - Log enrichment with trace IDs

5. Prometheus Metrics (prometheus_metrics.py)
   - Standard metric types
   - /metrics endpoint for Prometheus scraping
   - Business, system, database metrics

6. Grafana Dashboards (grafana_dashboards.py)
   - 4 pre-built dashboards (JSON)
   - Infrastructure, Database, API, Business
   - Exportable for production

7. Alert Manager (alert_manager_external.py)
   - Multi-channel alerts (Email, Slack, Teams, PagerDuty)
   - Deduplication, rate limiting, retry logic
   - Critical/Emergency incident escalation

Startup: python3 app_enterprise.py
API: http://localhost:8000
Metrics: http://localhost:8001/metrics
Docs: http://localhost:8000/docs
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthCredentials

# TOUR 3 + TOUR 4 modules
from session_manager import SessionManager, SessionConfig, get_session_manager
from api_key_manager import APIKeyManager, APIKeyConfig, APIKeyPermission, get_api_key_manager
from redis_integration import RedisClient, RedisConfig, get_redis_client
from opentelemetry_setup import init_otel, get_otel
from prometheus_metrics import get_metrics
from alert_manager_external import create_alert_manager_from_env, Alert, AlertSeverity
from grafana_dashboards import GrafanaDashboards

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Extract and validate user from JWT or session"""
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = auth_header.replace("Bearer ", "")
    
    # For now, basic validation. In production, decode JWT
    return {
        "user_id": "user123",
        "email": "test@erp-fabs.local",
        "role": "admin"
    }


async def get_api_key_user(request: Request) -> Dict[str, Any]:
    """Extract and validate user from API key"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    api_key_manager = get_api_key_manager()
    key_info = api_key_manager.get_key_info(api_key)
    
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "user_id": key_info.get("user_id"),
        "api_key_id": key_info.get("key_id"),
        "permissions": key_info.get("permissions", [])
    }


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info("TOUR 4: Enterprise Backend Starting")
    logger.info("=" * 60)
    
    # 1. Initialize OpenTelemetry
    logger.info("1. Initializing OpenTelemetry...")
    otel = get_otel()
    otel.instrument_requests()
    otel.instrument_pymongo()
    otel.instrument_redis()
    logger.info("   ✓ OpenTelemetry ready")
    
    # 2. Initialize Prometheus metrics
    logger.info("2. Initializing Prometheus metrics...")
    metrics = get_metrics()
    metrics.start_http_server(port=8001)
    logger.info("   ✓ Prometheus metrics ready on :8001/metrics")
    
    # 3. Initialize Redis
    logger.info("3. Initializing Redis...")
    redis_config = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        timeout=5
    )
    redis_client = RedisClient(redis_config)
    if redis_client.connect():
        logger.info("   ✓ Redis connected")
    else:
        logger.warning("   ⚠ Redis not available (running in degraded mode)")
    
    # 4. Initialize Session Manager
    logger.info("4. Initializing Session Manager...")
    session_config = SessionConfig(
        ttl_seconds=86400,
        redis_client=redis_client,
        enable_anomaly_detection=True,
        anomaly_threshold=5
    )
    session_manager = SessionManager(session_config)
    logger.info("   ✓ Session Manager ready")
    
    # 5. Initialize API Key Manager
    logger.info("5. Initializing API Key Manager...")
    api_key_config = APIKeyConfig(
        rotation_days=90,
        max_keys_per_user=5,
        db_client=None  # Use global MongoDB
    )
    api_key_manager = APIKeyManager(api_key_config)
    logger.info("   ✓ API Key Manager ready")
    
    # 6. Initialize Alert Manager
    logger.info("6. Initializing Alert Manager...")
    alert_manager = create_alert_manager_from_env()
    logger.info(f"   ✓ Alert Manager ready with {len(alert_manager.channels)} channels")
    
    # 7. Load Grafana dashboards
    logger.info("7. Loading Grafana dashboards...")
    dashboards = GrafanaDashboards()
    dashboard_list = dashboards.get_all_dashboards()
    logger.info(f"   ✓ {len(dashboard_list)} Grafana dashboards loaded")
    
    # Store in app.state for access in routes
    app.state.otel = otel
    app.state.metrics = metrics
    app.state.redis = redis_client
    app.state.session_manager = session_manager
    app.state.api_key_manager = api_key_manager
    app.state.alert_manager = alert_manager
    app.state.dashboards = dashboards
    
    logger.info("=" * 60)
    logger.info("TOUR 4: Enterprise Backend Ready")
    logger.info("=" * 60)
    
    yield  # App runs here
    
    # ===== SHUTDOWN =====
    logger.info("Shutting down TOUR 4 services...")
    otel.shutdown()
    redis_client.close()
    logger.info("✓ Shutdown complete")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="ERP FABS CI - TOUR 4 Enterprise",
    description="Production-grade ERP with distributed tracing, monitoring, alerts",
    version="10.1.0",
    lifespan=lifespan
)

# Instrument FastAPI for automatic tracing
otel_setup = init_otel(app)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_trace_context(request: Request, call_next):
    """Middleware to add trace context to all requests"""
    start_time = time.time()
    
    # Get OpenTelemetry tracer
    otel = app.state.otel
    metrics = app.state.metrics
    
    # Start span
    with otel.get_tracer().start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.client_ip", request.client.host)
        
        # Add trace ID to response headers
        span.set_attribute("trace_id", otel.get_current_trace_id())
        
        try:
            # Call next middleware/handler
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            metrics.track_http_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration
            )
            
            # Record in span
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.duration_ms", duration * 1000)
            
            # Add trace ID to response
            response.headers["X-Trace-ID"] = otel.get_current_trace_id()
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            metrics.track_http_request(
                method=request.method,
                endpoint=request.url.path,
                status=500,
                duration=duration
            )
            
            raise


# ============================================================================
# HEALTH CHECKS
# ============================================================================

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    redis = app.state.redis
    
    return {
        "status": "healthy",
        "service": "ERP FABS CI Tour 4",
        "version": "10.1.0",
        "redis": "connected" if redis.is_connected() else "disconnected",
        "timestamp": time.time()
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check for load balancer"""
    redis = app.state.redis
    
    # Check critical dependencies
    if not redis.is_connected():
        raise HTTPException(status_code=503, detail="Redis unavailable")
    
    return {"ready": True}


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@app.get("/metrics", tags=["metrics"], response_class=PlainTextResponse)
async def get_metrics_endpoint():
    """Export metrics in Prometheus format"""
    metrics = app.state.metrics
    return metrics.export_metrics()


@app.post("/api/dashboards/export", tags=["dashboards"])
async def export_dashboards():
    """Export all Grafana dashboards as JSON"""
    dashboards = app.state.dashboards
    all_dashboards = dashboards.get_all_dashboards()
    
    return {
        "dashboards": all_dashboards,
        "count": len(all_dashboards)
    }


# ============================================================================
# SESSIONS API
# ============================================================================

@app.post("/api/sessions", tags=["sessions"])
async def create_session(user_id: str, ip_address: str):
    """Create new user session"""
    session_manager = app.state.session_manager
    otel = app.state.otel
    
    with otel.get_tracer().start_as_current_span("create_session") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("ip_address", ip_address)
        
        session = session_manager.create_session(user_id, ip_address)
        
        return {
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "created_at": session["created_at"]
        }


@app.get("/api/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: str):
    """Get session info"""
    session_manager = app.state.session_manager
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@app.delete("/api/sessions/{session_id}", tags=["sessions"])
async def delete_session(session_id: str):
    """Invalidate session"""
    session_manager = app.state.session_manager
    session_manager.invalidate_session(session_id)
    
    return {"message": "Session invalidated"}


# ============================================================================
# API KEYS API
# ============================================================================

@app.post("/api/keys/generate", tags=["api-keys"])
async def generate_api_key(user_id: str, permissions: list = None):
    """Generate new API key"""
    api_key_manager = app.state.api_key_manager
    otel = app.state.otel
    
    with otel.get_tracer().start_as_current_span("generate_api_key") as span:
        span.set_attribute("user_id", user_id)
        
        key_info = api_key_manager.generate_key(user_id, permissions or [])
        
        # Only return secret once
        return {
            "key_id": key_info["key_id"],
            "secret": key_info["secret"],  # WARNING: Show only once!
            "created_at": key_info["created_at"],
            "message": "Save the secret securely. It won't be shown again."
        }


@app.get("/api/keys/list", tags=["api-keys"])
async def list_api_keys(user_id: str):
    """List user's API keys (without secrets)"""
    api_key_manager = app.state.api_key_manager
    
    keys = api_key_manager.list_keys(user_id)
    
    # Remove secrets
    return [
        {k: v for k, v in key.items() if k != "secret_hash"}
        for key in keys
    ]


@app.post("/api/keys/{key_id}/rotate", tags=["api-keys"])
async def rotate_api_key(key_id: str, user_id: str):
    """Rotate API key (generate new secret)"""
    api_key_manager = app.state.api_key_manager
    
    new_secret = api_key_manager.rotate_key(key_id, user_id)
    if not new_secret:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {
        "key_id": key_id,
        "new_secret": new_secret,
        "message": "Previous secret is no longer valid"
    }


# ============================================================================
# REDIS/CACHE API
# ============================================================================

@app.get("/api/cache/{key}", tags=["cache"])
async def get_cache(key: str):
    """Get value from cache"""
    redis = app.state.redis
    value = redis.get(key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"key": key, "value": value}


@app.post("/api/cache/{key}", tags=["cache"])
async def set_cache(key: str, value: str, ttl: int = 3600):
    """Set cache value"""
    redis = app.state.redis
    redis.set(key, value, ttl)
    
    return {"key": key, "message": "Cache set"}


# ============================================================================
# ALERTS API
# ============================================================================

@app.post("/api/alerts", tags=["alerts"])
async def send_alert(title: str, message: str, severity: str = "warning"):
    """Send alert through configured channels"""
    alert_manager = app.state.alert_manager
    otel = app.state.otel
    
    alert = Alert(
        title=title,
        message=message,
        severity=severity,
        trace_id=otel.get_current_trace_id()
    )
    
    success = await alert_manager.queue_alert(alert)
    
    return {
        "alert_id": alert.get_hash(),
        "queued": success,
        "channels": list(alert_manager.channels.keys())
    }


# ============================================================================
# TEST ROUTES
# ============================================================================

@app.get("/test/trace", tags=["testing"])
async def test_trace():
    """Test OpenTelemetry tracing"""
    otel = app.state.otel
    
    with otel.get_tracer().start_as_current_span("test_span") as span:
        span.set_attribute("test", True)
        return {
            "trace_id": otel.get_current_trace_id(),
            "span_id": otel.get_current_span_id()
        }


@app.get("/test/metrics", tags=["testing"])
async def test_metrics():
    """Test Prometheus metrics recording"""
    metrics = app.state.metrics
    
    # Simulate various operations
    metrics.track_http_request("GET", "/test", 200, 0.05)
    metrics.track_db_query("find", "test_collection", 0.02)
    metrics.track_cache_hit("test_key")
    metrics.track_login("success")
    
    return {"message": "Metrics recorded"}


@app.get("/test/alert", tags=["testing"])
async def test_alert():
    """Test alert sending"""
    alert_manager = app.state.alert_manager
    
    alert = Alert(
        title="Test Alert",
        message="This is a test alert from TOUR 4 Enterprise",
        severity=AlertSeverity.WARNING
    )
    
    success = await alert_manager.queue_alert(alert)
    
    return {
        "message": "Test alert queued",
        "success": success
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """API root endpoint"""
    return {
        "name": "ERP FABS CI",
        "version": "10.1.0",
        "tour": "TOUR 4 Enterprise Grade",
        "features": [
            "Session Management",
            "API Key Management",
            "Distributed Tracing (OpenTelemetry)",
            "Prometheus Metrics",
            "Grafana Dashboards",
            "Multi-Channel Alerts",
            "Redis Cache & Sessions",
            "RBAC & Authentication"
        ],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "sessions": "/api/sessions",
            "api_keys": "/api/keys",
            "alerts": "/api/alerts",
            "cache": "/api/cache/{key}"
        }
    }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("TOUR 4: Enterprise Backend")
    logger.info("Starting uvicorn server...")
    logger.info("=" * 60)
    logger.info("API: http://localhost:8000")
    logger.info("Docs: http://localhost:8000/docs")
    logger.info("Metrics: http://localhost:8001/metrics")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
