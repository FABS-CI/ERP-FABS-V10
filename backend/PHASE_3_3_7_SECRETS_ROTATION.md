# Phase 3.3.7: Secrets Rotation

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `secrets_rotation_service.py` — Automated key rotation management
- `server.py` — Integration + API endpoints

---

## Overview

Automated, zero-downtime key rotation for:
- **JWT Secret** — Authentication tokens
- **Encryption Key** — Data-at-rest encryption
- **Signing Key** — Request signature validation
- **Database Password** — MongoDB credentials
- **Redis Password** — Cache credentials
- **API Keys** — Third-party integrations

**Key Features:**
- **Zero-downtime rotation** — Old key + new key both valid during grace period
- **Grace period** — 7 days for old keys (allows data decryption)
- **Policy-based** — Automatic rotation on schedule or manual on-demand
- **Audit logging** — All rotations logged with reason + user
- **Validation** — Support for decrypting/validating old data

---

## Rotation Policies

| Policy | Interval | Use Case |
|--------|----------|----------|
| **MANUAL** | Never automatic | Dev/testing, manual oversight |
| **DAILY** | 24 hours | High-security environments |
| **WEEKLY** | 7 days | Sensitive systems |
| **MONTHLY** | 30 days | Standard (default) |
| **QUARTERLY** | 90 days | Lower-risk systems |

### Default Schedules

```
JWT_SECRET:        Every 90 days (QUARTERLY)
ENCRYPTION_KEY:    Every 90 days (QUARTERLY)
SIGNING_KEY:       Every 90 days (QUARTERLY)
API_KEY:           Every 30 days (MONTHLY)
DB_PASSWORD:       Manual (MANUAL)
REDIS_PASSWORD:    Manual (MANUAL)
```

---

## Zero-Downtime Rotation Flow

### Before Rotation
```
Current Key: key_v123
Previous Keys: []
```

### During Rotation (Grace Period: 7 days)
```
Current Key: key_v124 (NEW)
Previous Keys: [key_v123 (valid until 2024-07-30)]
```

**Both keys are valid during grace period:**
- New requests use `key_v124`
- Old tokens/data decrypt with `key_v123`
- No downtime, no re-authentication required

### After Grace Period
```
Current Key: key_v124
Previous Keys: []  # key_v123 expired
```

---

## Rotation Metadata

### Database Structure

```javascript
{
  "secret_type": "jwt_secret",
  "current_value": "gAAAAABq...",
  "created_at": "2024-01-01T00:00:00Z",
  "last_rotated_at": "2024-06-23T17:50:00Z",
  "next_rotation_at": "2024-09-23T00:00:00Z",
  "rotation_policy": "quarterly",
  "previous_values": [
    {
      "value": "gAAAAABp...",
      "rotated_at": "2024-06-23T17:50:00Z",
      "valid_until": "2024-06-30T17:50:00Z"  // Grace period
    }
  ],
  "updated_at": "2024-06-23T17:50:00Z"
}
```

---

## API Endpoints (Admin)

### `GET /api/security/secrets-status`

Get rotation status for all secrets (super_admin only).

**Response:**
```json
{
  "status": "ok",
  "secrets": {
    "jwt_secret": {
      "created_at": "2024-01-01T00:00:00Z",
      "last_rotated_at": "2024-06-23T17:50:00Z",
      "next_rotation_at": "2024-09-23T00:00:00Z",
      "rotation_policy": "quarterly",
      "rotation_due": false,
      "previous_keys_count": 1
    },
    "encryption_key": {
      "created_at": "2024-01-01T00:00:00Z",
      "last_rotated_at": "2024-06-23T17:45:00Z",
      "next_rotation_at": "2024-09-23T00:00:00Z",
      "rotation_policy": "quarterly",
      "rotation_due": false,
      "previous_keys_count": 1
    },
    ...
  },
  "timestamp": "2024-06-23T17:54:00Z"
}
```

### `POST /api/security/rotate-secret`

Rotate a secret immediately (super_admin only).

**Query Parameters:**
- `secret_type` (required): jwt_secret, encryption_key, signing_key, etc.
- `reason` (default: "Manual rotation"): Reason for rotation

**Response:**
```json
{
  "success": true,
  "secret_type": "jwt_secret",
  "rotated_at": "2024-06-23T17:55:00Z",
  "old_key_valid_until": "2024-06-30T17:55:00Z",
  "grace_period_days": 7,
  "new_key_hash": "f0e1d2c3b4a5"
}
```

---

## Integration Patterns

### Validate Old Secrets

```python
# During grace period, old secrets still validate
from secrets_rotation_service import SecretType

is_valid = await secrets_rotation_service.validate_old_secret(
    secret_type=SecretType.JWT_SECRET,
    value=old_token_secret
)
# → True (if within grace period)
# → False (if expired)
```

### Get Rotation Status

```python
metadata = await secrets_rotation_service.get_secret_metadata(
    SecretType.ENCRYPTION_KEY
)

if metadata.is_due_for_rotation():
    # Schedule rotation
    await secrets_rotation_service.rotate_secret(
        secret_type=SecretType.ENCRYPTION_KEY,
        reason="Scheduled quarterly rotation"
    )
```

### Check Rotation Schedule

