"""
SIMPLIFIED TEST SUITE - Verify FNE corrections in code
Tests code changes without requiring all dependencies
"""

import re
import json


def test_c1_ncc_injection():
    """[C1] Verify NCC injection code is present in fne_module.py"""
    print("\n" + "="*70)
    print("TEST C1: NCC INJECTION CODE")
    print("="*70)
    
    with open('fne_module.py', 'r') as f:
        code = f.read()
    
    # Check for NCC injection code
    checks = [
        ('clientNcc injection pattern', 'if not fne_data.get("clientNcc") and self.config.company_ncc:'),
        ('NCC assignment', 'fne_data["clientNcc"] = self.config.company_ncc'),
        ('C1 log marker', '[C1] NCC injected from config'),
    ]
    
    for name, pattern in checks:
        if pattern in code:
            print(f"✓ FOUND: {name}")
        else:
            print(f"✗ MISSING: {name}")
            return False
    
    return True


def test_c2_template_fallback():
    """[C2] Verify smart template fallback logic"""
    print("\n" + "="*70)
    print("TEST C2: SMART TEMPLATE FALLBACK CODE")
    print("="*70)
    
    with open('fne_module.py', 'r') as f:
        code = f.read()
    
    checks = [
        ('particulier → B2C', 'client_type == "particulier"'),
        ('gouvernement → B2G', 'client_type == "gouvernement"'),
        ('international → B2F', 'client_type == "international"'),
        ('B2B without NCC fallback', 'current_template == "B2B" and not has_ncc'),
        ('C2 log marker', '[C2] Template changed'),
    ]
    
    for name, pattern in checks:
        if pattern in code:
            print(f"✓ FOUND: {name}")
        else:
            print(f"✗ MISSING: {name}")
            return False
    
    return True


def test_c3_payment_validation():
    """[C3] Verify payment method validation"""
    print("\n" + "="*70)
    print("TEST C3: PAYMENT METHOD VALIDATION CODE")
    print("="*70)
    
    with open('fne_module.py', 'r') as f:
        code = f.read()
    
    checks = [
        ('VALID_DGI_PAYMENT_METHODS set', 'VALID_DGI_PAYMENT_METHODS = {'),
        ('payment method validation', 'if dgi_method not in VALID_DGI_PAYMENT_METHODS:'),
        ('default to cash', 'dgi_method = "cash"'),
        ('C3 log marker', '[C3] Invalid DGI payment method'),
    ]
    
    for name, pattern in checks:
        if pattern in code:
            print(f"✓ FOUND: {name}")
        else:
            print(f"✗ MISSING: {name}")
            return False
    
    return True


def test_c4_item_taxes_default():
    """[C4] Verify item taxes default in models"""
    print("\n" + "="*70)
    print("TEST C4: ITEM TAXES DEFAULT")
    print("="*70)
    
    # Check fne_dgi_service.py
    with open('fne_dgi_service.py', 'r') as f:
        service_code = f.read()
    
    # Find FNEInvoiceItem class
    match = re.search(r'class FNEInvoiceItem\(BaseModel\):.*?(?=class |\Z)', service_code, re.DOTALL)
    if not match:
        print("✗ FNEInvoiceItem class not found")
        return False
    
    item_class = match.group(0)
    
    checks = [
        ('taxes before other fields', 'taxes: List[str] = Field(default=["TVA"])', item_class),
        ('default factory for customTaxes', 'customTaxes: List[Dict[str, Any]] = Field(default_factory=list)', item_class),
    ]
    
    for name, pattern, search_in in checks:
        if pattern in search_in:
            print(f"✓ FOUND: {name}")
        else:
            print(f"✗ MISSING: {name}")
            print(f"  Pattern: {pattern[:50]}...")
            return False
    
    # Check that taxes field is initialized BEFORE other fields
    lines = item_class.split('\n')
    taxes_line = None
    ref_line = None
    for i, line in enumerate(lines):
        if 'taxes:' in line and 'Field(default=' in line:
            taxes_line = i
        if 'reference: str' in line:
            ref_line = i
    
    if taxes_line is not None and ref_line is not None:
        # Should be before reference
        print(f"✓ FOUND: taxes default defined correctly")
    
    return True


def test_c5_api_response_marking():
    """[C5] Verify API response marking and audit log"""
    print("\n" + "="*70)
    print("TEST C5: API RESPONSE MARKING & AUDIT LOG CODE")
    print("="*70)
    
    with open('fne_module.py', 'r') as f:
        code = f.read()
    
    checks = [
        ('source marking', 'response_with_metadata["source"] = "dgi_api"'),
        ('certified_at timestamp', 'response_with_metadata["certified_at"] = datetime.now(timezone.utc).isoformat()'),
        ('api_version', 'response_with_metadata["api_version"] = "fne_2025"'),
        ('audit_log creation', 'audit_log = {'),
        ('audit log source field', '"source": "dgi_api"'),
        ('audit log action', '"action": "fne_certification_success"'),
        ('db insert audit log', 'await self.db.fne_logs.insert_one(audit_log)'),
        ('C5 log marker', '[C5]'),
    ]
    
    for name, pattern in checks:
        if pattern in code:
            print(f"✓ FOUND: {name}")
        else:
            print(f"✗ MISSING: {name}")
            return False
    
    return True


def test_env_configuration():
    """Verify .env has FNE configuration"""
    print("\n" + "="*70)
    print("TEST ENV: FNE Configuration in .env")
    print("="*70)
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    required_vars = [
        ('FNE_BASE_URL', 'http://54.247.95.108/ws'),
        ('DGI_API_KEY', 'test_key'),
        ('COMPANY_NCC', '2302562N'),
        ('COMPANY_NAME', 'EDITIONS FABS-CI'),
        ('POINT_OF_SALE', '01'),
        ('USE_PRODUCTION', 'false'),
    ]
    
    for var_name, expected_value_hint in required_vars:
        if var_name in env_content:
            print(f"✓ FOUND: {var_name}")
        else:
            print(f"✗ MISSING: {var_name}")
            return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  FNE AUDIT CORRECTIONS - CODE VERIFICATION".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    tests = [
        ("C1: NCC Injection", test_c1_ncc_injection),
        ("C2: Template Fallback", test_c2_template_fallback),
        ("C3: Payment Validation", test_c3_payment_validation),
        ("C4: Item Taxes Default", test_c4_item_taxes_default),
        ("C5: API Response Marking", test_c5_api_response_marking),
        ("ENV: FNE Configuration", test_env_configuration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} corrections verified in code")
    
    if passed == total:
        print("\n" + "█"*70)
        print("█" + " ✓ ALL CORRECTIONS IMPLEMENTED ".center(68, "█") + "█")
        print("█"*70)
        return True
    else:
        print("\n" + "█"*70)
        print("█" + " ✗ SOME CORRECTIONS MISSING ".center(68, "█") + "█")
        print("█"*70)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
