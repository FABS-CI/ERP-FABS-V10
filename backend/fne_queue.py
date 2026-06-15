"""
Queue Asynchrone FNE - Système de retry avec exponential backoff

Ce module gère la queue asynchrone pour la certification FNE,
avec retry automatique pour les erreurs 500 uniquement.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import redis
import os
from dotenv import load_dotenv

from motor.motor_asyncio import AsyncIOMotorClient
from fne_dgi_service import FNEDGIService, FNEStatus, FNESignRequest, FNERefundRequest

load_dotenv()


class FNEQueue:
    """Queue asynchrone pour la certification FNE"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
        self.queue_key = "fne:queue"
        self.processing_key = "fne:processing"
        self.service = FNEDGIService()
        
        # Délais de retry en secondes
        self.retry_delays = {
            1: 0,      # Immédiat
            2: 30,     # 30 secondes
            3: 120,    # 2 minutes
            4: 600,    # 10 minutes
            5: 3600    # 1 heure
        }
    
    async def enqueue_invoice_certification(
        self,
        invoice_id: str,
        invoice_data: Dict[str, Any],
        items_data: list
    ):
        """
        Ajoute une tâche de certification de facture à la queue
        
        Args:
            invoice_id: ID de la facture
            invoice_data: Données de la facture
            items_data: Liste des articles
        """
        task = {
            "type": "sign",
            "invoice_id": invoice_id,
            "invoice_data": invoice_data,
            "items_data": items_data,
            "attempt": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.redis_client.rpush(self.queue_key, json.dumps(task))
        await self._log_fne_action(
            invoice_id,
            "sign",
            0,
            0,
            {"task": "enqueued"},
            {"status": "queued"},
            0
        )
    
    async def enqueue_refund_certification(
        self,
        credit_note_id: str,
        invoice_id: str,
        refund_items: list
    ):
        """
        Ajoute une tâche de certification d'avoir à la queue
        
        Args:
            credit_note_id: ID de l'avoir
            invoice_id: ID de la facture d'origine (fne_invoice_id)
            refund_items: Liste des articles retournés
        """
        task = {
            "type": "refund",
            "credit_note_id": credit_note_id,
            "invoice_id": invoice_id,
            "refund_items": refund_items,
            "attempt": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.redis_client.rpush(self.queue_key, json.dumps(task))
        await self._log_fne_action(
            credit_note_id,
            "refund",
            0,
            0,
            {"task": "enqueued"},
            {"status": "queued"},
            0
        )
    
    async def process_queue(self):
        """Traite les tâches de la queue (boucle infinie)"""
        print("🚀 Démarrage du worker FNE...")
        
        while True:
            try:
                # Déplacer une tâche de la queue vers processing
                task_json = self.redis_client.brpoplpush(
                    self.queue_key,
                    self.processing_key,
                    timeout=5
                )
                
                if task_json:
                    task = json.loads(task_json)
                    await self._process_task(task)
                
                # Nettoyer les tâches en processing expirées (> 1 heure)
                await self._cleanup_processing()
                
            except Exception as e:
                print(f"❌ Erreur dans le worker FNE: {e}")
                await asyncio.sleep(10)
    
    async def _process_task(self, task: Dict[str, Any]):
        """
        Traite une tâche individuelle
        
        Args:
            task: Tâche à traiter
        """
        task_type = task["type"]
        attempt = task["attempt"]
        
        print(f"📋 Traitement tâche {task_type} - tentative {attempt}")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            if task_type == "sign":
                await self._process_sign_task(task)
            elif task_type == "refund":
                await self._process_refund_task(task)
            
            # Succès : supprimer de processing
            self.redis_client.lrem(self.processing_key, 0, json.dumps(task))
            
        except Exception as e:
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            print(f"❌ Erreur traitement tâche: {e}")
            
            # Déterminer si retry
            http_status = getattr(e, "status_code", 500)
            should_retry = self.service.should_retry(http_status, attempt)
            
            if should_retry:
                # Calculer le délai de retry
                delay = self.service.get_retry_delay(attempt)
                task["attempt"] = attempt + 1
                task["scheduled_at"] = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
                
                # Remettre dans la queue avec délai
                if delay == 0:
                    self.redis_client.rpush(self.queue_key, json.dumps(task))
                else:
                    # Pour les délais > 0, on utilise un set avec expiration
                    delayed_key = f"fne:delayed:{task['invoice_id']}"
                    self.redis_client.setex(delayed_key, delay, json.dumps(task))
                    # On créera un worker séparé pour traiter les tâches delayed
                
                print(f"🔄 Retry planifié dans {delay}s (tentative {attempt + 1})")
                
                # Logger l'erreur
                await self._log_fne_error(
                    task.get("invoice_id") or task.get("credit_note_id"),
                    task_type,
                    attempt,
                    http_status,
                    str(e),
                    duration_ms
                )
                
            else:
                # Échec final
                await self._mark_as_failed(task, str(e), http_status)
                self.redis_client.lrem(self.processing_key, 0, json.dumps(task))
                
                print(f"💀 Échec final après {attempt} tentatives")
                
                # Logger l'erreur finale
                await self._log_fne_error(
                    task.get("invoice_id") or task.get("credit_note_id"),
                    task_type,
                    attempt,
                    http_status,
                    str(e),
                    duration_ms
                )
    
    async def _process_sign_task(self, task: Dict[str, Any]):
        """
        Traite une tâche de certification de facture
        
        Args:
            task: Tâche de certification
        """
        invoice_id = task["invoice_id"]
        invoice_data = task["invoice_data"]
        items_data = task["items_data"]
        
        start_time = datetime.now(timezone.utc)
        
        # Vérifier si déjà certifiée
        existing_invoice = await self.db.invoices.find_one({"reference": invoice_id})
        if existing_invoice and existing_invoice.get("fne_status") == FNEStatus.CERTIFIED:
            print(f"✅ Facture {invoice_id} déjà certifiée, skip")
            return
        
        # Mettre à jour le statut en submitted
        await self.db.invoices.update_one(
            {"reference": invoice_id},
            {
                "$set": {
                    "fne_status": FNEStatus.SUBMITTED,
                    "fne_submitted_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Mapper vers le format FNE
        fne_request = self.service.map_invoice_to_fne_request(invoice_data, items_data)
        
        # Logger la requête
        await self._log_fne_action(
            invoice_id,
            "sign",
            task["attempt"],
            0,
            fne_request.model_dump(),
            None,
            0
        )
        
        # Appeler l'API DGI
        response = await self.service.sign_invoice(fne_request)
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        # Logger la réponse
        await self._log_fne_action(
            invoice_id,
            "sign",
            task["attempt"],
            200,
            fne_request.model_dump(),
            response.model_dump(),
            duration_ms
        )
        
        # Mettre à jour la facture avec les données DGI
        qr_code = await self.service.generate_qr_code(response.token)
        
        # Mettre à jour les lignes avec les IDs DGI
        for i, item in enumerate(items_data):
            if i < len(response.invoice.items):
                await self.db.invoice_items.update_one(
                    {"reference": item["reference"]},
                    {"$set": {"fne_item_id": response.invoice.items[i].id}}
                )
        
        await self.db.invoices.update_one(
            {"reference": invoice_id},
            {
                "$set": {
                    "fne_status": FNEStatus.CERTIFIED,
                    "fne_reference": response.reference,
                    "fne_token": response.token,
                    "fne_invoice_id": response.invoice.id,
                    "fne_certified_at": datetime.now(timezone.utc).isoformat(),
                    "fne_raw_response": response.model_dump(),
                    "fne_balance_sticker": response.balance_sticker,
                    "fne_retry_count": task["attempt"]
                }
            }
        )
        
        print(f"✅ Facture {invoice_id} certifiée: {response.reference}")
        
        # Alerte si balance_sticker < 20
        if response.balance_sticker < 20:
            await self._send_low_sticker_alert(response.balance_sticker)
    
    async def _process_refund_task(self, task: Dict[str, Any]):
        """
        Traite une tâche de certification d'avoir
        
        Args:
            task: Tâche de certification d'avoir
        """
        credit_note_id = task["credit_note_id"]
        invoice_id = task["invoice_id"]
        refund_items = task["refund_items"]
        
        start_time = datetime.now(timezone.utc)
        
        # Vérifier si déjà certifiée
        existing_credit_note = await self.db.credit_notes.find_one({"reference": credit_note_id})
        if existing_credit_note and existing_credit_note.get("fne_status") == FNEStatus.CERTIFIED:
            print(f"✅ Avoir {credit_note_id} déjà certifié, skip")
            return
        
        # Mettre à jour le statut en submitted
        await self.db.credit_notes.update_one(
            {"reference": credit_note_id},
            {
                "$set": {
                    "fne_status": FNEStatus.SUBMITTED,
                    "fne_submitted_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Mapper vers le format FNE
        fne_request = self.service.map_refund_to_fne_request(refund_items)
        
        # Logger la requête
        await self._log_fne_action(
            credit_note_id,
            "refund",
            task["attempt"],
            0,
            fne_request.model_dump(),
            None,
            0
        )
        
        # Appeler l'API DGI
        response = await self.service.refund_invoice(invoice_id, fne_request)
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        # Logger la réponse
        await self._log_fne_action(
            credit_note_id,
            "refund",
            task["attempt"],
            201,
            fne_request.model_dump(),
            response.model_dump(),
            duration_ms
        )
        
        # Mettre à jour l'avoir avec les données DGI
        await self.db.credit_notes.update_one(
            {"reference": credit_note_id},
            {
                "$set": {
                    "fne_status": FNEStatus.CERTIFIED,
                    "fne_reference": response.reference,
                    "fne_token": response.token,
                    "fne_certified_at": datetime.now(timezone.utc).isoformat(),
                    "fne_raw_response": response.model_dump(),
                    "fne_retry_count": task["attempt"]
                }
            }
        )
        
        print(f"✅ Avoir {credit_note_id} certifié: {response.reference}")
    
    async def _mark_as_failed(self, task: Dict[str, Any], error_message: str, http_status: int):
        """
        Marque une facture/avoir comme échec
        
        Args:
            task: Tâche échouée
            error_message: Message d'erreur
            http_status: Code HTTP
        """
        invoice_id = task.get("invoice_id")
        credit_note_id = task.get("credit_note_id")
        
        if invoice_id:
            await self.db.invoices.update_one(
                {"reference": invoice_id},
                {
                    "$set": {
                        "fne_status": FNEStatus.FAILED,
                        "fne_error_log": f"{http_status}: {error_message}",
                        "fne_retry_count": task["attempt"]
                    }
                }
            )
        elif credit_note_id:
            await self.db.credit_notes.update_one(
                {"reference": credit_note_id},
                {
                    "$set": {
                        "fne_status": FNEStatus.FAILED,
                        "fne_error_log": f"{http_status}: {error_message}",
                        "fne_retry_count": task["attempt"]
                    }
                }
            )
    
    async def _cleanup_processing(self):
        """Nettoie les tâches en processing expirées (> 1 heure)"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Récupérer toutes les tâches en processing
        processing_tasks = self.redis_client.lrange(self.processing_key, 0, -1)
        
        for task_json in processing_tasks:
            task = json.loads(task_json)
            scheduled_at = datetime.fromisoformat(task["scheduled_at"])
            
            if scheduled_at < cutoff:
                # Remettre dans la queue
                task["attempt"] = task["attempt"] + 1
                self.redis_client.rpush(self.queue_key, json.dumps(task))
                self.redis_client.lrem(self.processing_key, 0, task_json)
                print(f"🔄 Tâche expirée remise en queue: {task.get('invoice_id')}")
    
    async def _log_fne_action(
        self,
        invoice_id: str,
        action: str,
        attempt_number: int,
        http_status: int,
        request_body: Dict[str, Any],
        response_body: Optional[Dict[str, Any]],
        duration_ms: int
    ):
        """
        Log une action FNE dans la collection fne_logs
        
        Args:
            invoice_id: ID de la facture
            action: Type d'action (sign, refund)
            attempt_number: Numéro de tentative
            http_status: Code HTTP
            request_body: Corps de la requête
            response_body: Corps de la réponse
            duration_ms: Durée en ms
        """
        log_entry = {
            "invoice_id": invoice_id,
            "action": action,
            "attempt_number": attempt_number,
            "http_status": http_status,
            "request_body": request_body,
            "response_body": response_body,
            "duration_ms": duration_ms,
            "created_at": datetime.now(timezone.utc)
        }
        
        await self.db.fne_logs.insert_one(log_entry)
    
    async def _log_fne_error(
        self,
        invoice_id: str,
        action: str,
        attempt_number: int,
        http_status: int,
        error_message: str,
        duration_ms: int
    ):
        """
        Log une erreur FNE
        
        Args:
            invoice_id: ID de la facture
            action: Type d'action
            attempt_number: Numéro de tentative
            http_status: Code HTTP
            error_message: Message d'erreur
            duration_ms: Durée en ms
        """
        log_entry = {
            "invoice_id": invoice_id,
            "action": action,
            "attempt_number": attempt_number,
            "http_status": http_status,
            "request_body": {"error": error_message},
            "response_body": {"error": error_message},
            "duration_ms": duration_ms,
            "created_at": datetime.now(timezone.utc)
        }
        
        await self.db.fne_logs.insert_one(log_entry)
    
    async def _send_low_sticker_alert(self, balance: int):
        """
        Envoie une alerte si le solde de stickers est bas
        
        Args:
            balance: Solde de stickers
        """
        # TODO: Implémenter le système de notifications
        print(f"⚠️  ALERTE: Solde de stickers bas: {balance}")
        # Envoyer notification in-app et email à l'admin


# ============================================================================
# WORKER
# ============================================================================

async def start_fne_worker(db: AsyncIOMotorDatabase):
    """
    Démarre le worker FNE
    
    Args:
        db: Instance de base de données MongoDB
    """
    queue = FNEQueue(db)
    await queue.process_queue()
