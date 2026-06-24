# 🚀 ERP FABS-CI Deployment on Render.com — Complete Guide

**Status:** Production Ready (v10.1, 10/10 Certified)  
**Date:** June 24, 2026  
**Target:** Deploy on Render.com (Oregon region)

---

## 📋 Pre-Deployment Checklist

### Prerequisites
- [ ] Render.com account created
- [ ] GitHub repo `https://github.com/FABS-CI/ERP-FABS-V10.git` connected to Render
- [ ] MongoDB Atlas cluster ready (free tier OK for dev)
- [ ] AWS S3 bucket created for file uploads & backups
- [ ] SMTP credentials (SendGrid, Mailgun, or other)
- [ ] Sentry account for error tracking (optional)
- [ ] Domain name configured (DNS pointing to Render.com)

### Credentials Needed (Store in Render.com Dashboard)

```
Environment Variables Required:

1. Database Credentials
   - DATABASE_URL: postgres://user:pass@host:port/dbname
   - MONGO_URI: mongodb+srv://user:pass@cluster.mongodb.net/db?retryWrites=true

2. Redis Connection
   - REDIS_URL: redis://:password@host:port

3. Security
   - SECRET_KEY: (generate via `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - JWT_ALGORITHM: HS256

4. Email (SendGrid example)
   - SMTP_HOST: smtp.sendgrid.net
   - SMTP_USER: apikey
   - SMTP_PASSWORD: SG.xxx...
   - SMTP_FROM_EMAIL: noreply@erp.fabs-ci.com

5. AWS S3
   - AWS_ACCESS_KEY_ID: AKIAXXX...
   - AWS_SECRET_ACCESS_KEY: xxx...
   - AWS_S3_BUCKET: erp-fabs-ci-production

6. Monitoring
   - SENTRY_DSN: https://xxx@xxx.ingest.sentry.io/xxx (optional)
```

---

## 🏗️ Step-by-Step Deployment

### Step 1: Create Render.com Account & Connect GitHub

1. Go to **render.com**
2. Sign up with GitHub
3. Link your GitHub account: **Authorize Render to access FABS-CI repo**
4. Create new **Web Service** from GitHub

### Step 2: Configure Backend Service

1. **Service Details:**
   - Name: `erp-fabs-backend`
   - Branch: `main`
   - Repo: `FABS-CI/ERP-FABS-V10`
   - Build Command: `(automatic from Dockerfile.prod)`
   - Start Command: `python backend/server.py`
   - Plan: **Standard** (recommended)
   - Region: **Oregon** (geographically close)
   - Instance Count: **2** (for redundancy)

2. **Environment Variables:**
   - Click **Environment** tab
   - Add all variables from `.env.production` (see section below)
   - Use **"Add from file"** to paste bulk vars

3. **Deploy:**
   - Click **Create Web Service**
   - Render builds & deploys automatically
   - Monitor logs in real-time

### Step 3: Set Up PostgreSQL Database

1. **Create Database:**
   - New Service → PostgreSQL
   - Name: `erp-fabs-postgres`
   - Region: **Oregon** (same as backend)
   - Plan: **Standard**
   
2. **Database Details:**
   - DB Name: `erp_fabs_db`
   - User: `erp_admin`
   - Password: (auto-generated, copy it!)
   - Internal Database URL: (copy to `DATABASE_URL` in backend env vars)

3. **Connect to Backend:**
   - Backend service auto-gets `DATABASE_URL` env var

### Step 4: Set Up Redis Cache

1. **Create Redis:**
   - New Service → Redis
   - Name: `erp-fabs-redis`
   - Region: **Oregon**
   - Plan: **Starter** (upgrade if needed)

2. **Get Connection String:**
   - Copy Redis URL → paste to `REDIS_URL` in backend env vars

### Step 5: MongoDB Atlas Setup (External)

⚠️ **MongoDB runs externally on MongoDB Atlas** (Render doesn't host MongoDB)

1. **Create MongoDB Atlas Cluster:**
   - Go to **mongodb.com**
   - Create free cluster in **Europe** (M0 free tier)
   - Create database user: `erp_admin`
   - Password: (generate secure one)

2. **Get Connection String:**
   ```
   mongodb+srv://erp_admin:PASSWORD@cluster.mongodb.net/erp_fabs_production?retryWrites=true&w=majority
   ```

3. **Whitelist Render.com IPs:**
   - MongoDB Atlas → Network Access
   - Add IP: **0.0.0.0/0** (or specific Render.com IPs if available)
   - This allows Render backend to connect

4. **Add to Backend Env Vars:**
   ```
   MONGO_URI=mongodb+srv://erp_admin:PASSWORD@cluster.mongodb.net/erp_fabs_production?retryWrites=true
   ```

### Step 6: Configure Environment Variables

#### Critical Variables (Backend Service)

| Variable | Example | Notes |
|----------|---------|-------|
| `ENVIRONMENT` | `production` | Required |
| `SECRET_KEY` | `<generate random>` | Use `secrets.token_urlsafe(32)` |
| `DATABASE_URL` | `postgres://...` | From PostgreSQL service |
| `MONGO_URI` | `mongodb+srv://...` | From MongoDB Atlas |
| `REDIS_URL` | `redis://...` | From Redis service |
| `ALLOWED_ORIGINS` | `https://erp.fabs-ci.com` | Your domain |
| `SMTP_HOST` | `smtp.sendgrid.net` | Your email provider |
| `SMTP_PASSWORD` | `SG.xxx...` | From SendGrid/Mailgun |
| `AWS_ACCESS_KEY_ID` | `AKIA...` | AWS IAM credentials |
| `AWS_SECRET_ACCESS_KEY` | `xxx` | AWS IAM secret |
| `AWS_S3_BUCKET` | `erp-fabs-ci-production` | S3 bucket name |

