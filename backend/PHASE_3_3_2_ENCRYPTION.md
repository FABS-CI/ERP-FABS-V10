# Phase 3.3.2: Data Encryption at Rest

**Status:** ✅ Implemented  
**Commit:** TBD  
**Files:**
- `encryption_service.py` — AES-256 encryption via Fernet
- `server.py` — Integration + endpoint

---

## Overview

Protects sensitive data stored in MongoDB using **Fernet (AES-128 in CBC mode)** with HMAC authentication.

⚠️ **Important distinction:**
- **Passwords:** Use bcrypt hashing (irreversible, one-way) — NOT encryption
- **Other sensitive data:** Use encryption (reversible) for: card numbers, bank accounts, SSN, personal info

---

## Architecture

### Encryption Service (`encryption_service.py`)

```python
encryption_service.encrypt(plaintext)  # → Ciphertext
encryption_service.decrypt(ciphertext) # → Plaintext

# Selective field encryption
encrypted = encryption_service.encrypt_dict(data, ["card_token", "iban"])
decrypted = encryption_service.decrypt_dict(data, ["card_token", "iban"])
```

### Key Derivation

- **PBKDF2HMAC** with SHA-256
- 100,000 iterations (standard for 2024)
- Fixed salt (development mode) / Per-field salt (production)

### Supported Collections

```python
ENCRYPTED_FIELDS_BY_COLLECTION = {
    "users": [],  # ⚠️ Passwords use bcrypt hashing
    "clients": ["siret", "iban"],  # Business + bank info
    "paiements": ["card_token", "reference"],  # Payment tokens
    "employes": ["ssn", "phone", "email", "address"],  # Personal data
}
```

---

## Configuration

### Environment Variable

```bash
export ENCRYPTION_KEY="<32+ character random string>"
```

In production, use external key management:
- **AWS:** KMS (Key Management Service)
- **Azure:** Key Vault
- **HashiCorp:** Vault
- **Local:** Encrypted key file (hsm, TPM)

### Development

If `ENCRYPTION_KEY` is not set, service generates random key (data won't persist across restarts).

---

## API Endpoints

### `GET /api/security/encryption-fields`

List encrypted fields per collection (super_admin only).

**Response:**
```json
{
  "status": "ok",
  "encrypted_fields_by_collection": {
    "clients": ["siret", "iban"],
    "paiements": ["card_token", "reference"],
    "employes": ["ssn", "phone", "email", "address"]
  },
  "message": "Data-at-rest encryption is active for sensitive fields"
}
```

---

## Integration in Modules

### Example: Payment Module

```python
# When creating payment
payment_data = {
    "card_token": "4111111111111111",
    "reference": "REF123",
    ...
}

# Encrypt sensitive fields before insert
from encryption_service import encryption_service, get_encrypted_fields
encrypted = encryption_service.encrypt_dict(
    payment_data,
    get_encrypted_fields("paiements")
)
await db.paiements.insert_one(encrypted)

# When retrieving payment
payment = await db.paiements.find_one(...)
decrypted = encryption_service.decrypt_dict(
    payment,
    get_encrypted_fields("paiements")
)
```

---

## Security Considerations

### ✅ Strengths

1. **At-rest protection:** Data encrypted in MongoDB
2. **Authenticated encryption:** Fernet includes HMAC (prevents tampering)
3. **Key derivation:** PBKDF2HMAC with 100k iterations
4. **Timestamp in ciphertext:** Prevents replay attacks

### ⚠️ Limitations

1. **Not in-transit:** Use HTTPS/TLS for transport (Phase 3.4)
2. **Key rotation:** Not automatic (implement in Phase 3.5)
3. **Performance:** ~10-50ms per encrypt/decrypt operation
4. **Search:** Can't query encrypted fields directly (use plaintext index separately if needed)

### 🔐 Best Practices

1. **Never log plaintext** of encrypted fields
2. **Minimize plaintext exposure:** Decrypt only when needed
3. **Rotate keys** regularly (quarterly recommended)
4. **Monitor decryption failures** → possible key mismatch (audit log)
5. **Use separate ENCRYPTION_KEY** from JWT_SECRET in production

---

## Testing

```bash
# Test encryption/decryption
python3 -c "
from encryption_service import encryption_service

plaintext = 'sensitive-data'
ciphertext = encryption_service.encrypt(plaintext)
decrypted = encryption_service.decrypt(ciphertext)
assert decrypted == plaintext
print('✅ Encryption working')
"
```

---

## Next Steps

- **Phase 3.3.3:** Output encoding (JSON-safe escaping)
- **Phase 3.3.4:** Advanced RBAC/ACL (scope-based access)
- **Phase 3.3.5:** Secrets rotation (automated key management)
- **Phase 3.4:** Data in-transit protection (TLS enforcement)

---

## Monitoring

Log all encryption/decryption errors:

```logs
[ERROR] encryption_service: Decryption failed (possible key mismatch)
```

→ Investigate immediately. Could indicate:
- Wrong ENCRYPTION_KEY
- Corrupted data
- Ciphertext from different service/key

---

## References

- Fernet: https://cryptography.io/en/latest/fernet/
- PBKDF2: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/
- AES: https://en.wikipedia.org/wiki/Advanced_Encryption_Standard
