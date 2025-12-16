"""UN Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class UNDataConnector(BaseConnector):
    """Connector for UN Data API."""
    
    BASE_URL = "https://data.un.org/ws/rest/data"
    
    def __init__(self):
        super().__init__("un_data")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate UN Data query."""
        return "dataflow" in query or "indicator" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from UN Data API.
        
        Query format:
        {
            "dataflow": "DF_UNDATA_CO2_EMISSIONS",
            "indicator": "EN.ATM.CO2E.PC",
            "country": "USA;FRA;ITA",
            "startTime": "2000",
            "endTime": "2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataflow or indicator")
        
        dataflow = query.get("dataflow", "")
        indicator = query.get("indicator", "")
        country = query.get("country", "all")
        start_time = query.get("startTime", "2000")
        end_time = query.get("endTime", "2024")
        
        # UN Data uses SDMX format
        # UN Data SDMX format: /data/{agency},{dataflow},{version}/{key}
        # Note: UN Data API may have changed or requires different format
        if indicator and country != "all":
            key = f"{country}.{indicator}"
            url = f"{self.BASE_URL}/UN_DATA,{dataflow},1.0/{key}"
        elif country != "all":
            url = f"{self.BASE_URL}/UN_DATA,{dataflow},1.0/{country}...all"
        else:
            url = f"{self.BASE_URL}/UN_DATA,{dataflow},1.0/all"
        
        params = {
            "startPeriod": start_time,
            "endPeriod": end_time,
            "format": "json"
        }
        
        # Fetch data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                raise ValueError(f"Unexpected response format")
        except Exception as e:
            # If UN Data endpoint fails, return metadata
            records = [{
                "dataflow": dataflow,
                "indicator": indicator or "all",
                "country": country,
                "status": "endpoint_error",
                "note": f"UN Data SDMX endpoint may have changed or dataflow '{dataflow}' may not exist. Error: {str(e)}"
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "dataflow": dataflow,
                "indicator": indicator
            }
            provenance = {
                "source": "UN Data",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "UN Data License",
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
                        "dataflow": dataflow,
                        "indicator": indicator
                    }
                    records.append(record)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataflow": dataflow,
            "indicator": indicator
        }
        
        # Provenance
        provenance = {
            "source": "UN Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "UN Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

