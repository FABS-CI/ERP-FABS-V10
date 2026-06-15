"""
Module Multi-Channel Notifications - SMS, WhatsApp, Email
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging
import os
import httpx

logger = logging.getLogger("fabsci.multi_channel_notifications")

# ============================================================================
# SCHEMAS
# ============================================================================

class SMSNotificationIn(BaseModel):
    destinataire: str
    message: str
    canal: str = Field(pattern="^(twilio|orange_ci|mtn_ci)$")

class WhatsAppNotificationIn(BaseModel):
    destinataire: str
    message: str
    template_id: Optional[str] = None

class EmailNotificationIn(BaseModel):
    destinataire: str
    sujet: str
    corps_html: str
    corps_texte: str

class NotificationBatchIn(BaseModel):
    destinataires: List[str]
    message: str
    canal: str = Field(pattern="^(sms|whatsapp|email)$")
    priorite: str = Field(pattern="^(low|medium|high|critical)$")

class NotificationBatchOut(BaseModel):
    batch_id: str
    canal: str
    nombre_envoyes: int
    nombre_echecs: int
    echecs: List[dict]
    created_at: str

class NotificationPreferenceIn(BaseModel):
    canal_sms: bool = True
    canal_whatsapp: bool = True
    canal_email: bool = True
    priorite_minimale: str = Field(pattern="^(low|medium|high|critical)$")

# ============================================================================
# HELPERS
# ============================================================================

READ_ROLES = ["super_admin", "admin", "gestionnaire"]
WRITE_ROLES = ["super_admin", "admin", "gestionnaire"]

def _ensure(condition: bool, status: int, message: str):
    if not condition:
        raise HTTPException(status_code=status, detail=message)

# Twilio SMS
async def send_sms_twilio(phone: str, message: str) -> dict:
    """Envoyer SMS via Twilio"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, phone_number]):
        return {"success": False, "error": "Configuration Twilio manquante"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={
                    "From": phone_number,
                    "To": phone,
                    "Body": message
                }
            )
            
            if response.status_code == 201:
                return {"success": True, "message_id": response.json().get("sid")}
            else:
                return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Erreur Twilio: {e}")
        return {"success": False, "error": str(e)}

# Orange CI SMS
async def send_sms_orange_ci(phone: str, message: str) -> dict:
    """Envoyer SMS via Orange CI"""
    client_id = os.getenv("ORANGE_CI_CLIENT_ID")
    client_secret = os.getenv("ORANGE_CI_CLIENT_SECRET")
    sender = os.getenv("ORANGE_CI_SENDER")
    
    if not all([client_id, client_secret, sender]):
        return {"success": False, "error": "Configuration Orange CI manquante"}
    
    try:
        async with httpx.AsyncClient() as client:
            # Obtenir token OAuth
            token_response = await client.post(
                "https://api.orange.com/oauth/v3/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            
            if token_response.status_code != 200:
                return {"success": False, "error": "Erreur authentification Orange CI"}
            
            access_token = token_response.json().get("access_token")
            
            # Envoyer SMS
            sms_response = await client.post(
                "https://api.orange.com/smsmessaging/v1/outbound/tel:+225/requests",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "outboundSMSMessageRequest": {
                        "address": f"tel:{phone}",
                        "senderAddress": f"tel:{sender}",
                        "message": message
                    }
                }
            )
            
            if sms_response.status_code == 201:
                return {"success": True, "message_id": sms_response.json().get("outboundSMSMessageRequest", {}).get("resourceURL")}
            else:
                return {"success": False, "error": sms_response.text}
    except Exception as e:
        logger.error(f"Erreur Orange CI: {e}")
        return {"success": False, "error": str(e)}

# MTN CI SMS
async def send_sms_mtn_ci(phone: str, message: str) -> dict:
    """Envoyer SMS via MTN CI"""
    api_key = os.getenv("MTN_CI_API_KEY")
    api_secret = os.getenv("MTN_CI_API_SECRET")
    sender_id = os.getenv("MTN_CI_SENDER_ID")
    
    if not all([api_key, api_secret, sender_id]):
        return {"success": False, "error": "Configuration MTN CI manquante"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mtn.com/v1/sms",
                headers={
                    "X-API-Key": api_key,
                    "X-API-Secret": api_secret,
                    "Content-Type": "application/json"
                },
                json={
                    "senderId": sender_id,
                    "recipient": phone,
                    "message": message
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "message_id": response.json().get("messageId")}
            else:
                return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Erreur MTN CI: {e}")
        return {"success": False, "error": str(e)}

# WhatsApp Business
async def send_whatsapp(phone: str, message: str, template_id: Optional[str] = None) -> dict:
    """Envoyer message WhatsApp"""
    api_token = os.getenv("WHATSAPP_API_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    
    if not all([api_token, phone_id]):
        return {"success": False, "error": "Configuration WhatsApp manquante"}
    
    try:
        async with httpx.AsyncClient() as client:
            if template_id:
                # Template message
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{phone_id}/messages",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "template",
                        "template": {
                            "name": template_id,
                            "language": {"code": "fr"}
                        }
                    }
                )
            else:
                # Text message
                response = await client.post(
                    f"https://graph.facebook.com/v18.0/{phone_id}/messages",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "text",
                        "text": {"body": message}
                    }
                )
            
            if response.status_code == 200:
                return {"success": True, "message_id": response.json().get("messages", [{}])[0].get("id")}
            else:
                return {"success": False, "error": response.text}
    except Exception as e:
        logger.error(f"Erreur WhatsApp: {e}")
        return {"success": False, "error": str(e)}

