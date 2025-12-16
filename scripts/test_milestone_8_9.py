#!/usr/bin/env python3
"""Test script for Milestone 8 & 9 - Storage & Download, Audit."""
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
    print("🧪 Testing Milestone 8 & 9: Storage & Download, Audit")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Audit log models exist", 
         (project_root / "apps" / "backend" / "db" / "models" / "audit_log.py").exists())
    test("Audit schemas exist", 
         (project_root / "apps" / "backend" / "schemas" / "audit.py").exists())
    test("Audit router exists", 
         (project_root / "apps" / "backend" / "api" / "routers" / "audit.py").exists())
    test("Audit migration exists", 
         (project_root / "apps" / "backend" / "alembic" / "versions" / "006_audit_logs.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.audit_log import AuditLog, AuditAction
        test("Audit log models import", True)
    except Exception as e:
        test("Audit log models import", False, str(e))
    
    try:
        from schemas.audit import AuditLogResponse, AuditLogListResponse
        test("Audit schemas import", True)
    except Exception as e:
        test("Audit schemas import", False, str(e))
    
    try:
        from api.routers.audit import router as audit_router
        test("Audit router import", True)
    except Exception as e:
        test("Audit router import", False, str(e))
    
    # 3. Test model structure
    print("\n3. Testing model structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.audit_log import AuditLog, AuditAction
        test("AuditLog has action", hasattr(AuditLog, 'action'))
        test("AuditLog has resource_type", hasattr(AuditLog, 'resource_type'))
        test("AuditLog has trace_id", hasattr(AuditLog, 'trace_id'))
        test("AuditAction enum exists", AuditAction.DATASET_DOWNLOAD is not None)
    except Exception as e:
        test("Model structure check", False, str(e))
    
    # 4. Test download endpoints
    print("\n4. Testing download endpoints...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Dataset download endpoint exists", "/api/v1/download/datasets/{dataset_id}" in routes)
        test("Invoice download endpoint exists", "/api/v1/billing/invoices/{invoice_id}/download" in routes)
    except Exception as e:
        test("Download endpoints", False, str(e))
    
    # 5. Test audit endpoints
    print("\n5. Testing audit endpoints...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Audit logs list endpoint exists", "/api/v1/audit/logs" in routes)
        test("Audit log detail endpoint exists", "/api/v1/audit/logs/{log_id}" in routes)
    except Exception as e:
        test("Audit endpoints", False, str(e))
    
    # 6. Test dataset clone and history
    print("\n6. Testing dataset clone and history...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Dataset clone endpoint exists", "/api/v1/datasets/{dataset_id}/clone" in routes)
        test("Dataset history endpoint exists", "/api/v1/datasets/{dataset_id}/history" in routes)
    except Exception as e:
        test("Dataset clone/history", False, str(e))
    
    # 7. Test signed URL TTL config
    print("\n7. Testing signed URL TTL configuration...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from core.config import settings
        test("signed_url_ttl exists", hasattr(settings, 'signed_url_ttl'))
        test("signed_url_ttl is int", isinstance(settings.signed_url_ttl, int))
    except Exception as e:
        test("Signed URL TTL config", False, str(e))
    
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

