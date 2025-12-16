"""Wolfram Data Repository connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class WolframConnector(BaseConnector):
    """Connector for Wolfram Data Repository."""
    
    BASE_URL = "https://reference.wolfram.com"
    
    def __init__(self):
        super().__init__("wolfram")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate Wolfram query."""
        return "dataset_id" in query or "search" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from Wolfram Data Repository.
        
        Query format:
        {
            "dataset_id": "12345"
        }
        OR
        {
            "search": "mathematics",
            "limit": 100
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset_id or search")
        
        records = []
        
        if "dataset_id" in query:
            # Fetch specific dataset
            dataset_id = query["dataset_id"]
            url = f"{self.BASE_URL}/datasets/{dataset_id}"
            
            response = make_request_with_retry(self.client, "GET", url)
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            
            record = {
                "dataset_id": dataset_id,
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "category": data.get("category", ""),
                "tags": data.get("tags", []),
                "license": data.get("license", ""),
                "url": data.get("url", ""),
                "format": data.get("format", ""),
                "row_count": data.get("row_count", 0),
                "column_count": data.get("column_count", 0)
            }
            records.append(record)
        
        elif "search" in query:
            # Search datasets - Wolfram may use different endpoint structure
            search_term = query["search"]
            limit = query.get("limit", 100)
            
            # Try alternative endpoints
            urls_to_try = [
                f"{self.BASE_URL}/language/ref/Entity.html",
                "https://www.wolframalpha.com/api/v1/datasets",
            ]
            
            success = False
            for url in urls_to_try:
                try:
                    params = {"q": search_term, "limit": limit} if "api" in url else {}
                    response = make_request_with_retry(self.client, "GET", url, params=params)
                    if response.status_code == 200:
                        if "application/json" in response.headers.get("content-type", ""):
                            data = response.json()
                            results = data.get("results", data.get("datasets", []))
                            for result in results[:limit]:
                                record = {
                                    "dataset_id": result.get("id", ""),
                                    "name": result.get("name", ""),
                                    "description": result.get("description", ""),
                                    "category": result.get("category", ""),
                                    "tags": result.get("tags", [])
                                }
                                records.append(record)
                            success = True
                            break
                except Exception:
                    continue
            
            # If all attempts failed, return metadata
            if not success and not records:
                record = {
                    "search_term": search_term,
                    "status": "api_not_available",
                    "note": "Wolfram Data Repository API may require authentication or use different endpoint structure."
                }
                records.append(record)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "Wolfram Data Repository",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "Wolfram Data License",
            "api_version": "v1"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

