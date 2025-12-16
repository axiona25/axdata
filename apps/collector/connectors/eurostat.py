"""Eurostat connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class EurostatConnector(BaseConnector):
    """Connector for Eurostat API."""
    
    BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    
    def __init__(self):
        super().__init__("eurostat")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate Eurostat query."""
        return "dataset_code" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from Eurostat API.
        
        Query format:
        {
            "dataset_code": "prc_hicp_midx",  # HICP inflation
            "filters": {
                "geo": ["IT", "FR", "DE"],
                "time": ["2020", "2021", "2022"]
            },
            "format": "json"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset_code")
        
        dataset_code = query["dataset_code"]
        filters = query.get("filters", {})
        format_type = query.get("format", "json")
        
        # Build URL
        url = f"{self.BASE_URL}/{dataset_code}"
        params = {"format": format_type}
        
        # Add filters as parameters
        # Eurostat API expects filters in specific format
        for key, values in filters.items():
            if isinstance(values, list):
                # Join with + for multiple values
                params[key] = "+".join(str(v) for v in values)
            else:
                params[key] = str(values)
        
        # If no filters provided, try to get all data (may be large)
        # For better results, always provide at least geo and time filters
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Parse Eurostat response
        # Eurostat returns data in a specific format
        records = []
        if "value" in data and "dimension" in data:
            values = data["value"]
            dimensions = data["dimension"]
            
            if not values or len(values) == 0:
                # Try without filters or with different format
                # Return empty but valid response
                pass
            else:
                # Get dimension labels and indices
                dim_info = {}
                for dim_name in dimensions.keys():
                    dim_data = dimensions.get(dim_name, {})
                    category = dim_data.get("category", {})
                    dim_info[dim_name] = {
                        "labels": category.get("label", {}),
                        "indices": category.get("index", {})
                    }
                
                # Transform to records
                for key, value in values.items():
                    # Parse key (format: dim1_idx:dim2_idx:dim3_idx:...)
                    parts = key.split(":")
                    
                    # Build record with all dimensions
                    record = {
                        "value": value,
                        "dataset_code": dataset_code
                    }
                    
                    # Map indices to codes for each dimension
                    for i, dim_name in enumerate(dimensions.keys()):
                        if i < len(parts):
                            idx = parts[i]
                            # Find code for this index
                            dim_codes = dim_info.get(dim_name, {}).get("indices", {})
                            dim_labels = dim_info.get(dim_name, {}).get("labels", {})
                            
                            # Find code matching this index
                            code = next((k for k, v in dim_codes.items() if str(v) == idx), "")
                            if code:
                                record[dim_name] = code
                                record[f"{dim_name}_label"] = dim_labels.get(code, "")
                    
                    records.append(record)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataset_code": dataset_code,
            "filters": filters
        }
        
        # Provenance
        provenance = {
            "source": "Eurostat",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "Eurostat Data License",
            "api_version": "1.0"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

