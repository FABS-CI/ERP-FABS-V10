# 🚀 Render.com Deployment — Quick Start (5 min)

## Phase 1: Setup (10 minutes)

```bash
# 1. Create Render.com account
# 2. Connect GitHub: https://github.com/FABS-CI/ERP-FABS-V10

# 3. Create PostgreSQL service:
#    Name: erp-fabs-postgres
#    Plan: Standard
#    Region: Oregon
#    → Copy DATABASE_URL

# 4. Create Redis service:
#    Name: erp-fabs-redis
#    Plan: Starter
#    → Copy REDIS_URL

# 5. Create MongoDB cluster:
#    → MongoDB Atlas (external)
#    → Copy MONGO_URI
```

## Phase 2: Environment Setup (5 minutes)

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Create .env.production with all variables (see template below)
```

## Phase 3: Deploy Backend (2 minutes)

```bash
# In Render.com Dashboard:
# 1. New Web Service
# 2. Select: FABS-CI/ERP-FABS-V10
# 3. Branch: main
# 4. Build: Dockerfile.prod (auto-detected)
# 5. Region: Oregon
# 6. Plan: Standard
# 7. Add Environment Variables (see Phase 2)
# 8. Click "Create Web Service"
```

**Status:** Auto-deployed via GitHub webhook  
**URL:** `https://erp-fabs-backend.onrender.com`

## Phase 4: Verify Deployment (1 minute)

```bash
# Test health check
curl https://erp-fabs-backend.onrender.com/api/health

# Expected response:
# {"status": "ok"}
```

---

## 🔑 Essential Environment Variables

Paste these into Render.com dashboard:

```
# Core
ENVIRONMENT=production
SECRET_KEY=<generated-above>
DEBUG=False

# Database
DATABASE_URL=<from-postgresql-service>
MONGO_URI=<from-mongodb-atlas>
REDIS_URL=<from-redis-service>

# Security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://erp.fabs-ci.com

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
SMTP_FROM_EMAIL=noreply@erp.fabs-ci.com

# AWS S3
AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
AWS_S3_BUCKET=erp-fabs-ci-production

# Monitoring
PROMETHEUS_ENABLED=True
GRAFANA_ENABLED=True

# Timezone
TZ=Africa/Abidjan
```

---

## ✅ Post-Deploy Checklist

```bash
# 1. Health check
curl https://erp-fabs-backend.onrender.com/api/health

# 2. Test login
curl -X POST https://erp-fabs-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "pissken@editionsfabsci.com", "password": "Admin@2025"}'

# 3. Check logs
# → Render Dashboard → Logs tab

# 4. Monitor metrics
# → Render Dashboard → Metrics tab
```

---

## 📊 Architecture

```
GitHub (main branch)
    ↓
Render.com (webhook triggered)
    ↓
Build: Dockerfile.prod
    ↓
Services:
├─ Backend (FastAPI) → erp-fabs-backend
├─ PostgreSQL (managed)
├─ Redis (managed)
└─ MongoDB (Atlas external)
    ↓
HTTPS: erp-fabs-backend.onrender.com
```

---

## 🔧 If Something Goes Wrong

### Service won't start?
```bash
# Check logs in Render Dashboard
# Common issues:
# 1. Missing env var → add to dashboard
# 2. DB unreachable → verify DATABASE_URL
# 3. Port conflict → Render uses port 8002 by default
```

### Slow performance?
```bash
# 1. Upgrade plan: Settings → Standard → Pro
# 2. Check database: Render → PostgreSQL → Metrics
# 3. Scale workers: Increase WORKERS env var
```

### Need to rollback?
```bash
# Render Dashboard → Deployments → select previous → Deploy
```

---

## 📞 Support

| Issue | Link |
|-------|------|
| Render.com Docs | https://render.com/docs |
| API Reference | https://render.com/docs/api |
| Status | https://status.render.com |
| Slack Support | Render Community Slack |

---

## 🎯 Success Indicators

✅ Service running (green status)  
✅ Health endpoint responding  
✅ Users can login  
✅ API latency < 2s  
✅ Error rate < 0.1%  
✅ Backups running  

---

**Time to Deploy:** ~20 minutes  
**Confidence Level:** 10/10 ✅  
**Version:** v10.1 Production Ready  

🚀 **Ready to go live!**
