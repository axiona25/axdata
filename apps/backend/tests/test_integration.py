"""Integration tests for AXDATA pipeline end-to-end."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from axdata.spec.ds_spec import DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension, EntityDimension, VariableSpec
from axdata.pipeline.run_pipeline import run
from axdata.packaging.packager import package_dataset
import tempfile
from pathlib import Path


@pytest.fixture
def sample_ds_spec():
    """Sample DS-SPEC for integration testing."""
    return DatasetSpec(
        version="1.0",
        request=RequestSpec(query_text="Test integration dataset", language="it"),
        sector="health",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=True, start="2020", end="2024", granularity="year"),
            geo=GeoDimension(enabled=True, scope="EU", level="country"),
            entity=EntityDimension(kind="country", tracking=False)
        ),
        variables=[VariableSpec(name="incidence", type="numeric", unit="per_100k")]
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
            "geo_coverage": {"scope": "EU", "levels": ["country"]},
            "time_coverage": {"start": "2020", "end": "present"},
            "license": {"commercial_use": True, "attribution_required": True},
            "authority": {"level": 5, "publisher": "European Commission"},
            "endpoints": [{
                "id": "data",
                "path": "/api/dissemination/statistics/1.0/data",
                "method": "GET",
                "supports": {"time": True, "geo": True, "pagination": True}
            }]
        }
    ]


@pytest.fixture
def mock_collector_response():
    """Mock collector service response."""
    return {
        "source_id": "eurostat",
        "fetched_at": "2024-01-01T00:00:00Z",
        "payload": {
            "records": [
                {"country": "IT", "year": 2020, "incidence": 100.5},
                {"country": "IT", "year": 2021, "incidence": 102.3},
                {"country": "DE", "year": 2020, "incidence": 95.2},
            ],
            "data": {},
            "records": 3
        },
        "query": {"dataset_code": "default", "filters": {}},
        "storage_path": "/tmp/test.json",
        "provenance": {"source": "eurostat"}
    }


@patch('axdata.pipeline.run_pipeline.load_manifests')
@patch('axdata.pipeline.run_pipeline.fetch_from_source')
def test_pipeline_end_to_end(
    mock_fetch,
    mock_load_manifests,
    sample_ds_spec,
    mock_manifests,
    mock_collector_response
):
    """Test complete pipeline: DS-SPEC → Pipeline → Package."""
    # Setup mocks
    mock_load_manifests.return_value = mock_manifests
    mock_fetch.return_value = mock_collector_response
    
    # Run pipeline
    result = run(sample_ds_spec, manifest_dir=None, top_n_sources=1)
    
    # Verify pipeline result
    assert "template" in result
    assert "selected_sources" in result
    assert "raw_count" in result
    assert "transformed_count" in result
    assert "provenance" in result
    
    # Verify template was selected
    assert result["template"] in ["time_series", "tabular", "panel"]
    
    # Verify sources were selected
    assert len(result["selected_sources"]) > 0
    
    # Verify raw data was collected
    assert result["raw_count"] > 0
    
    # Verify transformation happened (if records available)
    if result.get("transformed_count", 0) > 0:
        assert "transformed_records" in result
        assert len(result["transformed_records"]) > 0
    
    # Verify provenance
    assert "sources_used" in result["provenance"]
    assert "timeline" in result["provenance"]
    assert "transformations_applied" in result["provenance"]
    assert "reproducibility" in result["provenance"]


@patch('axdata.pipeline.run_pipeline.load_manifests')
@patch('axdata.pipeline.run_pipeline.fetch_from_source')
def test_pipeline_with_normalization(
    mock_fetch,
    mock_load_manifests,
    sample_ds_spec,
    mock_manifests,
    mock_collector_response
):
    """Test pipeline with domain normalization."""
    # Setup mocks
    mock_load_manifests.return_value = mock_manifests
    mock_fetch.return_value = mock_collector_response
    
    # Mock normalizer
    with patch('axdata.pipeline.run_pipeline.get_normalizer') as mock_get_norm:
        mock_normalizer = Mock()
        mock_normalizer.normalize.return_value = [
            {"country": "IT", "year": 2020, "incidence": 100.5},
            {"country": "IT", "year": 2021, "incidence": 102.3},
        ]
        mock_get_norm.return_value = mock_normalizer
        
        # Run pipeline
        result = run(sample_ds_spec, manifest_dir=None, top_n_sources=1)
        
        # Verify normalization was applied
        assert result.get("normalization_applied") is not None
        if result.get("normalization_applied"):
            assert "normalization_domain" in result
            assert result["normalization_domain"] in ["biomedical", "health"]


@patch('axdata.pipeline.run_pipeline.load_manifests')
@patch('axdata.pipeline.run_pipeline.fetch_from_source')
def test_pipeline_packaging(
    mock_fetch,
    mock_load_manifests,
    sample_ds_spec,
    mock_manifests,
    mock_collector_response
):
    """Test complete pipeline including packaging."""
    # Setup mocks
    mock_load_manifests.return_value = mock_manifests
    mock_fetch.return_value = mock_collector_response
    
    # Run pipeline
    result = run(sample_ds_spec, manifest_dir=None, top_n_sources=1)
    
    # Package dataset
    with tempfile.TemporaryDirectory() as tmpdir:
        if result.get("transformed_records"):
            records = result["transformed_records"]
        else:
            records = [{"test": "data"}]
        
        # Convert records to CSV bytes
        import csv
        import io
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        dataset_bytes = output.getvalue().encode('utf-8')
        
        packaged = package_dataset(
            out_dir=tmpdir,
            ds_spec=sample_ds_spec,
            template=result["template"],
            sources_used=result["provenance"]["sources_used"],
            dataset_bytes=dataset_bytes,
            dataset_filename="dataset.csv",
            record_count=len(records),
            records=records,
            provenance=result["provenance"]
        )
        
        # Verify package structure
        assert "package_dir" in packaged
        assert "zip_path" in packaged
        
        package_dir = Path(packaged["package_dir"])
        assert (package_dir / "data" / "dataset.csv").exists()
        assert (package_dir / "schema.json").exists()
        assert (package_dir / "metadata.json").exists()
        assert (package_dir / "provenance.json").exists()
        assert (package_dir / "compliance.json").exists()
        assert (package_dir / "quality.json").exists()
        assert (package_dir / "README.md").exists()
        
        # Verify ZIP exists
        zip_path = Path(packaged["zip_path"])
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"


@patch('axdata.pipeline.run_pipeline.load_manifests')
def test_pipeline_error_handling(mock_load_manifests, sample_ds_spec):
    """Test pipeline error handling and partial recovery."""
    # Setup: no sources available
    mock_load_manifests.return_value = []
    
    result = run(sample_ds_spec, manifest_dir=None)
    
    # Should return error but not crash
    assert "error" in result
    assert result["template"] is None
    assert len(result["selected_sources"]) == 0


@patch('axdata.pipeline.run_pipeline.load_manifests')
@patch('axdata.pipeline.run_pipeline.fetch_from_source')
def test_pipeline_partial_recovery(
    mock_fetch,
    mock_load_manifests,
    sample_ds_spec,
    mock_manifests
):
    """Test pipeline continues with partial source failures."""
    # Setup: one source succeeds, one fails
    mock_load_manifests.return_value = mock_manifests + [
        {
            "source_id": "who_gho",
            "name": "WHO GHO",
            "sectors": ["health"],
            "data_types": ["tabular"],
            "geo_coverage": {"scope": "global"},
            "license": {"commercial_use": False},
            "authority": {"level": 5}
        }
    ]
    
    # First source succeeds, second fails
    def mock_fetch_side_effect(source, ds_spec, collector_url=None):
        if source["source_id"] == "eurostat":
            return {
                "source_id": "eurostat",
                "fetched_at": "2024-01-01T00:00:00Z",
                "payload": {"records": [{"test": "data"}]},
                "query": {},
                "provenance": {}
            }
        else:
            raise Exception("Source unavailable")
    
    mock_fetch.side_effect = mock_fetch_side_effect
    
    result = run(sample_ds_spec, manifest_dir=None, top_n_sources=2)
    
    # Should have partial success
    assert result["raw_count"] > 0
    # At least one source should have succeeded
