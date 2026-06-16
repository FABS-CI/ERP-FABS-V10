"""
Module Notifications - Système de notifications et alertes métier
Sprint 1 V10 : Moteur Central de Notifications ERP (temps réel WebSocket)
"""

from fastapi import APIRouter, HTTPException, Header, Request, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Set
from datetime import datetime, timezone, timedelta
import logging
import json
import os
import uuid
import asyncio

import jwt

logger = logging.getLogger("fabsci.notifications")


# ============================================================================
# CONNECTION MANAGER — WebSocket par utilisateur
# ============================================================================
class NotificationConnectionManager:
    """
    Gestionnaire de connexions WebSocket par user_id.
    Permet de pousser une notification à toutes les sessions d'un utilisateur
    (ex : un user connecté simultanément sur desktop + mobile).
    """

    def __init__(self) -> None:
        self._active: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._active.setdefault(user_id, set()).add(ws)
        logger.info("WS connect user=%s total_sessions=%d", user_id, len(self._active[user_id]))

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            if user_id in self._active:
                self._active[user_id].discard(ws)
                if not self._active[user_id]:
                    self._active.pop(user_id, None)
        logger.info("WS disconnect user=%s", user_id)

    async def send_to_user(self, user_id: str, payload: dict) -> int:
        """Envoie un payload JSON à toutes les sessions WebSocket d'un user.
        Retourne le nombre de sessions atteintes."""
        sockets = list(self._active.get(user_id, set()))
        delivered = 0
        for ws in sockets:
            try:
                await ws.send_json(payload)
                delivered += 1
            except Exception as exc:  # connexion fermée ou cassée
                logger.warning("WS send failed user=%s err=%s", user_id, exc)
                await self.disconnect(user_id, ws)
        return delivered

    def active_users(self) -> List[str]:
        return list(self._active.keys())


# Singleton global accessible aussi depuis les autres modules métier
manager = NotificationConnectionManager()


# ============================================================================
# SCHEMAS
# ============================================================================

class NotificationIn(BaseModel):
    user_id: str
    type: str = Field(pattern="^(info|warning|error|success)$")
    categorie: str = Field(pattern="^(stock|commande|paiement|livraison|systeme)$")
    titre: str
    message: str
    lien: Optional[str] = None

class NotificationOut(BaseModel):
    notification_id: str
    user_id: str
    type: str
    categorie: str
    titre: str
    message: str
    lien: Optional[str] = None
    lue: bool
    created_at: str
    expires_at: Optional[str] = None

class NotificationPreferenceIn(BaseModel):
    stock_alertes: bool = True
    commande_alertes: bool = True
    paiement_alertes: bool = True
    livraison_alertes: bool = True
    email_notifications: bool = True
    in_app_notifications: bool = True

class NotificationPreferenceOut(BaseModel):
    user_id: str
    preferences: dict
    updated_at: str

class EmailTemplateIn(BaseModel):
    code: str
    sujet: str
    corps_html: str
    corps_texte: str
    variables: List[str]

class EmailTemplateOut(BaseModel):
    template_id: str
    code: str
    sujet: str
    corps_html: str
    corps_texte: str
    variables: List[str]
    actif: bool
    created_at: str
    updated_at: str

