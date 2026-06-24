"""
TOUR 3: Error Handlers & Exception Management
- Custom exception classes
- Structured error responses
- Graceful degradation
- Retry logic with exponential backoff
"""

import time
import logging
import json
from typing import Any, Dict, Optional, Callable, Type
from functools import wraps
from enum import Enum
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseERPError(Exception):
    """Base exception for all ERP errors"""
    
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", 
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 http_status: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.code = code
        self.severity = severity
        self.http_status = http_status
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to structured format"""
        return {
            "error": {
                "message": self.message,
                "code": self.code,
                "severity": self.severity.value,
                "http_status": self.http_status,
                "timestamp": self.timestamp,
                "details": self.details
            }
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON"""
        return json.dumps(self.to_dict())


class ValidationError(BaseERPError):
    """Validation error (invalid input)"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        if field:
            message = f"Validation error in field '{field}': {message}"
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            severity=ErrorSeverity.WARNING,
            http_status=400,
            details=details or {}
        )


class AuthenticationError(BaseERPError):
    """Authentication error (invalid credentials)"""
    
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            severity=ErrorSeverity.WARNING,
            http_status=401,
            details=details or {}
        )


class AuthorizationError(BaseERPError):
    """Authorization error (insufficient permissions)"""
    
    def __init__(self, message: str = "Insufficient permissions", 
                 required_role: str = None, details: Dict[str, Any] = None):
        detail = details or {}
        if required_role:
            detail["required_role"] = required_role
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            severity=ErrorSeverity.WARNING,
            http_status=403,
            details=detail
        )


class NotFoundError(BaseERPError):
    """Resource not found"""
    
    def __init__(self, resource_type: str, resource_id: Any = None, 
                 details: Dict[str, Any] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            severity=ErrorSeverity.WARNING,
            http_status=404,
            details=details or {"resource_type": resource_type, "resource_id": resource_id}
        )


class ConflictError(BaseERPError):
    """Resource conflict (duplicate, constraint violation)"""
    
    def __init__(self, message: str, resource_type: str = None, 
                 details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            severity=ErrorSeverity.WARNING,
            http_status=409,
            details=details or {"resource_type": resource_type}
        )


class DatabaseError(BaseERPError):
    """Database operation error"""
    
    def __init__(self, message: str, operation: str = None, 
                 collection: str = None, details: Dict[str, Any] = None):
        detail = details or {}
        if operation:
            detail["operation"] = operation
        if collection:
            detail["collection"] = collection
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            severity=ErrorSeverity.ERROR,
            http_status=500,
            details=detail
        )


class ExternalServiceError(BaseERPError):
    """External service unavailable or error"""
    
    def __init__(self, service_name: str, message: str = None, 
                 status_code: int = None, details: Dict[str, Any] = None):
        msg = message or f"External service '{service_name}' is unavailable"
        detail = details or {}
        detail["service_name"] = service_name
        if status_code:
            detail["service_status_code"] = status_code
        super().__init__(
            message=msg,
            code="EXTERNAL_SERVICE_ERROR",
            severity=ErrorSeverity.ERROR,
            http_status=502,
            details=detail
        )


class RateLimitError(BaseERPError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", 
                 retry_after_seconds: int = None, details: Dict[str, Any] = None):
        detail = details or {}
        if retry_after_seconds:
            detail["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            severity=ErrorSeverity.WARNING,
            http_status=429,
            details=detail
        )


class TimeoutError(BaseERPError):
    """Operation timeout"""
    
    def __init__(self, operation: str = None, timeout_seconds: float = None, 
                 details: Dict[str, Any] = None):
        message = f"Operation timeout"
        if operation:
            message += f" ({operation})"
        detail = details or {}
        if timeout_seconds:
            detail["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            code="TIMEOUT",
            severity=ErrorSeverity.ERROR,
            http_status=504,
            details=detail
        )


class BusinessLogicError(BaseERPError):
    """Business rule violation"""
    
    def __init__(self, message: str, rule: str = None, details: Dict[str, Any] = None):
        detail = details or {}
        if rule:
            detail["rule"] = rule
        super().__init__(
            message=message,
            code="BUSINESS_LOGIC_ERROR",
            severity=ErrorSeverity.WARNING,
            http_status=422,
            details=detail
        )


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(self, max_attempts: int = 3, base_delay_ms: int = 100, 
                 max_delay_ms: int = 10000, exponential_base: float = 2.0,
                 retryable_exceptions: tuple = None, backoff_jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or (
            DatabaseError, ExternalServiceError, TimeoutError
        )
        self.backoff_jitter = backoff_jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt (exponential backoff with optional jitter)"""
        # Exponential backoff: delay = base_delay * exponential_base^attempt
        delay_ms = self.base_delay_ms * (self.exponential_base ** attempt)
        delay_ms = min(delay_ms, self.max_delay_ms)
        
        # Add jitter if enabled
        if self.backoff_jitter:
            import random
            jitter = random.uniform(0, delay_ms * 0.1)
            delay_ms += jitter
        
        return delay_ms / 1000.0  # Convert to seconds


