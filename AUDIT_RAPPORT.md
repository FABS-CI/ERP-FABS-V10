# Rapport d'Audit ERP FABS-CI V10
## Audit Pré-Production — Éditions FABS CI

**Date :** 16 juin 2026  
**Auteur :** Audit technique Runable AI  
**Version :** 1.0 — Final  
**Périmètre :** Code source complet + base de données live (MongoDB) + analyse statique

---

## Résumé Exécutif

L'ERP FABS-CI V10 **n'est pas prêt pour la mise en production** dans son état actuel. Le système présente **6 vulnérabilités critiques** dont deux pouvant compromettre la totalité du système : des credentials MongoDB et Redis ont été exposés dans l'historique Git public (commit `aaff545`), et tous les comptes désactivés peuvent encore s'authentifier. Le stock peut devenir négatif suite à un bug de calcul dans les bons de livraison.

**Score global : 52/100** (seuil production recommandé : 75/100)

> **Recommandation :** Bloquer la mise en production. Corriger les 6 findings CRITIQUE et les 5 findings ÉLEVÉS avant toute exposition publique. Délai estimé : 10-14 jours ouvrés pour un développeur expérimenté.

---

## Scores par Domaine

![Scores par domaine](/home/user/audit-fabs.report/scores_domaines.png)

| Domaine | Score | Statut |
|---|---|---|
| Métier / Workflows | 72/100 | ⚠️ Passable |
| Qualité du code | 68/100 | ⚠️ Passable |
| RBAC / Authentification | 55/100 | ❌ Insuffisant |
| Sécurité applicative | 42/100 | ❌ Critique |
| Performance / Base de données | 35/100 | ❌ Critique |
| DevOps / Production-readiness | 30/100 | ❌ Bloquant |

**Score global pondéré : 52/100**

---

## Synthèse des Findings

![Distribution des findings](/home/user/audit-fabs.report/findings_distribution.png)

**Total : 21 findings** — 6 Critiques · 5 Élevés · 6 Moyens · 4 Faibles

---

## FINDINGS CRITIQUES (6)

> Ces issues bloquent impérativement la mise en production.

---

### C1 — Secrets exposés dans l'historique Git public

