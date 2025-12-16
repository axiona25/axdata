"""Tests for template transformers."""
import pytest
from axdata.transformers.registry import get_transformer, list_transformers
from axdata.transformers.tabular_transformer import TabularTransformer
from axdata.transformers.time_series_transformer import TimeSeriesTransformer
from axdata.transformers.panel_transformer import PanelTransformer


def test_transformer_registry():
    """Test transformer registry."""
    transformers = list_transformers()
    assert len(transformers) == 8
    assert "tabular" in transformers
    assert "time_series" in transformers
    assert "panel" in transformers


def test_get_transformer():
    """Test getting transformer by name."""
    transformer = get_transformer("tabular")
    assert transformer is not None
    assert transformer.template_name == "tabular"
    
    transformer = get_transformer("invalid")
    assert transformer is None


def test_tabular_transformer():
    """Test tabular transformer."""
    transformer = TabularTransformer()
    
    raw_data = [
        {"id": 1, "value": 10, "category": "A"},
        {"id": 2, "value": 20, "category": "B"}
    ]
    
    ds_spec = {
        "variables": [{"name": "value", "type": "numeric"}],
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        }
    }
    
    result = transformer.transform(raw_data, ds_spec)
    
    assert len(result) == 2
    assert result[0]["value"] == 10


def test_time_series_transformer():
    """Test time series transformer."""
    transformer = TimeSeriesTransformer()
    
    raw_data = [
        {"date": "2020-01-01", "value": 100},
        {"date": "2021-01-01", "value": 110},
        {"date": "2022-01-01", "value": 120}
    ]
    
    ds_spec = {
        "variables": [{"name": "value", "type": "numeric"}],
        "dimensions": {
            "time": {"enabled": True, "granularity": "year"},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        }
    }
    
    result = transformer.transform(raw_data, ds_spec)
    
    assert len(result) == 3
    # Should have timestamp column
    assert any("timestamp" in str(r).lower() or "date" in str(r).lower() for r in result)


def test_panel_transformer():
    """Test panel transformer."""
    transformer = PanelTransformer()
    
    raw_data = [
        {"country": "IT", "year": "2020", "gdp": 1000},
        {"country": "IT", "year": "2021", "gdp": 1100},
        {"country": "FR", "year": "2020", "gdp": 2000}
    ]
    
    ds_spec = {
        "variables": [{"name": "gdp", "type": "numeric"}],
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False},
            "entity": {"kind": "country", "tracking": True}
        }
    }
    
    result = transformer.transform(raw_data, ds_spec)
    
    assert len(result) == 3
    # Should have entity_id
    assert any("entity_id" in r for r in result)
