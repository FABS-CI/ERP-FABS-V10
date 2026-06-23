# Phase 3.3.5: Enhanced Audit Trail

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `audit_service.py` — Comprehensive audit logging
- `server.py` — API endpoints + integration

---

## Overview

Comprehensive logging of all security-relevant actions:
- **Authentication:** Login success/failure, MFA changes
- **Resources:** Create, read, update, delete, export, import
- **Access Control:** Permission grants/revokes, role changes, denied access
- **System:** Config changes, backups, key rotations

Each log entry captures:
- **WHO:** User ID
- **WHAT:** Action type & resource
- **WHEN:** Timestamp (UTC)
- **WHERE:** IP address (masked for privacy)
- **HOW:** Request ID, session ID, user agent hash
- **OUTCOME:** Success/failure, error message

---

## Audit Actions

### Authentication (5)
- `login_success` — Successful login
- `login_failure` — Failed login attempt
- `logout` — User logout
- `password_change` — Password changed
- `password_reset` — Password reset

### MFA (2)
- `mfa_enabled` — Multi-factor auth enabled
- `mfa_disabled` — Multi-factor auth disabled

### Resources (6)
- `create` — Resource created
- `read` — Resource accessed
- `update` — Resource modified
- `delete` — Resource deleted
- `export` — Data exported
- `import` — Data imported

### Access Control (4)
- `permission_grant` — Permission granted
- `permission_revoke` — Permission revoked
- `role_change` — Role changed
- `access_denied` — Access attempt denied

### System (5)
- `configuration_change` — System settings changed
- `backup_created` — Database backup created
- `backup_restored` — Backup restored
- `key_rotation` — Encryption key rotated
- `security_patch` — Security update applied

### Security (1)
- `suspicious_activity` — Flagged for investigation

---

## Audit Levels

| Level | Severity | Retention | Examples |
|-------|----------|-----------|----------|
| **INFO** | Low | 90 days | Successful login, normal operations |
| **WARNING** | Medium | 180 days | Failed login, access denied |
| **CRITICAL** | High | 1 year | Suspicious activity, key rotation |

---

## Audit Event Structure

```json
{
  "audit_id": "audit_20240623174955432862",
  "timestamp": "2024-06-23T17:49:55.432862+00:00",
  "timestamp_iso": "2024-06-23T17:49:55.432862+00:00",
  
  "action": "login_success",
  "level": "info",
  "status": "success",
  
  "user_id": "user123",
  "resource_type": "auth",
  "resource_id": null,
  
  "ip_address": "a3f2c1d5e8f0b2a4c6d8e0f1a3b5c7d9",  // SHA256 hash
  "ip_address_masked": "192.168.1.***",              // Privacy-preserving
  "user_agent_hash": "f0e1d2c3b4a5",                 // Shortened
  
  "session_id": "sess_abc123",
  "request_id": "req_xyz789",
  
  "details": {},
  "changes": {},
  "error_message": null,
  
  "ttl_expires_at": "2024-06-23T17:49:55Z"  // MongoDB TTL cleanup
}
```

---

## Privacy Features

### IP Address Protection

```
Real IP: 192.168.1.100
Stored (hash): a3f2c1d5e8f0b2a4c6d8e0f1a3b5c7d9
Readable (masked): 192.168.1.***
```

- **Hash:** One-way, prevents IP tracking
- **Masked:** Readable while hiding precision
- Both stored for compliance + usability

### User Agent Hashing

User agents are hashed (not stored in plaintext) to reduce fingerprinting.

### Data Minimization

- Passwords/PII never logged
- Only changes logged (before/after), not full records
- Error messages sanitized (no sensitive data)

---

## API Endpoints

### `GET /api/audit/user-log`

Get audit log for current user.

**Query Parameters:**
- `limit`: 1-500 (default: 50)
- `skip`: Offset (default: 0)

**Response:**
```json
{
  "status": "ok",
  "user_id": "user123",
  "count": 25,
  "logs": [
    {
      "audit_id": "audit_20240623...",
      "timestamp": "2024-06-23T17:49:55Z",
      "action": "login_success",
      "level": "info",
      "status": "success",
      "ip_address_masked": "192.168.1.***",
      ...
    }
  ]
}
```

### `GET /api/audit/resource-log`

Get audit log for specific resource (super_admin only).

**Query Parameters:**
- `resource_type` (required): "client", "order", etc.
- `resource_id` (required): Resource ID
- `limit`: 1-500 (default: 50)

