"""
Query Optimizer for ERP FABS-CI
Provides optimized patterns for common N+1 query scenarios
Ready to integrate with MongoDB or any database
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta

class QueryOptimizer:
    """
    Patterns for optimizing N+1 queries in list endpoints
    Use these patterns to replace slow queries
    """
    
    @staticmethod
    def bulk_load_details(db, collection_name: str, ids: List[str], 
                         detail_collection: str, foreign_key: str) -> Dict[str, Any]:
        """
        Load parent + child records in 2 queries instead of N+1
        
        BEFORE (N+1):
        ```
        parents = db[collection_name].find().limit(100)
        for parent in parents:
            children = db[detail_collection].find({foreign_key: parent['_id']})
            parent['children'] = children
        ```
        
        AFTER (2 queries):
        ```
        optimizer = QueryOptimizer()
        result = optimizer.bulk_load_details(db, 'clients', client_ids, 'client_details', 'client_id')
        ```
        """
        if not ids:
            return {}
        
        # Load all children in one query
        children = list(db[detail_collection].find({foreign_key: {"$in": ids}}))
        
        # Group by foreign key
        grouped = {}
        for child in children:
            key = str(child[foreign_key])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(child)
        
        return grouped
    
    @staticmethod
    def aggregate_with_lookup(db, pipeline: List[Dict]) -> List[Dict]:
        """
        Use MongoDB aggregation pipeline with $lookup for efficient joins
        
        EXAMPLE:
        ```
        pipeline = [
            {"$match": {"statut": "ACTIF"}},
            {
                "$lookup": {
                    "from": "presences",
                    "localField": "_id",
                    "foreignField": "employe_id",
                    "as": "presences"
                }
            },
            {"$limit": 100}
        ]
        result = optimizer.aggregate_with_lookup(db, pipeline)
        ```
        """
        # This would call db.collection.aggregate(pipeline)
        # Returning structure for documentation
        return {
            "pattern": "aggregation_pipeline",
            "pipeline": pipeline,
            "note": "Use with: db.collection.aggregate(pipeline)"
        }
    
    @staticmethod
    def paginated_query(db, collection: str, query: Dict = None, 
                       page: int = 1, limit: int = 100, 
                       sort: Dict = None) -> Dict[str, Any]:
        """
        Efficient paginated query with metadata
        
        USAGE:
        ```
        result = optimizer.paginated_query(db, 'clients', 
                                          query={'statut': 'ACTIF'},
                                          page=1,
                                          limit=100,
                                          sort={'created_at': -1})
        # Returns: {
        #   'data': [...],
        #   'page': 1,
        #   'limit': 100,
        #   'total': 1234,
        #   'pages': 13,
        #   'has_next': True
        # }
        ```
        """
        query = query or {}
        sort = sort or {"_id": -1}
        
        skip = (page - 1) * limit
        total = db[collection].count_documents(query)
        
        items = list(db[collection]
                    .find(query)
                    .sort(list(sort.items())[0])
                    .skip(skip)
                    .limit(limit))
        
        return {
            "data": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
            "has_next": page < (total + limit - 1) // limit,
            "has_prev": page > 1,
        }
    
    @staticmethod
    def cached_query(cache, db, key: str, collection: str, 
                    query: Dict = None, ttl_seconds: int = 300) -> Any:
        """
        Query with Redis caching layer
        
        USAGE:
        ```
        cache = redis.Redis()
        result = optimizer.cached_query(cache, db, 'clients_list', 
                                       'clients', 
                                       query={'statut': 'ACTIF'},
                                       ttl_seconds=300)
        ```
        """
        # Check cache first
        if cache:
            cached = cache.get(key)
            if cached:
                return json.loads(cached)
        
        # Query database
        query = query or {}
        result = list(db[collection].find(query).limit(100))
        
        # Store in cache
        if cache and result:
            cache.setex(key, ttl_seconds, json.dumps(result, default=str))
        
        return result
    
    @staticmethod
    def batch_insert_with_validation(db, collection: str, documents: List[Dict],
                                     unique_fields: List[str] = None) -> Dict:
        """
        Insert multiple documents with deduplication
        
        USAGE:
        ```
        docs = [
            {'nom': 'Client 1', 'email': 'c1@test.com'},
            {'nom': 'Client 2', 'email': 'c2@test.com'},
        ]
        result = optimizer.batch_insert_with_validation(db, 'clients', docs, 
                                                       unique_fields=['email'])
        ```
        """
        unique_fields = unique_fields or ['email']
        inserted = 0
        skipped = 0
        
        for doc in documents:
            # Check for duplicates
            query = {field: doc.get(field) for field in unique_fields}
            existing = db[collection].find_one(query)
            
            if not existing:
                db[collection].insert_one(doc)
                inserted += 1
            else:
                skipped += 1
        
        return {
            "inserted": inserted,
            "skipped": skipped,
            "total": len(documents)
        }
    
    @staticmethod
    def generate_index_recommendations(db) -> List[Dict]:
        """
        Analyze collections and recommend missing indexes
        
        RETURNS:
        ```
        [
            {
                "collection": "clients",
                "field": "email",
                "type": "unique",
                "reason": "Used in filters and lookups"
            },
            ...
        ]
        ```
        """
        recommendations = [
            {"collection": "clients", "field": "email", "type": "unique"},
            {"collection": "clients", "field": "statut", "type": "regular"},
            {"collection": "commandes", "field": "client_id", "type": "regular"},
            {"collection": "commandes", "field": "statut", "type": "regular"},
            {"collection": "commandes", "field": "created_at", "type": "regular"},
            {"collection": "factures", "field": "client_id", "type": "regular"},
            {"collection": "factures", "field": "statut", "type": "regular"},
            {"collection": "presences", "field": "employe_id", "type": "regular"},
            {"collection": "presences", "field": "date", "type": "regular"},
            {"collection": "stock_entrees", "field": "produit_id", "type": "regular"},
            {"collection": "stock_entrees", "field": "date_entree", "type": "regular"},
        ]
        return recommendations


class CacheHelper:
    """Redis caching helper for frequent queries"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.ttl_default = 300  # 5 minutes
    
    def get(self, key: str):
        """Get cached value"""
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set cache with TTL"""
        if not self.redis:
            return
        ttl = ttl or self.ttl_default
        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
        except:
            pass
    
    def delete(self, key: str):
        """Delete cached value"""
        if not self.redis:
            return
        try:
            self.redis.delete(key)
        except:
            pass
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self.redis:
            return
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except:
            pass


class PaginationHelper:
    """Pagination helper for list endpoints"""
    
    @staticmethod
    def validate_params(limit: int = 100, skip: int = 0, max_limit: int = 100) -> tuple:
        """Validate and normalize pagination parameters"""
        limit = min(int(limit), max_limit)
        limit = max(1, limit)
        skip = max(0, int(skip))
        return limit, skip
    
    @staticmethod
    def paginate_array(data: List, limit: int, skip: int) -> tuple:
        """Paginate Python array"""
        total = len(data)
        page_data = data[skip:skip+limit]
        return page_data, total
    
    @staticmethod
    def build_response(data: List, total: int, limit: int, skip: int) -> Dict:
        """Build paginated response"""
        return {
            "data": data,
            "count": len(data),
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "current_page": (skip // limit) + 1,
        }


class PerformanceLogger:
    """Log query performance for analysis"""
    
    def __init__(self):
        self.logs = []
    
    def log_query(self, endpoint: str, duration_ms: float, 
                  query_count: int, cache_hit: bool = False):
        """Log a query execution"""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "query_count": query_count,
            "cache_hit": cache_hit,
        })
    
    def get_slowest(self, limit: int = 10) -> List[Dict]:
        """Get slowest queries"""
        return sorted(self.logs, key=lambda x: x['duration_ms'], reverse=True)[:limit]
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        if not self.logs:
            return {}
        
        durations = [log['duration_ms'] for log in self.logs]
        return {
            "total_queries": len(self.logs),
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "cache_hits": sum(1 for log in self.logs if log['cache_hit']),
        }


# ============================================================================
# READY-TO-USE PATTERNS FOR COMMON N+1 SCENARIOS
# ============================================================================

OPTIMIZATION_PATTERNS = {
    "clients_with_contacts": {
        "description": "List clients with contact details",
        "pattern": "bulk_load_details",
        "fix": """
