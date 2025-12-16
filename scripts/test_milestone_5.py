#!/usr/bin/env python3
"""Test script for Milestone 5 - Normalization & Export."""
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
    print("🧪 Testing Milestone 5: Normalization & Export")
    print("=" * 60)
    
    # 1. Check file structure
    print("\n1. Checking file structure...")
    test("Base normalizer exists", 
         (project_root / "apps" / "backend" / "normalizers" / "base.py").exists())
    test("Normalizer registry exists", 
         (project_root / "apps" / "backend" / "normalizers" / "registry.py").exists())
    test("Economics normalizer exists", 
         (project_root / "apps" / "backend" / "normalizers" / "economics.py").exists())
    test("Biomedical normalizer exists", 
         (project_root / "apps" / "backend" / "normalizers" / "biomedical.py").exists())
    test("Export service exists", 
         (project_root / "apps" / "backend" / "services" / "export_service.py").exists())
    test("Storage service exists", 
         (project_root / "apps" / "backend" / "services" / "storage_service.py").exists())
    
    # 2. Test imports
    print("\n2. Testing Python imports...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from normalizers.base import BaseNormalizer
        test("Base normalizer import", True)
    except Exception as e:
        test("Base normalizer import", False, str(e))
    
    try:
        from normalizers.registry import get_normalizer, list_normalizers
        test("Normalizer registry import", True)
    except Exception as e:
        test("Normalizer registry import", False, str(e))
    
    try:
        from normalizers.economics import EconomicsNormalizer
        test("Economics normalizer import", True)
    except Exception as e:
        test("Economics normalizer import", False, str(e))
    
    try:
        from normalizers.biomedical import BiomedicalNormalizer
        test("Biomedical normalizer import", True)
    except Exception as e:
        test("Biomedical normalizer import", False, str(e))
    
    try:
        from services.export_service import (
            export_to_csv, export_to_json, export_to_parquet,
            generate_manifest, generate_data_dictionary, create_bundle
        )
        test("Export service import", True)
    except Exception as e:
        test("Export service import", False, str(e))
    
    try:
        from services.storage_service import save_to_storage, generate_signed_url
        test("Storage service import", True)
    except Exception as e:
        test("Storage service import", False, str(e))
    
    # 3. Test normalizer registry
    print("\n3. Testing normalizer registry...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from normalizers import get_normalizer, list_normalizers
        normalizers = list_normalizers()
        test("Normalizers registered", len(normalizers) > 0)
        test("Economics normalizer registered", "economics" in normalizers)
        test("Biomedical normalizer registered", "biomedical" in normalizers)
        
        economics = get_normalizer("economics")
        test("Economics normalizer retrievable", economics is not None)
        
        biomedical = get_normalizer("biomedical")
        test("Biomedical normalizer retrievable", biomedical is not None)
    except Exception as e:
        test("Normalizer registry", False, str(e))
    
    # 4. Test normalizer functionality
    print("\n4. Testing normalizer functionality...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from normalizers import get_normalizer
        
        economics = get_normalizer("economics")
        if economics:
            test_records = [
                {"date": "2020-01-01", "value": 100},
                {"date": "2021-01-01", "value": 110}
            ]
            normalized = economics.normalize(test_records, [])
            test("Economics normalizer works", len(normalized) == 2)
            test("Economics normalizer validates", economics.validate(normalized))
        
        biomedical = get_normalizer("biomedical")
        if biomedical:
            test_records = [
                {"pmid": "123", "title": "Test", "abstract": "Test abstract"},
                {"pmid": "124", "title": "Test 2", "abstract": "Test abstract 2"}
            ]
            normalized = biomedical.normalize(test_records, [])
            test("Biomedical normalizer works", len(normalized) == 2)
            test("Biomedical normalizer validates", biomedical.validate(normalized))
    except Exception as e:
        test("Normalizer functionality", False, str(e))
    
    # 5. Test export functions
    print("\n5. Testing export functions...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from services.export_service import export_to_csv, export_to_json, generate_manifest, generate_data_dictionary
        
        test_records = [
            {"col1": "value1", "col2": 100},
            {"col1": "value2", "col2": 200}
        ]
        
        csv_data = export_to_csv(test_records)
        test("CSV export works", len(csv_data) > 0)
        
        json_data = export_to_json(test_records)
        test("JSON export works", len(json_data) > 0)
        
        manifest = generate_manifest(
            dataset_id="test-id",
            title="Test Dataset",
            domain="economics",
            sources=[],
            transformations=[],
            outputs=["csv"],
            row_count=2,
            created_at=__import__('datetime').datetime.utcnow()
        )
        test("Manifest generation works", "dataset_id" in manifest)
        
        data_dict = generate_data_dictionary(test_records)
        test("Data dictionary generation works", "columns" in data_dict)
    except Exception as e:
        test("Export functions", False, str(e))
    
    # 6. Test bundle creation
    print("\n6. Testing bundle creation...")
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
    try:
        from services.export_service import create_bundle
        from datetime import datetime
        
        test_records = [{"col1": "value1", "col2": 100}]
        manifest = {"dataset_id": "test", "title": "Test"}
        data_dict = {"columns": []}
        provenance = {"sources": []}
        
        bundle = create_bundle(
            records=test_records,
            manifest=manifest,
            data_dictionary=data_dict,
            provenance=provenance,
            outputs=["csv", "json"],
            dataset_id="test-id"
        )
        test("Bundle creation works", len(bundle) > 0)
        test("Bundle is ZIP format", bundle[:2] == b'PK')  # ZIP file signature
    except Exception as e:
        test("Bundle creation", False, str(e))
    
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

