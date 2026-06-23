# Phase 3.3.6: Advanced Rate Limiting

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `rate_limiting_service.py` — Per-user, per-endpoint rate limiting
- `server.py` — Integration + API endpoints

---

## Overview

Protects API from:
- **Brute force attacks:** Login attempts, credential stuffing
- **DoS attacks:** Request flooding, resource exhaustion
- **API abuse:** Scraping, excessive exports, data exfiltration

**Features:**
- Per-user rate limits (different limits per user tier)
- Per-endpoint limits (protect expensive operations)
- Adaptive limits (tiered users have higher quotas)
- IP blocking (temporary block for suspicious activity)
- Redis-backed (distributed across servers)

---

## Rate Limit Tiers

| Tier | Description | Use Case |
|------|-------------|----------|
| **FREE** | 5 logins/5min, 30 reads/min, 5 writes/hour | Public/trial users |
| **STANDARD** | 10 logins/5min, 100 reads/min, 20 writes/hour | Regular users |
| **PREMIUM** | 20 logins/5min, 500 reads/min, 100 writes/hour | Power users |
| **ENTERPRISE** | 50 logins/5min, unlimited reads/min, unlimited writes | Large organizations |
| **SUPER_ADMIN** | Unlimited | Internal administrators |

---

## Rate Limit Scopes

| Scope | Key | Example |
|-------|-----|---------|
| **GLOBAL** | All users combined | API quota |
| **IP** | Per IP address | Login attempts (by IP) |
| **USER** | Per authenticated user | Export quota |
| **ENDPOINT** | Per endpoint (all users) | System protection |
| **USER_ENDPOINT** | Per user per endpoint | Comprehensive limits |

---

## Endpoint Configuration

### Authentication
```
POST /api/auth/login
Scope: IP
Limits:
  FREE: 5 attempts / 5 min
  STANDARD: 10 attempts / 5 min
  PREMIUM: 20 attempts / 5 min
  ENTERPRISE: 50 attempts / 5 min
```

**Protection against:** Brute force, credential stuffing

### Read Operations
```
GET /api/clients
GET /api/commandes
Scope: USER_ENDPOINT
Limits:
  FREE: 30/min
  STANDARD: 100/min
  PREMIUM: 500/min
  ENTERPRISE: Unlimited
```

**Protection against:** API scraping, excessive polling

### Write Operations
```
POST /api/clients
POST /api/commandes
Scope: USER_ENDPOINT
Limits:
  FREE: 5/hour
  STANDARD: 20/hour
  PREMIUM: 100/hour
  ENTERPRISE: Unlimited
```

**Protection against:** Data injection, spam

### Expensive Operations
```
GET /api/rapports/export
POST /api/rapports/export
Scope: USER_ENDPOINT
Limits:
  FREE: 1/hour
  STANDARD: 5/hour
  PREMIUM: 20/hour
  ENTERPRISE: 100/hour
```

**Protection against:** Data exfiltration, resource hogging

---

## API Response Headers

Rate limit information is included in HTTP headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1624022400
Retry-After: 25  (if rate limited)
```

### When Rate Limited (429)

```json
{
  "detail": "Rate limit exceeded. Try again in 25 seconds.",
  "status_code": 429,
  "retry_after": 25,
  "limit": 100,
  "remaining": 0
}
```

---

## API Endpoints (Admin)

### `GET /api/ratelimit/status`

Get user's current rate limit status.

**Response:**
```json
{
  "status": "ok",
  "user_id": "user123",
  "tier": "standard",
  "limits": {
    "/api/clients": {
      "remaining": 87,
      "limit": 100,
      "reset_at": "2024-06-23T18:00:00Z"
    },
    "/api/clients:POST": {
      "remaining": 18,
      "limit": 20,
      "reset_at": "2024-06-24T00:00:00Z"
    },
    ...
  }
}
```

### `POST /api/ratelimit/block-ip`

Block an IP address temporarily (super_admin only).

**Query Parameters:**
- `ip_address` (required): IP to block
- `duration_minutes` (default: 60): Block duration
- `reason` (default: "Suspicious activity"): Block reason

**Response:**
```json
{
  "status": "ok",
  "ip_address": "203.0.113.100",
  "duration_minutes": 60,
  "reason": "Brute force attempts detected"
}
```

### `POST /api/ratelimit/reset-user`

Reset rate limits for a user (super_admin only).

**Query Parameters:**
- `user_id` (required): User ID to reset

**Response:**
```json
{
  "status": "ok",
  "user_id": "user123",
  "reset": true
}
```

---

## Integration Pattern

### Middleware Implementation

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip for safe endpoints
    if request.method == "GET" and request.url.path.startswith("/health"):
        return await call_next(request)
    
    # Get user (optional, use IP if not authenticated)
    user = await get_current_user(request)
    identifier = user["user_id"] if user else request.client.host
    tier = get_user_tier(user) if user else RateLimitTier.FREE
    
    # Check rate limit
    status = await rate_limiting_service.check_rate_limit(
        identifier=identifier,
        endpoint=request.url.path,
        method=request.method,
        user_tier=tier
    )
    
    if not status.allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(status.retry_after),
                "X-RateLimit-Limit": str(status.limit),
                "X-RateLimit-Remaining": "0",
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(status.limit)
    response.headers["X-RateLimit-Remaining"] = str(status.remaining)
    response.headers["X-RateLimit-Reset"] = str(int(status.reset_at.timestamp()))
    
    return response
```