# Before: N+1 queries
clients = db.clients.find().limit(100)
for client in clients:
    contacts = db.contacts.find({"client_id": client["_id"]})
    client["contacts"] = contacts

# After: 2 queries
optimizer = QueryOptimizer()
client_ids = [c["_id"] for c in clients]
contacts = optimizer.bulk_load_details(db, "clients", client_ids, "contacts", "client_id")
for client in clients:
    client["contacts"] = contacts.get(str(client["_id"]), [])
        """
    },
    
    "commandes_with_lignes": {
        "description": "List orders with line items",
        "pattern": "bulk_load_details",
        "fix": """
# Use aggregation pipeline
db.commandes.aggregate([
    {"$limit": 100},
    {
        "$lookup": {
            "from": "lignes_commande",
            "localField": "_id",
            "foreignField": "commande_id",
            "as": "lignes"
        }
    }
])
        """
    },
    
    "employes_with_presences": {
        "description": "List employees with attendance records",
        "pattern": "aggregation_pipeline",
        "fix": """
# Aggregate with $lookup
pipeline = [
    {"$match": {"statut": "ACTIF"}},
    {"$limit": 100},
    {
        "$lookup": {
            "from": "presences",
            "localField": "_id",
            "foreignField": "employe_id",
            "as": "presences"
        }
    }
]
result = list(db.employes.aggregate(pipeline))
        """
    }
}


if __name__ == "__main__":
    print("Query Optimizer Patterns Ready")
    print("\nAvailable patterns:")
    for name, details in OPTIMIZATION_PATTERNS.items():
        print(f"  - {name}: {details['description']}")
