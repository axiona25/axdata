"""Tests for AXDATA pipeline."""
import pytest
from unittest.mock import Mock, patch
from axdata.pipeline.run_pipeline import run, build_provenance
from axdata.spec.ds_spec import DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension, EntityDimension, VariableSpec
from axdata.sources.loader import load_manifests, get_manifest_path


@pytest.fixture
def sample_ds_spec():
    """Sample DS-SPEC for testing."""
    return DatasetSpec(
        version="1.0",
        request=RequestSpec(query_text="Test query", language="it"),
        sector="health",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=True, start="2020", end="2024"),
            geo=GeoDimension(enabled=True, scope="EU"),
            entity=EntityDimension(kind="country")
        ),
        variables=[VariableSpec(name="value", type="numeric")]
    )


@pytest.fixture
def mock_manifests():
    """Mock source manifests."""
    return [
        {
            "source_id": "eurostat",
            "name": "Eurostat",
            "sectors": ["health", "economy"],
            "data_types": ["tabular", "time_series"],
            "geo_coverage": {"scope": "EU"},
            "license": {"commercial_use": True},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.98}
        },
        {
            "source_id": "who_gho",
            "name": "WHO GHO",
            "sectors": ["health"],
            "data_types": ["tabular", "time_series"],
            "geo_coverage": {"scope": "global"},
            "license": {"commercial_use": False},
            "authority": {"level": 5},
            "reliability": {"uptime_score": 0.97}
        }
    ]


@patch('axdata.pipeline.run_pipeline.load_manifests')
@patch('axdata.pipeline.run_pipeline.fetch_from_source')
def test_pipeline_run(mock_fetch, mock_load_manifests, sample_ds_spec, mock_manifests):
    """Test pipeline execution."""
    mock_load_manifests.return_value = mock_manifests
    mock_fetch.return_value = {
        "source_id": "eurostat",
        "fetched_at": "2024-01-01T00:00:00Z",
        "payload": {"example": True}
    }
    
    result = run(sample_ds_spec, manifest_dir=None, top_n_sources=2)
    
    assert "template" in result
    assert "selected_sources" in result
    assert "raw_count" in result
    assert "provenance" in result
    assert result["template"] in ["time_series", "panel", "tabular"]
    assert len(result["selected_sources"]) > 0


@patch('axdata.pipeline.run_pipeline.load_manifests')
def test_pipeline_no_sources(mock_load_manifests, sample_ds_spec):
    """Test pipeline with no available sources."""
    mock_load_manifests.return_value = []
    
    result = run(sample_ds_spec, manifest_dir=None)
    
    assert "error" in result
    assert result["template"] is None
    assert len(result["selected_sources"]) == 0


@patch('axdata.pipeline.run_pipeline.load_manifests')
def test_pipeline_no_matching_sources(mock_load_manifests, sample_ds_spec):
    """Test pipeline with no matching sources."""
    # Sources that don't match (wrong sector)
    mock_manifests = [
        {
            "source_id": "nasa",
            "sectors": ["physics"],
            "data_types": ["tabular"],
            "geo_coverage": {"scope": "global"},
            "license": {"commercial_use": True},
            "authority": {"level": 5}
        }
    ]
    mock_load_manifests.return_value = mock_manifests
    
    result = run(sample_ds_spec, manifest_dir=None)
    
    assert "error" in result or len(result["selected_sources"]) == 0


def test_build_provenance(sample_ds_spec, mock_manifests):
    """Test provenance building with new ChatGPT UI fields."""
    provenance = build_provenance(
        sample_ds_spec, 
        "time_series", 
        mock_manifests,
        raw_data=None,
        transformations_applied=None,
        timeline=None
    )
    
    assert "generated_at" in provenance
    assert provenance["template"] == "time_series"
    assert len(provenance["sources_used"]) == 2
    assert provenance["sources_used"][0]["source_id"] == "eurostat"
    
    # New ChatGPT UI fields
    assert "api_endpoints" in provenance
    assert "timeline" in provenance
    assert "transformations_applied" in provenance
    assert "reproducibility" in provenance
    
    # Check reproducibility block
    assert "ds_spec_hash" in provenance["reproducibility"]
    assert "pipeline_version" in provenance["reproducibility"]
    assert "pipeline_flow" in provenance["reproducibility"]
    assert "reproduction_instructions" in provenance["reproducibility"]
    
    # Check sources_used has authority badge
    assert "authority" in provenance["sources_used"][0]
    assert "badge" in provenance["sources_used"][0]["authority"]
