"""NOAA Open Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class NOAAConnector(BaseConnector):
    """Connector for NOAA Open Data API."""
    
    BASE_URL = "https://www.ncei.noaa.gov/data"
    
    def __init__(self):
        super().__init__("noaa")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate NOAA query."""
        return "dataset" in query or "station" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from NOAA Open Data API.
        
        Query format:
        {
            "dataset": "global-summary-of-the-day",
            "station": "USW00094728",
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "datatype": "TMAX;TMIN;PRCP"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset or station")
        
        dataset = query.get("dataset", "")
        station = query.get("station", "")
        start_date = query.get("start_date", "")
        end_date = query.get("end_date", "")
        datatype = query.get("datatype", "")
        
        # Build URL - NOAA uses different endpoint
        if station:
            # Use the correct NOAA API endpoint
            url = "https://www.ncei.noaa.gov/access/services/data/v1"
            params = {
                "dataset": dataset or "daily-summaries",
                "stations": station,
                "format": "json"
            }
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
            if datatype:
                params["dataTypes"] = datatype.replace(";", ",") if ";" in datatype else datatype
        else:
            url = f"{self.BASE_URL}/{dataset}/access"
            params = {}
            if start_date:
                params["startdate"] = start_date
            if end_date:
                params["enddate"] = end_date
            if datatype:
                params["datatype"] = datatype
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Parse NOAA response
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "results" in data:
            records = data["results"]
        elif isinstance(data, dict):
            # Single record
            records = [data]
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                # NOAA API returns fields in uppercase
                transformed_records.append({
                    "station": record.get("STATION", record.get("station", station)),
                    "date": record.get("DATE", record.get("date", "")),
                    "tmax": record.get("TMAX", record.get("tmax", "")),
                    "tmin": record.get("TMIN", record.get("tmin", "")),
                    "prcp": record.get("PRCP", record.get("prcp", "")),
                    "datatype": record.get("DATATYPE", record.get("datatype", "")),
                    "value": record.get("VALUE", record.get("value", "")),
                    "dataset": dataset or "daily-summaries"
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "dataset": dataset,
            "station": station
        }
        
        # Provenance
        provenance = {
            "source": "NOAA Open Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "NOAA Public Domain",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

