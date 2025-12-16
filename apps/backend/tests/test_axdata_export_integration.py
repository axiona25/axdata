"""Tests for AXDATA export integration."""
import pytest
from unittest.mock import Mock, patch
from services.axdata_export_integration import (
    is_axdata_dataset,
    create_axdata_package_from_export,
    integrate_axdata_export
)


def test_is_axdata_dataset_with_ds_spec():
    """Test detection of AXDATA dataset with DS-SPEC."""
    plan_json = {
        "version": "1.0",
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        },
        "output": {"template": "auto"}
    }
    
    assert is_axdata_dataset(plan_json) is True


def test_is_axdata_dataset_with_pipeline_result():
    """Test detection of AXDATA dataset with pipeline result."""
    plan_json = {
        "pipeline_result": {
            "template": "time_series",
            "selected_sources": ["eurostat"]
        }
    }
    
    assert is_axdata_dataset(plan_json) is True


def test_is_axdata_dataset_legacy():
    """Test detection of legacy dataset (not AXDATA)."""
    plan_json = {
        "domain": "economics",
        "title": "GDP Data",
        "sources": []
    }
    
    assert is_axdata_dataset(plan_json) is False


def test_is_axdata_dataset_invalid():
    """Test with invalid plan_json."""
    assert is_axdata_dataset(None) is False
    assert is_axdata_dataset("not a dict") is False
    assert is_axdata_dataset({}) is False


@patch('services.axdata_export_integration.package_dataset')
@patch('services.axdata_export_integration.export_to_csv')
def test_create_axdata_package(mock_csv, mock_package):
    """Test AXDATA package creation."""
    import tempfile
    from pathlib import Path
    
    mock_csv.return_value = b"col1,col2\nval1,val2\n"
    
    plan_json = {
        "version": "1.0",
        "request": {"query_text": "Test"},
        "sector": "health",
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "auto", "formats": ["csv"]}
    }
    
    records = [{"col1": "val1", "col2": "val2"}]
    sources = [{"source_id": "eurostat", "name": "Eurostat"}]
    
    # Create a real temporary ZIP for the mock
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"
        zip_path.write_bytes(b"fake zip content")
        
        mock_package.return_value = {
            "package_dir": tmpdir,
            "zip_path": str(zip_path)
        }
        
        result = create_axdata_package_from_export(
            records=records,
            dataset_id="test-id",
            plan_json=plan_json,
            sources_used=sources,
            outputs=["csv"]
        )
        
        assert result is not None
        assert isinstance(result, bytes)
        mock_package.assert_called_once()


@patch('services.axdata_export_integration.is_axdata_dataset')
@patch('services.axdata_export_integration.create_axdata_package_from_export')
@patch('services.export_service.create_bundle')
def test_integrate_axdata_export_uses_axdata(mock_bundle, mock_axdata, mock_is_axdata):
    """Test integration uses AXDATA packager when available."""
    mock_is_axdata.return_value = True
    mock_axdata.return_value = b"axdata_zip_bytes"
    
    plan_json = {"version": "1.0", "dimensions": {}}
    result = integrate_axdata_export(
        records=[],
        dataset_id="test",
        plan_json=plan_json,
        sources=[],
        outputs=["csv"]
    )
    
    assert result == b"axdata_zip_bytes"
    mock_axdata.assert_called_once()
    mock_bundle.assert_not_called()


@patch('services.axdata_export_integration.is_axdata_dataset')
@patch('services.export_service.create_bundle')
def test_integrate_axdata_export_fallback(mock_bundle, mock_is_axdata):
    """Test integration falls back to standard export."""
    mock_is_axdata.return_value = False
    mock_bundle.return_value = b"standard_zip_bytes"
    
    plan_json = {"domain": "economics"}
    result = integrate_axdata_export(
        records=[],
        dataset_id="test",
        plan_json=plan_json,
        sources=[],
        outputs=["csv"]
    )
    
    assert result == b"standard_zip_bytes"
    mock_bundle.assert_called_once()
