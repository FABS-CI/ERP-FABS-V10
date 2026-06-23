"""
Request Signing Service — HMAC-SHA256 signature validation
Prevents request tampering and ensures API integrity
"""

import hmac
import hashlib
import json
import time
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger("fabsci.signing")

class RequestSigningService:
    """
    HMAC-SHA256 based request signing for API integrity.
    
    Client side: Sign request with SECRET_KEY
    Server side: Validate signature with PUBLIC_KEY (derived from SECRET_KEY)
    
    Signature = HMAC-SHA256(method + path + timestamp + body_hash)
    """
    
    def __init__(self, signing_key: str):
        """
        Args:
            signing_key: Base signing key (should be 32+ chars, from environment)
        """
        self.signing_key = signing_key.encode() if isinstance(signing_key, str) else signing_key
    
    @staticmethod
    def hash_body(body: str | bytes | Dict[str, Any] | None) -> str:
        """
        Hash request body (handles JSON, binary, empty).
        
        Args:
            body: Request body (can be JSON dict, string, bytes, or None)
            
        Returns:
            Hex digest of SHA256(body)
        """
        if body is None or body == "":
            body_bytes = b""
        elif isinstance(body, dict):
            body_bytes = json.dumps(body, sort_keys=True).encode()
        elif isinstance(body, str):
            body_bytes = body.encode()
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            body_bytes = str(body).encode()
        
        return hashlib.sha256(body_bytes).hexdigest()
    
    def generate_signature(
        self,
        method: str,
        path: str,
        timestamp: int,
        body_hash: str
    ) -> str:
        """
        Generate HMAC-SHA256 signature for request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /api/clients)
            timestamp: Unix timestamp
            body_hash: SHA256 hash of body
            
        Returns:
            Hex-encoded HMAC signature
        """
        message = f"{method.upper()}|{path}|{timestamp}|{body_hash}"
        signature = hmac.new(
            self.signing_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def validate_signature(
        self,
        method: str,
        path: str,
        timestamp: int,
        body_hash: str,
        provided_signature: str,
        max_age_seconds: int = 300
    ) -> Tuple[bool, str]:
        """
        Validate request signature.
        
        Args:
            method: HTTP method
            path: Request path
            timestamp: Unix timestamp from header
            body_hash: SHA256 hash of body
            provided_signature: Signature from X-Signature header
            max_age_seconds: Max age of request (default 5min)
            
        Returns:
            Tuple (is_valid, reason)
        """
        # 1. Check timestamp freshness (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - timestamp) > max_age_seconds:
            return False, f"Request timestamp too old (diff: {abs(current_time - timestamp)}s > {max_age_seconds}s)"
        
        # 2. Generate expected signature
        expected_signature = self.generate_signature(method, path, timestamp, body_hash)
        
        # 3. Constant-time comparison (prevent timing attacks)
        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        
        if not is_valid:
            logger.warning(
                f"Signature validation failed: {method} {path} | "
                f"Expected: {expected_signature[:16]}... | Got: {provided_signature[:16]}..."
            )
            return False, "Signature mismatch"
        
        return True, "Valid"
    
    @staticmethod
    def derive_public_key(signing_key: str) -> str:
        """
        Derive a public key from signing key (for clients to publish).
        In production, clients would have a separate key pair.
        For now, we use HMAC-SHA256 of the signing key.
        
        Args:
            signing_key: Secret signing key
            
        Returns:
            Public key (can be shared)
        """
        return hashlib.sha256(signing_key.encode()).hexdigest()


# Request signature headers (standard)
SIGNATURE_HEADERS = {
    "X-Timestamp": "Unix timestamp when request was signed",
    "X-Signature": "HMAC-SHA256 signature (hex)",
    "X-Client-Id": "Optional: Client identifier for audit"
}

# Request signing enabled endpoints (whitelist)
# GET requests are read-only, so we primarily sign mutation endpoints
SIGNING_REQUIRED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
SIGNING_EXEMPT_PATHS = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/docs",
    "/openapi.json",
    "/static",
}
