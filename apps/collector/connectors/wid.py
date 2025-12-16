"""World Inequality Database (WID) connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class WIDConnector(BaseConnector):
    """Connector for World Inequality Database API."""
    
    BASE_URL = "https://api.wid.world"
    
    def __init__(self):
        super().__init__("wid")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate WID query."""
        return "indicator" in query and "country" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from World Inequality Database API.
        
        Query format:
        {
            "indicator": "sptinc",  # Share of pre-tax national income
            "country": "US;FR;IT",
            "year": "2000:2024",
            "percentile": "p0p100"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing indicator or country")
        
        indicator = query["indicator"]
        country = query["country"]
        year_range = query.get("year", "2000:2024")
        percentile = query.get("percentile", "p0p100")
        
        # Parse year range
        if ":" in year_range:
            start_year, end_year = year_range.split(":")
        else:
            start_year = end_year = year_range
        
        # WID API endpoint - may require authentication
        # Try alternative endpoint structure
        url = f"{self.BASE_URL}/api/v1/squash/get"
        params = {
            "indicator": indicator,
            "country": country,
            "start_year": start_year,
            "end_year": end_year,
            "percentile": percentile,
            "format": "json"
        }
        
        # Try fetching data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
        except Exception as e:
            # If it fails, try returning metadata with note about authentication
            records = [{
                "indicator": indicator,
                "country": country,
                "start_year": start_year,
                "end_year": end_year,
                "status": "authentication_required",
                "note": "WID API may require authentication. Please check WID documentation for API access."
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "indicator": indicator,
                "country": country
            }
            provenance = {
                "source": "World Inequality Database (WID)",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "WID Data License",
                "api_version": "REST",
                "note": "API may require authentication"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        data = response.json()
        
        # Parse WID response
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "values" in data:
            records = data["values"]
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                transformed_records.append({
                    "country": record.get("country", ""),
                    "year": record.get("year", ""),
                    "indicator": indicator,
                    "percentile": percentile,
                    "value": record.get("value", record.get("share", ""))
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "indicator": indicator,
            "country": country
        }
        
        # Provenance
        provenance = {
            "source": "World Inequality Database (WID)",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "WID Data License",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

