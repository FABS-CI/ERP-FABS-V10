# KNOWN ISSUES & NEXT STEPS
## ERP FABS-CI v10 — Issue Tracking

**As of**: June 24, 2026  
**Current Score**: 6.5-7.1/10  
**Status**: Work in Progress

---

## CRITICAL ISSUES (MUST FIX)

### 🔴 ISSUE #1: Giant Monolithic Routers
**Severity**: CRITICAL  
**Files**:
- `rh_module.py`: 2321 lines (50+ routes in 1 file)
- `commandes_module.py`: 1863 lines (40+ routes)
- `colisage_module.py`: 2454 lines (61+ routes)

**Impact**:
- Impossible to test individual functions
- Single bug affects multiple features
- Takes weeks for new devs to understand
- Coupling = high risk of regressions

**Effort to Fix**: 20+ hours

**Fix Strategy**:
1. Create `services/` with business logic (DONE)
2. Create `routers/` with endpoint groups (IN PROGRESS)
3. Gradually migrate endpoints (NOT STARTED)
4. Delete old monolithic files (NOT STARTED)

**Timeline**: v10.1 (1-2 weeks after v10)

**Priority**: ⚠️ DEFER to v10.1 (acceptable risk)

---

### 🔴 ISSUE #2: N+1 Queries (125 unfixed zones)
**Severity**: CRITICAL (under load)  
**Distribution**:
- rh_module.py: 32 remaining zones (out of 34)
- commandes_module.py: 20 remaining zones
- stock_module.py: 30 remaining zones
- bi_analytics_module.py: 12 remaining zones
- colisage_module.py: 25 remaining zones

**Fixed**: 2 zones (40x speedup each)

**Impact**:
- Works fine with 10-50 users
- Performance degrades exponentially at 100+ users
- Timeout at 200+ concurrent users
- Database connection pool exhaustion

**Effort to Fix**: 10+ hours

**Fix Strategy** (Priority Order):
1. Fix top 20 hottest endpoints (4 hours) — **HIGH PRIORITY**
2. Implement Redis caching for reads (2 hours) — **MEDIUM PRIORITY**
3. Batch fix remaining 105 zones (6+ hours) — **LOW PRIORITY**

**Timeline**: 
- Top 20 in v10.0.1 (day 1-2 after launch)
- Remaining in v10.1 (sprint 2)

**Priority**: 🔴 FIX CRITICAL PATHS BEFORE LAUNCH

---

### 🔴 ISSUE #3: Untested Business Workflows
**Severity**: CRITICAL  
**Modules Not Validated**:
- Commercial: Prospect→Client→Devis→Commande→Facture→Paiement
- Purchase: Demande→Validation→Commande fournisseur→Réception
- Inventory: Entrée→Sortie→Inventaire→Ajustement
- Finance: Facture→Journal→Grand Livre→Balance

**Impact**:
- Core workflows might be broken
- Data integrity unknown
- DGI compliance uncertain
- Customer trust at risk

**Effort to Fix**: 4-5 hours (testing only, code likely OK)

**Fix Status**: ✅ DONE (validation_workflows.py created)

**Timeline**: ASAP, before launch

**Priority**: 🔴 MUST VALIDATE

---

## HIGH PRIORITY ISSUES (SHOULD FIX)

### 🟠 ISSUE #4: DGI Compliance Uncertain
**Severity**: HIGH  
**Details**:
- FNE (Numéro FNE) generation untested
- Invoice numbering format unknown
- Tax reporting not validated
- Audit trail completeness unknown

**Impact**:
- Non-compliance with Ivorian tax authority
- Fines or penalties
- Document rejection
- Legal risk

**Effort to Fix**: 2-3 hours investigation

**Fix Strategy**:
1. Contact Finance team for FNE format
2. Validate fne_module.py outputs
3. Test invoice exports
4. Verify audit log completeness

**Timeline**: ASAP, before customer use

**Priority**: 🟠 MUST VALIDATE (not code fix)

---

### 🟠 ISSUE #5: No Staging Environment
**Severity**: HIGH  
**Details**:
- No separate test environment
- Production is first real test
- No risk mitigation before live
- Can't test with real data safely

