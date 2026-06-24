#!/usr/bin/env python3
"""
UNIT TESTS TOUR 4 v10.1 — CORRECTED
====================================
Tous les 6 tests cassés maintenant corrigés avec les bonnes signatures.
"""

import sys
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s — %(message)s'
)
logger = logging.getLogger('UNIT_TESTS')

results = {
    'timestamp': datetime.now().isoformat(),
    'tests': [],
    'summary': {'total': 0, 'passed': 0, 'failed': 0}
}

def record_test(name: str, passed: bool, error: str = "", details: str = ""):
    """Record test result"""
    result = {
        'name': name,
        'passed': passed,
        'error': error,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    results['tests'].append(result)
    results['summary']['total'] += 1
    
    if passed:
        results['summary']['passed'] += 1
        print(f"✓ {name}")
    else:
        results['summary']['failed'] += 1
        print(f"✗ {name}: {error}")
    
    return result


# ============================================================================
# TEST 1: SessionManager
# ============================================================================
def test_1_session_manager():
    """SessionManager: Create + get sessions"""
    from backend.session_manager import SessionManager
    
    try:
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = MagicMock()
        
        sm = SessionManager(db=mock_db)
        
        session_id = sm.create_session(
            user_id="test_user",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if session_id and len(session_id) > 0:
            session = sm.get_session(session_id)
            if session is not None:
                record_test("1. SessionManager.create/get_session()", True,
                           details=f"Session created: {session_id[:12]}...")
            else:
                record_test("1. SessionManager.create/get_session()", False, 
                           "Session not retrieved")
        else:
            record_test("1. SessionManager.create/get_session()", False, 
                       "No session ID returned")
    
    except Exception as e:
        record_test("1. SessionManager.create/get_session()", False, str(e)[:80])


# ============================================================================
# TEST 2: APIKeyManager
# ============================================================================
def test_2_api_key_manager():
    """APIKeyManager: Generate + verify keys"""
    from backend.api_key_manager import APIKeyManager
    
    try:
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = MagicMock()
        
        akm = APIKeyManager(db=mock_db)
        
        # generate_key() returns (key_id, secret)
        key_id, secret = akm.generate_key(
            name="test_key",
            user_id="test_user"
        )
        
        if key_id and secret:
            key = akm.get_key(key_id)
            if key is not None:
                record_test("2. APIKeyManager.generate_key/get_key()", True,
                           details=f"Key: {key_id[:12]}...")
            else:
                record_test("2. APIKeyManager.generate_key/get_key()", False,
                           "Key not retrieved")
        else:
            record_test("2. APIKeyManager.generate_key/get_key()", False,
                       "generate_key() failed")
    
    except Exception as e:
        record_test("2. APIKeyManager.generate_key/get_key()", False, str(e)[:80])


# ============================================================================
# TEST 3: RedisClient
# ============================================================================
def test_3_redis_client():
    """RedisClient: Connection + cache operations"""
    from backend.redis_integration import RedisClient
    
    try:
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_class.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.get.return_value = json.dumps({"user": "test"})
            
            rc = RedisClient()
            
            if rc.is_connected():
                rc.cache_set('test_key', {'user': 'test'}, ttl_minutes=10)
                value = rc.cache_get('test_key')
                if value is not None:
                    record_test("3. RedisClient.cache_set/get()", True,
                               details="Redis cache OK")
                else:
                    record_test("3. RedisClient.cache_set/get()", False,
                               "Value not cached")
            else:
                record_test("3. RedisClient.cache_set/get()", False,
                           "Redis not connected")
    
    except Exception as e:
        record_test("3. RedisClient.cache_set/get()", False, str(e)[:80])


# ============================================================================
# TEST 4: PrometheusMetrics
# ============================================================================
def test_4_prometheus_metrics():
    """PrometheusMetrics: Initialize + set metrics"""
    from backend.prometheus_metrics import PrometheusMetrics
    
    try:
        pm = PrometheusMetrics(service_name="ERP-FABS-CI")
        pm.initialize_all()
        
        # set_active_sessions(user_role, count) NOT just (count)
        pm.set_active_sessions(user_role="admin", count=5)
        
        metrics_output = pm.export_metrics()
        if metrics_output and len(metrics_output) > 0:
            record_test("4. PrometheusMetrics.set_active_sessions()", True,
                       details=f"Metrics: {len(metrics_output)} bytes")
        else:
            record_test("4. PrometheusMetrics.set_active_sessions()", False,
                       "No metrics exported")
    
    except Exception as e:
        record_test("4. PrometheusMetrics.set_active_sessions()", False, str(e)[:80])


# ============================================================================
# TEST 5: GrafanaDashboards
# ============================================================================
def test_5_grafana_dashboards():
    """GrafanaDashboards: Get dashboards"""
    from backend.grafana_dashboards import GrafanaDashboards
    
    try:
        gd = GrafanaDashboards(datasource_uid="prometheus")
        
        dashboard = gd.get_api_performance_dashboard()
        if dashboard and isinstance(dashboard, dict):
            all_dashboards = gd.get_all_dashboards()
            if isinstance(all_dashboards, list):
                record_test("5. GrafanaDashboards.get_dashboards()", True,
                           details=f"Dashboards: {len(all_dashboards)}")
            else:
                record_test("5. GrafanaDashboards.get_dashboards()", False,
                           "get_all_dashboards() not a list")
        else:
            record_test("5. GrafanaDashboards.get_dashboards()", False,
                       "No dashboard returned")
    
    except Exception as e:
        record_test("5. GrafanaDashboards.get_dashboards()", False, str(e)[:80])


# ============================================================================
# TEST 6: AlertManager
# ============================================================================
def test_6_alert_manager():
    """AlertManager: Queue alerts"""
    from backend.alert_manager_external import AlertManager, Alert, AlertSeverity
    
    try:
        mock_redis = MagicMock()
        mock_redis.lpush = MagicMock(return_value=1)
        
        am = AlertManager(redis_client=mock_redis)
        
        # queue_alert(alert: Alert) — needs Alert object
        alert = Alert(
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.WARNING
        )
        
        result = am.queue_alert(alert)
        if result:  # queue_alert returns bool
            record_test("6. AlertManager.queue_alert()", True,
                       details="Alert queued OK")
        else:
            record_test("6. AlertManager.queue_alert()", False,
                       "queue_alert() returned False")
    
    except Exception as e:
        record_test("6. AlertManager.queue_alert()", False, str(e)[:80])


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "=" * 80)
    print("UNIT TESTS TOUR 4 v10.1 — CORRECTED")
    print("=" * 80)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        test_1_session_manager,
        test_2_api_key_manager,
        test_3_redis_client,
        test_4_prometheus_metrics,
        test_5_grafana_dashboards,
        test_6_alert_manager,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"ERROR in {test_func.__name__}: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    summary = results['summary']
    total = summary['total']
    passed = summary['passed']
    failed = summary['failed']
    pct = (100 * passed // total) if total > 0 else 0
    
    print(f"RESULTS: {passed}/{total} tests PASSED ({pct}%)")
    
    if failed == 0:
        print("✓✓✓ ALL 6 TESTS PASS ✓✓✓")
    else:
        print(f"⚠ {failed} test(s) still failing")
    
    # Save results
    report_path = '/home/user/ERP-FABS-V10/test_results_tour4.json'
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved: {report_path}")
    print("=" * 80 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
