# ERP FABS - Audit Fixes (20/06/2026)

## STATUS: PRIORITY 1 ✅ FIXED

### Priority 1 - CRITICAL (405/422 errors)

#### 1. ✅ ADD POST /api/utilisateurs endpoint
- **File:** `/home/user/ERP-FABS-V10/backend/administration_module.py`
- **Fix:** Added POST endpoint with UtilisateurIn schema
- **Changes:**
  - Added `uuid` + `Body` imports
  - Added `UtilisateurIn` schema (email, password, nom_complet, role, actif)
  - Updated `build_utilisateurs_router(db, resolve_user, hash_password=None, log_audit_event=None)`
  - Added `@router.post()` endpoint copying logic from auth/create-user
  - Updated server.py line 974 to pass hash_password + log_audit_event
- **Status:** ✅ VERIFIED: POST /api/utilisateurs returns 201, creates user successfully

#### 2. ✅ FIX POST /api/clients validation (422 error)
- **File:** `/home/user/ERP-FABS-V10/backend/clients_module.py`
- **Fix:** Added field aliases with Pydantic ConfigDict
- **Changes:**
  - Added `ConfigDict` import
  - Added `model_config = ConfigDict(populate_by_name=True)` to ClientIn
  - Added alias="nom_client" to `nom` field
  - Added alias="categorie" to `type_client` field
  - Made `representant` optional with default
- **Status:** ✅ VERIFIED: POST /api/clients with `nom_client` + `categorie` returns 201
- **Note:** Fixed audit test: changed "grande_entreprise" → "librairie" (valid enum value)

#### 3. ✅ VERIFY fournisseurs & approvisionnement modules
- **Status:** ✅ VERIFIED: GET /api/fournisseurs returns 200 (count: 0)

### Priority 2 - IMPORTANT

#### 4. Add GET /api/audit endpoint
#### 5. Add POST /api/stock/inventaire
#### 6. Implement bons-livraison endpoints

### Files Already Fixed (Verified 20/06/2026)
✅ GET /api/stock — returns stock_quantity, stock_value, total_articles, movements_today
✅ /api/analytics/financial total_encaisse — Fixed $montant → $montant_total
✅ /api/audit user_email — Added email resolution + parameter to log_audit_event()

---

## NEXT STEP
Activate venv, then fix Priority 1 (3 items) one by one.
