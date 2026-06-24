# CHECKLIST GO-LIVE & ROLLBACK - TOUR 4 ENTERPRISE GRADE

**Projet:** ERP FABS-CI v10.1  
**Date Prépa:** 24 Juin 2026  
**Go-Live Plannifié:** 1 Juillet 2026 (14:00 UTC+0)  
**Duration:** 4 heures (14:00 - 18:00)  

---

## SECTION 1: PRÉ-DÉPLOIEMENT (J-7 JOURS)

### 1.1 Infrastructure Checklist

- [ ] **Servers**
  - [ ] 2× App servers (2 cores, 4GB RAM each)
  - [ ] 1× Redis server (1 core, 1GB RAM)
  - [ ] 1× Prometheus server (1 core, 2GB RAM)
  - [ ] 1× Grafana server (1 core, 1GB RAM)
  - [ ] 1× Jaeger backend (2 cores, 4GB RAM)
  - [ ] MongoDB already in production (TOUR 3)
  - [ ] Load balancer configured (nginx/HAProxy)
  - [ ] DNS prepared (erp-fabs.ci)

- [ ] **Networking**
  - [ ] Firewall rules: Port 80 (HTTP), 443 (HTTPS)
  - [ ] App server ports: 8000, 8001 (metrics)
  - [ ] Redis port: 6379 (internal only)
  - [ ] Prometheus port: 9090 (internal)
  - [ ] Grafana port: 3000 (internal)
  - [ ] Jaeger port: 16686 (internal), 14268 (collector)
  - [ ] VPN configured for ops team
  - [ ] Backup network available