---

## Monitoring

### Metrics to Track

1. **Per-user quota usage:**
   ```bash
   GET /api/ratelimit/status
   ```

2. **Suspicious IPs (failed logins):**
   ```bash
   GET /api/audit/suspicious-ips?hours=24&threshold=5
   ```

3. **Rate limit violations:**
   - Monitor 429 responses
   - Alert on repeated blocks from same IP
   - Track quota exhaustion per tier

### Alerts

| Condition | Action |
|-----------|--------|
| IP rate limited 10+ times in 1 hour | Auto-block IP |
| User hits rate limit 5+ endpoints | Investigate for abuse |
| Unusual tier downgrade | Investigate account |

---

## Best Practices

### For Developers

1. **Cache responses:** Reduce unnecessary requests
2. **Batch operations:** Use bulk endpoints where available
3. **Implement backoff:** Respect Retry-After header
4. **Monitor quota:** Check remaining before expensive ops

### For Administrators

1. **Set realistic limits:** Balance protection + usability
2. **Monitor patterns:** Identify abuse early
3. **Whitelist IPs:** Trust internal systems
4. **Adjust tiers:** Premium users can request higher limits

---

## Customization

### Add New Endpoint

Edit `RATE_LIMIT_CONFIG` in `rate_limiting_service.py`:

```python
RATE_LIMIT_CONFIG = {
    "/api/custom/endpoint": {
        "scope": RateLimitScope.USER_ENDPOINT,
        "limits": {
            RateLimitTier.FREE: (5, 3600),
            RateLimitTier.STANDARD: (20, 3600),
            RateLimitTier.PREMIUM: (100, 3600),
            RateLimitTier.ENTERPRISE: (None, None),
            RateLimitTier.SUPER_ADMIN: (None, None),
        }
    },
}
```

### Change Tier

Update `get_user_tier()` function:

```python
def get_user_tier(user: Dict[str, Any]) -> RateLimitTier:
    # Custom logic: check subscription, plan, etc.
    if user.get("is_premium"):
        return RateLimitTier.PREMIUM
    ...
```

---

## Testing

```bash
# Get your current limits
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/ratelimit/status

# Simulate rate limit (make many requests)
for i in {1..101}; do
  curl -H "Authorization: Bearer TOKEN" \
    http://localhost:8002/api/clients
done
# Should get 429 on request 101+

# Block an IP (super_admin)
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  "http://localhost:8002/api/ratelimit/block-ip?ip_address=203.0.113.100&duration_minutes=60"

# Reset user limits (super_admin)
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  "http://localhost:8002/api/ratelimit/reset-user?user_id=user123"
```

---

## Performance

- **Redis latency:** ~1-2ms per check
- **Distributed:** Works across multiple API servers
- **Fail-open:** Allows requests if Redis unavailable
- **No database queries:** Purely Redis-based

---

## Next Steps

- **Phase 3.3.7:** Secrets rotation (automated key management)
- **Phase 3.4:** Data in-transit protection (TLS enforcement)
- **Phase 4:** Advanced monitoring (metrics, anomaly detection)

---

## References

- OWASP Rate Limiting: https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Prevention_Cheat_Sheet.html
- Redis: https://redis.io/
- HTTP 429: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429
