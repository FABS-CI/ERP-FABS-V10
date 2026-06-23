"""
Enhanced Audit Service — Comprehensive logging of all security-relevant actions
Logs: IP address, user agent, request details, changes, outcomes
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import hashlib

logger = logging.getLogger("fabsci.audit")


class AuditAction(str, Enum):
    """Audit action types"""
    # Auth
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # Resource Management
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    
    # Permission & Access
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_CHANGE = "role_change"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    KEY_ROTATION = "key_rotation"
    SECURITY_PATCH = "security_patch"


class AuditLevel(str, Enum):
    """Severity level of audit event"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditEvent:
    """Structured audit event"""
    
    def __init__(
        self,
        action: AuditAction,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Args:
            action: Type of action (login, create, update, etc.)
            user_id: ID of user performing action
            resource_type: Type of resource affected (client, order, etc.)
            resource_id: ID of specific resource
            ip_address: Client IP address
            user_agent: Client user agent
            status: success, failure, denied
            level: Severity level (info, warning, critical)
            details: Additional context (extra data)
            changes: Before/after values for updates
            error_message: Error details if failed
            request_id: Unique request identifier
            session_id: User session ID
        """
        self.action = action
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
        self.level = level
        self.details = details or {}
        self.changes = changes or {}
        self.error_message = error_message
        self.request_id = request_id
        self.session_id = session_id
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            "audit_id": self._generate_audit_id(),
            "timestamp": self.timestamp,
            "timestamp_iso": self.timestamp.isoformat(),
            "action": self.action.value,
            "level": self.level.value,
            "status": self.status,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self._hash_ip(self.ip_address) if self.ip_address else None,
            "ip_address_masked": self._mask_ip(self.ip_address) if self.ip_address else None,
            "user_agent_hash": hashlib.sha256((self.user_agent or "").encode()).hexdigest()[:16],
            "session_id": self.session_id,
            "request_id": self.request_id,
            "details": self.details,
            "changes": self.changes,
            "error_message": self.error_message,
            "ttl_expires_at": self.timestamp,  # MongoDB TTL index for cleanup
        }
    
    @staticmethod
    def _generate_audit_id() -> str:
        """Generate unique audit ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"audit_{timestamp}"
    
    @staticmethod
    def _hash_ip(ip: str) -> str:
        """Hash IP for privacy (one-way)"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    @staticmethod
    def _mask_ip(ip: str) -> str:
        """Mask IP for readability (last octet hidden)"""
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
        return ip


class AuditService:
    """Audit logging service"""
    
    def __init__(self, db):
        """
        Args:
            db: Motor async MongoDB connection
        """
        self.db = db
    
    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log audit event to database.
        
        Args:
            event: AuditEvent to log
            
        Returns:
            True if logged successfully
        """
        try:
            result = await self.db.audit_log.insert_one(event.to_dict())
            
            # Log to file/console too for critical events
            if event.level == AuditLevel.CRITICAL:
                logger.critical(
                    f"AUDIT [{event.action.value}] {event.user_id} on {event.resource_type}"
                    f" {event.resource_id} — {event.status}"
                )
            else:
                logger.info(
                    f"AUDIT [{event.action.value}] {event.user_id} — {event.status}"
                )
            
            return result.inserted_id is not None
        
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    async def log_login(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """Log login attempt"""
        event = AuditEvent(
            action=AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE,
            user_id=user_id or "unknown",
            resource_type="auth",
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failure",
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            error_message=error_message,
            session_id=session_id,
        )
        return await self.log_event(event)
    
    async def log_resource_change(
        self,
        action: AuditAction,
        user_id: str,
        resource_type: str,
        resource_id: str,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """Log resource creation/update/deletion"""
        event = AuditEvent(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            details=details,
            request_id=request_id,
        )
        return await self.log_event(event)
    
    async def log_access_denied(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Log denied access attempt"""
        event = AuditEvent(
            action=AuditAction.ACCESS_DENIED,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="denied",
            level=AuditLevel.WARNING,
            details={"reason": reason},
        )
        return await self.log_event(event)
    
    async def log_suspicious_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log suspicious activity"""
        event = AuditEvent(
            action=AuditAction.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            resource_type="security",
            ip_address=ip_address,
            user_agent=user_agent,
            status="flagged",
            level=AuditLevel.CRITICAL,
            details={
                "activity_type": activity_type,
                "description": description,
                **(additional_data or {}),
            },
        )
        return await self.log_event(event)
    
    async def get_user_audit_log(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get audit log for specific user"""
        cursor = self.db.audit_log.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_resource_audit_log(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit log for specific resource"""
        cursor = self.db.audit_log.find(
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_failed_logins(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get failed login attempts in last N hours"""
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cursor = self.db.audit_log.find({
            "action": "login_failure",
            "timestamp": {"$gte": cutoff},
        }).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_critical_events(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get critical security events"""
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cursor = self.db.audit_log.find({
            "level": "critical",
            "timestamp": {"$gte": cutoff},
        }).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(limit)
    
    async def get_suspicious_ips(
        self,
        hours: int = 24,
        failure_threshold: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get IPs with multiple failed login attempts"""
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        pipeline = [
            {
                "$match": {
                    "action": "login_failure",
                    "timestamp": {"$gte": cutoff},
                    "ip_address_masked": {"$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$ip_address_masked",
                    "count": {"$sum": 1},
                    "last_attempt": {"$max": "$timestamp"},
                    "users": {"$push": "$user_id"},
                }
            },
            {
                "$match": {"count": {"$gte": failure_threshold}}
            },
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]
        
        return await self.db.audit_log.aggregate(pipeline).to_list(None)


# Audit event TTL configuration (cleanup old logs)
AUDIT_TTL_DAYS = {
    "info": 90,  # Keep info logs 90 days
    "warning": 180,  # Keep warnings 180 days
    "critical": 365,  # Keep critical events 1 year
}


logger.info("✅ Enhanced Audit Service initialized")
