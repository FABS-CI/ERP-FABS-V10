"""
TOUR 3: Monitoring Setup for Production Hardening
- Prometheus metrics collection
- Request/performance tracing
- Health check system
- Alert thresholds
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from collections import defaultdict
import threading


class PrometheusMetrics:
    """Prometheus-style metrics collection (in-memory, not using prom client library)"""
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        self.reset_time = datetime.now()
    
    def increment_counter(self, metric_name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.counters[key] += value
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.gauges[key] = value
    
    def observe_histogram(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a value in a histogram"""
        with self.lock:
            key = self._make_key(metric_name, labels)
            self.histograms[key].append(value)
    
    def _make_key(self, metric_name: str, labels: Dict[str, str] = None) -> str:
        """Create a key from metric name and labels"""
        if not labels:
            return metric_name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric_name}{{{label_str}}}"
    
    def get_counter(self, metric_name: str) -> int:
        """Get counter value"""
        return self.counters.get(metric_name, 0)
    
    def get_gauge(self, metric_name: str) -> float:
        """Get gauge value"""
        return self.gauges.get(metric_name, 0.0)
    
    def get_histogram_stats(self, metric_name: str) -> Dict[str, float]:
        """Get histogram statistics (p50, p95, p99, avg, max)"""
        values = self.histograms.get(metric_name, [])
        if not values:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_vals = sorted(values)
        count = len(sorted_vals)
        
        return {
            "count": count,
            "avg": sum(values) / count,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "p50": sorted_vals[count // 2],
            "p95": sorted_vals[int(count * 0.95)],
            "p99": sorted_vals[int(count * 0.99)],
        }
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics in a structured format"""
        with self.lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.reset_time).total_seconds(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    k: self.get_histogram_stats(k)
                    for k in self.histograms.keys()
                }
            }
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.reset_time = datetime.now()


class RequestTracer:
    """Distributed request tracing (span tracking)"""
    
    def __init__(self):
        self.traces: Dict[str, List[Dict]] = {}
        self.lock = threading.Lock()
        self.max_traces = 1000
    
    def start_span(self, trace_id: str, span_name: str, metadata: Dict[str, Any] = None) -> str:
        """Start a new trace span"""
        with self.lock:
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            
            span = {
                "span_name": span_name,
                "start_time": time.time(),
                "end_time": None,
                "duration_ms": None,
                "metadata": metadata or {},
                "status": "in_progress"
            }
            self.traces[trace_id].append(span)
            return str(len(self.traces[trace_id]) - 1)
    
    def end_span(self, trace_id: str, span_index: int, status: str = "success", error: str = None):
        """End a trace span"""
        with self.lock:
            if trace_id in self.traces and span_index < len(self.traces[trace_id]):
                span = self.traces[trace_id][span_index]
                span["end_time"] = time.time()
                span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
                span["status"] = status
                if error:
                    span["error"] = error
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get a complete trace"""
        with self.lock:
            if trace_id in self.traces:
                return {
                    "trace_id": trace_id,
                    "spans": self.traces[trace_id],
                    "total_duration_ms": sum(s["duration_ms"] or 0 for s in self.traces[trace_id])
                }
        return None
    
    def export_traces(self) -> Dict:
        """Export all active traces"""
        with self.lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "active_traces": len(self.traces),
                "traces": {
                    k: {
                        "span_count": len(v),
                        "total_duration_ms": sum(s["duration_ms"] or 0 for s in v)
                    }
                    for k, v in self.traces.items()
                }
            }
    
    def cleanup_old_traces(self, max_age_seconds: int = 3600):
        """Remove traces older than max_age_seconds"""
        with self.lock:
            current_time = time.time()
            to_delete = [
                trace_id for trace_id, spans in self.traces.items()
                if spans and (current_time - spans[-1]["end_time"] > max_age_seconds)
            ]
            for trace_id in to_delete:
                del self.traces[trace_id]


