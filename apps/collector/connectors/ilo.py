"""ILO (International Labour Organization) connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class ILOConnector(BaseConnector):
    """Connector for ILO Statistics API (ILOSTAT)."""
    
    BASE_URL = "https://webapps.ilo.org/sdmx/rest/data"
    
    def __init__(self):
        super().__init__("ilo")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate ILO query."""
        return "dataflow" in query or "indicator" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from ILO Statistics API.
        
        Query format:
        {
            "dataflow": "DF_ILOSTAT_EES_SEX_AGE_RT_A",
            "indicator": "EES_SEX_AGE_RT_A",
            "country": "USA;FRA;ITA",
            "startPeriod": "2000",
            "endPeriod": "2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataflow or indicator")
        
        dataflow = query.get("dataflow", "")
        indicator = query.get("indicator", "")
        country = query.get("country", "all")
        start_period = query.get("startPeriod", "2000")
        end_period = query.get("endPeriod", "2024")
        
        # ILO uses SDMX format
        # ILO SDMX format: /{agency},{dataflow},{version}/{key}
        # Try compact format
        if country != "all" and indicator:
            # Build key: country.indicator
            key = f"{country}.{indicator}"
            url = f"{self.BASE_URL}/ILO,{dataflow},1.0/{key}"
        else:
            url = f"{self.BASE_URL}/ILO,{dataflow},1.0/all"
        
        params = {
            "startPeriod": start_period,
            "endPeriod": end_period,
            "format": "jsondata"
        }
        
        # Fetch data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                raise ValueError(f"Unexpected response format: {response.headers.get('content-type', 'unknown')}")
        except Exception as e:
            # If ILO endpoint fails, return metadata
            records = [{
                "dataflow": dataflow,
                "indicator": indicator or "all",
                "country": country,
                "start_period": start_period,
                "end_period": end_period,
                "status": "endpoint_error",
                "note": f"ILO SDMX endpoint error. Dataflow '{dataflow}' may require authentication or query format may be incorrect. Error: {str(e)}"
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "dataflow": dataflow,
                "indicator": indicator
            }
            provenance = {
                "source": "ILO Statistics (ILOSTAT)",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "ILO Data License",
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
            "source": "ILO Statistics (ILOSTAT)",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "ILO Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

