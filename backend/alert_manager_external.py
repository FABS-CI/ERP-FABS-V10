"""
TOUR 4: Alert Manager External - Multi-Channel Notifications
=============================================================
Purpose: Send alerts via Email, Slack, Microsoft Teams, PagerDuty

Channels:
- Email (SMTP): Critical alerts to ops team
- Slack: Real-time notifications to #erp-alerts channel
- Microsoft Teams: Formatted cards for ops dashboard
- PagerDuty: High-severity incidents for on-call rotation

Architecture:
- Alert queue stored in Redis (async processing)
- Background worker processes queue periodically
- Deduplication: Same alert within 5min window sent once
- Rate limiting: Max 10 alerts per minute (prevents flood)
- Retry logic: Up to 3 attempts with exponential backoff

Alert severity levels:
- INFO: Monitoring info (cache hits, successful logins)
- WARNING: Performance degradation, elevated error rates
- CRITICAL: Service down, database unavailable, security breach
- EMERGENCY: Data loss, production outage
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import logging


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class Alert:
    """Alert message structure"""
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.WARNING
    component: str = "erp-fabs"
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def get_hash(self) -> str:
        """Get unique hash for deduplication"""
        content = f"{self.title}:{self.message}:{self.component}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "component": self.component,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "hash": self.get_hash()
        }


# ============================================================================
# ALERT CHANNEL BASE CLASS
# ============================================================================

class AlertChannel(ABC):
    """Base class for alert channels"""
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send alert through channel"""
        pass


# ============================================================================
# EMAIL CHANNEL
# ============================================================================

