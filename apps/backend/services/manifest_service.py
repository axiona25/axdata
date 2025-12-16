"""Manifest Universale v1.0 generation service - FAIR-compliant, cross-domain."""
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import uuid

from core.config import settings

logger = logging.getLogger(__name__)


def calculate_checksum(data: bytes, algorithm: str = "sha256") -> str:
    """
    Calculate checksum for data.
    
    Args:
        data: Data bytes
        algorithm: Hash algorithm (sha256 or md5)
    
    Returns:
        Hexadecimal hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def generate_manifest_universale_v1(
    dataset_id: str,
    dataset_family_id: Optional[str],
    title: str,
    description: Optional[str],
    domain: str,
    keywords: Optional[List[str]],
    version: str,
    created_at: datetime,
    updated_at: datetime,
    user_id: str,
    org_id: Optional[str],
    sources: List[Dict[str, Any]],
    transformations: List[Dict[str, Any]],
    schema_summary: Dict[str, Any],
    files: List[Dict[str, Any]],
    license_info: Dict[str, Any],
    citation_info: Dict[str, Any],
    quality_info: Optional[Dict[str, Any]] = None,
    billing_info: Optional[Dict[str, Any]] = None,
    security_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate Manifest Universale v1.0 - FAIR-compliant, cross-domain.
    
    Args:
        dataset_id: Dataset UUID
        dataset_family_id: Optional family UUID for versioning
        title: Dataset title
        description: Dataset description
        domain: Domain (economics, biomedical, physics, math, demography)
        keywords: Optional keywords
        version: Version string
        created_at: Creation timestamp
        updated_at: Update timestamp
        user_id: User ID (owner)
        org_id: Optional organization ID
        sources: List of source information
        transformations: List of transformation steps
        schema_summary: Schema summary (row_count, column_count, etc.)
        files: List of file information with checksums
        license_info: License information
        citation_info: Citation information
        quality_info: Optional quality metrics
        billing_info: Optional billing information
        security_info: Optional security classification
    
    Returns:
        Manifest Universale v1.0 dictionary
    """
    # Creator information
    creator = {
        "name": "Dataset On-Demand Portal",
        "system": {
            "platform": "dataset-portal",
            "backend_version": getattr(settings, 'api_version', '0.1.0'),
            "collector_version": "0.1.0",
            "normalizer_version": "0.1.0"
        },
        "contact": {
            "email": getattr(settings, 'support_email', 'support@datasetportal.com'),
            "url": getattr(settings, 'portal_url', 'https://datasetportal.com')
        }
    }
    
    # Owner information (internal references, no sensitive data)
    owner = {
        "user_id": user_id
    }
    if org_id:
        owner["org_id"] = org_id
    
    # Build manifest
    manifest = {
        "manifest_version": "1.0",
        "dataset_id": dataset_id,
        "version": version,
        "title": title,
        "domain": domain,
        "created_at": created_at.isoformat(),
        "creator": creator,
        "owner": owner,
        "sources": sources,
        "transformations": transformations,
        "schema_summary": schema_summary,
        "files": files,
        "license": license_info,
        "citation": citation_info
    }
    
    # Optional fields
    if dataset_family_id:
        manifest["dataset_family_id"] = dataset_family_id
    
    if description:
        manifest["description"] = description
    
    if keywords:
        manifest["keywords"] = keywords[:50]  # Max 50 keywords
    
    manifest["updated_at"] = updated_at.isoformat()
    
    if quality_info:
        manifest["quality"] = quality_info
    
    if billing_info:
        manifest["billing"] = billing_info
    
    if security_info:
        manifest["security"] = security_info
    
    return manifest


