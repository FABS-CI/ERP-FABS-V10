# ERP FABS-CI Backend Architecture Refactoring

**Status**: PHASE 3 (Code Quality Improvement)
**Goal**: Break monolithic modules into testable, reusable components

---

## PROBLEM: Monolithic Routers

### Before (Current)
```
rh_module.py (2321 lines)
├── list_employes()
├── create_employe()
├── update_employe()
├── delete_employe()
├── list_departements()
├── create_departement()
├── ... (50+ more functions)
└── ALL in 1 file, 1 router
```

**Issues**:
- ❌ Can't test list_employes without creating router
- ❌ Can't reuse employee enrichment logic
- ❌ No separation of concerns
- ❌ Impossible to maintain
- ❌ Hard to find bugs

### After (Proposed)

```
services/
├── __init__.py
├── employee_service.py      ← Employee business logic
├── command_service.py       ← Order business logic
└── stock_service.py         ← Inventory business logic

routers/
├── __init__.py
├── employees.py             ← Employee endpoints (split from rh_module)
├── departments.py           ← Department endpoints
├── functions.py             ← Function endpoints
├── contracts.py             ← Contract endpoints
├── attendance.py            ← Attendance endpoints
└── ... (split large modules)

optimization_utils.py         ← Shared (bulk query, pagination)
```

**Benefits**:
- ✅ Can test `EmployeeService.enrich_employee_with_relationships()` independently
- ✅ Can reuse employee enrichment in CLI, webhooks, etc.
- ✅ Clear separation: routing vs. business logic
- ✅ Easy to find and fix bugs
- ✅ Testable endpoints

---

## MIGRATION STRATEGY (TOUR 3-4)

### Phase 1: Extract Services (DONE)
- [x] Create `services/` directory
- [x] `employee_service.py` — Employee logic
- [x] `command_service.py` — Order logic
- [x] `stock_service.py` — Inventory logic

### Phase 2: Test Services
- [ ] Unit tests for each service
- [ ] Database mocking
- [ ] Validate logic works

### Phase 3: Create New Routers
- [ ] `routers/employees.py` — /employes endpoints
- [ ] `routers/commands.py` — /commandes endpoints
- [ ] `routers/stock.py` — /stock endpoints

### Phase 4: Migrate Endpoints One-by-One
- [ ] Move `list_employes()` to use EmployeeService
- [ ] Test with same inputs
- [ ] Verify identical outputs
- [ ] Deploy

### Phase 5: Deprecate Old Modules
- [ ] Keep old modules for fallback
- [ ] Gradually migrate all endpoints
- [ ] Delete old modules when 100% migrated

---

## IMPACT ON SCORES

### Code Quality
- **Before**: 3/10 (2321-line files)
- **After**: 7/10 (split into <500-line modules)

### Stability
- **Before**: 7/10 (hard to fix bugs)
- **After**: 8/10 (isolated, testable)

### Maintenance
- **Before**: Nightmare
- **After**: Straightforward

---

## QUICK MIGRATION: LIST_EMPLOYES

### Current (In rh_module.py)
```python
@router.get("/employes")
async def list_employes(...):
    # 80 lines of logic
    return [EmployeOut(**doc) for doc in docs]
```

### New (Using Service)
```python
# routers/employees.py
from services.employee_service import EmployeeService

@router.get("/employes")
async def list_employes(...):
    service = EmployeeService(db)
    
    # Fetch
    docs = await db.employes.find(filters).skip(skip).limit(limit).to_list(limit)
    
    # Enrich (service)
    docs = await service.enrich_employee_with_relationships(docs)
    
    return [EmployeOut(**doc) for doc in docs]
```

**Benefit**: Easy to test `service.enrich_employee_with_relationships()` without FastAPI

---

## FILE SIZE TARGETS

| File | Before | After | Status |
|------|--------|-------|--------|
| rh_module.py | 2321 | 500 | 🔄 In progress |
| commandes_module.py | 1863 | 500 | ⏳ Next |
| colisage_module.py | 2454 | 500 | ⏳ Next |
| stock_module.py | 1242 | 500 | ⏳ Next |
| factures_module.py | 1529 | 600 | ⏳ Next |

---

## TESTING STRATEGY

### Unit Tests (New)
```python
# tests/test_employee_service.py

async def test_enrich_employee_with_relationships():
    # Create test data
    docs = [{"employe_id": 1, "departement_id": "D1"}]
    
    # Mock database
    db_mock = MagicMock()
    db_mock.departements.find(...).to_list(None) = [{"departement_id": "D1", "nom": "IT"}]
    
    # Test service
    service = EmployeeService(db_mock)
    result = await service.enrich_employee_with_relationships(docs)
    
    # Verify
    assert result[0]["departement_nom"] == "IT"
```

### Integration Tests (Existing)
```python
# Tests use actual endpoints
GET /api/rh/employes
→ Uses routers/employees.py
→ Uses services/employee_service.py
→ Uses actual database
```

---

## ROLLOUT PLAN

### This Week
- [ ] Create services/ (DONE)
- [ ] Write unit tests for services
- [ ] Create routers/ (empty)
- [ ] Start migration with employee endpoints

### Next Week
- [ ] Complete employee router migration
- [ ] Migrate command router
- [ ] Test both with integration tests
- [ ] Keep old modules as backup

### Following Week
- [ ] Migrate remaining routers
- [ ] Delete old monolithic modules
- [ ] Final integration test

---

## RISKS & MITIGATIONS

| Risk | Mitigation |
|------|-----------|
| Break existing API | Keep old modules as fallback |
| Logic differences | Compare outputs before/after |
| Database issues | Test with mock + real DB |

---

## LONG-TERM BENEFITS

1. **Testability**: Each service can be unit tested
2. **Reusability**: Services usable from CLI, webhooks, etc.
3. **Maintenance**: Find and fix bugs faster
4. **Onboarding**: New devs understand code faster
5. **Performance**: Easier to optimize (isolated pieces)

---

## NEXT STEPS

1. Run `tests/test_employee_service.py`
2. Create `routers/employees.py`
3. Migrate one endpoint at a time
4. Verify no behavior changes
5. Deploy gradually

---

**Created**: 2026-06-24 (TOUR 3)
**Updated**: During refactoring
**Status**: Starting migration phase
