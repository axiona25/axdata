"""Tests for AXDATA packaging components."""
import pytest
import json
from pathlib import Path
import tempfile
import shutil

from axdata.packaging.metadata_builder import build_metadata, stable_id_from_spec
from axdata.packaging.schema_generator import build_schema_from_spec
from axdata.packaging.compliance_builder import build_compliance
from axdata.packaging.readme_builder import build_readme
from axdata.packaging.packager import package_dataset
from axdata.spec.ds_spec import DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension, EntityDimension, VariableSpec


@pytest.fixture
def sample_ds_spec():
    """Sample DS-SPEC for testing."""
    return DatasetSpec(
        version="1.0",
        request=RequestSpec(query_text="Test dataset query", language="it"),
        sector="health",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=True, start="2020", end="2024", granularity="year"),
            geo=GeoDimension(enabled=True, scope="EU", level="country"),
            entity=EntityDimension(kind="country", tracking=False)
        ),
        variables=[VariableSpec(name="incidence", type="numeric", unit="per_100k")]
    )


@pytest.fixture
def sample_sources():
    """Sample source manifests for testing."""
    return [
        {
            "source_id": "eurostat",
            "name": "Eurostat",
            "license": {
                "name": "Eurostat License",
                "url": "https://ec.europa.eu/eurostat",
                "commercial_use": True,
                "attribution_required": True
            },
            "authority": {"level": 5, "publisher": "European Commission"}
        }
    ]


def test_metadata_builder(sample_ds_spec, sample_sources):
    """Test metadata builder."""
    metadata = build_metadata(
        ds_spec=sample_ds_spec,
        template="time_series",
        sources_used=sample_sources,
        record_count=100
    )
    
    assert metadata["axdata"]["dataset_id"] is not None
    assert metadata["axdata"]["template"] == "time_series"
    assert metadata["axdata"]["record_count"] == 100
    assert metadata["dcat"]["title"] is not None
    assert metadata["dcat"]["description"] == "Test dataset query"
    assert len(metadata["sources"]) == 1
    assert "fair" in metadata


def test_stable_id_generation(sample_ds_spec):
    """Test stable ID generation."""
    id1 = stable_id_from_spec(sample_ds_spec)
    id2 = stable_id_from_spec(sample_ds_spec)
    
    # Should be deterministic
    assert id1 == id2
    assert len(id1) == 24  # SHA256 hex first 24 chars


def test_schema_generator(sample_ds_spec):
    """Test schema generator."""
    schema = build_schema_from_spec(sample_ds_spec, "time_series")
    
    assert schema["schema_version"] == "1.0"
    assert schema["template"] == "time_series"
    assert "columns" in schema
    assert len(schema["columns"]) > 0
    
    # Should have timestamp column for time series
    column_names = [c["name"] for c in schema["columns"]]
    assert "timestamp" in column_names
    assert "entity_id" in column_names


def test_compliance_builder(sample_ds_spec, sample_sources):
    """Test compliance builder."""
    compliance = build_compliance(
        ds_spec=sample_ds_spec,
        sources_used=sample_sources,
        pii_detected=False,
        records=None
    )
    
    assert compliance["license_policy"] == "normal"
    assert compliance["pii"]["pii_detected"] is False
    assert compliance["pii"]["action"] == "allowed"
    assert len(compliance["licenses"]) > 0
    # New fields from ChatGPT spec
    assert "usage_rights" in compliance
    assert "jurisdiction" in compliance
    assert compliance["usage_rights"]["commercial_use"] in ["Allowed", "Restricted"]
    assert "jurisdictions" in compliance["jurisdiction"]


def test_compliance_pii_blocked(sample_ds_spec, sample_sources):
    """Test compliance with PII detected and not allowed."""
    compliance = build_compliance(
        ds_spec=sample_ds_spec,
        sources_used=sample_sources,
        pii_detected=True,
        records=None
    )
    
    assert compliance["pii"]["pii_detected"] is True
    assert compliance["pii"]["action"] == "blocked"  # allow_pii is False by default


def test_readme_builder(sample_ds_spec, sample_sources):
    """Test README builder."""
    readme = build_readme(sample_ds_spec, "time_series", sample_sources)
    
    assert "Test dataset query" in readme
    assert "health" in readme
    assert "time_series" in readme
    assert "Eurostat" in readme
    assert "Methodology" in readme
    assert "Limitations" in readme


def test_packager(sample_ds_spec, sample_sources):
    """Test complete packager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_bytes = b"col1,col2\nval1,val2\n"
        
        result = package_dataset(
            out_dir=tmpdir,
            ds_spec=sample_ds_spec,
            template="time_series",
            sources_used=sample_sources,
            dataset_bytes=dataset_bytes,
            dataset_filename="dataset.csv",
            record_count=1
        )
        
        assert "package_dir" in result
        assert "zip_path" in result
        
        # Check package structure
        package_dir = Path(result["package_dir"])
        assert (package_dir / "data" / "dataset.csv").exists()
        assert (package_dir / "schema.json").exists()
        assert (package_dir / "metadata.json").exists()
        assert (package_dir / "provenance.json").exists()
        assert (package_dir / "compliance.json").exists()
        assert (package_dir / "README.md").exists()
        
        # Check ZIP exists
        zip_path = Path(result["zip_path"])
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"


def test_packager_with_provenance(sample_ds_spec, sample_sources):
    """Test packager with custom provenance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        provenance = {
            "generated_at": "2024-01-01T00:00:00Z",
            "template": "time_series",
            "sources_used": [{"source_id": "eurostat"}]
        }
        
        result = package_dataset(
            out_dir=tmpdir,
            ds_spec=sample_ds_spec,
            template="time_series",
            sources_used=sample_sources,
            dataset_bytes=b"test",
            provenance=provenance
        )
        
        # Check provenance was saved
        provenance_path = Path(result["package_dir"]) / "provenance.json"
        assert provenance_path.exists()
        
        with open(provenance_path) as f:
            saved_provenance = json.load(f)
        assert saved_provenance["template"] == "time_series"
