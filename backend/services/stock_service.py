"""
Stock Service
Business logic for inventory/stock management
Extracted from stock_module.py (1242 lines → modular)
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class StockService:
    """Stock/Inventory business logic service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def enrich_stock_with_products(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich stock movements with product details (bulk)
        """
        if not docs:
            return docs
        
        product_ids = {
            d.get("produit_id") or d.get("product_id") 
            for d in docs 
            if d.get("produit_id") or d.get("product_id")
        }
        
        if not product_ids:
            return docs
        
        products = await self.db.produits.find(
            {"$or": [
                {"product_id": {"$in": list(product_ids)}},
                {"produit_id": {"$in": list(product_ids)}}
            ]}
        ).to_list(None)
        
        products_map = {}
        for p in products:
            pid = p.get("product_id") or p.get("produit_id")
            products_map[pid] = p
        
        for doc in docs:
            pid = doc.get("produit_id") or doc.get("product_id")
            if pid and pid in products_map:
                product = products_map[pid]
                doc["produit_nom"] = product.get("titre") or product.get("nom")
                doc["produit_reference"] = product.get("reference")
        
        return docs
    
    async def calculate_stock_totals(
        self,
        mouvement_type: str,
        quantite: float
    ) -> Dict:
        """Calculate stock impact"""
        
        return {
            "type": mouvement_type,
            "quantite_mouvement": quantite,
            "timestamp": None  # Set by caller
        }
    
    async def validate_stock_movement(
        self,
        data: Dict
    ) -> tuple[bool, Optional[str]]:
        """Validate stock movement"""
        
        if not data.get("produit_id") and not data.get("product_id"):
            return False, "product ID required"
        
        if not data.get("type_mouvement"):
            return False, "movement type required"
        
        if data.get("quantite", 0) <= 0:
            return False, "quantite must be > 0"
        
        return True, None
