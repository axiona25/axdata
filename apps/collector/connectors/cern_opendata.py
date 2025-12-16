"""CERN Open Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class CERNOpenDataConnector(BaseConnector):
    """Connector for CERN Open Data Portal."""
    
    BASE_URL = "https://opendata.cern.ch/api"
    
    def __init__(self):
        super().__init__("cern_opendata")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate CERN Open Data query."""
        return "experiment" in query or "dataset_id" in query or "search" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from CERN Open Data Portal.
        
        Query format:
        {
            "experiment": "CMS",
            "search": "Higgs",
            "limit": 100
        }
        OR
        {
            "dataset_id": "12345"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing experiment, dataset_id, or search")
        
        records = []
        
        if "dataset_id" in query:
            # Fetch specific dataset
            dataset_id = query["dataset_id"]
            url = f"{self.BASE_URL}/records/{dataset_id}"
            
            response = make_request_with_retry(self.client, "GET", url)
            data = response.json()
            
            if "metadata" in data:
                metadata_obj = data["metadata"]
                record = {
                    "dataset_id": dataset_id,
                    "title": metadata_obj.get("title", ""),
                    "experiment": metadata_obj.get("experiment", ""),
                    "year": metadata_obj.get("year", ""),
                    "collision_energy": metadata_obj.get("collision_energy", ""),
                    "collision_type": metadata_obj.get("collision_type", ""),
                    "doi": metadata_obj.get("doi", ""),
                    "license": metadata_obj.get("license", ""),
                    "files": len(metadata_obj.get("files", []))
                }
                records.append(record)
        
        elif "experiment" in query or "search" in query:
            # Search datasets
            experiment = query.get("experiment", "")
            search_term = query.get("search", "")
            limit = query.get("limit", 100)
            
            url = f"{self.BASE_URL}/records"
            params = {
                "size": limit,
                "format": "json"
            }
            
            if experiment:
                params["experiment"] = experiment
            if search_term:
                params["q"] = search_term
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            data = response.json()
            
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                source = hit.get("_source", {})
                metadata_obj = source.get("metadata", {})
                record = {
                    "dataset_id": hit.get("_id", ""),
                    "title": metadata_obj.get("title", ""),
                    "experiment": metadata_obj.get("experiment", ""),
                    "year": metadata_obj.get("year", ""),
                    "collision_energy": metadata_obj.get("collision_energy", ""),
                    "doi": metadata_obj.get("doi", "")
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
            "source": "CERN Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "CERN Open Data License",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

