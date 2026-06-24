"""
MongoDB Transaction Helper
Simple wrapper for multi-document ACID operations
"""

from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from typing import Callable, Any, Optional


class TransactionHelper:
    """Helper for safe multi-document operations"""
    
    def __init__(self, client: AsyncIOMotorClient):
        self.client = client
    
    @asynccontextmanager
    async def transaction(self):
        """
        Simple transaction context manager
        
        Usage:
            async with transaction_helper.transaction() as session:
                await db.collection1.insert_one(doc1, session=session)
                await db.collection2.insert_one(doc2, session=session)
                # Both succeed or both rollback atomically
        """
        session = await self.client.start_session()
        try:
            async with session.start_transaction():
                yield session
        except Exception as e:
            # Rollback happens automatically
            raise e
        finally:
            await session.end_session()
    
    async def atomic_multi_insert(
        self,
        db,
        operations: dict,
        session=None
    ) -> bool:
        """
        Insert multiple documents across collections atomically
        
        Example:
            operations = {
                "commandes": [cmd_doc],
                "commandes_lignes": [ligne1, ligne2]
            }
            success = await helper.atomic_multi_insert(db, operations)
        """
        try:
            use_session = session
            if not use_session:
                use_session = await self.client.start_session()
                async with use_session.start_transaction():
                    for collection_name, docs in operations.items():
                        if docs:
                            await db[collection_name].insert_many(docs, session=use_session)
                    return True
            else:
                for collection_name, docs in operations.items():
                    if docs:
                        await db[collection_name].insert_many(docs, session=use_session)
                return True
        except Exception as e:
            print(f"Transaction failed: {e}")
            return False
        finally:
            if not session:
                try:
                    await use_session.end_session()
                except:
                    pass
    
    async def atomic_update_multiple(
        self,
        db,
        updates: dict,
        session=None
    ) -> bool:
        """
        Update multiple documents across collections atomically
        
        Example:
            updates = {
                "commandes": [
                    ({"commande_id": "C1"}, {"$set": {"statut": "confirmed"}})
                ],
                "stock": [
                    ({"product_id": "P1"}, {"$inc": {"quantity": -10}})
                ]
            }
        """
        try:
            use_session = session
            if not use_session:
                use_session = await self.client.start_session()
                async with use_session.start_transaction():
                    for collection_name, update_ops in updates.items():
                        for filter_dict, update_dict in update_ops:
                            await db[collection_name].update_one(
                                filter_dict,
                                update_dict,
                                session=use_session
                            )
                    return True
            else:
                for collection_name, update_ops in updates.items():
                    for filter_dict, update_dict in update_ops:
                        await db[collection_name].update_one(
                            filter_dict,
                            update_dict,
                            session=use_session
                        )
                return True
        except Exception as e:
            print(f"Transaction failed: {e}")
            return False
        finally:
            if not session:
                try:
                    await use_session.end_session()
                except:
                    pass


# Example usage in a router:
"""
@router.post("/commandes")
async def create_commande(payload: CommandeIn):
    # Prepare documents
    cmd_doc = {"commande_id": "C1", "client_id": "CL1", ...}
    lignes = [{"produit_id": "P1", "quantite": 10}, ...]
    
    # Use transaction helper
    helper = TransactionHelper(db.client)
    operations = {
        "commandes": [cmd_doc],
        "commandes_lignes": lignes
    }
    
    success = await helper.atomic_multi_insert(db, operations)
    if success:
        return {"message": "Command créée", "commande_id": cmd_doc["commande_id"]}
    else:
        raise HTTPException(status_code=500, detail="Création échouée")
"""
