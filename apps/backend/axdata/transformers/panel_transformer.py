"""Panel/Longitudinal transformer - same entities over time."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class PanelTransformer(BaseTransformer):
    """Transform data into panel/longitudinal format (entity tracking)."""
    
    def __init__(self):
        super().__init__("panel")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to panel format.
        
        Rules:
        - Identify entity_id
        - Identify timestamp
        - Track same entities over time
        - Build entity_id + time composite key
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            return self._transform_manual(raw_data, ds_spec)
        
        df = pd.DataFrame(raw_data)
        
        # Identify entity column
        entity_col = self._find_entity_column(df, ds_spec)
        if entity_col is None:
            # Create entity_id from index or first categorical column
            entity_col = self._create_entity_column(df, ds_spec)
        
        # Identify timestamp (reuse time series logic)
        from axdata.transformers.time_series_transformer import TimeSeriesTransformer
        ts_transformer = TimeSeriesTransformer()
        timestamp_col = ts_transformer._find_timestamp_column(df, ds_spec)
        if timestamp_col is None:
            timestamp_col = ts_transformer._create_timestamp_column(df, ds_spec)
        
        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
            df = df.sort_values([entity_col, timestamp_col])
            df[timestamp_col] = df[timestamp_col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Ensure entity_id column exists
        if entity_col != 'entity_id':
            df['entity_id'] = df[entity_col]
        
        # Add entity_kind
        entity_kind = ds_spec.get("dimensions", {}).get("entity", {}).get("kind", "none")
        if entity_kind != "none":
            df['entity_kind'] = entity_kind
        
        return df.to_dict('records')
    
    def _find_entity_column(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> Optional[str]:
        """Find entity identifier column."""
        entity_names = ['entity_id', 'id', 'subject_id', 'patient_id', 'country_code', 'country', 'region']
        
        for col in df.columns:
            if col.lower() in entity_names:
                return col
        
        return None
    
    def _create_entity_column(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> str:
        """Create entity_id from available columns."""
        # Try to use first categorical or string column
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                return col
        
        # Fallback: create from index
        df['entity_id'] = df.index.astype(str)
        return 'entity_id'
    
    def _transform_manual(self, records: List[Dict[str, Any]], ds_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manual transformation without pandas."""
        # Find entity column
        entity_col = None
        for record in records:
            for key in record.keys():
                if key.lower() in ['entity_id', 'id', 'country', 'subject_id']:
                    entity_col = key
                    break
            if entity_col:
                break
        
        # Add entity_id if missing
        if entity_col and entity_col != 'entity_id':
            for record in records:
                record['entity_id'] = record.get(entity_col)
        
        # Add entity_kind
        entity_kind = ds_spec.get("dimensions", {}).get("entity", {}).get("kind", "none")
        if entity_kind != "none":
            for record in records:
                record['entity_kind'] = entity_kind
        
        return records
