"""Integration between AXDATA packager and existing export flow."""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import tempfile
import shutil

from axdata.spec.ds_spec import DatasetSpec
from axdata.packaging.packager import package_dataset
from axdata.sources.loader import load_manifests, get_manifest_path
from services.export_service import export_to_csv, export_to_json, export_to_parquet

logger = logging.getLogger(__name__)


def is_axdata_dataset(plan_json: Dict[str, Any]) -> bool:
    """
    Check if dataset was created with DS-SPEC (AXDATA standard).
    
    Args:
        plan_json: Dataset plan_json from database
    
    Returns:
        True if dataset uses AXDATA DS-SPEC
    """
    if not isinstance(plan_json, dict):
        return False
    
    # Check for DS-SPEC indicators
    has_version = plan_json.get("version") == "1.0"
    has_dimensions = "dimensions" in plan_json
    has_output_template = "output" in plan_json and "template" in plan_json.get("output", {})
    
    # Also check for pipeline_result (indicates AXDATA pipeline was used)
    has_pipeline_result = "pipeline_result" in plan_json
    
    return (has_version and has_dimensions) or has_pipeline_result


def create_axdata_package_from_export(
    records: List[Dict[str, Any]],
    dataset_id: str,
    plan_json: Dict[str, Any],
    sources_used: List[Dict[str, Any]],
    outputs: List[str],
    template: Optional[str] = None
) -> bytes:
    """
    Create AXDATA package from exported records.
    
    This integrates the AXDATA packager with the existing export flow.
    
    Args:
        records: Normalized records
        dataset_id: Dataset ID
        plan_json: Dataset plan (should contain DS-SPEC)
        sources_used: List of source manifests used
        outputs: Output formats requested
        template: Template type (if known)
    
    Returns:
        ZIP file bytes
    """
    # Extract DS-SPEC from plan_json
    if "pipeline_result" in plan_json:
        # DS-SPEC is at root level
        ds_spec_dict = {k: v for k, v in plan_json.items() if k != "pipeline_result"}
        template = template or plan_json.get("pipeline_result", {}).get("template", "tabular")
    else:
        # Assume plan_json is DS-SPEC
        ds_spec_dict = plan_json
        template = template or plan_json.get("output", {}).get("template", "auto")
    
    try:
        ds_spec = DatasetSpec(**ds_spec_dict)
    except Exception as e:
        logger.warning(f"Could not parse DS-SPEC from plan_json: {e}, using defaults")
        # Fallback to basic DS-SPEC
        ds_spec = DatasetSpec(
            version="1.0",
            request={
                "query_text": plan_json.get("title", "Dataset"),
                "language": "it"
            },
            sector=plan_json.get("sector", "unknown"),
            dimensions={
                "time": {"enabled": False},
                "geo": {"enabled": False},
                "entity": {"kind": "none"}
            },
            variables=[{"name": "value", "type": "numeric"}],
            output={"template": "auto", "formats": outputs}
        )
    
    # Determine dataset filename based on format
    dataset_filename = "dataset.csv"
    dataset_bytes = None
    
    if "csv" in outputs:
        dataset_bytes = export_to_csv(records)
        dataset_filename = "dataset.csv"
    elif "parquet" in outputs:
        try:
            dataset_bytes = export_to_parquet(records)
            dataset_filename = "dataset.parquet"
        except ImportError:
            dataset_bytes = export_to_csv(records)
            dataset_filename = "dataset.csv"
    elif "json" in outputs:
        dataset_bytes = export_to_json(records)
        dataset_filename = "dataset.json"
    else:
        dataset_bytes = export_to_csv(records)
        dataset_filename = "dataset.csv"
    
    # Load source manifests if not provided
    if not sources_used:
        manifest_dir = get_manifest_path()
        all_manifests = load_manifests(manifest_dir)
        # Try to match sources from plan
        pipeline_result = plan_json.get("pipeline_result", {})
        selected_source_ids = pipeline_result.get("selected_sources", [])
        sources_used = [
            m for m in all_manifests
            if m.get("source_id") in selected_source_ids
        ]
    
    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as tmpdir:
        package_result = package_dataset(
            out_dir=tmpdir,
            ds_spec=ds_spec,
            template=template,
            sources_used=sources_used,
            dataset_bytes=dataset_bytes,
            dataset_filename=dataset_filename,
            record_count=len(records),
            provenance=plan_json.get("pipeline_result", {}).get("provenance")
        )
        
        # Read ZIP file
        zip_path = Path(package_result["zip_path"])
        zip_bytes = zip_path.read_bytes()
        
        return zip_bytes


def integrate_axdata_export(
    records: List[Dict[str, Any]],
    dataset_id: str,
    plan_json: Dict[str, Any],
    sources: List[Dict[str, Any]],
    outputs: List[str],
    use_axdata_if_available: bool = True
) -> bytes:
    """
    Integrate AXDATA export with existing export flow.
    
    If dataset uses DS-SPEC, use AXDATA packager.
    Otherwise, use standard export.
    
    Args:
        records: Normalized records
        dataset_id: Dataset ID
        plan_json: Dataset plan
        sources: Source information
        outputs: Output formats
        use_axdata_if_available: Whether to use AXDATA packager if DS-SPEC detected
    
    Returns:
        ZIP bundle bytes
    """
    if use_axdata_if_available and is_axdata_dataset(plan_json):
        logger.info(f"Using AXDATA packager for dataset {dataset_id}")
        try:
            return create_axdata_package_from_export(
                records=records,
                dataset_id=dataset_id,
                plan_json=plan_json,
                sources_used=sources,
                outputs=outputs
            )
        except Exception as e:
            logger.error(f"Error using AXDATA packager, falling back to standard: {e}")
            # Fall through to standard export
    
    # Use standard export
    logger.info(f"Using standard export for dataset {dataset_id}")
    from services.export_service import (
        generate_manifest,
        generate_data_dictionary,
        create_bundle
    )
    from datetime import datetime
    from datetime import datetime
    
    # Generate standard manifest
    manifest = generate_manifest(
        dataset_id=dataset_id,
        title=plan_json.get("title", "Dataset"),
        domain=plan_json.get("sector", "unknown"),
        sources=sources,
        transformations=[],
        outputs=outputs,
        row_count=len(records),
        created_at=datetime.utcnow(),
        methodology=plan_json.get("methodology"),
        license=plan_json.get("license"),
        citation=plan_json.get("citation"),
        geographic_coverage=plan_json.get("geographic_coverage"),
        temporal_coverage=plan_json.get("temporal_coverage"),
        version=plan_json.get("version", "1.0")
    )
    
    data_dictionary = generate_data_dictionary(
        records=records,
        domain=plan_json.get("sector", "unknown")
    )
    
    from services.export_service import generate_provenance
    provenance = generate_provenance(
        sources=sources,
        transformations=[],
        created_at=datetime.utcnow(),
        dataset_id=dataset_id
    )
    
    return create_bundle(
        records=records,
        manifest=manifest,
        data_dictionary=data_dictionary,
        provenance=provenance,
        outputs=outputs,
        dataset_id=dataset_id
    )
