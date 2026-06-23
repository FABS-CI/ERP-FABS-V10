"""
Advanced Rate Limiting Service — Per-user, per-endpoint, context-aware limits
Prevents brute force, DoS, and resource exhaustion attacks
"""

import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta, timezone
import asyncio

logger = logging.getLogger("fabsci.ratelimit")


class RateLimitScope(str, Enum):
    """Scope of rate limit"""
    GLOBAL = "global"  # All users combined
    IP = "ip"  # Per IP address
    USER = "user"  # Per authenticated user
    ENDPOINT = "endpoint"  # Per endpoint (all users)
    USER_ENDPOINT = "user_endpoint"  # Per user per endpoint (most specific)


class RateLimitTier(str, Enum):
    """User tier for rate limiting"""
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    SUPER_ADMIN = "super_admin"  # Unlimited


# Rate limit configuration by endpoint and tier
RATE_LIMIT_CONFIG = {
    # Authentication endpoints
    "/api/auth/login": {
        "scope": RateLimitScope.IP,
        "limits": {
            RateLimitTier.FREE: (5, 300),  # 5 per 5 minutes
            RateLimitTier.STANDARD: (10, 300),
            RateLimitTier.PREMIUM: (20, 300),
            RateLimitTier.ENTERPRISE: (50, 300),
            RateLimitTier.SUPER_ADMIN: (None, None),  # Unlimited
        }
    },
    
    # API read endpoints
    "/api/clients": {
        "scope": RateLimitScope.USER_ENDPOINT,
        "limits": {
            RateLimitTier.FREE: (30, 60),  # 30 per minute
            RateLimitTier.STANDARD: (100, 60),
            RateLimitTier.PREMIUM: (500, 60),
            RateLimitTier.ENTERPRISE: (None, None),  # Unlimited
            RateLimitTier.SUPER_ADMIN: (None, None),
        }
    },
    
    # API write endpoints
    "/api/clients:POST": {
        "scope": RateLimitScope.USER_ENDPOINT,
        "limits": {
            RateLimitTier.FREE: (5, 3600),  # 5 per hour
            RateLimitTier.STANDARD: (20, 3600),
            RateLimitTier.PREMIUM: (100, 3600),
            RateLimitTier.ENTERPRISE: (None, None),
            RateLimitTier.SUPER_ADMIN: (None, None),
        }
    },
    
    # Expensive operations (exports, reports)
    "/api/rapports/export": {
        "scope": RateLimitScope.USER_ENDPOINT,
        "limits": {
            RateLimitTier.FREE: (1, 3600),  # 1 per hour
            RateLimitTier.STANDARD: (5, 3600),
            RateLimitTier.PREMIUM: (20, 3600),
            RateLimitTier.ENTERPRISE: (100, 3600),
            RateLimitTier.SUPER_ADMIN: (None, None),
        }
    },
    
    # Default for unspecified endpoints
    "default": {
        "scope": RateLimitScope.USER_ENDPOINT,
        "limits": {
            RateLimitTier.FREE: (100, 60),
            RateLimitTier.STANDARD: (500, 60),
            RateLimitTier.PREMIUM: (2000, 60),
            RateLimitTier.ENTERPRISE: (None, None),
            RateLimitTier.SUPER_ADMIN: (None, None),
        }
    }
}


class RateLimitStatus:
    """Rate limit status for a request"""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int,
        reset_at: datetime,
        limit: Optional[int],
        retry_after: Optional[int] = None,
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_at = reset_at
        self.limit = limit
        self.retry_after = retry_after or (reset_at.timestamp() - datetime.now(timezone.utc).timestamp())


