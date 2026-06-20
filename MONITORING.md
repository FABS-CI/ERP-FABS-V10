# 📊 Monitoring - ERP FABS-CI Production

## Health Checks

### ✅ Backend Health
```bash
curl -X GET http://localhost:8000/health
```
**Expected:** 200 OK with system status

### ✅ Frontend Health
```bash
curl -X GET http://localhost:3000
```
**Expected:** 200 OK

### ✅ Database Health
```bash
mongo --eval "db.adminCommand('ping')"
```
**Expected:** `{ ok: 1 }`

---

## Key Metrics to Monitor

### 1. **API Performance**
- Response times for critical endpoints:
  - `GET /api/commandes` should be < 100ms
  - `POST /api/commandes` should be < 200ms
  - `GET /api/analytics/financial` should be < 500ms
  
### 2. **Database Health**
- MongoDB connection status
- Index efficiency (`db.setProfilingLevel(2)` to check slow queries)
- Disk space usage
- Replication lag (if applicable)

### 3. **Error Rates**
- Track 5xx errors in backend logs
- Monitor failed paiements processing
- Track failed facture generation

### 4. **Business Metrics**
- Total paiements encaissés (should match `GET /api/analytics/financial`)
- Factures pending (not yet paid)
- Order fulfillment rate

---

## Logs Location

### Backend Logs
```
/tmp/backend.log
```
Monitor for:
- `ERROR` entries
- Slow queries (> 1s)
- Failed API calls

### Frontend Logs
```
/tmp/frontend.log
```
Monitor for:
- JavaScript errors
- Failed API requests
- Memory leaks (check every 4 hours)

### Audit Logs
```
MongoDB: db.audit_logs
```
Query for security events:
```javascript
db.audit_logs.find({
  "action": {"$in": ["DELETE", "UPDATE"]},
  "timestamp": {"$gte": "2026-06-20T00:00:00"}
})
```

---

## Alert Rules

| Metric | Threshold | Action |
|--------|-----------|--------|
| Backend Response Time | > 2s | Page on-call |
| Error Rate | > 5% | Investigate logs |
| Database CPU | > 80% | Scale or optimize |
| Disk Usage | > 90% | Archive old logs |
| Failed Payments | > 10/hr | Alert commerce team |

---

## Weekly Check Checklist

- [ ] Review error logs for patterns
- [ ] Check database size and cleanup old logs
- [ ] Verify backup completion (`auto-save-reports/`)
- [ ] Monitor API response times
- [ ] Check audit logs for unauthorized access
- [ ] Verify all critical workflows (order → invoice → payment)

---

## Emergency Procedures

### If Backend is Down
1. Check logs: `tail -f /tmp/backend.log`
2. Verify database: `mongo --eval "db.adminCommand('ping')"`
3. Restart backend: `cd backend && python3 server.py`

### If Database is Corrupted
1. Stop backend
2. Restore from latest snapshot in `auto-save-reports/`
3. Restart backend

### If API is Slow
1. Check MongoDB indexes: `db.getCollection('factures').getIndexes()`
2. Profile slow queries: `db.setProfilingLevel(1)`
3. Optimize or rebuild indexes if needed

---

## Integration with External Monitoring (Optional)

You can integrate with services like:
- **Sentry** (error tracking): Configure in backend/server.py
- **Datadog** (infrastructure): Add monitoring agent
- **New Relic** (APM): Add instrumentation
- **PagerDuty** (alerting): Set up escalation policies

Example Sentry setup:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1
)
```

---

**Last Updated:** 2026-06-20
