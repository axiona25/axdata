"""Global Carbon Atlas connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class GlobalCarbonConnector(BaseConnector):
    """Connector for Global Carbon Atlas API."""
    
    BASE_URL = "https://www.globalcarbonatlas.org/en/CO2-emissions"
    
    def __init__(self):
        super().__init__("global_carbon")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate Global Carbon Atlas query."""
        return "country" in query or "indicator" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from Global Carbon Atlas.
        
        Query format:
        {
            "country": "USA;FRA;ITA",
            "indicator": "fossil_fuel",
            "year": "2000:2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing country or indicator")
        
        country = query.get("country", "all")
        indicator = query.get("indicator", "fossil_fuel")
        year_range = query.get("year", "2000:2024")
        
        # Parse year range
        if ":" in year_range:
            start_year, end_year = year_range.split(":")
        else:
            start_year = end_year = year_range
        
        # Global Carbon Atlas uses web interface
        # This is a simplified API wrapper
        url = f"{self.BASE_URL}"
        params = {
            "country": country,
            "indicator": indicator,
            "start_year": start_year,
            "end_year": end_year
        }
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        # Global Carbon Atlas may return HTML or JSON
        # This is a simplified version
        data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "data" in data:
            records = data["data"]
        else:
            # Fallback: return metadata
            records = [{
                "country": country,
                "indicator": indicator,
                "year_range": year_range,
                "status": "metadata_retrieved",
                "note": "Full data may require specific API endpoint or web scraping"
            }]
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                transformed_records.append({
                    "country": record.get("country", country),
                    "indicator": indicator,
                    "year": record.get("year", ""),
                    "value": record.get("value", record.get("emissions", ""))
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "country": country,
            "indicator": indicator
        }
        
        # Provenance
        provenance = {
            "source": "Global Carbon Atlas",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "Global Carbon Atlas License",
            "api_version": "Web"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

