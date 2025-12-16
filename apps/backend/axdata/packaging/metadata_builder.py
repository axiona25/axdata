"""Metadata builder - DCAT/FAIR-compliant metadata generation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import json
from axdata.spec.ds_spec import DatasetSpec


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def stable_id_from_spec(ds_spec: Dict[str, Any] | DatasetSpec) -> str:
    """
    Generate stable ID from DS-SPEC (deterministic).
    
    Args:
        ds_spec: Dataset specification
    
    Returns:
        Stable ID (24 char hex)
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    raw = json.dumps(spec_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def build_metadata(
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    sources_used: List[Dict[str, Any]],
    record_count: Optional[int] = None,
    time_coverage: Optional[Dict[str, str]] = None,
    geo_coverage: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Build DCAT/FAIR-compliant metadata.
    
    Args:
        ds_spec: Dataset specification
        template: Selected template
        sources_used: List of source manifests used
        record_count: Number of records in dataset
        time_coverage: Time coverage info (optional override)
        geo_coverage: Geo coverage info (optional override)
    
    Returns:
        Metadata dictionary
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    ds_id = stable_id_from_spec(spec_dict)
    
    title = f"AXDATA Dataset ({spec_dict.get('sector', 'unknown')})"
    desc = spec_dict.get("request", {}).get("query_text", "").strip()
    
    # Licenze: raccogli e deduplica
    licenses = []
    for s in sources_used:
        lic = s.get("license", {})
        if lic:
            licenses.append({
                "source_id": s.get("source_id"),
                "name": lic.get("name"),
                "url": lic.get("url"),
                "commercial_use": lic.get("commercial_use", False),
                "attribution_required": lic.get("attribution_required", True)
            })
    
    # dedup by (name,url)
    seen = set()
    licenses_dedup = []
    for l in licenses:
        key = (l.get("name"), l.get("url"))
        if key in seen:
            continue
        seen.add(key)
        licenses_dedup.append(l)
    
    dims = spec_dict.get("dimensions", {})
    time_cov = time_coverage or {
        "enabled": dims.get("time", {}).get("enabled", False),
        "start": dims.get("time", {}).get("start"),
        "end": dims.get("time", {}).get("end"),
        "granularity": dims.get("time", {}).get("granularity", "none")
    }
    geo_cov = geo_coverage or {
        "enabled": dims.get("geo", {}).get("enabled", False),
        "scope": dims.get("geo", {}).get("scope"),
        "level": dims.get("geo", {}).get("level", "none"),
        "crs": dims.get("geo", {}).get("crs", "EPSG:4326")
    }
    
    # DCAT-ish core + FAIR notes
    return {
        "axdata": {
            "dataset_id": ds_id,
            "version": "1.0",
            "created_at": now_iso(),
            "template": template,
            "formats": spec_dict.get("output", {}).get("formats", ["csv"]),
            "record_count": record_count
        },
        "dcat": {
            "title": title,
            "description": desc,
            "language": spec_dict.get("request", {}).get("language", "it"),
            "theme": spec_dict.get("sector"),
            "publisher": "AXDATA",
            "keywords": [spec_dict.get("sector", "dataset"), template],
            "landing_page": "https://axdata.eu",
            "provenance": "Generated via AXDATA pipeline (sources and queries in provenance.json)."
        },
        "coverage": {
            "time": time_cov,
            "geo": geo_cov,
            "entity": dims.get("entity", {})
        },
        "variables": spec_dict.get("variables", []),
        "sources": [
            {
                "source_id": s.get("source_id"),
                "name": s.get("name"),
                "authority_level": (s.get("authority") or {}).get("level"),
                "publisher": (s.get("authority") or {}).get("publisher")
            }
            for s in sources_used
        ],
        "license": {
            "policy": spec_dict.get("output", {}).get("compliance", {}).get("license_policy", "normal"),
            "licenses": licenses_dedup
        },
        "fair": {
            "findable": "dataset_id, metadata.json and provenance.json enable discovery and citation.",
            "accessible": "packaged as standard files + optional API delivery.",
            "interoperable": "schema.json + normalized fields; formats include CSV/JSON/Parquet/GeoJSON.",
            "reusable": "license and provenance tracked; README documents methodology and limitations."
        }
    }
