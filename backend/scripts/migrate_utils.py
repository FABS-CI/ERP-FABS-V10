#!/usr/bin/env python3
"""
migrate_utils.py — Migration des clauses $or compat product_id/produit_id
vers requête directe {"produit_id": <val>} dans tous les modules backend.

Usage: python scripts/migrate_utils.py [--dry-run]
"""
import re
import sys
from pathlib import Path

DRY_RUN = "--dry-run" in sys.argv

BACKEND_DIR = Path(__file__).parent.parent

# Patterns exacts à remplacer et leurs remplacements
# Format: (regex_pattern, replacement_string, description)
REPLACEMENTS = [
    # Pattern 1: find_one avec $or simple product_id/produit_id
    (
        r'\{"\$or": \[\{"product_id": ([\w.]+)\}, \{"produit_id": \1\}\]\}',
        r'{"produit_id": \1}',
        "$or simple find_one"
    ),
    # Pattern 2: find_one avec $or + filtre actif
    (
        r'\{"\$or": \[\{"product_id": ([\w.]+)\}, \{"produit_id": \1\}\], "actif": True\}',
        r'{"produit_id": \1, "actif": True}',
        "$or + actif"
    ),
    # Pattern 3: find_one_and_update avec $or + stock_actuel
    (
        r'\{"\$or": \[\{"product_id": ([\w.]+)\}, \{"produit_id": \1\}\], "stock_actuel": \{"(.*?)"\}\}',
        r'{"produit_id": \1, "stock_actuel": {"\2"}}',
        "$or + stock_actuel"
    ),
    # Pattern 4: $or avec $in (collection find)
    (
        r'\{"\$or": \[\{"product_id": \{"\$in": ([\w.]+)\}\}, \{"produit_id": \{"\$in": \1\}\}\]\}',
        r'{"produit_id": {"$in": \1}}',
        "$or avec $in"
    ),
]

FILES_TO_PROCESS = [
    "commandes_module.py",
    "colisage_module.py",
]


def process_file(filepath: Path) -> int:
    content = filepath.read_text(encoding="utf-8")
    original = content
    total_changes = 0

    for pattern, replacement, desc in REPLACEMENTS:
        new_content, n = re.subn(pattern, replacement, content)
        if n > 0:
            print(f"  [{filepath.name}] {desc}: {n} remplacement(s)")
            content = new_content
            total_changes += n

    if total_changes > 0 and not DRY_RUN:
        filepath.write_text(content, encoding="utf-8")
        print(f"  => Fichier mis à jour ({total_changes} changements)")
    elif total_changes > 0 and DRY_RUN:
        print(f"  => [DRY-RUN] {total_changes} changements non appliqués")
    else:
        print(f"  [{filepath.name}] Aucun $or compat trouvé")

    return total_changes


def main():
    print(f"Mode: {'DRY-RUN' if DRY_RUN else 'APPLY'}")
    print()
    total = 0
    for fname in FILES_TO_PROCESS:
        fpath = BACKEND_DIR / fname
        if not fpath.exists():
            print(f"ABSENT: {fname}")
            continue
        total += process_file(fpath)

    print()
    print(f"Total: {total} remplacement(s) {'simulé(s)' if DRY_RUN else 'appliqué(s)'}")

    # Vérification post-migration
    print()
    print("=== Vérification résiduelle $or compat ===")
    for fname in FILES_TO_PROCESS:
        fpath = BACKEND_DIR / fname
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if '"$or"' in line and ('product_id' in line or 'produit_id' in line):
                # Uniquement les $or compat (pas les $or de recherche texte)
                if 'product_id":' in line and 'produit_id":' in line:
                    print(f"  RÉSIDUEL [{fname}:{i}]: {line.strip()}")


if __name__ == "__main__":
    main()