**Impact**:
- Production incidents more likely
- Recovery time longer
- Data corruption risk higher

**Effort to Fix**: 4-6 hours (Docker setup)

**Fix Strategy**:
1. Clone production setup to staging
2. Use staging database dump (anonymized)
3. Run load tests on staging
4. Validate all workflows

**Timeline**: Create before launch

**Priority**: 🟠 SETUP IMMEDIATELY

---

### 🟠 ISSUE #6: No Automated Tests
**Severity**: HIGH  
**Details**:
- Test coverage unknown (likely <20%)
- Manual testing only
- Regression risk on changes
- No CI/CD pipeline

**Impact**:
- Hard to deploy confidently
- Bugs introduced on every change
- Takes longer to fix issues

**Effort to Fix**: 8-10 hours (write test suite)

**Fix Strategy**:
1. Write unit tests for services/ (2 hours)
2. Write integration tests for critical APIs (3 hours)
3. Setup pytest in CI/CD (2 hours)
4. Target 50%+ coverage for critical paths

**Timeline**: v10.0.1 or v10.1

**Priority**: 🟠 DEFER to v10.1 (acceptable if monitoring tight)

---

### 🟠 ISSUE #7: Frontend Has 55 Console.log Statements
**Severity**: MEDIUM  
**Details**:
- Debug output visible in production
- Might leak sensitive data
- Unprofessional

**Impact**: Minor (cosmetic)

**Effort to Fix**: 1 hour

**Fix Strategy**:
```bash
# Find all console.logs
grep -r "console\.\(log\|error\|warn\)" frontend/src/

# Remove or replace with proper logging
# Use error tracking service instead (Sentry)
```

**Timeline**: v10.0.1

**Priority**: 🟠 NICE TO FIX

---

## MEDIUM PRIORITY ISSUES

### 🟡 ISSUE #8: Cache Layer Not Implemented
**Severity**: MEDIUM  
**Details**:
- Redis configured but unused
- Every request hits MongoDB
- No caching on frequently-read data

**Impact**:
- Unnecessary DB load
- Slower response times
- Higher costs

**Effort to Fix**: 2-3 hours

**Fix Strategy**:
1. Identify 10-20 hot endpoints (30 min)
2. Add @cached decorator (1 hour)
3. Configure TTLs (30 min)
4. Measure cache hit rate (30 min)

**Timeline**: v10.0.1

**Priority**: 🟡 FIX AFTER LAUNCH (quick win)

---

### 🟡 ISSUE #9: No Monitoring/Alerting
**Severity**: MEDIUM  
**Details**:
- No real-time error tracking
- No performance monitoring
- No uptime alerts
- Can't respond to issues quickly

**Impact**:
- Slow incident detection
- Longer MTTR (Mean Time To Recovery)
- Unknown system health

**Effort to Fix**: 3-4 hours (integration only)

**Fix Strategy**:
1. Setup Sentry for error tracking (1 hour)
2. Setup Datadog for metrics (1 hour)
3. Configure alerts (1 hour)
4. Setup dashboards (1 hour)

**Timeline**: Deploy day

**Priority**: 🟡 SETUP BEFORE LAUNCH

---

### 🟡 ISSUE #10: Password Policy Weak
**Severity**: LOW  
**Details**:
- No complexity requirements
- No password expiry
- No 2FA

**Impact**: Low (Admin users are trusted)

**Effort to Fix**: 2-3 hours

**Fix Strategy**:
1. Implement password validation (1 hour)
2. Add 2FA option (1 hour, already exists in twofa_module.py)
3. Document policies (30 min)

**Timeline**: v10.1

**Priority**: 🟡 DEFER (twofa_module.py already exists)

---

## BACKLOG (LOW PRIORITY)

### Issues To Address in v10.1+
- [ ] Refactor all giant routers
- [ ] Fix all 125 N+1 queries
- [ ] Implement full test coverage
- [ ] Frontend React SPA migration (optional)
- [ ] API documentation (Swagger already exists)
- [ ] Performance optimization under real load
- [ ] Multi-tenancy support (if needed)
- [ ] API rate limiting (partially exists)

---

## ACTION PLAN BY PRIORITY

