#!/usr/bin/env python3
"""Test script for Milestone 4 - Collector Connectors MVP."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
collector_env = project_root / "apps" / "collector" / ".env"
if collector_env.exists():
    load_dotenv(collector_env, override=True)

# Add project root to path
sys.path.insert(0, str(project_root / "apps" / "collector"))

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
    print("🧪 Testing Milestone 4: Collector Connectors MVP")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Base connector exists", 
         (project_root / "apps" / "collector" / "connectors" / "base.py").exists())
    test("Connector registry exists", 
         (project_root / "apps" / "collector" / "connectors" / "registry.py").exists())
    test("WorldBank connector exists", 
         (project_root / "apps" / "collector" / "connectors" / "worldbank.py").exists())
    test("Eurostat connector exists", 
         (project_root / "apps" / "collector" / "connectors" / "eurostat.py").exists())
    test("PubMed connector exists", 
         (project_root / "apps" / "collector" / "connectors" / "pubmed.py").exists())
    test("HTTP client exists", 
         (project_root / "apps" / "collector" / "client" / "http_client.py").exists())
    test("Storage service exists", 
         (project_root / "apps" / "collector" / "services" / "storage_service.py").exists())
    test("Collect router exists", 
         (project_root / "apps" / "collector" / "app" / "routers" / "collect.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        from connectors.base import BaseConnector, ConnectorOutput
        test("Base connector import", True)
    except Exception as e:
        test("Base connector import", False, str(e))
    
    try:
        from connectors.registry import register_connector, get_connector, list_connectors
        test("Connector registry import", True)
    except Exception as e:
        test("Connector registry import", False, str(e))
    
    try:
        from connectors.worldbank import WorldBankConnector
        test("WorldBank connector import", True)
    except Exception as e:
        test("WorldBank connector import", False, str(e))
    
    try:
        from connectors.eurostat import EurostatConnector
        test("Eurostat connector import", True)
    except Exception as e:
        test("Eurostat connector import", False, str(e))
    
    try:
        from connectors.pubmed import PubMedConnector
        test("PubMed connector import", True)
    except Exception as e:
        test("PubMed connector import", False, str(e))
    
    try:
        from client.http_client import get_client, make_request_with_retry
        test("HTTP client import", True)
    except Exception as e:
        test("HTTP client import", False, str(e))
    
    try:
        from services.storage_service import save_raw_asset, get_raw_asset
        test("Storage service import", True)
    except Exception as e:
        test("Storage service import", False, str(e))
    
    # 3. Test connector registry
    print("\n3. Testing connector registry...")
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        from connectors import get_connector, list_connectors
        connectors = list_connectors()
        test("Connectors registered", len(connectors) > 0)
        test("WorldBank connector registered", "worldbank" in connectors)
        test("Eurostat connector registered", "eurostat" in connectors)
        test("PubMed connector registered", "pubmed" in connectors)
        
        worldbank = get_connector("worldbank")
        test("WorldBank connector retrievable", worldbank is not None)
        
        eurostat = get_connector("eurostat")
        test("Eurostat connector retrievable", eurostat is not None)
        
        pubmed = get_connector("pubmed")
        test("PubMed connector retrievable", pubmed is not None)
    except Exception as e:
        test("Connector registry", False, str(e))
    
    # 4. Test connector structure
    print("\n4. Testing connector structure...")
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        from connectors import get_connector
        worldbank = get_connector("worldbank")
        if worldbank:
            test("WorldBank has validate_query", hasattr(worldbank, 'validate_query'))
            test("WorldBank has fetch", hasattr(worldbank, 'fetch'))
            test("WorldBank has connect", hasattr(worldbank, 'connect'))
        
        eurostat = get_connector("eurostat")
        if eurostat:
            test("Eurostat has validate_query", hasattr(eurostat, 'validate_query'))
            test("Eurostat has fetch", hasattr(eurostat, 'fetch'))
        
        pubmed = get_connector("pubmed")
        if pubmed:
            test("PubMed has validate_query", hasattr(pubmed, 'validate_query'))
            test("PubMed has fetch", hasattr(pubmed, 'fetch'))
    except Exception as e:
        test("Connector structure", False, str(e))
    
    # 5. Test query validation
    print("\n5. Testing query validation...")
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        from connectors import get_connector
        
        worldbank = get_connector("worldbank")
        if worldbank:
            valid_query = {"indicator": "NY.GDP.MKTP.CD", "country": "US"}
            invalid_query = {"indicator": "NY.GDP.MKTP.CD"}
            test("WorldBank validates correct query", worldbank.validate_query(valid_query))
            test("WorldBank rejects invalid query", not worldbank.validate_query(invalid_query))
        
        eurostat = get_connector("eurostat")
        if eurostat:
            valid_query = {"dataset_code": "prc_hicp_midx"}
            invalid_query = {}
            test("Eurostat validates correct query", eurostat.validate_query(valid_query))
            test("Eurostat rejects invalid query", not eurostat.validate_query(invalid_query))
        
        pubmed = get_connector("pubmed")
        if pubmed:
            valid_query1 = {"term": "covid-19"}
            valid_query2 = {"pmid": "12345678"}
            invalid_query = {}
            test("PubMed validates term query", pubmed.validate_query(valid_query1))
            test("PubMed validates pmid query", pubmed.validate_query(valid_query2))
            test("PubMed rejects invalid query", not pubmed.validate_query(invalid_query))
    except Exception as e:
        test("Query validation", False, str(e))
    
    # 6. Test router registration
    print("\n6. Testing router registration...")
    if collector_env.exists():
        load_dotenv(collector_env, override=True)
    try:
        from app.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        test("Collect endpoint exists", "/collect" in routes)
        test("Connectors list endpoint exists", "/connectors" in routes)
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

