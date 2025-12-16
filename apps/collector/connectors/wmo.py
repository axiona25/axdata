"""WMO (World Meteorological Organization) connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class WMOConnector(BaseConnector):
    """Connector for WMO Data Portal."""
    
    BASE_URL = "https://wmo.int/data"
    
    def __init__(self):
        super().__init__("wmo")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate WMO query."""
        return "dataset" in query or "station" in query or "indicator" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from WMO Data Portal.
        
        Query format:
        {
            "indicator": "temperature",
            "station": "12345",
            "start_date": "2020-01-01",
            "end_date": "2024-12-31"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset, station, or indicator")
        
        indicator = query.get("indicator", "")
        station = query.get("station", "")
        start_date = query.get("start_date", "")
        end_date = query.get("end_date", "")
        dataset = query.get("dataset", "")
        
        # WMO Data Portal - endpoint may have changed
        # WMO uses various data portals, try to return metadata if endpoint fails
        base_urls = [
            f"{self.BASE_URL}/stations/{station}" if station else None,
            f"{self.BASE_URL}/datasets/{dataset}" if dataset else None,
            "https://public.wmo.int/en/data"
        ]
        
        url = None
        for candidate_url in base_urls:
            if candidate_url:
                url = candidate_url
                break
        
        if not url:
            url = "https://public.wmo.int/en/data"
        
        params = {}
        if indicator:
            params["indicator"] = indicator
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        # Try fetching data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
        except Exception as e:
            # If it fails, return metadata with note
            records = [{
                "indicator": indicator or dataset or "various",
                "station": station or "",
                "dataset": dataset or "",
                "status": "endpoint_not_available",
                "note": "WMO data portal endpoint may have changed. Please check WMO website for current API access."
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "indicator": indicator,
                "station": station
            }
            provenance = {
                "source": "World Meteorological Organization (WMO)",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "WMO Data License",
                "api_version": "REST",
                "note": "Endpoint may require verification"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        
        # Parse WMO response
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "data" in data:
            records = data["data"]
        elif isinstance(data, dict) and "observations" in data:
            records = data["observations"]
        else:
            # Fallback: return metadata
            records = [{
                "indicator": indicator,
                "station": station,
                "dataset": dataset,
                "status": "metadata_retrieved"
            }]
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                transformed_records.append({
                    "station": record.get("station", station),
                    "indicator": indicator or record.get("indicator", ""),
                    "date": record.get("date", record.get("timestamp", "")),
                    "value": record.get("value", record.get("observation", "")),
                    "unit": record.get("unit", "")
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "indicator": indicator,
            "station": station
        }
        
        # Provenance
        provenance = {
            "source": "World Meteorological Organization (WMO)",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "WMO Data License",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