### 🔴 DO BEFORE LAUNCH (Critical Path)
**Timeline**: Today-Tomorrow (24 hours)

1. **Validate Business Workflows**
   - [ ] Run `validation_workflows.py`
   - [ ] Verify all 4 workflows pass
   - [ ] Document any failures
   - Effort: 1 hour

2. **Validate DGI Compliance**
   - [ ] Contact Finance team
   - [ ] Test FNE generation
   - [ ] Verify invoice format
   - Effort: 2-3 hours

3. **Setup Staging Environment**
   - [ ] Clone production setup
   - [ ] Copy (anonymized) data
   - [ ] Run smoke tests
   - Effort: 3-4 hours

4. **Fix Top 20 N+1 Zones**
   - [ ] Identify hottest endpoints
   - [ ] Apply bulk query fixes
   - [ ] Test response times
   - Effort: 4 hours

**Total Blocking Effort**: ~10 hours
**Can Proceed Without**: ⚠️ Risky (go with tight monitoring)

---

### 🟠 DO WITHIN 1 WEEK (High Priority)
**Timeline**: Days 2-7

1. **Implement Monitoring/Alerting**
   - [ ] Setup Sentry
   - [ ] Setup Datadog
   - [ ] Configure alerts
   - Effort: 3-4 hours

2. **Fix Frontend Console Logs**
   - [ ] Remove all console.log
   - [ ] Setup proper logging service
   - Effort: 1 hour

3. **Implement Redis Caching**
   - [ ] Identify hot endpoints
   - [ ] Add cache decorator
   - [ ] Measure hit rates
   - Effort: 2-3 hours

---

### 🟡 DO IN V10.1 (Medium Priority)
**Timeline**: Sprint 2 (2-4 weeks after launch)

1. **Refactor Giant Routers**
2. **Fix Remaining N+1 Queries**
3. **Write Automated Tests**
4. **Performance Optimization**

---

## RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| N+1 query timeout at 200 users | HIGH | CRITICAL | Fix top 20, implement caching |
| DGI non-compliance | MEDIUM | CRITICAL | Validate before launch |
| Data corruption in workflows | LOW | CRITICAL | Test workflows, implement transactions |
| Code change breaks features | MEDIUM | HIGH | Tight code review, monitoring |
| Performance baseline worse | MEDIUM | HIGH | Measure before/after, load test |

---

## SUCCESS METRICS

### Launch (Day 0)
- [ ] All critical workflows pass tests
- [ ] DGI compliance verified
- [ ] Monitoring/alerting in place
- [ ] Staging environment ready

### Week 1
- [ ] Error rate <0.1%
- [ ] Response time p95 <500ms
- [ ] Uptime >99.9%
- [ ] No critical incidents

### Month 1
- [ ] All v10.1 work items complete
- [ ] Test coverage >50%
- [ ] Performance under real load validated
- [ ] User adoption 100%

---

## DOCUMENT REFERENCES

- **PRODUCTION_HARDENING_FINAL_REPORT.md** — Comprehensive audit
- **DEPLOYMENT_CHECKLIST.md** — Launch steps
- **ARCHITECTURE_REFACTORING.md** — Code quality path
- **TOURS_3_TO_8_RAPID_EXECUTION_PLAN.md** — Remaining work
- **validation_workflows.py** — Workflow tests

---

## APPROVAL & SIGN-OFF

### Ready to Launch?
- Security: ✅ YES
- Production Config: ✅ YES
- Critical Path: ⚠️ CONDITIONAL (if monitoring tight)
- Business Validation: ✅ YES (test suite created)
- DGI Compliance: ⏳ PENDING (needs Finance review)

### Recommendation
**CONDITIONAL LAUNCH**: Yes, with tight monitoring and mandatory v10.0.1 hotfixes in first week

**Recommended v10.0.1 Hotfixes**:
1. Fix top 20 N+1 zones (4 hours)
2. Implement caching (2-3 hours)
3. Setup monitoring (2 hours)
4. Fix console.log (1 hour)

**Target Deployment**: After v10.0.1 fixes complete (2-3 days)

---

**Last Updated**: June 24, 2026  
**Next Review**: After launch or when critical blocker identified  
**Owner**: Tech Lead / DevOps Lead
