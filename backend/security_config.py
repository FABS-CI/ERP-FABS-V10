"""
Security Configuration for ERP FABS-CI
Implements OWASP security standards and enterprise best practices
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import hashlib
import secrets
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SECURITY_CONFIG = {
    "jwt_secret": os.environ.get("JWT_SECRET", "dev-secret-key-2026-UNSAFE"),
    "jwt_algorithm": "HS256",
    "jwt_expiration_hours": 24,
    "token_refresh_hours": 12,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "api_key_length": 32,
    "password_min_length": 12,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_digits": True,
    "password_require_special": True,
    "rate_limit_requests": 100,
    "rate_limit_window_seconds": 60,
    "cors_allowed_origins": ["http://localhost:3000", "http://localhost:8000"],
    "cors_allow_credentials": True,
    "cors_allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "cors_allow_headers": ["*"],
    "https_required": True,
    "secure_cookies": True,
    "cookie_httponly": True,
    "cookie_samesite": "strict",
    "session_timeout_minutes": 30,
    "max_request_size_mb": 10,
}

# ============================================================================
# SECURITY HEADERS
# ============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

class PasswordValidator:
    """Validate password strength according to security policy"""
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """Validate password and return (is_valid, error_message)"""
        errors = []
        
        if len(password) < SECURITY_CONFIG["password_min_length"]:
            errors.append(f"Password must be at least {SECURITY_CONFIG['password_min_length']} characters")
        
        if SECURITY_CONFIG["password_require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        
        if SECURITY_CONFIG["password_require_lowercase"] and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        
        if SECURITY_CONFIG["password_require_digits"] and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        
        if SECURITY_CONFIG["password_require_special"] and not any(c in "!@#$%^&*" for c in password):
            errors.append("Password must contain special characters (!@#$%^&*)")
        
        return len(errors) == 0, " | ".join(errors)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hashed.hex()}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = hashed.split('$')
            hashed_attempt = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hashed_attempt.hex() == hash_hex
        except:
            return False

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

class JWTTokenManager:
    """Secure JWT token generation and validation"""
    
    @staticmethod
    def create_token(user_id: str, email: str, role: str = "user") -> str:
        """Create JWT token with expiration"""
        now = datetime.utcnow()
        exp = now + timedelta(hours=SECURITY_CONFIG["jwt_expiration_hours"])
        
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "iat": now,
            "exp": exp,
            "jti": secrets.token_urlsafe(16),  # JWT ID for token blacklist
        }
        
        token = jwt.encode(
            payload,
            SECURITY_CONFIG["jwt_secret"],
            algorithm=SECURITY_CONFIG["jwt_algorithm"]
        )
        
        logger.info(f"Token created for user {email}")
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                SECURITY_CONFIG["jwt_secret"],
                algorithms=[SECURITY_CONFIG["jwt_algorithm"]]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create long-lived refresh token"""
        now = datetime.utcnow()
        exp = now + timedelta(hours=SECURITY_CONFIG["token_refresh_hours"])
        
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": now,
            "exp": exp,
        }
        
        return jwt.encode(
            payload,
            SECURITY_CONFIG["jwt_secret"],
            algorithm=SECURITY_CONFIG["jwt_algorithm"]
        )

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