```python
due_for_rotation = await secrets_rotation_service.schedule_rotation_check()
# → ["jwt_secret", "encryption_key"]
```

---

## Monitoring & Alerting

### Watch For

1. **Rotation schedule:** Check `/api/security/secrets-status` daily
2. **Overdue rotations:** Alert if `rotation_due: true`
3. **Rotation failures:** Check logs for error messages
4. **Grace period expiry:** Track `valid_until` timestamps

### Recommended Checks

```bash
# Daily check
0 2 * * * curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/security/secrets-status \
  | jq '.secrets[] | select(.rotation_due == true)'

# Monthly rotation
0 0 23 * * curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  "http://localhost:8002/api/security/rotate-secret?secret_type=api_key&reason=Monthly%20rotation"
```

---

## Best Practices

### For Development

1. **Test grace period:** Decrypt with old key during period
2. **Verify zero-downtime:** Rotate JWT secret, verify tokens still work
3. **Test schedule:** Run rotation check, verify due dates

### For Production

1. **Automate rotation:** Use background jobs (cron, APScheduler)
2. **Monitor schedule:** Alert on overdue rotations
3. **Document rotation:** Log reason + approver
4. **Test rollback:** Practice key recovery (if needed)
5. **Notify services:** Warn consumers of key change

### For Compliance

1. **Track rotations:** All rotations in audit log
2. **Enforce policies:** No manual disabling of rotation
3. **Retention:** Keep old key hashes for audit trail
4. **Approval workflow:** Require sign-off for critical keys

---

## Rotation Ceremony

### Before Rotation

```bash
# 1. Check status
GET /api/security/secrets-status

# 2. Verify nothing in-flight
GET /api/audit/critical-events?hours=1
```

### During Rotation

```bash
# 1. Rotate secret
POST /api/security/rotate-secret?secret_type=jwt_secret&reason="Quarterly rotation - Q3 2024"

# 2. Monitor logs
tail -f /var/log/app.log | grep "Secret rotated"

# 3. Verify grace period
GET /api/security/secrets-status
# Check: old_key_valid_until is 7 days from now
```

### After Grace Period

```bash
# 1. Confirm no old tokens in use
GET /api/audit/critical-events?hours=168  # 7 days

# 2. Document completion
echo "Quarterly rotation completed: jwt_secret, encryption_key, signing_key"
```

---

## Testing

```bash
# Get current rotation status
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8002/api/security/secrets-status | jq

# Rotate a key immediately (test)
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  "http://localhost:8002/api/security/rotate-secret?secret_type=jwt_secret&reason=Test%20rotation"

# Verify in logs
grep "Secret rotated" /var/log/app.log
```

---

## Compliance & Standards

### NIST Guidelines
- ✅ Periodic key rotation (configurable)
- ✅ Key versioning (multiple valid keys)
- ✅ Audit logging (all rotations tracked)
- ✅ Zero-downtime migration

### SOC 2
- ✅ Change management (audit trail)
- ✅ Access control (super_admin only)
- ✅ Monitoring (due date alerts)

### PCI DSS
- ✅ Key rotation every 90 days (configurable)
- ✅ Key destruction (old keys expire)
- ✅ Encryption key management

---

## Advanced Topics

### Hardware Security Module (HSM)

For production, integrate with HSM:

```python
# Instead of storing secrets in DB:
# 1. Generate key in HSM
# 2. Store key ID in DB
# 3. Call HSM for crypto operations
# 4. Rotate key on HSM

# Example: AWS KMS
import boto3
kms = boto3.client('kms')
new_key = kms.generate_key(...)
```

### Key Derivation Function (KDF)

Strengthen keys with KDF:

```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

key = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'fabs-ci-salt',
    iterations=100000
).derive(master_key.encode())
```

---

## Troubleshooting

### Old Key No Longer Validates

**Problem:** Tokens/data from before rotation fail to validate

**Solution:** Check `valid_until` in `previous_values`:
```bash
db.secrets_rotation.find({"secret_type": "jwt_secret"})
# Check: now() < valid_until of any previous_value
```

**Action:** If expired, restore from backup or re-encrypt with current key

### Rotation Stuck

**Problem:** Rotation endpoint hangs or fails

**Solution:** 
1. Check MongoDB connectivity
2. Check audit table permissions
3. Review logs for errors
4. Manually reset: `db.secrets_rotation.deleteOne({...})`

---

## Next Steps

- **Phase 3.4:** Data in-transit protection (TLS enforcement)
- **Phase 4:** Incident response automation
- **Phase 5:** Advanced monitoring + anomaly detection

---

## Phase 3.3 Complete! 🎉

**All 7 security features implemented:**
1. ✅ Request Signing (HMAC-SHA256)
2. ✅ Data Encryption at Rest (Fernet AES-128)
3. ✅ Output Encoding (XSS prevention)
4. ✅ Advanced RBAC/ACL (scope-based)
5. ✅ Enhanced Audit Trail (IP logging)
6. ✅ Advanced Rate Limiting (per-user, per-endpoint)
7. ✅ Secrets Rotation (automated key management)

**Production-ready security posture established.**

---

## References

- NIST Key Management: https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-57pt1r5.pdf
- OWASP Secrets Management: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- AWS KMS: https://docs.aws.amazon.com/kms/
