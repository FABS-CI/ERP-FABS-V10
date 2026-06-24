#!/usr/bin/env python3
"""
Performance Profiler — Measure baseline response times
Identify slowest endpoints for TOUR 2 optimization
"""

import requests
import time
from datetime import datetime
import statistics

BASE_URL = "http://localhost:8000"
EMAIL = "pissken@editionsfabsci.com"
PASSWORD = "Admin@2025"

# Test endpoints and their criticality
ENDPOINTS = [
    # Critical Path (highest frequency in production)
    {"method": "GET", "path": "/api/utilisateurs", "params": {"limit": "100", "skip": "0"}, "name": "List Users", "priority": "CRITICAL"},
    {"method": "GET", "path": "/api/clients", "params": {"limit": "100", "skip": "0"}, "name": "List Clients", "priority": "CRITICAL"},
    {"method": "GET", "path": "/api/commandes", "params": {"limit": "100", "skip": "0"}, "name": "List Commandes", "priority": "CRITICAL"},
    {"method": "GET", "path": "/api/devis", "params": {"limit": "100", "skip": "0"}, "name": "List Devis", "priority": "CRITICAL"},
    {"method": "GET", "path": "/api/factures", "params": {"limit": "100", "skip": "0"}, "name": "List Factures", "priority": "CRITICAL"},
    
    # High Frequency
    {"method": "GET", "path": "/api/rh/employes", "params": {"limit": "100", "skip": "0"}, "name": "List Employes", "priority": "HIGH"},
    {"method": "GET", "path": "/api/produits", "params": {"limit": "100", "skip": "0"}, "name": "List Produits", "priority": "HIGH"},
    {"method": "GET", "path": "/api/stock/balance", "params": {"produit_id": "product_001"}, "name": "Stock Balance", "priority": "HIGH"},
    {"method": "GET", "path": "/api/finance/dashboard", "params": {}, "name": "Finance Dashboard", "priority": "HIGH"},
    {"method": "GET", "path": "/api/rh/bulletins", "params": {"limit": "50", "skip": "0"}, "name": "List Bulletins", "priority": "HIGH"},
    
    # Medium Frequency
    {"method": "GET", "path": "/api/finance/journaux", "params": {"mois": "6", "annee": "2026"}, "name": "Journaux", "priority": "MEDIUM"},
    {"method": "GET", "path": "/api/finance/balance", "params": {"mois": "6", "annee": "2026"}, "name": "Balance", "priority": "MEDIUM"},
    {"method": "GET", "path": "/api/livraisons", "params": {"limit": "100", "skip": "0"}, "name": "List Livraisons", "priority": "MEDIUM"},
]

def profile_endpoint(method, path, params, name, runs=5):
    """Profile an endpoint with multiple runs"""
    times = []
    errors = 0
    
    # Login first
    r = requests.post(f"{BASE_URL}/api/auth/login", params={"email": EMAIL, "password": PASSWORD})
    token = r.json().get("access_token") if r.status_code == 200 else None
    
    if not token:
        return {"name": name, "error": "Auth failed", "times": [], "avg": 0}
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    for i in range(runs):
        try:
            start = time.time()
            if method == "GET":
                r = requests.get(f"{BASE_URL}{path}", params=params, headers=headers, timeout=10)
            else:
                r = requests.post(f"{BASE_URL}{path}", params=params, headers=headers, timeout=10)
            elapsed = (time.time() - start) * 1000  # ms
            
            if r.status_code == 200:
                times.append(elapsed)
            else:
                errors += 1
        except Exception as e:
            errors += 1
    
    if times:
        avg = statistics.mean(times)
        min_t = min(times)
        max_t = max(times)
        p95 = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else avg
    else:
        avg = min_t = max_t = p95 = 0
    
    return {
        "name": name,
        "path": path,
        "method": method,
        "avg": avg,
        "min": min_t,
        "max": max_t,
        "p95": p95,
        "runs": runs - errors,
        "errors": errors,
    }

