"""
Output Encoding Service — JSON-safe escaping for all API responses
Prevents XSS attacks in JSON responses and ensures safe serialization
"""

import json
import logging
import html
import re
from typing import Any, Dict, List, Union

logger = logging.getLogger("fabsci.encoding")


class OutputEncodingService:
    """
    Encode API responses to prevent XSS and injection attacks.
    
    Handles:
    - HTML entity escaping (<, >, &, ", ')
    - Unicode escaping (non-ASCII characters)
    - Safe JSON serialization
    - Nested object recursion
    """
    
    # Characters that need escaping in JSON/HTML context
    ESCAPE_MAP = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',  # Forward slash (escapes </script> injection)
    }
    
    # Additional unsafe patterns to detect
    UNSAFE_PATTERNS = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers (onclick=, onerror=, etc)
        r'<iframe',  # Iframes
        r'<object',  # Object tags
        r'<embed',  # Embed tags
    ]
    
    @staticmethod
    def escape_string(value: str, strict: bool = False) -> str:
        """
        HTML-escape a string to prevent XSS.
        
        Args:
            value: String to escape
            strict: If True, also escape forward slashes (more aggressive)
            
        Returns:
            Escaped string safe for JSON/HTML context
        """
        if not isinstance(value, str) or not value:
            return value
        
        # HTML escape common characters
        escaped = html.escape(value, quote=True)
        
        # Additional escaping for JSON context
        if strict:
            escaped = escaped.replace('/', '&#x2F;')
        
        return escaped
    
    @staticmethod
    def detect_suspicious_content(value: str) -> bool:
        """
        Detect potentially malicious patterns in string.
        
        Args:
            value: String to check
            
        Returns:
            True if suspicious content found
        """
        if not isinstance(value, str):
            return False
        
        for pattern in OutputEncodingService.UNSAFE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def encode_value(value: Any, encode_strings: bool = True) -> Any:
        """
        Recursively encode a value (string, list, dict, etc).
        
        Args:
            value: Value to encode
            encode_strings: Whether to encode string values (default True)
            
        Returns:
            Encoded value safe for JSON serialization
        """
        if value is None:
            return None
        
        if isinstance(value, bool):
            # Keep booleans as-is (JSON-safe)
            return value
        
        if isinstance(value, (int, float)):
            # Keep numbers as-is (JSON-safe)
            return value
        
        if isinstance(value, str):
            if encode_strings:
                # Check for suspicious content
                if OutputEncodingService.detect_suspicious_content(value):
                    logger.warning(f"Potentially malicious content detected in output")
                    # Don't process further, return escaped version
                    return OutputEncodingService.escape_string(value, strict=True)
                
                # HTML-escape the string
                return OutputEncodingService.escape_string(value)
            else:
                return value
        
        if isinstance(value, dict):
            # Recursively encode dictionary
            encoded = {}
            for key, val in value.items():
                # Keys should also be strings and potentially unsafe
                safe_key = OutputEncodingService.escape_string(str(key))
                encoded[safe_key] = OutputEncodingService.encode_value(val, encode_strings)
            return encoded
        
        if isinstance(value, (list, tuple)):
            # Recursively encode list
            return [OutputEncodingService.encode_value(item, encode_strings) for item in value]
        
        # For other types (custom objects, etc), convert to string and escape
        return OutputEncodingService.escape_string(str(value))
    
    @staticmethod
    def encode_json_response(data: Any, escape_strings: bool = True) -> str:
        """
        Encode data to JSON-safe string with output encoding.
        
        Args:
            data: Data to encode
            escape_strings: Whether to HTML-escape string values
            
        Returns:
            JSON string with encoded content
        """
        try:
            # First, recursively encode all values
            encoded = OutputEncodingService.encode_value(data, encode_strings=escape_strings)
            
            # Then serialize to JSON
            # Use ensure_ascii=True to escape all non-ASCII (extra safety)
            json_str = json.dumps(
                encoded,
                ensure_ascii=True,
                separators=(',', ':'),  # Compact JSON (no spaces)
                default=str  # Handle non-serializable objects
            )
            
            return json_str
        
        except Exception as e:
            logger.error(f"JSON encoding failed: {e}")
            # Return safe fallback
            return json.dumps({
                "error": "Encoding error",
                "detail": "Unable to encode response"
            })
    
    @staticmethod
    def sanitize_user_input(value: str) -> str:
        """
        Sanitize user input before processing.
        (Different from output encoding — used for input validation)
        
        Args:
            value: User input
            
        Returns:
            Sanitized input
        """
        if not value:
            return value
        
        # Remove null bytes
        value = value.replace('\0', '')
        
        # Remove control characters (except newline, tab)
        value = ''.join(
            char for char in value
            if ord(char) >= 32 or char in '\n\t'
        )
        
        # Trim whitespace
        return value.strip()


# Context-aware encoding strategies
ENCODING_STRATEGIES = {
    "html": lambda x: html.escape(x) if isinstance(x, str) else x,
    "json": lambda x: json.dumps(x, ensure_ascii=True),
    "xml": lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if isinstance(x, str) else x,
    "csv": lambda x: f'"{x}"' if isinstance(x, str) else str(x),
}


def get_encoding_strategy(context: str):
    """Get encoding function for specific context."""
    return ENCODING_STRATEGIES.get(context, lambda x: x)


# Global configuration
ENCODING_CONFIG = {
    "enabled": True,  # Master switch
    "escape_strings": True,  # Escape string values in responses
    "detect_suspicious": True,  # Warn on suspicious patterns
    "ensure_ascii": True,  # Force ASCII-only JSON
}


logger.info("✅ Output Encoding Service initialized")
