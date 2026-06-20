# ✅ Production Deployment Checklist - ERP FABS-CI

**Date:** 2026-06-20  
**Version:** 1.0.0  
**Environment:** Production  

---

## Pre-Deployment (48 hours before)

- [ ] Code review complete
- [ ] All tests passing (`npm test` in frontend)
- [ ] Database migrations tested
- [ ] Backup strategy confirmed
- [ ] Team trained on new features
- [ ] Rollback plan documented (see section below)
- [ ] Communication plan sent (to FABS-CI team)

---

## Pre-Flight Checks (1 hour before)

### 1. Code Quality
- [ ] No console.logs in production code
- [ ] No hardcoded credentials
- [ ] .env files configured correctly
- [ ] Git repository clean (no uncommitted changes)

### 2. System Status
```bash
# Backend running
curl http://localhost:8000/health

# Frontend running
curl http://localhost:3000

# Database accessible
mongo --eval "db.adminCommand('ping')"

# Redis accessible (if used)
redis-cli ping
```

- [ ] Backend: 200 OK
- [ ] Frontend: 200 OK
- [ ] Database: { ok: 1 }

### 3. Database Integrity
```bash
# Check critical collections
mongo --eval "db.produits.countDocuments()"    # Should be 56
mongo --eval "db.factures.countDocuments()"    # Should be > 0
mongo --eval "db.paiements.countDocuments()"   # Should be > 0
```

- [ ] Produits count: 56 ✓
- [ ] Factures count: > 0 ✓
- [ ] Paiements count: > 0 ✓

### 4. API Endpoints (Critical)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/stock
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/analytics/financial
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/commandes
```

- [ ] GET /api/stock returns 200 with stock_quantity
- [ ] GET /api/analytics/financial returns total_encaisse > 0
- [ ] GET /api/commandes returns list of orders

### 5. Critical Workflows
- [ ] Create Command: OK
- [ ] Submit Command: OK (status changes to submitted)
- [ ] Validate Command: OK (status changes to validated)
- [ ] Generate Facture: OK
- [ ] Record Payment: OK
- [ ] View Audit Logs: OK (user_email populated)

---

## Deployment Steps

### Step 1: Database Backup
```bash
# Create snapshot before deployment
mongodump --db fabsci_erp --out /tmp/erp_backup_$(date +%Y%m%d_%H%M%S)
```
- [ ] Backup created successfully
- [ ] Backup size: _____ MB

### Step 2: Git Tag Release
```bash
cd /home/user/ERP-FABS-V10
git tag -a release-1.0.0 -m "Production release: fixes stock endpoint, total_encaisse, audit logging"
git push origin release-1.0.0
```
- [ ] Tag created: release-1.0.0
- [ ] Tag pushed to GitHub

### Step 3: Backend Deployment
```bash
# If using Docker (optional)
docker build -t fabs-erp:1.0.0 .
docker run -d --name erp-prod -p 8000:8000 fabs-erp:1.0.0

# Or restart Python server
pkill -f "python.*server.py"
cd backend && python3 server.py &
```
- [ ] Backend restarted
- [ ] No errors in logs

### Step 4: Frontend Deployment
```bash
# If using Docker (optional)
docker build -t fabs-ui:1.0.0 ./frontend
docker run -d --name ui-prod -p 3000:3000 fabs-ui:1.0.0

# Or restart Node server
pkill -f "node.*vite"
cd frontend && npm run build && npm run preview &
```
- [ ] Frontend restarted
- [ ] No build errors

### Step 5: Verify Deployment
```bash
# Test all critical endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```
- [ ] Backend responding
- [ ] Frontend responding
- [ ] No 500 errors in logs

---

## Post-Deployment (1 hour after)

### 1. Smoke Tests
- [ ] Can log in with pissken@editionsfabsci.com
- [ ] Dashboard loads (< 2s)
- [ ] Can create a new command
- [ ] Can view analytics
- [ ] Can view audit logs
- [ ] Stock endpoint returns data

### 2. Data Validation
```javascript
// Check key metrics haven't changed unexpectedly
db.factures.countDocuments()   // Should match pre-deployment
db.paiements.countDocuments()  // Should be >= pre-deployment
```
- [ ] Factures count stable
- [ ] Paiements count stable
- [ ] No data corruption

### 3. Performance Check
- [ ] Page load time: < 3s
- [ ] API response time: < 500ms
- [ ] No memory leaks (check process memory)

### 4. Team Notification
- [ ] Notify FABS-CI team: deployment successful
- [ ] Provide release notes
- [ ] Provide contact info for issues

---

## Rollback Plan (If Issues)

### Automatic Rollback (< 30 min post-deployment)
```bash
# Stop new version
pkill -f "python.*server.py"
pkill -f "node.*vite"

# Restore from backup
mongorestore --db fabsci_erp /tmp/erp_backup_YYYYMMDD_HHMMSS

# Revert to previous Git tag
git reset --hard release-0.9.9  # (previous stable version)

# Restart backend/frontend with previous version
cd backend && python3 server.py &
cd frontend && npm run preview &
```

### Manual Rollback (if automatic fails)
1. Restore MongoDB dump manually
2. Checkout previous release tag
3. Rebuild and restart services
4. Verify all systems online

---

## Success Criteria

✅ Deployment is successful if:
- All API endpoints return 200 OK
- No 5xx errors in logs within 1 hour
- All critical workflows complete without errors
- User can log in and view dashboard
- Audit logs capture actions with user_email
- Stock endpoint returns data

❌ Rollback if:
- Any critical endpoint returns 500+
- Database corruption detected
- > 10 errors in logs within 5 minutes
- User cannot log in
- Workflows fail (order → facture → payment)

---

## Contacts

- **On-Call Engineer:** [Your name] - [Phone] - [Email]
- **Database Admin:** [Name] - [Contact]
- **FABS-CI Project Manager:** Luci Ma - Ivory Coast

---

## Lessons Learned / Notes for Next Deployment

(To be filled after deployment)

- 
- 
- 

---

**Deployment Status:** ⚪ Pending  
**Deployed At:** ______________  
**Deployed By:** ______________  
**Verified By:** ______________  

---

*Last Updated: 2026-06-20*
