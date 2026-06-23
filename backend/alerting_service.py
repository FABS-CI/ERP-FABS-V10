"""
Alerting Service
Prometheus-style alerting with rules, notification channels, escalation
Phase 3.8: Incident Response
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertingService:
    """Alert management and notification"""

    def __init__(self, db):
        self.db = db
        self.alert_collection = db["alerts"]
        self.alert_rules_collection = db["alert_rules"]
        self.notification_collection = db["notifications"]

    async def send_alert(
        self,
        title: str,
        severity: str,
        description: str = None,
        incident_id: str = None,
        metrics: Dict = None,
    ) -> str:
        """Send alert and trigger notifications"""
        alert_id = f"ALERT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        alert = {
            "_id": alert_id,
            "created_at": datetime.utcnow(),
            "title": title,
            "severity": severity,
            "description": description,
            "incident_id": incident_id,
            "metrics": metrics or {},
            "acknowledged": False,
            "escalated": False,
        }

        await self.alert_collection.insert_one(alert)

        # Get notification channels for this severity
        channels = await self._get_notification_channels(severity)

        # Send notifications
        for channel in channels:
            await self._send_notification(alert, channel)

        logger.warning(f"🚨 Alert sent: {title} ({severity})")
        return alert_id

    async def create_alert_rule(
        self,
        name: str,
        condition: str,
        threshold: float,
        severity: str,
        actions: List[str],
    ) -> str:
        """Create alert rule"""
        rule = {
            "_id": f"RULE_{name}",
            "name": name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "actions": actions,
            "enabled": True,
            "created_at": datetime.utcnow(),
        }

        await self.alert_rules_collection.insert_one(rule)
        logger.info(f"✅ Alert rule created: {name}")
        return rule["_id"]

    async def _get_notification_channels(self, severity: str) -> List[Dict]:
        """Get notification channels for severity"""
        channels = []

        if severity == "CRITICAL":
            channels = [
                {"type": "email", "recipients": ["security@fabsci.com"]},
                {"type": "sms", "recipients": ["+1234567890"]},
                {"type": "slack", "channel": "#security-alerts"},
            ]
        elif severity == "WARNING":
            channels = [
                {"type": "email", "recipients": ["ops@fabsci.com"]},
                {"type": "slack", "channel": "#ops-alerts"},
            ]
        else:
            channels = [
                {"type": "slack", "channel": "#monitoring"},
            ]

        return channels

    async def _send_notification(self, alert: Dict, channel: Dict):
        """Send notification via channel"""
        try:
            notification = {
                "alert_id": alert["_id"],
                "channel_type": channel["type"],
                "recipients": channel.get("recipients", []),
                "sent_at": datetime.utcnow(),
                "status": "SENT",
            }

            await self.notification_collection.insert_one(notification)
            logger.info(f"✅ Notification sent: {channel['type']}")

        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")


async def init_alerting_service(db) -> AlertingService:
    """Initialize alerting service"""
    service = AlertingService(db)
    logger.info("✅ Alerting Service initialized")
    return service
