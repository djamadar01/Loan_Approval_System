#!/usr/bin/env python3
"""
Test suite for enhanced ApplicantDB MCP server demonstrating all features:
1. Webhook support for profile updates
2. Batch get_applicants tool
3. Advanced validation rules for profiles
4. Historical data tracking (audit trail)
5. Data enrichment from external services
"""

import json
import sys
import time
from datetime import datetime, timedelta

# Import from enhanced server
from applicantdb_mcp_server_enhanced import (
    applicant_db,
    employer_db,
    audit_trail,
    webhook_manager,
    ValidationRuleType,
    AuditEventType,
    DataEnrichmentService,
    VALIDATION_RULES
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_1_webhook_support():
    """Test 1: Webhook support for profile updates."""
    print_section("TEST 1: WEBHOOK SUPPORT FOR PROFILE UPDATES")

    # Register webhooks for different event types
    print("Registering webhooks for different events...")
    webhook_1 = webhook_manager.register_webhook(
        "https://example.com/hooks/profile-updates",
        "profile_updated"
    )
    print(f"✓ Registered webhook (profile_updated): {webhook_1}")

    webhook_2 = webhook_manager.register_webhook(
        "https://example.com/hooks/credit-updates",
        "credit_updated"
    )
    print(f"✓ Registered webhook (credit_updated): {webhook_2}")

    webhook_3 = webhook_manager.register_webhook(
        "https://example.com/hooks/employment-verified",
        "employment_verified"
    )
    print(f"✓ Registered webhook (employment_verified): {webhook_3}")

    # List all webhooks
    print("\nListing all registered webhooks...")
    webhooks = webhook_manager.list_webhooks()
    print(f"✓ Total registered webhooks: {len(webhooks)}")
    for wh in webhooks:
        print(f"  - {wh['event_type']}: {wh['url']}")

    # Filter by event type
    print("\nFiltering webhooks by event type...")
    profile_webhooks = webhook_manager.list_webhooks("profile_updated")
    print(f"✓ Profile update webhooks: {len(profile_webhooks)}")

    # Trigger webhook (async)
    print("\nTriggering webhook event...")
    webhook_manager.trigger_webhook('profile_updated', {
        'applicant_id': 'APP001',
        'event': 'profile_created',
        'timestamp': datetime.utcnow().isoformat()
    })
    print("✓ Webhook triggered (async)")

    # Unregister webhook
    print(f"\nUnregistering webhook {webhook_1}...")
    success = webhook_manager.unregister_webhook(webhook_1)
    print(f"✓ Webhook unregistered: {success}")

    return True


def test_2_batch_operations():
    """Test 2: Batch get_applicants tool."""
    print_section("TEST 2: BATCH GET_APPLICANTS TOOL")

    # Create multiple test applicants
    print("Creating batch of applicants...")
    applicant_ids = []
    for i in range(5):
        app_id = f"BATCH_TEST_{i:03d}"
        applicant_data = {
            "id": app_id,
            "first_name": f"Batch{i}",
            "last_name": f"Test{i}",
            "email": f"batch{i}@example.com",
            "phone": f"555-000-{1000+i}",
            "employment_status": "active",
            "annual_income": 50000 + (i * 10000),
            "enrichment_data": {}
        }
        try:
            applicant_db.create_applicant(applicant_data)
            applicant_ids.append(app_id)
            print(f"✓ Created applicant: {app_id}")
        except Exception as e:
            print(f"✗ Error creating applicant {app_id}: {e}")

    # Retrieve batch of applicants
    print(f"\nRetrieving batch of {len(applicant_ids)} applicants...")
    applicants = applicant_db.get_applicants_batch(applicant_ids)
    print(f"✓ Retrieved {len(applicants)} applicants")

    for app in applicants:
        print(f"  - {app['id']}: {app['first_name']} {app['last_name']} ({app['email']})")

    # Add credit data to batch applicants
    print("\nAdding credit data to batch applicants...")
    for app_id in applicant_ids:
        credit_data = {
            "credit_score": 700 + (hash(app_id) % 150),
            "total_debt": 10000 + (hash(app_id) % 30000),
            "available_credit": 15000 + (hash(app_id) % 35000),
            "payment_history": ["on-time", "on-time", "on-time"]
        }
        try:
            applicant_db.add_credit_update(app_id, credit_data)
            print(f"✓ Added credit data for {app_id}")
        except Exception as e:
            print(f"✗ Error adding credit data: {e}")

    # Get profiles with credit history
    print("\nRetrieving batch profiles with credit history...")
    profiles = []
    for app_id in applicant_ids:
        applicant = applicant_db.get_applicant(app_id)
        credit_history = applicant_db.get_credit_history(app_id)
        profiles.append({
            "applicant": applicant,
            "credit_history": credit_history
        })

    print(f"✓ Retrieved {len(profiles)} complete profiles")
    for profile in profiles:
        app = profile['applicant']
        credit = profile['credit_history'][0] if profile['credit_history'] else None
        if credit:
            print(f"  - {app['id']}: Score={credit['credit_score']}, Debt=${credit['total_debt']:,.0f}")

    return True


def test_3_validation_rules():
    """Test 3: Advanced validation rules."""
    print_section("TEST 3: ADVANCED VALIDATION RULES FOR PROFILES")

    # Show all validation rules
    print("Registered validation rules:")
    for rule_type, rule in VALIDATION_RULES.items():
        print(f"  - {rule.name} ({rule_type.value}): {'✓ Enabled' if rule.enabled else '✗ Disabled'}")

    # Test email format validation
    print("\n1. Testing Email Format Rule:")
    test_cases = [
        {"email": "valid@example.com", "expected": True},
        {"email": "invalid.email", "expected": False},
        {"email": "also@invalid", "expected": False},
    ]
    email_rule = VALIDATION_RULES[ValidationRuleType.EMAIL_FORMAT]
    for test in test_cases:
        is_valid, error = email_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        print(f"  {status} {test['email']}: Valid={is_valid}, Error={error}")

    # Test credit score range validation
    print("\n2. Testing Credit Score Range Rule:")
    credit_rule = VALIDATION_RULES[ValidationRuleType.CREDIT_SCORE_RANGE]
    test_cases = [
        {"credit_score": 650, "expected": True},
        {"credit_score": 200, "expected": False},
        {"credit_score": 900, "expected": False},
        {"credit_score": 750, "expected": True},
    ]
    for test in test_cases:
        is_valid, error = credit_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        print(f"  {status} Score {test['credit_score']}: Valid={is_valid}")

    # Test income threshold validation
    print("\n3. Testing Income Threshold Rule:")
    income_rule = VALIDATION_RULES[ValidationRuleType.INCOME_THRESHOLD]
    test_cases = [
        {"annual_income": 50000, "expected": True},
        {"annual_income": 10000, "expected": False},
        {"annual_income": 100000, "expected": True},
    ]
    for test in test_cases:
        is_valid, error = income_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        print(f"  {status} Income ${test['annual_income']:,}: Valid={is_valid}")

    # Test employment status validation
    print("\n4. Testing Employment Status Rule:")
    status_rule = VALIDATION_RULES[ValidationRuleType.EMPLOYMENT_STATUS_VALID]
    test_cases = [
        {"employment_status": "active", "expected": True},
        {"employment_status": "invalid_status", "expected": False},
        {"employment_status": "unemployed", "expected": True},
    ]
    for test in test_cases:
        is_valid, error = status_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        print(f"  {status} Status '{test['employment_status']}': Valid={is_valid}")

    # Test debt-to-income ratio
    print("\n5. Testing Debt-to-Income Ratio Rule:")
    dti_rule = VALIDATION_RULES[ValidationRuleType.DEBT_TO_INCOME_RATIO]
    test_cases = [
        {"annual_income": 100000, "total_debt": 20000, "expected": True},  # 20% DTI
        {"annual_income": 100000, "total_debt": 50000, "expected": False},  # 50% DTI
    ]
    for test in test_cases:
        is_valid, error = dti_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        dti = (test["total_debt"] / test["annual_income"] * 100) if test["annual_income"] else 0
        print(f"  {status} DTI {dti:.1f}%: Valid={is_valid}")

    # Test age requirement
    print("\n6. Testing Age Requirement Rule:")
    age_rule = VALIDATION_RULES[ValidationRuleType.AGE_REQUIREMENT]
    today = datetime.utcnow()
    test_cases = [
        {"date_of_birth": (today - timedelta(days=365*25)).isoformat(), "expected": True},  # 25 years old
        {"date_of_birth": (today - timedelta(days=365*16)).isoformat(), "expected": False},  # 16 years old
    ]
    for test in test_cases:
        is_valid, error = age_rule.validate(test)
        status = "✓" if is_valid == test["expected"] else "✗"
        print(f"  {status} DOB {test['date_of_birth'][:10]}: Valid={is_valid}")

    return True


def test_4_audit_trail():
    """Test 4: Historical data tracking (audit trail)."""
    print_section("TEST 4: HISTORICAL DATA TRACKING (AUDIT TRAIL)")

    # Create test applicant with audit logging
    app_id = "AUDIT_TEST_001"
    print(f"Creating applicant {app_id} with audit logging...")
    applicant_data = {
        "id": app_id,
        "first_name": "Audit",
        "last_name": "Tester",
        "email": "audit@example.com",
        "annual_income": 75000,
        "employment_status": "active",
        "enrichment_data": {}
    }
    applicant_db.create_applicant(applicant_data)
    print(f"✓ Created applicant with ID {app_id}")

    # Log various audit events
    print("\nLogging audit events...")

    # Profile created event
    audit_trail.log_event(
        AuditEventType.PROFILE_CREATED,
        applicant_id=app_id,
        entity_type="applicant",
        action="create",
        new_values=applicant_data,
        user_id="system"
    )
    print("✓ Logged PROFILE_CREATED event")

    # Credit updated event
    credit_data = {
        "credit_score": 720,
        "total_debt": 15000,
        "available_credit": 20000
    }
    applicant_db.add_credit_update(app_id, credit_data, updated_by="credit_bureau")
    audit_trail.log_event(
        AuditEventType.CREDIT_UPDATED,
        applicant_id=app_id,
        entity_type="credit",
        action="update",
        new_values=credit_data,
        user_id="credit_bureau"
    )
    print("✓ Logged CREDIT_UPDATED event")

    # Validation event
    audit_trail.log_event(
        AuditEventType.VALIDATION_FAILED,
        applicant_id=app_id,
        entity_type="validation",
        action="validate",
        new_values={"errors": ["Income below threshold"]},
        user_id="system"
    )
    print("✓ Logged VALIDATION_FAILED event")

    # Data enrichment event
    audit_trail.log_event(
        AuditEventType.DATA_ENRICHED,
        applicant_id=app_id,
        entity_type="enrichment",
        action="enrich",
        new_values={"credit_enrichment": {"credit_score": 730}},
        user_id="enrichment_service"
    )
    print("✓ Logged DATA_ENRICHED event")

    # Retrieve audit history
    print(f"\nRetrieving audit history for {app_id}...")
    history = audit_trail.get_history(app_id, limit=10)
    print(f"✓ Retrieved {len(history)} audit events")

    for i, event in enumerate(history[:5], 1):
        print(f"\n  Event {i}:")
        print(f"    - Type: {event['event_type']}")
        print(f"    - Action: {event['action']}")
        print(f"    - User: {event['user_id']}")
        print(f"    - Timestamp: {event['timestamp']}")
        if event['new_values']:
            print(f"    - Changes: {json.loads(event['new_values']) if isinstance(event['new_values'], str) else event['new_values']}")

    return True


def test_5_data_enrichment():
    """Test 5: Data enrichment from external services (simulated)."""
    print_section("TEST 5: DATA ENRICHMENT FROM EXTERNAL SERVICES (SIMULATED)")

    # Create test applicant
    app_id = "ENRICHMENT_TEST_001"
    applicant_data = {
        "id": app_id,
        "first_name": "John",
        "last_name": "Enriched",
        "email": "john.enriched@example.com",
        "ssn": "123-45-6789",
        "annual_income": 85000,
        "employment_status": "active"
    }

    print("Creating applicant for enrichment testing...")
    applicant_db.create_applicant(applicant_data)
    print(f"✓ Created applicant {app_id}")

    # Test credit data enrichment
    print("\n1. Credit Data Enrichment (Simulated Credit Bureau):")
    credit_enrichment = DataEnrichmentService.enrich_credit_data(applicant_data)
    print(f"  Source: {credit_enrichment['source']}")
    print(f"  Credit Score: {credit_enrichment['credit_score']}")
    print(f"  Total Debt: ${credit_enrichment['total_debt']:,.2f}")
    print(f"  Available Credit: ${credit_enrichment['available_credit']:,.2f}")

    # Test employment data enrichment
    print("\n2. Employment Data Enrichment (Simulated Employment Service):")
    employment_enrichment = DataEnrichmentService.enrich_employment_data(applicant_data)
    print(f"  Source: {employment_enrichment['source']}")
    print(f"  Employment Verified: {employment_enrichment['employment_verified']}")
    print(f"  Verification Confidence: {employment_enrichment['verification_confidence']:.1%}")

    # Test identity data enrichment
    print("\n3. Identity Data Enrichment (Simulated Identity Service):")
    identity_enrichment = DataEnrichmentService.enrich_identity_data(applicant_data)
    print(f"  Source: {identity_enrichment['source']}")
    print(f"  Identity Verified: {identity_enrichment['identity_verified']}")
    print(f"  Verification Date: {identity_enrichment['verification_date']}")

    # Verify enrichment was stored
    print(f"\nRetrieving enriched applicant profile...")
    retrieved = applicant_db.get_applicant(app_id)
    if retrieved.get('enrichment_data'):
        enrichment = retrieved['enrichment_data']
        print(f"✓ Enrichment data stored and retrieved:")
        print(f"  - Credit Enrichment: {enrichment.get('credit_enrichment', {}).get('source', 'N/A')}")
        print(f"  - Employment Enrichment: {enrichment.get('employment_enrichment', {}).get('source', 'N/A')}")
        print(f"  - Identity Enrichment: {enrichment.get('identity_enrichment', {}).get('source', 'N/A')}")
        print(f"  - Enriched At: {enrichment.get('enriched_at', 'N/A')}")

    return True


def test_6_integrated_workflow():
    """Test 6: Integrated workflow using all features together."""
    print_section("TEST 6: INTEGRATED WORKFLOW - ALL FEATURES TOGETHER")

    # Create applicant with full workflow
    app_id = "WORKFLOW_TEST_001"
    print(f"Starting integrated workflow for applicant {app_id}...")

    # Step 1: Create applicant with enrichment
    print("\nStep 1: Create applicant with enrichment")
    applicant_data = {
        "id": app_id,
        "first_name": "Jane",
        "last_name": "Complete",
        "email": "jane.complete@example.com",
        "phone": "555-123-4567",
        "ssn": "987-65-4321",
        "date_of_birth": "1990-05-15",
        "address": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "employment_status": "active",
        "annual_income": 120000
    }

    enrichment = {
        'credit_enrichment': DataEnrichmentService.enrich_credit_data(applicant_data),
        'employment_enrichment': DataEnrichmentService.enrich_employment_data(applicant_data),
        'identity_enrichment': DataEnrichmentService.enrich_identity_data(applicant_data),
        'enriched_at': datetime.utcnow().isoformat()
    }
    applicant_data['enrichment_data'] = enrichment

    try:
        applicant_db.create_applicant(applicant_data)
        print(f"✓ Applicant created with enrichment data")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    # Step 2: Validate profile with all rules
    print("\nStep 2: Validate profile with all validation rules")
    applicant = applicant_db.get_applicant(app_id)
    errors = []
    for rule in VALIDATION_RULES.values():
        if rule.enabled:
            is_valid, error = rule.validate(applicant)
            if not is_valid:
                errors.append(error)
                print(f"  ✗ {error}")

    if not errors:
        print("  ✓ All validation rules passed!")
        applicant_db.update_validation_status(app_id, "valid")
    else:
        print(f"  ✗ Validation failed with {len(errors)} errors")
        applicant_db.update_validation_status(app_id, "invalid")

    # Step 3: Add credit data
    print("\nStep 3: Update credit history")
    credit_data = enrichment['credit_enrichment'].copy()
    credit_data['payment_history'] = ['on-time', 'on-time', 'on-time']
    try:
        record_id = applicant_db.add_credit_update(app_id, credit_data, updated_by="enrichment_service")
        print(f"✓ Credit history updated (record ID: {record_id})")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Step 4: Log to audit trail
    print("\nStep 4: Audit trail events logged")
    audit_trail.log_event(
        AuditEventType.PROFILE_CREATED,
        applicant_id=app_id,
        entity_type="applicant",
        action="create",
        new_values=applicant_data,
        status="success"
    )
    print("  ✓ PROFILE_CREATED logged")

    audit_trail.log_event(
        AuditEventType.DATA_ENRICHED,
        applicant_id=app_id,
        entity_type="enrichment",
        action="enrich",
        new_values=enrichment
    )
    print("  ✓ DATA_ENRICHED logged")

    # Step 5: Trigger webhooks
    print("\nStep 5: Webhook events triggered")
    webhook_manager.trigger_webhook('profile_updated', {
        'applicant_id': app_id,
        'event': 'profile_created',
        'timestamp': datetime.utcnow().isoformat()
    })
    print("  ✓ Profile update webhook triggered")

    webhook_manager.trigger_webhook('credit_updated', {
        'applicant_id': app_id,
        'event': 'credit_updated',
        'timestamp': datetime.utcnow().isoformat()
    })
    print("  ✓ Credit update webhook triggered")

    # Step 6: Retrieve complete profile
    print("\nStep 6: Retrieve complete enriched profile")
    applicant = applicant_db.get_applicant(app_id)
    credit_history = applicant_db.get_credit_history(app_id)
    history = audit_trail.get_history(app_id)

    print(f"  ✓ Applicant: {applicant['first_name']} {applicant['last_name']}")
    print(f"  ✓ Email: {applicant['email']}")
    print(f"  ✓ Validation Status: {applicant['validation_status']}")
    print(f"  ✓ Credit Records: {len(credit_history)}")
    print(f"  ✓ Audit Events: {len(history)}")
    if applicant.get('enrichment_data'):
        enrichment_stored = applicant['enrichment_data']
        print(f"  ✓ Enrichment Data Present:")
        print(f"    - Credit Score: {enrichment_stored.get('credit_enrichment', {}).get('credit_score')}")
        print(f"    - Identity Verified: {enrichment_stored.get('identity_enrichment', {}).get('identity_verified')}")
        print(f"    - Employment Verified: {enrichment_stored.get('employment_enrichment', {}).get('employment_verified')}")

    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  ENHANCED ApplicantDB MCP SERVER - COMPREHENSIVE TEST SUITE")
    print("="*80)

    tests = [
        ("Webhook Support", test_1_webhook_support),
        ("Batch Operations", test_2_batch_operations),
        ("Validation Rules", test_3_validation_rules),
        ("Audit Trail", test_4_audit_trail),
        ("Data Enrichment", test_5_data_enrichment),
        ("Integrated Workflow", test_6_integrated_workflow),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "PASSED" if result else "FAILED"
        except Exception as e:
            print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "FAILED"

    # Print summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v == "PASSED")
    failed = total - passed

    for test_name, result in results.items():
        status = "✓" if result == "PASSED" else "✗"
        print(f"{status} {test_name}: {result}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Enhanced ApplicantDB MCP server is fully functional.\n")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
