"""
Module Workflow Approvals & Audit - Approbations multi-niveaux et signature électronique
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger("fabsci.workflow_approvals")

# ============================================================================
# SCHEMAS
# ============================================================================

class ApprovalWorkflowIn(BaseModel):
    type_entite: str = Field(pattern="^(commande|facture|paiement|mission|achat)$")
    entite_id: str
    niveau_requis: int = Field(ge=1, le=5)
    approbateurs: List[str]
    description: Optional[str] = None

class ApprovalWorkflowOut(BaseModel):
    workflow_id: str
    type_entite: str
    entite_id: str
    niveau_requis: int
    approbateurs: List[str]
    description: Optional[str] = None
    statut: str
    created_at: str
    created_by: str

class ApprovalStepIn(BaseModel):
    workflow_id: str
    approbateur_id: str
    commentaire: Optional[str] = None

class ApprovalStepOut(BaseModel):
    step_id: str
    workflow_id: str
    approbateur_id: str
    statut: str
    commentaire: Optional[str] = None
    date_action: str

class SignatureElectroniqueIn(BaseModel):
    document_id: str
    signataire_id: str
    signature_data: str
    type_signature: str = Field(pattern="^(dessin|texte|image)$")

class SignatureElectroniqueOut(BaseModel):
    signature_id: str
    document_id: str
    signataire_id: str
    signature_data: str
    type_signature: str
    date_signature: str
    valide: bool

class AuditLogOut(BaseModel):
    log_id: Optional[str] = None
    action: str
    entite_type: Optional[str] = None
    entite_id: Optional[str] = None
    user_id: str
    details: dict
    ip_address: Optional[str] = None
    date_action: Optional[str] = None

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "directeur_general", "comptable"]
WRITE_ROLES = ["super_admin", "admin", "directeur_general"]
APPROVER_ROLES = ["super_admin", "admin", "directeur_general", "comptable"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

async def _check_workflow_completion(db, workflow_id: str) -> bool:
    workflow = await db.approval_workflows.find_one({"workflow_id": workflow_id})
    if not workflow:
        return False
    
    steps = await db.approval_steps.find({"workflow_id": workflow_id}).to_list(100)
    approved_steps = [s for s in steps if s["statut"] == "approuve"]
    
    return len(approved_steps) >= workflow["niveau_requis"]

async def _log_audit(db, action: str, entite_type: str, entite_id: str, user_id: str, details: dict, ip_address: Optional[str] = None):
    log_doc = {
        "log_id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
        "action": action,
        "entite_type": entite_type,
        "entite_id": entite_id,
        "user_id": user_id,
        "details": details,
        "ip_address": ip_address,
        "date_action": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(log_doc)

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_workflow_approvals_router(db, resolve_user):
    router = APIRouter(prefix="/workflow-approvals", tags=["workflow-approvals"])

    @router.get("/workflows", response_model=List[ApprovalWorkflowOut])
    async def list_workflows(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        type_entite: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if type_entite:
            filters["type_entite"] = type_entite
        if statut:
            filters["statut"] = statut

        cursor = db.approval_workflows.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [ApprovalWorkflowOut(**d) for d in docs]

    @router.post("/workflows", response_model=ApprovalWorkflowOut, status_code=201)
    async def create_workflow(
        payload: ApprovalWorkflowIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        workflow_id = f"wf_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        workflow_doc = {
            "workflow_id": workflow_id,
            "type_entite": payload.type_entite,
            "entite_id": payload.entite_id,
            "niveau_requis": payload.niveau_requis,
            "approbateurs": payload.approbateurs,
            "description": payload.description,
            "statut": "en_attente",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.approval_workflows.insert_one(workflow_doc)
        
        await _log_audit(db, "workflow_created", payload.type_entite, payload.entite_id, user["user_id"], {
            "workflow_id": workflow_id,
            "niveau_requis": payload.niveau_requis
        })

        logger.info(f"Workflow créé: {workflow_id} par {user['email']}")
        return ApprovalWorkflowOut(**workflow_doc)

    @router.post("/approvals", response_model=ApprovalStepOut, status_code=201)
    async def create_approval_step(
        payload: ApprovalStepIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in APPROVER_ROLES, 403, "Accès réservé")

        workflow = await db.approval_workflows.find_one({"workflow_id": payload.workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        
        if user["user_id"] not in workflow["approbateurs"]:
            raise HTTPException(status_code=403, detail="Non autorisé")

        step_id = f"step_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        step_doc = {
            "step_id": step_id,
            "workflow_id": payload.workflow_id,
            "approbateur_id": payload.approbateur_id,
            "statut": "approuve",
            "commentaire": payload.commentaire,
            "date_action": datetime.now(timezone.utc).isoformat()
        }

        await db.approval_steps.insert_one(step_doc)
        
        await _log_audit(db, "approval_given", workflow["type_entite"], workflow["entite_id"], user["user_id"], {
            "workflow_id": payload.workflow_id,
            "step_id": step_id
        })

        is_completed = await _check_workflow_completion(db, payload.workflow_id)
        if is_completed:
            await db.approval_workflows.update_one(
                {"workflow_id": payload.workflow_id},
                {"$set": {"statut": "approuve"}}
            )
            await _log_audit(db, "workflow_completed", workflow["type_entite"], workflow["entite_id"], user["user_id"], {
                "workflow_id": payload.workflow_id
            })

        return ApprovalStepOut(**step_doc)

    @router.post("/rejections")
    async def reject_workflow(
        workflow_id: str,
        commentaire: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in APPROVER_ROLES, 403, "Accès réservé")

        workflow = await db.approval_workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow introuvable")
        
        if user["user_id"] not in workflow["approbateurs"]:
            raise HTTPException(status_code=403, detail="Non autorisé")

        await db.approval_workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": {"statut": "rejete"}}
        )

        await _log_audit(db, "workflow_rejected", workflow["type_entite"], workflow["entite_id"], user["user_id"], {
            "workflow_id": workflow_id,
            "commentaire": commentaire
        })

        return {"message": "Workflow rejeté"}

    @router.post("/signatures", response_model=SignatureElectroniqueOut, status_code=201)
    async def create_signature(
        payload: SignatureElectroniqueIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        signature_id = f"sig_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        signature_doc = {
            "signature_id": signature_id,
            "document_id": payload.document_id,
            "signataire_id": payload.signataire_id,
            "signature_data": payload.signature_data,
            "type_signature": payload.type_signature,
            "date_signature": datetime.now(timezone.utc).isoformat(),
            "valide": True
        }

        await db.signatures_electroniques.insert_one(signature_doc)
        
        await _log_audit(db, "document_signed", "document", payload.document_id, user["user_id"], {
            "signature_id": signature_id,
            "type_signature": payload.type_signature
        })

        return SignatureElectroniqueOut(**signature_doc)

    @router.get("/audit-logs", response_model=List[AuditLogOut])
    async def list_audit_logs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if action:
            filters["action"] = action
        if resource_type:
            filters["resource_type"] = resource_type
        if resource_id:
            filters["resource_id"] = resource_id

        # On filtre uniquement les logs créés par ce module (ont un champ log_id)
        filters["log_id"] = {"$exists": True}
        cursor = db.audit_logs.find(filters, {"_id": 0}).sort("date_action", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        result = []
        for d in docs:
            try:
                result.append(AuditLogOut(**d))
            except Exception:
                pass
        return result

    return router
