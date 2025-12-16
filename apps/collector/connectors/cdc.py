"""CDC Open Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class CDCConnector(BaseConnector):
    """Connector for CDC Open Data API."""
    
    BASE_URL = "https://data.cdc.gov/resource"
    
    def __init__(self):
        super().__init__("cdc")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate CDC query."""
        return "dataset" in query or "resource_id" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from CDC Open Data API.
        
        Query format:
        {
            "dataset": "n8ey-b4q8",  # Dataset ID
            "limit": 1000,
            "offset": 0,
            "where": "year='2020'"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset or resource_id")
        
        dataset = query.get("dataset", query.get("resource_id", ""))
        limit = query.get("limit", 1000)
        offset = query.get("offset", 0)
        where_clause = query.get("where", "")
        
        # CDC uses Socrata API
        # Note: CDC datasets may require authentication or have changed IDs
        # Try to use the provided dataset, or return empty if not found
        if not dataset or dataset == "cdc":
            # Try a generic search endpoint instead
            # CDC Socrata API might need different approach
            # For now, return empty result with note
            records = []
            metadata = {
                "row_count": 0,
                "columns": [],
                "dataset": dataset,
                "note": "CDC dataset not found or requires authentication. Please provide a valid dataset ID."
            }
            provenance = {
                "source": "CDC Open Data",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": "",
                "license": "CDC Public Domain",
                "api_version": "Socrata",
                "note": "Dataset ID not found"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        url = f"{self.BASE_URL}/{dataset}.json"
        params = {
            "$limit": limit,
            "$offset": offset
        }
        
        if where_clause:
            params["$where"] = where_clause
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Transform records
        records = []
        if isinstance(data, list):
            records = data
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataset": dataset
        }
        
        # Provenance
        provenance = {
            "source": "CDC Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "CDC Public Domain",
            "api_version": "Socrata"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

