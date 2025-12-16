"""World Bank Open Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class WorldBankConnector(BaseConnector):
    """Connector for World Bank Open Data API."""
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    def __init__(self):
        super().__init__("worldbank")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate World Bank query."""
        required = ["indicator", "country"]
        return all(key in query for key in required)
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from World Bank API.
        
        Query format:
        {
            "indicator": "NY.GDP.MKTP.CD",  # GDP indicator
            "country": "US;FR;IT",  # Country codes (semicolon-separated)
            "date": "2000:2024",  # Date range (optional)
            "format": "json"  # Response format
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing required fields")
        
        indicator = query["indicator"]
        country = query.get("country", "all")
        date_range = query.get("date", "2000:2024")
        format_type = query.get("format", "json")
        
        # Build URL
        url = f"{self.BASE_URL}/country/{country}/indicator/{indicator}"
        params = {
            "date": date_range,
            "format": format_type,
            "per_page": 1000  # Max per page
        }
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Parse World Bank response
        if isinstance(data, list) and len(data) > 1:
            records = data[1]  # Second element contains data
        else:
            records = []
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                transformed_records.append({
                    "country": record.get("country", {}).get("value", ""),
                    "country_code": record.get("countryiso3code", ""),
                    "indicator": record.get("indicator", {}).get("value", ""),
                    "indicator_code": record.get("indicator", {}).get("id", ""),
                    "date": record.get("date", ""),
                    "value": record.get("value"),
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "indicator": indicator,
            "country": country,
            "date_range": date_range
        }
        
        # Provenance
        provenance = {
            "source": "World Bank Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "World Bank Open Data License",
            "api_version": "v2"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

