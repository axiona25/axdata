"""Packager - creates standard AXDATA dataset package."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import shutil
import zipfile
import logging

from axdata.packaging.metadata_builder import build_metadata
from axdata.packaging.schema_generator import build_schema_from_spec
from axdata.packaging.compliance_builder import build_compliance
from axdata.packaging.readme_builder import build_readme
from axdata.packaging.quality_builder import build_quality_report
from axdata.spec.ds_spec import DatasetSpec

logger = logging.getLogger(__name__)


def _write_json(path: Path, obj: Any) -> None:
    """Write JSON file."""
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_dir(p: Path) -> None:
    """Ensure directory exists."""
    p.mkdir(parents=True, exist_ok=True)


def create_zip(folder: Path, zip_path: Path) -> None:
    """Create ZIP archive from folder."""
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(folder))


def package_dataset(
    out_dir: str | Path,
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    sources_used: List[Dict[str, Any]],
    dataset_bytes: Optional[bytes] = None,
    dataset_filename: str = "dataset.csv",
    record_count: Optional[int] = None,
    records: Optional[List[Dict[str, Any]]] = None,  # For quality calculation
    pii_detected: bool = False,
    quality_report: Optional[Dict[str, Any]] = None,
    cross_validation_result: Optional[Dict[str, Any]] = None,
    provenance: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Package dataset into standard AXDATA structure.
    
    Args:
        out_dir: Output directory
        ds_spec: Dataset specification
        template: Selected template
        sources_used: List of source manifests used
        dataset_bytes: Dataset file bytes (CSV/Parquet/etc.)
        dataset_filename: Dataset filename
        record_count: Number of records
        pii_detected: Whether PII was detected
        quality_report: Optional quality report
        provenance: Optional provenance data
    
    Returns:
        Dictionary with package_dir and zip_path
    """
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    ensure_dir(out)
    
    data_dir = out / "data"
    ensure_dir(data_dir)
    
    # DATA
    if dataset_bytes is None:
        # placeholder, così non si rompe il flusso mentre integri la trasformazione vera
        dataset_bytes = b""
    (data_dir / dataset_filename).write_bytes(dataset_bytes)
    
    # SCHEMA
    schema = build_schema_from_spec(ds_spec, template)
    _write_json(out / "schema.json", schema)
    
    # METADATA
    metadata = build_metadata(ds_spec, template, sources_used, record_count=record_count)
    _write_json(out / "metadata.json", metadata)
    
    # PROVENANCE (se non passato, crea un placeholder)
    if provenance is None:
        provenance = {
            "note": "provenance not provided by pipeline yet. pass it from pipeline/run_pipeline.py output."
        }
    _write_json(out / "provenance.json", provenance)
    
    # COMPLIANCE
    compliance = build_compliance(
        ds_spec=ds_spec,
        sources_used=sources_used,
        pii_detected=pii_detected,
        records=records
    )
    _write_json(out / "compliance.json", compliance)
    
    # QUALITY REPORT (sempre generato se records disponibili)
    if quality_report is None and records is not None:
        # Convert to dict if needed
        spec_dict = ds_spec.model_dump() if isinstance(ds_spec, DatasetSpec) else ds_spec
        quality_report = build_quality_report(
            records=records,
            ds_spec=spec_dict,
            cross_validation_result=cross_validation_result
        )
    
    if quality_report is not None:
        _write_json(out / "quality.json", quality_report)
    
    # README
    readme = build_readme(ds_spec, template, sources_used)
    (out / "README.md").write_text(readme, encoding="utf-8")
    
    # ZIP
    zip_path = out.with_suffix(".zip")
    create_zip(out, zip_path)
    
    logger.info(f"Packaged dataset: {out} -> {zip_path}")
    
    return {
        "package_dir": str(out),
        "zip_path": str(zip_path)
    }
