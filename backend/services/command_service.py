"""
Command Service
Business logic for order/command management
Extracted from commandes_module.py (1863 lines → modular)
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class CommandService:
    """Command business logic service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def enrich_commands_with_clients(
        self,
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich command list with client information (bulk query)
        """
        if not docs:
            return docs
        
        client_ids = {d.get("client_id") for d in docs if d.get("client_id")}
        if not client_ids:
            return docs
        
        clients = await self.db.clients.find(
            {"client_id": {"$in": list(client_ids)}}
        ).to_list(None)
        clients_map = {c["client_id"]: c for c in clients}
        
        for doc in docs:
            if doc.get("client_id"):
                client = clients_map.get(doc["client_id"])
                if client:
                    doc["client_nom"] = client.get("nom")
                    doc["client_tel"] = client.get("telephone")
        
        return docs
    
    async def calculate_command_totals(
        self,
        lignes: List[Dict]
    ) -> Dict[str, float]:
        """Calculate HT, TVA, TTC from command lines"""
        
        ht = sum(float(l.get("montant_ht", 0)) for l in lignes)
        tva_rate = float(lignes[0].get("tva_rate", 0.18)) if lignes else 0.18
        tva = ht * tva_rate
        ttc = ht + tva
        
        return {
            "montant_ht": ht,
            "tva": tva,
            "montant_ttc": ttc
        }
    
    async def validate_command(
        self, 
        data: Dict
    ) -> tuple[bool, Optional[str]]:
        """Validate command data"""
        
        if not data.get("client_id"):
            return False, "client_id required"
        
        if not data.get("lignes") or len(data.get("lignes", [])) == 0:
            return False, "At least 1 line required"
        
        # Verify client exists
        client = await self.db.clients.find_one(
            {"client_id": data["client_id"]},
            {"_id": 1}
        )
        if not client:
            return False, "Client not found"
        
        return True, None
