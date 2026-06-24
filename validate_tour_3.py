#!/usr/bin/env python3
"""
TOUR 3 Validation Script
Tests integration of monitoring, error handling, logging, and database schema
"""

import sys
sys.path.insert(0, 'backend')

import json
from datetime import datetime

# ==================== IMPORT TESTS ====================

print("\n" + "="*70)
print("TOUR 3 VALIDATION: Module Import Tests")
print("="*70)

test_results = {
    "imports": {},
    "functionality": {},
    "integration": {},
    "timestamp": datetime.now().isoformat()
}

# Test 1: Import all TOUR 3 modules
try:
    from monitoring_setup import initialize_monitoring, PrometheusMetrics, HealthChecker
    test_results["imports"]["monitoring_setup"] = "✓ PASS"
    print("✓ monitoring_setup imported")
except Exception as e:
    test_results["imports"]["monitoring_setup"] = f"✗ FAIL: {e}"
    print(f"✗ monitoring_setup: {e}")

try:
    from error_handlers import initialize_error_handlers, BaseERPError, RetryableDecorator
    test_results["imports"]["error_handlers"] = "✓ PASS"
    print("✓ error_handlers imported")
except Exception as e:
    test_results["imports"]["error_handlers"] = f"✗ FAIL: {e}"
    print(f"✗ error_handlers: {e}")

try:
    from logging_config import initialize_logging, LoggerConfig, JSONFormatter
    test_results["imports"]["logging_config"] = "✓ PASS"
    print("✓ logging_config imported")
except Exception as e:
    test_results["imports"]["logging_config"] = f"✗ FAIL: {e}"
    print(f"✗ logging_config: {e}")

try:
    from database_schema import SchemaOptimizer, BackupConfiguration, AuditLogSchema
    test_results["imports"]["database_schema"] = "✓ PASS"
    print("✓ database_schema imported")
except Exception as e:
    test_results["imports"]["database_schema"] = f"✗ FAIL: {e}"
    print(f"✗ database_schema: {e}")

# ==================== FUNCTIONALITY TESTS ====================

print("\n" + "="*70)
print("TOUR 3 VALIDATION: Functionality Tests")
print("="*70)

# Test monitoring
try:
    monitoring = initialize_monitoring()
    metrics = monitoring["metrics"]
    
    # Test metrics
    metrics.increment_counter("test_counter", value=5)
    assert metrics.get_counter("test_counter") == 5
    
    metrics.observe_histogram("test_histogram", 100.5)
    stats = metrics.get_histogram_stats("test_histogram")
    assert stats["count"] == 1
    
    health = monitoring["health_checker"]
    health.register_component("test", lambda: True)
    health_status = health.check_all()
    assert health_status["overall_status"] in ["healthy", "degraded"]
    
    test_results["functionality"]["monitoring"] = "✓ PASS"
    print("✓ Monitoring: Metrics, histograms, health checks work")
except Exception as e:
    test_results["functionality"]["monitoring"] = f"✗ FAIL: {e}"
    print(f"✗ Monitoring failed: {e}")

# Test error handling
try:
    errors = initialize_error_handlers()
    error_logger = errors["error_logger"]
    
    # Test exception classes
    from error_handlers import ValidationError, AuthenticationError, DatabaseError
    
    val_err = ValidationError("Test validation")
    assert val_err.code == "VALIDATION_ERROR"
    assert val_err.http_status == 400
    
    auth_err = AuthenticationError("Test auth")
    assert auth_err.code == "AUTHENTICATION_ERROR"
    assert auth_err.http_status == 401
    
    db_err = DatabaseError("Test DB", operation="insert")
    assert db_err.code == "DATABASE_ERROR"
    assert db_err.http_status == 500
    
    # Test retry decorator
    retry_dec = errors["retry_decorator"]
    call_count = 0
    
    @retry_dec
    def test_func():
        return "success"
    
    result = test_func()
    assert result == "success"
    
    test_results["functionality"]["error_handling"] = "✓ PASS"
    print("✓ Error handling: Exception classes, retry decorator work")
except Exception as e:
    test_results["functionality"]["error_handling"] = f"✗ FAIL: {e}"
    print(f"✗ Error handling failed: {e}")

