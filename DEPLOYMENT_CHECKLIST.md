# TOUR 3: Production Deployment Checklist

Use this checklist before deploying ERP FABS V10 to production.

---

## Pre-Deployment Security

### Authentication & Secrets
- [ ] Change `JWT_SECRET` from default (use 32+ character random string)
- [ ] Set `SENTRY_DSN` for error tracking
- [ ] Configure `MONGODB_URI` with strong credentials
- [ ] Store all secrets in environment variables (not code)
- [ ] Rotate credentials every 90 days

### Network & Access
- [ ] MongoDB accessible only from app server (no public internet)
- [ ] API server behind reverse proxy (nginx/AWS ALB)
- [ ] CORS origins whitelist configured (not `*`)
- [ ] HTTPS/TLS enabled on all endpoints
- [ ] Firewall rules restrict port access (22, 8000 only)

### Environment Variables
```bash
ENV=production
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/fabs_ci?retryWrites=true&w=majority
JWT_SECRET=<generate-32-char-random-string>
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
```

---

## Database Setup

### Create Indexes
```python
from database_schema import SchemaOptimizer

# Connect to production MongoDB
from pymongo import MongoClient
client = MongoClient(MONGODB_URI)
db = client['fabs_ci']

# Create all indexes
for idx in SchemaOptimizer.get_all_indexes():
    print(f"Creating index: {idx.collection}.{idx.fields}")
    db[idx.collection].create_index(idx.fields)

print("✓ All indexes created")
```

### Verify Indexes
```bash
# Connect to MongoDB and run
db.collection_names()  # Should see all collections

# List indexes
db.utilisateurs.getIndexes()
db.clients.getIndexes()
db.products.getIndexes()
db.stock.getIndexes()
db.orders.getIndexes()
db.invoices.getIndexes()
db.payments.getIndexes()
db.audit_logs.getIndexes()
```

### Setup Backup Script
```bash
# Copy backup script
cp scripts/backup_mongodb.sh /opt/backups/

# Make executable
chmod +x /opt/backups/backup_mongodb.sh

# Add to cron (daily at 2 AM)
0 2 * * * /opt/backups/backup_mongodb.sh

# Test restore
/opt/backups/restore_mongodb.sh /backups/mongodb/fabs_ci-latest
```

### Enable Replication (HA)
If using MongoDB Replica Set:

```javascript
// On primary node
rs.initiate({
    _id: "erp_fabs_rs",
    members: [
        { _id: 0, host: "primary:27017", priority: 1 },
        { _id: 1, host: "secondary1:27017", priority: 0 },
        { _id: 2, host: "secondary2:27017", priority: 0 }
    ]
})

// Verify
rs.status()
```

---

## Application Deployment

### Build & Test
```bash
# Clone repo
git clone https://github.com/FABS-CI/ERP-FABS-V10.git
cd ERP-FABS-V10

# Install dependencies
pip install -r requirements.txt

# Run validation tests
python3 validate_tour_3.py

# Verify: Should see "10/10 tests passed"
```

### Start Application
```bash
# Using uvicorn with gunicorn workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/erp/access.log \
  --error-logfile /var/log/erp/error.log \
  backend.app_production:app

# Or using systemd (recommended)
systemctl start erp-fabs
systemctl enable erp-fabs  # Auto-start on reboot
```

### Verify Application Health
```bash
# Check health endpoint
curl -s http://localhost:8000/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "components": {
#     "mongodb": { "status": "healthy" },
#     "redis": { "status": "healthy" }
#   }
# }

# Check metrics
curl -s http://localhost:8000/metrics | jq .

# Check dashboard
curl -s http://localhost:8000/dashboard | jq .
```

---

## Monitoring & Observability

### Configure Sentry
```python
# In logging_config.py
SENTRY_DSN = "https://your-key@sentry.io/project-id"
```

### Setup Log Aggregation
Configure log collection to centralized service:

**Option 1: Syslog**
```bash
# Enable syslog handler
echo "*.* @syslog-server:514" >> /etc/rsyslog.d/30-erp.conf
```

**Option 2: ELK Stack**
```bash
# Ship logs to Elasticsearch
# Configure Filebeat to watch /var/log/erp/
```

**Option 3: Datadog/New Relic**
```bash
# Install agent
pip install datadog
# Configure in app_production.py
```