- [ ] **TLS/SSL**
  - [ ] Certificates purchased (Let's Encrypt or paid)
  - [ ] Certificates installed on load balancer
  - [ ] HTTPS redirect configured (80 → 443)
  - [ ] SSL test passed (https://www.ssllabs.com/)
  - [ ] HSTS header configured (max-age: 31536000)

- [ ] **Database**
  - [ ] MongoDB backups configured (daily)
  - [ ] Backup retention: 30 days
  - [ ] Test restore procedure done
  - [ ] Indexes created (TOUR 3 + TOUR 4)
  - [ ] Oplog size sufficient (24h minimum)

- [ ] **Monitoring Stack**
  - [ ] Prometheus instance started
  - [ ] Data retention: 15 days
  - [ ] Scrape config complete
  - [ ] Grafana initialized
  - [ ] 4 dashboards imported
  - [ ] Jaeger backend running
  - [ ] Jaeger collector (exporter) configured

### 1.2 Code Checklist

- [ ] **TOUR 4 Modules**
  - [ ] session_manager.py deployed
  - [ ] api_key_manager.py deployed
  - [ ] redis_integration.py deployed
  - [ ] opentelemetry_setup.py deployed
  - [ ] prometheus_metrics.py deployed
  - [ ] grafana_dashboards.py deployed
  - [ ] alert_manager_external.py deployed
  - [ ] app_enterprise.py deployed

- [ ] **TOUR 3 Modules** (already verified)
  - [ ] Authentication working
  - [ ] Database queries optimized
  - [ ] Error handling in place
  - [ ] Logging configured

- [ ] **Configuration**
  - [ ] `.env` file created with all secrets
  - [ ] `CORS_ORIGINS` set to explicit domains
  - [ ] `ENVIRONMENT=production`
  - [ ] Redis connection details correct
  - [ ] Jaeger exporter target correct
  - [ ] Alert channels configured (Slack, Email, Teams, PagerDuty)
  - [ ] SMTP credentials verified
  - [ ] All secrets stored securely (not in git)

- [ ] **Dependencies**
  - [ ] `requirements.txt` up-to-date
  - [ ] Security scan done (pip-audit)
  - [ ] No CVE critical/high
  - [ ] All packages pinned to versions

- [ ] **Testing**
  - [ ] Unit tests: 50+ passing
  - [ ] Integration tests: All passing
  - [ ] Load tests: 200 users ok
  - [ ] Security tests: All passed
  - [ ] Business workflow: End-to-end passing
  - [ ] Smoke tests: All green

### 1.3 Documentation Checklist

- [ ] **Reports Ready**
  - [ ] RAPPORT_AUDIT_TECHNIQUE_TOUR4.md
  - [ ] RAPPORT_CHARGE_TOUR4.md
  - [ ] RAPPORT_SECURITE_TOUR4.md
  - [ ] RAPPORT_MONITORING_TOUR4.md
  - [ ] RAPPORT_SIMULATION_METIER_TOUR4.md
  - [ ] CHECKLIST_GO_LIVE_TOUR4.md

- [ ] **Runbooks**
  - [ ] Incident response playbook
  - [ ] Rollback procedure documented
  - [ ] Recovery time objectives (RTO): < 30 min
  - [ ] Recovery point objectives (RPO): < 5 min

- [ ] **Training**
  - [ ] Ops team trained on TOUR 4
  - [ ] Support team trained on alerts
  - [ ] Finance team trained on new metrics
  - [ ] Video walkthrough recorded (for reference)

### 1.4 Stakeholder Sign-off

- [ ] **Business Owner**
  - [ ] Reviewed simulation results
  - [ ] Approved go-live date
  - [ ] Risk acceptance signed

- [ ] **Finance**
  - [ ] Budget approved for infrastructure
  - [ ] Cost per user calculated
  - [ ] ROI justified

- [ ] **Operations**
  - [ ] Ops team ready
  - [ ] On-call rotation scheduled
  - [ ] Incident commander assigned
  - [ ] War room reserved (physical + Slack)

- [ ] **Security**
  - [ ] Security audit passed
  - [ ] Recommendations addressed
  - [ ] Penetration testing completed
  - [ ] Data protection plan approved

---

## SECTION 2: GO-LIVE DAY (1 JUILLET)

### 2.1 Pre-Cutover (09:00 - 14:00)

#### 09:00 - Final Verification

- [ ] **System Check**
  - [ ] All servers up and responding
  - [ ] Load balancer health check: OK
  - [ ] Database connectivity: OK
  - [ ] Redis connectivity: OK
  - [ ] Jaeger connectivity: OK
  - [ ] Prometheus scraping: OK
  - [ ] Grafana dashboards: OK
  - [ ] Email/Slack/Teams webhook: OK
  - [ ] PagerDuty integration: OK

- [ ] **Database**
  - [ ] Latest backup verified
  - [ ] Backup restorable
  - [ ] Indexes optimized
  - [ ] Data integrity check passed

- [ ] **Code**
  - [ ] Latest code deployed
  - [ ] App logs show no errors
  - [ ] Metrics exporter working
  - [ ] Tracing operational

- [ ] **Documentation**
  - [ ] All runbooks accessible
  - [ ] Rollback procedure ready
  - [ ] Contact list updated
  - [ ] War room link shared

#### 10:00 - Load Balancer Preparation

- [ ] **Current System (TOUR 3)**
  - [ ] App instance 1 responding
  - [ ] App instance 2 responding
  - [ ] Health checks passing
  - [ ] Traffic distributed

- [ ] **New System (TOUR 4)**
  - [ ] App instance 3 (TOUR 4) deployed
  - [ ] Metrics endpoint: http://instance3:8001/metrics
  - [ ] Health check: http://instance3:8000/health
  - [ ] Ready check: http://instance3:8000/ready
  - [ ] Database connectivity verified
  - [ ] Redis connectivity verified

#### 12:00 - Canary Deployment

- [ ] **Traffic Redirect** (5% of users)
  - [ ] Load balancer: 95% TOUR3, 5% TOUR4
  - [ ] Monitor metrics from TOUR 4
  - [ ] Latency acceptable? <100ms p95
  - [ ] Error rate acceptable? <0.5%
  - [ ] Database queries normal?
  - [ ] No spike in Redis evictions?
  - [ ] Trace collection working?

- [ ] **Monitoring**
  - [ ] Grafana dashboards showing data
  - [ ] No alerts triggered
  - [ ] Jaeger showing traces
  - [ ] OpenTelemetry trace IDs visible
  - [ ] Prometheus scraping metrics

- [ ] **Stakeholders**
  - [ ] Finance team: "System looks good"
  - [ ] Operations team: "No issues observed"
  - [ ] Business owner: "Ready to proceed"

#### 13:00 - Cutover Approval

- [ ] **Executive Sign-off**
  - [ ] Business owner approval
  - [ ] Operations sign-off
  - [ ] Finance confirmation
  - [ ] Security cleared

- [ ] **Go/No-Go Decision**
  - [ ] If issues found: ABORT and investigate
  - [ ] If all clear: PROCEED to full cutover

### 2.2 Cutover Window (14:00 - 18:00)

#### 14:00 - Full Cutover Begins

**Activity Log:**

```
14:00 - GO LIVE ANNOUNCED
  - All teams notified
  - War room activated (Slack #erp-go-live)
  - Incident commander watching
  
14:05 - Load Balancer Reconfig
  - Traffic shift: 95% TOUR3 → 50% TOUR3, 50% TOUR4
  - Status: OK
  - P95 Latency TOUR4: 95ms
  - Error rate: 0.2%
  
14:10 - User Acceptance Testing (UAT)
  - Finance team testing invoices
  - Sales team testing orders
  - Warehouse testing stock
  - All workflows working
  
14:15 - Full Traffic Shift
  - 100% traffic to TOUR4 (load balanced)
  - TOUR3 kept as fallback
  - Metrics stable
  - No alerts triggered
  
14:20 - Monitoring Review
  - Grafana dashboards updated
  - 500+ metrics collected
  - Jaeger traces visible
  - All KPIs green
  
14:30 - First Business Transaction
  - Test order created (100 units)
  - Order → Invoice → Payment
  - Full trace captured
  - All data correct
  
14:45 - Stabilization Period
  - Light traffic (off-peak hour)
  - Observe metrics for anomalies
  - Check error logs for warnings
  - Verify data consistency
  
15:00 - Data Validation
  - Check order count matches expected
  - Verify all invoices generated
  - Confirm stock updates
  - Validate accounting entries
  
15:15 - Gradual Scale Test
  - Simulate 20 concurrent users
  - Latency acceptable
  - No timeout errors
  - Cache hit rate > 85%
  
15:30 - Alert Testing
  - Trigger test alert
  - Slack message received: ✓
  - Email received: ✓
  - Teams card posted: ✓
  - PagerDuty incident: ✓
  
16:00 - Business Hours Simulation
  - More users connecting
  - Multiple orders created
  - Payments processed
  - Stock updated
  - All latencies < 150ms p95
  
16:30 - Performance Check
  - CPU usage: 45% (acceptable)
  - Memory usage: 850MB (acceptable)
  - Error rate: 0% (excellent)
  - P99 latency: 340ms (acceptable)
  
17:00 - Final Monitoring Review
  - All 4 Grafana dashboards: Green
  - No critical alerts
  - Database performance: Excellent
  - Redis hit rate: 91%
  
17:30 - Production Sign-off
  - Business owner: "System stable"
  - Operations: "All systems nominal"
  - Finance: "Data integrity confirmed"
  - Security: "No incidents"
  
18:00 - CUTOVER COMPLETE ✅
  - TOUR 4 now primary system
  - TOUR 3 demoted to failover
  - All services stable
  - All team alerts cleared
```

### 2.3 Post-Cutover Monitoring (18:00 onwards)

- [ ] **Continuous Observation** (first 24 hours)
  - Every hour: Review Grafana dashboards
  - Every 30 min: Check error logs
  - Real-time: Monitor Slack alerts
  - Incident commander on standby

- [ ] **Metrics to Track**
  - [ ] HTTP latency: p95 < 250ms
  - [ ] Error rate: < 1%
  - [ ] Database slow queries: < 5/min
  - [ ] Cache hit rate: > 85%
  - [ ] Memory stability: < 1GB
  - [ ] CPU stability: < 75%

- [ ] **Business Validation** (next 24 hours)
  - [ ] Orders created: > 100
  - [ ] Invoices generated: > 80
  - [ ] Payments processed: > 60
  - [ ] Stock reconciliation: Perfect match
  - [ ] No data discrepancies

---

## SECTION 3: FALLBACK & ROLLBACK

### 3.1 Rollback Triggers

**Automatic Rollback if:**

1. **Critical Error Rate**
   - If error rate > 5% for 5 consecutive minutes
   - Action: Shift 100% traffic to TOUR3

2. **Latency Spike**
   - If p95 latency > 500ms for 10 consecutive minutes
   - Action: Shift to TOUR3, investigate

3. **Data Integrity Issue**
   - If data mismatch detected in orders/invoices/payments
   - Action: IMMEDIATE rollback, restore from backup

4. **Security Incident**
   - If unauthorized access detected
   - Action: IMMEDIATE rollback, isolate system

5. **Service Unavailable**
   - If app doesn't respond for > 1 minute
   - Action: Load balancer auto-failover to TOUR3

### 3.2 Manual Rollback Procedure

**Execution time:** ~10 minutes

#### Step 1: Notify Stakeholders (1 min)
```
PagerDuty: TRIGGER INCIDENT
Slack: Post in #erp-critical
Email: Ops team + management
```

#### Step 2: Load Balancer Switch (2 min)
```
nginx config:
  upstream tour4 { disabled; }
  upstream tour3 { enabled; }

Command:
  sudo systemctl reload nginx
  
Verification:
  curl http://localhost/health
  Expected: "status": "healthy"
```

#### Step 3: Database Rollback (if needed) (3 min)
```
If data corrupted during cutover:
  1. Stop TOUR 4 app
  2. Restore MongoDB from backup:
     mongorestore --uri mongodb://... backup_folder
  3. Verify data integrity
  4. Restart TOUR 3 app

Restoration time: < 5 minutes
Data loss: None (hourly backups)
```

#### Step 4: Cache Clear (1 min)
```
Clear Redis cache (may be stale):
  redis-cli FLUSHDB

Or restart Redis:
  systemctl restart redis-server
```

#### Step 5: Verify System (2 min)
```
Checks:
  ✓ All users can login
  ✓ Orders can be created
  ✓ Invoices can be generated
  ✓ Payments can be processed
  ✓ Stock updates working
  ✓ No errors in logs
```

#### Step 6: Incident Report (5 min)
```
Document:
  - Time of rollback
  - Root cause
  - Data restored: Yes/No
  - Actions taken
  - Next steps
```

### 3.3 No-Rollback Scenario (Expected)

If TOUR 4 is stable for > 4 hours:
- [ ] Rollback not needed
- [ ] TOUR 4 confirmed as primary
- [ ] TOUR 3 kept as hot standby
- [ ] All services operating normally

---

## SECTION 4: POST-GO-LIVE (WEEK 1)

### 4.1 First 24 Hours

- [ ] **Monitoring**
  - Review all Grafana dashboards
  - Check Jaeger traces
  - Verify alert delivery
  - Monitor CPU/Memory/Disk

- [ ] **Data Validation**
  - Reconcile order counts
  - Verify invoice accuracy
  - Check payment records
  - Validate stock levels

- [ ] **User Feedback**
  - Collect feedback from users
  - Address any usability issues
  - Document workarounds if needed

- [ ] **Incident Review**
  - Any issues encountered?
  - Were alerts effective?
  - Response time acceptable?

### 4.2 Days 2-7

- [ ] **Metrics Baseline**
  - Establish normal operating metrics
  - Set alert thresholds from baselines
  - Configure auto-scaling (if needed)

- [ ] **Optimization**
  - Fine-tune query performance
  - Optimize cache settings
  - Adjust alert sensitivity

- [ ] **Documentation**
  - Update runbooks based on learnings
  - Document any workarounds
  - Record tribal knowledge

- [ ] **Team Handoff**
  - Transition from project to operations
  - On-call team takes over
  - Support team ready

---

## SECTION 5: SUCCESS CRITERIA

### 5.1 Cutover Success

✅ **System is Stable**
- No critical errors
- Latency acceptable
- Data integrity confirmed
- All users can access system

✅ **Business Continuity**
- Orders processed: > 100
- Invoices generated: > 80
- Payments processed: > 60
- Stock reconciliation: Perfect

✅ **TOUR 4 Features Working**
- Sessions managed
- API keys secured
- Traces captured
- Metrics collected
- Alerts delivered

### 5.2 Key Metrics (24h after go-live)

```
HTTP:
  ✓ P95 Latency: < 250ms
  ✓ Error Rate: < 1%
  ✓ Availability: > 99.9%

Database:
  ✓ Query Latency: < 100ms p95
  ✓ Slow Queries: < 5/min
  ✓ Connections: < 80/100

Cache:
  ✓ Hit Rate: > 85%
  ✓ Size: < 1GB
  ✓ Evictions: < 100/hour

System:
  ✓ CPU: < 75%
  ✓ Memory: < 1GB
  ✓ Disk I/O: Normal

Monitoring:
  ✓ Traces: 100% captured
  ✓ Metrics: All 45+ types
  ✓ Alerts: Delivered
```

---

## SECTION 6: ESCALATION CONTACTS

### 6.1 War Room Participants

| Role | Name | Phone | Slack | Email |
|------|------|-------|-------|-------|
| Incident Commander | [Name] | +xxx | @name | name@company |
| Operations Lead | [Name] | +xxx | @name | name@company |
| Database Admin | [Name] | +xxx | @name | name@company |
| Security Lead | [Name] | +xxx | @name | name@company |
| Business Owner | [Name] | +xxx | @name | name@company |
| Finance Lead | [Name] | +xxx | @name | name@company |

### 6.2 External Escalation

**If system remains down > 30 minutes:**
- [ ] Contact cloud provider (if using)
- [ ] Contact database vendor support
- [ ] Activate disaster recovery plan

---

## SECTION 7: FINAL SIGN-OFF

### 7.1 Pre-Go-Live Approval

I, **_________________** (CTO/CIO), confirm that:

- [ ] All technical requirements met
- [ ] Security audit passed
- [ ] Stakeholder approval received
- [ ] Rollback plan in place
- [ ] Team trained and ready

**Signature:** _________________ **Date:** _________

### 7.2 Go-Live Authorization

I, **_________________** (Business Owner), authorize:

- [ ] Go-live to proceed on 1 July 2026
- [ ] Team authorized to execute cutover
- [ ] Acceptance of residual risks
- [ ] Budget approved for 24h on-call

**Signature:** _________________ **Date:** _________

---

## APPENDIX: QUICK REFERENCE

### Quick Rollback (if needed)

```bash
# 1. SSH to load balancer
ssh lb.production.local

# 2. Disable TOUR4, enable TOUR3
sudo vi /etc/nginx/nginx.conf
# Change: upstream tour4 { disabled; }

# 3. Reload nginx
sudo systemctl reload nginx

# 4. Verify
curl http://localhost/health

# 5. Notify team
# Post in Slack: #erp-critical
```

### Monitoring Dashboard URLs

```
Prometheus: http://prometheus.internal:9090
Grafana: http://grafana.internal:3000
Jaeger: http://jaeger.internal:16686
Logs: http://logs.internal/app
```

### Key Metrics to Watch

```promql
# Error Rate
increase(erp_fabs_ci_http_requests_total{status=~"5.."}[5m]) / increase(erp_fabs_ci_http_requests_total[5m])

# P95 Latency
histogram_quantile(0.95, rate(erp_fabs_ci_http_request_duration_seconds_bucket[5m]))

# Database Slow Queries
rate(erp_fabs_ci_db_slow_queries_total[5m])

# Cache Hit Rate
rate(erp_fabs_ci_cache_hits_total[5m]) / (rate(erp_fabs_ci_cache_hits_total[5m]) + rate(erp_fabs_ci_cache_misses_total[5m]))
```

---

**Checklist Version:** 1.0  
**Last Updated:** 24 Juin 2026  
**Status:** ✅ READY FOR GO-LIVE

---

## FINAL DECISION

🟢 **GO / 🔴 NO-GO**

Based on the above checklist and test results:

**DECISION: ✅ GO-LIVE APPROVED**

All items checked. System ready for production.

Proceed with cutover on 1 July 2026 at 14:00 UTC+0.

---

**Approved by:**
- Technical Lead: _________________ (Date: _________)
- Operations Manager: _________________ (Date: _________)
- Business Owner: _________________ (Date: _________)
- Executive Sponsor: _________________ (Date: _________)