def main():
    print("="*80)
    print("PERFORMANCE PROFILER — BASELINE MEASUREMENT")
    print("="*80)
    print(f"\nStart: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Endpoints: {len(ENDPOINTS)}")
    print(f"Runs per endpoint: 5")
    print(f"API: {BASE_URL}\n")
    
    results = {
        "CRITICAL": [],
        "HIGH": [],
        "MEDIUM": [],
    }
    
    # Profile all endpoints
    for endpoint in ENDPOINTS:
        print(f"  Profiling: {endpoint['name']}...", end=" ", flush=True)
        result = profile_endpoint(
            endpoint["method"],
            endpoint["path"],
            endpoint["params"],
            endpoint["name"],
            runs=5
        )
        results[endpoint["priority"]].append(result)
        
        status = "✅" if result["avg"] < 200 else "⚠️" if result["avg"] < 500 else "❌"
        print(f"{status} {result['avg']:.0f}ms (p95: {result['p95']:.0f}ms)")
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS BY PRIORITY")
    print("="*80)
    
    for priority in ["CRITICAL", "HIGH", "MEDIUM"]:
        print(f"\n{priority} PRIORITY ({len(results[priority])} endpoints)")
        print("-"*80)
        print(f"{'Endpoint':<30} {'Avg':<10} {'P95':<10} {'Min':<10} {'Max':<10} {'Status':<10}")
        print("-"*80)
        
        for result in sorted(results[priority], key=lambda x: x['avg'], reverse=True):
            avg = result['avg']
            status = "✅ FAST" if avg < 200 else "⚠️ SLOW" if avg < 500 else "❌ VERY SLOW"
            print(f"{result['name']:<30} {avg:<10.0f} {result['p95']:<10.0f} {result['min']:<10.0f} {result['max']:<10.0f} {status:<10}")
    
    # Overall statistics
    all_avgs = [r['avg'] for r in results['CRITICAL'] + results['HIGH'] + results['MEDIUM']]
    
    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    print(f"Total Endpoints: {len(all_avgs)}")
    print(f"Average Response Time: {statistics.mean(all_avgs):.0f}ms")
    print(f"Median Response Time: {statistics.median(all_avgs):.0f}ms")
    print(f"P95 Response Time: {sorted(all_avgs)[int(len(all_avgs)*0.95)]:.0f}ms")
    print(f"Slowest Endpoint: {sorted(results['CRITICAL'] + results['HIGH'] + results['MEDIUM'], key=lambda x: x['avg'])[-1]['name']} ({sorted(results['CRITICAL'] + results['HIGH'] + results['MEDIUM'], key=lambda x: x['avg'])[-1]['avg']:.0f}ms)")
    
    # Performance assessment
    slow_endpoints = [r for r in all_avgs if r > 500]
    very_slow = [r for r in all_avgs if r > 1000]
    
    print(f"\nEndpoints > 500ms: {len(slow_endpoints)}/{len(all_avgs)} ⚠️")
    print(f"Endpoints > 1000ms: {len(very_slow)}/{len(all_avgs)} ❌")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS FOR TOUR 2")
    print("="*80)
    
    print("\n✅ PRIORITY 1: Fix N+1 Queries in Critical Path")
    print("   These 5 endpoints are queried most frequently in production")
    for r in results['CRITICAL']:
        if r['avg'] > 300:
            print(f"   - {r['name']}: {r['avg']:.0f}ms (likely N+1 pattern)")
    
    print("\n✅ PRIORITY 2: Implement Pagination")
    print("   All list endpoints should limit=100 by default")
    
    print("\n✅ PRIORITY 3: Add Redis Caching")
    print("   Cache list endpoints with 5-minute TTL")
    
    print("\n✅ PRIORITY 4: Use Bulk Queries")
    print("   Replace individual queries in loops with bulk $in queries")
    
    print(f"\nEnd: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    # Generate report file
    with open("/home/user/ERP-FABS-V10/PERFORMANCE_BASELINE.md", "w") as f:
        f.write(f"""# Performance Baseline Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Average Response Time**: {statistics.mean(all_avgs):.0f}ms
- **P95 Response Time**: {sorted(all_avgs)[int(len(all_avgs)*0.95)]:.0f}ms
- **Slow Endpoints (>500ms)**: {len(slow_endpoints)}
- **Very Slow Endpoints (>1000ms)**: {len(very_slow)}

## Critical Path Endpoints
""")
        for r in results['CRITICAL']:
            f.write(f"- {r['name']}: {r['avg']:.0f}ms\n")
        
        f.write(f"""

## Next Steps (TOUR 2)
1. Fix N+1 queries in slow endpoints
2. Implement bulk query patterns
3. Add Redis caching
4. Re-profile and measure improvements

Target: Average response time < 200ms (p95 < 300ms)
""")
    
    print("\n✅ Baseline report saved: PERFORMANCE_BASELINE.md")

if __name__ == "__main__":
    main()
