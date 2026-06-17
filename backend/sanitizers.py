"""
sanitizers.py — Reusable Pydantic field validators for XSS sanitization.

Usage:
    from sanitizers import sanitize_str

    class MyModel(BaseModel):
        nom: str
        notes: Optional[str] = None

        _san_nom = field_validator("nom", mode="before")(sanitize_str)
        _san_notes = field_validator("notes", mode="before")(sanitize_str)
"""

import bleach


def sanitize_str(cls, v):
    """Strip ALL HTML tags from a string value. Safe to use on Optional fields."""
    if v is None:
        return v
    if not isinstance(v, str):
        return v
    return bleach.clean(v, tags=[], strip=True).strip()
