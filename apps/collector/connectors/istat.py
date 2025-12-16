"""ISTAT (Italian National Statistics) connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class ISTATConnector(BaseConnector):
    """Connector for ISTAT API (SDMX / REST)."""
    
    BASE_URL = "https://esploradati.istat.it/SDMXWS/rest/data"
    
    def __init__(self):
        super().__init__("istat")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate ISTAT query."""
        return "dataflow" in query or "dataset" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from ISTAT API.
        
        Query format:
        {
            "dataflow": "DCIS_POPSTRRES1",  # Population structure
            "filter": "IT.ALL.TOTAL",
            "startTime": "2000",
            "endTime": "2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataflow or dataset")
        
        dataflow = query.get("dataflow", query.get("dataset", ""))
        filter_str = query.get("filter", "")
        start_time = query.get("startTime", "2000")
        end_time = query.get("endTime", "2024")
        
        # ISTAT uses SDMX format
        # ISTAT SDMX format: /{agency},{dataflow},{version}/{key}
        # Try different endpoint structures
        if filter_str:
            url = f"{self.BASE_URL}/IT1,{dataflow},1.0/{filter_str}"
        else:
            # Try with "all" or empty key
            url = f"{self.BASE_URL}/IT1,{dataflow},1.0/all"
        
        params = {
            "startPeriod": start_time,
            "endPeriod": end_time,
            "format": "json"
        }
        
        # Fetch data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
            # Check if response is valid JSON
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                # If not JSON, might be error message
                raise ValueError(f"Unexpected response format: {response.headers.get('content-type', 'unknown')}")
        except Exception as e:
            # If ISTAT endpoint fails, return metadata
            records = [{
                "dataflow": dataflow,
                "filter": filter_str or "all",
                "status": "endpoint_error",
                "note": f"ISTAT SDMX endpoint error. Dataflow '{dataflow}' may not exist or query format may be incorrect. Error: {str(e)}"
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "dataflow": dataflow,
                "filter": filter_str
            }
            provenance = {
                "source": "ISTAT",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "ISTAT Open Data License",
                "api_version": "SDMX",
                "note": f"Endpoint error: {str(e)}"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        # Parse SDMX JSON response
        records = []
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
                        "dataflow": dataflow
                    }
                    records.append(record)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataflow": dataflow,
            "filter": filter_str
        }
        
        # Provenance
        provenance = {
            "source": "ISTAT",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "ISTAT Open Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

