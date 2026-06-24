# TOUR 2 — PLAN D'ATTAQUE PERFORMANCE

**Objectif**: Éliminer N+1 queries, passer Performance de 4→7

**Modules Critiques** (par ordre de criticité):
1. **rh_module.py** (2321 lignes, 24 zones N+1)
2. **commandes_module.py** (1863 lignes, 16 zones N+1)
3. **stock_module.py** (1242 lignes, 15 zones N+1)
4. **bi_analytics_module.py** (515 lignes, 13 zones N+1)
5. **colisage_module.py** (2454 lignes, 13 zones N+1)

---

## STRATÉGIES D'OPTIMISATION

### A) BULK QUERIES (Cas: Lire N documents et enrichir chacun)
**AVANT (N+1)**:
```python
for item in items:
    client = await db.clients.find_one({"client_id": item["client_id"]})
    item["client_name"] = client["nom"]
```
**Temps**: O(n) requêtes DB

**APRÈS (1 query)**:
```python
# Extraire toutes les IDs
client_ids = set(item["client_id"] for item in items)

# 1 query bulk pour récupérer tous les clients
clients = await db.clients.find(
    {"client_id": {"$in": list(client_ids)}}
).to_list(None)
clients_map = {c["client_id"]: c for c in clients}

# Enrichir localement (pas de DB)
for item in items:
    item["client_name"] = clients_map.get(item["client_id"], {}).get("nom", "")
```
**Temps**: O(1) requête DB + O(n) mem (rapide)

---

### B) AGGREGATION PIPELINE (Cas: Jointures + agrégations)
**AVANT (boucles)**:
```python
commandes = await db.commandes.find(...).to_list(100)
for cmd in commandes:
    client = await db.clients.find_one(...)
    lignes = await db.commande_lignes.find(...).to_list(None)
```
**Temps**: O(n) queries

**APRÈS (1 aggregation)**:
```python
pipeline = [
    {"$match": {...}},
    {"$lookup": {  # JOIN avec clients
        "from": "clients",
        "localField": "client_id",
        "foreignField": "client_id",
        "as": "client"
    }},
    {"$lookup": {  # JOIN avec lignes
        "from": "commande_lignes",
        "localField": "commande_id",
        "foreignField": "commande_id",
        "as": "lignes"
    }},
    {"$project": {...}}
]
result = await db.commandes.aggregate(pipeline).to_list(100)
```
**Temps**: O(1) query avec DB processing

---

### C) CACHING REDIS (Cas: Données immuables ou peu changeantes)
**AVANT**:
```python
# Chaque requête récupère de MongoDB
clients = await db.clients.find({"actif": True}).to_list(100)
```

**APRÈS**:
```python
# Vérifier Redis d'abord
cache_key = "clients:active:page:1"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Sinon récupérer de MongoDB et cacher
clients = await db.clients.find({"actif": True}).to_list(100)
await redis.setex(cache_key, 3600, json.dumps(...))  # 1h TTL
return clients
```
**Temps**: O(1) Redis get (< 1ms) vs O(n) MongoDB query

---

### D) PAGINATION (Cas: Lister N documents)
**AVANT**:
```python
# Charger TOUS les documents
all_docs = await db.collection.find().to_list(None)  # 1000+ docs = OOM
```

**APRÈS**:
```python
# Paginer: page 1 = 20 docs, page 2 = docs 20-40, etc.
page = query_params.get("page", 1)
limit = 20
skip = (page - 1) * limit

docs = await db.collection.find().skip(skip).limit(limit).to_list(limit)
total = await db.collection.count_documents({})
return {
    "data": docs,
    "total": total,
    "page": page,
    "pages": (total + limit - 1) // limit
}
```
**Temps**: O(1) requête pour une page

---

## ÉTAPES EXÉCUTION TOUR 2

### Phase 1: Audit détaillé
- [ ] Identifier exact N+1 patterns dans les 5 modules
- [ ] Évaluer impact par pattern (gains estimés)
- [ ] Décider stratégie pour chaque

### Phase 2: Refactoring Tier 1 (RH)
- [ ] rh_module.py: bulk queries + aggregation
- [ ] Tests locaux
- [ ] Mesurer improvement

### Phase 3: Refactoring Tier 2 (Commandes, Stock)
- [ ] commandes_module.py
- [ ] stock_module.py
- [ ] Tests

### Phase 4: Refactoring Tier 3 (Analytics, Colisage)
- [ ] bi_analytics_module.py
- [ ] colisage_module.py
- [ ] Tests

### Phase 5: Pagination + Caching globaux
- [ ] Ajouter pagination aux endpoints sans
- [ ] Ajouter caching Redis aux lectures fréquentes
- [ ] TTL intelligents

### Phase 6: Test de charge
- [ ] Simuler 200+ users concurrents
- [ ] Mesurer response times
- [ ] Vérifier stabilité

---

## MÉTRIQUES À TRACKER

- [ ] Nombre de requêtes par endpoint (before/after)
- [ ] Response time moyen par endpoint
- [ ] CPU usage (before: ?, after: <30%)
- [ ] Memory usage (before: ?, after: <500MB)
- [ ] Cache hit ratio (target: >80% pour lectures)

---

## RISQUES & MITIGATIONS

| Risque | Mitigation |
|--------|-----------|
| Cassé la logique métier | Code reviews + tests exhaustifs |
| Performance pire | Mesurer avant/après, revenir si dégradation |
| Mémoire OOM | Implémenter pagination partout |
| Cache stale | TTL courts + invalidation on write |

---

## SUCCÈS CRITÈRE TOUR 2

- Performance: 4→7/10 (N+1 queries éliminées ou <5%)
- Pagination: 21→82/82 fichiers implémentent
- Cache: 10→40+/82 fichiers utilisent Redis
- Response times: <500ms 90ile
- Test de charge: 200 users sans timeout

---

## GO!

Démarrer Phase 1: Audit détaillé avec snippets de code