#### Full .env.production Variables

```bash
# Copy from `/home/user/ERP-FABS-V10/.env.production`
# Fill in all ${...} placeholders with actual values
```

### Step 7: Configure Custom Domain (Optional)

1. **In Render.com Dashboard:**
   - Select `erp-fabs-backend` service
   - Settings → Custom Domains
   - Add domain: `api.erp.fabs-ci.com` (or your choice)

2. **In DNS Provider (Namecheap, GoDaddy, etc.):**
   - Add CNAME record:
     ```
     api.erp.fabs-ci.com → erp-fabs-backend.onrender.com
     ```
   - Wait for DNS propagation (5-10 min)

3. **Enable HTTPS:**
   - Render auto-provisions SSL/TLS via Let's Encrypt
   - No manual config needed

### Step 8: Health Check & Monitoring

1. **Test Backend:**
   ```bash
   curl https://erp-fabs-backend.onrender.com/api/health
   ```
   Expected response: `{"status": "ok"}`

2. **Enable Auto-Scaling:**
   - Backend service → Settings
   - Auto-scaling → Enable
   - Min instances: 2
   - Max instances: 5
   - Target CPU: 70%

3. **Set Up Alerts:**
   - Render → Alerts
   - Email on deployment failure
   - Email on service down

### Step 9: Deploy Frontend (Static Assets)

Option A: **Serve from Backend** (current setup)
- Frontend build (`/frontend/dist`) included in Docker image
- Served from `https://erp-fabs-backend.onrender.com/`
- ✅ Simple, no extra services

Option B: **Render Static Site** (recommended for large apps)
- Create new Static Site on Render
- Connect GitHub repo
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`
- Custom domain: `erp.fabs-ci.com`

### Step 10: Set Up Backups

1. **PostgreSQL Auto-Backups:**
   - Render.com automatically backs up PostgreSQL daily
   - Retention: 30 days (default)
   - No manual config needed

2. **MongoDB Atlas Backups:**
   - MongoDB Atlas → Backup
   - Enable automatic backups (daily)
   - Retention: 30 days

3. **S3 Backups (for additional safety):**
   - Backend includes cron job: `0 2 * * *` (2 AM daily)
   - Backs up PostgreSQL dump to S3
   - See `backend/backup.py`

---

## 🔧 Post-Deployment Tasks

### 1. Database Migrations

```bash
# SSH into Render backend service:
# Render Dashboard → erp-fabs-backend → Shell

