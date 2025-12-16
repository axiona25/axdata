"""AXDATA service - integrates AXDATA pipeline with backend."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging
import httpx
from pathlib import Path

from axdata.spec.ds_spec import DatasetSpec
from axdata.pipeline.run_pipeline import run as run_pipeline
from axdata.packaging.packager import package_dataset
from axdata.sources.loader import get_manifest_path
from core.config import settings

logger = logging.getLogger(__name__)


def convert_dataset_plan_to_ds_spec(plan: Dict[str, Any]) -> DatasetSpec:
    """
    Convert DatasetPlan to DS-SPEC with intelligent extraction of dimensions.
    
    Extracts:
    - Time dimension from temporal_coverage and source queries
    - Geo dimension from geographic_coverage and source queries
    - Variables from indicators_metadata and source queries
    - Entity tracking from transformations
    
    Args:
        plan: DatasetPlan dictionary
    
    Returns:
        DatasetSpec
    """
    # Extract basic info
    domain = plan.get("domain", "unknown")
    title = plan.get("title", "")
    
    # Parse temporal coverage
    temporal_coverage = plan.get("temporal_coverage", "")
    time_enabled = bool(temporal_coverage)
    time_start = None
    time_end = None
    time_granularity = "year"
    
    if temporal_coverage:
        # Try to extract years from strings like "2000-2023" or "2000 to 2024"
        import re
        years = re.findall(r'\d{4}', temporal_coverage)
        if len(years) >= 2:
            time_start = years[0]
            time_end = years[-1]
        elif len(years) == 1:
            time_start = years[0]
        
        # Detect granularity from keywords
        temporal_lower = temporal_coverage.lower()
        if any(x in temporal_lower for x in ["daily", "day", "giornaliero"]):
            time_granularity = "day"
        elif any(x in temporal_lower for x in ["weekly", "week", "settimanale"]):
            time_granularity = "week"
        elif any(x in temporal_lower for x in ["monthly", "month", "mensile"]):
            time_granularity = "month"
        elif any(x in temporal_lower for x in ["quarterly", "quarter", "trimestrale"]):
            time_granularity = "quarter"
        elif any(x in temporal_lower for x in ["annual", "year", "annuale", "anno"]):
            time_granularity = "year"
    
    # Also check source queries for time filters
    sources = plan.get("sources", [])
    for source in sources:
        queries = source.get("queries", [])
        for query in queries:
            # Check for time filters in query
            if isinstance(query, dict):
                if "time" in query or "startTime" in query or "start_time" in query:
                    time_enabled = True
                if "time" in query and isinstance(query["time"], list):
                    if not time_start and len(query["time"]) > 0:
                        time_start = str(query["time"][0])
                    if not time_end and len(query["time"]) > 0:
                        time_end = str(query["time"][-1])
    
    # Parse geographic coverage
    geographic_coverage = plan.get("geographic_coverage", "")
    geo_enabled = bool(geographic_coverage)
    geo_scope = None
    geo_level = "country"
    
    if geographic_coverage:
        geo_scope = geographic_coverage
        # Detect level from keywords
        geo_lower = geographic_coverage.lower()
        if any(x in geo_lower for x in ["global", "world", "mondiale"]):
            geo_level = "global"
        elif any(x in geo_lower for x in ["region", "regione", "regional"]):
            geo_level = "region"
        elif any(x in geo_lower for x in ["province", "provincia", "provincial"]):
            geo_level = "province"
        elif any(x in geo_lower for x in ["city", "città", "urban"]):
            geo_level = "city"
        elif any(x in geo_lower for x in ["point", "coordinate"]):
            geo_level = "point"
        elif any(x in geo_lower for x in ["polygon", "area"]):
            geo_level = "polygon"
    
    # Check source queries for geo filters
    for source in sources:
        queries = source.get("queries", [])
        for query in queries:
            if isinstance(query, dict):
                if "geo" in query or "country" in query or "geography" in query:
                    geo_enabled = True
                    if "geo" in query:
                        geo_scope = geo_scope or str(query["geo"])
    
    # Extract variables from indicators_metadata
    variables = []
    indicators_metadata = plan.get("indicators_metadata", {})
    if indicators_metadata:
        for var_name, var_meta in indicators_metadata.items():
            variables.append({
                "name": var_name,
                "type": "numeric",  # Default, could be enhanced
                "unit": var_meta.get("unit"),
                "preferred_sources": []
            })
    
    # If no variables from metadata, create default
    if not variables:
        variables = [{
            "name": "value",
            "type": "numeric",
            "unit": None,
            "preferred_sources": []
        }]
    
    # Detect entity tracking from transformations
    entity_tracking = False
    transformations = plan.get("transformations", [])
    for trans in transformations:
        if isinstance(trans, dict):
            trans_type = trans.get("type", "")
            if "panel" in trans_type.lower() or "longitudinal" in trans_type.lower():
                entity_tracking = True
    
    # Determine entity kind from domain and queries
    entity_kind = "none"
    if domain in ["biomedical", "health"]:
        # Check if queries mention studies, trials, patients
        for source in sources:
            queries = source.get("queries", [])
            for query in queries:
                if isinstance(query, dict):
                    query_str = str(query).lower()
                    if "study" in query_str or "trial" in query_str:
                        entity_kind = "study"
                    elif "patient" in query_str or "person" in query_str:
                        entity_kind = "person"
    
    # Map domain to sector
    sector_map = {
        "economics": "economy",
        "biomedical": "health",
        "physics": "physics",
        "math": "math",
        "demography": "society"
    }
    sector = sector_map.get(domain, domain)
    
    # Map outputs to formats
    outputs = plan.get("outputs", ["csv"])
    formats = []
    for out in outputs:
        if out in ["csv", "parquet", "json", "geojson"]:
            formats.append(out)
    if not formats:
        formats = ["csv"]
    
    ds_spec_dict = {
        "version": "1.0",
        "request": {
            "query_text": title,
            "language": "it",
            "user_role": "general"
        },
        "sector": sector,
        "subsector": None,
        "dimensions": {
            "time": {
                "enabled": time_enabled,
                "start": time_start,
                "end": time_end,
                "granularity": time_granularity
            },
            "geo": {
                "enabled": geo_enabled,
                "scope": geo_scope,
                "level": geo_level,
                "crs": "EPSG:4326"
            },
            "entity": {
                "kind": entity_kind,
                "tracking": entity_tracking,
                "id_strategy": "mapped"
            }
        },
        "variables": variables,
        "output": {
            "template": "auto",
            "formats": formats,
            "quality": {
                "min_completeness": 0.85,
                "deduplicate": True
            },
            "compliance": {
                "allow_pii": False,
                "license_policy": "normal"
            }
        }
    }
    
    return DatasetSpec(**ds_spec_dict)


def fetch_from_collector_service(
    connector_name: str,
    query: Dict[str, Any],
    collector_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch data from collector service (replaces stub in pipeline).
    
    Args:
        connector_name: Connector name
        query: Query parameters
        collector_url: Collector service URL (default: from settings)
    
    Returns:
        Raw data with provenance
    """
    if collector_url is None:
        collector_url = getattr(settings, 'collector_url', 'http://localhost:8001')
    
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{collector_url}/collect",
                json={
                    "connector_name": connector_name,
                    "query": query,
                    "dataset_step_id": None  # Not needed for direct calls
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "source_id": connector_name,
                "fetched_at": result.get("provenance", {}).get("retrieved_at", ""),
                "payload": {
                    "records": result.get("metadata", {}).get("row_count", 0),
                    "data": result.get("metadata", {})
                },
                "query": query,
                "storage_path": result.get("storage_path"),
                "provenance": result.get("provenance", {})
            }
    except Exception as e:
        logger.error(f"Error fetching from collector service: {e}")
        raise


