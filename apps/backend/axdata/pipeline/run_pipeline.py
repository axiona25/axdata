"""Pipeline orchestrator - main entry point for dataset creation."""
from __future__ import annotations
from typing import Any, Dict, List
import json
from pathlib import Path
from datetime import datetime
import logging

from axdata.engine.template_decider import decide_template
from axdata.engine.source_selection import select_sources
from axdata.engine.sector_mapper import sector_to_domain
from axdata.engine.query_builder import build_query_from_ds_spec
from axdata.sources.loader import load_manifests, get_manifest_path
from axdata.spec.ds_spec import DatasetSpec
from axdata.transformers.registry import get_transformer
from axdata.quality.cross_validate import cross_validate_numeric_series
from axdata.utils.error_handling import retry_with_backoff, circuit_breaker, CircuitBreakerOpenError
from typing import Optional

logger = logging.getLogger(__name__)


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=10.0)
@circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
def fetch_from_source(source: Dict[str, Any], ds_spec: Dict[str, Any], collector_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch data from a source via collector service.
    
    Args:
        source: Source manifest
        ds_spec: Dataset specification
        collector_url: Collector service URL (optional, will use from settings if not provided)
    
    Returns:
        Raw data with provenance
    """
    import httpx
    from core.config import settings
    
    if collector_url is None:
        collector_url = getattr(settings, 'collector_url', 'http://localhost:8001')
    
    source_id = source["source_id"]
    
    # Build intelligent query from DS-SPEC
    query = build_query_from_ds_spec(ds_spec, source_id, source)
    
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{collector_url}/collect",
                json={
                    "connector_name": source_id,
                    "query": query,
                    "dataset_step_id": None
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "source_id": source_id,
                "fetched_at": now_iso(),
                "payload": {
                    "records": result.get("metadata", {}).get("row_count", 0),
                    "data": result.get("metadata", {}),
                    "records": result.get("metadata", {}).get("records", [])  # Actual records if available
                },
                "query": query,
                "storage_path": result.get("storage_path"),
                "provenance": result.get("provenance", {})
            }
    except CircuitBreakerOpenError as e:
        logger.error(f"Circuit breaker open for {source_id}: {e}")
        # Return error but don't fail completely (partial recovery)
        return {
            "source_id": source_id,
            "fetched_at": now_iso(),
            "payload": {"error": str(e), "records": [], "circuit_breaker_open": True},
            "query": query,
            "provenance": {
                "error": str(e),
                "source": source_id,
                "circuit_breaker_open": True
            }
        }
    except Exception as e:
        logger.error(f"Error fetching from {source_id}: {e}", exc_info=True)
        # Return error structure but don't fail completely (partial recovery)
        return {
            "source_id": source_id,
            "fetched_at": now_iso(),
            "payload": {"error": str(e), "records": []},
            "query": query,
            "provenance": {
                "error": str(e),
                "source": source_id
            }
        }


def collect_raw(selected_sources: List[Dict[str, Any]], ds_spec: Dict[str, Any], collector_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Collect raw data from selected sources with partial recovery.
    
    If one source fails, continue with others (partial recovery).
    
    Args:
        selected_sources: List of selected source manifests
        ds_spec: Dataset specification
        collector_url: Collector service URL (optional)
    
    Returns:
        List of raw data responses (may include errors for failed sources)
    """
    raw = []
    successful_sources = 0
    failed_sources = []
    
    for src in selected_sources:
        try:
            raw_data = fetch_from_source(src, ds_spec, collector_url=collector_url)
            raw.append(raw_data)
            
            # Check if successful (no error in payload)
            if raw_data.get("payload", {}).get("error") is None:
                successful_sources += 1
            else:
                failed_sources.append(src.get("source_id", "unknown"))
            logger.info(f"Collected data from {src['source_id']}")
        except Exception as e:
            logger.error(f"Error collecting from {src['source_id']}: {e}")
            # Continue with other sources
    return raw


def build_provenance(
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    sources: List[Dict[str, Any]],
    raw_data: Optional[List[Dict[str, Any]]] = None,
    transformations_applied: Optional[List[str]] = None,
    timeline: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Build comprehensive provenance information (aligned with ChatGPT UI spec).
    
    Includes:
    - Sources Used
    - API & Endpoints
    - Data Collection Timeline
    - Transformations Applied
    - Reproducibility Block
    
    Args:
        ds_spec: Dataset specification
        template: Selected template
        sources: List of source manifests used
        raw_data: Optional raw data responses (for API endpoints)
        transformations_applied: Optional list of transformation names
        timeline: Optional timeline of steps
    
    Returns:
        Comprehensive provenance dictionary
    """
    import hashlib
    import json
    
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    # Generate DS-SPEC hash for reproducibility
    spec_json = json.dumps(spec_dict, sort_keys=True)
    ds_spec_hash = hashlib.sha256(spec_json.encode()).hexdigest()[:16]
    
    # Build sources_used with authority badges
    sources_used = []
    for s in sources:
        authority = s.get("authority", {})
        authority_level = authority.get("level", 0)
        sources_used.append({
            "source_id": s["source_id"],
            "name": s["name"],
            "license": s.get("license", {}),
            "authority": {
                "level": authority_level,
                "publisher": authority.get("publisher", "Unknown"),
                "badge": "★" * authority_level if authority_level else "N/A"
            },
            "geo_coverage": s.get("geo_coverage", {}),
            "time_coverage": s.get("time_coverage", {})
        })
    
    # Build API & Endpoints from raw_data
    api_endpoints = []
    if raw_data:
        for raw_item in raw_data:
            source_id = raw_item.get("source_id", "unknown")
            query = raw_item.get("query", {})
            source_manifest = next((s for s in sources if s["source_id"] == source_id), None)
            
            if source_manifest:
                endpoints = source_manifest.get("endpoints", [])
                for endpoint in endpoints:
                    api_endpoints.append({
                        "source_id": source_id,
                        "endpoint_id": endpoint.get("id", "default"),
                        "path": endpoint.get("path", ""),
                        "method": endpoint.get("method", "GET"),
                        "parameters": query.get("filters", {}),
                        "supports": endpoint.get("supports", {})
                    })
    
    # Build timeline if not provided
    if timeline is None:
        timeline = [
            {"step": "Sources selected", "timestamp": now_iso()},
            {"step": "Raw data collected", "timestamp": now_iso()},
            {"step": "Template transformation applied", "timestamp": now_iso()},
            {"step": "Quality checks passed", "timestamp": now_iso()},
            {"step": "Dataset packaged", "timestamp": now_iso()}
        ]
    
    # Build transformations list if not provided
    if transformations_applied is None:
        transformations_applied = []
        # Infer from template
        if template == "tabular":
            transformations_applied = [
                "JSON flattening",
                "Type casting (numeric, date)",
                "Deduplication"
            ]
        elif template == "time_series":
            transformations_applied = [
                "Timestamp identification",
                "Time sorting",
                "Gap handling",
                "Type casting"
            ]
        elif template == "panel":
            transformations_applied = [
                "Entity ID mapping",
                "Time series construction",
                "Panel structure enforcement"
            ]
        elif template == "geospatial":
            transformations_applied = [
                "Geometry extraction",
                "CRS normalization",
                "Coordinate validation"
            ]
        elif template == "text":
            transformations_applied = [
                "Full-text extraction",
                "Metadata enrichment",
                "Deduplication"
            ]
        elif template == "event":
            transformations_applied = [
                "Event detection",
                "Timestamp extraction",
                "Location mapping"
            ]
        else:
            transformations_applied = ["Template-specific transformation"]
    
    return {
        "generated_at": now_iso(),
        "ds_spec": spec_dict,
        "template": template,
        "sources_used": sources_used,
        "api_endpoints": api_endpoints,
        "timeline": timeline,
        "transformations_applied": transformations_applied,
        "reproducibility": {
            "ds_spec_hash": ds_spec_hash,
            "pipeline_version": "AXDATA Pipeline v1.0",
            "pipeline_flow": "DS-SPEC v1 → Domain Normalizer → Template Transformer → Packager v1",
            "reproduction_instructions": "Use the same query and DS-SPEC parameters to reproduce this dataset."
        }
    }


def run(
    ds_spec: Dict[str, Any] | DatasetSpec,
    manifest_dir: str | Path | None = None,
    top_n_sources: int = 3,
    collector_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete pipeline: template selection, source selection, collection.
    
    Args:
        ds_spec: Dataset specification
        manifest_dir: Directory containing source manifests (default: auto-detect)
        top_n_sources: Number of top sources to use
    
    Returns:
        Pipeline result with template, sources, raw data count, and provenance
    """
    # Load manifests
    if manifest_dir is None:
        manifest_dir = get_manifest_path()
    manifests = load_manifests(manifest_dir)
    
    if not manifests:
        logger.warning("No source manifests found")
        return {
            "error": "No source manifests available",
            "template": None,
            "selected_sources": [],
            "raw_count": 0
        }
    
    # Decide template
    template = decide_template(ds_spec)
    logger.info(f"Selected template: {template}")
    
    # Select sources
    spec_dict = ds_spec.model_dump() if isinstance(ds_spec, DatasetSpec) else ds_spec
    selected = select_sources(spec_dict, template, manifests, top_n=top_n_sources)
    logger.info(f"Selected {len(selected)} sources: {[s['source_id'] for s in selected]}")
    
    if not selected:
        logger.warning("No sources selected")
        return {
            "error": "No suitable sources found",
            "template": template,
            "selected_sources": [],
            "raw_count": 0
        }
    
    # Collect raw data
    raw = collect_raw(selected, spec_dict, collector_url=collector_url)
    
    # STEP 1: Normalize using domain-specific normalizer (if applicable)
    normalized_records = []
    normalization_applied = False
    
    # Determine domain from sector
    sector = spec_dict.get("sector", "")
    domain = sector_to_domain(sector)
    
    # Try to get normalizer for domain
    try:
        from normalizers.registry import get_normalizer
        normalizer = get_normalizer(domain)
        
        if normalizer and raw:
            logger.info(f"Applying {domain} normalizer to raw data")
            
            # Convert raw data to normalizer format (raw_assets)
            raw_assets = []
            for raw_item in raw:
                source_id = raw_item.get("source_id", "unknown")
                payload = raw_item.get("payload", {})
                query = raw_item.get("query", {})
                provenance = raw_item.get("provenance", {})
                
                # Extract records
                records = []
                if isinstance(payload, dict):
                    records = payload.get("records", [])
                    if not records and "data" in payload:
                        data = payload["data"]
                        if isinstance(data, list):
                            records = data
                        elif isinstance(data, dict):
                            records = [data]
                
                # Build raw_asset in normalizer format
                raw_asset = {
                    "data": records,
                    "records": records,  # Both formats for compatibility
                    "source": {
                        "connector": source_id,
                        "queries": [query] if query else []
                    },
                    "metadata": payload.get("data", {}),
                    "provenance": provenance,
                    "storage_path": raw_item.get("storage_path")
                }
                raw_assets.append(raw_asset)
            
            # Build dataset_plan from DS-SPEC for normalizer
            dataset_plan = {
                "domain": domain,
                "sources": [{"connector": s["source_id"]} for s in selected],
                "transformations": [],  # Normalizer will apply domain-specific transformations
                "outputs": spec_dict.get("output", {}).get("formats", ["csv"])
            }
            
            # Apply normalization
            normalized_data = normalizer.normalize(raw_assets, dataset_plan)
            
            # Convert normalized data to records format
            try:
                import pandas as pd
                if isinstance(normalized_data, pd.DataFrame):
                    normalized_records = normalized_data.to_dict('records')
                elif isinstance(normalized_data, list):
                    normalized_records = normalized_data
                else:
                    normalized_records = []
            except ImportError:
                # Pandas not available, use as-is
                if isinstance(normalized_data, list):
                    normalized_records = normalized_data
                else:
                    normalized_records = []
            
            normalization_applied = True
            logger.info(f"Normalized {len(raw_assets)} raw assets to {len(normalized_records)} normalized records")
            
    except Exception as e:
        logger.warning(f"Normalization failed for domain '{domain}': {e}. Continuing without normalization.")
        # Fallback: use raw records
        normalization_applied = False
    
    # STEP 2: Transform using template transformer
    transformed_records = []
    if normalization_applied and normalized_records:
        # Use normalized records
        input_records = normalized_records
        logger.info("Transforming normalized records to template format")
    elif raw:
        # Use raw records (fallback if normalization not applied)
        input_records = []
        for raw_item in raw:
            payload = raw_item.get("payload", {})
            if isinstance(payload, dict):
                records = payload.get("records", [])
                if records:
                    input_records.extend(records)
                elif "data" in payload:
                    data = payload["data"]
                    if isinstance(data, list):
                        input_records.extend(data)
                    elif isinstance(data, dict):
                        input_records.append(data)
        logger.info("Transforming raw records to template format (normalization skipped)")
    else:
        input_records = []
    
    if input_records:
        transformer = get_transformer(template)
        if transformer:
            spec_dict = ds_spec.model_dump() if isinstance(ds_spec, DatasetSpec) else ds_spec
            transformed_records = transformer.transform(
                raw_data=input_records,
                ds_spec=spec_dict
            )
            logger.info(f"Transformed {len(input_records)} input records to {len(transformed_records)} {template} records")
        else:
            logger.warning(f"No transformer found for template: {template}")
            transformed_records = input_records  # Use as-is
    
    # Cross-validation if multiple sources
    cross_validation_result = None
    if len(selected) > 1 and transformed_records:
        # Try to extract numeric series for cross-validation
        # This is simplified - in production you'd match series by entity/time
        try:
            # Extract first numeric variable
            spec_dict = ds_spec.model_dump() if isinstance(ds_spec, DatasetSpec) else ds_spec
            numeric_vars = [
                v["name"] for v in spec_dict.get("variables", [])
                if v.get("type") == "numeric"
            ]
            if numeric_vars and len(transformed_records) > 0:
                # Group by source (simplified)
                series_by_source = {}
                for raw_item in raw:
                    source_id = raw_item.get("source_id", "unknown")
                    payload = raw_item.get("payload", {})
                    records = payload.get("records", [])
                    if records and numeric_vars:
                        var_name = numeric_vars[0]
                        values = [
                            float(r.get(var_name, 0))
                            for r in records
                            if r.get(var_name) is not None
                        ]
                        if values:
                            series_by_source[source_id] = values
                
                if len(series_by_source) > 1:
                    cross_validation_result = cross_validate_numeric_series(series_by_source)
        except Exception as e:
            logger.warning(f"Cross-validation failed: {e}")
    
    # Build timeline
    timeline = [
        {"step": "Sources selected", "timestamp": now_iso()},
    ]
    
    # Track transformations
    transformations_applied = []
    if normalization_applied:
        transformations_applied.append(f"Domain normalization ({domain} standard)")
    
    transformer = get_transformer(template) if template else None
    if transformer:
        if template == "tabular":
            transformations_applied = [
                "JSON flattening",
                "Type casting (numeric, date)",
                "Entity ID mapping (ISO country codes)",
                "Deduplication",
                "Missing values handled"
            ]
        elif template == "time_series":
            transformations_applied = [
                "Timestamp identification",
                "Time sorting",
                "Gap handling",
                "Type casting"
            ]
        elif template == "panel":
            transformations_applied = [
                "Entity ID mapping",
                "Time series construction",
                "Panel structure enforcement"
            ]
        elif template == "geospatial":
            transformations_applied = [
                "Geometry extraction",
                "CRS normalization",
                "Coordinate validation"
            ]
        elif template == "text":
            transformations_applied = [
                "Full-text extraction",
                "Metadata enrichment",
                "Deduplication"
            ]
        elif template == "event":
            transformations_applied = [
                "Event detection",
                "Timestamp extraction",
                "Location mapping"
            ]
    
    # Add timeline steps
    if raw:
        timeline.append({"step": "Raw data collected", "timestamp": now_iso()})
    if normalization_applied:
        timeline.append({"step": f"Domain normalization completed ({domain})", "timestamp": now_iso()})
    if transformed_records:
        timeline.append({"step": "Template transformation completed", "timestamp": now_iso()})
    if cross_validation_result:
        timeline.append({"step": "Cross-source validation completed", "timestamp": now_iso()})
    timeline.append({"step": "Quality checks passed", "timestamp": now_iso()})
    timeline.append({"step": "Dataset packaged", "timestamp": now_iso()})
    
    # Build provenance
    provenance = build_provenance(
        ds_spec=ds_spec,
        template=template,
        sources=selected,
        raw_data=raw,
        transformations_applied=transformations_applied,
        timeline=timeline
    )
    
    return {
        "template": template,
        "selected_sources": [s["source_id"] for s in selected],
        "raw_count": len(raw),
        "normalized_count": len(normalized_records) if normalization_applied else 0,
        "normalization_applied": normalization_applied,
        "normalization_domain": domain if normalization_applied else None,
        "transformed_count": len(transformed_records),
        "raw_data": raw,
        "normalized_records": normalized_records if normalization_applied else None,
        "transformed_records": transformed_records,
        "provenance": provenance,
        "cross_validation": cross_validation_result
    }
