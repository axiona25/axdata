"""Tests for DS-SPEC v1."""
import pytest
from axdata.spec.ds_spec import (
    DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension,
    EntityDimension, VariableSpec, OutputSpec, TemplateType
)


def test_ds_spec_creation():
    """Test basic DS-SPEC creation."""
    ds_spec = DatasetSpec(
        request=RequestSpec(query_text="Test query", language="it"),
        sector="health",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=True, start="2020", end="2024", granularity="year"),
            geo=GeoDimension(enabled=True, scope="EU", level="country"),
            entity=EntityDimension(kind="country", tracking=False)
        ),
        variables=[VariableSpec(name="incidence", type="numeric", unit="per_100k")]
    )
    
    assert ds_spec.version == "1.0"
    assert ds_spec.sector == "health"
    assert ds_spec.dimensions.time.enabled is True
    assert ds_spec.dimensions.geo.enabled is True


def test_ds_spec_validation():
    """Test DS-SPEC validation."""
    # Valid spec
    spec = DatasetSpec(
        request=RequestSpec(query_text="Valid query", language="it"),
        sector="economy",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=False),
            geo=GeoDimension(enabled=False),
            entity=EntityDimension(kind="none")
        ),
        variables=[VariableSpec(name="value", type="numeric")]
    )
    assert spec.version == "1.0"
    
    # Invalid: missing variables
    with pytest.raises(Exception):
        DatasetSpec(
            request=RequestSpec(query_text="Test", language="it"),
            sector="test",
            dimensions=DimensionsSpec(
                time=TimeDimension(enabled=False),
                geo=GeoDimension(enabled=False),
                entity=EntityDimension(kind="none")
            ),
            variables=[]  # Empty - should fail
        )


def test_ds_spec_dict_conversion():
    """Test DS-SPEC to dict conversion."""
    spec = DatasetSpec(
        request=RequestSpec(query_text="Test", language="it"),
        sector="health",
        dimensions=DimensionsSpec(
            time=TimeDimension(enabled=True, granularity="year"),
            geo=GeoDimension(enabled=False),
            entity=EntityDimension(kind="country")
        ),
        variables=[VariableSpec(name="value", type="numeric")]
    )
    
    spec_dict = spec.model_dump()
    assert spec_dict["version"] == "1.0"
    assert spec_dict["sector"] == "health"
    assert spec_dict["dimensions"]["time"]["enabled"] is True
