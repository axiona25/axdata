"""Sector to Domain mapper for AXDATA pipeline."""
from __future__ import annotations
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# Mapping from sector (DS-SPEC) to domain (Normalizer)
SECTOR_TO_DOMAIN: Dict[str, str] = {
    "health": "biomedical",
    "economy": "economics",
    "economics": "economics",
    "physics": "physics",
    "math": "math",
    "mathematics": "math",
    "society": "demography",
    "demography": "demography",
    "demographics": "demography",
    "biomedical": "biomedical",
    "biomedicine": "biomedical",
    "science": "physics",  # Default science to physics
    "social": "demography",  # Default social to demography
}

# Reverse mapping from domain to sector
DOMAIN_TO_SECTOR: Dict[str, str] = {
    "biomedical": "health",
    "economics": "economy",
    "physics": "physics",
    "math": "math",
    "demography": "society",
}

# Fallback domain if sector not found
DEFAULT_DOMAIN = "economics"  # Most common domain


def sector_to_domain(sector: str) -> str:
    """
    Map sector (from DS-SPEC) to domain (for Normalizer).
    
    Args:
        sector: Sector name from DS-SPEC
    
    Returns:
        Domain name for normalizer
    """
    if not sector:
        return DEFAULT_DOMAIN
    
    sector_lower = sector.lower().strip()
    
    # Direct mapping
    if sector_lower in SECTOR_TO_DOMAIN:
        return SECTOR_TO_DOMAIN[sector_lower]
    
    # Partial matching (e.g., "health_care" -> "health")
    for key, domain in SECTOR_TO_DOMAIN.items():
        if key in sector_lower or sector_lower in key:
            return domain
    
    # Fallback
    logger.warning(f"Unknown sector '{sector}', using default domain '{DEFAULT_DOMAIN}'")
    return DEFAULT_DOMAIN


def domain_to_sector(domain: str) -> str:
    """
    Map domain (from Normalizer) to sector (for DS-SPEC).
    
    Args:
        domain: Domain name from normalizer
    
    Returns:
        Sector name for DS-SPEC
    """
    if not domain:
        return "economy"  # Default sector
    
    domain_lower = domain.lower().strip()
    
    if domain_lower in DOMAIN_TO_SECTOR:
        return DOMAIN_TO_SECTOR[domain_lower]
    
    # Fallback
    return domain_lower  # Use domain as sector if not found


def get_available_domains() -> list[str]:
    """Get list of available normalizer domains."""
    return list(DOMAIN_TO_SECTOR.keys())


def get_available_sectors() -> list[str]:
    """Get list of available sectors."""
    return list(set(SECTOR_TO_DOMAIN.values()))
