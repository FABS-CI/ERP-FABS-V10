# TOUR 3: Security Implementation Guide

Comprehensive guide to using TOUR 3 security and error handling features.

---

## Exception Hierarchy

### BaseERPError
All custom errors inherit from `BaseERPError`, providing:
- Consistent error structure
- HTTP status codes
- Severity levels (INFO, WARNING, ERROR, CRITICAL)
- JSON serialization

```python
from error_handlers import (
    BaseERPError, ValidationError, AuthenticationError,
    AuthorizationError, NotFoundError, DatabaseError,
    TimeoutError, RateLimitError
)

# All exceptions can be caught together
try:
    dangerous_operation()
except BaseERPError as e:
    # Has: e.message, e.code, e.severity, e.http_status, e.details
    logger.error(e.to_json())
```

---

## Error Handling Patterns

### 1. Input Validation
```python
from error_handlers import ValidationError

@app.post("/api/clients")
async def create_client(name: str, email: str):
    # Validate input
    if not name or len(name) < 2:
        raise ValidationError("Name must be 2+ characters", field="name")
    
    if "@" not in email:
        raise ValidationError("Invalid email format", field="email")
    
    # Continue with logic...
```

### 2. Authentication Errors
```python
from error_handlers import AuthenticationError

@app.post("/api/auth/login")
async def login(email: str, password: str):
    user = db["utilisateurs"].find_one({"email": email})
    
    if not user or not verify_password(password, user["password_hash"]):
        # Don't reveal which field is wrong
        raise AuthenticationError("Invalid credentials")
    
    return {"token": generate_token(user)}
```

### 3. Authorization Errors
```python
from error_handlers import AuthorizationError

async def require_admin(user_id: str):
    user = db["utilisateurs"].find_one({"_id": user_id})
    
    if user["role"] != "super_admin":
        raise AuthorizationError(
            "Admin access required",
            required_role="super_admin"
        )
    
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, admin: Dict = Depends(require_admin)):
    # Only admins can reach here
    db["utilisateurs"].delete_one({"_id": user_id})
    return {"status": "deleted"}
```

### 4. Not Found Errors
```python
from error_handlers import NotFoundError

@app.get("/api/clients/{client_id}")
async def get_client(client_id: str):
    client = db["clients"].find_one({"_id": client_id})
    
    if not client:
        raise NotFoundError("Client", resource_id=client_id)
    
    return client
```

### 5. Database Errors
```python
from error_handlers import DatabaseError

@app.get("/api/invoices")
async def list_invoices():
    try:
        invoices = list(db["invoices"].find())
        return {"data": invoices}
    except Exception as e:
        raise DatabaseError(
            f"Failed to fetch invoices: {str(e)}",
            operation="find",
            collection="invoices"
        )
```

### 6. Business Logic Errors
```python
from error_handlers import BusinessLogicError

@app.post("/api/orders")
async def create_order(client_id: str, total: float):
    client = db["clients"].find_one({"_id": client_id})
    
    if client["credit_limit"] < total:
        raise BusinessLogicError(
            f"Order exceeds credit limit: {client['credit_limit']}",
            rule="credit_check"
        )
    
    # Create order...
```

---

## Retry Logic

### Automatic Retries
Use the `@retry_decorator` for operations that might fail temporarily:

```python
from error_handlers import RetryableDecorator, RetryConfig

# Create decorator with custom config
retry_config = RetryConfig(
    max_attempts=3,
    base_delay_ms=100,
    max_delay_ms=10000,
    exponential_base=2.0,
    backoff_jitter=True
)
retry_dec = RetryableDecorator(retry_config)

# Apply to function
@retry_dec
def fetch_external_api():
    response = requests.get("https://external-api.com/data")
    return response.json()

# Call function (will auto-retry on failure)
data = fetch_external_api()
```

