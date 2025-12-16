"""Export service for generating datasets in multiple formats - FAIR-compliant."""
import json
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import zipfile
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("Pandas not available, Parquet export will be limited")

logger = logging.getLogger(__name__)


def export_to_csv(records: List[Dict[str, Any]]) -> bytes:
    """Export records to CSV format."""
    if not records:
        return b""
    
    output = io.StringIO()
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue().encode('utf-8')


def export_to_json(records: List[Dict[str, Any]], pretty: bool = True) -> bytes:
    """Export records to JSON format."""
    if pretty:
        content = json.dumps(records, indent=2, ensure_ascii=False)
    else:
        content = json.dumps(records, ensure_ascii=False)
    
    return content.encode('utf-8')


def export_to_parquet(records: List[Dict[str, Any]]) -> bytes:
    """Export records to Parquet format."""
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas is required for Parquet export")
    
    if not records:
        return b""
    
    df = pd.DataFrame(records)
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine='pyarrow')
    return buffer.getvalue()


def generate_manifest(
    dataset_id: str,
    title: str,
    domain: str,
    sources: List[Dict[str, Any]],
    transformations: List[Dict[str, Any]],
    outputs: List[str],
    row_count: int,
    created_at: datetime,
    methodology: Optional[str] = None,
    license: Optional[str] = None,
    citation: Optional[str] = None,
    geographic_coverage: Optional[str] = None,
    temporal_coverage: Optional[str] = None,
    version: str = "1.0"
) -> Dict[str, Any]:
    """
    Generate manifest (legacy function - use generate_manifest_universale_v1 for v1.0).
    
    This function is kept for backward compatibility.
    New code should use manifest_service.generate_manifest_universale_v1.
    """
    # Import new manifest service
    from services.manifest_service import generate_manifest_universale_v1, generate_schema_summary
    
    # This is a simplified version - full implementation uses manifest_service
    return {
        "title": title,
        "dataset_id": dataset_id,
        "domain": domain,
        "version": version,
        "created_at": created_at.isoformat(),
        "sources": sources,
        "transformations": transformations,
        "row_count": row_count,
        "outputs": outputs,
        "methodology": methodology,
        "license": license,
        "citation": citation,
        "geographic_coverage": geographic_coverage,
        "temporal_coverage": temporal_coverage,
        "standards": {
            "fair_compliant": True,
            "domain_standard": _get_domain_standard(domain)
        },
        "format_version": "2.0",
        "manifest_schema": "FAIR-Dataset-Manifest-v2.0"
    }


def _get_domain_standard(domain: str) -> str:
    """Get the standard used for a domain."""
    standards = {
        "economics": "SDMX (Statistical Data and Metadata eXchange)",
        "biomedical": "CDISC/HL7 FHIR/OMOP Common Data Model",
        "physics": "FAIR Data Principles / NetCDF",
        "math": "OpenML / UCI ML Repository conventions",
        "demography": "UN SDG Metadata / Eurostat demographic model"
    }
    return standards.get(domain, "FAIR Data Principles")


