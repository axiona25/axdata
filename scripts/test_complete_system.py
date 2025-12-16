#!/usr/bin/env python3
"""Complete system test - verifica tutto il backend."""
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
BLUE = '\033[0;34m'
NC = '\033[0m'

tests_passed = 0
tests_failed = 0
errors = []


def test(name, condition, error_msg=""):
    """Run a test."""
    global tests_passed, tests_failed, errors
    if condition:
        print(f"{GREEN}✓{NC} {name}")
        tests_passed += 1
        return True
    else:
        print(f"{RED}✗{NC} {name}" + (f" - {error_msg}" if error_msg else ""))
        tests_failed += 1
        errors.append(f"{name}: {error_msg}")
        return False


def main():
    """Run all tests."""
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{BLUE}🧪 TEST COMPLETO SISTEMA - Dataset On-Demand Portal{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    # 1. File Structure
    print(f"{YELLOW}1. Verifica Struttura File{NC}")
    print("-" * 70)
    
    backend_path = project_root / "apps" / "backend"
    test("Backend directory exists", backend_path.exists())
    test("Main app file exists", (backend_path / "app" / "main.py").exists())
    test("Config file exists", (backend_path / "core" / "config.py").exists())
    test("Database models directory exists", (backend_path / "db" / "models").exists())
    test("API routers directory exists", (backend_path / "api" / "routers").exists())
    test("Services directory exists", (backend_path / "services").exists())
    test("Workers directory exists", (backend_path / "workers").exists())
    test("Schemas directory exists", (backend_path / "schemas").exists())
    test("Alembic directory exists", (backend_path / "alembic").exists())
    
    # 2. Database Models
    print(f"\n{YELLOW}2. Verifica Database Models{NC}")
    print("-" * 70)
    
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    
    try:
        from db.models import (
            User, UserProfile,
            ChatSession, ChatMessage,
            DatasetRequest, DatasetStep, DatasetStatus, StepStatus, StepType,
            Payment, PaymentStatus, PaymentProvider,
            Invoice, InvoiceStatus,
            AuditLog, AuditAction
        )
        test("All models import successfully", True)
        test("User model has required fields", hasattr(User, 'email') and hasattr(User, 'deleted_at'))
        test("DatasetRequest model exists", DatasetRequest is not None)
        test("Payment model exists", Payment is not None)
        test("Invoice model exists", Invoice is not None)
        test("AuditLog model exists", AuditLog is not None)
    except Exception as e:
        test("All models import successfully", False, str(e))
    
    # 3. Core Configuration
    print(f"\n{YELLOW}3. Verifica Core Configuration{NC}")
    print("-" * 70)
    
    try:
        from core.config import settings
        test("Settings loaded", settings is not None)
        test("signed_url_ttl configured", hasattr(settings, 'signed_url_ttl'))
        test("user_purge_retention_days configured", hasattr(settings, 'user_purge_retention_days'))
        test("CORS origins list property", hasattr(settings, 'cors_origins_list'))
    except Exception as e:
        test("Settings loaded", False, str(e))
    
    # 4. Security & Dependencies
    print(f"\n{YELLOW}4. Verifica Security & Dependencies{NC}")
    print("-" * 70)
    
    try:
        from core.security import (
            verify_password, get_password_hash,
            create_access_token, create_refresh_token, decode_token
        )
        test("Security functions import", True)
        test("Password hashing function exists", callable(get_password_hash))
        test("Token creation function exists", callable(create_access_token))
    except Exception as e:
        test("Security functions import", False, str(e))
    
    try:
        from core.dependencies import get_current_user, get_current_active_user
        test("Dependencies import", True)
    except Exception as e:
        test("Dependencies import", False, str(e))
    
    # 5. API Routers
    print(f"\n{YELLOW}5. Verifica API Routers{NC}")
    print("-" * 70)
    
    try:
        from api.routers import auth, users, chat, datasets, billing, download, audit
        test("All routers import", True)
        test("Auth router exists", auth.router is not None)
        test("Users router exists", users.router is not None)
        test("Chat router exists", chat.router is not None)
        test("Datasets router exists", datasets.router is not None)
        test("Billing router exists", billing.router is not None)
        test("Download router exists", download.router is not None)
        test("Audit router exists", audit.router is not None)
    except Exception as e:
        test("All routers import", False, str(e))
    
    # 6. Services
    print(f"\n{YELLOW}6. Verifica Services{NC}")
    print("-" * 70)
    
    try:
        from services.storage_service import generate_signed_url, save_to_storage
        test("Storage service import", True)
        test("generate_signed_url function exists", callable(generate_signed_url))
    except Exception as e:
        test("Storage service import", False, str(e))
    
    try:
        from services.dataset_service import create_dataset_request_from_plan, update_dataset_status
        test("Dataset service import", True)
    except Exception as e:
        test("Dataset service import", False, str(e))
    
    try:
        from services.invoice_service import generate_invoice_number, create_invoice_from_payment
        test("Invoice service import", True)
    except Exception as e:
        test("Invoice service import", False, str(e))
    
    try:
        from services.stripe_service import create_checkout_session, verify_webhook_signature
        test("Stripe service import", True)
    except Exception as e:
        test("Stripe service import", False, str(e))
    
    try:
        from services.openai_service import chat_completion_with_tool
        test("OpenAI service import", True)
    except Exception as e:
        test("OpenAI service import", False, str(e))
    
    # 7. Workers
    print(f"\n{YELLOW}7. Verifica Workers{NC}")
    print("-" * 70)
    
    try:
        from workers.celery_app import celery_app
        test("Celery app import", True)
        test("Celery app configured", celery_app is not None)
    except Exception as e:
        test("Celery app import", False, str(e))
    
    try:
        from workers.tasks import process_dataset_request
        test("Celery tasks import", True)
    except Exception as e:
        test("Celery tasks import", False, str(e))
    
    try:
        from workers.purge_tasks import purge_deleted_users
        test("Purge tasks import", True)
    except Exception as e:
        test("Purge tasks import", False, str(e))
    
    # 8. Schemas
    print(f"\n{YELLOW}8. Verifica Schemas{NC}")
    print("-" * 70)
    
    try:
        from schemas.dataset import DatasetRequestCreate, DatasetRequestResponse
        test("Dataset schemas import", True)
    except Exception as e:
        test("Dataset schemas import", False, str(e))
    
    try:
        from schemas.chat import ChatSessionCreate, ChatMessageCreate
        test("Chat schemas import", True)
    except Exception as e:
        test("Chat schemas import", False, str(e))
    
    try:
        from schemas.payment import PaymentResponse, CheckoutResponse
        test("Payment schemas import", True)
    except Exception as e:
        test("Payment schemas import", False, str(e))
    
    try:
        from schemas.invoice import InvoiceResponse
        test("Invoice schemas import", True)
    except Exception as e:
        test("Invoice schemas import", False, str(e))
    
    try:
        from schemas.audit import AuditLogResponse
        test("Audit schemas import", True)
    except Exception as e:
        test("Audit schemas import", False, str(e))
    
    # 9. Main App
    print(f"\n{YELLOW}9. Verifica Main Application{NC}")
    print("-" * 70)
    
    try:
        from app.main import app
        test("Main app import", True)
        test("FastAPI app created", app is not None)
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Health endpoint exists", "/health" in routes)
        test("API health endpoint exists", "/api/v1/health" in routes)
        test("Auth endpoints exist", any("/api/v1/auth" in r for r in routes))
        test("Dataset endpoints exist", any("/api/v1/datasets" in r for r in routes))
        test("Billing endpoints exist", any("/api/v1/billing" in r for r in routes))
        test("Download endpoints exist", any("/api/v1/download" in r for r in routes))
        test("Audit endpoints exist", any("/api/v1/audit" in r for r in routes))
    except Exception as e:
        test("Main app import", False, str(e))
    
    # 10. Middleware
    print(f"\n{YELLOW}10. Verifica Middleware{NC}")
    print("-" * 70)
    
    try:
        from core.middleware import SecurityHeadersMiddleware
        test("Security middleware import", True)
    except Exception as e:
        test("Security middleware import", False, str(e))
    
    # 11. Migrations
    print(f"\n{YELLOW}11. Verifica Migrazioni Alembic{NC}")
    print("-" * 70)
    
    migrations_path = backend_path / "alembic" / "versions"
    if migrations_path.exists():
        migrations = list(migrations_path.glob("*.py"))
        test("Migrations directory exists", True)
        test("Initial users migration exists", any("001" in m.name for m in migrations))
        test("Chat migration exists", any("002" in m.name for m in migrations))
        test("Dataset migration exists", any("003" in m.name for m in migrations))
        test("Payments migration exists", any("004" in m.name for m in migrations))
        test("Invoices migration exists", any("005" in m.name for m in migrations))
        test("Audit logs migration exists", any("006" in m.name for m in migrations))
    else:
        test("Migrations directory exists", False)
    
    # 12. Collector Service
    print(f"\n{YELLOW}12. Verifica Collector Service{NC}")
    print("-" * 70)
    
    collector_path = project_root / "apps" / "collector"
    test("Collector directory exists", collector_path.exists())
    test("Collector main file exists", (collector_path / "app" / "main.py").exists())
    test("Connectors directory exists", (collector_path / "connectors").exists())
    
    try:
        sys.path.insert(0, str(collector_path))
        from connectors.registry import get_connector
        test("Connector registry import", True)
        test("get_connector function exists", callable(get_connector))
    except Exception as e:
        test("Connector registry import", False, str(e))
    
    # Summary
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}📊 RISULTATI TEST{NC}")
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{GREEN}Test Passati: {tests_passed}{NC}")
    if tests_failed > 0:
        print(f"{RED}Test Falliti: {tests_failed}{NC}")
        print(f"\n{RED}Errori Trovati:{NC}")
        for error in errors[:10]:  # Mostra primi 10 errori
            print(f"  {RED}•{NC} {error}")
        if len(errors) > 10:
            print(f"  {YELLOW}... e altri {len(errors) - 10} errori{NC}")
    else:
        print(f"{GREEN}Nessun errore trovato!{NC}")
    
    print(f"\n{BLUE}{'='*70}{NC}")
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