### Retry for Database Operations
```python
from error_handlers import RetryableDecorator
from error_handlers import DatabaseError

retry = RetryableDecorator()

@retry
def save_document(collection, document):
    result = db[collection].insert_one(document)
    return result.inserted_id

# Will retry up to 3 times on DatabaseError
client_id = save_document("clients", {"name": "Acme Corp"})
```

### Retry Configuration
```python
# Very aggressive retries
aggressive = RetryConfig(
    max_attempts=5,
    base_delay_ms=50,
    max_delay_ms=5000,
    exponential_base=1.5
)

# Conservative retries
conservative = RetryConfig(
    max_attempts=2,
    base_delay_ms=200,
    max_delay_ms=30000,
    exponential_base=3.0
)
```

---

## Circuit Breaker Pattern

### Protecting External Service Calls
```python
from error_handlers import CircuitBreaker, ExternalServiceError

circuit = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    recovery_timeout_seconds=60  # Try recovery after 60s
)

@app.get("/api/shipping-cost")
async def get_shipping_cost(weight: float):
    try:
        # This might fail
        cost = circuit.call(
            external_shipping_api,
            weight=weight
        )
        return {"cost": cost}
    
    except ExternalServiceError as e:
        # Circuit is open - use fallback
        return {
            "cost": calculate_default_shipping(weight),
            "note": "Using default shipping cost (service unavailable)"
        }
```

### Check Circuit State
```python
# Get circuit state
state = circuit.get_state()
# {"state": "closed", "failure_count": 2, "last_failure_time": "..."}

if state["state"] == "open":
    logger.warning("Circuit breaker is open - external service down")
```

---

## Graceful Degradation

### Mark Service as Degraded
```python
from error_handlers import GracefulDegradation

degradation = GracefulDegradation()

@app.get("/api/recommendations")
async def get_recommendations(client_id: str):
    try:
        # AI service might be down
        recommendations = ai_service.get_recommendations(client_id)
        return {"recommendations": recommendations}
    
    except Exception as e:
        # Mark as degraded, return empty fallback
        degradation.mark_degraded(
            "ai_service",
            reason="Connection timeout",
            fallback_data=[]
        )
        
        return {"recommendations": [], "note": "Service temporarily degraded"}
```

### Check Degradation Status
```python
# Check if service is degraded
if degradation.is_degraded("ai_service"):
    # Use fallback
    data = degradation.get_fallback("ai_service")
else:
    # Use normal path
    data = fetch_data()

# Get all degraded services
status = degradation.get_status()
# {"degraded_services": 1, "services": {"ai_service": {...}}}
```

### Mark Service Recovered
```python
# When service comes back online
degradation.mark_recovered("ai_service")
```

---

## Error Logging

### Centralized Error Logger
```python
from error_handlers import ErrorLogger

logger = ErrorLogger()

# Log error with context
try:
    risky_operation()
except Exception as e:
    logger.log_error(
        e,
        context={"operation": "payment_processing"},
        user_id=user_id,
        endpoint="/api/payments"
    )
```

### Unhandled Exception Handler
```python
import sys
from error_handlers import ErrorLogger

logger = ErrorLogger()

# Setup global exception handler
def handle_exception(exc_type, exc_value, traceback):
    logger.log_unhandled_exception(exc_type, exc_value, traceback)

sys.excepthook = handle_exception
```

---

## Monitoring Security

### Request Tracing
Every request gets a unique trace ID:

```python
# In response headers
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000

# Use for correlating logs
GET /api/orders/123
# Look for this trace ID in all service logs
```

### Performance Monitoring
```python
from monitoring_setup import get_monitoring_components

monitoring = get_monitoring_components()
metrics = monitoring["metrics"]

# Check request performance
stats = metrics.get_histogram_stats("http_request_duration_ms")
# {
#   "count": 1000,
#   "avg": 45.2,
#   "p50": 32.0,
#   "p95": 150.0,
#   "p99": 500.0
# }

# Alert if p95 > 200ms
if stats["p95"] > 200:
    logger.warning("Slow response time detected")
```

