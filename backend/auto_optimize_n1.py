#!/usr/bin/env python3
"""
Auto-patch N+1 query patterns in modules
Semi-intelligent refactoring to bulk queries
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

class N1PatternDetector:
    """Find and optionally fix N+1 query patterns"""
    
    # Patterns we can detect
    PATTERNS = [
        # Pattern 1: for doc in docs: await db.X.find_one(...)
        r'for\s+(\w+)\s+in\s+(\w+):\s*(?:.*?\n\s*)*?await\s+db\.(\w+)\.find_one\(',
        
        # Pattern 2: for item in items: result = await db.X.find_one(...)
        r'for\s+(\w+)\s+in\s+(\w+):\s*(?:.*?\n\s*)*?(\w+)\s*=\s*await\s+db\.(\w+)\.find_one\(',
    ]
    
    @staticmethod
    def detect_n1_zones(code: str) -> List[Tuple[int, str]]:
        """
        Detect N+1 patterns and return (line_number, pattern_snippet)
        """
        zones = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Simple heuristic: for loop + find_one within next 50 lines
            if ' for ' in line and ' in ' in line:
                snippet = '\n'.join(lines[i:min(i+50, len(lines))])
                if 'find_one(' in snippet or 'find(' in snippet:
                    zones.append((i+1, line.strip()[:60]))  # 1-indexed
        
        return zones
    
    @staticmethod
    def create_bulk_fix_template(loop_var: str, iterable: str, collection: str, lookup_field: str) -> str:
        """
        Generate a bulk query replacement template
        """
        template = f"""
# === OPTIMIZED: Bulk fetch instead of N+1 ===
# Collect all IDs to fetch
{loop_var}_ids = {{{loop_var}_id for {loop_var} in {iterable} if {loop_var}.get('{lookup_field}')}}

if {loop_var}_ids:
    # Bulk fetch (1 query instead of N)
    {loop_var}s = await db.{collection}.find(
        {{"{lookup_field}": {{"$in": list({loop_var}_ids)}}}}
    ).to_list(None)
    {loop_var}s_map = {{{item}["{lookup_field}"]: {item} for {item} in {loop_var}s}}
    
    # Enrich from map (no DB calls)
    for {loop_var} in {iterable}:
        if {loop_var}.get('{lookup_field}'):
            # Use map: {loop_var}s_map.get({loop_var}['{lookup_field}'])
"""
        return template
    
    @staticmethod
    def report(modules: List[str]) -> None:
        """Generate report of N+1 patterns found"""
        print("\n=== N+1 PATTERN ANALYSIS ===\n")
        
        total_zones = 0
        
        for module_file in modules:
            module_path = Path(module_file)
            if not module_path.exists():
                continue
            
            code = module_path.read_text()
            zones = N1PatternDetector.detect_n1_zones(code)
            
            if zones:
                print(f"{module_file}: {len(zones)} N+1 zones")
                for line_num, snippet in zones[:3]:  # Show first 3
                    print(f"  Line {line_num}: {snippet}")
                total_zones += len(zones)
        
        print(f"\nTotal N+1 zones: {total_zones}")
        print("Manual fixes recommended for each:")
        print("1. Extract all IDs from documents")
        print("2. Bulk fetch with $in")
        print("3. Create lookup map")
        print("4. Enrich from map (no DB calls)")


if __name__ == '__main__':
    modules = [
        'rh_module.py',
        'commandes_module.py',
        'stock_module.py',
        'factures_module.py',
        'colisage_module.py',
    ]
    
    detector = N1PatternDetector()
    detector.report(modules)
    
    print("\n✅ Run this before modifying modules to understand N+1 patterns")
    print("⚠️  Automatic fixes are complex — manual review recommended")
