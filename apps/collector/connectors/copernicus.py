"""Copernicus Climate Data Store connector."""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput


class CopernicusConnector(BaseConnector):
    """
    Connector for Copernicus Climate Data Store API.
    
    Supports two authentication methods:
    
    1. CDS (Climate Data Store) - Uses official ECMWF Data Stores Client:
       - Set ECMWF_DATASTORES_URL and ECMWF_DATASTORES_KEY environment variables, OR
       - Create ~/.ecmwfdatastoresrc file with:
           url: https://cds.climate.copernicus.eu/api
           key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    
    2. CDSE (Data Space Ecosystem) - Uses OAuth2 token:
       - Set COPERNICUS_CDSE_ACCESS_TOKEN environment variable
       - Or set COPERNICUS_CDSE_USERNAME and COPERNICUS_CDSE_PASSWORD to auto-generate token
       - Get token with: curl -d 'client_id=cdse-public' -d 'username=<user>' \
                         -d 'password=<pass>' -d 'grant_type=password' \
                         'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    """
    
    def __init__(self):
        super().__init__("copernicus")
        self._client = None
    
    def _get_client(self):
        """Get or create ECMWF Data Stores client."""
        if self._client is None:
            try:
                from ecmwf.datastores import Client
                
                # Try to get credentials from environment or config file
                url = os.getenv("ECMWF_DATASTORES_URL")
                key = os.getenv("ECMWF_DATASTORES_KEY")
                
                # If not in env, client will try to read from ~/.ecmwfdatastoresrc
                if url and key:
                    self._client = Client(url=url, key=key)
                else:
                    self._client = Client()
                
                # Optional: verify authentication
                try:
                    self._client.check_authentication()
                except Exception:
                    pass  # Authentication check failed, but continue anyway
                    
            except ImportError:
                raise ImportError(
                    "ecmwf-datastores-client is required for Copernicus connector. "
                    "Install with: pip install ecmwf-datastores-client"
                )
        return self._client
    
    def _get_cdse_token(self) -> Optional[str]:
        """
        Get Copernicus Data Space Ecosystem OAuth2 token.
        
        First tries to get from environment variable.
        If not found and username/password are available, generates token automatically.
        """
        # Try to get existing token first
        token = os.getenv("COPERNICUS_CDSE_ACCESS_TOKEN")
        if token:
            return token
        
        # If no token but username/password available, generate token
        username = os.getenv("COPERNICUS_CDSE_USERNAME")
        password = os.getenv("COPERNICUS_CDSE_PASSWORD")
        
        if username and password:
            try:
                import httpx
                import json
                
                client = httpx.Client(timeout=10.0)
                response = client.post(
                    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                    data={
                        "client_id": "cdse-public",
                        "username": username,
                        "password": password,
                        "grant_type": "password"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    return token
            except Exception:
                # If token generation fails, return None
                pass
        
        return None
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate Copernicus query."""
        return "collection_id" in query or "dataset" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from Copernicus Climate Data Store.
        
        Query format:
        {
            "collection_id": "reanalysis-era5-pressure-levels",  # or "dataset" (alias)
            "product_type": ["reanalysis"],
            "variable": ["temperature"],
            "year": ["2022"],
            "month": ["01"],
            "day": ["01"],
            "time": ["00:00"],
            "pressure_level": ["1000"],
            "data_format": "grib",
            "download_format": "unarchived"
        }
        
        OR for metadata only:
        {
            "collection_id": "reanalysis-era5-pressure-levels",
            "metadata_only": true
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing collection_id or dataset")
        
        try:
            client = self._get_client()
        except ImportError as e:
            # Return error record if client not available
            records = [{
                "error": str(e),
                "note": "Install ecmwf-datastores-client: pip install ecmwf-datastores-client"
            }]
            return ConnectorOutput(
                records=records,
                metadata={"row_count": 0, "columns": []},
                provenance={
                    "source": "Copernicus Climate Data Store",
                    "query": query,
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            )
        
        collection_id = query.get("collection_id") or query.get("dataset", "")
        metadata_only = query.get("metadata_only", False)
        
        records = []
        
        try:
            if metadata_only:
                # Get collection metadata only
                collection = client.get_collection(collection_id)
                records.append({
                    "collection_id": collection.id,
                    "title": collection.title,
                    "description": collection.description,
                    "published_at": str(collection.published_at) if hasattr(collection, 'published_at') else "",
                    "updated_at": str(collection.updated_at) if hasattr(collection, 'updated_at') else "",
                    "begin_datetime": str(collection.begin_datetime) if hasattr(collection, 'begin_datetime') else "",
                    "end_datetime": str(collection.end_datetime) if hasattr(collection, 'end_datetime') else "",
                    "bbox": collection.bbox if hasattr(collection, 'bbox') else None
                })
            else:
                # Build request from query (remove collection_id/dataset)
                request = query.copy()
                request.pop("collection_id", None)
                request.pop("dataset", None)
                request.pop("metadata_only", None)
                
                # Apply constraints to get available options
                constrained_request = client.apply_constraints(collection_id, request)
                
                # Get metadata about the request
                records.append({
                    "collection_id": collection_id,
                    "request": constrained_request,
                    "status": "request_prepared",
                    "note": "Use client.retrieve() or client.submit() to download data"
                })
                
        except Exception as e:
            records.append({
                "collection_id": collection_id,
                "error": str(e),
                "query": query
            })
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "collection_id": collection_id
        }
        
        # Provenance
        provenance = {
            "source": "Copernicus Climate Data Store",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "license": "Copernicus License",
            "api_version": "ECMWF Data Stores Client",
            "note": "Requires ECMWF_DATASTORES_URL and ECMWF_DATASTORES_KEY or ~/.ecmwfdatastoresrc"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

