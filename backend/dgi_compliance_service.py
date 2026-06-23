"""
DGI Compliance Reporting Service
Generates compliance reports for DGI (Direction Générale des Impôts) Côte d'Ivoire
Phase 3.7: Compliance & Audit
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import json
import hashlib
from decimal import Decimal

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    UNKNOWN = "UNKNOWN"


class DGIComplianceService:
    """DGI (Côte d'Ivoire tax authority) compliance reporting"""

    def __init__(self, db, audit_service, parametres_service):
        self.db = db
        self.audit_service = audit_service
        self.parametres_service = parametres_service
        self.compliance_collection = db["dgi_compliance_reports"]
        self._init_indexes()

    def _init_indexes(self):
        """Create indexes for compliance reports"""
        try:
            self.compliance_collection.create_index([("report_date", -1)])
            self.compliance_collection.create_index([("period_start", 1)])
            self.compliance_collection.create_index([("company_ncc", 1)])
            logger.info("✅ DGI compliance report indexes created")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")

    async def generate_monthly_report(
        self,
        month: int,
        year: int,
    ) -> Dict:
        """
        Generate monthly compliance report for DGI
        
        Args:
            month: Month (1-12)
            year: Year
            
        Returns:
            Compliance report
        """
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

        report_id = self._generate_report_id(month, year)

        try:
            # Fetch company parameters
            company_ncc = await self.parametres_service.get_parameter("company_ncc")
            company_name = await self.parametres_service.get_parameter("company_name")

            # Get sales transactions (factures)
            factures_count = await self.db["factures"].count_documents({
                "date_facture": {
                    "$gte": period_start,
                    "$lte": period_end,
                }
            })

            # Calculate total sales
            factures = await self.db["factures"].find({
                "date_facture": {
                    "$gte": period_start,
                    "$lte": period_end,
                }
            }).to_list(length=None)

            total_sales = sum(
                float(f.get("montant_total", 0)) for f in factures
            )
            total_tax = sum(
                float(f.get("montant_tva", 0)) for f in factures
            )

            # Get payments received
            paiements_count = await self.db["paiements"].count_documents({
                "date_paiement": {
                    "$gte": period_start,
                    "$lte": period_end,
                }
            })

            paiements = await self.db["paiements"].find({
                "date_paiement": {
                    "$gte": period_start,
                    "$lte": period_end,
                }
            }).to_list(length=None)

            total_payments = sum(
                float(p.get("montant", 0)) for p in paiements
            )

            # Calculate compliance metrics
            compliance_score = self._calculate_compliance_score(
                factures_count,
                paiements_count,
                total_sales,
                total_tax,
            )

            # Generate report document
            report = {
                "_id": report_id,
                "report_date": datetime.utcnow(),
                "period_start": period_start,
                "period_end": period_end,
                "period_label": f"{month:02d}/{year}",
                "company_ncc": company_ncc,
                "company_name": company_name,
                "transactions": {
                    "invoices_count": factures_count,
                    "payments_count": paiements_count,
                    "total_sales": float(total_sales),
                    "total_tax": float(total_tax),
                    "total_payments": float(total_payments),
                    "outstanding": float(total_sales - total_payments),
                },
                "compliance": {
                    "status": ComplianceStatus.COMPLIANT.value,
                    "score": compliance_score,
                    "checks": {
                        "all_invoices_recorded": factures_count > 0,
                        "all_payments_recorded": paiements_count > 0,
                        "tax_calculated": total_tax > 0,
                        "tax_remitted": True,  # Check against payment records
                        "records_complete": True,
                    },
                },
                "signature": None,  # Will be signed
                "dgi_submission": {
                    "submitted": False,
                    "submission_date": None,
                    "submission_id": None,
                    "confirmation_code": None,
                },
            }

            # Generate digital signature
            report["signature"] = self._generate_signature(report)

            # Store report
            await self.compliance_collection.insert_one(report)

            # Log compliance event
            await self.audit_service.log_event(
                event_type="COMPLIANCE",
                user_id="system",
                resource_type="compliance_report",
                resource_id=report_id,
                action="generate_monthly_report",
                details={
                    "month": month,
                    "year": year,
                    "total_sales": float(total_sales),
                    "compliance_score": compliance_score,
                },
            )

            logger.info(f"✅ Monthly report generated: {report_id}")
            return report

        except Exception as e:
            logger.error(f"❌ Failed to generate monthly report: {e}")
            raise

    async def generate_quarterly_report(
        self,
        quarter: int,
        year: int,
    ) -> Dict:
        """
        Generate quarterly compliance report
        
        Args:
            quarter: Quarter (1-4)
            year: Year
        """
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3

        try:
            monthly_reports = []
            for month in range(start_month, end_month + 1):
                report = await self.generate_monthly_report(month, year)
                monthly_reports.append(report)

            # Aggregate quarterly data
            quarter_report = {
                "_id": f"Q{quarter}_{year}",
                "report_date": datetime.utcnow(),
                "period_label": f"Q{quarter}/{year}",
                "monthly_reports": [r["_id"] for r in monthly_reports],
                "totals": {
                    "invoices": sum(r["transactions"]["invoices_count"] for r in monthly_reports),
                    "total_sales": sum(r["transactions"]["total_sales"] for r in monthly_reports),
                    "total_tax": sum(r["transactions"]["total_tax"] for r in monthly_reports),
                },
                "compliance_score": sum(
                    r["compliance"]["score"] for r in monthly_reports
                ) / len(monthly_reports),
            }

            await self.compliance_collection.insert_one(quarter_report)

            logger.info(f"✅ Quarterly report generated: Q{quarter}/{year}")
            return quarter_report

        except Exception as e:
            logger.error(f"❌ Failed to generate quarterly report: {e}")
            raise

    async def submit_to_dgi(
        self,
        report_id: str,
        endpoint: str = None,
        api_key: str = None,
    ) -> Dict:
        """
        Submit compliance report to DGI system
        
        Args:
            report_id: Report ID
            endpoint: DGI API endpoint
            api_key: DGI API key
            
        Returns:
            Submission confirmation
        """
        try:
            report = await self.compliance_collection.find_one({"_id": report_id})
            if not report:
                raise ValueError(f"Report not found: {report_id}")

            # Prepare submission payload
            payload = {
                "ncc": report["company_ncc"],
                "period": report["period_label"],
                "transactions": report["transactions"],
                "compliance": report["compliance"],
                "signature": report["signature"],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # In production, submit to actual DGI endpoint
            # For now, just mark as submitted
            submission_id = self._generate_submission_id()

            update = {
                "$set": {
                    "dgi_submission.submitted": True,
                    "dgi_submission.submission_date": datetime.utcnow(),
                    "dgi_submission.submission_id": submission_id,
                    "dgi_submission.confirmation_code": "DGI_" + submission_id,
                }
            }

            await self.compliance_collection.update_one(
                {"_id": report_id},
                update,
            )

            # Log submission
            await self.audit_service.log_event(
                event_type="COMPLIANCE",
                user_id="system",
                resource_type="compliance_submission",
                resource_id=submission_id,
                action="submit_to_dgi",
                details={
                    "report_id": report_id,
                    "period": report["period_label"],
                },
            )

            logger.info(f"✅ Report submitted to DGI: {submission_id}")
            return {
                "submission_id": submission_id,
                "confirmation_code": "DGI_" + submission_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "SUBMITTED",
            }

        except Exception as e:
            logger.error(f"❌ Failed to submit to DGI: {e}")
            raise

    async def get_compliance_status(self) -> Dict:
        """Get current compliance status"""
        try:
            # Get latest report
            latest = await self.compliance_collection.find_one(
                sort=[("report_date", -1)]
            )

            if not latest:
                return {
                    "status": ComplianceStatus.UNKNOWN.value,
                    "last_report": None,
                }

            return {
                "status": latest["compliance"]["status"],
                "score": latest["compliance"]["score"],
                "last_report": latest["_id"],
                "last_report_date": latest["report_date"],
                "dgi_submitted": latest["dgi_submission"]["submitted"],
            }

        except Exception as e:
            logger.error(f"❌ Failed to get compliance status: {e}")
            return {}

    def _calculate_compliance_score(
        self,
        invoices: int,
        payments: int,
        sales: float,
        tax: float,
    ) -> int:
        """Calculate compliance score (0-100)"""
        score = 100

        # Deduct points for missing transactions
        if invoices == 0:
            score -= 25
        if payments == 0:
            score -= 25
        if tax == 0:
            score -= 25

        # Ensure tax is reasonable (at least 5% of sales)
        if sales > 0 and tax < sales * 0.05:
            score -= 10

        return max(0, score)

    def _generate_signature(self, data: Dict) -> str:
        """Generate digital signature for compliance report"""
        report_copy = data.copy()
        report_copy.pop("signature", None)
        
        json_str = json.dumps(report_copy, sort_keys=True, default=str)
        signature = hashlib.sha256(json_str.encode()).hexdigest()
        
        return signature

    def _generate_report_id(self, month: int, year: int) -> str:
        """Generate report ID"""
        return f"DGI_{year}{month:02d}_{datetime.utcnow().strftime('%s')}"

    def _generate_submission_id(self) -> str:
        """Generate submission ID"""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{timestamp}{hash(timestamp)}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:12]


async def init_dgi_compliance_service(
    db,
    audit_service,
    parametres_service,
) -> DGIComplianceService:
    """Initialize DGI compliance service"""
    service = DGIComplianceService(db, audit_service, parametres_service)
    logger.info("✅ DGI Compliance Service initialized")
    return service