class RetryableDecorator:
    """Decorator for retryable functions with exponential backoff"""
    
    def __init__(self, config: RetryConfig = None, logger: logging.Logger = None):
        self.config = config or RetryConfig()
        self.logger = logger or logging.getLogger("retry")
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(self.config.max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except self.config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < self.config.max_attempts - 1:
                        delay = self.config.calculate_delay(attempt)
                        self.logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        self.logger.error(
                            f"All {self.config.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
                
                except Exception as e:
                    # Non-retryable exception
                    raise
            
            # If we get here, all retries failed
            if last_exception:
                raise last_exception
        
        return wrapper


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: int = 60,
                 logger: logging.Logger = None):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.logger = logger or logging.getLogger("circuit_breaker")
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if we should attempt recovery
        if self.state == "open":
            if self._should_attempt_recovery():
                self.state = "half_open"
                self.logger.info("Circuit breaker entering half_open state")
            else:
                raise ExternalServiceError(
                    func.__name__,
                    "Circuit breaker is open - service temporarily unavailable"
                )
        
        try:
            result = func(*args, **kwargs)
            
            # Success
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                self.logger.info("Circuit breaker closed - service recovered")
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                self.logger.error(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )
            
            raise
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class GracefulDegradation:
    """Handle graceful degradation when services fail"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("degradation")
        self.degraded_services: Dict[str, Dict] = {}
    
    def mark_degraded(self, service_name: str, reason: str, fallback_data: Any = None):
        """Mark a service as degraded"""
        self.degraded_services[service_name] = {
            "degraded_at": datetime.now().isoformat(),
            "reason": reason,
            "fallback_data": fallback_data
        }
        self.logger.warning(f"Service '{service_name}' marked as degraded: {reason}")
    
    def is_degraded(self, service_name: str) -> bool:
        """Check if service is degraded"""
        return service_name in self.degraded_services
    
    def get_fallback(self, service_name: str) -> Any:
        """Get fallback data for degraded service"""
        if service_name in self.degraded_services:
            return self.degraded_services[service_name].get("fallback_data")
        return None
    
    def mark_recovered(self, service_name: str):
        """Mark service as recovered"""
        if service_name in self.degraded_services:
            del self.degraded_services[service_name]
            self.logger.info(f"Service '{service_name}' marked as recovered")
    
    def get_status(self) -> Dict[str, Any]:
        """Get degradation status"""
        return {
            "degraded_services": len(self.degraded_services),
            "services": self.degraded_services
        }


class ErrorLogger:
    """Centralized error logging with context"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("errors")
    
    def log_error(self, exception: Exception, context: Dict[str, Any] = None,
                 user_id: str = None, endpoint: str = None):
        """Log error with full context"""
        
        if isinstance(exception, BaseERPError):
            error_dict = exception.to_dict()
        else:
            error_dict = {
                "error": {
                    "message": str(exception),
                    "code": "INTERNAL_ERROR",
                    "type": type(exception).__name__,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Add context
        if context:
            error_dict["context"] = context
        if user_id:
            error_dict["user_id"] = user_id
        if endpoint:
            error_dict["endpoint"] = endpoint
        
        self.logger.error(json.dumps(error_dict))
    
    def log_unhandled_exception(self, exc_type: Type, exc_value: Exception, traceback):
        """Log unhandled exception with traceback"""
        import traceback as tb
        self.logger.critical(json.dumps({
            "error": {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": tb.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
        }))


# Global instances
retry_decorator = None
circuit_breaker = None
graceful_degradation = None
error_logger = None


def initialize_error_handlers(logger: logging.Logger = None, retry_config: RetryConfig = None) -> Dict[str, Any]:
    """Initialize all error handling components"""
    global retry_decorator, circuit_breaker, graceful_degradation, error_logger
    
    retry_decorator = RetryableDecorator(retry_config or RetryConfig(), logger)
    circuit_breaker = CircuitBreaker(logger=logger)
    graceful_degradation = GracefulDegradation(logger)
    error_logger = ErrorLogger(logger)
    
    return {
        "retry_decorator": retry_decorator,
        "circuit_breaker": circuit_breaker,
        "graceful_degradation": graceful_degradation,
        "error_logger": error_logger
    }


def get_error_handlers() -> Dict[str, Any]:
    """Get initialized error handling components"""
    return {
        "retry_decorator": retry_decorator,
        "circuit_breaker": circuit_breaker,
        "graceful_degradation": graceful_degradation,
        "error_logger": error_logger
    }
