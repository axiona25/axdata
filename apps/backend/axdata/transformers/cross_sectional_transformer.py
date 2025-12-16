"""Cross-sectional transformer - snapshot at single point in time."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class CrossSectionalTransformer(BaseTransformer):
    """Transform data into cross-sectional format (single time point)."""
    
    def __init__(self):
        super().__init__("cross_sectional")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to cross-sectional format.
        
        Rules:
        - Filter to single time point (if time dimension exists)
        - Collapse time dimension
        - One row per entity
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            return self._transform_manual(raw_data, ds_spec)
        
        df = pd.DataFrame(raw_data)
        
        # If time dimension exists, filter to latest or specified time
        time_dim = ds_spec.get("dimensions", {}).get("time", {})
        if time_dim.get("enabled", False):
            # Find timestamp column
            from axdata.transformers.time_series_transformer import TimeSeriesTransformer
            ts_transformer = TimeSeriesTransformer()
            timestamp_col = ts_transformer._find_timestamp_column(df, ds_spec)
            
            if timestamp_col:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
                # Filter to latest timestamp
                latest_time = df[timestamp_col].max()
                df = df[df[timestamp_col] == latest_time]
                # Remove timestamp column (collapsing time dimension)
                df = df.drop(columns=[timestamp_col])
        
        # Ensure entity_id exists
        entity_col = self._find_entity_column(df, ds_spec)
        if entity_col and entity_col != 'entity_id':
            df['entity_id'] = df[entity_col]
        
        return df.to_dict('records')
    
    def _find_entity_column(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> Optional[str]:
        """Find entity identifier column."""
        entity_names = ['entity_id', 'id', 'country_code', 'country', 'region', 'subject_id']
        
        for col in df.columns:
            if col.lower() in entity_names:
                return col
        
        return None
    
    def _transform_manual(self, records: List[Dict[str, Any]], ds_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manual transformation without pandas."""
        # Filter to latest time if time dimension exists
        time_dim = ds_spec.get("dimensions", {}).get("time", {})
        if time_dim.get("enabled", False):
            # Find latest timestamp
            latest_time = None
            for record in records:
                for key, value in record.items():
                    if key.lower() in ['timestamp', 'date', 'time']:
                        if latest_time is None or value > latest_time:
                            latest_time = value
                        break
            
            # Filter to latest time
            if latest_time:
                records = [
                    r for r in records
                    if any(
                        (k.lower() in ['timestamp', 'date', 'time'] and v == latest_time)
                        for k, v in r.items()
                    )
                ]
        
        return records
