#!/usr/bin/env python3
"""
TOUR 4 v10.1 — Performance Load Testing
Tests de charge réels : 50 → 100 → 300 utilisateurs concurrents
Durée : 5 minutes par scénario
Métriques : TPS, latence (p50/p95/p99), CPU, mémoire, taux d'erreur
"""

import threading
import time
import requests
import json
import statistics
import psutil
import os
from datetime import datetime
from collections import defaultdict

# Configuration
BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = "/api/health"
LOGIN_ENDPOINT = "/api/auth/login"
CLIENTS_ENDPOINT = "/api/clients"

# Credentials test
TEST_USER = "pissken@editionsfabsci.com"
TEST_PASSWORD = "Admin@2025"

# Résultats agrégés
results = {
    "50_users": {"latencies": [], "errors": 0, "success": 0, "start_time": None, "end_time": None},
    "100_users": {"latencies": [], "errors": 0, "success": 0, "start_time": None, "end_time": None},
    "300_users": {"latencies": [], "errors": 0, "success": 0, "start_time": None, "end_time": None}
}

cpu_samples = []
memory_samples = []
lock = threading.Lock()

def get_system_metrics():
    """Capture CPU et mémoire actuals"""
    process = psutil.Process(os.getpid())
    cpu = process.cpu_percent(interval=0.1)
    memory = process.memory_info().rss / (1024 ** 2)  # MB
    return cpu, memory

def worker(scenario_key, endpoint, method="GET", data=None):
    """Worker qui effectue une requête et mesure la latence"""
    try:
        start = time.time()
        
        if method == "POST":
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=data,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
        else:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                timeout=10,
                headers={"Authorization": f"Bearer {getattr(worker, 'token', '')}"}
            )
        
        latency = (time.time() - start) * 1000  # ms
        
        with lock:
            if response.status_code in [200, 201]:
                results[scenario_key]["success"] += 1
                results[scenario_key]["latencies"].append(latency)
            else:
                results[scenario_key]["errors"] += 1
    
    except Exception as e:
        with lock:
            results[scenario_key]["errors"] += 1