**Response:** List of audit events affecting resource

### `GET /api/audit/critical-events`

Get critical security events (super_admin only).

**Query Parameters:**
- `hours`: 1-2160 (default: 24)
- `limit`: 1-500 (default: 100)

**Response:** Critical events (suspicious activity, key rotations, etc.)

### `GET /api/audit/suspicious-ips`

Get IPs with multiple failed login attempts (super_admin only).

**Query Parameters:**
- `hours`: Time window (default: 24)
- `threshold`: Min failure count to flag (default: 5)

**Response:**
```json
{
  "status": "ok",
  "hours": 24,
  "threshold": 5,
  "count": 3,
  "suspicious_ips": [
    {
      "_id": "203.0.113.***",
      "count": 15,
      "last_attempt": "2024-06-23T17:49:55Z",
      "users": ["unknown", "unknown", "admin@example.com"]
    }
  ]
}
```

---

## Integration Pattern

### Log Login

```python
from audit_service import AuditService, AuditAction

await audit_service.log_login(
    user_id="user123",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    success=True,
    session_id=session_id,
)
```

### Log Resource Change

```python
await audit_service.log_resource_change(
    action=AuditAction.CREATE,
    user_id="user123",
    resource_type="client",
    resource_id="client_456",
    changes={"name": "Acme Corp"},
    ip_address=request.client.host,
)
```

### Log Suspicious Activity

```python
await audit_service.log_suspicious_activity(
    user_id="user123",
    activity_type="brute_force",
    description="10 failed login attempts in 5 minutes",
    ip_address=request.client.host,
    additional_data={"attempt_count": 10, "window_minutes": 5}
)
```

### Log Access Denied

```python
await audit_service.log_access_denied(
    user_id="user123",
    resource_type="client",
    resource_id="client_999",
    reason="User not assigned to this client",
    ip_address=request.client.host,
)
```

---

## Compliance Features

### GDPR

- **Right to be forgotten:** Implement data deletion with audit impact
- **Data portability:** Export user's own audit logs
- **Privacy by design:** IP masking, hash-based tracking
- **Data minimization:** No PII stored in logs

### HIPAA / Medical Data

- Detailed audit trail required by law
- All user actions logged
- Immutable records (append-only)
- Retention: 6 years minimum

### SOC 2

- Comprehensive audit logging
- Tamper-proof (use append-only collections)
- Regular review (critical events dashboard)
- Incident response (suspicious IP alerts)

---

## Monitoring & Alerts

### Watch For

1. **Repeated failed logins:**
   ```bash
   GET /api/audit/critical-events?hours=24
   ```

2. **Suspicious IPs:**
   ```bash
   GET /api/audit/suspicious-ips?hours=24&threshold=5
   ```

3. **Unauthorized access attempts:**
   ```bash
   GET /api/audit/resource-log?resource_type=client&resource_id=X
   ```

### Recommended Alert Rules

| Condition | Action |
|-----------|--------|
| 5+ failed logins from same IP in 1 hour | Block IP, notify admin |
| Critical event logged | Immediate notification |
| Suspicious activity flag | Security team review |
| Config change by non-admin | Immediate rollback check |

---

## Testing

```bash
# Check user's own audit log
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/audit/user-log?limit=10

# Check critical events (super_admin)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/audit/critical-events?hours=24

# Check suspicious IPs (super_admin)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/audit/suspicious-ips?threshold=5
```

---

## Database Indexes

Create for performance:

```javascript
db.audit_log.createIndex({ "user_id": 1, "timestamp": -1 })
db.audit_log.createIndex({ "resource_type": 1, "resource_id": 1, "timestamp": -1 })
db.audit_log.createIndex({ "action": 1, "level": 1, "timestamp": -1 })
db.audit_log.createIndex({ "ip_address_masked": 1, "timestamp": -1 })

// TTL index (auto-delete old logs based on level)
db.audit_log.createIndex(
  { "ttl_expires_at": 1 },
  { expireAfterSeconds: 7776000 }  // ~90 days
)
```

---

## Next Steps

- **Phase 3.3.6:** Rate limiting advanced (per-user, per-endpoint)
- **Phase 3.3.7:** Secrets rotation (automated key management)
- **Phase 3.4:** Data in-transit protection (TLS enforcement)
- **Phase 4:** Incident response automation

---

## References

- OWASP Logging: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- GDPR Audit Requirements: https://gdpr-info.eu/
- SOC 2 Logging: https://www.soc2report.com/
