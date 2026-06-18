"""
notification_service.py — Service centralisé de notifications ERP FABS V10

Centralise la logique de création et d'envoi de notifications
pour éviter la duplication entre notifications_module.py
et multi_channel_notifications_module.py.

Usage:
    from notification_service import create_notification, NOTIF_TYPES

"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


# ── Types de notifications ─────────────────────────────────────────────────────

NOTIF_TYPES = {
    # Commandes
    "COMMANDE_CREEE": "Nouvelle commande créée",
    "COMMANDE_VALIDEE": "Commande validée",
    "COMMANDE_ANNULEE": "Commande annulée",
    # Factures
    "FACTURE_EMISE": "Facture émise",
    "FACTURE_PAYEE": "Facture payée",
    "FACTURE_RETARD": "Facture en retard de paiement",
    # Stock
    "STOCK_BAS": "Stock en dessous du seuil minimum",
    "STOCK_RUPTURE": "Rupture de stock",
    "STOCK_REAPPRO": "Réapprovisionnement effectué",
    # Livraisons
    "BL_CREE": "Bon de livraison créé",
    "BL_EXPEDIE": "Livraison expédiée",
    # Système
    "SYSTEME_INFO": "Information système",
    "SYSTEME_ALERTE": "Alerte système",
}

NOTIF_SEVERITIES = ["info", "warning", "error", "success"]


# ── Création de notification ───────────────────────────────────────────────────

async def create_notification(
    db: AsyncIOMotorDatabase,
    type_notif: str,
    message: str,
    user_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    severity: str = "info",
    metadata: Optional[dict] = None,
) -> str:
    """Crée une notification en base de données.

    Args:
        db: Instance AsyncIOMotorDatabase
        type_notif: Type de notification (voir NOTIF_TYPES)
        message: Message lisible par l'utilisateur
        user_id: ID de l'utilisateur destinataire (None = global/broadcast)
        entity_id: ID de l'entité concernée (commande_id, facture_id, etc.)
        entity_type: Type d'entité ("commande", "facture", "produit", etc.)
        severity: Niveau ("info", "warning", "error", "success")
        metadata: Données supplémentaires libres

    Returns:
        str: notification_id généré
    """
    if severity not in NOTIF_SEVERITIES:
        severity = "info"

    notif_id = f"notif_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    doc = {
        "notification_id": notif_id,
        "type": type_notif,
        "message": message,
        "severity": severity,
        "lu": False,
        "created_at": now,
    }

    if user_id:
        doc["user_id"] = user_id
    if entity_id:
        doc["entity_id"] = entity_id
    if entity_type:
        doc["entity_type"] = entity_type
    if metadata:
        doc["metadata"] = metadata

    await db.notifications.insert_one(doc)
    return notif_id


async def mark_as_read(
    db: AsyncIOMotorDatabase,
    notification_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """Marque une notification comme lue.

    Returns:
        bool: True si mise à jour effectuée
    """
    query = {"notification_id": notification_id}
    if user_id:
        query["user_id"] = user_id

    result = await db.notifications.update_one(
        query,
        {"$set": {"lu": True, "lu_at": datetime.now(timezone.utc).isoformat()}}
    )
    return result.modified_count > 0


async def get_unread_count(
    db: AsyncIOMotorDatabase,
    user_id: Optional[str] = None,
) -> int:
    """Retourne le nombre de notifications non lues.

    Args:
        user_id: Si fourni, filtre par utilisateur. Sinon global.
    """
    query: dict = {"lu": False}
    if user_id:
        query["$or"] = [{"user_id": user_id}, {"user_id": {"$exists": False}}]

    return await db.notifications.count_documents(query)


async def notify_stock_bas(
    db: AsyncIOMotorDatabase,
    produit_id: str,
    produit_nom: str,
    stock_actuel: int,
    seuil_minimum: int,
) -> str:
    """Raccourci : notifier un stock en dessous du seuil."""
    message = (
        f"Stock bas : {produit_nom} — "
        f"{stock_actuel} unités restantes (seuil: {seuil_minimum})"
    )
    return await create_notification(
        db=db,
        type_notif="STOCK_BAS",
        message=message,
        entity_id=produit_id,
        entity_type="produit",
        severity="warning",
        metadata={"stock_actuel": stock_actuel, "seuil_minimum": seuil_minimum},
    )


async def notify_commande(
    db: AsyncIOMotorDatabase,
    commande_id: str,
    reference: str,
    event: str = "COMMANDE_CREEE",
    user_id: Optional[str] = None,
) -> str:
    """Raccourci : notifier un événement commande."""
    label = NOTIF_TYPES.get(event, event)
    message = f"{label} : {reference}"
    return await create_notification(
        db=db,
        type_notif=event,
        message=message,
        user_id=user_id,
        entity_id=commande_id,
        entity_type="commande",
        severity="info",
    )
