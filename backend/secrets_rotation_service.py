"""
Secrets Rotation Service — Automated key rotation for JWT, encryption, signing keys
Supports zero-downtime key rotation with gradual migration
"""

import logging
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import json

logger = logging.getLogger("fabsci.rotation")


class SecretType(str, Enum):
    """Type of secret to rotate"""
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    SIGNING_KEY = "signing_key"
    DATABASE_PASSWORD = "db_password"
    REDIS_PASSWORD = "redis_password"
    API_KEY = "api_key"


class RotationPolicy(str, Enum):
    """Key rotation policy"""
    MANUAL = "manual"  # Manual rotation only
    DAILY = "daily"  # Every day
    WEEKLY = "weekly"  # Every 7 days
    MONTHLY = "monthly"  # Every 30 days
    QUARTERLY = "quarterly"  # Every 90 days


class SecretMetadata:
    """Metadata for a secret"""
    
    def __init__(
        self,
        secret_type: SecretType,
        current_value: str,
        created_at: datetime,
        rotation_policy: RotationPolicy = RotationPolicy.MONTHLY,
        last_rotated_at: Optional[datetime] = None,
        next_rotation_at: Optional[datetime] = None,
    ):
        self.secret_type = secret_type
        self.current_value = current_value
        self.created_at = created_at
        self.rotation_policy = rotation_policy
        self.last_rotated_at = last_rotated_at
        self.next_rotation_at = next_rotation_at or self._calculate_next_rotation()
        self.previous_values: List[str] = []  # For grace period
    
    def _calculate_next_rotation(self) -> datetime:
        """Calculate next rotation time based on policy"""
        base_time = self.last_rotated_at or self.created_at
        
        if self.rotation_policy == RotationPolicy.MANUAL:
            return base_time + timedelta(days=365)  # Far future
        elif self.rotation_policy == RotationPolicy.DAILY:
            return base_time + timedelta(days=1)
        elif self.rotation_policy == RotationPolicy.WEEKLY:
            return base_time + timedelta(weeks=1)
        elif self.rotation_policy == RotationPolicy.MONTHLY:
            return base_time + timedelta(days=30)
        elif self.rotation_policy == RotationPolicy.QUARTERLY:
            return base_time + timedelta(days=90)
        
        return base_time + timedelta(days=30)  # Default
    
    def is_due_for_rotation(self) -> bool:
        """Check if key is due for rotation"""
        return datetime.now(timezone.utc) >= self.next_rotation_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "secret_type": self.secret_type.value,
            "created_at": self.created_at.isoformat(),
            "last_rotated_at": self.last_rotated_at.isoformat() if self.last_rotated_at else None,
            "next_rotation_at": self.next_rotation_at.isoformat(),
            "rotation_policy": self.rotation_policy.value,
            "rotation_due": self.is_due_for_rotation(),
            "previous_values_count": len(self.previous_values),
        }


