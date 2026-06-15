"""
Module Backup & Disaster Recovery — Sauvegarde locale automatique
Scheduler APScheduler, mongodump, compression ZIP, rotation automatique
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging
import os
import subprocess
import shutil
import zipfile
import hashlib
import glob

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("fabsci.backup")

# ============================================================================
# CONSTANTES
# ============================================================================

READ_ROLES  = ["super_admin", "admin"]
WRITE_ROLES = ["super_admin", "admin"]

BACKUP_BASE = os.path.abspath(
    os.getenv("BACKUP_PATH", os.path.join(os.path.dirname(__file__), "backups"))
)

# Référence globale au scheduler (initialisé dans build_backup_router)
_scheduler: Optional[AsyncIOScheduler] = None
_db_ref = None

# ============================================================================
# SCHEMAS
# ============================================================================

class BackupConfigIn(BaseModel):
    frequence_heures: int  = Field(ge=1, le=168, default=24)
    heure_execution:  str  = "02:00"
    retention_jours:  int  = Field(ge=1, le=365, default=30)
    actif:            bool = True
    chiffrement:      bool = False
    compression:      bool = True

class BackupConfigOut(BaseModel):
    config_id:        str
    frequence_heures: int = 24
    heure_execution:  str = "02:00"
    retention_jours:  int = 30
    actif:            bool = True
    chiffrement:      bool = False
    compression:      bool = True
    dernier_backup:   Optional[str] = None
    prochain_backup:  Optional[str] = None
    backup_path:      str = ""
    created_at:       str = ""

class BackupOut(BaseModel):
    backup_id:      str
    type_backup:    str
    chemin_fichier: str
    taille_octets:  int
    checksum:       Optional[str] = None
    statut:         str
    message:        Optional[str] = None
    created_at:     str
    created_by:     str

class RestoreIn(BaseModel):
    backup_id: str

class RestoreOut(BaseModel):
    restore_id:   str
    backup_id:    str
    statut:       str
    date_restore: str
    restore_par:  str

# ============================================================================
# HELPERS
# ============================================================================

def _ensure(condition: bool, status: int, msg: str):
    if not condition:
        raise HTTPException(status_code=status, detail=msg)

def _get_subdir(name: str) -> str:
    path = os.path.join(BACKUP_BASE, name)
    os.makedirs(path, exist_ok=True)
    return path

def _checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def _fmt_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except Exception:
        return 0

def _next_run_time(heure: str) -> str:
    """Calcule la prochaine exécution à partir de heure HH:MM."""
    try:
        h, m  = map(int, heure.split(":"))
        now   = datetime.now()
        nxt   = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(days=1)
        return nxt.isoformat()
    except Exception:
        return ""

# ── Suppression du dossier temporaire ──
def _cleanup_tmp(tmp: str):
    if os.path.isdir(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

# ── Dump MongoDB ──────────────────────────────────────────────────────────────
def _do_mongodump(out_dir: str) -> bool:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name   = os.getenv("DB_NAME", "fabsci_erp")
    result = subprocess.run(
        ["mongodump", f"--uri={mongo_url}/{db_name}", f"--out={out_dir}"],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        logger.error(f"mongodump stderr: {result.stderr}")
        raise RuntimeError(f"mongodump échoué : {result.stderr[:300]}")
    return True

# ── Restauration MongoDB ──────────────────────────────────────────────────────
def _do_mongorestore(dump_dir: str):
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name   = os.getenv("DB_NAME", "fabsci_erp")
    result = subprocess.run(
        ["mongorestore", f"--uri={mongo_url}/{db_name}", "--drop", dump_dir],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        logger.error(f"mongorestore stderr: {result.stderr}")
        raise RuntimeError(f"mongorestore échoué : {result.stderr[:300]}")

# ── Création du backup complet ─────────────────────────────────────────────────
async def _run_backup(db, user_id: str = "scheduler") -> dict:
    ts        = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{ts}"
    db_dir    = _get_subdir("Database")
    tmp_dump  = os.path.join(db_dir, f"tmp_{backup_id}")
    zip_path  = os.path.join(db_dir, f"{backup_id}.zip")

    try:
        os.makedirs(tmp_dump, exist_ok=True)

        # 1. mongodump
        _do_mongodump(tmp_dump)

        # 2. compression ZIP
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(tmp_dump):
                for file in files:
                    fp = os.path.join(root, file)
                    zf.write(fp, os.path.relpath(fp, tmp_dump))

        _cleanup_tmp(tmp_dump)

        size     = _fmt_size(zip_path)
        checksum = _checksum(zip_path)

        doc = {
            "backup_id":      backup_id,
            "type_backup":    "complet",
            "chemin_fichier": zip_path,
            "taille_octets":  size,
            "checksum":       checksum,
            "statut":         "succes",
            "message":        None,
            "created_at":     datetime.now(timezone.utc).isoformat(),
            "created_by":     user_id,
        }
        await db.backups.insert_one(doc)
        await db.backup_config.update_one(
            {"config_id": "default"},
            {"$set": {"dernier_backup": doc["created_at"]}},
            upsert=True,
        )
        logger.info(f"[Backup] Succès — {backup_id} ({size} o)")
        return doc

    except Exception as e:
        _cleanup_tmp(tmp_dump)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        err_doc = {
            "backup_id":      backup_id,
            "type_backup":    "complet",
            "chemin_fichier": "",
            "taille_octets":  0,
            "checksum":       None,
            "statut":         "echec",
            "message":        str(e),
            "created_at":     datetime.now(timezone.utc).isoformat(),
            "created_by":     user_id,
        }
        await db.backups.insert_one(err_doc)
        logger.error(f"[Backup] Échec — {e}")
        raise

# ── Rotation / nettoyage des anciens backups ───────────────────────────────────
async def _apply_retention(db):
    config = await db.backup_config.find_one({"config_id": "default"})
    if not config:
        return
    retention = config.get("retention_jours", 30)
    cutoff    = datetime.now(timezone.utc) - timedelta(days=retention)
    old_docs  = await db.backups.find(
        {"statut": "succes", "created_at": {"$lt": cutoff.isoformat()}}
    ).to_list(500)
    for doc in old_docs:
        fp = doc.get("chemin_fichier", "")
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
                logger.info(f"[Retention] Supprimé : {fp}")
            except Exception as ex:
                logger.warning(f"[Retention] Erreur suppression {fp}: {ex}")
        await db.backups.delete_one({"backup_id": doc["backup_id"]})

# ── Scheduler job ──────────────────────────────────────────────────────────────
async def _scheduled_backup_job():
    if _db_ref is None:
        return
    logger.info("[Scheduler] Démarrage backup planifié")
    try:
        await _run_backup(_db_ref, user_id="scheduler")
        await _apply_retention(_db_ref)
    except Exception as e:
        logger.error(f"[Scheduler] Backup planifié échoué : {e}")

# ── (Re)planifier le scheduler ─────────────────────────────────────────────────
def _reschedule(heure: str, actif: bool):
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.remove_all_jobs()
    if actif:
        try:
            h, m = map(int, heure.split(":"))
            _scheduler.add_job(
                _scheduled_backup_job,
                CronTrigger(hour=h, minute=m),
                id="daily_backup",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] Planifié à {heure} chaque jour")
        except Exception as e:
            logger.error(f"[Scheduler] Erreur planification : {e}")

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_backup_router(db, resolve_user):
    global _scheduler, _db_ref
    _db_ref = db

    # ── Démarrage du scheduler ──
    _scheduler = AsyncIOScheduler(timezone="Africa/Abidjan")
    _scheduler.start()

    # ── Lire config initiale et planifier ──
    import asyncio

    async def _init_scheduler():
        config = await db.backup_config.find_one({"config_id": "default"})
        if config and config.get("actif", True):
            _reschedule(config.get("heure_execution", "02:00"), True)
        else:
            _reschedule("02:00", True)  # défaut si pas encore de config

    asyncio.get_event_loop().create_task(_init_scheduler())

    router = APIRouter(prefix="/backup", tags=["backup"])

    # ── Config ────────────────────────────────────────────────────────────────

    @router.get("/config", response_model=BackupConfigOut)
    async def get_backup_config(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        config = await db.backup_config.find_one({"config_id": "default"}, {"_id": 0})
        if not config:
            config = {
                "config_id": "default", "frequence_heures": 24,
                "heure_execution": "02:00", "retention_jours": 30,
                "actif": True, "chiffrement": False, "compression": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            # Persister la config par défaut en DB
            await db.backup_config.update_one(
                {"config_id": "default"}, {"$setOnInsert": config}, upsert=True
            )
        config.setdefault("dernier_backup", None)
        config["prochain_backup"] = _next_run_time(config.get("heure_execution", "02:00"))
        config["backup_path"]     = BACKUP_BASE
        return BackupConfigOut(**config)

    @router.put("/config", response_model=BackupConfigOut)
    async def update_backup_config(
        payload: BackupConfigIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        doc = {
            "config_id": "default",
            **payload.dict(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.backup_config.update_one(
            {"config_id": "default"}, {"$set": doc}, upsert=True
        )
        _reschedule(payload.heure_execution, payload.actif)
        existing = await db.backup_config.find_one({"config_id": "default"}, {"_id": 0})
        existing.setdefault("dernier_backup", None)
        existing["prochain_backup"] = _next_run_time(payload.heure_execution)
        existing["backup_path"]     = BACKUP_BASE
        logger.info(f"Config backup mise à jour par {user['email']}")
        return BackupConfigOut(**existing)

    # ── Backups ───────────────────────────────────────────────────────────────

    @router.post("/backups", response_model=BackupOut, status_code=201)
    async def create_backup_manual(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        try:
            doc = await _run_backup(db, user_id=user["user_id"])
            return BackupOut(**doc)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/backups", response_model=List[BackupOut])
    async def list_backups(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        limit: int = Query(50, le=200),
        skip:  int = Query(0, ge=0),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        cursor = db.backups.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs   = await cursor.to_list(limit)
        result = []
        for d in docs:
            d.setdefault("checksum", None)
            d.setdefault("message", None)
            result.append(BackupOut(**d))
        return result

    @router.post("/restore", response_model=RestoreOut, status_code=201)
    async def restore_backup_endpoint(
        payload: RestoreIn,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        backup = await db.backups.find_one({"backup_id": payload.backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="Backup introuvable")
        zip_path = backup.get("chemin_fichier", "")
        if not zip_path or not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="Fichier backup introuvable sur le disque")
        tmp_restore = zip_path.replace(".zip", "_restore_tmp")
        try:
            os.makedirs(tmp_restore, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_restore)
            _do_mongorestore(tmp_restore)
            _cleanup_tmp(tmp_restore)
            restore_doc = {
                "restore_id":   f"restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "backup_id":    payload.backup_id,
                "statut":       "succes",
                "date_restore": datetime.now(timezone.utc).isoformat(),
                "restore_par":  user["user_id"],
            }
            await db.restores.insert_one(restore_doc)
            logger.info(f"Restore {restore_doc['restore_id']} par {user['email']}")
            return RestoreOut(**restore_doc)
        except Exception as e:
            _cleanup_tmp(tmp_restore)
            logger.error(f"Restore échoué : {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/backups/{backup_id}")
    async def delete_backup(
        backup_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        backup = await db.backups.find_one({"backup_id": backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="Backup introuvable")
        fp = backup.get("chemin_fichier", "")
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception as e:
                logger.warning(f"Suppression fichier échouée : {e}")
        await db.backups.delete_one({"backup_id": backup_id})
        logger.info(f"Backup supprimé : {backup_id} par {user['email']}")
        return {"message": "Backup supprimé"}

    # ── Stats disque ──────────────────────────────────────────────────────────

    @router.get("/stats")
    async def backup_stats(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        total_size = 0
        count      = 0
        db_dir     = os.path.join(BACKUP_BASE, "Database")
        if os.path.isdir(db_dir):
            for f in glob.glob(os.path.join(db_dir, "*.zip")):
                total_size += os.path.getsize(f)
                count += 1
        # Espace disque
        try:
            usage = shutil.disk_usage(BACKUP_BASE)
            free_gb  = round(usage.free  / 1e9, 2)
            total_gb = round(usage.total / 1e9, 2)
            used_gb  = round(usage.used  / 1e9, 2)
        except Exception:
            free_gb = total_gb = used_gb = None
        return {
            "backup_count":    count,
            "total_size_bytes": total_size,
            "backup_path":     BACKUP_BASE,
            "disk": {
                "total_gb": total_gb,
                "used_gb":  used_gb,
                "free_gb":  free_gb,
            }
        }

    # ── Téléchargement d'un backup ────────────────────────────────────────────

    @router.get("/backups/{backup_id}/download")
    async def download_backup(
        backup_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ):
        from fastapi.responses import FileResponse
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")
        db_dir   = os.path.join(BACKUP_BASE, "Database")
        zip_path = os.path.join(db_dir, f"{backup_id}.zip")
        if not os.path.isfile(zip_path):
            raise HTTPException(status_code=404, detail="Fichier backup introuvable")
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"{backup_id}.zip",
        )

    return router