class EmailLogOut(BaseModel):
    email_log_id: str
    template_id: str
    destinataire: str
    sujet: str
    statut: str
    erreur: Optional[str] = None
    variables: dict
    sent_at: Optional[str] = None

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire"]
WRITE_ROLES = ["super_admin", "admin"]
DELETE_ROLES = ["super_admin"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

async def _get_user_preferences(db, user_id: str) -> dict:
    """Récupérer les préférences de notification d'un utilisateur"""
    prefs = await db.notification_preferences.find_one({"user_id": user_id})
    if prefs:
        return prefs.get("preferences", {})
    # Préférences par défaut
    return {
        "stock_alertes": True,
        "commande_alertes": True,
        "paiement_alertes": True,
        "livraison_alertes": True,
        "email_notifications": True,
        "in_app_notifications": True
    }

async def _send_notification(db, user_id: str, type: str, categorie: str, titre: str, message: str, lien: Optional[str] = None):
    """Envoyer une notification interne à un utilisateur.
    - Persiste dans `notifications`
    - Logue dans `notification_logs`
    - Push WebSocket temps réel à toutes les sessions de l'utilisateur
    """
    prefs = await _get_user_preferences(db, user_id)

    if not prefs.get("in_app_notifications", True):
        return None

    now = datetime.now(timezone.utc)
    notification_id = f"notif_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    notification_doc = {
        "notification_id": notification_id,
        "user_id": user_id,
        "type": type,
        "categorie": categorie,
        "titre": titre,
        "message": message,
        "lien": lien,
        "lue": False,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
    }

    await db.notifications.insert_one(notification_doc)

    # Audit log
    try:
        await db.notification_logs.insert_one({
            "log_id": f"nlog_{uuid.uuid4().hex[:12]}",
            "notification_id": notification_id,
            "user_id": user_id,
            "categorie": categorie,
            "titre": titre,
            "channel": "in_app",
            "status": "created",
            "ts": now.isoformat(),
        })
    except Exception as exc:  # logs non bloquants
        logger.warning("Erreur insertion notification_logs: %s", exc)

    # Push temps réel
    payload = {k: v for k, v in notification_doc.items() if k != "_id"}
    payload["event"] = "notification:new"
    try:
        delivered = await manager.send_to_user(user_id, payload)
        if delivered > 0:
            await db.notification_logs.insert_one({
                "log_id": f"nlog_{uuid.uuid4().hex[:12]}",
                "notification_id": notification_id,
                "user_id": user_id,
                "categorie": categorie,
                "titre": titre,
                "channel": "websocket",
                "status": "delivered",
                "sessions_count": delivered,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:
        logger.warning("WS push failed user=%s err=%s", user_id, exc)

    logger.info("Notification envoyée user=%s titre=%s", user_id, titre)
    return notification_id


async def publish_notification(db, user_id: str, type: str, categorie: str, titre: str, message: str, lien: Optional[str] = None):
    """API publique pour les autres modules métier (commandes, factures…)."""
    return await _send_notification(db, user_id, type, categorie, titre, message, lien)


# Rôles qui reçoivent les notifications vente
VENTE_NOTIF_ROLES = {
    "super_admin", "directeur_general", "directeur_commercial",
    "secretariat", "assistante_commerciale", "comptable",
    "responsable_magasinier", "service_logistique",
}


async def notify_vente_event(
    db,
    type: str,
    categorie: str,
    titre: str,
    message: str,
    lien: Optional[str] = None,
    exclude_user_id: Optional[str] = None,
):
    """
    Envoie une notification à tous les utilisateurs actifs ayant un rôle vente.
    exclude_user_id : ne pas notifier l'auteur de l'action.
    """
    try:
        cursor = db.users.find(
            {"role": {"$in": list(VENTE_NOTIF_ROLES)}, "actif": True},
            {"user_id": 1, "_id": 0},
        )
        users = await cursor.to_list(500)
        tasks = []
        for u in users:
            uid = u.get("user_id")
            if not uid:
                continue
            if exclude_user_id and uid == exclude_user_id:
                continue
            tasks.append(_send_notification(db, uid, type, categorie, titre, message, lien))
        if tasks:
            import asyncio as _aio
            await _aio.gather(*tasks, return_exceptions=True)
        logger.info("notify_vente_event titre=%s → %d destinataires", titre, len(tasks))
    except Exception as exc:
        logger.error("notify_vente_event error: %s", exc)

async def _publish_event(db, event_type: str, payload: dict):
    """Publier un événement sur Redis pour traitement asynchrone"""
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
        await redis_client.publish(f"events:{event_type}", json.dumps(payload))
    except Exception as e:
        logger.error(f"Erreur publication événement: {e}")

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_notifications_router(db, resolve_user):
    router = APIRouter(prefix="/notifications", tags=["notifications"])

    # ============================================================================
    # NOTIFICATIONS ENDPOINTS
    # ============================================================================

    @router.get("", response_model=List[NotificationOut])
    async def list_notifications(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        categorie: Optional[str] = None,
        lue: Optional[bool] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les notifications de l'utilisateur connecté"""
        user = await resolve_user(request, authorization)
        
        filters = {"user_id": user["user_id"]}
        if categorie:
            filters["categorie"] = categorie
        if lue is not None:
            filters["lue"] = lue
        
        cursor = db.notifications.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [NotificationOut(**d) for d in docs]

    @router.get("/non-lues", response_model=List[NotificationOut])
    async def list_unread_notifications(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Lister les notifications non lues"""
        user = await resolve_user(request, authorization)
        
        filters = {"user_id": user["user_id"], "lue": False}
        cursor = db.notifications.find(filters, {"_id": 0}).sort("created_at", -1).limit(50)
        docs = await cursor.to_list(50)
        return [NotificationOut(**d) for d in docs]

    @router.get("/count")
    async def count_unread(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Compter les notifications non lues"""
        user = await resolve_user(request, authorization)
        
        count = await db.notifications.count_documents({"user_id": user["user_id"], "lue": False})
        return {"count": count}

    @router.patch("/{notification_id}/lire")
    async def mark_as_read(
        notification_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Marquer une notification comme lue"""
        user = await resolve_user(request, authorization)
        
        notification = await db.notifications.find_one({"notification_id": notification_id})
        if not notification:
            raise HTTPException(status_code=404, detail="Notification introuvable")
        
        if notification["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        await db.notifications.update_one(
            {"notification_id": notification_id},
            {"$set": {"lue": True}}
        )
        
        return {"message": "Notification marquée comme lue"}

    @router.patch("/tout-lire")
    async def mark_all_as_read(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Marquer toutes les notifications comme lues"""
        user = await resolve_user(request, authorization)
        
        await db.notifications.update_many(
            {"user_id": user["user_id"], "lue": False},
            {"$set": {"lue": True}}
        )
        
        return {"message": "Toutes les notifications marquées comme lues"}

    @router.delete("/{notification_id}")
    async def delete_notification(
        notification_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Supprimer une notification"""
        user = await resolve_user(request, authorization)
        
        notification = await db.notifications.find_one({"notification_id": notification_id})
        if not notification:
            raise HTTPException(status_code=404, detail="Notification introuvable")
        
        if notification["user_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        await db.notifications.delete_one({"notification_id": notification_id})
        
        return {"message": "Notification supprimée"}

    # ============================================================================
    # PREFERENCES ENDPOINTS
    # ============================================================================

    @router.get("/preferences", response_model=NotificationPreferenceOut)
    async def get_preferences(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Récupérer les préférences de notification"""
        user = await resolve_user(request, authorization)
        
        prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]})
        if not prefs:
            # Créer les préférences par défaut
            default_prefs = {
                "user_id": user["user_id"],
                "preferences": {
                    "stock_alertes": True,
                    "commande_alertes": True,
                    "paiement_alertes": True,
                    "livraison_alertes": True,
                    "email_notifications": True,
                    "in_app_notifications": True
                },
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notification_preferences.insert_one(default_prefs)
            prefs = default_prefs
        
        return NotificationPreferenceOut(**prefs)

    @router.put("/preferences", response_model=NotificationPreferenceOut)
    async def update_preferences(
        payload: NotificationPreferenceIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour les préférences de notification"""
        user = await resolve_user(request, authorization)
        
        update_data = {
            "preferences": payload.dict(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notification_preferences.update_one(
            {"user_id": user["user_id"]},
            {"$set": update_data},
            upsert=True
        )
        
        updated = await db.notification_preferences.find_one({"user_id": user["user_id"]})
        return NotificationPreferenceOut(**updated)

    # ============================================================================
    # EMAIL TEMPLATES ENDPOINTS (ADMIN)
    # ============================================================================

    @router.get("/templates", response_model=List[EmailTemplateOut])
    async def list_email_templates(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Lister les templates d'email (admin)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        
        cursor = db.email_templates.find({}, {"_id": 0}).sort("code", 1)
        docs = await cursor.to_list(100)
        return [EmailTemplateOut(**d) for d in docs]

    @router.post("/templates", response_model=EmailTemplateOut, status_code=201)
    async def create_email_template(
        payload: EmailTemplateIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Créer un template d'email (admin)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        
        template_id = f"tpl_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        template_doc = {
            "template_id": template_id,
            "code": payload.code,
            "sujet": payload.sujet,
            "corps_html": payload.corps_html,
            "corps_texte": payload.corps_texte,
            "variables": payload.variables,
            "actif": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.email_templates.insert_one(template_doc)
        logger.info(f"Template email créé: {payload.code} par {user['email']}")
        
        return EmailTemplateOut(**template_doc)

    @router.put("/templates/{template_id}", response_model=EmailTemplateOut)
    async def update_email_template(
        template_id: str,
        payload: EmailTemplateIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Mettre à jour un template d'email (admin)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        
        existing = await db.email_templates.find_one({"template_id": template_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Template introuvable")
        
        update_data = {
            "code": payload.code,
            "sujet": payload.sujet,
            "corps_html": payload.corps_html,
            "corps_texte": payload.corps_texte,
            "variables": payload.variables,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.email_templates.update_one({"template_id": template_id}, {"$set": update_data})
        
        updated = await db.email_templates.find_one({"template_id": template_id}, {"_id": 0})
        return EmailTemplateOut(**updated)

    @router.delete("/templates/{template_id}")
    async def delete_email_template(
        template_id: str,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Supprimer un template d'email (admin)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in DELETE_ROLES, 403, "Accès réservé")
        
        await db.email_templates.delete_one({"template_id": template_id})
        logger.info(f"Template email supprimé: {template_id} par {user['email']}")
        
        return {"message": "Template supprimé"}

    # ============================================================================
    # EMAIL LOGS ENDPOINTS (ADMIN)
    # ============================================================================

    @router.get("/logs", response_model=List[EmailLogOut])
    async def list_email_logs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        destinataire: Optional[str] = None,
        statut: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = Query(0, ge=0)
    ):
        """Lister les logs d'envoi d'emails (admin)"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")
        
        filters = {}
        if destinataire:
            filters["destinataire"] = destinataire
        if statut:
            filters["statut"] = statut
        
        cursor = db.email_logs.find(filters, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)
        return [EmailLogOut(**d) for d in docs]

    # ============================================================================
    # HELPER ENDPOINT FOR TESTING
    # ============================================================================

    @router.post("/test")
    async def send_test_notification(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Envoyer une notification de test"""
        user = await resolve_user(request, authorization)
        
        await _send_notification(
            db,
            user["user_id"],
            "info",
            "systeme",
            "Notification de test",
            "Ceci est une notification de test pour vérifier le système.",
            "/dashboard"
        )
        
        return {"message": "Notification de test envoyée"}

    # ========================================================================
    # WEBSOCKET — Push temps réel (Sprint 1 V10)
    # ========================================================================
    @router.websocket("/ws")
    async def notifications_ws(websocket: WebSocket, token: Optional[str] = Query(default=None)):
        """
        WebSocket endpoint pour notifications temps réel.
        Auth :
        - cookie httpOnly `session_token` (auto-envoyé par le navigateur)
        - OU fallback query param `token=<JWT>` (utile pour tests / clients non-browser)
        URL : `wss://<host>/api/notifications/ws`
        Messages :
        - Le serveur push : `{event:"notification:new", notification_id, titre, ...}`
        - Le client peut envoyer un ping `{"event":"ping"}` → réponse `{"event":"pong"}`
        """
        # Authentification JWT (cookie d'abord, puis query param)
        jwt_token = websocket.cookies.get("session_token") or token
        secret = os.environ.get("JWT_SECRET", "")
        algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
        if not jwt_token or not secret:
            await websocket.close(code=4401, reason="no-token")
            return
        try:
            decoded = jwt.decode(jwt_token, secret, algorithms=[algorithm])
            user_id = decoded.get("user_id")
            if not user_id:
                raise ValueError("missing user_id in token")
        except Exception as exc:
            logger.warning("WS auth failed: %s", exc)
            await websocket.close(code=4401, reason="invalid-token")
            return

        # Connexion acceptée
        await manager.connect(user_id, websocket)
        try:
            # Push compteur initial
            count = await db.notifications.count_documents({"user_id": user_id, "lue": False})
            await websocket.send_json({"event": "notification:count", "count": count})

            while True:
                msg = await websocket.receive_text()
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                if data.get("event") == "ping":
                    await websocket.send_json({"event": "pong", "ts": datetime.now(timezone.utc).isoformat()})
        except WebSocketDisconnect:
            await manager.disconnect(user_id, websocket)
        except Exception as exc:
            logger.warning("WS error user=%s err=%s", user_id, exc)
            await manager.disconnect(user_id, websocket)

    return router
