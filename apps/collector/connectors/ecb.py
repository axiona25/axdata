"""ECB Statistical Data Warehouse connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class ECBConnector(BaseConnector):
    """Connector for ECB Statistical Data Warehouse (SDMX)."""
    
    BASE_URL = "https://sdw-wsrest.ecb.europa.eu/service/data"
    
    def __init__(self):
        super().__init__("ecb")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate ECB query."""
        return "dataflow" in query or "key" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from ECB Statistical Data Warehouse.
        
        Query format:
        {
            "dataflow": "EXR",  # Exchange rates
            "key": "D.USD.EUR.SP00.A",
            "startPeriod": "2000-01",
            "endPeriod": "2024-12"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataflow or key")
        
        dataflow = query.get("dataflow", "EXR")
        key = query.get("key", "")
        start_period = query.get("startPeriod", "2000-01")
        end_period = query.get("endPeriod", "2024-12")
        
        # ECB uses SDMX format
        # ECB API format: /data/{dataflow}/{key}?startPeriod=...&endPeriod=...
        # ECB requires key in path, not as parameter
        if key:
            # Key should be in the path
            url = f"{self.BASE_URL}/{dataflow}/{key}"
            params = {
                "startPeriod": start_period,
                "endPeriod": end_period,
                "format": "jsondata",
                "detail": "dataonly"
            }
        else:
            # If no key, try to get all data for dataflow (may be large or fail)
            url = f"{self.BASE_URL}/{dataflow}"
            params = {
                "startPeriod": start_period,
                "endPeriod": end_period,
                "format": "jsondata",
                "detail": "dataonly"
            }
        
        # Fetch data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
            data = response.json()
        except Exception as e:
            # If ECB endpoint fails, try alternative approach or return metadata
            records = [{
                "dataflow": dataflow,
                "key": key or "all",
                "status": "endpoint_error",
                "note": "ECB SDMX endpoint may require authentication or have changed. Please verify endpoint and credentials."
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "dataflow": dataflow,
                "key": key
            }
            provenance = {
                "source": "ECB Statistical Data Warehouse",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "ECB Data License",
                "api_version": "SDMX",
                "note": "Endpoint error: " + str(e)
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
            "key": key
        }
        
        # Provenance
        provenance = {
            "source": "ECB Statistical Data Warehouse",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "ECB Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