### Setup Prometheus Scraping
```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'erp-fabs'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Create Grafana Dashboards
Import premade dashboards or create:
- Request rate & latency
- Error rate
- Database performance
- Component health status
- Business metrics (invoices, payments)

---

## Testing Before Go-Live

### Unit Tests
```bash
python3 -m pytest backend/tests/ -v
# Should see: passed 28+ tests
```

### Integration Tests
```bash
# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Admin@2025"}'

# Test data endpoints
curl http://localhost:8000/api/clients
curl http://localhost:8000/api/products
curl http://localhost:8000/api/orders
```

### Load Testing
```bash
# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/api/clients

# Expected: Latency <100ms avg, >90% success rate
```

### Backup & Restore Test
```bash
# Create backup
/opt/backups/backup_mongodb.sh

# Restore to test database
/opt/backups/restore_mongodb.sh /backups/mongodb/latest

# Verify data integrity
mongosh fabs_ci
db.clients.countDocuments()
db.orders.countDocuments()
```

---

## Performance Tuning

### Database Connection Pool
```python
# In app_production.py
client = MongoClient(
    MONGO_URI,
    maxPoolSize=100,  # Increase if high concurrency
    minPoolSize=10,
    maxIdleTimeMS=45000
)
```

### FastAPI Workers
```bash
# Increase workers based on CPU cores
gunicorn -w <number-of-cpu-cores> \
  -k uvicorn.workers.UvicornWorker \
  backend.app_production:app
```

### Redis Caching (v10.1+)
```python
# When implemented
redis_client = Redis(host='localhost', port=6379, db=0)

# Cache frequently accessed data
@app.get("/api/products")
async def list_products(skip: int = 0):
    cache_key = f"products:{skip}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    # Fetch from DB and cache
```

---

## Monitoring Alerts

### Setup Alert Rules

**High Error Rate (>5%)**
```
Alert when: (http_errors_total / http_requests_total) > 0.05
Severity: High
Action: Page on-call engineer
```

**Database Connection Failed**
```
Alert when: mongodb health check returns false
Severity: Critical
Action: Immediate page (service down)
```

**High Response Time (>1s)**
```
Alert when: http_request_duration_ms p95 > 1000
Severity: Medium
Action: Notify DevOps team
```

**Low Disk Space**
```
Alert when: free disk < 10%
Severity: High
Action: Automatic cleanup of old backups
```

---

## Post-Deployment Validation

### Day 1
- [ ] Health check endpoint responding
- [ ] No errors in logs
- [ ] Database queries responsive
- [ ] All API endpoints accessible
- [ ] Authentication working

### Week 1
- [ ] Monitor error rate (should be <1%)
- [ ] Check database performance (no slow queries)
- [ ] Verify backups running successfully
- [ ] Review audit logs for any anomalies
- [ ] Test failover (if using replica set)

### Month 1
- [ ] Review performance trends
- [ ] Analyze user patterns
- [ ] Optimize slow endpoints
- [ ] Update indexes if needed
- [ ] Plan scaling if needed

---

## Rollback Procedure

If issues occur after deployment:

### Quick Rollback (Minutes)
```bash
# Stop current version
systemctl stop erp-fabs

# Restore from backup
/opt/backups/restore_mongodb.sh /backups/mongodb/pre-deployment

# Start previous version
git checkout v9.0
pip install -r requirements.txt
systemctl start erp-fabs
```

### Zero-Downtime Rollback (Blue-Green)
```bash
# Keep v9 running on 8000
# Deploy v10 on 8001
# Switch load balancer to 8001
# If issues, switch back to 8000
```

---

## Maintenance Tasks

### Daily
- [ ] Check health endpoint
- [ ] Review error logs
- [ ] Verify backup completed

### Weekly
- [ ] Test restore procedure
- [ ] Review performance metrics
- [ ] Check disk usage
- [ ] Review security logs

### Monthly
- [ ] Update dependencies (`pip install --upgrade`)
- [ ] Rotate credentials
- [ ] Review database statistics
- [ ] Optimize slow queries
- [ ] Capacity planning

### Quarterly
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Performance profiling
- [ ] Backup restore to new environment

---

## Emergency Contacts

- **On-Call Engineer:** [Name & Phone]
- **Database Administrator:** [Name & Phone]
- **Security Team:** [Name & Email]
- **Vendor Support:** [Service & Contact]

---

## Sign-Off

- [ ] DevOps Lead approved
- [ ] Security approved
- [ ] Product Manager approved
- [ ] Testing team approved

**Deployment Date:** __________  
**Deployed By:** __________  
**Verified By:** __________

---

**Last Updated:** 2026-06-24  
**Version:** TOUR 3 (10.0.0)
