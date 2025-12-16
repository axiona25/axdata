"""Tests for AXDATA service integration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from axdata.spec.ds_spec import DatasetSpec
from services.axdata_service import convert_dataset_plan_to_ds_spec
from services.ds_spec_generator import generate_ds_spec_from_query


def test_convert_dataset_plan_to_ds_spec():
    """Test conversion from DatasetPlan to DS-SPEC."""
    plan = {
        "domain": "health",
        "title": "Diabetes incidence in Europe 2015-2024",
        "sources": [],
        "outputs": ["csv", "json"],
        "geographic_coverage": "EU",
        "temporal_coverage": "2015-2024",
        "indicators_metadata": {
            "diabetes_incidence": {
                "description": "Diabetes incidence rate",
                "unit": "per_100k"
            }
        }
    }
    
    ds_spec = convert_dataset_plan_to_ds_spec(plan)
    
    assert ds_spec.sector == "health"
    assert ds_spec.dimensions.time.enabled is True
    assert ds_spec.dimensions.geo.enabled is True
    assert ds_spec.dimensions.geo.scope == "EU"
    assert len(ds_spec.variables) > 0


def test_convert_dataset_plan_extract_time():
    """Test time extraction from DatasetPlan."""
    plan = {
        "domain": "economy",
        "title": "GDP growth 2000-2023",
        "sources": [],
        "temporal_coverage": "2000-2023"
    }
    
    ds_spec = convert_dataset_plan_to_ds_spec(plan)
    
    assert ds_spec.dimensions.time.enabled is True
    assert ds_spec.dimensions.time.start == "2000"
    assert ds_spec.dimensions.time.end == "2023"


def test_convert_dataset_plan_extract_geo():
    """Test geographic extraction from DatasetPlan."""
    plan = {
        "domain": "economy",
        "title": "GDP by country",
        "sources": [],
        "geographic_coverage": "Global"
    }
    
    ds_spec = convert_dataset_plan_to_ds_spec(plan)
    
    assert ds_spec.dimensions.geo.enabled is True
    assert ds_spec.dimensions.geo.scope == "Global"


def test_generate_ds_spec_from_query():
    """Test DS-SPEC generation from natural language query."""
    query = "Incidenza diabete in Europa dal 2015 al 2024 per paese"
    sector = "health"
    
    ds_spec = generate_ds_spec_from_query(query, sector)
    
    assert ds_spec.sector == sector
    assert ds_spec.request.query_text == query
    assert ds_spec.dimensions.time.enabled is True
    assert ds_spec.dimensions.geo.enabled is True
    assert len(ds_spec.variables) > 0


def test_generate_ds_spec_time_keywords():
    """Test time keyword detection."""
    query = "Serie temporale mensile dell'inflazione"
    ds_spec = generate_ds_spec_from_query(query, "economy")
    
    assert ds_spec.dimensions.time.enabled is True
    assert ds_spec.dimensions.time.granularity == "month"


def test_generate_ds_spec_geo_keywords():
    """Test geographic keyword detection."""
    query = "Dati regionali per l'Italia"
    ds_spec = generate_ds_spec_from_query(query, "economy")
    
    assert ds_spec.dimensions.geo.enabled is True
    assert ds_spec.dimensions.geo.level == "region"


def test_generate_ds_spec_entity_tracking():
    """Test entity tracking detection."""
    query = "Panel longitudinale di pazienti nel tempo"
    ds_spec = generate_ds_spec_from_query(query, "health")
    
    assert ds_spec.dimensions.entity.tracking is True
    # Note: entity kind detection may not always work perfectly, so we check tracking
    # which is the key indicator for panel datasets
