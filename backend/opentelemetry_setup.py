"""
TOUR 4: OpenTelemetry Setup - Distributed Tracing & Log Correlation
=====================================================================
Purpose: Initialize OpenTelemetry SDK with Jaeger exporter for distributed tracing
- Trace context propagation (W3C TraceContext)
- Span creation and correlation
- Log correlation with trace IDs
- Performance monitoring at distributed level

Architecture:
- TracerProvider: Creates tracer instances
- Jaeger Exporter: Sends spans to Jaeger (or stdout in dev)
- Log Processor: Enriches logs with trace context
- Resource: Service identification metadata

Production: Sends to Jaeger backend
Development: Prints traces to console
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps

# OpenTelemetry imports
from opentelemetry import trace, metrics
try:
    from opentelemetry import logs
except ImportError:
    logs = None  # Not available in this version

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Optional Jaeger exporter (version compatibility issue)
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False
    JaegerExporter = None

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.propagate import set_global_textmap

# Optional instrumentations
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentation
except ImportError:
    FastAPIInstrumentation = None

try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentation
except ImportError:
    RequestsInstrumentation = None

try:
    from opentelemetry.instrumentation.pymongo import PyMongoInstrumentation
except ImportError:
    PyMongoInstrumentation = None

try:
    from opentelemetry.instrumentation.redis import RedisInstrumentation
except ImportError:
    RedisInstrumentation = None

# Optional Jaeger propagator
try:
    from opentelemetry.propagators.jaeger.jaeger import JaegerPropagator
except ImportError:
    JaegerPropagator = None

# Optional propagators
try:
    from opentelemetry.propagators.w3c_trace_context import W3CTraceContextPropagator
except ImportError:
    W3CTraceContextPropagator = None

try:
    from opentelemetry.propagators.composite import CompositePropagator
except ImportError:
    CompositePropagator = None


class OpenTelemetrySetup:
    """
    Centralized OpenTelemetry configuration for TOUR 4
    
    Handles:
    - Distributed tracing initialization
    - Span processor setup
    - Log correlation
    - Instrumentation of common libraries
    """

    def __init__(
        self,
        service_name: str = "ERP-FABS-CI",
        service_version: str = "10.1.0",
        environment: str = "production",
        jaeger_host: Optional[str] = None,
        jaeger_port: int = 6831,
        enable_console_export: bool = False
    ):
        """
        Initialize OpenTelemetry setup
        
        Args:
            service_name: Service identifier for traces
            service_version: Service version for metadata
            environment: Environment (production, staging, development)
            jaeger_host: Jaeger agent host (None = localhost)
            jaeger_port: Jaeger agent port
            enable_console_export: Export to console for dev/debug
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.jaeger_host = jaeger_host or os.getenv("JAEGER_HOST", "localhost")
        self.jaeger_port = jaeger_port
        self.enable_console_export = enable_console_export
        
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.meter_provider: Optional[MeterProvider] = None
        self.trace_context_stack: Dict[str, Any] = {}

    def setup(self) -> None:
        """Initialize TracerProvider, exporter, and propagators"""
        
        # 1. Create resource for service identification
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "service.namespace": "FABS",
            "host.name": os.getenv("HOSTNAME", "unknown"),
        })

        # 3. Create TracerProvider with optional Jaeger exporter
        self.tracer_provider = TracerProvider(resource=resource)
        
        # 2. Setup Jaeger exporter if available
        if JAEGER_AVAILABLE and JaegerExporter:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=self.jaeger_host,
                    agent_port=self.jaeger_port,
                )
                self.tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
            except Exception as e:
                logging.warning(f"Jaeger exporter unavailable: {e}")

        # 4. Console exporter for development
        if self.enable_console_export:
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            self.tracer_provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )

        # 5. Set global TracerProvider
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer = trace.get_tracer(__name__)

        # 6. Setup propagators (W3C + optional Jaeger)
        if CompositePropagator and W3CTraceContextPropagator:
            try:
                propagators = [W3CTraceContextPropagator()]
                if JaegerPropagator:
                    try:
                        propagators.append(JaegerPropagator())
                    except Exception:
                        pass
                
                propagator = CompositePropagator(propagators)
                set_global_textmap(propagator)
            except Exception as e:
                logging.warning(f"Could not setup propagators: {e}")
        else:
            logging.warning("CompositePropagator or W3CTraceContextPropagator not available")

        logging.info(
            f"OpenTelemetry initialized: {self.service_name} "
            f"v{self.service_version} in {self.environment}"
        )

    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI app for automatic span creation"""
        if FastAPIInstrumentation:
            try:
                FastAPIInstrumentation.instrument_app(app)
                logging.info("FastAPI instrumented for distributed tracing")
            except Exception as e:
                logging.warning(f"Failed to instrument FastAPI: {e}")
        else:
            logging.warning("FastAPIInstrumentation not available")

    def instrument_requests(self) -> None:
        """Instrument requests library for outbound HTTP calls"""
        if RequestsInstrumentation:
            try:
                RequestsInstrumentation().instrument()
                logging.info("Requests instrumented for outbound span tracking")
            except Exception as e:
                logging.warning(f"Failed to instrument requests: {e}")
        else:
            logging.warning("RequestsInstrumentation not available")

    def instrument_pymongo(self) -> None:
        """Instrument PyMongo for database operation tracing"""
        if PyMongoInstrumentation:
            try:
                PyMongoInstrumentation().instrument()
                logging.info("PyMongo instrumented for database tracing")
            except Exception as e:
                logging.warning(f"Failed to instrument PyMongo: {e}")
        else:
            logging.warning("PyMongoInstrumentation not available")

    def instrument_redis(self) -> None:
        """Instrument Redis client for cache operation tracing"""
        if RedisInstrumentation:
            try:
                RedisInstrumentation().instrument()
                logging.info("Redis instrumented for cache tracing")
            except Exception as e:
                logging.warning(f"Failed to instrument Redis: {e}")
        else:
            logging.warning("RedisInstrumentation not available")

    def get_tracer(self) -> trace.Tracer:
        """Get global tracer instance"""
        if self.tracer is None:
            self.setup()
        return self.tracer

    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> trace.Span:
        """Create a new span with attributes"""
        tracer = self.get_tracer()
        span = tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        return span

    def trace_function(self, span_name: Optional[str] = None):
        """
        Decorator to automatically trace function execution
        
        Usage:
            @otel.trace_function("process_order")
            def process_order(order_id):
                return order
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = span_name or f"{func.__module__}.{func.__name__}"
                with self.get_tracer().start_as_current_span(name) as span:
                    # Add function arguments to span (exclude sensitive data)
                    span.set_attribute("function.args_count", len(args))
                    span.set_attribute("function.kwargs_count", len(kwargs))
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("function.status", "success")
                        return result
                    except Exception as e:
                        span.set_attribute("function.status", "error")
                        span.set_attribute("function.error", str(e))
                        span.set_attribute("exception.type", type(e).__name__)
                        raise
            return wrapper
        return decorator

    def get_current_trace_id(self) -> str:
        """Get current trace ID from span context"""
        span = trace.get_current_span()
        if span and span.is_recording():
            return format(span.get_span_context().trace_id, '032x')
        return "unknown"

    def get_current_span_id(self) -> str:
        """Get current span ID from span context"""
        span = trace.get_current_span()
        if span and span.is_recording():
            return format(span.get_span_context().span_id, '016x')
        return "unknown"

    def add_log_with_trace(self, logger: logging.Logger, level: int, message: str, **kwargs) -> None:
        """
        Log message with trace context enrichment
        
        Automatically includes trace_id, span_id, and timestamp
        """
        trace_id = self.get_current_trace_id()
        span_id = self.get_current_span_id()
        
        # Enrich log record
        extra = {
            "trace_id": trace_id,
            "span_id": span_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        logger.log(level, message, extra=extra)

    def create_trace_context(self, context_id: str, **metadata) -> Dict[str, Any]:
        """
        Create trace context for request/session
        
        Stores metadata for correlation across microservices
        """
        context = {
            "context_id": context_id,
            "trace_id": self.get_current_trace_id(),
            "span_id": self.get_current_span_id(),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata
        }
        self.trace_context_stack[context_id] = context
        return context

    def get_trace_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored trace context"""
        return self.trace_context_stack.get(context_id)

    def export_spans(self) -> None:
        """Force flush and export pending spans (use before shutdown)"""
        if self.tracer_provider:
            self.tracer_provider.force_flush()
            logging.info("Spans exported to Jaeger")

    def shutdown(self) -> None:
        """Graceful shutdown of TracerProvider"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logging.info("OpenTelemetry shutdown complete")


# Singleton instance
_otel_instance: Optional[OpenTelemetrySetup] = None


def get_otel() -> OpenTelemetrySetup:
    """Get or create global OpenTelemetry instance"""
    global _otel_instance
    if _otel_instance is None:
        _otel_instance = OpenTelemetrySetup(
            environment=os.getenv("ENVIRONMENT", "production"),
            enable_console_export=os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true"
        )
        _otel_instance.setup()
    return _otel_instance


def init_otel(app) -> OpenTelemetrySetup:
    """
    Initialize OpenTelemetry for FastAPI app
    
    Usage in app_enterprise.py:
        from opentelemetry_setup import init_otel
        app = FastAPI()
        otel = init_otel(app)
    """
    otel = get_otel()
    otel.instrument_fastapi(app)
    otel.instrument_requests()
    otel.instrument_pymongo()
    otel.instrument_redis()
    return otel


# --- Example Usage for Testing ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize
    otel = OpenTelemetrySetup(
        service_name="test-service",
        environment="development",
        enable_console_export=True
    )
    otel.setup()
    
    # Create a span
    with otel.get_tracer().start_as_current_span("test_operation") as span:
        span.set_attribute("operation.type", "import_test")
        logging.info(f"Trace ID: {otel.get_current_trace_id()}")
        logging.info(f"Span ID: {otel.get_current_span_id()}")
    
    otel.shutdown()
    print("✓ OpenTelemetry setup complete")
