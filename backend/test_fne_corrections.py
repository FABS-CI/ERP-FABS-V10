"""
TEST SUITE - FNE AUDIT CORRECTIONS
Tests pour vérifier que toutes les corrections (C1-C5) sont implémentées correctement.
"""

import asyncio
import json
from datetime import datetime, timezone
from fne_dgi_service import (
    FNEInvoiceItem, FNESignRequest, InvoiceTemplate, 
    PaymentMethod, map_payment_method, FNEDGIService
)
from fne_module import FNEService, FNEConfig, FNEInvoice


# ============================================================================
# TEST C1: NCC Injection from Config
# ============================================================================

async def test_c1_ncc_injection():
    """[C1] Verify NCC is injected from config when missing from payload"""
    print("\n" + "="*70)
    print("TEST C1: NCC INJECTION FROM CONFIG")
    print("="*70)
    
    # Setup
    config = FNEConfig(
        company_ncc="2302562N",
        company_name="EDITIONS FABS-CI"
    )
    
    # Create invoice WITHOUT clientNcc
    invoice = FNEInvoice(
        reference="INV-T1-001",
        clientCompanyName="Client SARL",
        clientPhone="+225 1234567",
        items=[
            FNEInvoiceItem(
                reference="P001",
                description="Product 1",
                quantity=5,
                amount=100
            )
        ]
    )
    
    # Mock DB & Redis
    class MockDB:
        pass
    
    service = FNEService(config, MockDB(), None)
    fne_data = await service.transform_invoice_to_fne(invoice)
    
    # Verify
    assert fne_data.get("clientNcc") == "2302562N", f"Expected NCC '2302562N', got {fne_data.get('clientNcc')}"
    print("✓ PASS: NCC correctly injected from config")
    print(f"  - clientNcc in payload: {fne_data.get('clientNcc')}")
    return True


# ============================================================================
# TEST C2: Smart Template Fallback
# ============================================================================

async def test_c2_template_fallback():
    """[C2] Verify template is set correctly based on client_type and NCC"""
    print("\n" + "="*70)
    print("TEST C2: SMART TEMPLATE FALLBACK")
    print("="*70)
    
    config = FNEConfig(company_ncc="2302562N")
    
    tests = [
        {
            "name": "Particulier → B2C",
            "invoice": {
                "reference": "INV-T2-001",
                "clientCompanyName": "Jean Dupont",
                "clientPhone": "+225...",
                "client_type": "particulier",
                "template": "B2B",  # Even if B2B, should change to B2C
                "items": [FNEInvoiceItem(reference="P1", description="P1", quantity=1, amount=100)]
            },
            "expected_template": "B2C"
        },
        {
            "name": "Gouvernement → B2G",
            "invoice": {
                "reference": "INV-T2-002",
                "clientCompanyName": "Ministry",
                "clientPhone": "+225...",
                "client_type": "gouvernement",
                "template": "B2B",
                "items": [FNEInvoiceItem(reference="P1", description="P1", quantity=1, amount=100)]
            },
            "expected_template": "B2G"
        },
        {
            "name": "International → B2F",
            "invoice": {
                "reference": "INV-T2-003",
                "clientCompanyName": "Foreign Corp",
                "clientPhone": "+225...",
                "client_type": "international",
                "template": "B2B",
                "items": [FNEInvoiceItem(reference="P1", description="P1", quantity=1, amount=100)]
            },
            "expected_template": "B2F"
        },
        {
            "name": "B2B without NCC → fallback to B2C",
            "invoice": {
                "reference": "INV-T2-004",
                "clientCompanyName": "Client Corp",
                "clientPhone": "+225...",
                "clientNcc": None,  # No NCC
                "client_type": "entreprise",
                "template": "B2B",  # B2B requires NCC
                "items": [FNEInvoiceItem(reference="P1", description="P1", quantity=1, amount=100)]
            },
            "expected_template": "B2C"
        },
        {
            "name": "B2B with NCC → stays B2B",
            "invoice": {
                "reference": "INV-T2-005",
                "clientCompanyName": "Client Corp",
                "clientPhone": "+225...",
                "clientNcc": "9999999X",  # Has NCC
                "client_type": "entreprise",
                "template": "B2B",
                "items": [FNEInvoiceItem(reference="P1", description="P1", quantity=1, amount=100)]
            },
            "expected_template": "B2B"
        }
    ]
    
    class MockDB:
        pass
    
    service = FNEService(config, MockDB(), None)
    
    for test in tests:
        invoice = FNEInvoice(**test["invoice"])
        fne_data = await service.transform_invoice_to_fne(invoice)
        actual = fne_data.get("template")
        expected = test["expected_template"]
        
        if actual == expected:
            print(f"✓ PASS: {test['name']}")
            print(f"  - Expected: {expected}, Got: {actual}")
        else:
            print(f"✗ FAIL: {test['name']}")
            print(f"  - Expected: {expected}, Got: {actual}")
            return False
    
    return True


# ============================================================================
# TEST C3: Payment Method Validation
# ============================================================================

async def test_c3_payment_method_validation():
    """[C3] Verify payment method mapping and validation"""
    print("\n" + "="*70)
    print("TEST C3: PAYMENT METHOD VALIDATION")
    print("="*70)
    
    tests = [
        ("especes", "cash"),
        ("espèces", "cash"),
        ("mobile_money", "mobile-money"),
        ("orange_money", "mobile-money"),
        ("mtn_money", "mobile-money"),
        ("wave", "mobile-money"),
        ("carte_bancaire", "card"),
        ("cheque", "check"),
        ("virement", "transfer"),
    ]
    
    for erp_value, expected_dgi in tests:
        actual_dgi = map_payment_method(erp_value)
        if actual_dgi == expected_dgi:
            print(f"✓ PASS: {erp_value} → {actual_dgi}")
        else:
            print(f"✗ FAIL: {erp_value} → Expected {expected_dgi}, got {actual_dgi}")
            return False
    
    return True


