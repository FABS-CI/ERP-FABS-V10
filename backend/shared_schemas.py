"""
shared_schemas.py — Schémas Pydantic partagés ERP FABS V10

Ce module centralise les modèles Pydantic utilisés dans plusieurs modules
pour éviter la duplication et garantir la cohérence des contrats API.

Usage:
    from shared_schemas import EmailPayload, NotificationPreferenceIn
    from shared_schemas import EcritureComptableIn, EcritureComptableOut
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Email ──────────────────────────────────────────────────────────────────────

class EmailPayload(BaseModel):
    """Payload pour l'envoi d'un document par email.
    
    Utilisé dans : commandes_module, factures_module, paiements_module, proformas_module
    """
    destinataire: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    objet: Optional[str] = None
    message: Optional[str] = None


# ── Notifications ──────────────────────────────────────────────────────────────

class NotificationPreferenceIn(BaseModel):
    """Préférences de notification d'un utilisateur.
    
    Utilisé dans : notifications_module, multi_channel_notifications_module
    """
    stock_alertes: bool = True
    commande_alertes: bool = True
    paiement_alertes: bool = True
    livraison_alertes: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    whatsapp_notifications: bool = False


# ── Comptabilité ───────────────────────────────────────────────────────────────

class EcritureComptableIn(BaseModel):
    """Création d'une écriture comptable manuelle.
    
    Utilisé dans : comptabilite_module, comptabilite_avancee_module
    """
    journal: str                          # Code journal (VTE, ACH, BQ, etc.)
    date_ecriture: str                    # Format YYYY-MM-DD
    compte: str                           # Numéro de compte SYSCOHADA
    libelle: str
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    piece_reference: Optional[str] = None  # Référence facture/paiement


class EcritureComptableOut(BaseModel):
    """Représentation d'une écriture comptable en sortie d'API.
    
    Utilisé dans : comptabilite_module, comptabilite_avancee_module
    """
    ecriture_id: str
    journal: str
    date_ecriture: str
    compte: str
    libelle: str
    debit: float
    credit: float
    piece_reference: Optional[str] = None
    created_by: str
    created_at: str


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    """Métadonnées de pagination communes à toutes les listes paginées."""
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Enveloppe de réponse paginée générique."""
    data: list
    meta: PaginationMeta


# ── Réponse standard ───────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    """Réponse simple de succès."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Réponse d'erreur standard."""
    success: bool = False
    detail: str
    code: Optional[int] = None
