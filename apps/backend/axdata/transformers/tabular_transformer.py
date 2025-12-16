"""Tabular transformer - standard table format."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class TabularTransformer(BaseTransformer):
    """Transform data into tabular format (rows = observations, columns = variables)."""
    
    def __init__(self):
        super().__init__("tabular")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to tabular format.
        
        Rules:
        - Flatten nested structures
        - One row = one observation
        - No arrays in cells
        - Strong typing
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            # Fallback: flatten dicts manually
            return self._flatten_manual(raw_data)
        
        # Use pandas for efficient flattening
        df = pd.DataFrame(raw_data)
        
        # Flatten nested columns
        df = self._flatten_dataframe(df)
        
        # Remove arrays (convert to string or first element)
        df = self._remove_arrays(df)
        
        # Ensure strong typing
        df = self._enforce_types(df, ds_spec)
        
        return df.to_dict('records')
    
    def _flatten_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flatten nested columns."""
        # Flatten columns with nested dicts
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if it's a dict
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(sample, dict):
                    # Expand dict columns
                    expanded = pd.json_normalize(df[col])
                    expanded.columns = [f"{col}_{subcol}" for subcol in expanded.columns]
                    df = pd.concat([df.drop(columns=[col]), expanded], axis=1)
        
        return df
    
    def _remove_arrays(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove arrays from cells."""
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(
                    lambda x: str(x) if isinstance(x, (list, tuple)) else x
                )
        return df
    
    def _enforce_types(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> pd.DataFrame:
        """Enforce types from DS-SPEC."""
        variables = ds_spec.get("variables", [])
        var_types = {v["name"]: v["type"] for v in variables}
        
        for var_name, var_type in var_types.items():
            if var_name in df.columns:
                if var_type == "numeric":
                    df[var_name] = pd.to_numeric(df[var_name], errors='coerce')
                elif var_type == "categorical":
                    df[var_name] = df[var_name].astype(str)
        
        return df
    
    def _flatten_manual(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Manual flattening without pandas."""
        flattened = []
        for record in records:
            flat = {}
            for key, value in record.items():
                if isinstance(value, dict):
                    # Flatten nested dict
                    for subkey, subvalue in value.items():
                        flat[f"{key}_{subkey}"] = subvalue
                elif isinstance(value, (list, tuple)):
                    # Convert array to string
                    flat[key] = str(value)
                else:
                    flat[key] = value
            flattened.append(flat)
        return flattened
