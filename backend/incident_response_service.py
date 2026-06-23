"""
Incident Response Service
Automated incident detection, alerting, playbooks, remediation
Phase 3.8: Incident Response
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATING = "MITIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentResponseService:
    """Automated incident response and playbooks"""

    def __init__(self, db, audit_service, alert_service=None):
        self.db = db
        self.audit_service = audit_service
        self.alert_service = alert_service
        self.incident_collection = db["incidents"]
        self.playbook_collection = db["playbooks"]
        self.response_log_collection = db["response_logs"]

    async def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        source_event_id: str = None,
        affected_systems: List[str] = None,
        impact: str = None,
    ) -> str:
        """Create incident"""
        incident_id = self._generate_incident_id()
        
        incident = {
            "_id": incident_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "title": title,
            "description": description,
            "severity": severity.value,
            "status": IncidentStatus.OPEN.value,
            "source_event_id": source_event_id,
            "affected_systems": affected_systems or [],
            "impact": impact,
            "assigned_to": None,
            "response_actions": [],
            "resolution_time_minutes": None,
        }

        await self.incident_collection.insert_one(incident)

        # Trigger automatic response if CRITICAL
        if severity == IncidentSeverity.CRITICAL:
            await self._auto_respond_critical(incident_id)

        logger.warning(f"⚠️  Incident created: {incident_id} ({severity.value})")
        return incident_id

    async def detect_anomalies(self) -> List[str]:
        """Detect security anomalies and auto-create incidents"""
        incidents_created = []

        try:
            # Check 1: Excessive failed logins
            failed_logins = await self.db["audit_logs"].count_documents({
                "event_type": "LOGIN",
                "level": "WARNING",
                "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=5)}
            })

            if failed_logins > 10:
                incident_id = await self.create_incident(
                    title="Suspicious login attempts detected",
                    description=f"{failed_logins} failed logins in last 5 minutes",
                    severity=IncidentSeverity.HIGH,
                    affected_systems=["authentication"],
                    impact="Potential brute force attack",
                )
                incidents_created.append(incident_id)

            # Check 2: Elevated database errors
            db_errors = await self.db["audit_logs"].count_documents({
                "event_type": "DATA_ACCESS",
                "level": "CRITICAL",
                "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=10)}
            })

            if db_errors > 20:
                incident_id = await self.create_incident(
                    title="Database errors spike detected",
                    description=f"{db_errors} database errors in last 10 minutes",
                    severity=IncidentSeverity.CRITICAL,
                    affected_systems=["database"],
                    impact="Service degradation",
                )
                incidents_created.append(incident_id)

            # Check 3: Unusual data access patterns
            suspicious_access = await self.db["audit_logs"].count_documents({
                "event_type": "DATA_ACCESS",
                "level": "SECURITY",
                "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            })

            if suspicious_access > 50:
                incident_id = await self.create_incident(
                    title="Unusual data access pattern detected",
                    description=f"{suspicious_access} suspicious accesses in last hour",
                    severity=IncidentSeverity.MEDIUM,
                    affected_systems=["data_access"],
                    impact="Potential unauthorized data access",
                )
                incidents_created.append(incident_id)

            logger.info(f"✅ Anomaly detection complete: {len(incidents_created)} incidents")
            return incidents_created

        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")
            return []

    async def execute_playbook(self, incident_id: str, playbook_name: str) -> Dict:
        """Execute incident response playbook"""
        try:
            incident = await self.incident_collection.find_one({"_id": incident_id})
            if not incident:
                raise ValueError(f"Incident not found: {incident_id}")

            # Get playbook
            playbook = await self.playbook_collection.find_one({"name": playbook_name})
            if not playbook:
                raise ValueError(f"Playbook not found: {playbook_name}")

            # Execute steps
            results = {
                "incident_id": incident_id,
                "playbook_name": playbook_name,
                "started_at": datetime.utcnow(),
                "steps_executed": [],
                "status": "SUCCESS",
            }

            for step in playbook.get("steps", []):
                try:
                    step_result = await self._execute_step(step, incident)
                    results["steps_executed"].append(step_result)
                except Exception as e:
                    logger.error(f"❌ Step failed: {step['name']} - {e}")
                    results["status"] = "PARTIAL_FAILURE"

            # Update incident status
            await self.incident_collection.update_one(
                {"_id": incident_id},
                {
                    "$set": {
                        "status": IncidentStatus.MITIGATING.value,
                        "updated_at": datetime.utcnow(),
                    },
                    "$push": {"response_actions": playbook_name}
                }
            )

            logger.info(f"✅ Playbook executed: {playbook_name} on {incident_id}")
            return results

        except Exception as e:
            logger.error(f"❌ Playbook execution failed: {e}")
            raise

    async def _auto_respond_critical(self, incident_id: str):
        """Automatically respond to CRITICAL incidents"""
        try:
            # Execute critical playbook
            await self.execute_playbook(incident_id, "critical_incident_response")

            # Alert security team
            if self.alert_service:
                await self.alert_service.send_alert(
                    title="CRITICAL Incident Auto-Response Triggered",
                    severity="CRITICAL",
                    incident_id=incident_id,
                )

        except Exception as e:
            logger.error(f"❌ Auto-response failed: {e}")

    async def resolve_incident(
        self,
        incident_id: str,
        resolution_notes: str = None,
        root_cause: str = None,
    ) -> Dict:
        """Resolve incident"""
        try:
            incident = await self.incident_collection.find_one({"_id": incident_id})
            if not incident:
                raise ValueError(f"Incident not found: {incident_id}")

            resolution_time = (
                datetime.utcnow() - incident["created_at"]
            ).total_seconds() / 60

            await self.incident_collection.update_one(
                {"_id": incident_id},
                {
                    "$set": {
                        "status": IncidentStatus.RESOLVED.value,
                        "resolution_notes": resolution_notes,
                        "root_cause": root_cause,
                        "resolution_time_minutes": resolution_time,
                        "resolved_at": datetime.utcnow(),
                    }
                }
            )

            logger.info(f"✅ Incident resolved: {incident_id} ({resolution_time:.0f} min)")
            return {
                "incident_id": incident_id,
                "status": IncidentStatus.RESOLVED.value,
                "resolution_time_minutes": resolution_time,
            }

        except Exception as e:
            logger.error(f"❌ Failed to resolve incident: {e}")
            raise

    async def get_incident_statistics(self, days: int = 30) -> Dict:
        """Get incident statistics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            incidents = await self.incident_collection.find({
                "created_at": {"$gte": start_date}
            }).to_list(length=None)

            stats = {
                "total_incidents": len(incidents),
                "critical": len([i for i in incidents if i.get("severity") == "CRITICAL"]),
                "high": len([i for i in incidents if i.get("severity") == "HIGH"]),
                "resolved": len([i for i in incidents if i.get("status") == "RESOLVED"]),
                "avg_resolution_time_minutes": sum(
                    i.get("resolution_time_minutes", 0) for i in incidents
                    if i.get("resolution_time_minutes")
                ) / max(1, len([i for i in incidents if i.get("resolution_time_minutes")])),
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}

    async def _execute_step(self, step: Dict, incident: Dict) -> Dict:
        """Execute single playbook step"""
        step_name = step.get("name", "unknown")
        action_type = step.get("action", "log")

        result = {
            "step_name": step_name,
            "action": action_type,
            "executed_at": datetime.utcnow(),
            "success": False,
        }

        try:
            if action_type == "isolate_system":
                # Simulate isolating system
                logger.warning(f"🔒 Isolating system: {step.get('target')}")
                result["success"] = True

            elif action_type == "block_user":
                # Simulate blocking user
                user_id = step.get("user_id")
                await self.db["users"].update_one(
                    {"_id": user_id},
                    {"$set": {"is_active": False}}
                )
                logger.warning(f"🚫 User blocked: {user_id}")
                result["success"] = True

            elif action_type == "log_event":
                # Log to audit trail
                await self.audit_service.log_event(
                    event_type="SECURITY_EVENT",
                    user_id="system",
                    resource_type="incident_response",
                    action=step.get("description", ""),
                )
                result["success"] = True

            elif action_type == "alert":
                # Send alert
                if self.alert_service:
                    await self.alert_service.send_alert(
                        title=step.get("title", "Incident Response Alert"),
                        severity=step.get("severity", "HIGH"),
                        incident_id=incident["_id"],
                    )
                result["success"] = True

            return result

        except Exception as e:
            logger.error(f"❌ Step execution failed: {step_name} - {e}")
            result["error"] = str(e)
            return result

    def _generate_incident_id(self) -> str:
        """Generate unique incident ID"""
        timestamp = datetime.utcnow()
        return f"INC_{timestamp.strftime('%Y%m%d_%H%M%S')}"


async def init_incident_response_service(
    db,
    audit_service,
    alert_service=None,
) -> IncidentResponseService:
    """Initialize incident response service"""
    service = IncidentResponseService(db, audit_service, alert_service)
    logger.info("✅ Incident Response Service initialized")
    return service