class PerformanceLogger:
    """Log and track performance metrics"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger("performance")
        self.slow_query_threshold_ms = 100
        self.slow_request_threshold_ms = 500
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, 
                   ip: str = None, user_id: str = None):
        """Log HTTP request performance"""
        level = logging.WARNING if status_code >= 400 else logging.INFO
        
        log_entry = {
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "user_id": user_id
        }
        
        if duration_ms > self.slow_request_threshold_ms:
            log_entry["slow_request"] = True
            level = logging.WARNING
        
        self.logger.log(level, json.dumps(log_entry))
    
    def log_db_query(self, collection: str, operation: str, duration_ms: float, 
                    query_count: int = 1, error: str = None):
        """Log database operation performance"""
        level = logging.ERROR if error else logging.INFO
        
        log_entry = {
            "event": "db_query",
            "collection": collection,
            "operation": operation,
            "duration_ms": duration_ms,
            "query_count": query_count,
            "timestamp": datetime.now().isoformat(),
        }
        
        if error:
            log_entry["error"] = error
            level = logging.ERROR
        
        if duration_ms > self.slow_query_threshold_ms:
            log_entry["slow_query"] = True
            level = logging.WARNING
        
        self.logger.log(level, json.dumps(log_entry))
    
    def log_cache_hit(self, cache_key: str, hit: bool):
        """Log cache hit/miss"""
        self.logger.info(json.dumps({
            "event": "cache_access",
            "key": cache_key,
            "hit": hit,
            "timestamp": datetime.now().isoformat()
        }))


class HealthChecker:
    """Health check system with component status"""
    
    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def register_component(self, name: str, check_fn: Callable[[], bool], 
                          critical: bool = True):
        """Register a health check component"""
        with self.lock:
            self.components[name] = {
                "check_fn": check_fn,
                "critical": critical,
                "last_status": None,
                "last_check": None,
                "consecutive_failures": 0
            }
    
    def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        with self.lock:
            for component_name, component in self.components.items():
                try:
                    is_healthy = component["check_fn"]()
                    component["last_status"] = "healthy" if is_healthy else "unhealthy"
                    component["last_check"] = datetime.now().isoformat()
                    
                    if is_healthy:
                        component["consecutive_failures"] = 0
                    else:
                        component["consecutive_failures"] += 1
                    
                    results[component_name] = {
                        "status": component["last_status"],
                        "last_check": component["last_check"],
                        "consecutive_failures": component["consecutive_failures"],
                        "critical": component["critical"]
                    }
                    
                    if not is_healthy and component["critical"]:
                        overall_healthy = False
                
                except Exception as e:
                    component["consecutive_failures"] += 1
                    component["last_status"] = "error"
                    results[component_name] = {
                        "status": "error",
                        "error": str(e),
                        "consecutive_failures": component["consecutive_failures"],
                        "critical": component["critical"]
                    }
                    
                    if component["critical"]:
                        overall_healthy = False
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if overall_healthy else "degraded",
            "components": results
        }
    
    def get_status(self, component_name: str) -> Optional[Dict]:
        """Get status of a specific component"""
        with self.lock:
            if component_name in self.components:
                comp = self.components[component_name]
                return {
                    "status": comp["last_status"],
                    "last_check": comp["last_check"],
                    "consecutive_failures": comp["consecutive_failures"]
                }
        return None


class AlertManager:
    """Alert management for monitoring thresholds"""
    
    def __init__(self):
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict] = []
        self.lock = threading.Lock()
    
    def register_alert(self, alert_name: str, condition_fn: Callable[[], bool], 
                      severity: str = "warning"):
        """Register an alert condition"""
        with self.lock:
            self.alerts[alert_name] = {
                "condition_fn": condition_fn,
                "severity": severity,
                "triggered": False,
                "last_check": None,
                "first_triggered": None
            }
    
    def check_alerts(self) -> List[Dict]:
        """Check all registered alerts"""
        triggered = []
        
        with self.lock:
            for alert_name, alert in self.alerts.items():
                try:
                    is_triggered = alert["condition_fn"]()
                    alert["last_check"] = datetime.now().isoformat()
                    
                    if is_triggered and not alert["triggered"]:
                        alert["triggered"] = True
                        alert["first_triggered"] = datetime.now().isoformat()
                        triggered.append({
                            "alert_name": alert_name,
                            "severity": alert["severity"],
                            "triggered_at": alert["first_triggered"]
                        })
                    
                    elif not is_triggered and alert["triggered"]:
                        alert["triggered"] = False
                    
                    if is_triggered:
                        triggered.append({
                            "alert_name": alert_name,
                            "severity": alert["severity"],
                            "triggered_at": alert["first_triggered"],
                            "ongoing": True
                        })
                
                except Exception as e:
                    triggered.append({
                        "alert_name": alert_name,
                        "severity": "error",
                        "error": str(e)
                    })
        
        if triggered:
            self.alert_history.extend(triggered)
        
        return triggered
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all currently active alerts"""
        with self.lock:
            return [
                {
                    "alert_name": name,
                    "severity": alert["severity"],
                    "triggered_at": alert["first_triggered"]
                }
                for name, alert in self.alerts.items()
                if alert["triggered"]
            ]


class MonitoringDashboard:
    """Aggregate view of all monitoring data"""
    
    def __init__(self, metrics: PrometheusMetrics, tracer: RequestTracer, 
                health: HealthChecker, alert_manager: AlertManager):
        self.metrics = metrics
        self.tracer = tracer
        self.health = health
        self.alert_manager = alert_manager
    
    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate complete monitoring dashboard"""
        health_status = self.health.check_all()
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": health_status["overall_status"],
            "alerts_active": len(active_alerts),
            "health_details": health_status,
            "active_alerts": active_alerts,
            "metrics_summary": {
                "total_requests": self.metrics.get_counter("http_requests_total"),
                "error_rate": self._calculate_error_rate(),
                "avg_response_time_ms": self._calculate_avg_response_time(),
            },
            "traces": self.tracer.export_traces()
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        total = self.metrics.get_counter("http_requests_total")
        if total == 0:
            return 0.0
        errors = self.metrics.get_counter("http_errors_total")
        return (errors / total) * 100
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        stats = self.metrics.get_histogram_stats("http_request_duration_ms")
        return stats.get("avg", 0.0)


# Global instances (initialized by app)
metrics = None
tracer = None
performance_logger = None
health_checker = None
alert_manager = None
dashboard = None


def initialize_monitoring(logger: logging.Logger = None) -> Dict[str, Any]:
    """Initialize all monitoring components"""
    global metrics, tracer, performance_logger, health_checker, alert_manager, dashboard
    
    metrics = PrometheusMetrics()
    tracer = RequestTracer()
    performance_logger = PerformanceLogger(logger)
    health_checker = HealthChecker()
    alert_manager = AlertManager()
    dashboard = MonitoringDashboard(metrics, tracer, health_checker, alert_manager)
    
    return {
        "metrics": metrics,
        "tracer": tracer,
        "performance_logger": performance_logger,
        "health_checker": health_checker,
        "alert_manager": alert_manager,
        "dashboard": dashboard
    }


def get_monitoring_components() -> Dict[str, Any]:
    """Get initialized monitoring components"""
    return {
        "metrics": metrics,
        "tracer": tracer,
        "performance_logger": performance_logger,
        "health_checker": health_checker,
        "alert_manager": alert_manager,
        "dashboard": dashboard
    }
