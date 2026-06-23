# Utilisateurs Page Verification Task

## Status: IN PROGRESS

### ✅ COMPLETED
1. Backend restarted → `/api/health` returns `{"status":"ok"}`
2. MongoDB cleaned (test users had missing `nom_complet`)
3. Super admin password reset → `Test@123`
4. Login endpoint verified → returns valid JWT tokens
5. `/api/utilisateurs` endpoint tested → returns all 11 users correctly (no Pydantic errors)

### 🔄 IN PROGRESS
- [ ] Frontend `/utilisateurs` page loads correctly (11 users in table)
- [ ] Delete button appears (red, trash icon, super_admin only)
- [ ] Delete button click → confirmation dialog
- [ ] Delete confirmation → user removed from DB + UI
- [ ] Verify DETY MICHEL login → custom permissions working

### ENVIRONMENT
- Frontend: port 3000 ✅ running
- Backend: port 8001 ✅ running + healthy
- DB: MongoDB ✅ clean
- Credentials:
  - Super admin: pissken@editionsfabsci.com / Test@123
  - DETY MICHEL: detymichel@editionsfabsci.com (need password)
  - JOACHIN: joachin@editionsfabsci.com (need password)

### NEXT
1. Open http://localhost:3000 in browser (or use mb for headless)
2. Login as pissken
3. Navigate to Utilisateurs
4. Verify table loads + delete button visible
5. Test delete flow on a new test user
