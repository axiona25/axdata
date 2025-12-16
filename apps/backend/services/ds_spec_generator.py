"""Helper to generate DS-SPEC from natural language queries."""
from __future__ import annotations
from typing import Dict, Any, Optional
import re
from axdata.spec.ds_spec import DatasetSpec, RequestSpec, DimensionsSpec, TimeDimension, GeoDimension, EntityDimension, VariableSpec, OutputSpec


def extract_time_info(query: str) -> Dict[str, Any]:
    """
    Extract time dimension information from natural language query.
    
    Args:
        query: Natural language query
    
    Returns:
        Dictionary with time dimension info
    """
    query_lower = query.lower()
    
    # Extract years
    years = re.findall(r'\b(19|20)\d{2}\b', query)
    time_start = years[0] if years else None
    time_end = years[-1] if len(years) > 1 else years[0] if years else None
    
    # Detect granularity
    granularity = "year"
    if any(x in query_lower for x in ["daily", "giornaliero", "day"]):
        granularity = "day"
    elif any(x in query_lower for x in ["weekly", "settimanale", "week"]):
        granularity = "week"
    elif any(x in query_lower for x in ["monthly", "mensile", "month"]):
        granularity = "month"
    elif any(x in query_lower for x in ["quarterly", "trimestrale", "quarter"]):
        granularity = "quarter"
    
    # Check for time-related keywords
    time_keywords = [
        "temporal", "time", "period", "anno", "year", "storico", "historical",
        "trend", "evoluzione", "andamento", "serie temporale"
    ]
    time_enabled = any(kw in query_lower for kw in time_keywords) or bool(years)
    
    return {
        "enabled": time_enabled,
        "start": time_start,
        "end": time_end,
        "granularity": granularity
    }


def extract_geo_info(query: str) -> Dict[str, Any]:
    """
    Extract geographic dimension information from natural language query.
    
    Args:
        query: Natural language query
    
    Returns:
        Dictionary with geo dimension info
    """
    query_lower = query.lower()
    
    geo_keywords = {
        "global": ["global", "mondiale", "world", "internazionale"],
        "EU": ["europa", "european", "ue", "eu", "eurostat"],
        "IT": ["italia", "italian", "istat", "italy"],
        "US": ["usa", "united states", "america", "statunitense"]
    }
    
    geo_enabled = False
    geo_scope = None
    geo_level = "country"
    
    # Detect scope
    for scope, keywords in geo_keywords.items():
        if any(kw in query_lower for kw in keywords):
            geo_enabled = True
            geo_scope = scope
            break
    
    # Detect level
    if any(x in query_lower for x in ["region", "regione", "regional"]):
        geo_level = "region"
    elif any(x in query_lower for x in ["province", "provincia", "provincial"]):
        geo_level = "province"
    elif any(x in query_lower for x in ["city", "città", "urban", "comune"]):
        geo_level = "city"
    elif any(x in query_lower for x in ["coordinate", "lat", "long", "point"]):
        geo_level = "point"
    elif any(x in query_lower for x in ["area", "polygon", "zona"]):
        geo_level = "polygon"
    
    return {
        "enabled": geo_enabled,
        "scope": geo_scope,
        "level": geo_level
    }


def extract_entity_info(query: str, sector: str) -> Dict[str, Any]:
    """
    Extract entity dimension information from natural language query.
    
    Args:
        query: Natural language query
        sector: Dataset sector
    
    Returns:
        Dictionary with entity dimension info
    """
    query_lower = query.lower()
    
    entity_kind = "none"
    tracking = False
    
    # Detect entity kind from keywords
    if any(x in query_lower for x in ["paese", "country", "nazione"]):
        entity_kind = "country"
    elif any(x in query_lower for x in ["persona", "person", "individuo", "patient"]):
        entity_kind = "person"
    elif any(x in query_lower for x in ["organizzazione", "organization", "azienda", "company"]):
        entity_kind = "organization"
    elif any(x in query_lower for x in ["studio", "study", "trial", "sperimentale"]):
        entity_kind = "study"
    elif any(x in query_lower for x in ["documento", "document", "pubblicazione", "publication"]):
        entity_kind = "document"
    
    # Detect tracking (panel/longitudinal)
    tracking_keywords = [
        "panel", "longitudinal", "stesso", "same", "tracking", "seguire",
        "nel tempo", "over time", "longitudinale"
    ]
    tracking = any(kw in query_lower for kw in tracking_keywords)
    
    return {
        "kind": entity_kind,
        "tracking": tracking
    }


def extract_variables(query: str, sector: str) -> list[Dict[str, Any]]:
    """
    Extract variables from natural language query.
    
    Args:
        query: Natural language query
        sector: Dataset sector
    
    Returns:
        List of variable specifications
    """
    variables = []
    query_lower = query.lower()
    
    # Common variable patterns
    var_patterns = {
        "numeric": [
            r"(incidenza|incidence|rate|tasso|percentuale|percentage|growth|crescita)",
            r"(gdp|pil|reddito|income|prodotto)",
            r"(temperatura|temperature|temp)",
            r"(popolazione|population|pop)",
            r"(prezzo|price|prezzo)"
        ],
        "categorical": [
            r"(categoria|category|tipo|type|class|classe)",
            r"(stato|status|stato|condition)"
        ],
        "text": [
            r"(testo|text|documento|document|abstract|riassunto)",
            r"(pubblicazione|publication|paper|articolo)"
        ],
        "event": [
            r"(evento|event|incidente|incident|outbreak)",
            r"(notifica|notification|alert)"
        ]
    }
    
    # Try to extract variable names
    for var_type, patterns in var_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            if matches:
                var_name = matches[0] if isinstance(matches[0], str) else matches[0][0] if matches[0] else "value"
                variables.append({
                    "name": var_name,
                    "type": var_type,
                    "unit": None,
                    "preferred_sources": []
                })
                break
    
    # Default if nothing found
    if not variables:
        variables = [{
            "name": "value",
            "type": "numeric",
            "unit": None,
            "preferred_sources": []
        }]
    
    return variables


def generate_ds_spec_from_query(
    query: str,
    sector: str,
    language: str = "it",
    user_role: str = "general"
) -> DatasetSpec:
    """
    Generate DS-SPEC from natural language query.
    
    This is useful for the wizard modal - user enters query, system generates DS-SPEC.
    
    Args:
        query: Natural language query
        sector: Dataset sector (e.g., "health", "economy")
        language: Query language
        user_role: User role
    
    Returns:
        DatasetSpec
    """
    # Extract dimensions
    time_info = extract_time_info(query)
    geo_info = extract_geo_info(query)
    entity_info = extract_entity_info(query, sector)
    variables = extract_variables(query, sector)
    
    # Build DS-SPEC
    ds_spec = DatasetSpec(
        version="1.0",
        request=RequestSpec(
            query_text=query,
            language=language,
            user_role=user_role
        ),
        sector=sector,
        subsector=None,
        dimensions=DimensionsSpec(
            time=TimeDimension(**time_info),
            geo=GeoDimension(
                enabled=geo_info["enabled"],
                scope=geo_info["scope"],
                level=geo_info["level"],
                crs="EPSG:4326"
            ),
            entity=EntityDimension(
                kind=entity_info["kind"],
                tracking=entity_info["tracking"],
                id_strategy="mapped"
            )
        ),
        variables=[VariableSpec(**v) for v in variables],
        output=OutputSpec(
            template="auto",
            formats=["csv"],
            quality={"min_completeness": 0.85, "deduplicate": True},
            compliance={"allow_pii": False, "license_policy": "normal"}
        )
    )
    
    return ds_spec
