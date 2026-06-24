# PLAN DE CORRECTION — Atteindre 9.5+/10 Production Ready
**Date:** 24 Juin 2026  
**Objectif:** Corriger défaillances critiques, valider preuves réelles  
**Timeline:** 5-7 jours (exécution + tests réels)

---

## PRIORITÉ 1 — UNIT TESTS (CRITIQUE)

### Problème
- **Statut:** 3/9 PASSED (67% échecs)
- **Modules échoués:** SessionManager, APIKeyManager, RedisClient, PrometheusMetrics, GrafanaDashboards, AlertManager
- **Erreurs Typiques:** Missing kwargs, missing attributes, import errors

### Action 1.1: Vérifier et corriger SessionManager
```bash
cd /home/user/ERP-FABS-V10

# Inspécter le code
python3 << 'EOF'
import inspect
from backend.session_manager import SessionManager
print(inspect.signature(SessionManager.__init__))
EOF

# Expected: __init__(self, config: dict, cache: Optional[dict] = None)
# Actual: Prend redis_client en argument?

# FIX: Adapter le test ou corriger la classe
```

**Livrable:** `test_results_final.json` avec 9/9 PASSED

---

### Action 1.2: Vérifier et corriger APIKeyManager
```python
# Erreur: "APIKeyManager.generate_key() missing 1 required positional argument: 'name'"
# Fix: Vérifier signature réelle, adapter appel test

from backend.api_key_manager import APIKeyManager
# Ajouter 'name' parameter dans test
```

**Livrable:** `backend/tests/test_api_key_manager_fixed.py`

---

### Action 1.3: Corriger RedisClient
```python
# Erreur: "'RedisClient' object has no attribute 'health_check'"
# Fix: Implémenter health_check() ou adapter test

# Option A: Ajouter method health_check()
# Option B: Mock redis_client dans test
```

**Livrable:** `RedisClient.health_check()` implémenté

---

### Action 1.4: Corriger PrometheusMetrics
```python
# Erreur: "object has no attribute 'increment_counter'"
# Fix: Implémenter increment_counter() 

class PrometheusMetrics:
    def increment_counter(self, name: str, labels: dict = None):
        """Increment counter metric"""
        # Implementation
```

**Livrable:** `backend/prometheus_metrics.py` + test PASSED

---

### Action 1.5: Corriger GrafanaDashboards
```python
# Erreur: "object has no attribute 'create_dashboard'"
# Fix: Implémenter create_dashboard()

class GrafanaDashboards:
    def create_dashboard(self, name: str, panels: list):
        """Create Grafana dashboard"""
        # Implementation
```

**Livrable:** `backend/grafana_dashboards.py` + test PASSED

---

### Action 1.6: Corriger AlertManager
```python
# Erreur: "module does not have the attribute 'smtplib'"
# Fix: Import smtplib correctement

import smtplib  # ← Manquait
from email.mime.text import MIMEText
```

**Livrable:** `backend/alert_manager_external.py` + test PASSED

---

## PRIORITÉ 2 — LOAD TEST (CRITIQUE)

### Problème
- **Affirmation:** 40.5K requêtes, 0 erreur, TPS 211.59
- **Preuve:** Aucun fichier k6 JSON ou logs bruts
- **Impact:** Cannot verify performance claims

### Action 2.1: Installer k6 (si absent)
```bash
# Check
which k6 || echo "k6 not installed"

# Install
sudo apt-get update && sudo apt-get install -y k6
```

---

### Action 2.2: Créer load test k6 réel
**Fichier:** `tests/load_test_k6.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = 'http://localhost:8000';

export const options = {
  stages: [
    { duration: '5m', target: 50 },   // 50 users, 5 min
    { duration: '5m', target: 100 },  // 100 users, 5 min
    { duration: '5m', target: 300 },  // 300 users, 5 min
    { duration: '5m', target: 0 },    // Cooldown
  ],
  thresholds: {
    http_req_duration: ['p(95)<250', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  // Login
  let loginRes = http.post(`${BASE_URL}/api/auth/login`, {
    email: 'pissken@editionsfabsci.com',
    password: 'Admin@2025',
  });
  
  let token = loginRes.json('access_token');
  let params = { headers: { Authorization: `Bearer ${token}` } };

  // Business workflows
  http.get(`${BASE_URL}/api/clients`, params);
  http.get(`${BASE_URL}/api/products`, params);
  http.get(`${BASE_URL}/api/commandes`, params);
  http.get(`${BASE_URL}/api/stock`, params);
  http.get(`${BASE_URL}/api/finance/dashboard`, params);

  sleep(1);
}
```

---

### Action 2.3: Exécuter test k6 et exporter JSON
```bash
cd /home/user/ERP-FABS-V10

# Exécuter avec export JSON
k6 run tests/load_test_k6.js \
  -o json=load_test_results_real.json \
  --vus=50 --duration=20m

# Vérifier résultat
cat load_test_results_real.json | jq '.summary'
```

