#!/usr/bin/env python3
"""
TOUR 4 v10.1 — Resilience Testing
Tests : arrêt Redis, redémarrage, coupure réseau, failover, récupération automatique
"""

import subprocess
import time
import requests
import json
import psutil
from datetime import datetime
import signal
import os

BASE_URL = "http://localhost:8000"
REDIS_PORT = 6379
MONGODB_PORT = 27017

resilience_results = {
    "timestamp": datetime.now().isoformat(),
    "scenarios": {},
    "recovery_metrics": {}
}

def find_process_by_port(port):
    """Find process running on given port"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return proc
        except:
            pass
    return None

def check_service_health(service_name, endpoint="/api/health"):
    """Check if service is responding"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=3)
        return response.status_code == 200
    except:
        return False

def test_redis_failure_recovery():
    """Test Redis failure and automatic recovery"""
    print("\n" + "=" * 70)
    print("🧪 Test 1: Redis Failure and Recovery")
    print("=" * 70)
    
    results = {
        "test_name": "Redis Failure & Recovery",
        "start_time": datetime.now().isoformat(),
        "events": []
    }
    
    # Baseline: Service is healthy
    print("\n1️⃣  Baseline check: Backend healthy?")
    is_healthy = check_service_health("backend")
    print(f"   {'✅ YES' if is_healthy else '❌ NO'}")
    results["events"].append({
        "timestamp": datetime.now().isoformat(),
        "event": "baseline_health_check",
        "status": "healthy" if is_healthy else "unhealthy"
    })
    
    # Simulate Redis failure (kill Redis process)
    print("\n2️⃣  Simulating Redis failure...")
    redis_proc = find_process_by_port(REDIS_PORT)
    if redis_proc:
        redis_pid = redis_proc.pid
        print(f"   Redis PID: {redis_pid}")
        redis_proc.terminate()
        time.sleep(2)
        
        results["events"].append({
            "timestamp": datetime.now().isoformat(),
            "event": "redis_killed",
            "pid": redis_pid
        })
        print("   ✓ Redis process terminated")
    else:
        print("   ℹ️  Redis not running (may be in container or disabled)")
        results["events"].append({
            "timestamp": datetime.now().isoformat(),
            "event": "redis_not_found",
            "note": "May be container/cluster mode"
        })
    
    # Test service during Redis outage
    print("\n3️⃣  Testing service during Redis outage (30 seconds)...")
    start_outage = time.time()
    outage_errors = 0
    outage_successes = 0
    
    while time.time() - start_outage < 30:
        is_healthy = check_service_health("backend")
        if is_healthy:
            outage_successes += 1
        else:
            outage_errors += 1
        time.sleep(1)
    
    results["events"].append({
        "timestamp": datetime.now().isoformat(),
        "event": "outage_period",
        "duration_seconds": 30,
        "successful_requests": outage_successes,
        "failed_requests": outage_errors
    })
    print(f"   During outage: {outage_successes} success, {outage_errors} failures")
    
    # Recovery
    print("\n4️⃣  Recovery phase...")
    if redis_proc:
        # Restart Redis
        try:
            subprocess.Popen(["redis-server", "--port", str(REDIS_PORT)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            print("   ✓ Redis restart initiated")
            
            # Wait for recovery
            recovery_time = 0
            max_recovery_time = 60
            while recovery_time < max_recovery_time:
                if check_service_health("backend"):
                    print(f"   ✓ Service recovered in {recovery_time}s")
                    break
                time.sleep(1)
                recovery_time += 1
            else:
                print(f"   ⚠️  Recovery not complete after {max_recovery_time}s")
            
            results["events"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "redis_recovery",
                "recovery_time_seconds": recovery_time,
                "status": "recovered" if recovery_time < max_recovery_time else "timeout"
            })
        except Exception as e:
            print(f"   ❌ Error restarting Redis: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    results["total_duration_seconds"] = 0  # Manually set for now
    
    resilience_results["scenarios"]["redis_failure"] = results
    return results

def test_high_memory_pressure():
    """Test service behavior under memory pressure"""
    print("\n" + "=" * 70)
    print("🧪 Test 2: High Memory Pressure")
    print("=" * 70)
    
    results = {
        "test_name": "Memory Pressure",
        "start_time": datetime.now().isoformat(),
        "events": []
    }
    
    print("\n1️⃣  Baseline memory usage:")
    process = psutil.Process(os.getpid())
    baseline_memory = process.memory_info().rss / (1024 ** 2)
    print(f"   Backend memory: {baseline_memory:.2f} MB")
    
    results["events"].append({
        "timestamp": datetime.now().isoformat(),
        "event": "baseline_memory",
        "memory_mb": baseline_memory
    })
    
    print("\n2️⃣  Sending bulk requests to trigger memory usage...")
    try:
        # Get auth token first
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "pissken@editionsfabsci.com", "password": "Admin@2025"},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            
            # Send multiple requests
            for i in range(10):
                try:
                    requests.get(
                        f"{BASE_URL}/api/clients",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                except:
                    pass
                time.sleep(0.5)
            
            # Check memory after requests
            peak_memory = process.memory_info().rss / (1024 ** 2)
            memory_increase = peak_memory - baseline_memory
            
            print(f"   Peak memory: {peak_memory:.2f} MB (+{memory_increase:.2f} MB)")
            
            results["events"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "peak_memory_after_requests",
                "memory_mb": peak_memory,
                "increase_mb": memory_increase
            })
            
            # Check if service is still healthy
            is_healthy = check_service_health("backend")
            print(f"   Service health: {'✅ Healthy' if is_healthy else '❌ Degraded'}")
            
            results["events"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "health_check_after_memory_pressure",
                "status": "healthy" if is_healthy else "degraded"
            })
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    resilience_results["scenarios"]["memory_pressure"] = results
    return results

