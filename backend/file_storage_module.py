"""
Module File Storage Enterprise - MinIO/S3, documents, factures PDF
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import logging
import os
import shutil
import uuid

logger = logging.getLogger("fabsci.file_storage")

# C4 fix: validation upload — extensions et types MIME autorisés
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.xlsx', '.xls', '.docx', '.doc', '.csv', '.txt', '.zip'}
ALLOWED_MIME_TYPES = {
    'application/pdf', 'image/jpeg', 'image/png', 'image/gif',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/csv', 'text/plain',
    'application/zip', 'application/octet-stream',
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# ============================================================================
# SCHEMAS
# ============================================================================

class DocumentIn(BaseModel):
    nom: str
    type_document: str = Field(pattern="^(facture|contrat|bon_livraison|bon_commande|autre)$")
    entite_type: str
    entite_id: str
    description: Optional[str] = None

class DocumentOut(BaseModel):
    document_id: str
    nom: str
    type_document: str
    entite_type: str
    entite_id: str
    chemin_fichier: str
    taille_octets: int
    type_mime: str
    description: Optional[str] = None
    created_at: str
    created_by: str

class FacturePDFIn(BaseModel):
    facture_id: str
    chemin_fichier: str

class FacturePDFOut(BaseModel):
    pdf_id: str
    facture_id: str
    chemin_fichier: str
    genere_le: str
    genere_par: str

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "directeur_general", "comptable"]
WRITE_ROLES = ["super_admin", "admin", "directeur_general", "comptable"]
DELETE_ROLES = ["super_admin", "admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

def _get_storage_path() -> str:
    """Récupérer le chemin de stockage des fichiers"""
    storage_path = os.getenv("FILE_STORAGE_PATH", "./storage/documents")
    os.makedirs(storage_path, exist_ok=True)
    return storage_path

def _generate_unique_filename(original_filename: str) -> str:
    """Générer un nom de fichier unique"""
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4()}{ext}"

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_file_storage_router(db, resolve_user):
    router = APIRouter(prefix="/file-storage", tags=["file-storage"])

    # ============================================================================
    # DOCUMENTS ENDPOINTS
    # ============================================================================

    @router.get("/documents", response_model=List[DocumentOut])
    async def list_documents(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        type_document: Optional[str] = None,
        entite_type: Optional[str] = None,
        entite_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les documents"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if type_document:
            filters["type_document"] = type_document
        if entite_type:
            filters["entite_type"] = entite_type
        if entite_id:
            filters["entite_id"] = entite_id

        cursor = db.documents.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [DocumentOut(**d) for d in docs]

    @router.post("/documents/upload", response_model=DocumentOut, status_code=201)
    async def upload_document(
        request: Request,
        file: UploadFile = File(...),
        type_document: str = Query(...),
        entite_type: str = Query(...),
        entite_id: str = Query(...),
        description: Optional[str] = Query(None),
        authorization: Optional[str] = Header(default=None)
    ):
        """Uploader un document"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        storage_path = _get_storage_path()
        unique_filename = _generate_unique_filename(file.filename)
        file_path = os.path.join(storage_path, unique_filename)

        # Sauvegarder le fichier
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Erreur upload fichier: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de l'upload")

        # Récupérer la taille du fichier
        file_size = os.path.getsize(file_path)

        document_id = f"doc_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        document_doc = {
            "document_id": document_id,
            "nom": file.filename,
            "type_document": type_document,
            "entite_type": entite_type,
            "entite_id": entite_id,
            "chemin_fichier": file_path,
            "taille_octets": file_size,
            "type_mime": file.content_type or "application/octet-stream",
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }

        await db.documents.insert_one(document_doc)

        logger.info(f"Document uploadé: {document_id} par {user['email']}")
        return DocumentOut(**document_doc)

    @router.get("/documents/{document_id}", response_model=DocumentOut)
    async def get_document(
        document_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer un document"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        document = await db.documents.find_one({"document_id": document_id}, {"_id": 0})
        if not document:
            raise HTTPException(status_code=404, detail="Document introuvable")
        
        return DocumentOut(**document)

    @router.delete("/documents/{document_id}")
    async def delete_document(
        document_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Supprimer un document"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")

        document = await db.documents.find_one({"document_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document introuvable")

        # Supprimer le fichier physique
        try:
            if os.path.exists(document["chemin_fichier"]):
                os.remove(document["chemin_fichier"])
        except Exception as e:
            logger.error(f"Erreur suppression fichier: {e}")

        await db.documents.delete_one({"document_id": document_id})

        logger.info(f"Document supprimé: {document_id} par {user['email']}")
        return {"message": "Document supprimé"}

    # ============================================================================
    # FACTURES PDF ENDPOINTS
    # ============================================================================

    @router.get("/factures-pdf", response_model=List[FacturePDFOut])
    async def list_factures_pdf(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        facture_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les factures PDF"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if facture_id:
            filters["facture_id"] = facture_id

        cursor = db.factures_pdf.find(filters, {"_id": 0}).sort("genere_le", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [FacturePDFOut(**d) for d in docs]

    @router.post("/factures-pdf", response_model=FacturePDFOut, status_code=201)
    async def create_facture_pdf(
        payload: FacturePDFIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Associer un PDF à une facture"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        # Vérifier que la facture existe
        facture = await db.factures.find_one({"facture_id": payload.facture_id})
        if not facture:
            raise HTTPException(status_code=404, detail="Facture introuvable")

        pdf_id = f"pdf_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        pdf_doc = {
            "pdf_id": pdf_id,
            "facture_id": payload.facture_id,
            "chemin_fichier": payload.chemin_fichier,
            "genere_le": datetime.now(timezone.utc).isoformat(),
            "genere_par": user["user_id"]
        }

        await db.factures_pdf.insert_one(pdf_doc)

        logger.info(f"Facture PDF créé: {pdf_id} par {user['email']}")
        return FacturePDFOut(**pdf_doc)

    # ============================================================================
    # STORAGE STATS
    # ============================================================================

    @router.get("/stats")
    async def get_storage_stats(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les statistiques de stockage"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        storage_path = _get_storage_path()
        
        # Calculer la taille totale
        total_size = 0
        file_count = 0
        
        if os.path.exists(storage_path):
            for root, dirs, files in os.walk(storage_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1

        # Compter les documents dans la base
        total_documents = await db.documents.count_documents({})
        total_factures_pdf = await db.factures_pdf.count_documents({})

        return {
            "storage_path": storage_path,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "file_count": file_count,
            "total_documents": total_documents,
            "total_factures_pdf": total_factures_pdf
        }

    return router
