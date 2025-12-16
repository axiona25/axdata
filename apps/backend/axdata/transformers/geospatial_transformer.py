"""Geospatial transformer - data with coordinates."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class GeospatialTransformer(BaseTransformer):
    """Transform data into geospatial format."""
    
    def __init__(self):
        super().__init__("geospatial")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to geospatial format.
        
        Rules:
        - Enrich with coordinates (lat/long)
        - Normalize CRS
        - Validate geometry
        - GeoJSON format support
        """
        if not raw_data:
            return []
        
        if not PANDAS_AVAILABLE:
            return self._transform_manual(raw_data, ds_spec)
        
        df = pd.DataFrame(raw_data)
        
        # Find or create geometry columns
        geometry = self._extract_geometry(df, ds_spec)
        
        # Add CRS
        crs = ds_spec.get("dimensions", {}).get("geo", {}).get("crs", "EPSG:4326")
        df['crs'] = crs
        
        # Add geo_scope and geo_level
        geo_dim = ds_spec.get("dimensions", {}).get("geo", {})
        df['geo_scope'] = geo_dim.get("scope")
        df['geo_level'] = geo_dim.get("level", "none")
        
        # Add geometry as GeoJSON if not present
        if 'geometry' not in df.columns and geometry:
            df['geometry'] = geometry
        
        return df.to_dict('records')
    
    def _extract_geometry(self, df: pd.DataFrame, ds_spec: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract or create geometry from coordinates."""
        # Look for lat/long columns
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'lat' in col_lower or 'latitude' in col_lower:
                lat_col = col
            elif 'lon' in col_lower or 'longitude' in col_lower or 'lng' in col_lower:
                lon_col = col
        
        if lat_col and lon_col:
            # Create GeoJSON Point geometry
            geometries = []
            for _, row in df.iterrows():
                lat = row[lat_col]
                lon = row[lon_col]
                if pd.notna(lat) and pd.notna(lon):
                    geometries.append({
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)]
                    })
                else:
                    geometries.append(None)
            return geometries
        
        # Check if geometry column already exists
        if 'geometry' in df.columns:
            return df['geometry'].tolist()
        
        return None
    
    def _transform_manual(self, records: List[Dict[str, Any]], ds_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Manual transformation without pandas."""
        # Find lat/long columns
        lat_col = None
        lon_col = None
        
        for record in records:
            for key in record.keys():
                key_lower = key.lower()
                if 'lat' in key_lower:
                    lat_col = key
                elif 'lon' in key_lower or 'lng' in key_lower:
                    lon_col = key
        
        # Add geometry
        if lat_col and lon_col:
            for record in records:
                lat = record.get(lat_col)
                lon = record.get(lon_col)
                if lat is not None and lon is not None:
                    record['geometry'] = {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)]
                    }
        
        # Add CRS and geo info
        geo_dim = ds_spec.get("dimensions", {}).get("geo", {})
        crs = geo_dim.get("crs", "EPSG:4326")
        
        for record in records:
            record['crs'] = crs
            record['geo_scope'] = geo_dim.get("scope")
            record['geo_level'] = geo_dim.get("level", "none")
        
        return records
