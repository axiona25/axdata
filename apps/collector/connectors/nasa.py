"""NASA Open Data connector."""
import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class NASAConnector(BaseConnector):
    """Connector for NASA Open Data API (CKAN)."""
    
    BASE_URL = "https://data.nasa.gov/api/3/action"
    
    def __init__(self):
        super().__init__("nasa")
        self.client = get_client()
        # Initialize credentials attributes first
        self.username = None
        self.password = None
        # Load NASA token/credentials if available
        self.token = self._load_nasa_token()
    
    def _load_nasa_token(self) -> Optional[str]:
        """
        Load NASA Earthdata token.
        
        First tries to get from environment variable.
        If not found and username/password are available, can use Basic Auth instead.
        """
        # Try to get existing token first
        token = os.getenv("NASA_EARTHDATA_TOKEN")
        if token:
            return token
        
        # If no token, we can use username/password for Basic Auth if needed
        username = os.getenv("NASA_EARTHDATA_USERNAME")
        password = os.getenv("NASA_EARTHDATA_PASSWORD")
        
        # If username/password available, store them for Basic Auth
        if username and password:
            self.username = username
            self.password = password
        else:
            self.username = None
            self.password = None
        
        return None
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate NASA query."""
        # Accept either dataset (package) ID or resource ID
        return "dataset" in query or "resource_id" in query or "package_id" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from NASA Open Data API (CKAN).
        
        Query format:
        {
            "dataset": "08-05-2010-uh60",  # Package/Dataset ID
            "resource_id": "abc-123",  # Optional: specific resource ID
            "limit": 1000
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset, package_id or resource_id")
        
        package_id = query.get("dataset", query.get("package_id", ""))
        resource_id = query.get("resource_id")
        limit = query.get("limit", 1000)
        
        # Add NASA authentication headers if available
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.username and self.password:
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        # If resource_id is specified, fetch the resource directly
        if resource_id:
            url = f"{self.BASE_URL}/resource_show"
            params = {"id": resource_id}
        else:
            # Otherwise, get package info and use first resource
            url = f"{self.BASE_URL}/package_show"
            params = {"id": package_id}
        
        # Fetch package/resource metadata
        if headers:
            response = make_request_with_retry(self.client, "GET", url, params=params, headers=headers)
        else:
            response = make_request_with_retry(self.client, "GET", url, params=params)
        
        result_data = response.json()
        
        # Extract resource URL from CKAN response
        records = []
        resource_url = None
        
        if result_data.get("success"):
            result = result_data.get("result", {})
            
            if resource_id:
                # Direct resource response
                resource_url = result.get("url")
                # Try to fetch the actual data from the resource URL
                if resource_url:
                    try:
                        data_response = make_request_with_retry(self.client, "GET", resource_url)
                        # Try to parse as JSON
                        try:
                            data = data_response.json()
                            if isinstance(data, list):
                                records = data[:limit]
                            elif isinstance(data, dict):
                                # If it's a dict, try to extract list from common keys
                                for key in ["data", "results", "features", "records"]:
                                    if key in data and isinstance(data[key], list):
                                        records = data[key][:limit]
                                        break
                                else:
                                    # If no list found, add the dict itself
                                    records = [data]
                        except:
                            # If not JSON, store raw text (truncated)
                            records = [{"raw_data": data_response.text[:1000]}]
                    except:
                        # If resource URL fails, store metadata
                        records = []
            else:
                # Package response - get first resource
                resources = result.get("resources", [])
                if resources:
                    resource = resources[0]
                    resource_url = resource.get("url")
                    resource_id = resource.get("id")
                    # Try to fetch the actual data
                    if resource_url:
                        try:
                            data_response = make_request_with_retry(self.client, "GET", resource_url)
                            try:
                                data = data_response.json()
                                if isinstance(data, list):
                                    records = data[:limit]
                                elif isinstance(data, dict):
                                    for key in ["data", "results", "features", "records"]:
                                        if key in data and isinstance(data[key], list):
                                            records = data[key][:limit]
                                            break
                                    else:
                                        records = [data]
                            except:
                                records = [{"raw_data": data_response.text[:1000]}]
                        except:
                            records = []
        
        # If no records from resource URL, return package metadata
        if not records:
            # Return package metadata as a record
            if result_data.get("success"):
                result = result_data.get("result", {})
                records = [{
                    "package_id": result.get("id", package_id),
                    "title": result.get("title", ""),
                    "description": result.get("notes", "")[:500] if result.get("notes") else "",
                    "resources_count": len(result.get("resources", [])),
                    "tags": [tag.get("name", "") for tag in result.get("tags", [])],
                    "organization": result.get("organization", {}).get("title", "") if result.get("organization") else ""
                }]
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "package_id": package_id,
            "resource_id": resource_id,
            "resource_url": resource_url
        }
        
        # Provenance
        provenance = {
            "source": "NASA Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "NASA Public Domain",
            "api_version": "CKAN"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )
