#!/usr/bin/env python3
"""Test script for Milestone 6 - Pagamenti Stripe."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
backend_env = project_root / "apps" / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=True)

# Add project root to path
sys.path.insert(0, str(project_root / "apps" / "backend"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

tests_passed = 0
tests_failed = 0


def test(name, condition, error_msg=""):
    """Run a test."""
    global tests_passed, tests_failed
    if condition:
        print(f"{GREEN}✓{NC} {name}")
        tests_passed += 1
        return True
    else:
        print(f"{RED}✗{NC} {name}" + (f" - {error_msg}" if error_msg else ""))
        tests_failed += 1
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Milestone 6: Pagamenti Stripe")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Payment models exist", 
         (project_root / "apps" / "backend" / "db" / "models" / "payment.py").exists())
    test("Payment schemas exist", 
         (project_root / "apps" / "backend" / "schemas" / "payment.py").exists())
    test("Stripe service exists", 
         (project_root / "apps" / "backend" / "services" / "stripe_service.py").exists())
    test("Billing router exists", 
         (project_root / "apps" / "backend" / "api" / "routers" / "billing.py").exists())
    test("Payment migration exists", 
         (project_root / "apps" / "backend" / "alembic" / "versions" / "004_payments.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.payment import Payment, PaymentStatus, PaymentProvider
        test("Payment models import", True)
    except Exception as e:
        test("Payment models import", False, str(e))
    
    try:
        from schemas.payment import PaymentResponse, CheckoutResponse
        test("Payment schemas import", True)
    except Exception as e:
        test("Payment schemas import", False, str(e))
    
    try:
        from services.stripe_service import create_checkout_session, verify_webhook_signature
        test("Stripe service import", True)
    except Exception as e:
        test("Stripe service import", False, str(e))
    
    try:
        from api.routers.billing import router as billing_router
        test("Billing router import", True)
    except Exception as e:
        test("Billing router import", False, str(e))
    
    # 3. Test model structure
    print("\n3. Testing model structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.payment import Payment, PaymentStatus, PaymentProvider
        test("Payment has user_id", hasattr(Payment, 'user_id'))
        test("Payment has dataset_request_id", hasattr(Payment, 'dataset_request_id'))
        test("Payment has amount", hasattr(Payment, 'amount'))
        test("Payment has status", hasattr(Payment, 'status'))
        test("Payment has provider_ref", hasattr(Payment, 'provider_ref'))
        test("Payment has idempotency_key", hasattr(Payment, 'idempotency_key'))
        test("PaymentStatus enum exists", PaymentStatus.PENDING is not None)
        test("PaymentProvider enum exists", PaymentProvider.STRIPE is not None)
    except Exception as e:
        test("Model structure check", False, str(e))
    
    # 4. Test Stripe service structure
    print("\n4. Testing Stripe service structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        import stripe
        test("Stripe module available", stripe is not None)
        
        from services.stripe_service import create_checkout_session
        test("create_checkout_session function exists", callable(create_checkout_session))
        
        from services.stripe_service import verify_webhook_signature
        test("verify_webhook_signature function exists", callable(verify_webhook_signature))
    except Exception as e:
        test("Stripe service structure", False, str(e))
    
    # 5. Test router registration
    print("\n5. Testing router registration...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Checkout endpoint exists", "/api/v1/billing/checkout" in routes)
        test("Webhook endpoint exists", "/api/v1/billing/webhooks/stripe" in routes)
        test("Payments list endpoint exists", "/api/v1/billing/payments" in routes)
    except Exception as e:
        test("Router registration", False, str(e))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"{GREEN}Passed: {tests_passed}{NC}")
    if tests_failed > 0:
        print(f"{RED}Failed: {tests_failed}{NC}")
        return 1
    else:
        print(f"{GREEN}All tests passed!{NC}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

