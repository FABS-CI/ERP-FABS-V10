"""
Module 2FA TOTP — ERP FABS-CI V10
Authentification à deux facteurs pour super_admin
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional
import pyotp
import qrcode
import qrcode.image.svg
import base64
import io
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("fabsci.2fa")

# Rôles obligés d'activer le 2FA
# E5 fix: étendre 2FA obligatoire aux rôles avec accès données financières sensibles
ROLES_2FA_REQUIRED = {"directeur_general", "comptable", "directeur_commercial"}

# ============================================================================
# SCHEMAS
# ============================================================================

class TwoFASetupOut(BaseModel):
    secret: str
    qr_code_base64: str
    otpauth_url: str
    message: str

class TwoFAVerifyIn(BaseModel):
    code: str

class TwoFAVerifyOut(BaseModel):
    valid: bool
    message: str
    access_token: Optional[str] = None   # Présent si verify post-login
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

class TwoFAStatusOut(BaseModel):
    enabled: bool
    required: bool
    role: str

# ============================================================================
# ROUTER
# ============================================================================

def build_twofa_router(db, resolve_user, log_audit_event, create_jwt_token=None, create_refresh_token=None, JWT_ACCESS_TOKEN_EXPIRY_MINUTES=30, JWT_REFRESH_TOKEN_EXPIRY_DAYS=7):
    router = APIRouter(prefix="/auth/2fa", tags=["2FA"])

    @router.get("/status", response_model=TwoFAStatusOut)
    async def get_2fa_status(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """Retourne le statut 2FA de l'utilisateur connecté"""
        user = await resolve_user(request, authorization)
        db_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        return TwoFAStatusOut(
            enabled=db_user.get("twofa_enabled", False),
            required=user["role"] in ROLES_2FA_REQUIRED,
            role=user["role"]
        )

    @router.post("/setup", response_model=TwoFASetupOut)
    async def setup_2fa(
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Génère un secret TOTP et retourne le QR code.
        À appeler avant d'activer le 2FA.
        """
        user = await resolve_user(request, authorization)
        db_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        if db_user.get("twofa_enabled"):
            raise HTTPException(status_code=400, detail="Le 2FA est déjà activé. Désactivez-le d'abord.")

        # Générer secret TOTP
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        otpauth_url = totp.provisioning_uri(
            name=user["email"],
            issuer_name="ERP FABS-CI"
        )

        # Générer QR code en base64
        qr = qrcode.make(otpauth_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        qr_b64 = base64.b64encode(buffer.read()).decode("utf-8")

        # Sauvegarder le secret temporaire (pas encore activé)
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {
                "twofa_secret_pending": secret,
                "twofa_setup_at": datetime.now(timezone.utc).isoformat()
            }}
        )

        await log_audit_event(
            user_id=user["user_id"],
            action="2FA_SETUP_INITIATED",
            resource_type="auth",
            details={"email": user["email"]},
            ip_address=request.client.host if request.client else None
        )

        return TwoFASetupOut(
            secret=secret,
            qr_code_base64=qr_b64,
            otpauth_url=otpauth_url,
            message="Scannez le QR code avec votre application (Google Authenticator, Authy). Puis vérifiez avec /2fa/activate."
        )

    @router.post("/activate", response_model=TwoFAVerifyOut)
    async def activate_2fa(
        body: TwoFAVerifyIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Vérifie le code TOTP et active le 2FA si valide.
        """
        user = await resolve_user(request, authorization)
        db_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        secret = db_user.get("twofa_secret_pending")
        if not secret:
            raise HTTPException(status_code=400, detail="Aucun setup 2FA en cours. Appelez /2fa/setup d'abord.")

        totp = pyotp.TOTP(secret)
        if not totp.verify(body.code, valid_window=1):
            raise HTTPException(status_code=400, detail="Code invalide. Vérifiez l'heure de votre appareil.")

        # Activer le 2FA
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {
                "twofa_enabled": True,
                "twofa_secret": secret,
                "twofa_activated_at": datetime.now(timezone.utc).isoformat()
            }, "$unset": {"twofa_secret_pending": ""}}
        )

        await log_audit_event(
            user_id=user["user_id"],
            action="2FA_ACTIVATED",
            resource_type="auth",
            details={"email": user["email"]},
            ip_address=request.client.host if request.client else None
        )

        return TwoFAVerifyOut(valid=True, message="2FA activé avec succès.")

    @router.post("/verify", response_model=TwoFAVerifyOut)
    async def verify_2fa(
        body: TwoFAVerifyIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Vérifie un code TOTP.
        - Si le token est pré-auth (scope=2fa_pending) → échange contre un vrai JWT + refresh
        - Sinon → simple vérification (déjà loggué)
        """
        user = await resolve_user(request, authorization)
        db_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        if not db_user.get("twofa_enabled"):
            raise HTTPException(status_code=400, detail="2FA non activé sur ce compte.")

        secret = db_user.get("twofa_secret")
        if not secret:
            raise HTTPException(status_code=500, detail="Secret 2FA manquant.")

        totp = pyotp.TOTP(secret)
        valid = totp.verify(body.code, valid_window=1)

        if not valid:
            await log_audit_event(
                user_id=user["user_id"],
                action="2FA_FAILED",
                resource_type="auth",
                details={"email": user["email"]},
                ip_address=request.client.host if request.client else None
            )
            raise HTTPException(status_code=401, detail="Code 2FA invalide.")

        await log_audit_event(
            user_id=user["user_id"],
            action="2FA_VERIFIED",
            resource_type="auth",
            details={"email": user["email"]},
            ip_address=request.client.host if request.client else None
        )

        # ── Si token pré-auth → émettre les vrais tokens ──────────────────
        is_preauth = user.get("scope") == "2fa_pending"
        if is_preauth and create_jwt_token and create_refresh_token:
            access_token = create_jwt_token(user["user_id"], user["email"], user["role"])
            refresh_token = create_refresh_token(user["user_id"])
            # Stocker le refresh token
            refresh_doc = {
                "refresh_token": refresh_token,
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRY_DAYS)).isoformat(),
                "revoked": False
            }
            await db.refresh_tokens.insert_one(refresh_doc)
            return TwoFAVerifyOut(
                valid=True,
                message="2FA validé. Connexion autorisée.",
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=JWT_ACCESS_TOKEN_EXPIRY_MINUTES * 60
            )
        # ──────────────────────────────────────────────────────────────────

        return TwoFAVerifyOut(valid=True, message="Code 2FA valide.")

    @router.post("/disable", response_model=TwoFAVerifyOut)
    async def disable_2fa(
        body: TwoFAVerifyIn,
        request: Request,
        authorization: Optional[str] = Header(default=None)
    ):
        """
        Désactive le 2FA (nécessite un code valide pour confirmer).
        Refusé pour super_admin (2FA obligatoire).
        """
        user = await resolve_user(request, authorization)

        if user["role"] in ROLES_2FA_REQUIRED:
            raise HTTPException(
                status_code=403,
                detail="Le 2FA est obligatoire pour votre rôle et ne peut pas être désactivé."
            )

        db_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        if not db_user.get("twofa_enabled"):
            raise HTTPException(status_code=400, detail="2FA déjà désactivé.")

        secret = db_user.get("twofa_secret")
        totp = pyotp.TOTP(secret)
        if not totp.verify(body.code, valid_window=1):
            raise HTTPException(status_code=400, detail="Code invalide. Désactivation refusée.")

        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"twofa_enabled": False},
             "$unset": {"twofa_secret": "", "twofa_activated_at": ""}}
        )

        await log_audit_event(
            user_id=user["user_id"],
            action="2FA_DISABLED",
            resource_type="auth",
            details={"email": user["email"]},
            ip_address=request.client.host if request.client else None
        )

        return TwoFAVerifyOut(valid=True, message="2FA désactivé.")

    return router
