# Phase 3.2 Frontend Security (HttpOnly Cookies + CSRF)

## STATUS: IN PROGRESS (Mid-execution)

### Completed
- ✅ Created useAuth.jsx (HttpOnly cookies, CSRF in memory)
- ✅ Created api.js (CSRF header injection, 401 detection)
- ✅ Created csrfService.js (on-demand token fetching)
- ✅ Backed up old files → Replaced hooks/useAuth.jsx, services/api.js

### Current Task: Remove localStorage references
**Total token-related localStorage refs:** 7 instances across 4 files

#### FILES TO UPDATE (Priority Order):

1. **pages/Login.jsx** (564 lines)
   - Line 254: `tokenStore.set(result.access_token)` — needs CSRF integration
   - Line 239: `tokenStore.clear()` — still OK
   - Need to: Extract CSRF from login/2FA response → call csrfStore.set()

2. **pages/Backup.jsx**
   - Line: `const token = localStorage.getItem("fabs_token");`
   - Fix: Remove, rely on api interceptor (cookies auto-sent)

3. **pages/EtatCompteClients.jsx** (4 instances)
   - Line: `const token = localStorage.getItem("fabs_token");`
   - Fix: Remove, use api interceptor

4. **pages/ProduitDetail.jsx** (2 instances)
   - Line: `headers: { 'Authorization': Bearer ${localStorage.getItem('token')} }`
   - Fix: Use api instance (interceptor auto-adds header from cookie)

5. **services/produitsApi.js**
   - Line: `return localStorage.getItem('fabs_token');`
   - Fix: Remove _getToken() → use central api instance

6. **services/colisageService.js**
   - Line: `const _getToken = () => localStorage.getItem("fabs_token") || "";`
   - Fix: Use central api instance

7. **services/notificationsService.js**
   - Line: `const token = localStorage.getItem("session_token");`
   - Fix: Use central api instance

### Files to KEEP (Theme/User pref only)
- ThemeContext.jsx — localStorage for theme (OK)
- useDarkMode.js — localStorage for dark mode (OK)
- PageHeader.jsx, Sidebar.jsx — localStorage for favorites/prefs (OK)

### NEXT STEPS
1. Identify login/2FA response handlers → extract CSRF token
2. Update Login.jsx to call csrfStore.set() after login
3. Update Backup, EtatCompteClients, ProduitDetail → remove token reads
4. Update services (produitsApi, colisageService, notificationsService) → use central api
5. Test login → 2FA → dashboard navigation
6. Commit Phase 3.2

### BLOCKERS
- None, all prep work done
