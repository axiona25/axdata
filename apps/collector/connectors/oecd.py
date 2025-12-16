"""OECD Statistics connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class OECDConnector(BaseConnector):
    """Connector for OECD Statistics API (SDMX)."""
    
    BASE_URL = "https://stats.oecd.org/SDMX-JSON/data"
    
    def __init__(self):
        super().__init__("oecd")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate OECD query."""
        return "dataset" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from OECD Statistics API.
        
        Query format:
        {
            "dataset": "SNA_TABLE1",  # National Accounts
            "filter": "AUS+AUT+BEL.CAN+CHL+COL+CRI",  # Countries
            "startTime": "2000",
            "endTime": "2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset")
        
        dataset = query["dataset"]
        filter_str = query.get("filter", "")
        start_time = query.get("startTime", "2000")
        end_time = query.get("endTime", "2024")
        
        # Build SDMX query
        url = f"{self.BASE_URL}/{dataset}/all"
        params = {
            "startTime": start_time,
            "endTime": end_time,
            "contentType": "json"
        }
        
        if filter_str:
            params["filter"] = filter_str
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Parse SDMX JSON response
        records = []
        # OECD SDMX format can vary
        if isinstance(data, dict):
            if "dataSets" in data and len(data["dataSets"]) > 0:
                dataset_data = data["dataSets"][0]
                series = dataset_data.get("series", {})
                
                for series_key, series_values in series.items():
                    observations = series_values.get("observations", {})
                    
                    for obs_key, obs_value in observations.items():
                        record = {
                            "series_key": series_key,
                            "period": obs_key,
                            "value": obs_value[0] if isinstance(obs_value, list) else obs_value,
                            "dataset": dataset
                        }
                        records.append(record)
            elif "data" in data:
                # OECD sometimes returns data directly in 'data' key
                data_obj = data.get("data", {})
                if isinstance(data_obj, list):
                    for item in data_obj:
                        if isinstance(item, dict):
                            records.append({
                                **item,
                                "dataset": dataset
                            })
                elif isinstance(data_obj, dict):
                    # If data is a dict, it might contain structured data
                    # Try to extract series-like structure
                    if "dataSets" in data_obj:
                        # Nested dataSets
                        for ds in data_obj.get("dataSets", []):
                            if isinstance(ds, dict) and "series" in ds:
                                series = ds.get("series", {})
                                for series_key, series_values in series.items():
                                    observations = series_values.get("observations", {})
                                    for obs_key, obs_value in observations.items():
                                        records.append({
                                            "series_key": series_key,
                                            "period": obs_key,
                                            "value": obs_value[0] if isinstance(obs_value, list) else obs_value,
                                            "dataset": dataset
                                        })
                    else:
                        # Try to extract key-value pairs
                        for key, value in data_obj.items():
                            if isinstance(value, (int, float, str)):
                                records.append({
                                    "key": key,
                                    "value": value,
                                    "dataset": dataset
                                })
                            elif isinstance(value, dict):
                                # Nested structure
                                records.append({
                                    "key": key,
                                    **value,
                                    "dataset": dataset
                                })
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataset": dataset,
            "filter": filter_str
        }
        
        # Provenance
        provenance = {
            "source": "OECD Statistics",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "OECD Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

