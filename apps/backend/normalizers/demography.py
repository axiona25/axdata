"""Demography normalizer following UN SDG Metadata and Eurostat demographic model.

Standards:
- UN SDG Metadata (Sustainable Development Goals)
- Eurostat demographic model
- ISO 3166 (countries)
- ISO 4217 (currencies)

Used for:
- Demographic statistics
- Social indicators
- Population data
- UN SDG tracking
"""
from typing import List, Dict, Any, Optional
from normalizers.base import BaseNormalizer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class DemographyNormalizer(BaseNormalizer):
    """
    Normalizer for demographic/social data following UN SDG/Eurostat standards.
    
    Structure:
    - Multidimensional demographic data
    - Dimensions: geo, year, indicator, age_group, sex
    - Similar to SDMX but with demographic-specific dimensions
    """
    
    def __init__(self):
        super().__init__("demography")
    
    def normalize(self, records: List[Dict[str, Any]], transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize demographic data following UN SDG/Eurostat standards.
        
        Applies:
        - Geographic normalization (ISO 3166)
        - Temporal normalization
        - Demographic dimension standardization (age_group, sex)
        - Indicator standardization
        """
        if not records:
            return []
        
        if not PANDAS_AVAILABLE:
            return records
        
        df = pd.DataFrame(records)
        
        # Apply transformations
        for transformation in transformations:
            trans_type = transformation.get("type")
            params = transformation.get("params", {})
            
            if trans_type == "normalize_geo":
                df = self._normalize_geographic(df)
            elif trans_type == "normalize_demographic_dims":
                df = self._normalize_demographic_dimensions(df, params)
            elif trans_type == "standardize_indicators":
                df = self._standardize_indicators(df)
            elif trans_type == "handle_missing":
                df = self._handle_missing_values(df, params)
        
        # Ensure demographic dimensions
        df = self._ensure_demographic_dimensions(df)
        
        return df.to_dict('records')
    
    def _normalize_geographic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize geographic columns to ISO 3166 standard.
        
        UN SDG requires ISO country codes.
        """
        geo_columns = ['geo', 'country', 'region', 'country_code', 'iso_code']
        for col in geo_columns:
            if col in df.columns:
                # Ensure uppercase for ISO codes
                if col in ['country_code', 'iso_code']:
                    df[col] = df[col].astype(str).str.upper()
                # Rename to standard 'geo' if needed
                if col != 'geo' and 'geo' not in df.columns:
                    df['geo'] = df[col]
        
        return df
    
    def _normalize_demographic_dimensions(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Normalize demographic-specific dimensions.
        
        Dimensions:
        - age_group: Standard age groups (0-14, 15-64, 65+)
        - sex: M/F or Male/Female
        """
        # Normalize sex/gender field
        sex_columns = ['sex', 'gender', 'male_female']
        for col in sex_columns:
            if col in df.columns:
                # Standardize to M/F
                df[col] = df[col].astype(str).str.upper()
                df[col] = df[col].replace({
                    'MALE': 'M', 'FEMALE': 'F',
                    'M': 'M', 'F': 'F'
                })
                if col != 'sex' and 'sex' not in df.columns:
                    df['sex'] = df[col]
        
        # Normalize age groups
        if 'age_group' in df.columns:
            # Standardize age group format
            df['age_group'] = df['age_group'].astype(str)
        
        return df
    
    def _standardize_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize demographic indicators (UN SDG indicators)."""
        # Common demographic indicator mappings
        indicator_mappings = {
            'population': 'total_population',
            'birth_rate': 'crude_birth_rate',
            'death_rate': 'crude_death_rate',
            'life_expectancy': 'life_expectancy_at_birth',
            'fertility': 'total_fertility_rate'
        }
        
        if 'indicator' in df.columns:
            df['indicator'] = df['indicator'].str.lower().replace(indicator_mappings)
        
        return df
    
    def _ensure_demographic_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure demographic dimensions are present.
        
        Required dimensions:
        - geo (geographic)
        - year (temporal)
        - indicator (demographic indicator)
        Optional:
        - age_group
        - sex
        """
        # Ensure geo dimension
        if 'geo' not in df.columns:
            geo_candidates = ['country', 'region', 'country_code', 'iso_code']
            for col in geo_candidates:
                if col in df.columns:
                    df['geo'] = df[col]
                    break
        
        # Ensure year dimension
        if 'year' not in df.columns and 'time' in df.columns:
            df['year'] = df['time']
        
        # Ensure indicator dimension
        if 'indicator' not in df.columns:
            # Try to infer from other columns
            df['indicator'] = 'value'
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Handle missing values in demographic data."""
        method = params.get("method", "drop")
        
        if method == "drop":
            df = df.dropna(subset=['value']) if 'value' in df.columns else df.dropna()
        elif method == "fill":
            fill_value = params.get("fill_value", 0)
            df = df.fillna(fill_value)
        
        return df
    
    def validate(self, records: List[Dict[str, Any]]) -> bool:
        """
        Validate demographic data.
        
        Requires:
        - Geographic dimension (geo/country)
        - Temporal dimension (year/time)
        - At least one measure (value)
        """
        if not records:
            return False
        
        first_record = records[0]
        
        # Must have geographic dimension
        has_geo = any(field in first_record for field in ['geo', 'country', 'region', 'country_code'])
        
        # Must have temporal dimension
        has_temporal = any(field in first_record for field in ['year', 'time', 'date'])
        
        # Must have at least one numeric value
        has_value = any(isinstance(v, (int, float)) for v in first_record.values())
        
        return has_geo and has_temporal and has_value
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get UN SDG/Eurostat metadata for this normalizer."""
        return {
            "standards": [
                "UN SDG Metadata",
                "Eurostat demographic model",
                "ISO 3166 (countries)",
                "ISO 4217 (currencies)"
            ],
            "dimensions": {
                "required": ["geo", "year", "indicator"],
                "optional": ["age_group", "sex"]
            },
            "description": "UN SDG/Eurostat-compliant normalizer for demographic and social statistics"
        }