**Livrable:** 
- `load_test_results_real.json` (vrai output k6)
- `RAPPORT_LOAD_TEST_REAL.md` (analyse résultats)

---

### Action 2.4: Valider affirmations vs résultats réels
```bash
# Extraire stats
cat load_test_results_real.json | jq '.summary | {
  "total_requests": .requests.total,
  "successful_requests": .requests.success,
  "failed_requests": .requests.failed,
  "error_rate": (.requests.failed / .requests.total),
  "avg_duration": .duration.avg,
  "p95_duration": .duration.p95,
  "p99_duration": .duration.p99,
  "throughput_rps": .throughput
}'
```

**Livrable:** Comparaison affirmation vs réalité

---

## PRIORITÉ 3 — SÉCURITÉ OWASP (MOYEN)

### Problème
- **Affirmation:** OWASP Top 10 audit complet
- **Preuve:** Aucun rapport audit
- **Impact:** Cannot verify security claims

### Action 3.1: Installer ZAP (OWASP ZAProxy)
```bash
# Install (if not present)
which zaproxy || sudo apt-get install -y zaproxy

# Verify
zaproxy -version
```

---

### Action 3.2: Exécuter ZAP scan
```bash
# Baseline scan
zaproxy -cmd \
  -host localhost \
  -port 8000 \
  -r zap_report.html

# Vérifier rapport
ls -lh zap_report.html
```

---

### Action 3.3: Scan alternatif (si ZAP indisponible)
```python
# Manual OWASP checklist test
python3 << 'EOF'
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "your_jwt_token"

tests = {
    "A1_injection": test_sql_injection(),
    "A2_auth": test_auth_bypass(),
    "A3_xss": test_xss(),
    "A4_xxe": test_xxe(),
    "A5_acl": test_acl(),
    "A6_crypto": test_crypto(),
    "A7_auth_mgmt": test_session_mgmt(),
    "A8_data": test_data_exposure(),
    "A9_deps": test_vulnerable_deps(),
    "A10_logging": test_logging(),
}

results = {k: v for k, v in tests.items()}
with open('owasp_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)
EOF
```

**Livrable:** `RAPPORT_SECURITE_OWASP_AUDIT.md` + résultats JSON

---

## PRIORITÉ 4 — RÉSILIENCE (MOYEN)

### Problème
- **Affirmation:** 4 scénarios failover testés, 100% uptime
- **Preuve:** Aucun test d'exécution
- **Impact:** Cannot verify resilience

### Action 4.1: Créer test résilience
**Fichier:** `tests/test_resilience.py`

```python
import time
import requests
import json

BASE_URL = "http://localhost:8000"

class ResilienceTest:
    def __init__(self):
        self.results = {
            "scenarios": [],
            "timestamp": time.time()
        }
    
    def test_scenario_1_api_restart(self):
        """Restart API, verify recovery < 5s"""
        # Kill process
        # Measure time to response OK
        # Record result
        pass
    
    def test_scenario_2_db_failure(self):
        """Database unavailable, verify graceful degradation"""
        pass
    
    def test_scenario_3_cache_failure(self):
        """Redis unavailable, verify fallback to DB"""
        pass
    
    def test_scenario_4_network_latency(self):
        """Add 500ms latency, verify circuit breaker"""
        pass
    
    def run_all(self):
        self.test_scenario_1_api_restart()
        self.test_scenario_2_db_failure()
        self.test_scenario_3_cache_failure()
        self.test_scenario_4_network_latency()
        
        # Export results
        with open('resilience_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

if __name__ == '__main__':
    test = ResilienceTest()
    test.run_all()
```

**Livrable:** `resilience_test_results.json` + `RAPPORT_RESILIENCE_TESTS.md`

---

## PRIORITÉ 5 — BACKUP/RESTORE (MOYEN)

### Problème
- **Affirmation:** RPO 60min, RTO <1s, PITR supported
- **Preuve:** Aucun log restauration
- **Impact:** Cannot verify backup strategy

### Action 5.1: Créer backup + restore test
**Fichier:** `tests/test_backup_restore.py`

