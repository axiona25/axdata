"""Template decision engine - auto-selects one of 8 templates based on DS-SPEC."""
from __future__ import annotations
from typing import Dict, Any
from axdata.spec.ds_spec import TemplateType, DatasetSpec


TEMPLATES = {
    "tabular", "time_series", "cross_sectional", "panel",
    "geospatial", "text", "event", "hybrid", "auto"
}


def decide_template(ds_spec: Dict[str, Any] | DatasetSpec) -> str:
    """
    Decide which template to use based on DS-SPEC.
    
    Args:
        ds_spec: Dataset specification (dict or DatasetSpec)
    
    Returns:
        Template name (one of the 8 templates)
    """
    # Convert to dict if needed
    if isinstance(ds_spec, DatasetSpec):
        spec_dict = ds_spec.model_dump()
    else:
        spec_dict = ds_spec
    
    out = spec_dict.get("output", {})
    forced = out.get("template", "auto")
    
    if forced != "auto":
        if forced not in TEMPLATES:
            raise ValueError(f"Unknown template: {forced}")
        return forced
    
    dims = spec_dict["dimensions"]
    time_enabled = dims["time"]["enabled"]
    geo_enabled = dims["geo"]["enabled"]
    geo_level = dims["geo"].get("level", "none")
    entity_kind = dims["entity"]["kind"]
    entity_tracking = dims["entity"].get("tracking", False)
    
    # Se la richiesta è chiaramente documentale/eventi:
    var_types = {v["type"] for v in spec_dict.get("variables", [])}
    if "text" in var_types or entity_kind == "document":
        return "text"
    if "event" in var_types:
        return "event"
    if geo_enabled and geo_level in {"point", "polygon"}:
        return "geospatial"
    
    # Temporale:
    if time_enabled and entity_tracking:
        return "panel"
    if time_enabled and not entity_tracking:
        return "time_series"
    
    # Snapshot:
    if not time_enabled and geo_enabled:
        return "cross_sectional"
    
    return "tabular"
