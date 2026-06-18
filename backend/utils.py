"""
utils.py — Utilitaires partagés ERP FABS V10

Ce module centralise les helpers communs à tous les modules backend
pour éviter la duplication de code.

Usage:
    from utils import _ensure, _now_iso
"""
from datetime import datetime, timezone
from fastapi import HTTPException


def _ensure(condition: bool, status: int, detail: str) -> None:
    """Lève HTTPException si la condition est False.
    
    Args:
        condition: Expression booléenne à vérifier
        status: Code HTTP à retourner si condition est False
        detail: Message d'erreur
        
    Raises:
        HTTPException: Si condition est False
    """
    if not condition:
        raise HTTPException(status_code=status, detail=detail)


def _now_iso() -> str:
    """Retourne la date/heure courante UTC en format ISO 8601.
    
    Returns:
        str: datetime UTC au format ISO 8601 (ex: '2025-01-15T10:30:00.123456+00:00')
    """
    return datetime.now(timezone.utc).isoformat()