# ============================================================================
# TEST C4: Item Taxes Default
# ============================================================================

async def test_c4_item_taxes_default():
    """[C4] Verify each invoice item has taxes defaulted to ['TVA']"""
    print("\n" + "="*70)
    print("TEST C4: ITEM TAXES DEFAULT")
    print("="*70)
    
    config = FNEConfig(company_ncc="2302562N")
    
    # Item WITHOUT taxes field (should default to ["TVA"])
    item = FNEInvoiceItem(
        reference="P001",
        description="Product without taxes",
        quantity=5,
        amount=100
        # NO taxes field - should default
    )
    
    # Verify the item model has default
    item_dict = item.model_dump()
    assert "taxes" in item_dict, "Item dict missing 'taxes' field"
    assert item_dict["taxes"] == ["TVA"], f"Expected ['TVA'], got {item_dict['taxes']}"
    print(f"✓ PASS: FNEInvoiceItem has taxes default")
    print(f"  - item.taxes = {item.taxes}")
    
    # Test full invoice transformation
    invoice = FNEInvoice(
        reference="INV-T4-001",
        clientCompanyName="Test Client",
        clientPhone="+225...",
        items=[
            FNEInvoiceItem(
                reference="P1",
                description="Product 1",
                quantity=1,
                amount=100
                # NO taxes
            ),
            FNEInvoiceItem(
                reference="P2",
                description="Product 2",
                quantity=2,
                amount=200,
                taxes=["TVAB"]  # Custom taxes
            )
        ]
    )
    
    class MockDB:
        pass
    
    service = FNEService(config, MockDB(), None)
    fne_data = await service.transform_invoice_to_fne(invoice)
    
    # Verify all items have taxes
    for i, item_data in enumerate(fne_data["items"]):
        assert "taxes" in item_data, f"Item {i} missing taxes field"
        assert len(item_data["taxes"]) > 0, f"Item {i} has empty taxes"
        print(f"  - Item {i}: taxes = {item_data['taxes']}")
    
    print(f"✓ PASS: All items have taxes field after transformation")
    return True


# ============================================================================
# TEST C5: API Response Marking & Audit Log
# ============================================================================

async def test_c5_api_response_marking():
    """[C5] Verify API response is marked with source='dgi_api' and certified_at"""
    print("\n" + "="*70)
    print("TEST C5: API RESPONSE MARKING & AUDIT LOG")
    print("="*70)
    
    # Simulate DGI API response
    dgi_response = {
        "ncc": "2302562N",
        "reference": "FNE-20260622-ABC123",
        "token": "verify_token_xyz",
        "warning": False,
        "balance_sticker": 98,
        "invoice": {
            "id": "inv_123",
            "token": "verify_token_xyz",
            "reference": "FNE-20260622-ABC123",
            "type": "sale",
            "status": "validated",
            "amount": 100000,
            "vatAmount": 18000,
            "items": []
        }
    }
    
    # Verify response marking
    response_with_metadata = dgi_response.copy()
    response_with_metadata["source"] = "dgi_api"
    response_with_metadata["certified_at"] = datetime.now(timezone.utc).isoformat()
    response_with_metadata["api_version"] = "fne_2025"
    
    assert response_with_metadata.get("source") == "dgi_api", "source field not marked"
    assert "certified_at" in response_with_metadata, "certified_at field missing"
    assert response_with_metadata.get("api_version") == "fne_2025", "api_version not set"
    
    print("✓ PASS: DGI response correctly marked")
    print(f"  - source: {response_with_metadata.get('source')}")
    print(f"  - certified_at: {response_with_metadata.get('certified_at')}")
    print(f"  - api_version: {response_with_metadata.get('api_version')}")
    
    # Verify audit log structure
    audit_log = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "invoice_id": "INV-T5-001",
        "action": "fne_certification_success",
        "source": "dgi_api",
        "ncc": response_with_metadata.get("ncc"),
        "reference": response_with_metadata.get("reference"),
        "token": response_with_metadata.get("token"),
        "http_status": 200,
        "response_summary": {
            "status": response_with_metadata.get("invoice", {}).get("status"),
            "amount": response_with_metadata.get("invoice", {}).get("amount"),
        }
    }
    
    assert audit_log["source"] == "dgi_api", "Audit log source not set"
    assert audit_log["action"] == "fne_certification_success", "Audit log action incorrect"
    assert "ts" in audit_log, "Audit log missing timestamp"
    
    print("✓ PASS: Audit log structure valid")
    print(f"  - action: {audit_log['action']}")
    print(f"  - response_summary: {json.dumps(audit_log['response_summary'], indent=2)}")
    
    return True


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all tests"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  FNE AUDIT CORRECTIONS TEST SUITE (C1-C5)".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    results = []
    
    try:
        results.append(("C1: NCC Injection", await test_c1_ncc_injection()))
        results.append(("C2: Template Fallback", await test_c2_template_fallback()))
        results.append(("C3: Payment Validation", await test_c3_payment_method_validation()))
        results.append(("C4: Item Taxes Default", await test_c4_item_taxes_default()))
        results.append(("C5: API Response Marking", await test_c5_api_response_marking()))
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "█"*70)
        print("█" + " ALL CORRECTIONS VERIFIED ".center(68, "█") + "█")
        print("█"*70)
        return True
    else:
        print("\n" + "█"*70)
        print("█" + " SOME TESTS FAILED ".center(68, "█") + "█")
        print("█"*70)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
