"""ESA Open Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class ESAConnector(BaseConnector):
    """Connector for ESA Open Data Portal."""
    
    BASE_URL = "https://eogateway.esa.int"
    
    def __init__(self):
        super().__init__("esa")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate ESA query."""
        return "dataset" in query or "mission" in query or "search" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from ESA Open Data Portal.
        
        Query format:
        {
            "mission": "Sentinel-2",
            "search": "NDVI",
            "limit": 100
        }
        OR
        {
            "dataset": "S2A_MSIL1C_20200101T100031_N0208_R122_T33TUM_20200101T120046"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset, mission, or search")
        
        records = []
        
        if "dataset" in query:
            # Fetch specific dataset
            dataset_id = query["dataset"]
            url = f"{self.BASE_URL}/datasets/{dataset_id}"
            
            response = make_request_with_retry(self.client, "GET", url)
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            
            record = {
                "dataset_id": dataset_id,
                "title": data.get("title", ""),
                "mission": data.get("mission", ""),
                "platform": data.get("platform", ""),
                "instrument": data.get("instrument", ""),
                "acquisition_date": data.get("acquisition_date", ""),
                "cloud_cover": data.get("cloud_cover", ""),
                "footprint": data.get("footprint", "")
            }
            records.append(record)
        
        elif "mission" in query or "search" in query:
            # Search datasets - ESA uses eogateway portal
            mission = query.get("mission", "")
            search_term = query.get("search", "")
            limit = query.get("limit", 100)
            
            # ESA eogateway uses search endpoint via web interface
            # Since direct API may not be publicly available, return metadata
            url = f"{self.BASE_URL}/search"
            params = {}
            if mission:
                params["category"] = "data"
                # Try to construct search URL
                search_url = f"{self.BASE_URL}/search?category=data"
                if mission:
                    search_url += f"&mission={mission}"
                if search_term:
                    search_url += f"&query={search_term}"
            else:
                search_url = url
            
            try:
                response = make_request_with_retry(self.client, "GET", search_url, params=params)
                # If response is HTML (likely), extract basic info
                if "text/html" in response.headers.get("content-type", ""):
                    # Return metadata record indicating web interface
                    record = {
                        "mission": mission or "various",
                        "search_term": search_term or "",
                        "status": "web_interface_available",
                        "search_url": search_url,
                        "note": "ESA eogateway uses web interface. Direct API access may require authentication."
                    }
                    records.append(record)
                else:
                    # Try JSON response
                    data = response.json()
                    results = data.get("results", data.get("features", []))
                    for result in results[:limit]:
                        properties = result.get("properties", result)
                        record = {
                            "dataset_id": result.get("id", properties.get("identifier", "")),
                            "title": properties.get("title", ""),
                            "mission": properties.get("mission", mission),
                            "acquisition_date": properties.get("acquisition_date", ""),
                            "cloud_cover": properties.get("cloud_cover", "")
                        }
                        records.append(record)
            except Exception:
                # If request fails, return metadata
                record = {
                    "mission": mission or "various",
                    "search_term": search_term or "",
                    "status": "api_not_available",
                    "note": "ESA eogateway may require authentication or use web interface only."
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
            "source": "ESA Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "ESA Data License",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

