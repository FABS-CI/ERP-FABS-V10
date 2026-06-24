# TOUR 3: Monitoring & Observability Guide

Complete guide to using the TOUR 3 monitoring infrastructure.

---

## Quick Start

### Access Monitoring Dashboard
```bash
# Get full dashboard as JSON
curl http://localhost:8000/dashboard | jq .

# Get just metrics
curl http://localhost:8000/metrics | jq .

# Check health
curl http://localhost:8000/health | jq .
```

### Dashboard Structure
```json
{
  "timestamp": "2026-06-24T15:30:00",
  "overall_health": "healthy",
  "alerts_active": 0,
  "health_details": { ... },
  "active_alerts": [],
  "metrics_summary": {
    "total_requests": 1000,
    "error_rate": 0.5,
    "avg_response_time_ms": 45.2
  },
  "traces": {
    "active_traces": 5,
    "traces": { ... }
  }
}
```

---

## Metrics Collection

### Available Metrics

#### Counter Metrics
```python
# Track request volume
http_requests_total: {
  "method": "GET",
  "status": "200"
}

# Track errors
http_errors_total: {
  "status": "500"
}

# Authentication metrics
auth_attempts: {}
auth_failures: {}
auth_success: {}

# Application lifecycle
app_startups: {}
```

#### Histogram Metrics
```python
# Request duration (p50, p95, p99, avg, min, max)
http_request_duration_ms: {
  "count": 1000,
  "avg": 45.2,
  "min": 5.0,
  "max": 2000.0,
  "p50": 30.0,
  "p95": 150.0,
  "p99": 500.0
}
```

#### Gauge Metrics
(Added dynamically by monitoring system)

### Accessing Metrics Programmatically
```python
from monitoring_setup import get_monitoring_components

monitoring = get_monitoring_components()
metrics = monitoring["metrics"]

# Increment counter
metrics.increment_counter("custom_event", value=5)

# Record histogram
metrics.observe_histogram("custom_operation_ms", duration_ms)

# Get current value
total_requests = metrics.get_counter("http_requests_total")

# Get histogram stats
stats = metrics.get_histogram_stats("http_request_duration_ms")
# {"count": 1000, "avg": 45.2, "p50": 30.0, "p95": 150.0, ...}

# Export all metrics
all_metrics = metrics.export_metrics()
```

---

## Health Checks

### Health Check Endpoints
```bash
# Get overall health and all components
curl http://localhost:8000/health | jq .
```

### Response Format
```json
{
  "status": "healthy",
  "timestamp": "2026-06-24T15:30:00",
  "components": {
    "mongodb": {
      "status": "healthy",
      "last_check": "2026-06-24T15:30:00",
      "consecutive_failures": 0,
      "critical": true
    },
    "redis": {
      "status": "unhealthy",
      "last_check": "2026-06-24T15:29:55",
      "consecutive_failures": 3,
      "critical": false
    }
  }
}
```

### Register Custom Health Checks
```python
from monitoring_setup import health_checker

def check_cache():
    try:
        redis_client.ping()
        return True
    except:
        return False

def check_external_api():
    try:
        response = requests.get(EXTERNAL_API_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

# Register checks
health_checker.register_component("cache", check_cache, critical=False)
health_checker.register_component("external_api", check_external_api, critical=False)

# Check all
status = health_checker.check_all()
```

---

## Request Tracing

### Trace IDs
Every request gets a unique trace ID:

```python
# Automatically added to response headers
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000

# Correlate logs
# In application logs, filter by this trace ID to see all related events
```

### Using Trace IDs
```bash
# Get trace ID from response header
curl -i http://localhost:8000/api/clients | grep "X-Trace-Id"
# X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000

# Find all logs with this trace ID
grep "550e8400-e29b-41d4-a716-446655440000" /var/log/erp/app.log

# Track across multiple services
# Include X-Trace-Id in requests to other services
curl -H "X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000" \
  http://localhost:8001/api/service-b
```

### Accessing Traces Programmatically
```python
from monitoring_setup import get_monitoring_components

monitoring = get_monitoring_components()
tracer = monitoring["tracer"]

# Get specific trace
trace = tracer.get_trace("550e8400-e29b-41d4-a716-446655440000")
# {
#   "trace_id": "...",
#   "spans": [
#     {
#       "span_name": "GET /api/clients",
#       "duration_ms": 45.2,
#       "status": "success"
#     }
#   ],
#   "total_duration_ms": 45.2
# }

# Export all traces
all_traces = tracer.export_traces()
```

---

## Performance Logging

### JSON Structured Logs
```python
from monitoring_setup import get_monitoring_components

monitoring = get_monitoring_components()
perf_logger = monitoring["performance_logger"]

# Log HTTP request
perf_logger.log_request(
    method="POST",
    path="/api/invoices",
    status_code=201,
    duration_ms=150.5,
    ip="192.168.1.100",
    user_id="user_123"
)

# Log database query
perf_logger.log_db_query(
    collection="invoices",
    operation="insert",
    duration_ms=45.2,
    query_count=1
)

# Log cache hit/miss
perf_logger.log_cache_hit("invoices:123", hit=True)
```

