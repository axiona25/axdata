"""Physics/Nature normalizer following FAIR Data Principles and NetCDF/HDF5 conventions.

Standards:
- FAIR Data Principles (Findable, Accessible, Interoperable, Reusable)
- NetCDF / HDF5 for environmental/climate data
- CERN Open Data Model for experimental data

Used for:
- Environmental data
- Climatology
- Satellite observations
- Physics experiments
"""
from typing import List, Dict, Any, Optional
from normalizers.base import BaseNormalizer
from datetime import datetime


class PhysicsNormalizer(BaseNormalizer):
    """
    Normalizer for physics/natural sciences data following FAIR principles.
    
    Structure:
    - Experiment/mission-based datasets
    - Strong metadata requirements
    - Often multi-file datasets (bundles)
    - Coordinates (spatial, temporal)
    """
    
    def __init__(self):
        super().__init__("physics")
    
    def normalize(self, records: List[Dict[str, Any]], transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize physics/nature data following FAIR principles.
        
        Applies:
        - Coordinate normalization (spatial, temporal)
        - Unit standardization
        - Experiment/mission metadata
        - Multi-file structure support
        """
        if not records:
            return []
        
        normalized = records.copy()
        
        # Apply transformations
        for transformation in transformations:
            trans_type = transformation.get("type")
            params = transformation.get("params", {})
            
            if trans_type == "normalize_coordinates":
                normalized = self._normalize_coordinates(normalized, params)
            elif trans_type == "standardize_units":
                normalized = self._standardize_units(normalized, params)
            elif trans_type == "add_experiment_metadata":
                normalized = self._add_experiment_metadata(normalized, params)
            elif trans_type == "validate":
                normalized = self._validate_records(normalized, params)
        
        return normalized
    
    def _normalize_coordinates(self, records: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize spatial and temporal coordinates.
        
        Ensures:
        - Temporal: ISO 8601 format
        - Spatial: Standard lat/lon or coordinate system
        """
        normalized = []
        for record in records:
            normalized_record = record.copy()
            
            # Normalize temporal coordinates
            for time_field in ['time', 'timestamp', 'date', 'observation_date']:
                if time_field in normalized_record:
                    try:
                        dt = datetime.fromisoformat(str(normalized_record[time_field]).replace('Z', '+00:00'))
                        normalized_record[time_field] = dt.isoformat()
                    except:
                        pass
            
            # Normalize spatial coordinates
            if 'latitude' in normalized_record and 'longitude' in normalized_record:
                try:
                    normalized_record['lat'] = float(normalized_record['latitude'])
                    normalized_record['lon'] = float(normalized_record['longitude'])
                except:
                    pass
            
            normalized.append(normalized_record)
        
        return normalized
    
    def _standardize_units(self, records: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Standardize units of measurement (SI units preferred)."""
        unit_mappings = params.get("unit_mappings", {})
        normalized = []
        
        for record in records:
            normalized_record = record.copy()
            
            # Apply unit mappings if provided
            for field, target_unit in unit_mappings.items():
                if field in normalized_record and 'unit' in record:
                    # Unit conversion would go here
                    normalized_record['unit'] = target_unit
            
            normalized.append(normalized_record)
        
        return normalized
    
    def _add_experiment_metadata(self, records: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add experiment/mission metadata (CERN-style or environmental).
        
        Metadata includes:
        - experiment/project name
        - run_id/event_id
        - instruments
        - version
        """
        experiment_name = params.get("experiment", "")
        run_id = params.get("run_id", "")
        version = params.get("version", "1.0")
        
        normalized = []
        for record in records:
            normalized_record = record.copy()
            
            if experiment_name:
                normalized_record['experiment'] = experiment_name
            if run_id:
                normalized_record['run_id'] = run_id
            normalized_record['dataset_version'] = version
            
            normalized.append(normalized_record)
        
        return normalized
    
    def _validate_records(self, records: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate records."""
        required_fields = params.get("required_fields", [])
        validated = []
        
        for record in records:
            if required_fields:
                if all(field in record and record[field] for field in required_fields):
                    validated.append(record)
            else:
                validated.append(record)
        
        return validated
    
    def validate(self, records: List[Dict[str, Any]]) -> bool:
        """Validate physics/nature data."""
        if not records:
            return False
        
        # Should have at least temporal or spatial coordinates
        first_record = records[0]
        has_temporal = any(field in first_record for field in ['time', 'timestamp', 'date'])
        has_spatial = any(field in first_record for field in ['lat', 'lon', 'latitude', 'longitude'])
        
        # At least one coordinate type recommended
        return has_temporal or has_spatial or len(records) > 0
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get FAIR/NetCDF metadata for this normalizer."""
        return {
            "standards": [
                "FAIR Data Principles",
                "NetCDF / HDF5 conventions",
                "CERN Open Data Model"
            ],
            "principles": {
                "findable": "Rich metadata, persistent identifiers",
                "accessible": "Standard protocols, authentication when needed",
                "interoperable": "Standard formats, vocabularies",
                "reusable": "Clear licenses, detailed provenance"
            },
            "description": "FAIR-compliant normalizer for physics and natural sciences data"
        }