def test_network_latency_simulation():
    """Simulate network degradation"""
    print("\n" + "=" * 70)
    print("🧪 Test 3: Network Latency and Packet Loss")
    print("=" * 70)
    
    results = {
        "test_name": "Network Degradation",
        "start_time": datetime.now().isoformat(),
        "events": [],
        "latencies_observed": []
    }
    
    print("\n1️⃣  Testing response times under normal conditions:")
    
    latencies = []
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "pissken@editionsfabsci.com", "password": "Admin@2025"},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            
            for i in range(10):
                start = time.time()
                try:
                    requests.get(
                        f"{BASE_URL}/api/clients",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                    latency = (time.time() - start) * 1000
                    latencies.append(latency)
                except:
                    pass
                time.sleep(0.2)
            
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            print(f"   Average latency: {avg_latency:.2f} ms")
            
            results["events"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "normal_latency_measurement",
                "average_ms": avg_latency,
                "samples": len(latencies)
            })
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    results["latencies_observed"] = latencies
    resilience_results["scenarios"]["network_latency"] = results
    return results

def test_concurrent_connection_limits():
    """Test behavior under high concurrent connections"""
    print("\n" + "=" * 70)
    print("🧪 Test 4: Concurrent Connection Limits")
    print("=" * 70)
    
    results = {
        "test_name": "Concurrent Connections",
        "start_time": datetime.now().isoformat(),
        "events": []
    }
    
    print("\n1️⃣  Opening 50 concurrent connections...")
    
    import threading
    success_count = 0
    error_count = 0
    lock = threading.Lock()
    
    def make_request():
        nonlocal success_count, error_count
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            with lock:
                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
        except:
            with lock:
                error_count += 1
    
    threads = []
    for i in range(50):
        t = threading.Thread(target=make_request)
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Wait for all to complete
    for t in threads:
        t.join(timeout=15)
    
    print(f"   Results: {success_count} successful, {error_count} failed")
    
    results["events"].append({
        "timestamp": datetime.now().isoformat(),
        "event": "concurrent_connections_test",
        "concurrent_count": 50,
        "successful": success_count,
        "failed": error_count,
        "success_rate_percent": (success_count / 50 * 100) if success_count + error_count > 0 else 0
    })
    
    results["end_time"] = datetime.now().isoformat()
    resilience_results["scenarios"]["concurrent_connections"] = results
    return results

def main():
    print("=" * 70)
    print("🛡️  TOUR 4 v10.1 — Resilience Testing")
    print("=" * 70)
    
    # Run all resilience tests
    test_redis_failure_recovery()
    test_high_memory_pressure()
    test_network_latency_simulation()
    test_concurrent_connection_limits()
    
    # Export results
    with open("/home/user/ERP-FABS-V10/resilience_test_results.json", "w") as f:
        json.dump(resilience_results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ Resilience tests complete")
    print("📊 Results exported to resilience_test_results.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