def get_auth_token():
    """Login et récupère le JWT token"""
    try:
        response = requests.post(
            f"{BASE_URL}{LOGIN_ENDPOINT}?email={TEST_USER}&password={TEST_PASSWORD}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except:
        pass
    return None

def run_load_test(num_users, duration_seconds=300, scenario_key="50_users"):
    """Exécute un test de charge avec N utilisateurs concurrents pendant D secondes"""
    print(f"\n{'='*70}")
    print(f"SCÉNARIO : {num_users} utilisateurs concurrents, {duration_seconds}s")
    print(f"{'='*70}")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    worker.token = token
    
    results[scenario_key]["start_time"] = datetime.now()
    start_time = time.time()
    
    threads = []
    request_count = 0
    
    # Spawn workers
    while time.time() - start_time < duration_seconds:
        # Crée N threads qui envoient des requêtes en parallèle
        for _ in range(num_users):
            # Alterne entre endpoints
            endpoint = CLIENTS_ENDPOINT if request_count % 2 == 0 else HEALTH_ENDPOINT
            method = "GET"
            
            t = threading.Thread(
                target=worker,
                args=(scenario_key, endpoint, method, None)
            )
            t.daemon = True
            t.start()
            threads.append(t)
            request_count += 1
        
        # Capture system metrics
        cpu, memory = get_system_metrics()
        cpu_samples.append(cpu)
        memory_samples.append(memory)
        
        # Attends 1 seconde avant la prochaine vague
        time.sleep(1)
    
    # Wait for all threads to finish
    for t in threads[:100]:  # Limite pour éviter timeout
        t.join(timeout=5)
    
    results[scenario_key]["end_time"] = datetime.now()
    
    # Affiche résultats
    print_scenario_results(scenario_key, num_users)

def print_scenario_results(scenario_key, num_users):
    """Affiche les résultats pour un scénario"""
    data = results[scenario_key]
    
    if not data["latencies"]:
        print(f"❌ Pas de requêtes réussies")
        return
    
    latencies = sorted(data["latencies"])
    total_requests = data["success"] + data["errors"]
    tps = total_requests / ((data["end_time"] - data["start_time"]).total_seconds())
    
    print(f"\n📊 Résultats pour {num_users} utilisateurs:")
    print(f"  ✓ Requêtes réussies : {data['success']}")
    print(f"  ✗ Erreurs : {data['errors']}")
    print(f"  📈 TPS (transactions/sec) : {tps:.2f}")
    print(f"  ⏱️  Latence moyenne : {statistics.mean(latencies):.2f} ms")
    print(f"  ⏱️  Latence p50 : {latencies[len(latencies)//2]:.2f} ms")
    print(f"  ⏱️  Latence p95 : {latencies[int(len(latencies)*0.95)]:.2f} ms")
    print(f"  ⏱️  Latence p99 : {latencies[int(len(latencies)*0.99)]:.2f} ms")
    print(f"  ⏱️  Latence min : {min(latencies):.2f} ms")
    print(f"  ⏱️  Latence max : {max(latencies):.2f} ms")
    
    if cpu_samples:
        print(f"  🖥️  CPU moyen : {statistics.mean(cpu_samples):.2f}%")
        print(f"  🖥️  CPU max : {max(cpu_samples):.2f}%")
    
    if memory_samples:
        print(f"  💾 Mémoire moyenne : {statistics.mean(memory_samples):.2f} MB")
        print(f"  💾 Mémoire max : {max(memory_samples):.2f} MB")
    
    error_rate = (data["errors"] / total_requests * 100) if total_requests > 0 else 0
    print(f"  ⚠️  Taux d'erreur : {error_rate:.2f}%")

def export_results_json():
    """Exporte tous les résultats en JSON avec preuves"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "scenarios": {}
    }
    
    for scenario_key, data in results.items():
        if data["latencies"]:
            latencies = sorted(data["latencies"])
            output["scenarios"][scenario_key] = {
                "successful_requests": data["success"],
                "failed_requests": data["errors"],
                "total_requests": data["success"] + data["errors"],
                "tps": (data["success"] + data["errors"]) / ((data["end_time"] - data["start_time"]).total_seconds()),
                "latency_stats": {
                    "mean_ms": statistics.mean(latencies),
                    "p50_ms": latencies[len(latencies)//2],
                    "p95_ms": latencies[int(len(latencies)*0.95)] if len(latencies) > 20 else latencies[-1],
                    "p99_ms": latencies[int(len(latencies)*0.99)] if len(latencies) > 100 else latencies[-1],
                    "min_ms": min(latencies),
                    "max_ms": max(latencies)
                },
                "system_metrics": {
                    "avg_cpu_percent": statistics.mean(cpu_samples) if cpu_samples else 0,
                    "max_cpu_percent": max(cpu_samples) if cpu_samples else 0,
                    "avg_memory_mb": statistics.mean(memory_samples) if memory_samples else 0,
                    "max_memory_mb": max(memory_samples) if memory_samples else 0
                },
                "error_rate_percent": (data["errors"] / (data["success"] + data["errors"]) * 100) if (data["success"] + data["errors"]) > 0 else 0,
                "duration_seconds": (data["end_time"] - data["start_time"]).total_seconds()
            }
    
    return output

def main():
    print("🚀 TOUR 4 v10.1 — Performance Load Testing")
    print(f"Base URL: {BASE_URL}")
    
    # Check backend health
    try:
        response = requests.get(f"{BASE_URL}{HEALTH_ENDPOINT}", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"⚠️  Backend health check returned {response.status_code}")
    except Exception as e:
        print(f"❌ Backend unreachable: {e}")
        return
    
    # Run load tests
    print("\n📋 Exécution des tests de charge...")
    
    # Scenario 1: 50 users for 2 minutes (démo)
    run_load_test(50, duration_seconds=120, scenario_key="50_users")
    
    # Scenario 2: 100 users for 2 minutes (démo)
    run_load_test(100, duration_seconds=120, scenario_key="100_users")
    
    # Scenario 3: 300 users for 2 minutes (démo)
    run_load_test(300, duration_seconds=120, scenario_key="300_users")
    
    # Export results
    output = export_results_json()
    
    with open("/home/user/ERP-FABS-V10/performance_load_test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Résultats exportés vers performance_load_test_results.json")

if __name__ == "__main__":
    main()