class SecretsRotationService:
    """
    Manages secrets rotation with:
    - Zero-downtime rotation (old key + new key both valid)
    - Audit logging of all rotations
    - Grace period for old keys
    - Policy-based scheduling
    """
    
    def __init__(self, db, audit_service=None):
        """
        Args:
            db: Motor async MongoDB connection
            audit_service: Optional AuditService for logging rotations
        """
        self.db = db
        self.audit_service = audit_service
        self.grace_period_days = 7  # Old keys valid for 7 days
    
    async def get_secret_metadata(self, secret_type: SecretType) -> Optional[SecretMetadata]:
        """Get metadata for a secret"""
        try:
            doc = await self.db.secrets_rotation.find_one(
                {"secret_type": secret_type.value}
            )
            
            if not doc:
                return None
            
            metadata = SecretMetadata(
                secret_type=SecretType(doc["secret_type"]),
                current_value=doc["current_value"],
                created_at=doc["created_at"],
                rotation_policy=RotationPolicy(doc.get("rotation_policy", "monthly")),
                last_rotated_at=doc.get("last_rotated_at"),
            )
            metadata.previous_values = doc.get("previous_values", [])
            
            return metadata
        
        except Exception as e:
            logger.error(f"Failed to get secret metadata: {e}")
            return None
    
    async def rotate_secret(
        self,
        secret_type: SecretType,
        new_value: Optional[str] = None,
        user_id: Optional[str] = None,
        reason: str = "Scheduled rotation",
    ) -> Dict[str, Any]:
        """
        Rotate a secret (generate new key).
        
        Args:
            secret_type: Type of secret to rotate
            new_value: New secret value (if None, generate random)
            user_id: ID of user performing rotation (for audit)
            reason: Reason for rotation
            
        Returns:
            Rotation result with old_key_valid_until
        """
        try:
            # Get current metadata
            metadata = await self.get_secret_metadata(secret_type)
            
            if not metadata:
                logger.error(f"Secret {secret_type.value} not found")
                return {"success": False, "error": "Secret not found"}
            
            # Generate or use provided value
            if new_value is None:
                new_value = secrets.token_urlsafe(32)
            
            # Save old value for grace period
            old_value = metadata.current_value
            previous_values = metadata.previous_values.copy()
            
            # Keep last 2 old keys for grace period
            if len(previous_values) >= 2:
                previous_values.pop(0)
            previous_values.append({
                "value": old_value,
                "rotated_at": datetime.now(timezone.utc).isoformat(),
                "valid_until": (datetime.now(timezone.utc) + timedelta(days=self.grace_period_days)).isoformat(),
            })
            
            # Update in database
            old_valid_until = datetime.now(timezone.utc) + timedelta(days=self.grace_period_days)
            
            await self.db.secrets_rotation.update_one(
                {"secret_type": secret_type.value},
                {
                    "$set": {
                        "current_value": new_value,
                        "last_rotated_at": datetime.now(timezone.utc),
                        "next_rotation_at": (
                            datetime.now(timezone.utc) + timedelta(days=30)
                        ),
                        "previous_values": previous_values,
                        "updated_at": datetime.now(timezone.utc),
                    }
                }
            )
            
            # Log rotation event
            if self.audit_service:
                from audit_service import AuditAction, AuditLevel
                await self.audit_service.log_event(
                    AuditEvent(
                        action=AuditAction.KEY_ROTATION,
                        user_id=user_id or "system",
                        resource_type="security",
                        resource_id=secret_type.value,
                        level=AuditLevel.CRITICAL,
                        details={
                            "secret_type": secret_type.value,
                            "reason": reason,
                            "old_key_hash": hashlib.sha256(old_value.encode()).hexdigest()[:16],
                            "new_key_hash": hashlib.sha256(new_value.encode()).hexdigest()[:16],
                            "grace_period_days": self.grace_period_days,
                        }
                    )
                )
            
            logger.critical(
                f"Secret rotated: {secret_type.value} | "
                f"Reason: {reason} | By: {user_id or 'system'} | "
                f"Old key valid until: {old_valid_until.isoformat()}"
            )
            
            return {
                "success": True,
                "secret_type": secret_type.value,
                "rotated_at": datetime.now(timezone.utc).isoformat(),
                "old_key_valid_until": old_valid_until.isoformat(),
                "grace_period_days": self.grace_period_days,
                "new_key_hash": hashlib.sha256(new_value.encode()).hexdigest()[:16],
            }
        
        except Exception as e:
            logger.error(f"Secret rotation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_secrets_status(self) -> Dict[str, Any]:
        """Get rotation status for all secrets"""
        try:
            secrets_list = await self.db.secrets_rotation.find({}).to_list(None)
            
            status = {}
            for doc in secrets_list:
                secret_type = doc["secret_type"]
                status[secret_type] = {
                    "created_at": doc.get("created_at", {}).isoformat() if hasattr(doc.get("created_at"), 'isoformat') else str(doc.get("created_at")),
                    "last_rotated_at": doc.get("last_rotated_at", {}).isoformat() if hasattr(doc.get("last_rotated_at"), 'isoformat') else str(doc.get("last_rotated_at")),
                    "next_rotation_at": doc.get("next_rotation_at", {}).isoformat() if hasattr(doc.get("next_rotation_at"), 'isoformat') else str(doc.get("next_rotation_at")),
                    "rotation_policy": doc.get("rotation_policy", "unknown"),
                    "rotation_due": datetime.fromisoformat(str(doc.get("next_rotation_at")).replace('Z', '+00:00')) <= datetime.now(timezone.utc) if doc.get("next_rotation_at") else False,
                    "previous_keys_count": len(doc.get("previous_values", [])),
                }
            
            return {
                "status": "ok",
                "secrets": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to get secrets status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def validate_old_secret(
        self,
        secret_type: SecretType,
        value: str,
    ) -> bool:
        """
        Validate that a secret is either current or in grace period.
        Used for decrypting old data or validating old JWTs.
        
        Args:
            secret_type: Type of secret
            value: Secret value to validate
            
        Returns:
            True if valid (current or in grace period)
        """
        try:
            metadata = await self.get_secret_metadata(secret_type)
            
            if not metadata:
                return False
            
            # Check current value
            if value == metadata.current_value:
                return True
            
            # Check previous values within grace period
            for prev in metadata.previous_values:
                if value == prev.get("value"):
                    valid_until = datetime.fromisoformat(
                        prev["valid_until"].replace('Z', '+00:00')
                    )
                    if datetime.now(timezone.utc) <= valid_until:
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to validate old secret: {e}")
            return False
    
    async def schedule_rotation_check(self) -> List[str]:
        """
        Check all secrets and return list of those due for rotation.
        Should be called periodically (e.g., daily by cron job).
        
        Returns:
            List of secret types due for rotation
        """
        try:
            secrets_list = await self.db.secrets_rotation.find({}).to_list(None)
            
            due_for_rotation = []
            for doc in secrets_list:
                next_rotation = doc.get("next_rotation_at")
                if next_rotation and datetime.fromisoformat(str(next_rotation).replace('Z', '+00:00')) <= datetime.now(timezone.utc):
                    due_for_rotation.append(doc["secret_type"])
            
            if due_for_rotation:
                logger.warning(f"Secrets due for rotation: {due_for_rotation}")
            
            return due_for_rotation
        
        except Exception as e:
            logger.error(f"Failed to check rotation schedule: {e}")
            return []


# Rotation schedule for background job
ROTATION_SCHEDULES = {
    SecretType.JWT_SECRET: RotationPolicy.QUARTERLY,  # Every 90 days
    SecretType.ENCRYPTION_KEY: RotationPolicy.QUARTERLY,  # Every 90 days
    SecretType.SIGNING_KEY: RotationPolicy.QUARTERLY,  # Every 90 days
    SecretType.API_KEY: RotationPolicy.MONTHLY,  # Every 30 days
}


async def init_secrets_rotation(db):
    """
    Initialize secrets rotation collection with defaults.
    Call once during app startup.
    
    Args:
        db: Motor async MongoDB connection
    """
    try:
        for secret_type in SecretType:
            # Check if already initialized
            exists = await db.secrets_rotation.find_one(
                {"secret_type": secret_type.value}
            )
            
            if not exists:
                # Get current value from environment or generate
                env_key = secret_type.value.upper()
                current_value = None  # Would come from environment in production
                
                if current_value is None:
                    current_value = secrets.token_urlsafe(32)
                
                # Create initial document
                await db.secrets_rotation.insert_one({
                    "secret_type": secret_type.value,
                    "current_value": current_value,
                    "created_at": datetime.now(timezone.utc),
                    "last_rotated_at": None,
                    "next_rotation_at": datetime.now(timezone.utc) + timedelta(days=90),
                    "rotation_policy": ROTATION_SCHEDULES.get(secret_type, RotationPolicy.MONTHLY).value,
                    "previous_values": [],
                    "updated_at": datetime.now(timezone.utc),
                })
                
                logger.info(f"Initialized {secret_type.value} rotation")
    
    except Exception as e:
        logger.error(f"Failed to initialize secrets rotation: {e}")


logger.info("✅ Secrets Rotation Service initialized")