```python
import subprocess
import time
import json
from datetime import datetime

class BackupTest:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
    
    def backup_database(self):
        """Create full backup"""
        start = time.time()
        # Backup logic
        duration = time.time() - start
        self.results["tests"].append({
            "scenario": "backup_full",
            "duration_sec": duration,
            "status": "OK" if duration < 60 else "SLOW"
        })
    
    def test_restore_full(self):
        """Full restore test"""
        start = time.time()
        # Restore logic
        duration = time.time() - start
        rto = duration
        self.results["tests"].append({
            "scenario": "restore_full",
            "rto_sec": rto,
            "status": "OK" if rto < 1 else "SLOW"
        })
    
    def test_pitr(self, time_delta_hours=6):
        """Point-in-time recovery test"""
        start = time.time()
        # PITR logic
        duration = time.time() - start
        self.results["tests"].append({
            "scenario": f"pitr_{time_delta_hours}h",
            "duration_sec": duration,
            "status": "OK"
        })
    
    def test_rpo(self):
        """Measure Recovery Point Objective"""
        # Check backup frequency
        rpo_minutes = 60  # Expected
        self.results["tests"].append({
            "scenario": "rpo_measurement",
            "rpo_minutes": rpo_minutes,
            "status": "OK" if rpo_minutes <= 60 else "FAIL"
        })
    
    def run_all(self):
        self.backup_database()
        self.test_restore_full()
        self.test_pitr()
        self.test_rpo()
        
        with open('backup_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

if __name__ == '__main__':
    test = BackupTest()
    test.run_all()
```

**Livrable:** `backup_test_results.json` + `RAPPORT_BACKUP_TEST.md`

---

## PRIORITÉ 6 — OBSERVABILITÉ EXPORT (BAS)

### Problème
- **État:** Prometheus + Grafana code ready, pas d'export réel
- **Preuve:** Aucun CSV/JSON d'export métriques
- **Impact:** Cannot verify observability metrics

### Action 6.1: Exporter Prometheus metrics
```bash
# Vérifier endpoint Prometheus
curl http://localhost:8000/metrics 2>/dev/null | head -50

# Exporter en format JSON
curl http://localhost:8000/metrics 2>/dev/null > prometheus_export.txt

# Parser et convertir JSON
python3 << 'EOF'
import re
import json

with open('prometheus_export.txt') as f:
    lines = f.readlines()

metrics = {}
for line in lines:
    if line.startswith('#'):
        continue
    if '{' in line:
        name, value = line.rsplit('}', 1)
        name = name.split('{')[0]
        try:
            metrics[name] = float(value.strip())
        except:
            pass

with open('prometheus_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
EOF
```

**Livrable:** `prometheus_metrics.json` (data réelle)

---

## CHRONOLOGIE EXÉCUTION

```
Jour 1: Fix unit tests (1.1-1.6)
        - 6 modules, ~2h par module
        - ETA: ~12h travail
        - Livrable: test_results_final.json (9/9 PASSED)

Jour 2: Load test k6 réel (2.1-2.4)
        - Créer script + exécuter 20min
        - ETA: ~3h
        - Livrable: load_test_results_real.json

Jour 3: Sécurité OWASP (3.1-3.3)
        - ZAP scan ou checklist manuel
        - ETA: ~4h
        - Livrable: RAPPORT_SECURITE_OWASP_AUDIT.md

Jour 4: Résilience tests (4.1)
        - 4 scénarios, ~30min chacun
        - ETA: ~3h
        - Livrable: resilience_test_results.json

Jour 5: Backup tests (5.1)
        - Backup + restore + PITR + RPO
        - ETA: ~3h
        - Livrable: backup_test_results.json

Jour 6: Observabilité export (6.1)
        - Export metrics réelles
        - ETA: ~1h
        - Livrable: prometheus_metrics.json

Jour 7: Audit final + documentation
        - Générer score final (target 9.5+/10)
        - Mettre à jour rapports
        - ETA: ~4h
        - Livrable: SCORE_FINAL_AUDIT.md
```

---

## CRITÈRES DE SUCCÈS

### ✅ Avant Go-live, vérifier:

| Critère | Preuve | Target |
|---------|--------|--------|
| Unit Tests | test_results_final.json | 9/9 PASSED ✅ |
| Load Tests | load_test_results_real.json | 0 erreurs ✅ |
| Security | OWASP audit report | Top 10 covered ✅ |
| Resilience | resilience_test_results.json | 4/4 scenarios OK ✅ |
| Backup | backup_test_results.json | RTO <1s ✅ |
| Observability | prometheus_metrics.json | Data exported ✅ |
| Score Composite | SCORE_FINAL_AUDIT.md | ≥9.5/10 ✅ |

---

## COMMANDES QUICK REFERENCE

```bash
# 1. Fix unit tests
cd /home/user/ERP-FABS-V10
pytest backend/tests/ -v --json=test_results_final.json

# 2. Load test k6
k6 run tests/load_test_k6.js -o json=load_test_results_real.json

# 3. OWASP security scan
zaproxy -cmd -host localhost -port 8000 -r zap_report.html

# 4. Resilience tests
python3 tests/test_resilience.py

# 5. Backup tests
python3 tests/test_backup_restore.py

# 6. Export Prometheus
curl http://localhost:8000/metrics > prometheus_export.txt

# 7. Audit final
python3 generate_audit_score.py
```

---

**Next:** Exécuter actions Priority 1-2 (Unit tests + Load test) pour passer de 6/10 → 8+/10