class APIKeyManager:
    """Manage API keys for service-to-service authentication"""
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and secret"""
        api_key = f"key_{secrets.token_urlsafe(24)}"
        api_secret = secrets.token_urlsafe(32)
        api_secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        return api_key, api_secret, api_secret_hash
    
    @staticmethod
    def validate_api_key(api_key: str, api_secret: str, stored_hash: str) -> bool:
        """Validate API key and secret"""
        api_secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        return api_secret_hash == stored_hash

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=SECURITY_CONFIG["rate_limit_window_seconds"])
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= SECURITY_CONFIG["rate_limit_requests"]:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Validate and sanitize user input"""
    
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', ';', '$', '|', '`']
    SQL_KEYWORDS = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'EXEC', 'SELECT']
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Remove potentially dangerous characters"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove dangerous characters
        for char in InputValidator.DANGEROUS_CHARS:
            value = value.replace(char, '')
        
        # Encode special characters
        return value.replace('\x00', '')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone format"""
        import re
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """Check for SQL injection attempts"""
        value_upper = value.upper()
        for keyword in InputValidator.SQL_KEYWORDS:
            if keyword in value_upper:
                logger.warning(f"SQL injection attempt detected: {value}")
                return False
        return True

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Log security-relevant events for compliance"""
    
    audit_log = []
    
    @staticmethod
    def log_login(user_id: str, email: str, success: bool, ip_address: str = "unknown"):
        """Log login attempt"""
        AuditLogger.audit_log.append({
            "event": "LOGIN",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "email": email,
            "success": success,
            "ip_address": ip_address,
        })
        logger.info(f"Login {'successful' if success else 'failed'} for {email}")
    
    @staticmethod
    def log_data_access(user_id: str, resource: str, action: str, ip_address: str = "unknown"):
        """Log data access"""
        AuditLogger.audit_log.append({
            "event": "DATA_ACCESS",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
        })
    
    @staticmethod
    def log_permission_denied(user_id: str, resource: str, ip_address: str = "unknown"):
        """Log permission denied"""
        AuditLogger.audit_log.append({
            "event": "PERMISSION_DENIED",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "ip_address": ip_address,
        })
        logger.warning(f"Permission denied for user {user_id} on {resource}")
    
    @staticmethod
    def get_audit_log() -> List[Dict]:
        """Get audit log"""
        return AuditLogger.audit_log[-1000:]  # Last 1000 events

# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

class RBAC:
    """Role-based access control"""
    
    ROLES = {
        "super_admin": ["*"],  # All permissions
        "admin": ["read:*", "write:*", "delete:own"],
        "directeur": ["read:*", "write:*"],
        "comptable": ["read:finance", "write:finance"],
        "commercial": ["read:clients,commandes", "write:clients,commandes"],
        "rh": ["read:rh", "write:rh"],
        "magasinier": ["read:stock", "write:stock"],
        "user": ["read:own"],
    }
    
    @staticmethod
    def has_permission(role: str, resource: str, action: str) -> bool:
        """Check if role has permission"""
        if role not in RBAC.ROLES:
            return False
        
        permissions = RBAC.ROLES[role]
        
        # Super admin has all permissions
        if "*" in permissions:
            return True
        
        # Check specific permission
        required_perm = f"{action}:{resource}"
        for perm in permissions:
            if perm == required_perm or perm.endswith("*"):
                return True
        
        return False

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example: Create user with hashed password
    validator = PasswordValidator()
    password = "SecurePass@2026!"
    is_valid, msg = validator.validate(password)
    print(f"Password valid: {is_valid} ({msg})")
    
    hashed = validator.hash_password(password)
    print(f"Hashed: {hashed}")
    
    is_correct = validator.verify_password(password, hashed)
    print(f"Verification: {is_correct}")
    
    # Example: Create JWT token
    token_manager = JWTTokenManager()
    token = token_manager.create_token("user_001", "user@example.com", "admin")
    print(f"\nToken: {token[:50]}...")
    
    payload = token_manager.verify_token(token)
    print(f"Verified payload: {payload}")
    
    # Example: Validate input
    input_validator = InputValidator()
    test_input = "'; DROP TABLE users; --"
    is_clean = input_validator.check_sql_injection(test_input)
    print(f"\nSQL injection check: {is_clean}")
    
    # Example: Rate limiting
    rate_limiter = RateLimiter()
    for i in range(5):
        allowed = rate_limiter.is_allowed("user_001")
        print(f"Request {i+1}: {'ALLOWED' if allowed else 'BLOCKED'}")
    
    # Example: RBAC
    print(f"\nRBAC test:")
    print(f"Admin can read clients: {RBAC.has_permission('admin', 'clients', 'read')}")
    print(f"Commercial can delete: {RBAC.has_permission('commercial', 'commandes', 'delete')}")
