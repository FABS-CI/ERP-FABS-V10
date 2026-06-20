#!/usr/bin/env python3
"""
FIX #3: Add GET /api/audit endpoint with RBAC
Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR
"""

import sys

# Code to append to administration_module.py
AUDIT_ENDPOINT_CODE = '''

# ---------------------------------------------------------------------------
# AUDIT LOGS ENDPOINT
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    """Schema for audit log response"""
    _id: Optional[str] = None
    timestamp: str
    utilisateur_id: Optional[str] = None
    utilisateur_email: Optional[str] = None
    utilisateur_nom: Optional[str] = None
    module: str
    action: str
    objet_type: Optional[str] = None
    objet_id: Optional[str] = None
    statut: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


def build_audit_router(db: AsyncIOMotorDatabase, resolve_user, log_audit_event=None) -> APIRouter:
    """Build audit logs router"""
    router = APIRouter(prefix="/audit", tags=["audit"])
    
    # Allowed roles for audit access
    AUDIT_ROLES = {"super_admin", "admin", "auditeur"}
    
    @router.get("", response_model=List[AuditLogOut])
    async def list_audit_logs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        module: Optional[str] = Query(None, description="Filter by module"),
        utilisateur_email: Optional[str] = Query(None, description="Filter by user email"),
        action: Optional[str] = Query(None, description="Filter by action"),
        limite: int = Query(100, ge=1, le=1000, description="Max results"),
        offset: int = Query(0, ge=0, description="Pagination offset"),
    ):
        """
        GET /api/audit
        List audit logs with optional filters
        Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR
        """
        me = await resolve_user(request, authorization)
        
        # RBAC check
        if me.get("role") not in AUDIT_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"Audit access denied. Required roles: {AUDIT_ROLES}"
            )
        
        # Build query filters
        filters = {"statut": {"$in": ["success", "error", "warning"]}}
        
        if module:
            filters["module"] = module
        
        if utilisateur_email:
            filters["utilisateur_email"] = utilisateur_email
        
        if action:
            filters["action"] = action
        
        # Query audit logs
        audit_logs = await db.audit_logs.find(filters).skip(offset).limit(limite).sort("timestamp", -1).to_list(None)
        
        # Convert ObjectId to string for JSON response
        result = []
        for log in audit_logs:
            log["_id"] = str(log.get("_id", ""))
            result.append(log)
        
        return result
    
    @router.get("/stats", response_model=dict)
    async def get_audit_stats(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        """
        GET /api/audit/stats
        Summary statistics of audit logs
        Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR
        """
        me = await resolve_user(request, authorization)
        
        # RBAC check
        if me.get("role") not in AUDIT_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"Audit access denied. Required roles: {AUDIT_ROLES}"
            )
        
        total_logs = await db.audit_logs.count_documents({})
        success_count = await db.audit_logs.count_documents({"statut": "success"})
        error_count = await db.audit_logs.count_documents({"statut": "error"})
        warning_count = await db.audit_logs.count_documents({"statut": "warning"})
        
        # Get unique modules and actions
        modules = await db.audit_logs.distinct("module")
        actions = await db.audit_logs.distinct("action")
        
        return {
            "total_logs": total_logs,
            "success_count": success_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "unique_modules": len(modules) if modules else 0,
            "unique_actions": len(actions) if actions else 0,
            "modules": sorted(modules) if modules else [],
            "actions": sorted(actions) if actions else [],
        }
    
    return router
'''

def add_audit_endpoint():
    """Add audit endpoint to administration_module.py"""
    
    print("=" * 80)
    print("FIX #3: ADD AUDIT ENDPOINT")
    print("=" * 80)
    
    try:
        with open("/home/user/ERP-FABS-V10/backend/administration_module.py", "r") as f:
            content = f.read()
        
        # Check if endpoint already exists
        if "def build_audit_router" in content:
            print("✅ Audit endpoint already exists")
            return True
        
        # Append endpoint code
        with open("/home/user/ERP-FABS-V10/backend/administration_module.py", "a") as f:
            f.write("\n" + AUDIT_ENDPOINT_CODE)
        
        print("✅ Audit endpoint added to administration_module.py")
        print("\nEndpoints:")
        print("  - GET /api/audit (list logs with filters)")
        print("  - GET /api/audit/stats (summary statistics)")
        print("\nRBAC:")
        print("  Accessible to: SUPER_ADMIN, ADMIN, AUDITEUR")
        print("\n✅ FIX #3 COMPLETED")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = add_audit_endpoint()
    sys.exit(0 if success else 1)
