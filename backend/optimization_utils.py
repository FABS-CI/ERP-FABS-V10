"""
Performance Optimization Utilities
Bulk queries, caching, aggregation helpers
"""

from typing import List, Dict, Any, Optional, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

class BulkQueryOptimizer:
    """Optimize N+1 queries using bulk operations"""
    
    @staticmethod
    async def enrich_documents_bulk(
        docs: List[Dict],
        db: AsyncIOMotorDatabase,
        enrichments: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Enrich documents with related data using bulk queries instead of N+1.
        
        Example:
            docs = [{"emp_id": 1, "dept_id": 10}, ...]
            
            enrichments = {
                "departement": {
                    "collection": "departements",
                    "local_field": "dept_id",
                    "foreign_field": "departement_id",
                    "output_field": "departement_nom",
                    "display_field": "nom"
                }
            }
            
            result = await BulkQueryOptimizer.enrich_documents_bulk(
                docs, db, enrichments
            )
        
        Before: N documents + N queries = N+1
        After: N documents + K queries (K = number of enrichments)
        """
        
        for enrich_name, config in enrichments.items():
            collection_name = config["collection"]
            local_field = config["local_field"]
            foreign_field = config["foreign_field"]
            output_field = config["output_field"]
            display_field = config["display_field"]
            
            # Extract all IDs to fetch
            ids_to_fetch: Set = set()
            for doc in docs:
                if doc.get(local_field):
                    ids_to_fetch.add(doc[local_field])
            
            if not ids_to_fetch:
                continue
            
            # Bulk fetch all related documents
            related_docs = await db[collection_name].find(
                {foreign_field: {"$in": list(ids_to_fetch)}}
            ).to_list(None)
            
            # Create lookup map
            lookup_map = {}
            for related_doc in related_docs:
                key = related_doc[foreign_field]
                value = related_doc.get(display_field)
                
                # Handle composite display fields
                if isinstance(display_field, list):
                    value = " ".join(
                        str(related_doc.get(f, "")) for f in display_field
                    ).strip()
                
                lookup_map[key] = value
            
            # Enrich original documents
            for doc in docs:
                if doc.get(local_field):
                    doc[output_field] = lookup_map.get(doc[local_field])
        
        return docs
    
    @staticmethod
    async def bulk_fetch_by_ids(
        db: AsyncIOMotorDatabase,
        collection_name: str,
        id_field: str,
        ids: List[str],
        projection: Optional[Dict] = None
    ) -> Dict[str, Dict]:
        """
        Fetch multiple documents by IDs and return as dict for quick lookup.
        
        Returns: {id: document, ...}
        """
        if not ids:
            return {}
        
        query = {id_field: {"$in": ids}}
        docs = await db[collection_name].find(query, projection).to_list(None)
        
        return {doc[id_field]: doc for doc in docs}


class PaginationHelper:
    """Standardize pagination across endpoints"""
    
    @staticmethod
    async def paginate_query(
        db_query,
        page: int = 1,
        limit: int = 20,
        count_total: bool = True,
        total_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Paginate a motor query and return standardized response.
        
        Returns:
        {
            "data": [...],
            "pagination": {
                "total": int,
                "page": int,
                "limit": int,
                "pages": int,
                "has_next": bool,
                "has_prev": bool
            }
        }
        """
        
        # Validate page
        page = max(1, page)
        limit = min(limit, 100)  # Cap at 100 for safety
        
        # Apply pagination
        skip = (page - 1) * limit
        data = await db_query.skip(skip).limit(limit).to_list(limit)
        
        # Get total count if requested
        if total_count is None and count_total:
            # This requires the original query without skip/limit
            # The caller should pass it as total_count if available
            total_count = len(data)  # Fallback (not accurate but safe)
        
        total_count = total_count or len(data)
        total_pages = max(1, (total_count + limit - 1) // limit)
        
        return {
            "data": data,
            "pagination": {
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }


class CacheHelper:
    """Simple Redis caching wrapper"""
    
    @staticmethod
    async def get_or_fetch(
        redis_client,
        cache_key: str,
        fetch_func,
        ttl: int = 3600
    ):
        """
        Get from cache or fetch and cache.
        
        fetch_func: async callable that returns data to cache
        ttl: cache time-to-live in seconds
        """
        
        # Try cache first
        cached = await redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass  # Invalid JSON, fetch fresh
        
        # Fetch fresh
        data = await fetch_func()
        
        # Cache result
        try:
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str)
            )
        except:
            pass  # Cache failure doesn't break API
        
        return data


class AggregationHelper:
    """Build optimized aggregation pipelines"""
    
    @staticmethod
    def create_join_pipeline(
        matches: Optional[Dict] = None,
        joins: Optional[List[Dict]] = None,
        sort: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """
        Create a MongoDB aggregation pipeline with joins.
        
        Example:
            pipeline = AggregationHelper.create_join_pipeline(
                matches={"statut": "active"},
                joins=[
                    {
                        "from": "departements",
                        "local_field": "dept_id",
                        "foreign_field": "dept_id",
                        "as": "department"
                    }
                ],
                sort={"created_at": -1},
                skip=0,
                limit=20
            )
        """
        
        pipeline = []
        
        # Match stage
        if matches:
            pipeline.append({"$match": matches})
        
        # Lookup stages (joins)
        if joins:
            for join in joins:
                pipeline.append({
                    "$lookup": {
                        "from": join["from"],
                        "localField": join["local_field"],
                        "foreignField": join["foreign_field"],
                        "as": join["as"]
                    }
                })
        
        # Sort stage
        if sort:
            pipeline.append({"$sort": sort})
        
        # Pagination
        if skip > 0:
            pipeline.append({"$skip": skip})
        if limit > 0:
            pipeline.append({"$limit": limit})
        
        return pipeline
