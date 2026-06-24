"""
TOUR 4 PRIORITÉ 1: Session User Management
- Session creation, expiration, renewal
- Session revocation
- Multiple sessions per user
- Connection history & audit
- Anomaly detection
"""

import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging


class SessionStatus(Enum):
    """Session states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"


class SessionType(Enum):
    """Session types"""
    WEB = "web"
    API = "api"
    MOBILE = "mobile"
    ADMIN = "admin"


class UserSession:
    """Individual user session"""
    
    def __init__(self, user_id: str, session_id: str = None, session_type: str = "web"):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_type = session_type
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=24)
        self.status = SessionStatus.ACTIVE.value
        self.ip_address = None
        self.user_agent = None
        self.device_fingerprint = None
        self.refresh_count = 0
        self.failed_attempts = 0
        self.access_log: List[Dict] = []
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if session is valid and active"""
        return (
            self.status == SessionStatus.ACTIVE.value
            and not self.is_expired()
            and self.failed_attempts < 5
        )
    
    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def record_access(self, endpoint: str, method: str, status_code: int):
        """Record endpoint access"""
        self.access_log.append({
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "refresh_count": self.refresh_count,
            "is_expired": self.is_expired(),
            "access_log_count": len(self.access_log)
        }


class SessionManager:
    """Manage user sessions"""
    
    def __init__(self, logger: logging.Logger = None, db=None):
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.logger = logger or logging.getLogger("sessions")
        self.db = db  # For persistence (MongoDB)
        self.max_sessions_per_user = 5
        self.session_timeout_hours = 24
        self.inactivity_timeout_minutes = 60
    
    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str = None,
        session_type: str = "web"
    ) -> str:
        """Create new user session"""
        
        # Check if user has too many sessions
        user_sessions = self.user_sessions.get(user_id, [])
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest_session_id = user_sessions[0]
            self.revoke_session(oldest_session_id, reason="max_sessions_exceeded")
            user_sessions = self.user_sessions.get(user_id, [])
        
        # Create session
        session = UserSession(user_id, session_type=session_type)
        session.ip_address = ip_address
        session.user_agent = user_agent
        session.device_fingerprint = device_fingerprint
        
        # Store
        self.sessions[session.session_id] = session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session.session_id)
        
        # Persist
        if self.db:
            self._persist_session(session)
        
        # Audit
        self.logger.info(f"Session created", extra={
            "session_id": session.session_id,
            "user_id": user_id,
            "ip": ip_address,
            "type": session_type
        })
        
        return session.session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Check expiration
        if session.is_expired():
            self.revoke_session(session_id, reason="expired")
            return None
        
        # Check inactivity
        inactivity = (datetime.now() - session.last_activity).total_seconds() / 60
        if inactivity > self.inactivity_timeout_minutes:
            self.revoke_session(session_id, reason="inactivity")
            return None
        
        return session
    
    def refresh_session(self, session_id: str) -> bool:
        """Refresh session expiration"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Extend expiration
        session.expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)
        session.refresh_count += 1
        session.touch()
        
        # Persist
        if self.db:
            self._persist_session(session)
        
        self.logger.debug(f"Session refreshed", extra={
            "session_id": session_id,
            "refresh_count": session.refresh_count
        })
        
        return True
    
    def revoke_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """Revoke session"""
        session = self.sessions.get(session_id)
        
        if not session:
            return False
        
        # Mark as revoked
        session.status = SessionStatus.REVOKED.value
        
        # Remove from active
        if session.user_id in self.user_sessions:
            if session_id in self.user_sessions[session.user_id]:
                self.user_sessions[session.user_id].remove(session_id)
        
        # Persist
        if self.db:
            self._persist_session(session)
        
        # Audit
        self.logger.info(f"Session revoked", extra={
            "session_id": session_id,
            "user_id": session.user_id,
            "reason": reason
        })
        
        return True
    
    def revoke_all_user_sessions(self, user_id: str, reason: str = "admin_action") -> int:
        """Revoke all sessions for user"""
        count = 0
        
        if user_id in self.user_sessions:
            session_ids = list(self.user_sessions[user_id])
            for session_id in session_ids:
                self.revoke_session(session_id, reason=reason)
                count += 1
        
        self.logger.warning(f"All sessions revoked for user", extra={
            "user_id": user_id,
            "count": count,
            "reason": reason
        })
        
        return count
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for user"""
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session:
                sessions.append(session.to_dict())
        
        return sessions
    
    def validate_session(self, session_id: str, ip_address: str = None) -> bool:
        """Validate session and check for anomalies"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Check IP change (anomaly detection)
        if ip_address and session.ip_address and ip_address != session.ip_address:
            session.failed_attempts += 1
            self.logger.warning(f"Possible session hijacking detected", extra={
                "session_id": session_id,
                "user_id": session.user_id,
                "expected_ip": session.ip_address,
                "actual_ip": ip_address,
                "attempts": session.failed_attempts
            })
            
            # Lock if too many anomalies
            if session.failed_attempts >= 5:
                session.status = SessionStatus.LOCKED.value
                return False
        
        # Update activity
        session.touch()
        
        return True
    
    def record_endpoint_access(
        self,
        session_id: str,
        endpoint: str,
        method: str,
        status_code: int
    ):
        """Record endpoint access for session"""
        session = self.sessions.get(session_id)
        if session:
            session.record_access(endpoint, method, status_code)
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired = []
        
        for session_id, session in list(self.sessions.items()):
            if session.is_expired():
                expired.append(session_id)
                del self.sessions[session_id]
                
                # Remove from user index
                if session.user_id in self.user_sessions:
                    if session_id in self.user_sessions[session.user_id]:
                        self.user_sessions[session.user_id].remove(session_id)
        
        if expired:
            self.logger.info(f"Cleaned up expired sessions", extra={
                "count": len(expired)
            })
        
        return len(expired)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for s in self.sessions.values()
            if s.status == SessionStatus.ACTIVE.value and not s.is_expired()
        )
        expired_sessions = sum(
            1 for s in self.sessions.values()
            if s.is_expired()
        )
        revoked_sessions = sum(
            1 for s in self.sessions.values()
            if s.status == SessionStatus.REVOKED.value
        )
        
        return {
            "total": total_sessions,
            "active": active_sessions,
            "expired": expired_sessions,
            "revoked": revoked_sessions,
            "unique_users": len(self.user_sessions)
        }
    
    def _persist_session(self, session: UserSession):
        """Persist session to database"""
        if not self.db:
            return
        
        try:
            self.db["sessions"].update_one(
                {"session_id": session.session_id},
                {
                    "$set": {
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "session_type": session.session_type,
                        "created_at": session.created_at,
                        "last_activity": session.last_activity,
                        "expires_at": session.expires_at,
                        "status": session.status,
                        "ip_address": session.ip_address,
                        "user_agent": session.user_agent,
                        "device_fingerprint": session.device_fingerprint,
                        "refresh_count": session.refresh_count
                    }
                },
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Failed to persist session: {e}")
    
    def generate_session_token(self, session_id: str, secret: str) -> str:
        """Generate session token"""
        data = f"{session_id}:{datetime.now().isoformat()}:{secret}"
        return hashlib.sha256(data.encode()).hexdigest()


class SessionAuditLogger:
    """Audit all session-related events"""
    
    def __init__(self, logger: logging.Logger = None, db=None):
        self.logger = logger or logging.getLogger("session_audit")
        self.db = db
    
    def log_login(self, user_id: str, session_id: str, ip: str, user_agent: str):
        """Log successful login"""
        event = {
            "timestamp": datetime.now(),
            "event": "LOGIN",
            "user_id": user_id,
            "session_id": session_id,
            "ip_address": ip,
            "user_agent": user_agent,
            "severity": "low"
        }
        
        self.logger.info(f"User login", extra=event)
        if self.db:
            self.db["session_audit"].insert_one(event)
    
    def log_logout(self, user_id: str, session_id: str):
        """Log logout"""
        event = {
            "timestamp": datetime.now(),
            "event": "LOGOUT",
            "user_id": user_id,
            "session_id": session_id,
            "severity": "low"
        }
        
        self.logger.info(f"User logout", extra=event)
        if self.db:
            self.db["session_audit"].insert_one(event)
    
    def log_session_hijacking_attempt(self, session_id: str, user_id: str, expected_ip: str, actual_ip: str):
        """Log possible session hijacking"""
        event = {
            "timestamp": datetime.now(),
            "event": "SESSION_HIJACKING_ATTEMPT",
            "session_id": session_id,
            "user_id": user_id,
            "expected_ip": expected_ip,
            "actual_ip": actual_ip,
            "severity": "critical"
        }
        
        self.logger.critical(f"Session hijacking attempt detected", extra=event)
        if self.db:
            self.db["session_audit"].insert_one(event)
    
    def log_session_revocation(self, user_id: str, session_id: str, reason: str):
        """Log session revocation"""
        event = {
            "timestamp": datetime.now(),
            "event": "SESSION_REVOKED",
            "user_id": user_id,
            "session_id": session_id,
            "reason": reason,
            "severity": "medium"
        }
        
        self.logger.info(f"Session revoked", extra=event)
        if self.db:
            self.db["session_audit"].insert_one(event)
    
    def get_user_login_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user login history"""
        if not self.db:
            return []
        
        return list(
            self.db["session_audit"].find(
                {"user_id": user_id, "event": "LOGIN"}
            ).sort("timestamp", -1).limit(limit)
        )
    
    def get_session_events(self, session_id: str) -> List[Dict]:
        """Get all events for session"""
        if not self.db:
            return []
        
        return list(
            self.db["session_audit"].find(
                {"session_id": session_id}
            ).sort("timestamp", -1)
        )


# Global instances
session_manager = None
session_audit_logger = None


def initialize_sessions(logger: logging.Logger = None, db=None) -> Dict[str, Any]:
    """Initialize session management"""
    global session_manager, session_audit_logger
    
    session_manager = SessionManager(logger, db)
    session_audit_logger = SessionAuditLogger(logger, db)
    
    return {
        "session_manager": session_manager,
        "session_audit_logger": session_audit_logger
    }


def get_session_components() -> Dict[str, Any]:
    """Get session components"""
    return {
        "session_manager": session_manager,
        "session_audit_logger": session_audit_logger
    }
