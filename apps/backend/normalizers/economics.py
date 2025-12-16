"""Economics normalizer following SDMX standard (Statistical Data and Metadata eXchange).

SDMX is the #1 global standard for economic and statistical data, used by:
- World Bank
- IMF
- OECD
- Eurostat
- UN Data
- Central Banks

Key concept: Dataset = multidimensional time series
"""
from typing import List, Dict, Any
from datetime import datetime
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from normalizers.base import BaseNormalizer


class EconomicsNormalizer(BaseNormalizer):
    """
    Normalizer for economics/time series data following SDMX standard.
    
    SDMX Structure:
    - Dimensions: time, geo, indicator
    - Measures: value (numeric)
    - Attributes: unit, frequency, source, notes
    """
    
    def __init__(self):
        super().__init__("economics")
    
    def normalize(
        self,
        raw_assets: List[Dict[str, Any]],
        dataset_plan: Dict[str, Any]
    ) -> Any:
        """
        Trasforma dati grezzi in dataset SDMX-compliant.
        
        Args:
            raw_assets: Lista di asset grezzi dal Collector
            dataset_plan: DatasetPlan con transformations
        
        Returns:
            DataFrame normalizzato (SDMX structure)
        """
        if not raw_assets:
            if PANDAS_AVAILABLE:
                return pd.DataFrame()
            return []
        
        if not PANDAS_AVAILABLE:
            # Fallback: return records as-is
            all_records = []
            for asset in raw_assets:
                data = asset.get("data", [])
                if isinstance(data, list):
                    all_records.extend(data)
                elif isinstance(data, dict):
                    all_records.append(data)
            return all_records
        
        # Convert raw assets to DataFrames
        frames = []
        for asset in raw_assets:
            data = asset.get("data", [])
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                continue
            frames.append(df)
        
        if not frames:
            return pd.DataFrame()
        
        # Concatenate all frames
        df = pd.concat(frames, ignore_index=True)
        
        # Apply transformations from dataset_plan
        transformations = dataset_plan.get("transformations", [])
        for transformation in transformations:
            trans_type = transformation.get("type")
            params = transformation.get("params", {})
            
            if trans_type == "normalize_dates":
                df = self._normalize_dates(df)
            elif trans_type == "normalize_geo":
                df = self._normalize_geographic(df)
            elif trans_type == "standardize_indicators":
                df = self._standardize_indicators(df)
            elif trans_type == "join":
                df = self._join_time_series(df, params)
            elif trans_type == "handle_missing":
                df = self._handle_missing_values(df, params)
            elif trans_type == "standardize_columns":
                df = self._standardize_columns(df, params)
            elif trans_type == "sdmx_structure":
                df = self._apply_sdmx_structure(df, params)
        
        # Ensure SDMX dimensions are present
        df = self._ensure_sdmx_dimensions(df)
        
        return df
    
    def build_data_dictionary(
        self,
        dataframe: Any
    ) -> List[Dict[str, Any]]:
        """
        Genera data dictionary per dataset economico (SDMX-compliant).
        
        Returns:
            Lista di colonne con metadata SDMX
        """
        if not PANDAS_AVAILABLE:
            # Fallback: analyze list of dicts
            if not isinstance(dataframe, list) or not dataframe:
                return []
            
            first_record = dataframe[0]
            columns = []
            for name, value in first_record.items():
                col_type = "string"
                if isinstance(value, (int, float)):
                    col_type = "float" if isinstance(value, float) else "integer"
                elif isinstance(value, bool):
                    col_type = "boolean"
                
                role = "dimension"
                if name.lower() in ["geo", "country", "region"]:
                    role = "dimension"
                elif name.lower() in ["time", "year", "period"]:
                    role = "dimension"
                elif name.lower() in ["indicator"]:
                    role = "dimension"
                elif col_type in ["float", "integer"]:
                    role = "measure"
                else:
                    role = "attribute"
                
                columns.append({
                    "name": name,
                    "type": col_type,
                    "role": role,
                    "nullable": False,
                    "description": f"SDMX {role}",
                    "standard": "SDMX"
                })
            
            return columns
        
        if dataframe.empty:
            return []
        
        columns = []
        for col_name in dataframe.columns:
            col_type = str(dataframe[col_name].dtype)
            if "int" in col_type:
                col_type = "integer"
            elif "float" in col_type:
                col_type = "float"
            elif "bool" in col_type:
                col_type = "boolean"
            elif "datetime" in col_type:
                col_type = "date"
            else:
                col_type = "string"
            
            # Determine SDMX role
            role = "dimension"
            if col_name.lower() in ["geo", "country", "region"]:
                role = "dimension"
            elif col_name.lower() in ["time", "year", "period", "date"]:
                role = "dimension"
            elif col_name.lower() in ["indicator"]:
                role = "dimension"
            elif col_type in ["float", "integer"]:
                role = "measure"
            else:
                role = "attribute"
            
            nullable = dataframe[col_name].isna().any()
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "role": role,
                "nullable": nullable,
                "description": f"SDMX {role}",
                "standard": "SDMX"
            })
        
        return columns
    
    def validate(self, dataframe: Any) -> None:
        """
        Valida dataset economico (SDMX requirements).
        
        Raises:
            ValueError: Se il dataset non è valido
        """
        if not PANDAS_AVAILABLE:
            if not isinstance(dataframe, list) or len(dataframe) == 0:
                raise ValueError("Dataset economico vuoto")
            
            first_record = dataframe[0]
            # Must have at least one numeric value (measure)
            has_measure = any(isinstance(v, (int, float)) for v in first_record.values())
            if not has_measure:
                raise ValueError("Dataset economico deve avere almeno una misura (value)")
            
            return
        
        if dataframe.empty:
            raise ValueError("Dataset economico vuoto")
        
        # Must have at least one numeric column (measure)
        numeric_cols = dataframe.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            raise ValueError("Dataset economico deve avere almeno una colonna numerica (measure)")
        
        # Should have temporal dimension (recommended)
        temporal_cols = ['time', 'year', 'date', 'period', 'quarter', 'month']
        has_temporal = any(col in dataframe.columns for col in temporal_cols)
        if not has_temporal:
            # Warning but not error - temporal is recommended but not strictly required
            pass
    
    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize date columns to SDMX temporal dimension format."""
        date_columns = ['date', 'time', 'year', 'period', 'quarter', 'month']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if 'year' not in df.columns:
                        df['year'] = df[col].dt.year
                    if 'quarter' not in df.columns and col != 'quarter':
                        df['quarter'] = df[col].dt.quarter
                except:
                    pass
        return df
    
    def _normalize_geographic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize geographic columns to ISO 3166 standard."""
        geo_columns = ['geo', 'country', 'region', 'country_code', 'iso_code']
        for col in geo_columns:
            if col in df.columns:
                if col in ['country_code', 'iso_code']:
                    df[col] = df[col].astype(str).str.upper()
                if col != 'geo' and 'geo' not in df.columns:
                    df['geo'] = df[col]
        return df
    
    def _standardize_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize indicator names."""
        indicator_mappings = {
            'cpi': 'consumer_price_index',
            'gdp': 'gross_domestic_product',
            'unemployment': 'unemployment_rate',
            'inflation': 'inflation_rate'
        }
        if 'indicator' in df.columns:
            df['indicator'] = df['indicator'].str.lower().replace(indicator_mappings)
        return df
    
    def _apply_sdmx_structure(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Apply SDMX structure: ensure dimensions, measures, attributes."""
        if 'value' not in df.columns:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 1:
                df['value'] = df[numeric_cols[0]]
            elif len(numeric_cols) > 1:
                df['value'] = df[numeric_cols[0]]
        
        if 'unit' not in df.columns:
            df['unit'] = params.get('default_unit', '')
        if 'frequency' not in df.columns:
            df['frequency'] = params.get('frequency', 'annual')
        if 'source' not in df.columns:
            df['source'] = params.get('source', 'unknown')
        
        return df
    
    def _ensure_sdmx_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure SDMX dimensions are present."""
        if 'time' not in df.columns and 'year' in df.columns:
            df['time'] = df['year'].astype(str)
        
        if 'geo' not in df.columns:
            geo_candidates = ['country', 'region', 'country_code', 'iso_code']
            for col in geo_candidates:
                if col in df.columns:
                    df['geo'] = df[col]
                    break
        
        if 'indicator' not in df.columns:
            df['indicator'] = 'value'
        
        return df
    
    def _join_time_series(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Join time series data."""
        join_on = params.get("on", ["time", "geo"])
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Handle missing values."""
        method = params.get("method", "drop")
        if method == "drop":
            df = df.dropna(subset=['value']) if 'value' in df.columns else df.dropna()
        elif method == "fill":
            fill_value = params.get("fill_value", 0)
            df = df.fillna(fill_value)
        elif method == "interpolate":
            if 'time' in df.columns:
                df = df.sort_values('time')
                df = df.interpolate(method='time')
            else:
                df = df.interpolate()
        return df
    
    def _standardize_columns(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Standardize column names to SDMX conventions."""
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get SDMX metadata for this normalizer."""
        return {
            "standard": "SDMX (Statistical Data and Metadata eXchange)",
            "version": "2.1",
            "dimensions": ["time", "geo", "indicator"],
            "measures": ["value"],
            "attributes": ["unit", "frequency", "source", "notes"],
            "description": "SDMX-compliant normalizer for economic and statistical data"
        }