### Log Output
```json
{
  "event": "http_request",
  "method": "POST",
  "path": "/api/invoices",
  "status_code": 201,
  "duration_ms": 150.5,
  "timestamp": "2026-06-24T15:30:00",
  "ip": "192.168.1.100",
  "user_id": "user_123"
}

{
  "event": "db_query",
  "collection": "invoices",
  "operation": "insert",
  "duration_ms": 45.2,
  "timestamp": "2026-06-24T15:30:00",
  "slow_query": false
}
```

### Slow Query Detection
Queries > 100ms are marked as slow:
```json
{
  "event": "db_query",
  "collection": "invoices",
  "operation": "find",
  "duration_ms": 250.0,
  "slow_query": true,
  "timestamp": "2026-06-24T15:30:00"
}
```

---

## Alert Management

### Available Alert Types
```python
from monitoring_setup import get_monitoring_components

monitoring = get_monitoring_components()
alert_manager = monitoring["alert_manager"]

# Check all active alerts
active_alerts = alert_manager.get_active_alerts()
# [
#   {
#     "alert_name": "high_error_rate",
#     "severity": "high",
#     "triggered_at": "2026-06-24T15:25:00"
#   }
# ]
```

### Register Custom Alerts
```python
from monitoring_setup import alert_manager

def check_error_rate():
    """Alert if error rate > 5%"""
    total = metrics.get_counter("http_requests_total")
    errors = metrics.get_counter("http_errors_total")
    if total > 0:
        error_rate = (errors / total)
        return error_rate > 0.05
    return False

def check_response_time():
    """Alert if p95 response time > 500ms"""
    stats = metrics.get_histogram_stats("http_request_duration_ms")
    return stats.get("p95", 0) > 500

def check_database_latency():
    """Alert if database queries > 100ms avg"""
    # Custom check
    return get_db_latency() > 100

# Register alerts
alert_manager.register_alert("high_error_rate", check_error_rate, severity="high")
alert_manager.register_alert("slow_response", check_response_time, severity="medium")
alert_manager.register_alert("db_latency", check_database_latency, severity="medium")

# Check all alerts
triggered = alert_manager.check_alerts()
```

---

## Monitoring Dashboard

### View Dashboard
```bash
curl http://localhost:8000/dashboard | jq .
```

### Dashboard Data Structure
```json
{
  "timestamp": "2026-06-24T15:30:00",
  "overall_health": "healthy",
  "alerts_active": 2,
  "health_details": {
    "overall_status": "healthy",
    "components": {
      "mongodb": {
        "status": "healthy",
        "last_check": "2026-06-24T15:30:00",
        "consecutive_failures": 0,
        "critical": true
      }
    }
  },
  "active_alerts": [
    {
      "alert_name": "high_error_rate",
      "severity": "high",
      "triggered_at": "2026-06-24T15:25:00"
    }
  ],
  "metrics_summary": {
    "total_requests": 5000,
    "error_rate": 2.5,
    "avg_response_time_ms": 52.3
  },
  "traces": {
    "active_traces": 15,
    "traces": {
      "550e8400-e29b-41d4-a716-446655440000": {
        "span_count": 3,
        "total_duration_ms": 120.5
      }
    }
  }
}
```

---

## Integration with External Services

### Prometheus Integration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'erp-fabs'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

For full Prometheus compatibility in v10.1, add:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import REGISTRY, CollectorRegistry

# Create standard Prometheus metrics
request_count = Counter('http_requests_total', 'Total requests', ['method', 'status'])
request_duration = Histogram('http_request_duration_ms', 'Request duration', buckets=[...])
active_connections = Gauge('active_connections', 'Active connections')

# Export endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")
```

### Sentry Integration
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-key@sentry.io/project-id",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0
)

# Errors automatically sent to Sentry
```

### ELK Stack Integration
```python
from pythonjsonlogger import jsonlogger
import logging

# Configure JSON logging
logHandler = logging.FileHandler('/var/log/erp/app.log')
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Use Filebeat to ship logs
# filebeat.yml:
# filebeat.inputs:
# - type: log
#   paths:
#     - /var/log/erp/app.log
# output.elasticsearch:
#   hosts: ["elasticsearch:9200"]
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "ERP FABS V10",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m]) / rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_ms)"
          }
        ]
      }
    ]
  }
}
```

---

## Performance Optimization Tips

### 1. Monitor Slow Queries
```python
# Enable slow query logging
slow_threshold = 100  # ms

perf_logger.slow_query_threshold_ms = slow_threshold

# Review slow queries
# grep "slow_query" /var/log/erp/app.log
```

### 2. Optimize Database Indexes
Use the pre-defined indexes:
```python
from database_schema import SchemaOptimizer

for idx in SchemaOptimizer.get_all_indexes():
    db[idx.collection].create_index(idx.fields)
```

