"""UN Population Division connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class UNPopulationConnector(BaseConnector):
    """Connector for UN Population Division API."""
    
    BASE_URL = "https://population.un.org/dataportalapi/api/v1"
    
    def __init__(self):
        super().__init__("un_population")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate UN Population query."""
        return "indicator" in query or "location" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from UN Population Division API.
        
        Query format:
        {
            "indicator": "SP_POP_TOTL",  # Total population
            "location": "840;250;380",  # Country codes (USA, FRA, ITA)
            "start_year": 2000,
            "end_year": 2024
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing indicator or location")
        
        indicator = query.get("indicator", "")
        location = query.get("location", query.get("country", "all"))
        start_year = query.get("start_year", query.get("year", 2000))
        end_year = query.get("end_year", query.get("year", 2024))
        
        # Convert indicator format if needed (SP.POP.TOTL -> SP_POP_TOTL)
        if "." in indicator:
            indicator = indicator.replace(".", "_")
        elif indicator.startswith("SP_POP_TOTL"):
            pass  # Already correct
        else:
            # Try to map common indicators
            indicator_map = {
                "SP.POP.TOTL": "SP_POP_TOTL",
                "SP_POP_TOTL": "SP_POP_TOTL"
            }
            indicator = indicator_map.get(indicator, indicator)
        
        # UN Population Division API
        url = f"{self.BASE_URL}/data/indicators/{indicator}"
        params = {
            "startYear": start_year,
            "endYear": end_year
        }
        
        if location != "all":
            # UN Population uses numeric location codes (840 for USA)
            params["locations"] = location
        
        # Fetch data with retry
        try:
            response = make_request_with_retry(self.client, "GET", url, params=params)
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                # Try to parse anyway
                data = response.json() if response.text else {}
        except Exception as e:
            # If UN Population endpoint fails, return metadata
            records = [{
                "indicator": indicator,
                "location": location or "all",
                "start_year": start_year,
                "end_year": end_year,
                "status": "endpoint_error",
                "note": f"UN Population Division API error. Indicator '{indicator}' may not exist or endpoint may have changed. Error: {str(e)}"
            }]
            metadata = {
                "row_count": len(records),
                "columns": list(records[0].keys()) if records else [],
                "indicator": indicator,
                "location": location
            }
            provenance = {
                "source": "UN Population Division",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": url,
                "license": "UN Data License",
                "api_version": "v1",
                "note": f"Endpoint error: {str(e)}"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        # Parse UN Population response
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "data" in data:
            records = data["data"]
        elif isinstance(data, dict) and "results" in data:
            records = data["results"]
        elif isinstance(data, dict) and "value" in data:
            # Single value response
            records = [data]
        
        # Transform to standard format
        transformed_records = []
        for record in records:
            if isinstance(record, dict):
                transformed_records.append({
                    "location": record.get("Location", record.get("location", "")),
                    "location_code": record.get("LocID", record.get("location_code", "")),
                    "indicator": indicator,
                    "year": record.get("Time", record.get("year", "")),
                    "value": record.get("Value", record.get("value", "")),
                    "sex": record.get("Sex", record.get("sex", "")),
                    "age_group": record.get("AgeGrp", record.get("age_group", ""))
                })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "indicator": indicator,
            "location": location
        }
        
        # Provenance
        provenance = {
            "source": "UN Population Division",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "UN Data License",
            "api_version": "v1"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

