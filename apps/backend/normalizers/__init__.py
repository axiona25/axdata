"""Normalizer modules for data transformation - FAIR-compliant, following global standards."""
from normalizers.registry import (
    register_normalizer,
    get_normalizer,
    list_normalizers,
    get_normalizer_metadata
)
from normalizers.economics import EconomicsNormalizer
from normalizers.biomedical import BiomedicalNormalizer
from normalizers.physics import PhysicsNormalizer
from normalizers.ml_math import MLMathNormalizer
from normalizers.demography import DemographyNormalizer

# Auto-register all normalizers
register_normalizer("economics", EconomicsNormalizer)
register_normalizer("biomedical", BiomedicalNormalizer)
register_normalizer("physics", PhysicsNormalizer)
register_normalizer("math", MLMathNormalizer)
register_normalizer("demography", DemographyNormalizer)

__all__ = [
    "register_normalizer",
    "get_normalizer",
    "list_normalizers",
    "get_normalizer_metadata",
    "EconomicsNormalizer",
    "BiomedicalNormalizer",
    "PhysicsNormalizer",
    "MLMathNormalizer",
    "DemographyNormalizer"
]