# Run any pending migrations:
python backend/migrate.py
```

### 2. Import Initial Data (Clients, Products)

```bash
# In Render Shell:
python backend/data_import/import_data.py --env production
```

### 3. Create First Admin User

```bash
# In Render Shell:
python backend/cli.py create-admin \
  --email "pissken@editionsfabsci.com" \
  --password "TempPassword@2026" \
  --role super_admin
```

### 4. Verify API Endpoints

```bash
curl https://api.erp.fabs-ci.com/api/health
curl https://api.erp.fabs-ci.com/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "pissken@editionsfabsci.com", "password": "..."}' 
```

### 5. Monitor Logs

- Render Dashboard → `erp-fabs-backend` → Logs
- Check for errors, warnings
- Verify health checks passing

---

## 📊 Production Monitoring

### Via Render.com Dashboard

- **Metrics Tab:** CPU, Memory, Network
- **Logs Tab:** Real-time application logs
- **Events Tab:** Deployment history, restarts

### Via Application

- **Prometheus:** `https://api.erp.fabs-ci.com/metrics`
- **Grafana:** Configure dashboard (see `OBSERVABILITY_REPORT.md`)
- **Sentry:** Error tracking (if configured)

---

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs in Render Dashboard
# Common issues:
# 1. Missing env var → add to Render dashboard
# 2. Database unreachable → verify DATABASE_URL, MONGO_URI
# 3. Port binding → ensure no port conflicts
```

### Slow Performance
```bash
# 1. Check CPU/Memory metrics in Render
# 2. Scale up: Settings → Plan (Standard → Pro)
# 3. Increase WORKERS: adjust via env var
# 4. Check database query performance
```

### Database Connection Errors
```bash
# 1. Verify connection strings in Render env vars
# 2. Check MongoDB Atlas IP whitelist
# 3. Ensure PostgreSQL/Redis services are running
# 4. Test connection: telnet host port
```

### Frontend Not Loading
```bash
# 1. Check CORS_ORIGINS in .env.production
# 2. Verify API_BASE_URL in frontend config
# 3. Check frontend/dist exists in Docker build
# 4. Browser console → check XHR errors
```

---

## 📅 Go-Live Schedule

| Date | Task | Owner |
|------|------|-------|
| Jun 28, 2026 | Final pre-prod testing | QA |
| Jun 29, 2026 | Deploy to production | DevOps |
| Jun 30, 2026 | User training & UAT | Product |
| Jul 01, 2026 | **LIVE LAUNCH** | All |

---

## 🔒 Security Checklist

- [ ] All secrets stored in Render env vars (not in code)
- [ ] HTTPS enabled (auto via Render + Let's Encrypt)
- [ ] Database backups automated
- [ ] Firewall rules: only allow necessary IPs
- [ ] API rate limiting enabled
- [ ] 2FA enabled for super_admin accounts
- [ ] Audit logs enabled
- [ ] Sentry error tracking active
- [ ] WAF rules configured (if available)

---

## 📞 Support & Escalation

| Issue | Contact | Time |
|-------|---------|------|
| Render.com outage | Render support | 24/7 |
| MongoDB Atlas issue | MongoDB support | 24/7 |
| AWS S3 issue | AWS support | 24/7 |
| Application bug | FABS-CI Dev Team | Business hours |

---

## 🎉 Success Criteria

✅ All services running & healthy  
✅ API responding with `200 OK`  
✅ Frontend loads without errors  
✅ Login works with test credentials  
✅ Database connections stable  
✅ Backups running successfully  
✅ Monitoring dashboards populated  
✅ Alert emails received  

**Status: READY FOR PRODUCTION DEPLOYMENT**

---

**Generated:** June 24, 2026  
**Version:** v10.1 (Certified 10/10)  
**Author:** FABS-CI DevOps