def create_dataset_with_axdata_pipeline(
    ds_spec: DatasetSpec | Dict[str, Any],
    manifest_dir: Optional[str | Path] = None,
    top_n_sources: int = 3,
    collector_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create dataset using AXDATA pipeline.
    
    This now includes:
    - Template selection
    - Source selection
    - Data collection (via collector service)
    - Template transformation
    - Cross-validation
    
    Args:
        ds_spec: Dataset specification
        manifest_dir: Directory with source manifests
        top_n_sources: Number of top sources to use
        collector_url: Collector service URL
    
    Returns:
        Pipeline result with transformed data
    """
    """
    Create dataset using AXDATA pipeline.
    
    Args:
        ds_spec: Dataset specification
        manifest_dir: Directory with source manifests
        top_n_sources: Number of top sources to use
        collector_url: Collector service URL
    
    Returns:
        Pipeline result with packaged dataset info
    """
    # Run pipeline
    pipeline_result = run_pipeline(
        ds_spec=ds_spec,
        manifest_dir=manifest_dir,
        top_n_sources=top_n_sources
    )
    
    if "error" in pipeline_result:
        return pipeline_result
    
    # Replace stub fetch_from_source with real collector calls
    # This integrates with the existing collector service
    raw_data = []
    for source_id in pipeline_result["selected_sources"]:
        # Find source manifest
        if manifest_dir is None:
            manifest_dir = get_manifest_path()
        from axdata.sources.loader import load_manifests
        manifests = load_manifests(manifest_dir)
        source_manifest = next((s for s in manifests if s["source_id"] == source_id), None)
        
        if source_manifest:
            # Build query from DS-SPEC (simplified - you may want to enhance this)
            spec_dict = ds_spec.dict() if isinstance(ds_spec, DatasetSpec) else ds_spec
            query = {
                "dataset_code": "default",  # Should be extracted from DS-SPEC
                "filters": {}
            }
            
    # Pipeline now handles collection and transformation internally
    # No additional processing needed here
    
    return pipeline_result


def package_dataset_from_pipeline(
    pipeline_result: Dict[str, Any],
    ds_spec: DatasetSpec | Dict[str, Any],
    out_dir: str | Path,
    dataset_bytes: Optional[bytes] = None,
    dataset_filename: str = "dataset.csv"
) -> Dict[str, str]:
    """
    Package dataset from pipeline result.
    
    Args:
        pipeline_result: Pipeline result (with transformed_records)
        ds_spec: Dataset specification
        out_dir: Output directory
        dataset_bytes: Dataset file bytes (if None, will generate from transformed_records)
        dataset_filename: Dataset filename
    
    Returns:
        Package info with paths
    """
    from axdata.packaging.packager import package_dataset
    from services.export_service import export_to_csv
    
    sources_used = []
    for source_id in pipeline_result.get("selected_sources", []):
        # Load manifest to get full source info
        manifest_dir = get_manifest_path()
        from axdata.sources.loader import load_manifests
        manifests = load_manifests(manifest_dir)
        source_manifest = next((s for s in manifests if s["source_id"] == source_id), None)
        if source_manifest:
            sources_used.append(source_manifest)
    
    # Get transformed records
    transformed_records = pipeline_result.get("transformed_records", [])
    
    # Generate dataset bytes if not provided
    if dataset_bytes is None and transformed_records:
        dataset_bytes = export_to_csv(transformed_records)
    
    packaged = package_dataset(
        out_dir=out_dir,
        ds_spec=ds_spec,
        template=pipeline_result.get("template", "tabular"),
        sources_used=sources_used,
        dataset_bytes=dataset_bytes,
        dataset_filename=dataset_filename,
        record_count=pipeline_result.get("transformed_count", len(transformed_records)),
        records=transformed_records,  # Pass records for quality calculation
        cross_validation_result=pipeline_result.get("cross_validation"),
        provenance=pipeline_result.get("provenance")
    )
    
    return packaged