### 3. Cache Frequent Queries
```python
# In v10.1, add Redis caching
redis_client = redis.Redis(host='localhost')

@app.get("/api/products")
async def get_products(skip: int = 0, limit: int = 20):
    cache_key = f"products:{skip}:{limit}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    products = db["products"].find().skip(skip).limit(limit)
    redis_client.setex(cache_key, 3600, json.dumps(products))
    return products
```

### 4. Monitor Resource Usage
```python
import psutil

def check_cpu_usage():
    return psutil.cpu_percent() < 80

def check_memory_usage():
    return psutil.virtual_memory().percent < 85

def check_disk_usage():
    return psutil.disk_usage('/').percent < 90

health_checker.register_component("cpu", check_cpu_usage)
health_checker.register_component("memory", check_memory_usage)
health_checker.register_component("disk", check_disk_usage)
```

---

## Troubleshooting

### High Error Rate
```python
# 1. Check active alerts
curl http://localhost:8000/dashboard | jq '.active_alerts'

# 2. Review error logs
grep "ERROR" /var/log/erp/error.log | tail -20

# 3. Check health
curl http://localhost:8000/health | jq .

# 4. Review Sentry
# Visit: https://sentry.io/organizations/.../issues/
```

### Slow Response Times
```python
# 1. Check metrics
curl http://localhost:8000/metrics | jq '.histograms.http_request_duration_ms'

# 2. Review slow queries
grep "slow_query.*true" /var/log/erp/app.log

# 3. Check database
db.stats()  # Check collection sizes

# 4. Review traces
curl http://localhost:8000/dashboard | jq '.traces'
```

### High Memory Usage
```python
# 1. Check metrics storage size
from monitoring_setup import metrics
print(len(metrics.counters))  # Number of counter metrics
print(len(metrics.histograms))  # Number of histogram metrics

# 2. Clear old traces
tracer.cleanup_old_traces(max_age_seconds=3600)

# 3. Reset metrics
metrics.reset()
```

### Database Connection Issues
```python
# 1. Test connectivity
curl http://localhost:8000/health | jq '.components.mongodb'

# 2. Check connection pool
client.close()
client = MongoClient(MONGODB_URI, maxPoolSize=100)

# 3. Review MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

---

## Dashboard Templates

### Business Metrics Dashboard
```json
{
  "title": "Business Metrics",
  "panels": [
    {
      "title": "Invoices Created (Daily)",
      "metric": "invoices_created_total"
    },
    {
      "title": "Revenue (Daily)",
      "metric": "revenue_daily"
    },
    {
      "title": "Payments Received",
      "metric": "payments_received_total"
    },
    {
      "title": "Outstanding Invoices",
      "metric": "invoices_outstanding"
    }
  ]
}
```

### System Health Dashboard
```json
{
  "title": "System Health",
  "panels": [
    {
      "title": "API Response Time (p95)",
      "metric": "http_request_duration_ms",
      "percentile": 95
    },
    {
      "title": "Error Rate (%)",
      "metric": "error_rate_percent"
    },
    {
      "title": "Database Latency",
      "metric": "db_query_duration_ms"
    },
    {
      "title": "Request Rate (RPS)",
      "metric": "http_requests_per_second"
    }
  ]
}
```

---

## Alerting Examples

### Send Alerts to Slack
```python
import requests

def send_slack_alert(alert_name: str, severity: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    
    color = {
        "low": "#36a64f",
        "medium": "#ff9900",
        "high": "#ff0000"
    }.get(severity, "#999999")
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": alert_name,
                "text": f"Alert triggered at {datetime.now()}",
                "fields": [
                    {"title": "Severity", "value": severity, "short": True}
                ]
            }
        ]
    }
    
    requests.post(webhook, json=payload)

# When alert triggers
if alert_manager.get_active_alerts():
    for alert in alert_manager.get_active_alerts():
        send_slack_alert(alert["alert_name"], alert["severity"])
```

### Send Alerts to PagerDuty
```python
import requests

def send_pagerduty_alert(alert_name: str, severity: str):
    integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
    
    severity_map = {
        "low": "info",
        "medium": "warning",
        "high": "error",
        "critical": "critical"
    }
    
    payload = {
        "routing_key": integration_key,
        "event_action": "trigger",
        "dedup_key": alert_name,
        "payload": {
            "summary": f"Alert: {alert_name}",
            "timestamp": datetime.now().isoformat(),
            "severity": severity_map.get(severity, "error"),
            "source": "ERP-FABS"
        }
    }
    
    requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json=payload
    )
```

---

## Monitoring Checklist

Before production deployment:

- [ ] Health check endpoint working
- [ ] Metrics endpoint accessible
- [ ] Dashboard displaying data
- [ ] Alerts configured
- [ ] Sentry DSN set
- [ ] Log aggregation configured
- [ ] Performance baseline established
- [ ] Monitoring dashboards created
- [ ] Alert notification setup
- [ ] Backup monitoring enabled
- [ ] Database monitoring active
- [ ] Request tracing working

---

**Last Updated:** 2026-06-24  
**Version:** TOUR 3 (10.0.0)