### Health Checks
```python
# All health checks accessible at /health
{
  "status": "healthy",
  "components": {
    "mongodb": {
      "status": "healthy",
      "last_check": "2026-06-24T15:30:00"
    },
    "redis": {
      "status": "unhealthy",
      "last_check": "2026-06-24T15:29:55",
      "error": "Connection refused"
    }
  }
}
```

---

## Audit Logging

### Log Security Events
```python
from logging_config import create_structured_logger

audit = create_structured_logger("audit")

# Log login attempt
audit.info("User login", extra={
    "user_id": user_id,
    "email": email,
    "ip": request.client.host,
    "success": True
})

# Log admin action
audit.warning("User deleted", extra={
    "admin_id": admin_id,
    "deleted_user_id": user_id,
    "action": "delete_user"
})

# Log failed authentication
audit.error("Failed login attempt", extra={
    "email": email,
    "ip": request.client.host,
    "attempts": 5  # Track failed attempts
})
```

### View Audit Logs
```python
# Query audit collection
logs = db["audit_logs"].find({
    "action": "LOGIN_FAILED"
}).sort("timestamp", -1).limit(10)

# Search by user
logs = db["audit_logs"].find({"user_id": user_id})

# Search by date range
from datetime import datetime, timedelta
week_ago = datetime.now() - timedelta(days=7)
logs = db["audit_logs"].find({"timestamp": {"$gte": week_ago}})
```

---

## Rate Limiting (v10.1)

### Current Implementation
Rate limiting is configured in `monitoring_setup.py`:

```python
# Max 60 requests per minute per IP
rate_limiter = RateLimiter(requests_per_minute=60)

if rate_limiter.is_rate_limited(client_ip):
    raise RateLimitError("Rate limit exceeded")
```

### Recommended Setup for Production
Use Redis for distributed rate limiting:

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379)

def rate_limit(max_requests=60, window_seconds=60):
    def decorator(f):
        @wraps(f)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, window_seconds)
            
            if count > max_requests:
                raise RateLimitError("Rate limit exceeded")
            
            return await f(request, *args, **kwargs)
        return wrapper
    return decorator

@app.post("/api/invoices")
@rate_limit(max_requests=30, window_seconds=60)
async def create_invoice(request: Request):
    # Max 30 invoices per minute
    ...
```

---

## Data Encryption (v10.1)

### Encryption at Rest
```python
# Configure MongoDB encryption
client = MongoClient(
    MONGO_URI,
    autoEncryptionOpts={
        "keyVaultNamespace": "encryption.__keyVault",
        "kmsProviders": {
            "aws": {
                "accessKeyId": AWS_KEY,
                "secretAccessKey": AWS_SECRET
            }
        }
    }
)
```

### Encryption in Transit
```python
# Use TLS for all connections
MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/?ssl=true"

# Verify certificate
client = MongoClient(
    MONGO_URI,
    tlsCAFile="/path/to/ca.pem"
)
```

---

## Secrets Management

### Environment Variables
```bash
# Never commit secrets to git!
# Use environment variables instead:

export JWT_SECRET="<generate-with-secrets.token_urlsafe(32)>"
export MONGODB_URI="mongodb+srv://user:pass@..."
export SENTRY_DSN="https://key@sentry.io/..."

# Or use .env file (add to .gitignore)
# pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

### Using AWS Secrets Manager
```python
import boto3

client = boto3.client('secretsmanager')

secret = client.get_secret_value(SecretId='erp-fabs-secrets')
secrets = json.loads(secret['SecretString'])

JWT_SECRET = secrets['jwt_secret']
MONGODB_URI = secrets['mongodb_uri']
```

### Using HashiCorp Vault
```python
import hvac

client = hvac.Client(url='http://vault:8200')
secrets = client.secrets.kv.v2.read_secret_version(path='erp-fabs')

JWT_SECRET = secrets['data']['data']['jwt_secret']
```

