"""
Employee Service
Business logic for employee management
Extracted from rh_module.py (2321 → modular structure)
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class EmployeeService:
    """Employee business logic service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def enrich_employee_with_relationships(
        self, 
        docs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich employee list with department, fonction, category, supervisor
        Using bulk queries instead of N+1
        """
        if not docs:
            return docs
        
        # Collect all IDs
        dept_ids = {d.get("departement_id") for d in docs if d.get("departement_id")}
        fonc_ids = {d.get("fonction_id") for d in docs if d.get("fonction_id")}
        cat_ids = {d.get("categorie_pro_id") for d in docs if d.get("categorie_pro_id")}
        sup_ids = {d.get("superieur_hierarchique_id") for d in docs if d.get("superieur_hierarchique_id")}
        
        # Bulk fetch
        depts = await self.db.departements.find(
            {"departement_id": {"$in": list(dept_ids)}}
        ).to_list(None)
        depts_map = {d["departement_id"]: d.get("nom") for d in depts}
        
        foncs = await self.db.fonctions.find(
            {"fonction_id": {"$in": list(fonc_ids)}}
        ).to_list(None)
        funcs_map = {f["fonction_id"]: f.get("nom") for f in foncs}
        
        cats = await self.db.categories_pro.find(
            {"categorie_pro_id": {"$in": list(cat_ids)}}
        ).to_list(None)
        cats_map = {c["categorie_pro_id"]: c.get("nom") for c in cats}
        
        sups = await self.db.employes.find(
            {"employe_id": {"$in": list(sup_ids)}}
        ).to_list(None)
        sups_map = {s["employe_id"]: f"{s.get('nom', '')} {s.get('prenoms', '')}".strip() for s in sups}
        
        # Enrich
        for doc in docs:
            doc["departement_nom"] = depts_map.get(doc.get("departement_id"))
            doc["fonction_nom"] = funcs_map.get(doc.get("fonction_id"))
            doc["categorie_pro_nom"] = cats_map.get(doc.get("categorie_pro_id"))
            doc["superieur_nom"] = sups_map.get(doc.get("superieur_hierarchique_id"))
        
        return docs
    
    async def validate_employee_data(self, data: Dict) -> tuple[bool, Optional[str]]:
        """Validate employee data before create/update"""
        
        # Required fields
        required = ["nom", "prenoms", "email"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return False, f"Missing fields: {missing}"
        
        # Email uniqueness
        existing = await self.db.employes.find_one(
            {"email": data["email"]},
            {"_id": 1}
        )
        if existing:
            return False, "Email already exists"
        
        return True, None
