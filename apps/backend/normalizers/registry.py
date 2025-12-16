"""Normalizer registry - FAIR-compliant, following global standards."""
from typing import Dict, Optional, Type
from normalizers.base import BaseNormalizer
from normalizers.economics import EconomicsNormalizer
from normalizers.biomedical import BiomedicalNormalizer
from normalizers.physics import PhysicsNormalizer
from normalizers.ml_math import MLMathNormalizer
from normalizers.demography import DemographyNormalizer

# Registry of normalizers (FAIR-compliant, following global standards)
_registry: Dict[str, Type[BaseNormalizer]] = {
    "economics": EconomicsNormalizer,      # SDMX standard
    "biomedical": BiomedicalNormalizer,    # CDISC/HL7 FHIR/OMOP
    "physics": PhysicsNormalizer,          # FAIR/NetCDF
    "math": MLMathNormalizer,              # OpenML/UCI
    "demography": DemographyNormalizer,    # UN SDG/Eurostat
}

# Cache of instances
_instances: Dict[str, BaseNormalizer] = {}


def register_normalizer(domain: str, normalizer_class: Type[BaseNormalizer]):
    """
    Register a normalizer for a domain.
    
    Args:
        domain: Domain name
        normalizer_class: Normalizer class
    """
    _registry[domain.lower()] = normalizer_class
    # Clear instance cache for this domain
    if domain.lower() in _instances:
        del _instances[domain.lower()]


def get_normalizer(domain: str) -> Optional[BaseNormalizer]:
    """
    Get normalizer for a domain.
    
    Args:
        domain: Domain name (e.g., "economics", "biomedical", "physics", "math", "demography")
    
    Returns:
        Normalizer instance or None
    """
    domain_lower = domain.lower()
    
    # Check cache first
    if domain_lower in _instances:
        return _instances[domain_lower]
    
    # Get from registry and create instance
    normalizer_class = _registry.get(domain_lower)
    if normalizer_class:
        instance = normalizer_class()
        _instances[domain_lower] = instance
        return instance
    
    return None


def list_normalizers() -> list[str]:
    """List all registered normalizer domains."""
    return list(_registry.keys())


def get_normalizer_metadata(domain: str) -> Optional[Dict]:
    """
    Get metadata about a normalizer (standards, structure, etc.).
    
    Args:
        domain: Domain name
    
    Returns:
        Metadata dictionary or None
    """
    normalizer = get_normalizer(domain)
    if normalizer and hasattr(normalizer, 'get_metadata'):
        return normalizer.get_metadata()
    return None
