"""Tests for Template Decision Engine."""
import pytest
from axdata.engine.template_decider import decide_template
from axdata.spec.ds_spec import DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension, EntityDimension, VariableSpec


def test_tabular_template():
    """Test tabular template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False},
            "entity": {"kind": "none", "tracking": False}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "tabular"


def test_time_series_template():
    """Test time series template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": True, "granularity": "year"},
            "geo": {"enabled": False},
            "entity": {"kind": "country", "tracking": False}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "time_series"


def test_panel_template():
    """Test panel/longitudinal template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": True, "granularity": "year"},
            "geo": {"enabled": False},
            "entity": {"kind": "person", "tracking": True}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "panel"


def test_geospatial_template():
    """Test geospatial template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": True, "level": "point"},
            "entity": {"kind": "none"}
        },
        "variables": [{"name": "value", "type": "geo"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "geospatial"


def test_text_template():
    """Test text/document template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False},
            "entity": {"kind": "document"}
        },
        "variables": [{"name": "text", "type": "text"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "text"


def test_event_template():
    """Test event-based template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        },
        "variables": [{"name": "event", "type": "event"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "event"


def test_forced_template():
    """Test forced template (not auto)."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False},
            "entity": {"kind": "none"}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "hybrid"}
    }
    
    template = decide_template(ds_spec)
    assert template == "hybrid"


def test_cross_sectional_template():
    """Test cross-sectional template selection."""
    ds_spec = {
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": True, "level": "country"},
            "entity": {"kind": "country"}
        },
        "variables": [{"name": "value", "type": "numeric"}],
        "output": {"template": "auto"}
    }
    
    template = decide_template(ds_spec)
    assert template == "cross_sectional"