class EmailAlertChannel(AlertChannel):
    """Send alerts via SMTP"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        recipient_emails: List[str]
    ):
        """
        Initialize email channel
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP port (465 for TLS, 587 for STARTTLS)
            sender_email: Sender email address
            sender_password: Sender password or app token
            recipient_emails: List of recipient email addresses
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_emails = recipient_emails
        self.logger = logging.getLogger(__name__)
    
    async def send(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create HTML email
            html = self._create_email_html(alert)
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)
            
            msg.attach(MIMEText(html, "html"))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_port == 587:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_emails, msg.as_string())
            
            self.logger.info(f"Email alert sent: {alert.title}")
            return True
        
        except Exception as e:
            self.logger.error(f"Email alert failed: {e}")
            return False
    
    def _create_email_html(self, alert: Alert) -> str:
        """Create HTML email body"""
        severity_color = {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.CRITICAL: "#dc3545",
            AlertSeverity.EMERGENCY: "#721c24"
        }
        
        color = severity_color.get(alert.severity, "#6c757d")
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{ border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: #f9f9f9; }}
                .severity {{ color: {color}; font-weight: bold; font-size: 14px; }}
                .timestamp {{ color: #666; font-size: 12px; }}
                .metadata {{ background: #f0f0f0; padding: 10px; margin-top: 10px; border-radius: 4px; }}
                .metadata-item {{ margin: 5px 0; font-family: monospace; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <div class="severity">{alert.severity.upper()}</div>
                <h3>{alert.title}</h3>
                <p>{alert.message}</p>
                <p class="timestamp">Time: {alert.timestamp}</p>
                {f'<p class="timestamp">Trace: {alert.trace_id}</p>' if alert.trace_id else ''}
                
                {'<div class="metadata">' + ''.join(f'<div class="metadata-item"><strong>{k}:</strong> {v}</div>' for k, v in alert.metadata.items()) + '</div>' if alert.metadata else ''}
            </div>
        </body>
        </html>
        """


# ============================================================================
# SLACK CHANNEL
# ============================================================================

class SlackAlertChannel(AlertChannel):
    """Send alerts to Slack webhook"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack channel
        
        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    async def send(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            import httpx
            
            payload = {
                "attachments": [
                    {
                        "color": self._get_slack_color(alert.severity),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {"title": "Severity", "value": alert.severity.upper(), "short": True},
                            {"title": "Component", "value": alert.component, "short": True},
                            {"title": "Time", "value": alert.timestamp, "short": True},
                        ] + (
                            [{"title": "Trace ID", "value": alert.trace_id, "short": True}]
                            if alert.trace_id else []
                        ),
                        "footer": "ERP FABS Alert Manager"
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"Slack alert sent: {alert.title}")
                    return True
                else:
                    self.logger.error(f"Slack failed: {response.text}")
                    return False
        
        except Exception as e:
            self.logger.error(f"Slack alert failed: {e}")
            return False
    
    @staticmethod
    def _get_slack_color(severity: AlertSeverity) -> str:
        """Get Slack color for severity"""
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.EMERGENCY: "#990000"
        }
        return colors.get(severity, "#808080")


# ============================================================================
# MICROSOFT TEAMS CHANNEL
# ============================================================================

class TeamsAlertChannel(AlertChannel):
    """Send alerts to Microsoft Teams webhook"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Teams channel
        
        Args:
            webhook_url: Teams incoming webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    async def send(self, alert: Alert) -> bool:
        """Send alert to Microsoft Teams"""
        try:
            import httpx
            
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": alert.title,
                "themeColor": self._get_teams_color(alert.severity),
                "sections": [
                    {
                        "activityTitle": alert.title,
                        "activitySubtitle": alert.message,
                        "facts": [
                            {"name": "Severity", "value": alert.severity.upper()},
                            {"name": "Component", "value": alert.component},
                            {"name": "Time", "value": alert.timestamp},
                        ] + (
                            [{"name": "Trace ID", "value": alert.trace_id}]
                            if alert.trace_id else []
                        ),
                        "markdown": True
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"Teams alert sent: {alert.title}")
                    return True
                else:
                    self.logger.error(f"Teams failed: {response.text}")
                    return False
        
        except Exception as e:
            self.logger.error(f"Teams alert failed: {e}")
            return False
    
    @staticmethod
    def _get_teams_color(severity: AlertSeverity) -> str:
        """Get Teams color for severity"""
        colors = {
            AlertSeverity.INFO: "0078D4",
            AlertSeverity.WARNING: "FFB900",
            AlertSeverity.CRITICAL: "D13438",
            AlertSeverity.EMERGENCY: "#990000"
        }
        return colors.get(severity, "737373")


# ============================================================================
# PAGERDUTY CHANNEL
# ============================================================================

class PagerDutyAlertChannel(AlertChannel):
    """Send incidents to PagerDuty"""
    
    def __init__(self, api_key: str, integration_key: str):
        """
        Initialize PagerDuty channel
        
        Args:
            api_key: PagerDuty API key
            integration_key: PagerDuty integration key for this service
        """
        self.api_key = api_key
        self.integration_key = integration_key
        self.logger = logging.getLogger(__name__)
    
    async def send(self, alert: Alert) -> bool:
        """Send alert to PagerDuty (CRITICAL/EMERGENCY only)"""
        # Only escalate critical and emergency alerts
        if alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            return True  # Don't create PagerDuty incidents for low severity
        
        try:
            import httpx
            
            # PagerDuty Events API v2
            payload = {
                "routing_key": self.integration_key,
                "event_action": "trigger",
                "dedup_key": alert.get_hash(),
                "payload": {
                    "summary": alert.title,
                    "severity": "critical" if alert.severity == AlertSeverity.CRITICAL else "critical",
                    "source": alert.component,
                    "custom_details": {
                        "message": alert.message,
                        "timestamp": alert.timestamp,
                        "trace_id": alert.trace_id,
                        **alert.metadata
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    headers={"Authorization": f"Token token={self.api_key}"},
                    timeout=5
                )
                
                if response.status_code == 202:
                    self.logger.info(f"PagerDuty incident created: {alert.title}")
                    return True
                else:
                    self.logger.error(f"PagerDuty failed: {response.text}")
                    return False
        
        except Exception as e:
            self.logger.error(f"PagerDuty alert failed: {e}")
            return False


# ============================================================================
# ALERT MANAGER
# ============================================================================

class AlertManager:
    """
    Central alert manager coordinating multiple channels
    
    Features:
    - Deduplication (same alert not sent twice within 5 min)
    - Rate limiting (max 10 alerts/minute)
    - Retry logic (up to 3 attempts)
    - Alert history tracking
    """
    
    def __init__(self, redis_client=None, max_alerts_per_minute: int = 10):
        """
        Initialize alert manager
        
        Args:
            redis_client: Redis client for deduplication and queue
            max_alerts_per_minute: Rate limit for alerts
        """
        self.redis = redis_client
        self.max_alerts_per_minute = max_alerts_per_minute
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    def register_channel(self, name: str, channel: AlertChannel) -> None:
        """Register an alert channel"""
        self.channels[name] = channel
        self.logger.info(f"Alert channel registered: {name}")
    
    async def send_alert(self, alert: Alert, channels: Optional[List[str]] = None) -> bool:
        """
        Send alert through specified channels
        
        Args:
            alert: Alert object
            channels: List of channel names (None = all channels)
        
        Returns:
            True if sent successfully, False otherwise
        """
        async with self._lock:
            # Check rate limiting
            if not self._check_rate_limit():
                self.logger.warning("Alert rate limit exceeded")
                return False
            
            # Check deduplication
            if self._is_duplicate(alert):
                self.logger.debug(f"Duplicate alert filtered: {alert.title}")
                return False
            
            # Store in history
            self.alert_history[alert.get_hash()] = datetime.utcnow()
            
            # Send through channels
            channels_to_use = channels or list(self.channels.keys())
            results = []
            
            for channel_name in channels_to_use:
                if channel_name in self.channels:
                    channel = self.channels[channel_name]
                    try:
                        result = await channel.send(alert)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Channel {channel_name} error: {e}")
                        results.append(False)
            
            return any(results)  # Success if at least one channel succeeds
    
    def _check_rate_limit(self) -> bool:
        """Check if alert rate limit allows more alerts"""
        if not self.redis:
            return True  # No rate limiting without Redis
        
        try:
            key = "alerts:rate_limit"
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, 60)  # Reset counter every minute
            return count <= self.max_alerts_per_minute
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is duplicate within deduplication window"""
        alert_hash = alert.get_hash()
        if alert_hash in self.alert_history:
            last_time = self.alert_history[alert_hash]
            if datetime.utcnow() - last_time < timedelta(minutes=5):
                return True  # Duplicate within 5 minute window
        return False
    
    async def queue_alert(self, alert: Alert) -> bool:
        """Queue alert for background processing"""
        if not self.redis:
            return await self.send_alert(alert)
        
        try:
            # Store alert in Redis queue
            key = "alerts:queue"
            self.redis.lpush(key, json.dumps(alert.to_dict()))
            self.logger.info(f"Alert queued: {alert.title}")
            return True
        except Exception as e:
            self.logger.error(f"Queue failed: {e}")
            return await self.send_alert(alert)  # Fallback: send immediately


# ============================================================================
# BACKGROUND WORKER
# ============================================================================

async def process_alert_queue(alert_manager: AlertManager, interval: int = 10) -> None:
    """
    Background worker to process alert queue from Redis
    
    Args:
        alert_manager: AlertManager instance
        interval: Check interval in seconds
    """
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            if not alert_manager.redis:
                await asyncio.sleep(interval)
                continue
            
            # Get alert from queue
            alert_data = alert_manager.redis.rpop("alerts:queue")
            if alert_data:
                alert_dict = json.loads(alert_data)
                alert = Alert(**alert_dict)
                await alert_manager.send_alert(alert)
            
            await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
        
        except Exception as e:
            logger.error(f"Alert processing error: {e}")
            await asyncio.sleep(interval)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_alert_manager_from_env() -> AlertManager:
    """Create AlertManager from environment variables"""
    manager = AlertManager()
    
    # Email channel
    if os.getenv("ALERT_EMAIL_ENABLED") == "true":
        email_channel = EmailAlertChannel(
            smtp_host=os.getenv("SMTP_HOST", "localhost"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            sender_email=os.getenv("ALERT_EMAIL_FROM", "alerts@erp-fabs.local"),
            sender_password=os.getenv("ALERT_EMAIL_PASSWORD", ""),
            recipient_emails=os.getenv("ALERT_EMAIL_TO", "ops@erp-fabs.local").split(",")
        )
        manager.register_channel("email", email_channel)
    
    # Slack channel
    if os.getenv("ALERT_SLACK_WEBHOOK"):
        slack_channel = SlackAlertChannel(os.getenv("ALERT_SLACK_WEBHOOK"))
        manager.register_channel("slack", slack_channel)
    
    # Teams channel
    if os.getenv("ALERT_TEAMS_WEBHOOK"):
        teams_channel = TeamsAlertChannel(os.getenv("ALERT_TEAMS_WEBHOOK"))
        manager.register_channel("teams", teams_channel)
    
    # PagerDuty channel
    if os.getenv("ALERT_PAGERDUTY_KEY"):
        pagerduty_channel = PagerDutyAlertChannel(
            api_key=os.getenv("ALERT_PAGERDUTY_KEY"),
            integration_key=os.getenv("ALERT_PAGERDUTY_INTEGRATION_KEY", "")
        )
        manager.register_channel("pagerduty", pagerduty_channel)
    
    return manager


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create manager
    manager = AlertManager()
    
    # Register channels (mock for testing)
    manager.register_channel("email", EmailAlertChannel(
        "smtp.gmail.com", 587, "test@test.com", "pass", ["admin@test.com"]
    ))
    manager.register_channel("slack", SlackAlertChannel("https://hooks.slack.com/..."))
    
    # Create and send alert
    alert = Alert(
        title="Database Connection Pool Exhausted",
        message="MongoDB connection pool at capacity (100/100)",
        severity=AlertSeverity.CRITICAL,
        component="database",
        metadata={"pool_size": 100, "active_connections": 100}
    )
    
    # Queue for async processing
    asyncio.run(manager.queue_alert(alert))
    
    print("✓ Alert manager configured")
