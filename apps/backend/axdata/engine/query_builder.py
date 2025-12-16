"""Intelligent query builder from DS-SPEC to connector-specific queries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# Mapping variables to API indicators/dataset codes by source
VARIABLE_TO_INDICATOR: Dict[str, Dict[str, str]] = {
    "eurostat": {
        "gdp": "nama_10_gdp",
        "gdp_per_capita": "tec00001",
        "inflation": "prc_hicp_aind",
        "unemployment": "une_rt_m",
        "population": "demo_gind",
        "trade": "ext_st_27_main",
        "health_expenditure": "hlth_sha11_hc",
    },
    "worldbank": {
        "gdp": "NY.GDP.MKTP.CD",
        "gdp_per_capita": "NY.GDP.PCAP.CD",
        "inflation": "FP.CPI.TOTL.ZG",
        "unemployment": "SL.UEM.TOTL.ZS",
        "population": "SP.POP.TOTL",
        "life_expectancy": "SP.DYN.LE00.IN",
        "fertility": "SP.DYN.TFRT.IN",
    },
    "who_gho": {
        "life_expectancy": "WHOSIS_000001",
        "mortality": "WHOSIS_000002",
        "health_expenditure": "WHS6_102",
        "immunization": "WHS3_544",
    },
    "oecd": {
        "gdp": "GDP",
        "inflation": "CPI",
        "unemployment": "LRUNTTTT",
        "trade": "XT",
    },
    "imf": {
        "gdp": "NGDP_RPCH",
        "inflation": "PCPI_PCH",
        "unemployment": "LUR",
    },
}


def extract_dataset_code_from_variables(
    variables: List[Dict[str, Any]],
    source_id: str
) -> Optional[str]:
    """
    Extract dataset_code/indicator from DS-SPEC variables.
    
    Args:
        variables: List of variable specs from DS-SPEC
        source_id: Source identifier
    
    Returns:
        Dataset code/indicator or None
    """
    if not variables:
        return None
    
    # Get mapping for this source
    source_mapping = VARIABLE_TO_INDICATOR.get(source_id, {})
    if not source_mapping:
        return None
    
    # Try to match variable names to indicators
    for var in variables:
        var_name = var.get("name", "").lower()
        
        # Direct match
        if var_name in source_mapping:
            return source_mapping[var_name]
        
        # Partial match (e.g., "gdp_per_capita" contains "gdp")
        for key, indicator in source_mapping.items():
            if key in var_name or var_name in key:
                logger.info(f"Matched variable '{var_name}' to indicator '{indicator}' for {source_id}")
                return indicator
    
    return None


def build_query_from_ds_spec(
    ds_spec: Dict[str, Any],
    source_id: str,
    source_manifest: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build connector-specific query from DS-SPEC.
    
    Args:
        ds_spec: Dataset specification
        source_id: Source identifier
        source_manifest: Optional source manifest for endpoint info
    
    Returns:
        Query dictionary for connector
    """
    # Start with base query
    query: Dict[str, Any] = {
        "filters": {}
    }
    
    # Extract dataset_code from variables
    variables = ds_spec.get("variables", [])
    dataset_code = extract_dataset_code_from_variables(variables, source_id)
    
    if dataset_code:
        query["dataset_code"] = dataset_code
    else:
        # Fallback: try to infer from first variable name
        if variables:
            first_var = variables[0].get("name", "").lower()
            # Generic fallback
            query["dataset_code"] = first_var.replace("_", "-") if first_var else "default"
            logger.warning(f"Could not map variables to indicator for {source_id}, using fallback: {query['dataset_code']}")
        else:
            query["dataset_code"] = "default"
    
    # Extract dimensions
    dims = ds_spec.get("dimensions", {})
    
    # Time filters
    time_dim = dims.get("time", {})
    if time_dim.get("enabled", False):
        if time_dim.get("start"):
            query["filters"]["startTime"] = time_dim["start"]
        if time_dim.get("end"):
            query["filters"]["endTime"] = time_dim["end"]
        if time_dim.get("granularity") and time_dim.get("granularity") != "none":
            query["filters"]["timeGranularity"] = time_dim["granularity"]
    
    # Geo filters
    geo_dim = dims.get("geo", {})
    if geo_dim.get("enabled", False):
        if geo_dim.get("scope"):
            # Parse scope (e.g., "EU", "IT,DE,FR", "global")
            scope = geo_dim["scope"]
            if "," in scope:
                # Multiple countries
                query["filters"]["geo"] = [c.strip() for c in scope.split(",")]
            else:
                query["filters"]["geo"] = scope
        
        if geo_dim.get("level") and geo_dim.get("level") != "none":
            query["filters"]["geoLevel"] = geo_dim["level"]
    
    # Entity filters (if applicable)
    entity_dim = dims.get("entity", {})
    if entity_dim.get("kind") and entity_dim.get("kind") != "none":
        query["filters"]["entityKind"] = entity_dim["kind"]
    
    # Source-specific query adjustments
    if source_id == "eurostat":
        # Eurostat-specific: ensure dataset_code is set
        if "dataset_code" not in query or query["dataset_code"] == "default":
            # Try to use first variable as dataset code
            if variables:
                query["dataset_code"] = variables[0].get("name", "default").upper()
    
    elif source_id == "worldbank":
        # World Bank uses "indicator" instead of "dataset_code"
        if "dataset_code" in query:
            query["indicator"] = query.pop("dataset_code")
    
    elif source_id in ["who_gho", "oecd", "imf"]:
        # Similar structure
        pass
    
    return query


def build_queries_for_sources(
    ds_spec: Dict[str, Any],
    selected_sources: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Build queries for all selected sources.
    
    Args:
        ds_spec: Dataset specification
        selected_sources: List of selected source manifests
    
    Returns:
        Dictionary mapping source_id to query
    """
    queries = {}
    
    for source in selected_sources:
        source_id = source.get("source_id", "unknown")
        query = build_query_from_ds_spec(ds_spec, source_id, source)
        queries[source_id] = query
    
    return queries
