"""Schema generator - automatic schema.json generation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from axdata.spec.ds_spec import DatasetSpec


TYPE_MAP = {
    "numeric": "number",
    "categorical": "string",
    "text": "string",
    "event": "object",
    "geo": "object",
}


def build_schema_from_spec(
    ds_spec: Dict[str, Any] | DatasetSpec,
    template: str,
    explicit_columns: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate schema.json from DS-SPEC.
    
    Args:
        ds_spec: Dataset specification
        template: Selected template
        explicit_columns: Optional explicit column definitions (if available from actual data)
    
    Returns:
        Schema dictionary
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    # If explicit columns provided, use them
    if explicit_columns:
        cols = explicit_columns
    else:
        # Generate expected schema from DS-SPEC
        dims = spec_dict.get("dimensions", {})
        cols = []
        
        # colonne dimensioni (standard)
        entity_kind = dims.get("entity", {}).get("kind", "none")
        if entity_kind != "none":
            cols.append({
                "name": "entity_id",
                "type": "string",
                "description": "Stable entity identifier"
            })
            cols.append({
                "name": "entity_kind",
                "type": "string",
                "description": f"Entity kind ({entity_kind})"
            })
        
        time_enabled = dims.get("time", {}).get("enabled", False)
        if time_enabled:
            cols.append({
                "name": "timestamp",
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp"
            })
            granularity = dims.get("time", {}).get("granularity", "none")
            if granularity and granularity != "none":
                cols.append({
                    "name": "granularity",
                    "type": "string",
                    "description": f"Declared granularity ({granularity})"
                })
        
        geo_enabled = dims.get("geo", {}).get("enabled", False)
        if geo_enabled:
            cols.append({
                "name": "geo_scope",
                "type": "string",
                "description": "Requested geo scope"
            })
            cols.append({
                "name": "geo_level",
                "type": "string",
                "description": "Geo level"
            })
            if template == "geospatial":
                cols.append({
                    "name": "geometry",
                    "type": "object",
                    "description": "GeoJSON geometry"
                })
                cols.append({
                    "name": "crs",
                    "type": "string",
                    "description": "Coordinate reference system"
                })
        
        # colonne variabili
        for v in spec_dict.get("variables", []):
            cols.append({
                "name": v.get("name"),
                "type": TYPE_MAP.get(v.get("type", "string"), "string"),
                "unit": v.get("unit"),
                "description": f"Variable: {v.get('name')}"
            })
    
    # Determine primary key
    dims = spec_dict.get("dimensions", {})
    time_enabled = dims.get("time", {}).get("enabled", False)
    entity_kind = dims.get("entity", {}).get("kind", "none")
    
    primary_key = None
    if time_enabled and entity_kind != "none":
        primary_key = ["entity_id", "timestamp"]
    elif entity_kind != "none":
        primary_key = ["entity_id"]
    
    return {
        "schema_version": "1.0",
        "template": template,
        "primary_key": primary_key,
        "columns": cols
    }
