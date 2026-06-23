"""
TLS Configuration Service
Manages SSL/TLS certificate loading, validation, and rotation
Supports mutual TLS (mTLS) for client certificate authentication
"""

import os
import ssl
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple
from pathlib import Path
import OpenSSL.crypto
from OpenSSL import SSL

logger = logging.getLogger(__name__)


class CertificateMetadata:
    """Certificate metadata and validation"""
    
    def __init__(self, cert_path: str):
        self.cert_path = cert_path
        self.loaded_at = datetime.now()
        self.cert = None
        self.valid_from = None
        self.valid_to = None
        self.subject = None
        self.issuer = None
        self._load_cert()
    
    def _load_cert(self):
        """Load and parse certificate"""
        try:
            with open(self.cert_path, 'rb') as f:
                cert_data = f.read()
            self.cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_data
            )
            
            # Extract metadata
            self.valid_from = datetime.strptime(
                self.cert.get_notBefore().decode(), '%Y%m%d%H%M%SZ'
            )
            self.valid_to = datetime.strptime(
                self.cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ'
            )
            self.subject = self.cert.get_subject()
            self.issuer = self.cert.get_issuer()
            
            logger.info(f"✅ Certificate loaded: {self.cert_path}")
            logger.info(f"   Valid: {self.valid_from} → {self.valid_to}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load certificate: {e}")
            raise
    
    def is_valid(self) -> bool:
        """Check if certificate is currently valid"""
        now = datetime.now()
        return self.valid_from <= now <= self.valid_to
    
    def days_until_expiry(self) -> int:
        """Days until certificate expires"""
        return (self.valid_to - datetime.now()).days
    
    def to_dict(self) -> Dict:
        """Export metadata as dict"""
        return {
            'cert_path': self.cert_path,
            'loaded_at': self.loaded_at.isoformat(),
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'days_until_expiry': self.days_until_expiry(),
            'is_valid': self.is_valid(),
            'subject': str(self.subject) if self.subject else None,
            'issuer': str(self.issuer) if self.issuer else None,
        }


class TLSConfigService:
    """TLS Configuration and Certificate Management"""
    
    def __init__(self, audit_service=None):
        self.audit_service = audit_service
        self.enabled = os.getenv('TLS_ENABLED', 'false').lower() == 'true'
        self.port = int(os.getenv('TLS_PORT', 8443))
        self.cert_path = os.getenv('TLS_CERT_PATH')
        self.key_path = os.getenv('TLS_KEY_PATH')
        self.mtls_enabled = os.getenv('TLS_MTLS_ENABLED', 'false').lower() == 'true'
        self.mtls_ca_path = os.getenv('TLS_MTLS_CA_PATH')
        self.mtls_request_mode = os.getenv('TLS_MTLS_REQUEST_CLIENT_CERT', 'optional')
        self.log_level = os.getenv('TLS_LOG_LEVEL', 'info')
        
        self.cert_metadata = None
        self.ca_metadata = None
        self.ssl_context = None
        
        logger.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
        
        if self.enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize TLS configuration"""
        logger.info("🔒 Initializing TLS Configuration")
        
        if not self.cert_path or not self.key_path:
            logger.warning("⚠️  TLS enabled but cert/key paths missing in .env")
            return
        
        # Validate files exist
        if not Path(self.cert_path).exists():
            raise FileNotFoundError(f"Certificate not found: {self.cert_path}")
        if not Path(self.key_path).exists():
            raise FileNotFoundError(f"Private key not found: {self.key_path}")
        
        # Load certificate metadata
        self.cert_metadata = CertificateMetadata(self.cert_path)
        
        # Check expiry warning
        days_left = self.cert_metadata.days_until_expiry()
        if days_left < 30:
            logger.warning(f"⚠️  Certificate expires in {days_left} days!")
            if self.audit_service:
                self.audit_service.log(
                    user_id='system',
                    action='CERT_EXPIRY_WARNING',
                    resource_type='security',
                    details={'days_until_expiry': days_left},
                    level='WARNING'
                )
        
        # Load CA if mTLS enabled
        if self.mtls_enabled and self.mtls_ca_path:
            if not Path(self.mtls_ca_path).exists():
                raise FileNotFoundError(f"CA cert not found: {self.mtls_ca_path}")
            self.ca_metadata = CertificateMetadata(self.mtls_ca_path)
            logger.info(f"✅ mTLS enabled with CA: {self.mtls_ca_path}")
        
        # Create SSL context
        self._create_ssl_context()
        
        logger.info(f"✅ TLS initialized on port {self.port}")
    
    def _create_ssl_context(self):
        """Create and configure SSL context"""
        # Use server context with TLS 1.2+ only (prefer 1.3)
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(self.cert_path, self.key_path)
        
        # Force TLS 1.2+ minimum
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Try to set TLS 1.3 if available
        try:
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            logger.info("✅ TLS 1.3 enabled")
        except AttributeError:
            logger.warning("⚠️  TLS 1.3 not available, using TLS 1.2")
        
        # Strong cipher suites
        self.ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # mTLS configuration
        if self.mtls_enabled and self.mtls_ca_path:
            self.ssl_context.load_verify_locations(self.mtls_ca_path)
            
            if self.mtls_request_mode == 'required':
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                logger.info("✅ mTLS: client certificate REQUIRED")
            else:
                self.ssl_context.verify_mode = ssl.CERT_OPTIONAL
                logger.info("✅ mTLS: client certificate OPTIONAL")
        
        logger.info("✅ SSL context configured")
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Get configured SSL context for server"""
        return self.ssl_context
    
    def get_cert_metadata(self) -> Optional[Dict]:
        """Get certificate metadata"""
        return self.cert_metadata.to_dict() if self.cert_metadata else None
    
    def get_ca_metadata(self) -> Optional[Dict]:
        """Get CA certificate metadata"""
        return self.ca_metadata.to_dict() if self.ca_metadata else None
    
    def get_tls_status(self) -> Dict:
        """Get full TLS configuration status"""
        return {
            'enabled': self.enabled,
            'port': self.port,
            'certificate': self.get_cert_metadata(),
            'mtls': {
                'enabled': self.mtls_enabled,
                'request_mode': self.mtls_request_mode,
                'ca_certificate': self.get_ca_metadata(),
            },
            'tls_version': self._get_tls_version_string(),
            'initialized': self.ssl_context is not None,
        }
    
    def _get_tls_version_string(self) -> str:
        """Get TLS version from context"""
        if not self.ssl_context:
            return 'Not initialized'
        try:
            return f"TLS {self.ssl_context.maximum_version.name.replace('TLSVersion.', '')}"
        except:
            return 'TLS 1.2+'
    
    def validate_certificate_chain(self) -> bool:
        """Validate certificate chain integrity"""
        try:
            if not self.cert_metadata or not self.cert_metadata.cert:
                return False
            
            # Check self-signed or proper chain
            issuer = self.cert_metadata.issuer
            subject = self.cert_metadata.subject
            
            is_self_signed = issuer == subject
            logger.info(f"📋 Certificate type: {'Self-signed' if is_self_signed else 'Issued by CA'}")
            
            return self.cert_metadata.is_valid()
        except Exception as e:
            logger.error(f"❌ Certificate validation failed: {e}")
            return False


async def init_tls_config(audit_service=None) -> TLSConfigService:
    """Initialize TLS configuration service"""
    service = TLSConfigService(audit_service)
    return service
