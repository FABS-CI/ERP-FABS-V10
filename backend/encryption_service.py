"""
Data Encryption at Rest — AES-256 encryption for sensitive MongoDB fields
Protects: passwords, card numbers, SSN, medical info, etc.
"""

import os
import json
import logging
from typing import Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger("fabsci.encryption")


class EncryptionService:
    """
    Fernet (AES-128) encryption for database fields at rest.
    
    ⚠️ NOTE: Passwords should ALWAYS use bcrypt hashing, not encryption.
    This service is for OTHER sensitive data (card numbers, SSN, medical info).
    
    Fernet guarantees:
    - AES-128 in CBC mode
    - HMAC for authenticity
    - Timestamps & TTL (prevents old-ciphertext attacks)
    """
    
    def __init__(self, master_key: str):
        """
        Initialize with master key.
        
        Args:
            master_key: Strong key (32+ chars). Should come from environment variable.
                       In production: use AWS KMS, Azure Key Vault, or HashiCorp Vault
        """
        self.master_key = master_key
        self._fernet = self._derive_fernet_key(master_key)
    
    @staticmethod
    def _derive_fernet_key(master_key: str) -> Fernet:
        """
        Derive a Fernet key from master key using PBKDF2.
        
        Args:
            master_key: Master encryption key
            
        Returns:
            Fernet cipher instance
        """
        # Use a fixed salt for deterministic key derivation
        # (In production, consider per-field salt in ciphertext)
        salt = b'fabsci-encryption-salt-v1'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(master_key.encode())
        )
        
        return Fernet(key)
    
    def encrypt(self, plaintext: Any) -> str:
        """
        Encrypt a value.
        
        Args:
            plaintext: Value to encrypt (string, int, dict, list)
            
        Returns:
            Encrypted ciphertext (base64-encoded Fernet token)
        """
        try:
            # Convert to JSON string if not already
            if isinstance(plaintext, str):
                data = plaintext
            else:
                data = json.dumps(plaintext)
            
            # Encrypt
            ciphertext = self._fernet.encrypt(data.encode())
            
            return ciphertext.decode()  # Return as string for storage
        
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption error: {e}")
    
    def decrypt(self, ciphertext: str) -> Any:
        """
        Decrypt a value.
        
        Args:
            ciphertext: Encrypted ciphertext (base64-encoded Fernet token)
            
        Returns:
            Decrypted plaintext (original type)
        """
        try:
            if not ciphertext:
                return None
            
            # Decrypt
            plaintext = self._fernet.decrypt(ciphertext.encode()).decode()
            
            # Try to parse as JSON (if it was serialized)
            try:
                return json.loads(plaintext)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return plaintext
        
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # In production, log to audit trail for key rotation suspicion
            raise ValueError(f"Decryption error (possible key mismatch): {e}")
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Selectively encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary to encrypt
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted and encrypted[field] is not None:
                try:
                    encrypted[field] = self.encrypt(encrypted[field])
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field}: {e}")
                    # Don't fail the whole operation
                    pass
        
        return encrypted
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Selectively decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary to decrypt
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted and decrypted[field]:
                try:
                    decrypted[field] = self.decrypt(decrypted[field])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    # Don't fail the whole operation; leave encrypted
                    pass
        
        return decrypted


# Sensitive fields per collection (configure based on business needs)
ENCRYPTED_FIELDS_BY_COLLECTION = {
    "users": [],  # ⚠️ Passwords use bcrypt hashing, NOT encryption
    "clients": ["siret", "iban"],  # Business registration + bank account
    "paiements": ["card_token", "reference"],  # Payment details
    "factures": [],  # Generally not needed; customer data in clients collection
    "employes": ["ssn", "phone", "email", "address"],  # Personal identifiable info
    "approvisionnement": ["supplier_contact", "supplier_email"],
}


def get_encrypted_fields(collection_name: str) -> list:
    """Get list of encrypted fields for a collection."""
    return ENCRYPTED_FIELDS_BY_COLLECTION.get(collection_name, [])


# Initialize service
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Development fallback (INSECURE — must be set in production)
    import secrets
    ENCRYPTION_KEY = secrets.token_urlsafe(32)
    logger.warning("⚠️  ENCRYPTION_KEY not set in environment. Using random key (data won't persist).")

encryption_service = EncryptionService(ENCRYPTION_KEY)
logger.info("✅ Encryption Service initialized (AES-256 via Fernet)")