class RateLimitingService:
    """
    Advanced rate limiting with multiple scopes and adaptive limits.
    
    Uses Redis for distributed rate limiting across multiple servers.
    """
    
    def __init__(self, redis_client):
        """
        Args:
            redis_client: Async Redis connection
        """
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        identifier: str,  # IP, user_id, or combination
        endpoint: str,  # API path
        method: str,  # HTTP method
        user_tier: RateLimitTier = RateLimitTier.STANDARD,
    ) -> RateLimitStatus:
        """
        Check if request is allowed by rate limits.
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            user_tier: User's rate limit tier
            
        Returns:
            RateLimitStatus with allowed, remaining, reset_at
        """
        # Super admin always allowed
        if user_tier == RateLimitTier.SUPER_ADMIN:
            return RateLimitStatus(
                allowed=True,
                remaining=-1,
                reset_at=datetime.now(timezone.utc) + timedelta(hours=1),
                limit=None,
            )
        
        # Get config for this endpoint
        config = self._get_endpoint_config(endpoint, method)
        scope = config["scope"]
        limits = config["limits"].get(user_tier, config["limits"]["standard"])
        
        if limits[0] is None:  # Unlimited
            return RateLimitStatus(
                allowed=True,
                remaining=-1,
                reset_at=datetime.now(timezone.utc) + timedelta(hours=1),
                limit=None,
            )
        
        max_requests, window_seconds = limits
        
        # Build Redis key based on scope
        redis_key = self._build_redis_key(identifier, endpoint, method, scope)
        
        # Get current count
        try:
            current_count = await self.redis.incr(redis_key)
            
            # Set expiry on first increment
            if current_count == 1:
                await self.redis.expire(redis_key, window_seconds)
            
            # Check if over limit
            remaining = max(0, max_requests - current_count)
            reset_at = datetime.now(timezone.utc) + timedelta(seconds=window_seconds)
            
            allowed = current_count <= max_requests
            retry_after = None if allowed else int(window_seconds)
            
            return RateLimitStatus(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                limit=max_requests,
                retry_after=retry_after,
            )
        
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open (allow request) if Redis unavailable
            return RateLimitStatus(
                allowed=True,
                remaining=-1,
                reset_at=datetime.now(timezone.utc) + timedelta(hours=1),
                limit=None,
            )
    
    async def is_rate_limited(
        self,
        identifier: str,
        endpoint: str,
        method: str,
        user_tier: RateLimitTier = RateLimitTier.STANDARD,
    ) -> bool:
        """Quick check: is request rate limited?"""
        status = await self.check_rate_limit(identifier, endpoint, method, user_tier)
        return not status.allowed
    
    async def get_user_limits(
        self,
        user_id: str,
        user_tier: RateLimitTier,
    ) -> Dict[str, Any]:
        """Get current rate limit status for user across all endpoints"""
        endpoints = [
            "/api/clients",
            "/api/clients:POST",
            "/api/commandes",
            "/api/commandes:POST",
            "/api/factures",
            "/api/rapports/export",
        ]
        
        limits = {}
        for endpoint in endpoints:
            status = await self.check_rate_limit(user_id, endpoint, "GET", user_tier)
            limits[endpoint] = {
                "remaining": status.remaining,
                "limit": status.limit,
                "reset_at": status.reset_at.isoformat() if status.reset_at else None,
            }
        
        return limits
    
    async def reset_user_limits(self, user_id: str) -> bool:
        """Reset all rate limits for a user (admin function)"""
        try:
            # Find all keys for this user
            pattern = f"ratelimit:user:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Reset rate limits for user {user_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to reset user limits: {e}")
            return False
    
    async def block_ip(
        self,
        ip_address: str,
        duration_minutes: int = 60,
        reason: str = "Suspicious activity",
    ) -> bool:
        """Block an IP address temporarily"""
        try:
            redis_key = f"ratelimit:blocked:{ip_address}"
            await self.redis.setex(
                redis_key,
                duration_minutes * 60,
                reason
            )
            logger.warning(f"Blocked IP {ip_address} for {duration_minutes}min: {reason}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to block IP: {e}")
            return False
    
    async def is_ip_blocked(self, ip_address: str) -> Optional[str]:
        """Check if IP is blocked. Returns reason if blocked."""
        try:
            redis_key = f"ratelimit:blocked:{ip_address}"
            reason = await self.redis.get(redis_key)
            return reason
        
        except Exception as e:
            logger.error(f"Failed to check IP block: {e}")
            return None
    
    @staticmethod
    def _get_endpoint_config(endpoint: str, method: str) -> Dict[str, Any]:
        """Get rate limit config for endpoint"""
        # Try exact match with method
        key = f"{endpoint}:{method}"
        if key in RATE_LIMIT_CONFIG:
            return RATE_LIMIT_CONFIG[key]
        
        # Try endpoint without method
        if endpoint in RATE_LIMIT_CONFIG:
            return RATE_LIMIT_CONFIG[endpoint]
        
        # Use default
        return RATE_LIMIT_CONFIG["default"]
    
    @staticmethod
    def _build_redis_key(
        identifier: str,
        endpoint: str,
        method: str,
        scope: RateLimitScope,
    ) -> str:
        """Build Redis key for rate limiting"""
        if scope == RateLimitScope.GLOBAL:
            return f"ratelimit:global:{endpoint}"
        elif scope == RateLimitScope.IP:
            return f"ratelimit:ip:{identifier}:{endpoint}"
        elif scope == RateLimitScope.USER:
            return f"ratelimit:user:{identifier}"
        elif scope == RateLimitScope.ENDPOINT:
            return f"ratelimit:endpoint:{endpoint}"
        elif scope == RateLimitScope.USER_ENDPOINT:
            return f"ratelimit:user:{identifier}:{endpoint}:{method}"
        
        return f"ratelimit:default:{identifier}"


# Helper to get user tier from user object
def get_user_tier(user: Dict[str, Any]) -> RateLimitTier:
    """Determine user's rate limit tier based on role/subscription"""
    role = user.get("role")
    
    if role == "super_admin":
        return RateLimitTier.SUPER_ADMIN
    
    # Could also check subscription status, plan, etc.
    subscription = user.get("subscription_tier")
    if subscription:
        return RateLimitTier[subscription.upper()]
    
    return RateLimitTier.STANDARD


logger.info("✅ Advanced Rate Limiting Service initialized")
