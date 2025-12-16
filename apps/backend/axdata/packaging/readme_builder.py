"""README builder - methodology and limitations documentation."""
from __future__ import annotations
from typing import Any, Dict, List
from axdata.spec.ds_spec import DatasetSpec


def build_readme(
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    sources_used: List[Dict[str, Any]]
) -> str:
    """
    Build README.md content.
    
    Args:
        ds_spec: Dataset specification
        template: Selected template
        sources_used: List of source manifests used
    
    Returns:
        README content as string
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    q = spec_dict.get("request", {}).get("query_text", "")
    sector = spec_dict.get("sector", "unknown")
    dims = spec_dict.get("dimensions", {})
    
    sources_lines = "\n".join([
        f"- {s.get('name')} ({s.get('source_id')})"
        for s in sources_used
    ]) or "- (none)"
    
    time_line = "enabled" if dims.get("time", {}).get("enabled", False) else "disabled"
    geo_line = "enabled" if dims.get("geo", {}).get("enabled", False) else "disabled"
    
    time_start = dims.get("time", {}).get("start", "N/A")
    time_end = dims.get("time", {}).get("end", "N/A")
    time_gran = dims.get("time", {}).get("granularity", "none")
    
    geo_scope = dims.get("geo", {}).get("scope", "N/A")
    geo_level = dims.get("geo", {}).get("level", "none")
    geo_crs = dims.get("geo", {}).get("crs", "EPSG:4326")
    
    return f"""# AXDATA Dataset Package

## Query

{q}

## Sector

{sector}

## Template

{template}

## Coverage

- Time: {time_line} | start={time_start} end={time_end} granularity={time_gran}
- Geo: {geo_line} | scope={geo_scope} level={geo_level} crs={geo_crs}

## Sources used

{sources_lines}

## Methodology (high level)

1. DS-SPEC parsed from user query (see provenance.json).
2. Sources selected by Source Selection Engine (authority + coverage + license).
3. Raw data fetched and stored (see provenance.json).
4. Normalization + quality checks.
5. Template transformation into the chosen model.
6. Packaging into a standard, reproducible bundle.

## Limitations

- Source availability, rate limits, and schema changes may affect completeness.
- Cross-source differences may exist; check provenance.json and quality reports if present.
- License and attribution requirements apply (see compliance.json).
"""
