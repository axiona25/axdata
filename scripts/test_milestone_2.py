#!/usr/bin/env python3
"""Test script for Milestone 2 - Chat & OpenAI Integration."""
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
    print("🧪 Testing Milestone 2: Chat & OpenAI Integration")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Chat models exist", 
         (project_root / "apps" / "backend" / "db" / "models" / "chat.py").exists())
    test("Chat schemas exist", 
         (project_root / "apps" / "backend" / "schemas" / "chat.py").exists())
    test("DatasetPlan schema exists", 
         (project_root / "apps" / "backend" / "schemas" / "dataset_plan.py").exists())
    test("OpenAI service exists", 
         (project_root / "apps" / "backend" / "services" / "openai_service.py").exists())
    test("Chat router exists", 
         (project_root / "apps" / "backend" / "api" / "routers" / "chat.py").exists())
    test("Chat migration exists", 
         (project_root / "apps" / "backend" / "alembic" / "versions" / "002_chat_sessions_messages.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.chat import ChatSession, ChatMessage
        test("Chat models import", True)
    except Exception as e:
        test("Chat models import", False, str(e))
    
    try:
        from schemas.chat import ChatMessageCreate, ChatSessionResponse
        test("Chat schemas import", True)
    except Exception as e:
        test("Chat schemas import", False, str(e))
    
    try:
        from schemas.dataset_plan import DatasetPlan, DATASET_PLAN_TOOL_SCHEMA
        test("DatasetPlan schema import", True)
    except Exception as e:
        test("DatasetPlan schema import", False, str(e))
    
    try:
        from services.openai_service import chat_completion_stream, chat_completion_with_tool
        test("OpenAI service import", True)
    except Exception as e:
        test("OpenAI service import", False, str(e))
    
    try:
        from api.routers.chat import router as chat_router
        test("Chat router import", True)
    except Exception as e:
        test("Chat router import", False, str(e))
    
    # 3. Test model structure
    print("\n3. Testing model structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from db.models.chat import ChatSession, ChatMessage
        test("ChatSession has user_id", hasattr(ChatSession, 'user_id'))
        test("ChatSession has title", hasattr(ChatSession, 'title'))
        test("ChatMessage has session_id", hasattr(ChatMessage, 'session_id'))
        test("ChatMessage has role", hasattr(ChatMessage, 'role'))
        test("ChatMessage has content", hasattr(ChatMessage, 'content'))
        test("ChatMessage has metadata", hasattr(ChatMessage, 'metadata'))
    except Exception as e:
        test("Model structure check", False, str(e))
    
    # 4. Test DatasetPlan schema
    print("\n4. Testing DatasetPlan schema...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from schemas.dataset_plan import DatasetPlan, Domain, SourcePlan
        # Test creating a valid plan
        plan = DatasetPlan(
            domain=Domain.ECONOMICS,
            title="Test Dataset",
            sources=[
                SourcePlan(
                    connector="worldbank",
                    queries=[{"indicator": "GDP"}]
                )
            ]
        )
        test("DatasetPlan creation works", plan.title == "Test Dataset")
        test("DatasetPlan has domain", plan.domain == Domain.ECONOMICS)
        test("DatasetPlan has sources", len(plan.sources) > 0)
    except Exception as e:
        test("DatasetPlan schema", False, str(e))
    
    # 5. Test OpenAI service (without actual API call)
    print("\n5. Testing OpenAI service structure...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from services.openai_service import DATASET_PLAN_TOOL_SCHEMA, client
        test("OpenAI client initialized", client is not None)
        test("Tool schema exists", DATASET_PLAN_TOOL_SCHEMA is not None)
        test("Tool schema has function", "function" in DATASET_PLAN_TOOL_SCHEMA)
        test("Tool function name correct", 
             DATASET_PLAN_TOOL_SCHEMA.get("function", {}).get("name") == "create_dataset_plan")
    except Exception as e:
        test("OpenAI service structure", False, str(e))
    
    # 6. Test router registration
    print("\n6. Testing router registration...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Chat sessions create route exists", "/api/v1/chat/sessions" in routes)
        test("Chat sessions list route exists", "/api/v1/chat/sessions" in routes)
        test("Chat messages create route exists", "/api/v1/chat/sessions/{session_id}/messages" in routes)
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

