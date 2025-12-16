"""Tests for Source Selection Engine."""
import pytest
from axdata.engine.source_selection import select_sources, score_source


@pytest.fixture
def sample_manifests():
    """Sample source manifests for testing."""
    return [
        {
            "source_id": "eurostat",
            "name": "Eurostat",
            "sectors": ["economy", "health"],
            "data_types": ["tabular", "time_series"],
            "geo_coverage": {"scope": "EU", "levels": ["country"]},
            "license": {"commercial_use": True},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.98}
        },
        {
            "source_id": "worldbank",
            "name": "World Bank",
            "sectors": ["economy"],
            "data_types": ["tabular", "time_series", "panel"],
            "geo_coverage": {"scope": "global", "levels": ["country"]},
            "license": {"commercial_use": True},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.99}
        },
        {
            "source_id": "who_gho",
            "name": "WHO GHO",
            "sectors": ["health"],
            "data_types": ["tabular", "time_series"],
            "geo_coverage": {"scope": "global", "levels": ["country"]},
            "license": {"commercial_use": False},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.97}
        },
        {
            "source_id": "istat",
            "name": "ISTAT",
            "sectors": ["economy", "society"],
            "data_types": ["tabular"],
            "geo_coverage": {"scope": "IT", "levels": ["country"]},
            "license": {"commercial_use": True},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.97}
        }
    ]


def test_source_selection_by_sector(sample_manifests):
    """Test source selection by sector."""
    ds_spec = {
        "sector": "economy",
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False}
        },
        "output": {"compliance": {"license_policy": "normal"}}
    }
    
    selected = select_sources(ds_spec, "time_series", sample_manifests, top_n=2)
    
    assert len(selected) <= 2
    assert all("economy" in s.get("sectors", []) for s in selected)
    assert "eurostat" in [s["source_id"] for s in selected] or "worldbank" in [s["source_id"] for s in selected]


def test_source_selection_by_geo(sample_manifests):
    """Test source selection by geographic coverage."""
    ds_spec = {
        "sector": "economy",
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": True, "scope": "EU"}
        },
        "output": {"compliance": {"license_policy": "normal"}}
    }
    
    selected = select_sources(ds_spec, "tabular", sample_manifests, top_n=3)
    
    # Should prefer EU sources
    source_ids = [s["source_id"] for s in selected]
    assert "eurostat" in source_ids or "worldbank" in source_ids  # worldbank is global, so OK


def test_source_selection_license_strict(sample_manifests):
    """Test source selection with strict license policy."""
    ds_spec = {
        "sector": "health",
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False}
        },
        "output": {"compliance": {"license_policy": "strict"}}
    }
    
    selected = select_sources(ds_spec, "tabular", sample_manifests, top_n=5)
    
    # Should exclude WHO (commercial_use: False)
    source_ids = [s["source_id"] for s in selected]
    assert "who_gho" not in source_ids or all(s["license"]["commercial_use"] for s in selected)


def test_source_selection_ranking(sample_manifests):
    """Test source ranking by authority and reliability."""
    ds_spec = {
        "sector": "economy",
        "dimensions": {
            "time": {"enabled": True},
            "geo": {"enabled": False}
        },
        "output": {"compliance": {"license_policy": "normal"}}
    }
    
    selected = select_sources(ds_spec, "time_series", sample_manifests, top_n=2)
    
    # Should be ranked by authority + reliability
    if len(selected) >= 2:
        # World Bank should rank higher than ISTAT (both level 5, but WB has higher uptime)
        scores = [score_source(ds_spec, s) for s in selected]
        assert scores == sorted(scores, reverse=True)  # Should be descending


def test_source_selection_no_matches(sample_manifests):
    """Test source selection when no sources match."""
    ds_spec = {
        "sector": "physics",  # No sources have this sector
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False}
        },
        "output": {"compliance": {"license_policy": "normal"}}
    }
    
    selected = select_sources(ds_spec, "tabular", sample_manifests, top_n=3)
    assert len(selected) == 0


def test_source_selection_data_type_filter(sample_manifests):
    """Test source selection filters by data type."""
    ds_spec = {
        "sector": "economy",
        "dimensions": {
            "time": {"enabled": False},
            "geo": {"enabled": False}
        },
        "output": {"compliance": {"license_policy": "normal"}}
    }
    
    # Request panel template - only worldbank supports it
    selected = select_sources(ds_spec, "panel", sample_manifests, top_n=5)
    
    if len(selected) > 0:
        assert all("panel" in s["data_types"] for s in selected)