def generate_schema_summary(
    records: List[Dict[str, Any]],
    domain: str,
    primary_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate schema summary for manifest.
    
    Args:
        records: Dataset records
        domain: Dataset domain
        primary_keys: Optional primary key columns
    
    Returns:
        Schema summary dictionary
    """
    if not records:
        return {
            "row_count": 0,
            "column_count": 0,
            "time_granularity": "unknown",
            "geo_granularity": "unknown",
            "units": []
        }
    
    first_record = records[0]
    column_count = len(first_record.keys())
    row_count = len(records)
    
    summary = {
        "row_count": row_count,
        "column_count": column_count,
        "time_granularity": "unknown",
        "geo_granularity": "unknown",
        "units": []
    }
    
    if primary_keys:
        summary["primary_keys"] = primary_keys
    
    # Detect time granularity
    time_fields = ['time', 'year', 'quarter', 'month', 'day', 'date', 'timestamp']
    for field in time_fields:
        if field in first_record:
            if field in ['year']:
                summary["time_granularity"] = "year"
            elif field in ['quarter']:
                summary["time_granularity"] = "quarter"
            elif field in ['month']:
                summary["time_granularity"] = "month"
            elif field in ['day', 'date']:
                summary["time_granularity"] = "day"
            elif field in ['timestamp']:
                summary["time_granularity"] = "hour"
            break
    
    # Detect geo granularity
    geo_fields = ['geo', 'country', 'region', 'city']
    for field in geo_fields:
        if field in first_record:
            if field == 'country' or field == 'geo':
                summary["geo_granularity"] = "country"
            elif field == 'region':
                summary["geo_granularity"] = "region"
            elif field == 'city':
                summary["geo_granularity"] = "city"
            break
    
    # Extract units from records or column names
    units = set()
    for record in records[:100]:  # Sample first 100 records
        for key, value in record.items():
            if 'unit' in key.lower() and value:
                units.add(str(value))
    
    summary["units"] = list(units)[:20]  # Max 20 units
    
    return summary


def generate_file_entry(
    role: str,
    format_type: str,
    uri: str,
    data: bytes,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate file entry with checksum.
    
    Args:
        role: File role (data, manifest, data_dictionary, etc.)
        format_type: File format (csv, json, parquet, etc.)
        uri: File URI/path
        data: File data bytes
        mime_type: Optional MIME type
    
    Returns:
        File entry dictionary
    """
    # Calculate checksum
    checksum_value = calculate_checksum(data, "sha256")
    
    # Determine MIME type if not provided
    if not mime_type:
        mime_types = {
            "csv": "text/csv",
            "json": "application/json",
            "parquet": "application/octet-stream",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
            "txt": "text/plain",
            "zip": "application/zip"
        }
        mime_type = mime_types.get(format_type, "application/octet-stream")
    
    return {
        "role": role,
        "format": format_type,
        "uri": uri,
        "checksum": {
            "algo": "sha256",
            "value": checksum_value
        },
        "bytes": len(data),
        "mime_type": mime_type
    }


def generate_source_entry(
    connector: str,
    source_name: str,
    source_type: str,
    base_url: Optional[str],
    retrieved_at: datetime,
    queries: List[Dict[str, Any]],
    license_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate source entry for manifest.
    
    Args:
        connector: Connector name
        source_name: Source name
        source_type: Source type (api, repository, download, scrape, manual)
        base_url: Base URL
        retrieved_at: Retrieval timestamp
        queries: List of queries
        license_info: Optional license information
    
    Returns:
        Source entry dictionary
    """
    source = {
        "connector": connector,
        "source_name": source_name,
        "source_type": source_type,
        "retrieved_at": retrieved_at.isoformat(),
        "queries": queries
    }
    
    if base_url:
        source["base_url"] = base_url
    
    if license_info:
        source["license"] = license_info
    
    return source


def generate_transformation_entry(
    step_id: str,
    trans_type: str,
    params: Dict[str, Any],
    applied_at: datetime,
    input_assets: Optional[List[str]] = None,
    output_assets: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate transformation entry for manifest.
    
    Args:
        step_id: Step identifier
        trans_type: Transformation type
        params: Transformation parameters
        applied_at: Application timestamp
        input_assets: Optional input asset paths
        output_assets: Optional output asset paths
    
    Returns:
        Transformation entry dictionary
    """
    trans = {
        "step_id": step_id,
        "type": trans_type,
        "params": params,
        "applied_at": applied_at.isoformat()
    }
    
    if input_assets:
        trans["input_assets"] = input_assets
    
    if output_assets:
        trans["output_assets"] = output_assets
    
    return trans


def validate_manifest(manifest: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate manifest against JSON Schema.
    
    Args:
        manifest: Manifest dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import jsonschema
        schema_path = Path(__file__).parent.parent / "schemas" / "manifest_schema.json"
        
        if not schema_path.exists():
            logger.warning("Manifest schema not found, skipping validation")
            return True, None
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        jsonschema.validate(instance=manifest, schema=schema)
        return True, None
    
    except ImportError:
        logger.warning("jsonschema not installed, skipping validation")
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Error validating manifest: {e}", exc_info=True)
        return False, str(e)