# Email SMTP
async def send_email(destinataire: str, sujet: str, corps_html: str, corps_texte: str) -> dict:
    """Envoyer email via SMTP"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")
    
    if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
        return {"success": False, "error": "Configuration SMTP manquante"}
    
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"] = smtp_from
        msg["To"] = destinataire
        
        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
        msg.attach(MIMEText(corps_html, "html", "utf-8"))
        
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {"success": True, "message_id": f"email_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
    except Exception as e:
        logger.error(f"Erreur SMTP: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# ROUTER FACTORY
# ============================================================================

def build_multi_channel_notifications_router(db, resolve_user):
    router = APIRouter(prefix="/multi-channel-notifications", tags=["multi-channel-notifications"])

    # ============================================================================
    # SMS ENDPOINTS
    # ============================================================================

    @router.post("/sms")
    async def send_sms(
        payload: SMSNotificationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Envoyer un SMS"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        if payload.canal == "twilio":
            result = await send_sms_twilio(payload.destinataire, payload.message)
        elif payload.canal == "orange_ci":
            result = await send_sms_orange_ci(payload.destinataire, payload.message)
        elif payload.canal == "mtn_ci":
            result = await send_sms_mtn_ci(payload.destinataire, payload.message)
        else:
            raise HTTPException(status_code=400, detail="Canal SMS invalide")

        # Logger le résultat
        log_doc = {
            "log_id": f"log_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "type": "sms",
            "canal": payload.canal,
            "destinataire": payload.destinataire,
            "message": payload.message,
            "success": result["success"],
            "error": result.get("error"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.notification_logs.insert_one(log_doc)

        if result["success"]:
            return {"message": "SMS envoyé avec succès", "message_id": result.get("message_id")}
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    # ============================================================================
    # WHATSAPP ENDPOINTS
    # ============================================================================

    @router.post("/whatsapp")
    async def send_whatsapp_message(
        payload: WhatsAppNotificationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Envoyer un message WhatsApp"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        result = await send_whatsapp(payload.destinataire, payload.message, payload.template_id)

        # Logger le résultat
        log_doc = {
            "log_id": f"log_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "type": "whatsapp",
            "destinataire": payload.destinataire,
            "message": payload.message,
            "template_id": payload.template_id,
            "success": result["success"],
            "error": result.get("error"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.notification_logs.insert_one(log_doc)

        if result["success"]:
            return {"message": "Message WhatsApp envoyé avec succès", "message_id": result.get("message_id")}
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    # ============================================================================
    # EMAIL ENDPOINTS
    # ============================================================================

    @router.post("/email")
    async def send_email_message(
        payload: EmailNotificationIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Envoyer un email"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        result = await send_email(payload.destinataire, payload.sujet, payload.corps_html, payload.corps_texte)

        # Logger le résultat
        log_doc = {
            "log_id": f"log_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "type": "email",
            "destinataire": payload.destinataire,
            "sujet": payload.sujet,
            "success": result["success"],
            "error": result.get("error"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.notification_logs.insert_one(log_doc)

        if result["success"]:
            return {"message": "Email envoyé avec succès", "message_id": result.get("message_id")}
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    # ============================================================================
    # BATCH NOTIFICATIONS ENDPOINTS
    # ============================================================================

    @router.post("/batch", response_model=NotificationBatchOut)
    async def send_batch_notifications(
        payload: NotificationBatchIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Envoyer des notifications en lot"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in WRITE_ROLES, 403, "Accès réservé")

        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        nombre_envoyes = 0
        nombre_echecs = 0
        echecs = []

        for destinataire in payload.destinataires:
            if payload.canal == "sms":
                result = await send_sms_twilio(destinataire, payload.message)
            elif payload.canal == "whatsapp":
                result = await send_whatsapp(destinataire, payload.message)
            elif payload.canal == "email":
                result = await send_email(destinataire, "Notification", payload.message, payload.message)
            
            if result["success"]:
                nombre_envoyes += 1
            else:
                nombre_echecs += 1
                echecs.append({
                    "destinataire": destinataire,
                    "error": result.get("error")
                })

        # Logger le batch
        batch_doc = {
            "batch_id": batch_id,
            "canal": payload.canal,
            "nombre_destinataires": len(payload.destinataires),
            "nombre_envoyes": nombre_envoyes,
            "nombre_echecs": nombre_echecs,
            "echecs": echecs,
            "priorite": payload.priorite,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["user_id"]
        }
        await db.notification_batches.insert_one(batch_doc)

        logger.info(f"Batch {batch_id} envoyé: {nombre_envoyes}/{len(payload.destinataires)}")

        return NotificationBatchOut(
            batch_id=batch_id,
            canal=payload.canal,
            nombre_envoyes=nombre_envoyes,
            nombre_echecs=nombre_echecs,
            echecs=echecs,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    # ============================================================================
    # LOGS ENDPOINTS
    # ============================================================================

    @router.get("/logs")
    async def list_notification_logs(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        type_: Optional[str] = None,
        limit: int = 50
    ):
        """Lister les logs de notifications"""
        user = await resolve_user(request, authorization)
        _ensure(user["role"] in READ_ROLES, 403, "Accès refusé")

        filters = {}
        if type_:
            filters["type"] = type_

        cursor = db.notification_logs.find(filters, {"_id": 0}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(limit)
        return docs

    # ============================================================================
    # CONFIGURATION CHECK
    # ============================================================================

    @router.get("/config-check")
    async def check_configuration():
        """Vérifier la configuration des APIs"""
        config = {
            "twilio": {
                "configured": all([os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_PHONE_NUMBER")]),
                "missing": []
            },
            "orange_ci": {
                "configured": all([os.getenv("ORANGE_CI_CLIENT_ID"), os.getenv("ORANGE_CI_CLIENT_SECRET"), os.getenv("ORANGE_CI_SENDER")]),
                "missing": []
            },
            "mtn_ci": {
                "configured": all([os.getenv("MTN_CI_API_KEY"), os.getenv("MTN_CI_API_SECRET"), os.getenv("MTN_CI_SENDER_ID")]),
                "missing": []
            },
            "whatsapp": {
                "configured": all([os.getenv("WHATSAPP_API_TOKEN"), os.getenv("WHATSAPP_PHONE_ID")]),
                "missing": []
            },
            "email": {
                "configured": all([os.getenv("SMTP_HOST"), os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"), os.getenv("SMTP_FROM")]),
                "missing": []
            }
        }

        # Identifier les variables manquantes
        if not os.getenv("TWILIO_ACCOUNT_SID"):
            config["twilio"]["missing"].append("TWILIO_ACCOUNT_SID")
        if not os.getenv("TWILIO_AUTH_TOKEN"):
            config["twilio"]["missing"].append("TWILIO_AUTH_TOKEN")
        if not os.getenv("TWILIO_PHONE_NUMBER"):
            config["twilio"]["missing"].append("TWILIO_PHONE_NUMBER")

        if not os.getenv("ORANGE_CI_CLIENT_ID"):
            config["orange_ci"]["missing"].append("ORANGE_CI_CLIENT_ID")
        if not os.getenv("ORANGE_CI_CLIENT_SECRET"):
            config["orange_ci"]["missing"].append("ORANGE_CI_CLIENT_SECRET")
        if not os.getenv("ORANGE_CI_SENDER"):
            config["orange_ci"]["missing"].append("ORANGE_CI_SENDER")

        if not os.getenv("MTN_CI_API_KEY"):
            config["mtn_ci"]["missing"].append("MTN_CI_API_KEY")
        if not os.getenv("MTN_CI_API_SECRET"):
            config["mtn_ci"]["missing"].append("MTN_CI_API_SECRET")
        if not os.getenv("MTN_CI_SENDER_ID"):
            config["mtn_ci"]["missing"].append("MTN_CI_SENDER_ID")

        if not os.getenv("WHATSAPP_API_TOKEN"):
            config["whatsapp"]["missing"].append("WHATSAPP_API_TOKEN")
        if not os.getenv("WHATSAPP_PHONE_ID"):
            config["whatsapp"]["missing"].append("WHATSAPP_PHONE_ID")

        if not os.getenv("SMTP_HOST"):
            config["email"]["missing"].append("SMTP_HOST")
        if not os.getenv("SMTP_USER"):
            config["email"]["missing"].append("SMTP_USER")
        if not os.getenv("SMTP_PASSWORD"):
            config["email"]["missing"].append("SMTP_PASSWORD")
        if not os.getenv("SMTP_FROM"):
            config["email"]["missing"].append("SMTP_FROM")

        return config

    return router
