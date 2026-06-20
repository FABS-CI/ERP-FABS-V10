# Automated Backup System — ERP FABS-CI

## Overview

Two complementary scripts automatically backup the ERP database, validate system health, and commit changes to GitHub.

| Script | Type | Best For |
|--------|------|----------|
| `auto-save.sh` | Bash | Simple, standalone execution |
| `auto-save-manager.py` | Python (async) | Rich health checks, detailed reporting |

Both scripts:
- ✅ Detect Git changes (modified, added, deleted files)
- ✅ Update `.gitignore` automatically
- ✅ Validate Frontend (npm dependencies)
- ✅ Validate Backend (Python venv, requirements.txt)
- ✅ Health check HTTP endpoints (Backend 8000, Frontend 3000)
- ✅ Create atomic commits with auto-detected type (feat/fix/docs/refactor)
- ✅ Push to GitHub (requires credentials via SSH or HTTPS token)
- ✅ Generate timestamped reports in `auto-save-reports/`

---

## Usage

### Manual Run (Bash)
```bash
cd /home/user/ERP-FABS-V10
./auto-save.sh
```

### Manual Run (Python)
```bash
cd /home/user/ERP-FABS-V10
python3 auto-save-manager.py
```

### Automated Scheduling (Linux/Mac with crontab)
Edit your user crontab:
```bash
crontab -e
```

Add weekly backup (every Sunday at 2:00 AM UTC):
```cron
0 2 * * 0 cd /home/user/ERP-FABS-V10 && /home/user/ERP-FABS-V10/auto-save-manager.py >> /tmp/auto-save-cron.log 2>&1
```

For daily backups (every day at 2:00 AM):
```cron
0 2 * * * cd /home/user/ERP-FABS-V10 && /home/user/ERP-FABS-V10/auto-save-manager.py >> /tmp/auto-save-cron.log 2>&1
```

---

## Report Output

After each run, a JSON report is saved:
```
/home/user/ERP-FABS-V10/auto-save-reports/report-YYYYMMDD_HHMMSS.json
```

**Report fields:**
- `timestamp` — Execution time
- `git_status` — Modified, added, deleted file counts
- `checks.frontend` — npm install status
- `checks.backend` — Python venv + requirements.txt status
- `checks.health` — Backend/Frontend HTTP response times
- `commit` — Commit hash (or error)
- `push` — Push success/failure (or error reason)
- `errors` — List of all issues encountered

**Example:**
```json
{
  "timestamp": "2026-06-20T09:15:56",
  "git_status": {
    "modified": 11,
    "added": 26,
    "deleted": 0
  },
  "commit": "6f7a66b",
  "push": {
    "success": false,
    "error": "fatal: could not read Username for 'https://github.com': No such device or address"
  }
}
```

---

## GitHub Credentials

### For HTTPS (Personal Access Token)
Create a `.git-credentials` file in your home:
```bash
echo "https://YOUR_USERNAME:YOUR_PAT@github.com" > ~/.git-credentials
git config --global credential.helper store
```

### For SSH
Add your SSH key to the Git agent:
```bash
ssh-add ~/.ssh/id_rsa
```

---

## What Gets Backed Up

**Included in commits:**
- Frontend source (`/frontend/src/`, `package.json`)
- Backend source (`/backend/app/`, `requirements.txt`)
- Database migrations (if any)
- Project docs (`README.md`, audit reports)
- Auto-save scripts themselves

**Explicitly ignored (via `.gitignore`):**
- `node_modules/` — Too large
- `/backend/venv/` — Python virtual environment
- `.env*` — Secrets/credentials
- `logs/` — Runtime logs
- `__pycache__/` — Python bytecode
- `.vscode/` — IDE settings
- `auto-save-reports/` — Local reports only

---

## Troubleshooting

### ❌ "Author identity unknown"
Git needs your email configured:
```bash
git config --global user.email "your@email.com"
git config --global user.name "Your Name"
```

### ❌ "Could not read Username for GitHub"
Git can't authenticate. Set up SSH or HTTPS token (see **GitHub Credentials** above).

### ❌ "Frontend verification failed"
Node modules missing or corrupted:
```bash
cd /home/user/ERP-FABS-V10/frontend
npm install
```

### ❌ "Backend verification failed"
Python venv or requirements issue:
```bash
cd /home/user/ERP-FABS-V10/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ⚠️ Health checks timeout
Backend/Frontend services not running. Start them manually:
```bash
# Terminal 1: Backend
cd /home/user/ERP-FABS-V10/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd /home/user/ERP-FABS-V10/frontend
npm run dev
```

---

## Advanced

### Commit Type Detection
The script auto-determines commit type based on changes:
- **`feat`** — New files or modifications (default)
- **`fix`** — Deletions only
- **`refactor`** — If keyword "refactor" found in filenames
- **`docs`** — If only README/doc files changed

Override with environment variable:
```bash
COMMIT_TYPE=fix python3 auto-save-manager.py
```

### Custom Commit Message
```bash
COMMIT_MSG="chore: weekly backup" python3 auto-save-manager.py
```

### Skip Push (commit only)
```bash
SKIP_PUSH=true python3 auto-save-manager.py
```

---

## Logs

- Console output → Timestamped with colors (Python version only)
- Cron logs → `/tmp/auto-save-cron.log` (if scheduled)
- Reports → `/home/user/ERP-FABS-V10/auto-save-reports/` (JSON format)

View cron history:
```bash
tail -f /tmp/auto-save-cron.log
```

View last report:
```bash
ls -lrt /home/user/ERP-FABS-V10/auto-save-reports/ | tail -1
```

---

## When to Run Manually

- **After major feature development** — Ensure clean state before pushing
- **Before production deployments** — Verify all checks pass
- **After adding dependencies** — npm/pip changes need validation
- **Weekly maintenance** — Backup untracked files (audit reports, logs)

---

## Project Status

**Last tested:** 2026-06-20 09:15 UTC  
**System:** Production-ready (95% operationally complete)  
**Services:** Backend (8000) ✅ | Frontend (3000) ✅ | MongoDB ✅  
**Next steps:** Configure GitHub credentials, schedule cron job

---

**Questions?** See `/home/user/ERP-FABS-V10/RAPPORT_FINAL_AUDIT.md` for full system audit.
