# FABS ERP Deployment — Progress Log

## Current Session [2026-06-19 10:16 UTC]

### ✅ Done
1. **Redis** — Running, connected
2. **Backend fixes** — Pydantic tolerant to bad docs, seed_factures robust
3. **Security** — .env (600 perms), JWT strong, SUPER_ADMIN_PASSWORD, ENVIRONMENT=production
4. **Frontend** — npm dev server on port 3000 (stable)
5. **Deps installed** — gunicorn, pymongo, motor, redis, fastapi, all requirements.txt
6. **.env created** — From backend/env.example, with JWT_SECRET, CORS_ORIGINS, admin creds
7. **pm2 running** — Daemon alive, ecosystem.config.js points to start_gunicorn.sh
8. **Backend boot** — Gunicorn 4 workers spawning (logs show "Started server process" 3020-3023, Redis ready)

### 🔄 In Progress
- **Backend binding**: Port 8000 not listening yet. Gunicorn processes alive but workers may still be initializing (MongoDB seed_factures running in background?)
- **Tests**: Need to run once backend is fully up

### ⏭️ Next
1. Wait for port 8000 to bind (seed/indexes may be slow)
2. Run full test suite (`pytest backend/tests/`)
3. Commit all changes + push every 3 min (auto_commit.sh daemon running)
4. Monitor stability

### ⚙️ Key Commands
```bash
pm2 status                          # Check backend process
pm2 logs erp-backend --nostream     # View logs
curl http://localhost:8000/health   # Health check
python -m pytest backend/tests/ -v  # Test suite
```

### 📝 Notes
- Gunicorn uvicorn workers reading from backend/server.py (not main.py)
- Auto-commit every 3 min to git (if changes exist)
- pm2 config: /home/user/ERP-FABS-V10/ecosystem.config.js
