"""Time series transformer - temporal data format."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class TimeSeriesTransformer(BaseTransformer):
    """Transform data into time series format."""
    
    def __init__(self):
        super().__init__("time_series")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to time series format.
        
        Rules:
        - Identify timestamp column
        - Sort temporally
        - Handle gaps
        - ISO 8601 format
        - Declared frequency
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            return self._transform_manual(raw_data, ds_spec)
        
        df = pd.DataFrame(raw_data)
        
        # Identify timestamp column
        timestamp_col = self._find_timestamp_column(df, ds_spec)
        if timestamp_col is None:
            # Try to create from date columns
            timestamp_col = self._create_timestamp_column(df, ds_spec)
        
        if timestamp_col is None:
            # Fallback: use index as time
            df['timestamp'] = pd.date_range(start='2000-01-01', periods=len(df), freq='D')
            timestamp_col = 'timestamp'
        
        # Convert to datetime
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        
        # Sort by timestamp
        df = df.sort_values(timestamp_col)
        
        # Add granularity
        granularity = ds_spec.get("dimensions", {}).get("time", {}).get("granularity", "none")
        if granularity != "none":
            df['granularity'] = granularity
        
        # Format timestamp as ISO 8601
        df[timestamp_col] = df[timestamp_col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Handle gaps (optional - could add missing timestamps)
        # For now, we just sort and format
        
        return df.to_dict('records')
    
    def _find_timestamp_column(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> Optional[str]:
        """Find timestamp column in dataframe."""
        # Common timestamp column names
        timestamp_names = ['timestamp', 'date', 'time', 'datetime', 'period', 'year', 'month']
        
        for col in df.columns:
            if col.lower() in timestamp_names:
                return col
        
        # Check if any column looks like dates
        for col in df.columns:
            if df[col].dtype == 'object':
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample and isinstance(sample, str):
                    try:
                        pd.to_datetime(sample)
                        return col
                    except:
                        pass
        
        return None
    
    def _create_timestamp_column(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> Optional[str]:
        """Create timestamp from date components."""
        # Try to find year, month, day columns
        year_col = None
        month_col = None
        day_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'year' in col_lower:
                year_col = col
            elif 'month' in col_lower:
                month_col = col
            elif 'day' in col_lower:
                day_col = col
        
        if year_col:
            # Create timestamp
            try:
                if month_col and day_col:
                    df['timestamp'] = pd.to_datetime(
                        df[[year_col, month_col, day_col]].astype(str).agg('-'.join, axis=1),
                        errors='coerce'
                    )
                elif month_col:
                    df['timestamp'] = pd.to_datetime(
                        df[[year_col, month_col]].astype(str).agg('-'.join, axis=1) + '-01',
                        errors='coerce'
                    )
                else:
                    df['timestamp'] = pd.to_datetime(df[year_col].astype(str) + '-01-01', errors='coerce')
                return 'timestamp'
            except:
                pass
        
        return None
    
    def _transform_manual(self, records: List[Dict[str, Any]], ds_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manual transformation without pandas."""
        # Find timestamp column
        timestamp_col = None
        for record in records:
            for key in record.keys():
                if key.lower() in ['timestamp', 'date', 'time', 'datetime']:
                    timestamp_col = key
                    break
            if timestamp_col:
                break
        
        # Sort by timestamp
        if timestamp_col:
            try:
                records = sorted(records, key=lambda x: x.get(timestamp_col, ''))
            except:
                pass
        
        # Add granularity
        granularity = ds_spec.get("dimensions", {}).get("time", {}).get("granularity", "none")
        if granularity != "none":
            for record in records:
                record['granularity'] = granularity
        
        return records