**Sévérité :** 🔴 CRITIQUE  
**Fichier :** `.git/history` → commit `aaff545`  
**Statut :** Non corrigé (le commit existe toujours dans l'historique)

**Description :**  
Les credentials de connexion MongoDB et Redis ont été commités en clair dans le fichier `.env` et sont accessibles dans l'historique Git public sur GitHub :

```
MONGO_URL=mongodb://fabsci_app:FabsCI_App_2026!@<host>:27017/fabsci_erp?authSource=fabsci_erp
REDIS_URL=redis://:FabsCI_Redis_2026!@<host>:6379
```

Un attaquant ayant accès au repo peut se connecter directement à la base de données et extraire/détruire l'intégralité des données (1014 clients, toutes les factures, transactions).

**Preuve :** `git show aaff545 -- .env` révèle les secrets.

**Correction requise :**
1. Révoquer et changer immédiatement tous les mots de passe MongoDB et Redis
2. Purger l'historique Git (`git filter-branch` ou `BFG Repo-Cleaner`)
3. Activer GitHub Secret Scanning
4. Vérifier que `.env` est bien dans `.gitignore`

---

### C2 — Comptes désactivés peuvent s'authentifier (authN bypass)

**Sévérité :** 🔴 CRITIQUE  
**Fichiers :** `fournisseurs_module.py`, `approvisionnement_module.py` (et potentiellement d'autres)  
**Statut :** Non corrigé

**Description :**  
La fonction locale `resolve_user()` dans ces modules décode le JWT et retourne l'utilisateur **sans vérifier** si `actif=False` en base de données. Un utilisateur dont le compte a été désactivé peut continuer à s'authentifier indéfiniment tant que son JWT n'a pas expiré.

```python
# Code actuel — VULNÉRABLE
async def resolve_user(request, authorization=None):
    payload = jwt.decode(token, SECRET, algorithms=['HS256'])
    user_id = payload.get('user_id')
    return {"user_id": user_id, "role": payload.get('role', 'user')}
    # ← AUCUNE vérification actif=False en DB
```

La fonction `resolve_user` centrale dans `server.py` vérifie correctement `actif`, mais ces modules ont leur propre copie locale qui ne le fait pas.

**Correction :**
```python
async def resolve_user(request, authorization=None):
    payload = jwt.decode(token, SECRET, algorithms=['HS256'])
    user_id = payload.get('user_id')
    db = request.app.state.db
    user_doc = await db.users.find_one({"user_id": user_id})
    if not user_doc or not user_doc.get("actif", True):
        raise HTTPException(status_code=401, detail="Compte désactivé ou introuvable")
    return {"user_id": user_id, "role": payload.get('role', 'user')}
```

---

### C3 — Endpoint `/health` public expose l'infrastructure interne

**Sévérité :** 🔴 CRITIQUE  
**Fichier :** `server.py` ligne ~883  
**Statut :** Non corrigé

**Description :**  
L'endpoint `GET /api/health` est accessible sans aucune authentification. Il expose :
- L'état de connexion MongoDB et Redis
- Le nombre de collections en base
- Les erreurs internes en cas de problème

```json
{
  "status": "healthy",
  "checks": {
    "mongodb": {"status": "connected"},
    "redis": {"status": "connected"},
    "collections": {"status": "ok", "count": 41}
  }
}
```

Ces informations aident un attaquant à cartographier l'infrastructure et à identifier les services actifs.

**Correction :** Restreindre l'accès à `super_admin` ou réduire la réponse publique à `{"status": "ok"}` sans détails internes.

---

### C4 — Upload de fichiers sans validation (exécution arbitraire possible)

**Sévérité :** 🔴 CRITIQUE  
**Fichier :** `file_storage_module.py` ligne ~130  
**Statut :** Non corrigé

**Description :**  
L'endpoint d'upload ne valide pas :
- Le type MIME réel du fichier (seul `file.content_type` est lu, facilement falsifié)
- L'extension du fichier
- La taille maximale

Un attaquant avec accès peut uploader un script Python/Shell et potentiellement obtenir une exécution de code si le répertoire de stockage est accessible via le web.

```python
# Code actuel — DANGEREUX
with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)
# ← Aucune validation d'extension, type ou taille
```

**Correction :**
```python
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.docx', '.csv'}
ALLOWED_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png', ...}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ext = Path(file.filename).suffix.lower()
if ext not in ALLOWED_EXTENSIONS:
    raise HTTPException(400, f"Extension non autorisée: {ext}")
content = await file.read()
if len(content) > MAX_FILE_SIZE:
    raise HTTPException(413, "Fichier trop volumineux (max 10 MB)")
```

---

### C5 — Injection NoSQL / ReDoS via paramètre `q` non échappé

**Sévérité :** 🔴 CRITIQUE  
**Fichiers :** `commandes_module.py` (l.344-348), `factures_module.py` (l.372-376), `bons_livraison_module.py` (l.129-133)  
**Statut :** Non corrigé

**Description :**  
Le paramètre de recherche `q` est injecté directement dans des opérateurs MongoDB `$regex` sans échappement :

```python
# Code actuel — VULNÉRABLE
{"$or": [
    {"reference": {"$regex": q, "$options": "i"}},
    {"client_nom": {"$regex": q, "$options": "i"}},
    ...
]}
```

**Impact 1 — ReDoS :** Un regex catastrophique comme `q=(a+)+$` peut bloquer le thread event loop Python pendant plusieurs secondes → déni de service.

**Impact 2 — Injection NoSQL :** Selon la version MongoDB, certains patterns peuvent contourner des filtres.

**Correction :**
```python
import re
def escape_regex(q: str) -> str:
    return re.escape(q)

# Usage
safe_q = escape_regex(q)
{"reference": {"$regex": safe_q, "$options": "i"}}
```

---

### C6 — Bug stock : décrémentation sans garde → stock négatif

**Sévérité :** 🔴 CRITIQUE  
**Fichier :** `bons_livraison_module.py` ligne ~255  
**Statut :** Non corrigé

**Description :**  
Lors de la livraison d'un bon de livraison, le stock est décrémenté via `$inc` sans garde-fou :

```python
# Code actuel — BUGUÉ
stock_apres = max(0, stock_avant - _qte)  # ← utilisé seulement pour le LOG
await db.produits.update_one(
    {"product_id": ligne["produit_id"]},
    {"$inc": {"stock_actuel": -_qte}}  # ← DÉCRÉMENTE SANS LIMITE
)
```

Le calcul `max(0, ...)` est appliqué uniquement pour le log du mouvement, **pas pour l'opération `$inc` réelle**. Si `stock_avant = 5` et `_qte = 10`, le stock en base devient `-5`.

**Correction :**
```python
# Option 1 : Ajouter une condition
if stock_avant < _qte:
    raise HTTPException(400, f"Stock insuffisant pour {ligne['produit_id']}: {stock_avant} < {_qte}")

# Option 2 : findOneAndUpdate avec filtre atomique
result = await db.produits.find_one_and_update(
    {"product_id": ligne["produit_id"], "stock_actuel": {"$gte": _qte}},
    {"$inc": {"stock_actuel": -_qte}},
    return_document=True
)
if not result:
    raise HTTPException(400, "Stock insuffisant")
```

---

## FINDINGS ÉLEVÉS (5)

---

### E1 — RBAC : `directeur_general` aveugle sur 10 modules critiques

**Sévérité :** 🟠 ÉLEVÉE  
**Fichier :** `rbac_constants.py`  
**Statut :** Non corrigé

**Description :**  
Le rôle `directeur_general` a `level=0` (aucun accès) sur les modules suivants :

| Module | Niveau DG actuel | Niveau recommandé |
|---|---|---|
| `comptabilite` | 0 (aucun) | 1 (lecture) |
| `comptabilite_avancee` | 0 | 1 |
| `bi_analytics` | 0 | 1 |
| `workflow_approvals` | 0 | 2 (approbation) |
| `utilisateurs` | 0 | 1 |
| `parametres` | 0 | 1 |
| `backup` | 0 | 1 |
| `logistics_costs` | 0 | 1 |
| `file_storage` | 0 | 1 |
| `multi_channel_notifications` | 0 | 1 |

Un directeur général ne peut voir ni la comptabilité, ni les analytics, ni approuver les workflows de sa propre entreprise. C'est fonctionnellement bloquant.

**Correction :** Mettre à jour `MODULE_PERMISSIONS` dans `rbac_constants.py` pour donner au moins `level=1` (lecture) sur tous ces modules.

---

### E2 — CORS ouvert par défaut si `ENVIRONMENT` non défini

**Sévérité :** 🟠 ÉLEVÉE  
**Fichier :** `server.py` ligne 90, 457  
**Statut :** Non corrigé

**Description :**
```python
env = os.environ.get('ENVIRONMENT', 'development')  # défaut = 'development'
allow_origins=["*"] if env != "production" else cors_origins
```

Si la variable `ENVIRONMENT` n'est pas définie en production (erreur d'oubli), l'ERP accepte des requêtes cross-origin de **n'importe quel domaine**, ouvrant la voie à des attaques CSRF.

**Correction :** Inverser la logique — refuser par défaut, autoriser seulement si explicitement configuré en production.

---

### E3 — Stack traces internes exposées dans les erreurs 500

**Sévérité :** 🟠 ÉLEVÉE  
**Fichiers :** `backup_module.py` (l.361, l.415), `commandes_module.py` (l.1241)  
**Statut :** Non corrigé

```python
raise HTTPException(status_code=500, detail=str(e))  # ← expose le stack trace
```

Les détails d'exception Python (chemins de fichiers, noms de variables, version des librairies) sont renvoyés au client et facilitent le fingerprinting du système.

**Correction :**
```python
logger.error(f"Erreur interne: {e}", exc_info=True)
raise HTTPException(status_code=500, detail="Erreur interne du serveur")
```

---

### E4 — `refresh_tokens` : 145 entrées non purgées, aucun index

**Sévérité :** 🟠 ÉLEVÉE  
**Collection MongoDB :** `refresh_tokens`  
**Statut :** Non corrigé

**Problèmes identifiés :**
- **145 tokens** stockés, **0 révoqués**, **0 expirés purgés**
- Collection sans index → chaque vérification de refresh = full scan
- Pas de job de nettoyage périodique
- Croissance illimitée → performance dégradée à l'échelle

**Correction :**
```python
# Index à créer
await db.refresh_tokens.create_index("user_id")
await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)  # TTL index auto-purge
```

---

### E5 — 2FA obligatoire uniquement pour `super_admin`

**Sévérité :** 🟠 ÉLEVÉE  
**Fichier :** `twofa_module.py` ligne 20  
**Statut :** Non corrigé

```python
ROLES_2FA_REQUIRED = {"super_admin"}  # ← insuffisant
```

Le `directeur_general`, le `comptable`, et le `directeur_commercial` ont accès à des données financières sensibles sans protection 2FA obligatoire.

**Correction :**
```python
ROLES_2FA_REQUIRED = {"super_admin", "directeur_general", "comptable", "directeur_commercial"}
```

---

## FINDINGS MOYENS (6)

---

### M1 — Aucun index sur `email` dans la collection `users`

**Collection :** `users`  
Chaque login déclenche un full scan de la collection. Acceptable à 9 utilisateurs, problématique à l'échelle.

**Correction :**
```python
await db.users.create_index("email", unique=True)
```

---

### M2 — 7 collections sans index métier

**Collections concernées :** `bons_livraison`, `proformas`, `audit_logs`, `refresh_tokens`, `facture_lignes`, `commande_lignes`, `bl_lignes`

Toutes les requêtes de recherche/filtrage sont des full scans. En production avec des volumes importants, cela dégradera fortement les performances.

**Index recommandés :**
```python
await db.bons_livraison.create_index([("statut", 1), ("date_creation", -1)])
await db.proformas.create_index([("client_id", 1), ("statut", 1)])
await db.audit_logs.create_index([("user_id", 1), ("created_at", -1)])
await db.facture_lignes.create_index("facture_id")
await db.commande_lignes.create_index("commande_id")
await db.bl_lignes.create_index("bl_id")
```

---

### M3 — Incohérence permissions frontend/backend : `secretariat` et factures

**Fichiers :** `frontend/src/constants/permissions.js` vs `backend/rbac_constants.py`

Le frontend autorise `secretariat` à lire les factures (`level=1`) mais le backend refuse (`level=0`). Résultat : l'interface affiche la page mais l'API retourne 403. Expérience utilisateur brisée.

**Correction :** Aligner les deux fichiers — choisir une politique cohérente et la répliquer.

---

### M4 — Rôle `"commercial"` utilisé mais non défini dans `ROLES`

**Fichier :** `server.py` route `/envois-historique`

Le rôle `"commercial"` apparaît dans la liste `ALLOWED` de cet endpoint mais n'existe pas dans `ROLES` de `rbac_constants.py`. Si un token avec ce rôle est créé, il pourrait accéder à l'endpoint sans contrôle RBAC complet.

**Correction :** Soit ajouter `"commercial"` à `ROLES`, soit le retirer de `ALLOWED`.

---

### M5 — Build frontend de production absent

**Répertoire :** `frontend/build/` — **n'existe pas**

L'application React n'a jamais été buildée pour la production. Le serveur sert actuellement le mode développement (`npm start` sur port 3000) avec hot-reload, source maps exposées, et performances dégradées.

**Correction :**
```bash
cd frontend && npm run build
# Configurer Nginx ou le serveur FastAPI pour servir le dossier build/
```

---

### M6 — 1005 clients sans email en base, 1 doublon

**Collection :** `clients`

- **1005 clients** ont `email=null` (pas d'email renseigné)
- **1 doublon** : `email@yahoo.fr` apparaît 2 fois

Pas critique mais signale un problème de qualité des données importées.

---

## FINDINGS FAIBLES (4)

---

### F1 — Variable `JWT_EXPIRY_DAYS` ignorée

**Fichier :** `.env`

La variable `JWT_EXPIRY_DAYS` dans `.env` est ignorée par le code qui utilise `JWT_ACCESS_TOKEN_EXPIRY_MINUTES` et `JWT_REFRESH_TOKEN_EXPIRY_DAYS`. Source de confusion pour les administrateurs.

---

### F2 — `colisage_module.py` sans traçabilité audit

**Fichier :** `colisage_module.py`

Les opérations de colisage ne passent pas `log_audit_event` à leurs fonctions internes → aucune trace des modifications de colis dans les logs d'audit.

---

### F3 — `ModulePlaceholder.jsx` non routé

**Fichier :** `frontend/src/pages/ModulePlaceholder.jsx`

Le composant existe mais n'est référencé dans aucune route de `App.js`. Code mort.

---

### F4 — Credential super_admin hardcodé en fallback

**Fichier :** `server.py` ligne 1043-1044

```python
super_admin_password = os.environ.get('SUPER_ADMIN_PASSWORD', 'Admin@2025')
```

Si `SUPER_ADMIN_PASSWORD` n'est pas défini, le mot de passe `Admin@2025` est utilisé. Une vérification bloque cela en production (`env == 'production'`), mais la dépendance à une valeur par défaut hardcodée est risquée.

---

## Plan de Correction Priorisé

![Plan de correction](/home/user/audit-fabs.report/plan_correction.png)

### Sprint 1 — Jours 1-3 (BLOQUANTS sécurité)

| # | Action | Effort | Impact |
|---|---|---|---|
| C1 | Changer credentials MongoDB + Redis, purger historique Git | 4h | Critique |
| C2 | Corriger `resolve_user` dans fournisseurs_module + approvisionnement_module | 2h | Critique |
| C3 | Protéger `/health` par auth ou réduire réponse | 1h | Critique |
| C4 | Ajouter validation extension/type/taille uploads | 3h | Critique |
| C6 | Corriger bug décrémentation stock BL | 2h | Critique |
| E3 | Masquer stack traces dans les erreurs 500 | 1h | Élevée |

### Sprint 2 — Jours 4-7 (Sécurité élevée)

| # | Action | Effort | Impact |
|---|---|---|---|
| C5 | Échapper paramètre `q` dans tous les modules $regex | 2h | Critique |
| E1 | Corriger permissions RBAC directeur_general (10 modules) | 2h | Élevée |
| E2 | Inverser logique CORS (refuser par défaut) | 1h | Élevée |
| E4 | Créer index refresh_tokens + TTL auto-purge | 1h | Élevée |
| E5 | Étendre 2FA obligatoire aux rôles financiers | 1h | Élevée |
| M5 | Construire build production frontend | 2h | Moyenne |

### Sprint 3 — Jours 8-14 (Performance + cohérence)

| # | Action | Effort | Impact |
|---|---|---|---|
| M1 | Créer index unique sur `users.email` | 0.5h | Moyenne |
| M2 | Créer index sur les 7 collections manquantes | 1h | Moyenne |
| M3 | Aligner permissions frontend/backend secretariat | 1h | Moyenne |
| M4 | Résoudre rôle "commercial" indéfini | 0.5h | Moyenne |
| F2 | Ajouter log_audit_event dans colisage_module | 1h | Faible |

### Sprint 4 — Jours 15-21 (Nettoyage + hardening)

| # | Action | Effort | Impact |
|---|---|---|---|
| M6 | Nettoyer données clients (emails null, doublons) | 2h | Moyenne |
| F1 | Nettoyer variable JWT_EXPIRY_DAYS inutile | 0.5h | Faible |
| F3 | Supprimer ModulePlaceholder.jsx ou le router | 0.5h | Faible |
| F4 | Supprimer credential hardcodé en fallback | 0.5h | Faible |

**Effort total estimé : ~30 heures développeur**

---

## Évaluation Production-Readiness

| Critère | État actuel | Requis |
|---|---|---|
| Secrets sécurisés | ❌ Exposés historique Git | ✅ Rotated + .gitignore |
| Auth comptes désactivés | ❌ Bypass possible | ✅ Vérif actif en DB |
| Validation uploads | ❌ Aucune | ✅ Extension + taille + MIME |
| Injection NoSQL | ❌ Paramètre q non échappé | ✅ `re.escape()` |
| Intégrité stock | ❌ Bug décrémentation | ✅ Guard stock >= qte |
| RBAC DG | ❌ Aveugle 10 modules | ✅ Level 1 lecture |
| CORS | ⚠️ Ouvert si env non défini | ✅ Whitelist stricte |
| 2FA | ⚠️ Super_admin seulement | ✅ Rôles financiers inclus |
| Index MongoDB | ❌ 7 collections sans index | ✅ Index créés |
| Build production | ❌ Inexistant | ✅ `npm run build` |
| Stack traces exposées | ❌ `detail=str(e)` | ✅ Messages génériques |
| Refresh tokens TTL | ❌ 145 tokens non purgés | ✅ TTL index |

**Production-readiness actuelle : 35%**  
**Après corrections Sprint 1+2 : ~78%**  
**Après corrections Sprint 1+2+3+4 : ~94%**

---

## Points Positifs

L'ERP présente plusieurs aspects bien conçus qu'il convient de souligner :

- **Architecture solide** : FastAPI + Motor (async MongoDB) bien structuré, 25 000+ lignes de code organisées en modules distincts
- **Workflow métier complet** : Proforma → Commande → BL → Facture → Paiement correctement implémenté
- **Audit trail** : `log_audit_event` présent dans les modules principaux
- **JWT + Refresh tokens** : Mécanisme en place avec expiration configurable
- **Factures avec index** : La collection `factures` dispose d'index sur `client_id`, `statut`, `date_emission`
- **2FA implémentée** : Module TOTP fonctionnel (Google Authenticator / Authy)
- **Module FNE DGI** : Intégration fisc ivoirienne implémentée
- **Tests** : Suite de tests présente (`/backend/tests/`) bien que la couverture ne soit pas mesurée

---

## Méthodologie

Cet audit a été réalisé par :
1. **Analyse statique** : Lecture complète du code source (25 468 lignes Python backend, 15 000+ lignes JSX frontend)
2. **Analyse dynamique MongoDB** : Connexion directe à la base de données live pour vérifier les index, compter les collections, identifier les doublons
3. **Revue de l'historique Git** : Analyse des 4 derniers commits pour identifier les secrets exposés
4. **Revue RBAC** : Analyse croisée de `rbac_constants.py` (backend) et `permissions.js` (frontend)

**Limites :** Pas de tests de pénétration HTTP actifs. Pas de mesure de couverture de tests. Pas d'audit de performance sous charge.

---

*Rapport généré le 16 juin 2026 — ERP FABS-CI V10 — Éditions FABS CI, Côte d'Ivoire*
