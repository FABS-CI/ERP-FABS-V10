"""
TOUR 4: Prometheus Metrics - Standard Metrics Collection
=========================================================
Purpose: Prometheus-compatible metrics for monitoring and alerting
- Counter: Monotonic increasing values (requests, errors, sales)
- Gauge: Point-in-time values (memory, queue size, active sessions)
- Histogram: Distribution of values (response time, payload size)
- Summary: Percentiles (p50, p90, p99 latency)

Metrics categories:
1. System: CPU, memory, disk, network
2. HTTP: Request count, duration, status codes
3. Database: Query count, latency, connection pool
4. Business: Orders, invoices, clients, products
5. Cache: Hit rate, miss rate, eviction

All metrics exportable as Prometheus format on /metrics endpoint
"""

import time
import os
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime
from threading import Lock

from prometheus_client import (
    Counter, Gauge, Histogram, Summary, 
    CollectorRegistry, generate_latest, REGISTRY,
    start_http_server
)


# ============================================================================
# DATACLASSES FOR METRICS CONFIGURATION
# ============================================================================

@dataclass
class MetricConfig:
    """Base configuration for any metric"""
    name: str
    help: str
    labels: List[str] = field(default_factory=list)
    registry: CollectorRegistry = field(default_factory=lambda: REGISTRY)


@dataclass
class CounterConfig(MetricConfig):
    """Configuration for Counter metric"""
    pass


@dataclass
class GaugeConfig(MetricConfig):
    """Configuration for Gauge metric"""
    pass


@dataclass
class HistogramConfig(MetricConfig):
    """Configuration for Histogram metric"""
    buckets: tuple = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


@dataclass
class SummaryConfig(MetricConfig):
    """Configuration for Summary metric"""
    percentiles: List[float] = field(default_factory=lambda: [0.5, 0.9, 0.99])


# ============================================================================
# PROMETHEUS METRICS CLASS
# ============================================================================