def generate_data_dictionary(
    records: List[Dict[str, Any]],
    domain: str = "general",
    indicators_metadata: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive data dictionary (FAIR-compliant).
    
    Includes:
    - Column name, type, description
    - Unit of measurement
    - Domain-specific metadata
    - Validation rules
    
    Args:
        records: Sample records to analyze
        domain: Dataset domain for domain-specific metadata
        indicators_metadata: Optional metadata for indicators/columns
    
    Returns:
        Comprehensive data dictionary
    """
    if not records:
        return {"columns": [], "total_rows": 0, "generated_at": datetime.utcnow().isoformat()}
    
    columns = []
    first_record = records[0]
    
    for column_name in first_record.keys():
        # Analyze column
        values = [record.get(column_name) for record in records if column_name in record]
        non_null_values = [v for v in values if v is not None]
        
        # Determine type
        if non_null_values:
            first_value = non_null_values[0]
            if isinstance(first_value, (int, float)):
                col_type = "numeric"
            elif isinstance(first_value, bool):
                col_type = "boolean"
            elif isinstance(first_value, str):
                # Try to detect date
                try:
                    datetime.fromisoformat(first_value.replace('Z', '+00:00'))
                    col_type = "date"
                except:
                    col_type = "string"
            else:
                col_type = "string"
        else:
            col_type = "unknown"
        
        # Get domain-specific metadata if available
        col_metadata = indicators_metadata.get(column_name, {}) if indicators_metadata else {}
        
        column_info = {
            "name": column_name,
            "type": col_type,
            "nullable": len(non_null_values) < len(values),
            "null_count": len(values) - len(non_null_values),
            "description": col_metadata.get("description", ""),
            "unit": col_metadata.get("unit", ""),
            "notes": col_metadata.get("notes", "")
        }
        
        # Domain-specific enhancements
        if domain == "economics":
            # SDMX-style metadata
            if column_name.lower() in ["geo", "country", "region"]:
                column_info["dimension_type"] = "geographic"
                column_info["standard"] = "ISO 3166"
            elif column_name.lower() in ["time", "year", "period", "date"]:
                column_info["dimension_type"] = "temporal"
            elif col_type == "numeric":
                column_info["dimension_type"] = "measure"
                column_info["indicator"] = col_metadata.get("indicator", column_name)
        
        elif domain == "biomedical":
            # CDISC/OMOP-style metadata
            if column_name.lower() in ["study_id", "trial_id"]:
                column_info["cdisc_domain"] = "STUDY"
            elif column_name.lower() in ["condition", "disease"]:
                column_info["cdisc_domain"] = "CM"
            elif column_name.lower() in ["population", "cohort"]:
                column_info["cdisc_domain"] = "COHORT"
        
        elif domain == "math":
            # ML-style metadata
            if col_metadata.get("role") == "feature":
                column_info["ml_role"] = "feature"
            elif col_metadata.get("role") == "target":
                column_info["ml_role"] = "target"
                column_info["task"] = col_metadata.get("task", "unknown")
        
        # Add unique values count if reasonable
        if col_type in ["string", "date"] and len(non_null_values) <= 100:
            unique_values = len(set(non_null_values))
            column_info["unique_values"] = unique_values
        
        # Add statistics for numeric columns
        if col_type == "numeric" and non_null_values:
            numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
            if numeric_values:
                column_info["statistics"] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values) if numeric_values else None
                }
        
        columns.append(column_info)
    
    return {
        "columns": columns,
        "total_rows": len(records),
        "domain": domain,
        "generated_at": datetime.utcnow().isoformat(),
        "schema_version": "2.0"
    }


def generate_provenance(
    sources: List[Dict[str, Any]],
    transformations: List[Dict[str, Any]],
    created_at: datetime,
    dataset_id: str
) -> Dict[str, Any]:
    """
    Generate comprehensive provenance information (FAIR-compliant).
    
    Includes:
    - Source information
    - Query details
    - Transformations applied
    - Timestamps
    - Lineage
    
    Args:
        sources: List of data sources
        transformations: List of transformations
        created_at: Creation timestamp
        dataset_id: Dataset ID
    
    Returns:
        Comprehensive provenance dictionary
    """
    provenance = {
        "dataset_id": dataset_id,
        "created_at": created_at.isoformat(),
        "sources": [],
        "transformations": [],
        "lineage": {
            "raw_data_collected": created_at.isoformat(),
            "normalization_applied": True,
            "export_generated": datetime.utcnow().isoformat()
        }
    }
    
    # Add source provenance
    for source in sources:
        source_prov = {
            "connector": source.get("connector", "unknown"),
            "queries": source.get("queries", []),
            "row_count": source.get("row_count", 0),
            "collected_at": source.get("collected_at", created_at.isoformat()),
            "storage_path": source.get("storage_path"),
            "metadata": source.get("metadata", {}),
            "provenance": source.get("provenance", {})
        }
        provenance["sources"].append(source_prov)
    
    # Add transformation provenance
    for transformation in transformations:
        trans_prov = {
            "type": transformation.get("type", "unknown"),
            "params": transformation.get("params", {}),
            "applied_at": datetime.utcnow().isoformat()
        }
        provenance["transformations"].append(trans_prov)
    
    return provenance


def create_bundle(
    records: List[Dict[str, Any]],
    manifest: Dict[str, Any],
    data_dictionary: Dict[str, Any],
    provenance: Dict[str, Any],
    outputs: List[str],
    dataset_id: str,
    readme_content: Optional[str] = None,
    use_manifest_v1: bool = True
) -> bytes:
    """
    Create a FAIR-compliant bundle (ZIP) with dataset files and documentation.
    
    Bundle includes:
    - Data files (CSV, JSON, Parquet)
    - manifest.json (FAIR-compliant)
    - data_dictionary.json (comprehensive)
    - provenance.json (complete lineage)
    - README.md (optional scientific documentation)
    
    Args:
        records: Dataset records
        manifest: Manifest dictionary
        data_dictionary: Data dictionary
        provenance: Provenance information
        outputs: List of output formats to include
        dataset_id: Dataset ID
        readme_content: Optional README content
    
    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add data files
        if "csv" in outputs:
            csv_data = export_to_csv(records)
            zip_file.writestr(f"{dataset_id}.csv", csv_data)
        
        if "json" in outputs:
            json_data = export_to_json(records, pretty=True)
            zip_file.writestr(f"{dataset_id}.json", json_data)
        
        if "parquet" in outputs:
            try:
                parquet_data = export_to_parquet(records)
                zip_file.writestr(f"{dataset_id}.parquet", parquet_data)
            except ImportError:
                logger.warning("Parquet export skipped (pandas/pyarrow not available)")
        
        # Add documentation (FAIR-compliant)
        # Use manifest as-is (should already be Manifest Universale v1.0 if use_manifest_v1=True)
        manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
        zip_file.writestr("manifest.json", manifest_json.encode('utf-8'))
        
        data_dict_json = json.dumps(data_dictionary, indent=2, ensure_ascii=False)
        zip_file.writestr("data_dictionary.json", data_dict_json.encode('utf-8'))
        
        provenance_json = json.dumps(provenance, indent=2, ensure_ascii=False)
        zip_file.writestr("provenance.json", provenance_json.encode('utf-8'))
        
        # Add README if provided
        if readme_content:
            zip_file.writestr("README.md", readme_content.encode('utf-8'))
        else:
            # Generate basic README
            readme = f"""# {manifest.get('title', 'Dataset')}

## Dataset Information

- **Domain**: {manifest.get('domain', 'unknown')}
- **Version**: {manifest.get('version', '1.0')}
- **Created**: {manifest.get('created_at', 'unknown')}
- **Rows**: {manifest.get('row_count', 0)}

## Standards Compliance

This dataset follows:
- **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
- **Domain Standard**: {manifest.get('standards', {}).get('domain_standard', 'FAIR Data Principles')}

## Files

- `{dataset_id}.csv` - CSV format
- `{dataset_id}.json` - JSON format
- `{dataset_id}.parquet` - Parquet format (if available)
- `manifest.json` - Complete dataset metadata
- `data_dictionary.json` - Column definitions and metadata
- `provenance.json` - Data lineage and transformations

## Citation

{manifest.get('citation', 'Please cite according to source licenses')}

## License

{manifest.get('license', 'See source licenses')}
"""
            zip_file.writestr("README.md", readme.encode('utf-8'))
    
    buffer.seek(0)
    return buffer.getvalue()
