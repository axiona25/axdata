#!/usr/bin/env python3
"""Verifica robustezza del sistema - error handling, transactions, validations."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
backend_env = project_root / "apps" / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=True)

sys.path.insert(0, str(project_root / "apps" / "backend"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

issues = []


def check_file(file_path, checks):
    """Check a file for issues."""
    if not file_path.exists():
        issues.append(f"{RED}✗{NC} File not found: {file_path}")
        return
    
    content = file_path.read_text()
    file_issues = []
    
    for check_name, check_func in checks.items():
        if not check_func(content):
            file_issues.append(f"  {RED}✗{NC} {check_name}")
        else:
            file_issues.append(f"  {GREEN}✓{NC} {check_name}")
    
    if any("✗" in issue for issue in file_issues):
        issues.append(f"\n{YELLOW}{file_path.name}:{NC}")
        issues.extend(file_issues)


def main():
    """Run robustness checks."""
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{BLUE}🔍 VERIFICA ROBUSTEZZA SISTEMA{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    backend_path = project_root / "apps" / "backend"
    
    # Check routers for error handling
    print(f"{YELLOW}Verifica Error Handling nei Router...{NC}")
    
    router_files = [
        backend_path / "api" / "routers" / "auth.py",
        backend_path / "api" / "routers" / "users.py",
        backend_path / "api" / "routers" / "chat.py",
        backend_path / "api" / "routers" / "datasets.py",
        backend_path / "api" / "routers" / "billing.py",
        backend_path / "api" / "routers" / "download.py",
    ]
    
    for router_file in router_files:
        if router_file.exists():
            content = router_file.read_text()
            
            # Check for try/except in critical operations
            has_try_except = "try:" in content and "except" in content
            has_db_commit = "db.commit()" in content
            has_error_logging = "logger.error" in content or "logger.warning" in content
            
            checks = {
                "Has error handling": has_try_except,
                "Has DB commits": has_db_commit,
                "Has error logging": has_error_logging,
            }
            
            check_file(router_file, checks)
    
    # Check services
    print(f"\n{YELLOW}Verifica Services...{NC}")
    
    service_files = [
        backend_path / "services" / "dataset_service.py",
        backend_path / "services" / "invoice_service.py",
        backend_path / "services" / "stripe_service.py",
        backend_path / "services" / "openai_service.py",
        backend_path / "services" / "storage_service.py",
    ]
    
    for service_file in service_files:
        if service_file.exists():
            content = service_file.read_text()
            
            checks = {
                "Has error handling": "try:" in content and "except" in content,
                "Has logging": "logger" in content,
            }
            
            check_file(service_file, checks)
    
    # Check models for proper structure
    print(f"\n{YELLOW}Verifica Database Models...{NC}")
    
    model_files = [
        backend_path / "db" / "models" / "user.py",
        backend_path / "db" / "models" / "dataset.py",
        backend_path / "db" / "models" / "payment.py",
        backend_path / "db" / "models" / "invoice.py",
    ]
    
    for model_file in model_files:
        if model_file.exists():
            content = model_file.read_text()
            
            checks = {
                "Has Base inheritance": "Base" in content,
                "Has __repr__": "__repr__" in content,
                "Has proper imports": "from db.session import Base" in content,
            }
            
            check_file(model_file, checks)
    
    # Summary
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}📊 RISULTATI VERIFICA{NC}")
    print(f"{BLUE}{'='*70}{NC}")
    
    if issues:
        print("\n".join(issues))
        print(f"\n{RED}Trovati {len([i for i in issues if '✗' in i])} problemi potenziali{NC}")
    else:
        print(f"{GREEN}Nessun problema trovato! Sistema robusto.{NC}")
    
    print(f"\n{BLUE}{'='*70}{NC}")
    
    return 0 if not issues or len([i for i in issues if '✗' in i]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