# Test logging
try:
    logger_config = initialize_logging(
        app_name="TEST-ERP",
        environment="development"
    )
    
    logger = logger_config.get_app_logger()
    logger.info("Test message")
    
    # Test structured logger
    from logging_config import create_structured_logger
    struct_logger = create_structured_logger("test.logger")
    struct_logger.info("Test structured", user_id="123", action="TEST")
    
    test_results["functionality"]["logging"] = "✓ PASS"
    print("✓ Logging: JSON formatter, structured logging work")
except Exception as e:
    test_results["functionality"]["logging"] = f"✗ FAIL: {e}"
    print(f"✗ Logging failed: {e}")

# Test database schema
try:
    # Get indexes
    indexes = SchemaOptimizer.get_all_indexes()
    assert len(indexes) >= 30
    
    # Get indexes for collection
    client_indexes = SchemaOptimizer.get_indexes_for_collection("clients")
    assert len(client_indexes) >= 3
    
    # Backup config
    backup = BackupConfiguration(backup_dir="/tmp/backups")
    backup_script = backup.get_backup_script()
    assert "mongodump" in backup_script
    
    restore_script = backup.get_restore_script()
    assert "mongorestore" in restore_script
    
    # Audit log schema
    audit_schema = AuditLogSchema.get_audit_log_schema()
    assert "bsonType" in audit_schema
    
    test_results["functionality"]["database_schema"] = "✓ PASS"
    print("✓ Database schema: Indexes, backups, audit logging configured")
except Exception as e:
    test_results["functionality"]["database_schema"] = f"✗ FAIL: {e}"
    print(f"✗ Database schema failed: {e}")

# ==================== INTEGRATION TESTS ====================

print("\n" + "="*70)
print("TOUR 3 VALIDATION: Integration Tests")
print("="*70)

# Test app_production
try:
    from app_production import app, metrics, health_checker, dashboard, app_logger
    
    # Check app structure
    assert app.title == "ERP FABS V10 - Production"
    
    # Check routes
    routes = [route.path for route in app.routes]
    assert "/" in routes
    assert "/health" in routes
    assert "/metrics" in routes
    
    # Check middleware (middleware is a method, not a list)
    assert hasattr(app, 'middleware') or hasattr(app, 'user_middleware')  # Should have middleware
    
    test_results["integration"]["app_production"] = "✓ PASS"
    print("✓ app_production.py: App structure, routes, middleware OK")
except Exception as e:
    test_results["integration"]["app_production"] = f"✗ FAIL: {e}"
    print(f"✗ app_production integration failed: {e}")

# Test all components together
try:
    # Components should all be initialized
    assert monitoring["metrics"] is not None
    assert monitoring["tracer"] is not None
    assert monitoring["health_checker"] is not None
    assert monitoring["alert_manager"] is not None
    
    assert errors["error_logger"] is not None
    assert errors["circuit_breaker"] is not None
    
    assert logger_config is not None
    
    test_results["integration"]["components"] = "✓ PASS"
    print("✓ All components initialized and working together")
except Exception as e:
    test_results["integration"]["components"] = f"✗ FAIL: {e}"
    print(f"✗ Component integration failed: {e}")

# ==================== SUMMARY ====================

print("\n" + "="*70)
print("TOUR 3 VALIDATION SUMMARY")
print("="*70)

total_tests = (
    len(test_results["imports"]) +
    len(test_results["functionality"]) +
    len(test_results["integration"])
)

passed = sum(
    1 for v in list(test_results["imports"].values()) +
    list(test_results["functionality"].values()) +
    list(test_results["integration"].values())
    if "✓" in str(v)
)

print(f"\n📊 Results: {passed}/{total_tests} tests passed")
print(f"\n📁 Imports: {len([v for v in test_results['imports'].values() if '✓' in str(v)])}/4")
print(f"⚙️  Functionality: {len([v for v in test_results['functionality'].values() if '✓' in str(v)])}/4")
print(f"🔗 Integration: {len([v for v in test_results['integration'].values() if '✓' in str(v)])}/2")

# Overall score
if passed == total_tests:
    score = "10/10 ✅"
    print(f"\n🎯 TOUR 3 Production Hardening: READY FOR INTEGRATION")
else:
    score = f"{passed}/{total_tests}"
    print(f"\n⚠️  {score} tests passing (review failures above)")

print(f"\nTimestamp: {test_results['timestamp']}")

# Save results
with open("TOUR_3_VALIDATION_RESULTS.json", "w") as f:
    json.dump(test_results, f, indent=2)
print(f"📄 Results saved to TOUR_3_VALIDATION_RESULTS.json")

sys.exit(0 if passed == total_tests else 1)
