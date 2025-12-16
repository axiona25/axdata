"""Transformer registry - get transformer by template name."""
from typing import Dict, Optional
from axdata.transformers.base import BaseTransformer
from axdata.transformers.tabular_transformer import TabularTransformer
from axdata.transformers.time_series_transformer import TimeSeriesTransformer
from axdata.transformers.panel_transformer import PanelTransformer
from axdata.transformers.cross_sectional_transformer import CrossSectionalTransformer
from axdata.transformers.geospatial_transformer import GeospatialTransformer
from axdata.transformers.text_transformer import TextTransformer
from axdata.transformers.event_transformer import EventTransformer
from axdata.transformers.hybrid_transformer import HybridTransformer


_registry: Dict[str, BaseTransformer] = {}


def _init_registry():
    """Initialize transformer registry."""
    global _registry
    _registry = {
        "tabular": TabularTransformer(),
        "time_series": TimeSeriesTransformer(),
        "panel": PanelTransformer(),
        "cross_sectional": CrossSectionalTransformer(),
        "geospatial": GeospatialTransformer(),
        "text": TextTransformer(),
        "event": EventTransformer(),
        "hybrid": HybridTransformer()
    }


def get_transformer(template_name: str) -> Optional[BaseTransformer]:
    """
    Get transformer by template name.
    
    Args:
        template_name: Template name (e.g., "tabular", "time_series")
    
    Returns:
        Transformer instance or None if not found
    """
    if not _registry:
        _init_registry()
    
    return _registry.get(template_name)


def list_transformers() -> list[str]:
    """
    List all available transformer names.
    
    Returns:
        List of transformer names
    """
    if not _registry:
        _init_registry()
    
    return list(_registry.keys())
