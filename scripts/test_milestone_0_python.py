#!/usr/bin/env python3
"""Python test script for Milestone 0 - Bootstrap & Infrastruttura."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env files
project_root = Path(__file__).parent.parent
backend_env = project_root / "apps" / "backend" / ".env"
collector_env = project_root / "apps" / "collector" / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
if collector_env.exists():
    load_dotenv(collector_env)

# Add project root to path
sys.path.insert(0, str(project_root / "apps" / "backend"))
sys.path.insert(0, str(project_root / "apps" / "collector"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

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
    print("🧪 Testing Milestone 0: Bootstrap & Infrastruttura (Python)")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Docker Compose exists", 
         (project_root / "infra" / "docker-compose.yml").exists())
    test("Backend main.py exists", 
         (project_root / "apps" / "backend" / "app" / "main.py").exists())
    test("Backend config.py exists", 
         (project_root / "apps" / "backend" / "core" / "config.py").exists())
    test("Collector main.py exists", 
         (project_root / "apps" / "collector" / "app" / "main.py").exists())
    test("Collector config.py exists", 
         (project_root / "apps" / "collector" / "core" / "config.py").exists())
    test("Backend requirements.txt exists", 
         (project_root / "apps" / "backend" / "requirements.txt").exists())
    test("Collector requirements.txt exists", 
         (project_root / "apps" / "collector" / "requirements.txt").exists())
    
    # 2. Check configuration files
    print("\n2. Checking configuration files...")
    backend_env = project_root / "apps" / "backend" / ".env"
    collector_env = project_root / "apps" / "collector" / ".env"
    test("Backend .env exists", backend_env.exists())
    test("Collector .env exists", collector_env.exists())
    
    # 3. Test imports (with proper env loading)
    print("\n3. Testing Python imports...")
    # Load backend env before importing
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "backend"))
        from app.main import app as backend_app
        test("Backend app imports successfully", True)
    except Exception as e:
        test("Backend app imports successfully", False, str(e))
    
    try:
        from core.config import settings as backend_settings
        test("Backend config imports successfully", True)
    except Exception as e:
        test("Backend config imports successfully", False, str(e))
    
    # Load collector env before importing
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "collector"))
        from app.main import app as collector_app
        test("Collector app imports successfully", True)
    except Exception as e:
        test("Collector app imports successfully", False, str(e))
    
    try:
        from core.config import settings as collector_settings
        test("Collector config imports successfully", True)
    except Exception as e:
        test("Collector config imports successfully", False, str(e))
    
    # 4. Test configuration loading
    print("\n4. Testing configuration loading...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "backend"))
        from core.config import settings
        test("Backend settings load", hasattr(settings, 'database_url') and settings.database_url is not None)
        test("Backend settings have Redis URL", hasattr(settings, 'redis_url') and settings.redis_url is not None)
        test("Backend settings have S3 config", hasattr(settings, 's3_bucket') and settings.s3_bucket is not None)
    except Exception as e:
        test("Backend settings load", False, str(e))
    
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "collector"))
        from core.config import settings as collector_settings
        test("Collector settings load", hasattr(collector_settings, 's3_bucket') and collector_settings.s3_bucket is not None)
    except Exception as e:
        test("Collector settings load", False, str(e))
    
    # 5. Test FastAPI app structure
    print("\n5. Testing FastAPI app structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "backend"))
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Backend has /health route", "/health" in routes)
        # Check if route exists (might be registered differently)
        has_api_health = "/api/v1/health" in routes or any("/api/v1/health" in str(route) for route in app.routes)
        test("Backend has /api/v1/health route", has_api_health)
    except Exception as e:
        test("Backend routes check", False, str(e))
    
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        sys.path.insert(0, str(project_root / "apps" / "collector"))
        from app.main import app as collector_app
        collector_routes = [route.path for route in collector_app.routes if hasattr(route, 'path')]
        test("Collector has /health route", "/health" in collector_routes)
    except Exception as e:
        test("Collector routes check", False, str(e))
    
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

