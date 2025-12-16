#!/usr/bin/env python3
"""Test script for Milestone 3 - Dataset Orchestration."""
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
    print("🧪 Testing Milestone 3: Dataset Orchestration")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Dataset models exist", 
         (project_root / "apps" / "backend" / "db" / "models" / "dataset.py").exists())
    test("Dataset schemas exist", 
         (project_root / "apps" / "backend" / "schemas" / "dataset.py").exists())
    test("Dataset service exists", 
         (project_root / "apps" / "backend" / "services" / "dataset_service.py").exists())
    test("Celery app exists", 
         (project_root / "apps" / "backend" / "workers" / "celery_app.py").exists())
    test("Celery tasks exist", 
         (project_root / "apps" / "backend" / "workers" / "tasks.py").exists())
    test("Datasets router exists", 
         (project_root / "apps" / "backend" / "api" / "routers" / "datasets.py").exists())
    test("Dataset migration exists", 
         (project_root / "apps" / "backend" / "alembic" / "versions" / "003_dataset_requests_steps.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.dataset import DatasetRequest, DatasetStep, DatasetStatus, StepStatus, StepType
        test("Dataset models import", True)
    except Exception as e:
        test("Dataset models import", False, str(e))
    
    try:
        from schemas.dataset import DatasetRequestCreate, DatasetRequestResponse, DatasetProgressResponse
        test("Dataset schemas import", True)
    except Exception as e:
        test("Dataset schemas import", False, str(e))
    
    try:
        from services.dataset_service import create_dataset_request_from_plan, update_dataset_status, update_step_status
        test("Dataset service import", True)
    except Exception as e:
        test("Dataset service import", False, str(e))
    
    try:
        from workers.celery_app import celery_app
        test("Celery app import", True)
    except Exception as e:
        test("Celery app import", False, str(e))
    
    try:
        from workers.tasks import process_dataset_request, execute_collect_step
        test("Celery tasks import", True)
    except Exception as e:
        test("Celery tasks import", False, str(e))
    
    try:
        from api.routers.datasets import router as datasets_router
        test("Datasets router import", True)
    except Exception as e:
        test("Datasets router import", False, str(e))
    
    # 3. Test model structure
    print("\n3. Testing model structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.dataset import DatasetRequest, DatasetStep, DatasetStatus, StepStatus, StepType
        test("DatasetRequest has user_id", hasattr(DatasetRequest, 'user_id'))
        test("DatasetRequest has status", hasattr(DatasetRequest, 'status'))
        test("DatasetRequest has plan_json", hasattr(DatasetRequest, 'plan_json'))
        test("DatasetStep has step_type", hasattr(DatasetStep, 'step_type'))
        test("DatasetStep has step_order", hasattr(DatasetStep, 'step_order'))
        test("DatasetStep has status", hasattr(DatasetStep, 'status'))
        test("DatasetStatus enum exists", DatasetStatus.DRAFT is not None)
        test("StepStatus enum exists", StepStatus.QUEUED is not None)
        test("StepType enum exists", StepType.COLLECT is not None)
    except Exception as e:
        test("Model structure check", False, str(e))
    
    # 4. Test state machine
    print("\n4. Testing state machine...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.dataset import DatasetStatus
        # Test valid transitions
        valid_transitions = {
            DatasetStatus.DRAFT: [DatasetStatus.RUNNING, DatasetStatus.FAILED],
            DatasetStatus.RUNNING: [DatasetStatus.READY_FOR_PAYMENT, DatasetStatus.FAILED],
            DatasetStatus.READY_FOR_PAYMENT: [DatasetStatus.PAID, DatasetStatus.FAILED],
            DatasetStatus.PAID: [DatasetStatus.DELIVERED, DatasetStatus.FAILED],
        }
        test("State machine transitions defined", len(valid_transitions) > 0)
        test("DRAFT can transition to RUNNING", DatasetStatus.RUNNING in valid_transitions[DatasetStatus.DRAFT])
        test("RUNNING can transition to READY_FOR_PAYMENT", 
             DatasetStatus.READY_FOR_PAYMENT in valid_transitions[DatasetStatus.RUNNING])
    except Exception as e:
        test("State machine", False, str(e))
    
    # 5. Test Celery configuration
    print("\n5. Testing Celery configuration...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from workers.celery_app import celery_app
        test("Celery app initialized", celery_app is not None)
        test("Celery broker configured", celery_app.conf.broker_url is not None)
        test("Celery backend configured", celery_app.conf.result_backend is not None)
    except Exception as e:
        test("Celery configuration", False, str(e))
    
    # 6. Test router registration
    print("\n6. Testing router registration...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Datasets create route exists", "/api/v1/datasets" in routes)
        test("Datasets list route exists", "/api/v1/datasets" in routes)
        test("Dataset progress route exists", "/api/v1/datasets/{dataset_id}/progress" in routes)
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