---

## Security Best Practices

### 1. Input Validation
Always validate user input:
```python
from error_handlers import ValidationError

def validate_email(email: str):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$', email):
        raise ValidationError("Invalid email format", field="email")

def validate_phone(phone: str):
    if not re.match(r'^\+?1?\d{9,15}$', phone):
        raise ValidationError("Invalid phone format", field="phone")
```

### 2. SQL/NoSQL Injection Prevention
Use parameterized queries (PyMongo handles this):
```python
# ✓ SAFE - PyMongo parameterizes
user = db["utilisateurs"].find_one({"email": user_input})

# ✗ DANGEROUS - Don't do this!
# eval(f"db.utilisateurs.find_one({{'email': '{user_input}'}})")
```

### 3. Cross-Site Scripting (XSS)
Always escape user input in responses:
```python
# ✓ SAFE - FastAPI auto-escapes
return {"name": user_input}

# If returning HTML:
from html import escape
return escape(user_input)
```

### 4. CSRF Protection
FastAPI handles CSRF in forms. For APIs, use token validation:
```python
# Token validation via middleware (not needed for JSON APIs)
# Already implemented in app_production.py
```

### 5. Dependency Injection
Use FastAPI's dependency system:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(get_current_user)):
    # current_user is automatically injected and validated
    ...
```

---

## Compliance & Auditing

### GDPR Compliance
```python
# Right to be forgotten: Delete user data
@app.delete("/api/users/{user_id}")
async def delete_user_data(user_id: str):
    # Delete from all collections
    db["utilisateurs"].delete_one({"_id": user_id})
    db["orders"].delete_many({"user_id": user_id})
    db["invoices"].delete_many({"user_id": user_id})
    db["audit_logs"].delete_many({"user_id": user_id})
    
    # Log the deletion
    logger.warning(f"User data deleted: {user_id}")
```

### Audit Trail
```python
# All important actions logged to audit_logs collection
# Retention: 365 days (auto-delete via TTL index)

db["audit_logs"].find_one({
    "action": "UPDATE",
    "resource_type": "invoices",
    "user_id": admin_id
})
```

### Data Access Logging
```python
# Log all sensitive data access
@app.get("/api/clients/{client_id}/payment-details")
async def get_payment_details(client_id: str, current_user = Depends(get_current_user)):
    audit.warning("Accessed sensitive data", extra={
        "user_id": current_user["id"],
        "resource_type": "client",
        "resource_id": client_id,
        "data_type": "payment_details"
    })
```

---

## Security Checklist

Before going to production:

- [ ] JWT_SECRET is random (32+ characters)
- [ ] MongoDB credentials strong (12+ chars, special chars)
- [ ] All secrets in environment variables (not code)
- [ ] HTTPS/TLS enabled
- [ ] CORS origins whitelist (not `*`)
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Error details hidden in production
- [ ] Input validation on all endpoints
- [ ] SQL/NoSQL injection prevention
- [ ] XSS protection enabled
- [ ] CSRF protection (if needed)
- [ ] Sentry DSN configured
- [ ] Backup encryption enabled
- [ ] Database access restricted (firewall)
- [ ] API behind reverse proxy
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Disaster recovery tested

---

## Security Incident Response

### If Compromised
1. **Immediate**: Stop the application
2. **Investigation**: Review audit logs
3. **Containment**: Change all secrets
4. **Recovery**: Restore from backup
5. **Post-Mortem**: Review what happened

### If Data Breach
1. **Assess**: What data was accessed?
2. **Notify**: Inform affected users (GDPR required)
3. **Remediate**: Patch vulnerability
4. **Audit**: Verify breach is closed
5. **Improve**: Implement preventive measures

---

**Last Updated:** 2026-06-24  
**Version:** TOUR 3 (10.0.0)
