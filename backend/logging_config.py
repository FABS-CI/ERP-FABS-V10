"""
TOUR 3: Logging Configuration
- Structured JSON logging
- Sentry integration (template)
- Log levels and formatters
- Environment-based configuration
"""

import logging
import logging.handlers
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import os


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'levelno', 'lineno', 'module', 'msecs',
                              'message', 'pathname', 'process', 'processName',
                              'relativeCreated', 'thread', 'threadName', 'exc_info',
                              'exc_text', 'stack_info', 'getMessage'):
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """Filter that adds context information to logs"""
    
    def __init__(self, context: Dict[str, Any] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to the log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class LoggerConfig:
    """Centralized logging configuration"""
    
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    def __init__(self, app_name: str = "ERP-FABS", environment: str = None):
        self.app_name = app_name
        self.environment = environment or os.getenv("ENV", "development")
        self.loggers: Dict[str, logging.Logger] = {}
        self.context_filter = ContextFilter()
    
    def get_log_level(self) -> int:
        """Get log level based on environment"""
        if self.environment == "production":
            return logging.INFO
        elif self.environment == "staging":
            return logging.DEBUG
        else:
            return logging.DEBUG
    
    def setup_console_handler(self, logger: logging.Logger, level: int = None):
        """Setup console (stdout) handler"""
        if level is None:
            level = self.get_log_level()
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        if self.environment == "production":
            formatter = JSONFormatter()
        else:
            # Pretty format for development
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        handler.addFilter(self.context_filter)
        logger.addHandler(handler)
        
        return handler
    
    def setup_file_handler(self, logger: logging.Logger, filename: str, level: int = None):
        """Setup file handler with rotation"""
        if level is None:
            level = self.get_log_level()
        
        # Create rotating file handler (max 10MB per file, keep 5 backups)
        handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        handler.setLevel(level)
        
        # Always use JSON format for files
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        handler.addFilter(self.context_filter)
        logger.addHandler(handler)
        
        return handler
    
    def setup_syslog_handler(self, logger: logging.Logger, address: str = '/dev/log',
                            facility: int = logging.handlers.SysLogHandler.LOG_LOCAL0,
                            level: int = None):
        """Setup syslog handler"""
        if level is None:
            level = self.get_log_level()
        
        try:
            handler = logging.handlers.SysLogHandler(address=address, facility=facility)
            handler.setLevel(level)
            
            formatter = logging.Formatter(
                f'{self.app_name}[%(process)d]: %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            handler.addFilter(self.context_filter)
            logger.addHandler(handler)
            
            return handler
        except Exception as e:
            print(f"Warning: Could not setup syslog handler: {e}")
            return None
    
    def get_logger(self, name: str, level: int = None) -> logging.Logger:
        """Get or create a logger with the given name"""
        if name in self.loggers:
            return self.loggers[name]
        
        if level is None:
            level = self.get_log_level()
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        
        # Add console handler
        self.setup_console_handler(logger, level)
        
        self.loggers[name] = logger
        return logger
    
    def get_app_logger(self) -> logging.Logger:
        """Get application logger"""
        return self.get_logger(f"{self.app_name}.app")
    
    def get_request_logger(self) -> logging.Logger:
        """Get request logger"""
        return self.get_logger(f"{self.app_name}.request")
    
    def get_database_logger(self) -> logging.Logger:
        """Get database logger"""
        return self.get_logger(f"{self.app_name}.database")
    
    def get_security_logger(self) -> logging.Logger:
        """Get security logger"""
        return self.get_logger(f"{self.app_name}.security")
    
    def get_error_logger(self) -> logging.Logger:
        """Get error logger"""
        return self.get_logger(f"{self.app_name}.error")
    
    def set_context(self, context: Dict[str, Any]):
        """Set context that will be added to all log records"""
        self.context_filter = ContextFilter(context)
        for logger in self.loggers.values():
            logger.filters.clear()
            for handler in logger.handlers:
                handler.addFilter(self.context_filter)
    
    def add_context(self, key: str, value: Any):
        """Add a single context item"""
        current = self.context_filter.context or {}
        current[key] = value
        self.set_context(current)


class SentryConfig:
    """Sentry error tracking configuration template"""
    
    def __init__(self, dsn: str = None, environment: str = None, 
                 version: str = None, debug: bool = False):
        self.dsn = dsn
        self.environment = environment or os.getenv("ENV", "development")
        self.version = version or "1.0.0"
        self.debug = debug
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get Sentry config as dictionary (for use with sentry-sdk)"""
        return {
            "dsn": self.dsn,
            "environment": self.environment,
            "release": self.version,
            "debug": self.debug,
            "traces_sample_rate": 0.1 if self.environment == "production" else 1.0,
            "profiles_sample_rate": 0.1 if self.environment == "production" else 1.0,
        }
    
    def initialize(self):
        """Initialize Sentry (requires sentry-sdk)"""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
            
            sentry_sdk.init(**self.get_config_dict())
            print(f"✓ Sentry initialized for {self.environment}")
            return True
        except ImportError:
            print("⚠ sentry-sdk not installed. Install with: pip install sentry-sdk")
            return False
        except Exception as e:
            print(f"✗ Failed to initialize Sentry: {e}")
            return False


class LoggingMiddleware:
    """ASGI middleware for request/response logging"""
    
    def __init__(self, app, logger: logging.Logger = None):
        self.app = app
        self.logger = logger or logging.getLogger("request")
    
    async def __call__(self, scope, receive, send):
        """Log HTTP requests and responses"""
        import time
        
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        client_addr = scope.get("client", ("unknown", 0))[0]
        
        # Store response status
        response_status = None
        
        async def send_with_logging(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_with_logging)
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info("HTTP request completed", extra={
                "method": method,
                "path": path,
                "status_code": response_status or 500,
                "duration_ms": duration_ms,
                "client_ip": client_addr
            })


class StructuredLogger:
    """Helper class for logging structured data"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log(self, level: int, message: str, **kwargs):
        """Log with additional structured data"""
        self.logger.log(level, message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level"""
        self.log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info level"""
        self.log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level"""
        self.log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level"""
        self.log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical level"""
        self.log(logging.CRITICAL, message, **kwargs)


# Global configuration instance
_logger_config: Optional[LoggerConfig] = None


def initialize_logging(app_name: str = "ERP-FABS", environment: str = None,
                      sentry_dsn: str = None, log_file: str = None) -> LoggerConfig:
    """Initialize logging system"""
    global _logger_config
    
    _logger_config = LoggerConfig(app_name, environment)
    
    # Setup loggers
    app_logger = _logger_config.get_app_logger()
    request_logger = _logger_config.get_request_logger()
    db_logger = _logger_config.get_database_logger()
    security_logger = _logger_config.get_security_logger()
    error_logger = _logger_config.get_error_logger()
    
    # Setup file handlers if requested
    if log_file:
        _logger_config.setup_file_handler(app_logger, f"{log_file}.app.log")
        _logger_config.setup_file_handler(request_logger, f"{log_file}.request.log")
        _logger_config.setup_file_handler(error_logger, f"{log_file}.error.log")
    
    # Setup Sentry if DSN provided
    if sentry_dsn:
        sentry_config = SentryConfig(dsn=sentry_dsn, environment=environment)
        sentry_config.initialize()
    
    return _logger_config


def get_logger_config() -> Optional[LoggerConfig]:
    """Get initialized logger config"""
    return _logger_config


def create_structured_logger(name: str) -> StructuredLogger:
    """Create a structured logger instance"""
    logger = logging.getLogger(name)
    return StructuredLogger(logger)
