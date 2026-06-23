"""
Enhanced Audit Log Service
Centralized audit logging with retention, archiving, and compliance
Phase 3.7: Compliance & Audit
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from pymongo import ASCENDING, DESCENDING
import hashlib
import json

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Audit event severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"


class AuditEventType(Enum):
    """Types of audit events"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    DATA_DELETION = "DATA_DELETION"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    SECURITY_EVENT = "SECURITY_EVENT"
    COMPLIANCE = "COMPLIANCE"
    BACKUP = "BACKUP"


class EnhancedAuditLogService:
    """Centralized audit logging service with compliance features"""

    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.audit_collection = db["audit_logs"]
        self.compliance_collection = db["compliance_logs"]
        self.archive_collection = db["audit_logs_archive"]
        
        self._init_indexes()
        self._init_retention_policy()

    def _init_indexes(self):
        """Create database indexes for efficient querying"""
        try:
            # Main audit log indexes
            self.audit_collection.create_index([("timestamp", DESCENDING)])
            self.audit_collection.create_index([("user_id", ASCENDING)])
            self.audit_collection.create_index([("event_type", ASCENDING)])
            self.audit_collection.create_index([("resource_type", ASCENDING)])
            self.audit_collection.create_index([("level", ASCENDING)])
            
            # Compound indexes
            self.audit_collection.create_index([
                ("user_id", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            self.audit_collection.create_index([
                ("event_type", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            
            # TTL index for automatic deletion (7 years for compliance)
            # Set to 0 initially, enable via retention policy
            
            logger.info("✅ Audit log indexes created")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")

    def _init_retention_policy(self):
        """Initialize retention policy with TTL indexes"""
        try:
            # 7 years retention (DGI requirement)
            retention_seconds = 7 * 365 * 24 * 60 * 60
            
            # Create TTL index (expires after retention period)
            self.audit_collection.create_index(
                [("created_at", ASCENDING)],
                expireAfterSeconds=retention_seconds,
                name="audit_log_ttl"
            )
            
            logger.info(f"✅ TTL retention policy set: {retention_seconds}s (7 years)")
        except Exception as e:
            logger.warning(f"⚠️  Could not set TTL index: {e}")

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_type: str,
        resource_id: str = None,
        action: str = None,
        details: Dict = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: str = None,
        user_agent: str = None,
    ) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            user_id: User who performed action
            resource_type: Type of resource affected
            resource_id: ID of resource
            action: Specific action performed
            details: Additional details (JSON)
            level: Event severity
            ip_address: Client IP
            user_agent: Client user agent
            
        Returns:
            Event ID
        """
        event_id = self._generate_event_id()
        timestamp = datetime.utcnow()
        
        audit_event = {
            "_id": event_id,
            "timestamp": timestamp,
            "created_at": timestamp,  # For TTL index
            "event_type": event_type.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": details or {},
            "level": level.value,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "checksum": None,  # Will be set before insert
        }
        
        # Generate checksum for integrity verification
        audit_event["checksum"] = self._generate_checksum(audit_event)
        
        try:
            await self.audit_collection.insert_one(audit_event)
            
            # Cache in Redis for fast access (1 hour)
            if self.redis:
                await self.redis.setex(
                    f"audit_event:{event_id}",
                    3600,
                    json.dumps(audit_event, default=str)
                )
            
            logger.debug(f"✅ Audit event logged: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
            raise

    async def get_event(self, event_id: str) -> Optional[Dict]:
        """Retrieve audit event by ID"""
        try:
            return await self.audit_collection.find_one({"_id": event_id})
        except Exception as e:
            logger.error(f"❌ Failed to retrieve event: {e}")
            return None

    async def get_events(
        self,
        user_id: str = None,
        event_type: str = None,
        resource_type: str = None,
        level: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict]:
        """
        Query audit events with filters
        
        Returns:
            List of audit events
        """
        query = {}
        
        if user_id:
            query["user_id"] = user_id
        if event_type:
            query["event_type"] = event_type
        if resource_type:
            query["resource_type"] = resource_type
        if level:
            query["level"] = level
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["timestamp"] = date_query
        
        try:
            cursor = (
                self.audit_collection
                .find(query)
                .sort("timestamp", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"❌ Failed to query events: {e}")
            return []

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict:
        """Get user activity summary"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            events = await self.get_events(
                user_id=user_id,
                start_date=start_date,
            )
            
            # Count by event type
            event_counts = {}
            for event in events:
                event_type = event.get("event_type", "UNKNOWN")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            return {
                "user_id": user_id,
                "total_events": len(events),
                "event_counts": event_counts,
                "period_days": days,
                "first_event": events[-1]["timestamp"] if events else None,
                "last_event": events[0]["timestamp"] if events else None,
            }
        except Exception as e:
            logger.error(f"❌ Failed to get user activity: {e}")
            return {}

    async def get_compliance_summary(self, days: int = 30) -> Dict:
        """Get compliance summary for period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            events = await self.get_events(
                level="SECURITY",
                start_date=start_date,
            )
            
            # Categorize by severity
            critical = len([e for e in events if e.get("level") == "CRITICAL"])
            warnings = len([e for e in events if e.get("level") == "WARNING"])
            
            return {
                "period_days": days,
                "total_security_events": len(events),
                "critical_events": critical,
                "warning_events": warnings,
                "compliance_score": max(0, 100 - (critical * 10 + warnings * 2)),
            }
        except Exception as e:
            logger.error(f"❌ Failed to get compliance summary: {e}")
            return {}

    async def archive_old_logs(self, days_old: int = 365) -> int:
        """
        Archive logs older than specified days
        
        Returns:
            Number of archived events
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        try:
            # Find old events
            old_events = await self.audit_collection.find({
                "timestamp": {"$lt": cutoff_date}
            }).to_list(length=None)
            
            if not old_events:
                return 0
            
            # Insert into archive
            await self.archive_collection.insert_many(old_events)
            
            # Delete from main collection
            deleted = await self.audit_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            logger.info(f"✅ Archived {deleted.deleted_count} old audit logs")
            return deleted.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to archive logs: {e}")
            return 0

    async def verify_audit_integrity(self, event_id: str) -> bool:
        """Verify audit event hasn't been tampered with"""
        try:
            event = await self.get_event(event_id)
            if not event:
                return False
            
            stored_checksum = event.get("checksum")
            event_copy = event.copy()
            event_copy.pop("checksum", None)
            
            calculated_checksum = self._generate_checksum(event_copy)
            
            is_valid = stored_checksum == calculated_checksum
            
            if not is_valid:
                logger.warning(f"❌ Audit event integrity check failed: {event_id}")
            
            return is_valid
        except Exception as e:
            logger.error(f"❌ Failed to verify integrity: {e}")
            return False

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{timestamp}{hash(timestamp)}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def _generate_checksum(self, data: Dict) -> str:
        """Generate SHA256 checksum for audit event"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def get_statistics(self) -> Dict:
        """Get audit log statistics"""
        try:
            total_events = await self.audit_collection.count_documents({})
            
            # Count by level
            levels = {}
            for level in AuditLevel:
                count = await self.audit_collection.count_documents(
                    {"level": level.value}
                )
                levels[level.value] = count
            
            # Count by event type
            event_types = {}
            for event_type in AuditEventType:
                count = await self.audit_collection.count_documents(
                    {"event_type": event_type.value}
                )
                event_types[event_type.value] = count
            
            return {
                "total_events": total_events,
                "by_level": levels,
                "by_event_type": event_types,
            }
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}


async def init_audit_log_service(db, redis_client=None) -> EnhancedAuditLogService:
    """Initialize audit log service"""
    service = EnhancedAuditLogService(db, redis_client)
    logger.info("✅ Audit Log Service initialized")
    return service
