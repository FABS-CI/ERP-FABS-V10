"""
TOUR 4 PRIORITÉ 3: Redis Integration
- Sessions storage
- Cache layer
- Rate limiting
- Distributed metrics
- Lightweight queues
- Distributed locks
"""

import json
import redis
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import hashlib


class RedisClient:
    """Redis integration wrapper"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        logger: logging.Logger = None,
        ssl: bool = False
    ):
        self.logger = logger or logging.getLogger("redis")
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                ssl=ssl,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            self.logger.info(f"✓ Redis connected ({host}:{port})")
        except Exception as e:
            self.logger.error(f"✗ Redis connection failed: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            return self.client is not None and self.client.ping()
        except:
            return False
    
    # ==================== SESSION STORAGE ====================
    
    def store_session(self, session_id: str, session_data: Dict, ttl_hours: int = 24):
        """Store session in Redis"""
        if not self.client:
            return False
        
        try:
            key = f"session:{session_id}"
            ttl = ttl_hours * 3600
            
            self.client.setex(
                key,
                ttl,
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to store session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session from Redis"""
        if not self.client:
            return None
        
        try:
            key = f"session:{session_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            self.logger.error(f"Failed to get session: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        if not self.client:
            return False
        
        try:
            key = f"session:{session_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for user"""
        if not self.client:
            return []
        
        try:
            pattern = f"session:*"
            sessions = []
            
            for key in self.client.scan_iter(pattern):
                data = self.client.get(key)
                if data:
                    session = json.loads(data)
                    if session.get("user_id") == user_id:
                        sessions.append(session)
            
            return sessions
        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []
    
    # ==================== CACHE ====================
    
    def cache_set(self, key: str, value: Any, ttl_minutes: int = 60):
        """Set cache value"""
        if not self.client:
            return False
        
        try:
            cache_key = f"cache:{key}"
            ttl = ttl_minutes * 60
            
            self.client.setex(
                cache_key,
                ttl,
                json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to set cache: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.client:
            return None
        
        try:
            cache_key = f"cache:{key}"
            data = self.client.get(cache_key)
            
            if not data:
                return None
            
            # Try JSON parse, otherwise return as string
            try:
                return json.loads(data)
            except:
                return data
        except Exception as e:
            self.logger.error(f"Failed to get cache: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.client:
            return False
        
        try:
            cache_key = f"cache:{key}"
            self.client.delete(cache_key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete cache: {e}")
            return False
    
    def cache_clear(self):
        """Clear all cache"""
        if not self.client:
            return False
        
        try:
            pattern = "cache:*"
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    # ==================== RATE LIMITING ====================
    
    def rate_limit_check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check rate limit (returns True if allowed)"""
        if not self.client:
            return True  # Allow if Redis down
        
        try:
            rate_key = f"rate:{key}"
            current = self.client.incr(rate_key)
            
            if current == 1:
                self.client.expire(rate_key, window_seconds)
            
            return current <= limit
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return True
    
    def rate_limit_reset(self, key: str) -> bool:
        """Reset rate limit counter"""
        if not self.client:
            return False
        
        try:
            rate_key = f"rate:{key}"
            self.client.delete(rate_key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset rate limit: {e}")
            return False
    
    # ==================== DISTRIBUTED METRICS ====================
    
    def increment_metric(self, metric_name: str, value: int = 1) -> bool:
        """Increment metric counter"""
        if not self.client:
            return False
        
        try:
            key = f"metric:{metric_name}"
            self.client.incrby(key, value)
            self.client.expire(key, 86400)  # 24 hours
            return True
        except Exception as e:
            self.logger.error(f"Failed to increment metric: {e}")
            return False
    
    def get_metric(self, metric_name: str) -> int:
        """Get metric value"""
        if not self.client:
            return 0
        
        try:
            key = f"metric:{metric_name}"
            value = self.client.get(key)
            return int(value) if value else 0
        except Exception as e:
            self.logger.error(f"Failed to get metric: {e}")
            return 0
    
    def set_gauge(self, gauge_name: str, value: float) -> bool:
        """Set gauge value"""
        if not self.client:
            return False
        
        try:
            key = f"gauge:{gauge_name}"
            self.client.set(key, str(value))
            self.client.expire(key, 86400)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set gauge: {e}")
            return False
    
    def get_gauge(self, gauge_name: str) -> Optional[float]:
        """Get gauge value"""
        if not self.client:
            return None
        
        try:
            key = f"gauge:{gauge_name}"
            value = self.client.get(key)
            return float(value) if value else None
        except Exception as e:
            self.logger.error(f"Failed to get gauge: {e}")
            return None
    
    # ==================== QUEUES ====================
    
    def enqueue(self, queue_name: str, item: Dict) -> bool:
        """Add item to queue"""
        if not self.client:
            return False
        
        try:
            key = f"queue:{queue_name}"
            self.client.rpush(key, json.dumps(item))
            return True
        except Exception as e:
            self.logger.error(f"Failed to enqueue: {e}")
            return False
    
    def dequeue(self, queue_name: str) -> Optional[Dict]:
        """Get item from queue"""
        if not self.client:
            return None
        
        try:
            key = f"queue:{queue_name}"
            item = self.client.lpop(key)
            return json.loads(item) if item else None
        except Exception as e:
            self.logger.error(f"Failed to dequeue: {e}")
            return None
    
    def queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        if not self.client:
            return 0
        
        try:
            key = f"queue:{queue_name}"
            return self.client.llen(key)
        except Exception as e:
            self.logger.error(f"Failed to get queue length: {e}")
            return 0
    
    # ==================== DISTRIBUTED LOCKS ====================
    
    def acquire_lock(self, lock_name: str, timeout_seconds: int = 10) -> bool:
        """Acquire distributed lock"""
        if not self.client:
            return True  # Allow if Redis down
        
        try:
            key = f"lock:{lock_name}"
            lock_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Try to set if not exists
            result = self.client.set(
                key,
                lock_id,
                ex=timeout_seconds,
                nx=True
            )
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to acquire lock: {e}")
            return False
    
    def release_lock(self, lock_name: str) -> bool:
        """Release distributed lock"""
        if not self.client:
            return False
        
        try:
            key = f"lock:{lock_name}"
            self.client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to release lock: {e}")
            return False
    
    # ==================== MONITORING ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self.client:
            return {"status": "disconnected"}
        
        try:
            info = self.client.info()
            return {
                "status": "connected",
                "memory_usage_mb": info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_keys": len(list(self.client.keys("*")))
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def flush_all(self):
        """Clear all Redis data (DANGER!)"""
        if not self.client:
            return False
        
        try:
            self.client.flushall()
            self.logger.warning("Redis flushed completely")
            return True
        except Exception as e:
            self.logger.error(f"Failed to flush Redis: {e}")
            return False


# Global instance
redis_client = None


def initialize_redis(
    host: str = "localhost",
    port: int = 6379,
    password: str = None,
    logger: logging.Logger = None
) -> Optional[RedisClient]:
    """Initialize Redis client"""
    global redis_client
    
    redis_client = RedisClient(
        host=host,
        port=port,
        password=password,
        logger=logger
    )
    
    return redis_client


def get_redis() -> Optional[RedisClient]:
    """Get Redis client"""
    return redis_client
