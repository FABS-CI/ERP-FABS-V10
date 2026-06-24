"""
TOUR 4 PRIORITÉ 2: API Key Management
- Secure generation
- Hashing
- Rotation
- Revocation
- Expiration
- Permissions per key
- Audit logging
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import json


class KeyStatus(Enum):
    """API Key status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class KeyPermission(Enum):
    """API Key permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class APIKey:
    """API Key definition"""
    
    def __init__(self, name: str, user_id: str, key_id: str = None):
        self.key_id = key_id or str(uuid.uuid4())
        self.name = name
        self.user_id = user_id
        self.key_hash = None  # Will be set after generation
        self.key_secret = None  # Generated once, never stored plain
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=365)
        self.last_used = None
        self.status = KeyStatus.ACTIVE.value
        self.permissions: List[str] = [KeyPermission.READ.value]
        self.rate_limit = 1000  # requests per hour
        self.allowed_ips: List[str] = []  # If empty, allow all
        self.description = ""
        self.rotated_at = None
        self.rotation_count = 0
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if key is valid"""
        return (
            self.status == KeyStatus.ACTIVE.value
            and not self.is_expired()
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if key has permission"""
        if KeyPermission.ADMIN.value in self.permissions:
            return True
        return permission in self.permissions
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if not self.allowed_ips:
            return True
        return ip in self.allowed_ips
    
    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "key_id": self.key_id,
            "name": self.name,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "status": self.status,
            "permissions": self.permissions,
            "rate_limit": self.rate_limit,
            "allowed_ips": self.allowed_ips,
            "description": self.description,
            "is_expired": self.is_expired(),
            "rotation_count": self.rotation_count
        }
        
        if include_secret and self.key_secret:
            data["key_secret"] = self.key_secret
        
        return data


class APIKeyManager:
    """Manage API keys"""
    
    def __init__(self, logger: logging.Logger = None, db=None):
        self.logger = logger or logging.getLogger("api_keys")
        self.db = db
        self.keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self.key_hashes: Dict[str, str] = {}  # hash -> key_id
    
    def generate_key(
        self,
        name: str,
        user_id: str,
        permissions: List[str] = None,
        expires_in_days: int = 365,
        allowed_ips: List[str] = None,
        description: str = ""
    ) -> tuple[str, str]:
        """Generate new API key (returns key_id and secret)"""
        
        # Generate key
        api_key = APIKey(name, user_id)
        api_key.key_secret = secrets.token_urlsafe(32)
        api_key.expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        if permissions:
            api_key.permissions = permissions
        
        if allowed_ips:
            api_key.allowed_ips = allowed_ips
        
        api_key.description = description
        
        # Hash key
        api_key.key_hash = self._hash_key(api_key.key_secret)
        
        # Store
        self.keys[api_key.key_id] = api_key
        self.key_hashes[api_key.key_hash] = api_key.key_id
        
        # Persist
        if self.db:
            self._persist_key(api_key)
        
        # Audit
        self.logger.info(f"API key generated", extra={
            "key_id": api_key.key_id,
            "user_id": user_id,
            "name": name,
            "permissions": permissions,
            "expires_in_days": expires_in_days
        })
        
        return api_key.key_id, api_key.key_secret
    
    def verify_key(self, key_secret: str, ip_address: str = None) -> Optional[APIKey]:
        """Verify API key and return it"""
        
        # Hash provided key
        key_hash = self._hash_key(key_secret)
        
        # Lookup
        key_id = self.key_hashes.get(key_hash)
        if not key_id:
            self.logger.warning(f"Invalid API key attempt")
            return None
        
        key = self.keys.get(key_id)
        if not key:
            return None
        
        # Check validity
        if not key.is_valid():
            self.logger.warning(f"Invalid API key (expired/revoked)", extra={
                "key_id": key_id,
                "status": key.status
            })
            return None
        
        # Check IP
        if ip_address and not key.is_ip_allowed(ip_address):
            self.logger.warning(f"API key IP not allowed", extra={
                "key_id": key_id,
                "expected_ips": key.allowed_ips,
                "actual_ip": ip_address
            })
            return None
        
        # Update last used
        key.last_used = datetime.now()
        if self.db:
            self._persist_key(key)
        
        return key
    
    def revoke_key(self, key_id: str, reason: str = "user_revocation") -> bool:
        """Revoke API key"""
        key = self.keys.get(key_id)
        
        if not key:
            return False
        
        key.status = KeyStatus.REVOKED.value
        
        # Persist
        if self.db:
            self._persist_key(key)
        
        # Audit
        self.logger.warning(f"API key revoked", extra={
            "key_id": key_id,
            "user_id": key.user_id,
            "reason": reason
        })
        
        return True
    
    def rotate_key(self, key_id: str) -> Optional[tuple[str, str]]:
        """Rotate API key (generate new secret, keep ID)"""
        key = self.keys.get(key_id)
        
        if not key:
            return None
        
        # Remove old hash
        if key.key_hash in self.key_hashes:
            del self.key_hashes[key.key_hash]
        
        # Generate new secret
        new_secret = secrets.token_urlsafe(32)
        new_hash = self._hash_key(new_secret)
        
        key.key_secret = new_secret
        key.key_hash = new_hash
        key.rotated_at = datetime.now()
        key.rotation_count += 1
        
        # Update hash map
        self.key_hashes[new_hash] = key_id
        
        # Persist
        if self.db:
            self._persist_key(key)
        
        # Audit
        self.logger.info(f"API key rotated", extra={
            "key_id": key_id,
            "user_id": key.user_id,
            "rotation_count": key.rotation_count
        })
        
        return key_id, new_secret
    
    def get_key(self, key_id: str) -> Optional[APIKey]:
        """Get key by ID"""
        return self.keys.get(key_id)
    
    def get_user_keys(self, user_id: str) -> List[Dict]:
        """Get all keys for user"""
        keys = []
        
        for key in self.keys.values():
            if key.user_id == user_id:
                keys.append(key.to_dict())
        
        return keys
    
    def revoke_all_user_keys(self, user_id: str, reason: str = "user_deactivation") -> int:
        """Revoke all keys for user"""
        count = 0
        
        for key_id, key in list(self.keys.items()):
            if key.user_id == user_id:
                self.revoke_key(key_id, reason=reason)
                count += 1
        
        self.logger.warning(f"All API keys revoked for user", extra={
            "user_id": user_id,
            "count": count,
            "reason": reason
        })
        
        return count
    
    def get_key_stats(self) -> Dict[str, Any]:
        """Get API key statistics"""
        total = len(self.keys)
        active = sum(1 for k in self.keys.values() if k.is_valid())
        expired = sum(1 for k in self.keys.values() if k.is_expired())
        revoked = sum(1 for k in self.keys.values() if k.status == KeyStatus.REVOKED.value)
        
        return {
            "total": total,
            "active": active,
            "expired": expired,
            "revoked": revoked,
            "unique_users": len(set(k.user_id for k in self.keys.values()))
        }
    
    def cleanup_expired_keys(self) -> int:
        """Mark expired keys"""
        count = 0
        
        for key in self.keys.values():
            if key.is_expired() and key.status == KeyStatus.ACTIVE.value:
                key.status = KeyStatus.EXPIRED.value
                if self.db:
                    self._persist_key(key)
                count += 1
        
        if count > 0:
            self.logger.info(f"Marked expired API keys", extra={"count": count})
        
        return count
    
    def _hash_key(self, key_secret: str) -> str:
        """Hash API key"""
        return hashlib.sha256(key_secret.encode()).hexdigest()
    
    def _persist_key(self, key: APIKey):
        """Persist key to database"""
        if not self.db:
            return
        
        try:
            self.db["api_keys"].update_one(
                {"key_id": key.key_id},
                {
                    "$set": {
                        "key_id": key.key_id,
                        "name": key.name,
                        "user_id": key.user_id,
                        "key_hash": key.key_hash,
                        "created_at": key.created_at,
                        "expires_at": key.expires_at,
                        "last_used": key.last_used,
                        "status": key.status,
                        "permissions": key.permissions,
                        "rate_limit": key.rate_limit,
                        "allowed_ips": key.allowed_ips,
                        "description": key.description,
                        "rotation_count": key.rotation_count
                    }
                },
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Failed to persist API key: {e}")


class APIKeyAuditLogger:
    """Audit API key events"""
    
    def __init__(self, logger: logging.Logger = None, db=None):
        self.logger = logger or logging.getLogger("api_key_audit")
        self.db = db
    
    def log_key_usage(self, key_id: str, user_id: str, endpoint: str, method: str, ip: str):
        """Log API key usage"""
        event = {
            "timestamp": datetime.now(),
            "event": "KEY_USED",
            "key_id": key_id,
            "user_id": user_id,
            "endpoint": endpoint,
            "method": method,
            "ip_address": ip,
            "severity": "low"
        }
        
        if self.db:
            self.db["api_key_audit"].insert_one(event)
    
    def log_invalid_key(self, ip: str, endpoint: str):
        """Log invalid API key attempt"""
        event = {
            "timestamp": datetime.now(),
            "event": "INVALID_KEY",
            "ip_address": ip,
            "endpoint": endpoint,
            "severity": "high"
        }
        
        self.logger.warning(f"Invalid API key attempt", extra=event)
        if self.db:
            self.db["api_key_audit"].insert_one(event)
    
    def get_key_usage_history(self, key_id: str, limit: int = 100) -> List[Dict]:
        """Get usage history for key"""
        if not self.db:
            return []
        
        return list(
            self.db["api_key_audit"].find(
                {"key_id": key_id, "event": "KEY_USED"}
            ).sort("timestamp", -1).limit(limit)
        )


# Global instances
api_key_manager = None
api_key_audit_logger = None


def initialize_api_keys(logger: logging.Logger = None, db=None) -> Dict[str, Any]:
    """Initialize API key management"""
    global api_key_manager, api_key_audit_logger
    
    api_key_manager = APIKeyManager(logger, db)
    api_key_audit_logger = APIKeyAuditLogger(logger, db)
    
    return {
        "api_key_manager": api_key_manager,
        "api_key_audit_logger": api_key_audit_logger
    }


def get_api_key_components() -> Dict[str, Any]:
    """Get API key components"""
    return {
        "api_key_manager": api_key_manager,
        "api_key_audit_logger": api_key_audit_logger
    }