class PrometheusMetrics:
    """
    Centralized Prometheus metrics management for TOUR 4
    
    Provides:
    - Standard metric types (Counter, Gauge, Histogram, Summary)
    - Automatic metric registration
    - Business logic metrics
    - Export to Prometheus format
    """

    def __init__(self, service_name: str = "ERP-FABS-CI", export_port: Optional[int] = None):
        """
        Initialize Prometheus metrics
        
        Args:
            service_name: Service identifier for metric prefix
            export_port: Port for /metrics endpoint (None = no HTTP server)
        """
        self.service_name = service_name
        self.prefix = service_name.lower().replace("-", "_")
        self.export_port = export_port
        self.registry = REGISTRY
        self._metrics: Dict[str, Any] = {}
        self._lock = Lock()

    # ========================================================================
    # SYSTEM METRICS
    # ========================================================================

    def _init_system_metrics(self) -> None:
        """Initialize system-level metrics"""
        
        # CPU and memory metrics
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_cpu_percent",
                help="CPU usage percentage"
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_memory_bytes",
                help="Memory usage in bytes",
                labels=["type"]  # heap, rss, virtual
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_disk_bytes",
                help="Disk usage in bytes",
                labels=["mount"]
            )
        )
        
        # Uptime
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_uptime_seconds",
                help="Service uptime in seconds"
            )
        )

    # ========================================================================
    # HTTP METRICS
    # ========================================================================

    def _init_http_metrics(self) -> None:
        """Initialize HTTP request/response metrics"""
        
        # Request count by method and path
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_http_requests_total",
                help="Total HTTP requests",
                labels=["method", "endpoint", "status"]
            )
        )
        
        # Request duration histogram
        self._register_histogram(
            HistogramConfig(
                name=f"{self.prefix}_http_request_duration_seconds",
                help="HTTP request duration in seconds",
                labels=["method", "endpoint"],
                buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
            )
        )
        
        # Request size histogram
        self._register_histogram(
            HistogramConfig(
                name=f"{self.prefix}_http_request_size_bytes",
                help="HTTP request size in bytes",
                labels=["method", "endpoint"]
            )
        )
        
        # Response size histogram
        self._register_histogram(
            HistogramConfig(
                name=f"{self.prefix}_http_response_size_bytes",
                help="HTTP response size in bytes",
                labels=["method", "endpoint", "status"]
            )
        )
        
        # Active HTTP connections gauge
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_http_connections_active",
                help="Active HTTP connections",
                labels=["endpoint"]
            )
        )
        
        # HTTP errors counter
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_http_errors_total",
                help="Total HTTP errors",
                labels=["status", "endpoint"]
            )
        )

    # ========================================================================
    # DATABASE METRICS
    # ========================================================================

    def _init_database_metrics(self) -> None:
        """Initialize database operation metrics"""
        
        # Query count by operation
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_db_queries_total",
                help="Total database queries",
                labels=["operation", "collection"]  # operation: find, insert, update, delete
            )
        )
        
        # Query duration
        self._register_histogram(
            HistogramConfig(
                name=f"{self.prefix}_db_query_duration_seconds",
                help="Database query duration",
                labels=["operation", "collection"]
            )
        )
        
        # Connection pool metrics
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_db_connections_active",
                help="Active database connections"
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_db_connections_available",
                help="Available database connections"
            )
        )
        
        # Slow query counter
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_db_slow_queries_total",
                help="Slow queries (>100ms)",
                labels=["operation", "collection"]
            )
        )
        
        # Database errors
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_db_errors_total",
                help="Total database errors",
                labels=["operation", "collection", "error_type"]
            )
        )

    # ========================================================================
    # CACHE METRICS (Redis)
    # ========================================================================

    def _init_cache_metrics(self) -> None:
        """Initialize cache (Redis) metrics"""
        
        # Cache hits/misses
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_cache_hits_total",
                help="Cache hit count",
                labels=["key_pattern"]
            )
        )
        
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_cache_misses_total",
                help="Cache miss count",
                labels=["key_pattern"]
            )
        )
        
        # Cache operations
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_cache_operations_total",
                help="Cache operations",
                labels=["operation"]  # get, set, delete, expire
            )
        )
        
        # Cache size
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_cache_size_bytes",
                help="Total cache size in bytes"
            )
        )
        
        # Cache evictions
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_cache_evictions_total",
                help="Cache evictions",
                labels=["policy"]
            )
        )

    # ========================================================================
    # AUTHENTICATION & SECURITY METRICS
    # ========================================================================

    def _init_auth_metrics(self) -> None:
        """Initialize authentication and security metrics"""
        
        # Login attempts
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_auth_login_attempts_total",
                help="Login attempts",
                labels=["status"]  # success, failed, locked
            )
        )
        
        # Active sessions
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_auth_active_sessions",
                help="Active user sessions",
                labels=["user_role"]
            )
        )
        
        # API key usage
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_auth_api_key_requests_total",
                help="API key requests",
                labels=["key_id", "status"]
            )
        )
        
        # Security events
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_security_events_total",
                help="Security events",
                labels=["event_type"]  # ip_change, multiple_failures, api_abuse
            )
        )

    # ========================================================================
    # BUSINESS METRICS
    # ========================================================================

    def _init_business_metrics(self) -> None:
        """Initialize business logic metrics"""
        
        # Orders
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_orders_created_total",
                help="Orders created",
                labels=["status"]  # pending, confirmed, shipped, canceled
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_orders_pending_total",
                help="Pending orders count"
            )
        )
        
        # Invoices
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_invoices_created_total",
                help="Invoices created",
                labels=["status"]  # issued, paid, overdue
            )
        )
        
        # Payments
        self._register_counter(
            CounterConfig(
                name=f"{self.prefix}_payments_total",
                help="Payments processed",
                labels=["status", "method"]  # success, failed; cash, card, transfer
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_revenue_total",
                help="Total revenue"
            )
        )
        
        # Stock
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_stock_items_total",
                help="Total stock items"
            )
        )
        
        self._register_gauge(
            GaugeConfig(
                name=f"{self.prefix}_stock_value_total",
                help="Total stock value"
            )
        )

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _register_counter(self, config: CounterConfig) -> Counter:
        """Register a Counter metric"""
        with self._lock:
            if config.name not in self._metrics:
                metric = Counter(
                    config.name, config.help,
                    labelnames=config.labels,
                    registry=config.registry
                )
                self._metrics[config.name] = metric
            return self._metrics[config.name]

    def _register_gauge(self, config: GaugeConfig) -> Gauge:
        """Register a Gauge metric"""
        with self._lock:
            if config.name not in self._metrics:
                metric = Gauge(
                    config.name, config.help,
                    labelnames=config.labels,
                    registry=config.registry
                )
                self._metrics[config.name] = metric
            return self._metrics[config.name]

    def _register_histogram(self, config: HistogramConfig) -> Histogram:
        """Register a Histogram metric"""
        with self._lock:
            if config.name not in self._metrics:
                metric = Histogram(
                    config.name, config.help,
                    labelnames=config.labels,
                    buckets=config.buckets,
                    registry=config.registry
                )
                self._metrics[config.name] = metric
            return self._metrics[config.name]

    def _register_summary(self, config: SummaryConfig) -> Summary:
        """Register a Summary metric"""
        with self._lock:
            if config.name not in self._metrics:
                metric = Summary(
                    config.name, config.help,
                    labelnames=config.labels,
                    registry=config.registry
                )
                self._metrics[config.name] = metric
            return self._metrics[config.name]

    def get_metric(self, name: str) -> Optional[Any]:
        """Retrieve a registered metric"""
        return self._metrics.get(name)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def initialize_all(self) -> None:
        """Initialize all metric categories"""
        self._init_system_metrics()
        self._init_http_metrics()
        self._init_database_metrics()
        self._init_cache_metrics()
        self._init_auth_metrics()
        self._init_business_metrics()

    def track_http_request(self, method: str, endpoint: str, status: int, duration: float, request_size: int = 0, response_size: int = 0) -> None:
        """Track HTTP request metrics"""
        counter = self.get_metric(f"{self.prefix}_http_requests_total")
        if counter:
            counter.labels(method=method, endpoint=endpoint, status=status).inc()
        
        histogram = self.get_metric(f"{self.prefix}_http_request_duration_seconds")
        if histogram:
            histogram.labels(method=method, endpoint=endpoint).observe(duration)
        
        if request_size > 0:
            histogram_req = self.get_metric(f"{self.prefix}_http_request_size_bytes")
            if histogram_req:
                histogram_req.labels(method=method, endpoint=endpoint).observe(request_size)
        
        if response_size > 0:
            histogram_resp = self.get_metric(f"{self.prefix}_http_response_size_bytes")
            if histogram_resp:
                histogram_resp.labels(method=method, endpoint=endpoint, status=status).observe(response_size)

    def track_db_query(self, operation: str, collection: str, duration: float) -> None:
        """Track database query metrics"""
        counter = self.get_metric(f"{self.prefix}_db_queries_total")
        if counter:
            counter.labels(operation=operation, collection=collection).inc()
        
        histogram = self.get_metric(f"{self.prefix}_db_query_duration_seconds")
        if histogram:
            histogram.labels(operation=operation, collection=collection).observe(duration)
        
        # Track slow queries
        if duration > 0.1:  # 100ms
            slow_counter = self.get_metric(f"{self.prefix}_db_slow_queries_total")
            if slow_counter:
                slow_counter.labels(operation=operation, collection=collection).inc()

    def track_cache_hit(self, key_pattern: str) -> None:
        """Track cache hit"""
        counter = self.get_metric(f"{self.prefix}_cache_hits_total")
        if counter:
            counter.labels(key_pattern=key_pattern).inc()

    def track_cache_miss(self, key_pattern: str) -> None:
        """Track cache miss"""
        counter = self.get_metric(f"{self.prefix}_cache_misses_total")
        if counter:
            counter.labels(key_pattern=key_pattern).inc()

    def track_login(self, status: str) -> None:
        """Track login attempt"""
        counter = self.get_metric(f"{self.prefix}_auth_login_attempts_total")
        if counter:
            counter.labels(status=status).inc()

    def set_active_sessions(self, user_role: str, count: int) -> None:
        """Set active sessions gauge"""
        gauge = self.get_metric(f"{self.prefix}_auth_active_sessions")
        if gauge:
            gauge.labels(user_role=user_role).set(count)

    def track_order(self, status: str) -> None:
        """Track order creation"""
        counter = self.get_metric(f"{self.prefix}_orders_created_total")
        if counter:
            counter.labels(status=status).inc()

    def track_payment(self, status: str, method: str) -> None:
        """Track payment"""
        counter = self.get_metric(f"{self.prefix}_payments_total")
        if counter:
            counter.labels(status=status, method=method).inc()

    def export_metrics(self) -> str:
        """Export metrics in Prometheus text format"""
        return generate_latest(self.registry).decode('utf-8')

    def start_http_server(self, port: Optional[int] = None) -> None:
        """Start HTTP server for /metrics endpoint"""
        port = port or self.export_port or 8001
        try:
            start_http_server(port, registry=self.registry)
            print(f"✓ Prometheus metrics available at http://localhost:{port}/metrics")
        except Exception as e:
            print(f"✗ Failed to start metrics server: {e}")

    def http_request_decorator(self, endpoint: str = None):
        """
        Decorator to automatically track HTTP request metrics
        
        Usage:
            @metrics.http_request_decorator("GET /api/clients")
            async def get_clients(request):
                return response
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                ep = endpoint or func.__name__
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.track_http_request("GET", ep, 200, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.track_http_request("GET", ep, 500, duration)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                ep = endpoint or func.__name__
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.track_http_request("GET", ep, 200, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.track_http_request("GET", ep, 500, duration)
                    raise
            
            # Return async or sync wrapper based on function type
            return async_wrapper if hasattr(func, '__await__') else sync_wrapper
        
        return decorator


# Singleton instance
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics(
            export_port=int(os.getenv("PROMETHEUS_PORT", "8001"))
        )
        _metrics_instance.initialize_all()
    return _metrics_instance


# Example usage for testing
if __name__ == "__main__":
    metrics = PrometheusMetrics()
    metrics.initialize_all()
    metrics.start_http_server()
    
    # Simulate some metrics
    metrics.track_http_request("GET", "/api/clients", 200, 0.05)
    metrics.track_http_request("POST", "/api/orders", 201, 0.15)
    metrics.track_db_query("find", "clients", 0.02)
    metrics.track_cache_hit("client:123")
    metrics.track_login("success")
    metrics.track_order("pending")
    metrics.track_payment("success", "card")
    
    print("✓ Prometheus metrics initialized")
    print("\n" + "=" * 60)
    print("Metrics Output Sample:")
    print("=" * 60)
    print(metrics.export_metrics()[:500] + "\n...")
