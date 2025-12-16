"""Event-based transformer - discrete events format."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class EventTransformer(BaseTransformer):
    """Transform data into event-based format."""
    
    def __init__(self):
        super().__init__("event")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to event format.
        
        Rules:
        - Event detection
        - Unique timestamp per event
        - Event typing
        - Location (if available)
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            return self._transform_manual(raw_data, ds_spec)
        
        df = pd.DataFrame(raw_data)
        
        # Ensure event_id exists
        if 'event_id' not in df.columns:
            df['event_id'] = df.index.astype(str)
        
        # Identify event_type
        event_type_col = self._find_event_type_column(df)
        if event_type_col and event_type_col != 'event_type':
            df['event_type'] = df[event_type_col]
        elif 'event_type' not in df.columns:
            df['event_type'] = 'event'  # Default
        
        # Identify timestamp
        from axdata.transformers.time_series_transformer import TimeSeriesTransformer
        ts_transformer = TimeSeriesTransformer()
        timestamp_col = ts_transformer._find_timestamp_column(df, ds_spec)
        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
            df = df.sort_values(timestamp_col)
            df[timestamp_col] = df[timestamp_col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Create timestamp from index
            df['timestamp'] = pd.date_range(start='2000-01-01', periods=len(df), freq='H')
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            timestamp_col = 'timestamp'
        
        # Extract location if available
        location = self._extract_location(df)
        if location:
            df['location'] = location
        
        # Build event record
        event_cols = ['event_id', 'event_type', timestamp_col]
        if 'location' in df.columns:
            event_cols.append('location')
        
        # Add all other columns as attributes
        df['attributes'] = df.drop(columns=event_cols).to_dict('records')
        
        return df[event_cols + ['attributes']].to_dict('records')
    
    def _find_event_type_column(self, df) -> Optional[str]:
        """Find event type column."""
        event_type_names = ['event_type', 'type', 'category', 'kind', 'classification']
        
        for col in df.columns:
            if col.lower() in event_type_names:
                return col
        
        return None
    
    def _extract_location(self, df) -> Optional[List[str]]:
        """Extract location information."""
        location_cols = ['location', 'place', 'country', 'region', 'city', 'address']
        
        for col in df.columns:
            if col.lower() in location_cols:
                return df[col].tolist()
        
        return None
    
    def _transform_manual(self, records: List[Dict[str, Any]], ds_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manual transformation without pandas."""
        transformed = []
        
        for idx, record in enumerate(records):
            event = {
                "event_id": record.get("id") or record.get("event_id") or f"event_{idx}",
                "event_type": record.get("event_type") or record.get("type") or "event",
                "timestamp": record.get("timestamp") or record.get("date") or record.get("time"),
                "location": record.get("location") or record.get("country") or record.get("place"),
                "attributes": {k: v for k, v in record.items() 
                             if k not in ['id', 'event_id', 'event_type', 'type', 'timestamp', 'date', 'time', 'location', 'country', 'place']}
            }
            transformed.append(event)
        
        return transformed
