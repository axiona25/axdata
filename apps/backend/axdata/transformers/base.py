"""Base transformer for all template types."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class BaseTransformer(ABC):
    """
    Base class for template transformers.
    
    Each transformer converts raw data into a specific template format.
    """
    
    template_name: str
    
    def __init__(self, template_name: str):
        """
        Initialize transformer.
        
        Args:
            template_name: Name of the template (e.g., "tabular", "time_series")
        """
        self.template_name = template_name
    
    @abstractmethod
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform raw data into template format.
        
        Args:
            raw_data: List of raw data records from sources
            ds_spec: Dataset specification
            metadata: Optional metadata from sources
        
        Returns:
            Transformed records in template format
        """
        pass
    
    def validate_output(
        self,
        records: List[Dict[str, Any]],
        ds_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate transformed output.
        
        Args:
            records: Transformed records
            ds_spec: Dataset specification
        
        Returns:
            Validation report
        """
        return {
            "valid": True,
            "record_count": len(records),
            "warnings": []
        }
