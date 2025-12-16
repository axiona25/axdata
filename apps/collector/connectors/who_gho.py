"""WHO Global Health Observatory (GHO) connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class WHOGHOConnector(BaseConnector):
    """Connector for WHO Global Health Observatory API."""
    
    BASE_URL = "https://ghoapi.azureedge.net/api"
    
    def __init__(self):
        super().__init__("who_gho")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate WHO GHO query."""
        return "indicator" in query or "dimension" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from WHO GHO API.
        
        Query format:
        {
            "indicator": "WHOSIS_000001",  # Life expectancy
            "country": "USA;FRA;ITA",
            "year": "2020"
        }
        OR
        {
            "dimension": "GHO",
            "filter": "COUNTRY:USA;YEAR:2020"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing indicator or dimension")
        
        records = []
        
        if "indicator" in query:
            # Fetch by indicator
            indicator = query["indicator"]
            country = query.get("country", "")
            year = query.get("year", "")
            
            url = f"{self.BASE_URL}/{indicator}"
            params = {
                "$top": 100  # Limit results
            }
            
            # WHO GHO uses OData format
            if country:
                params["$filter"] = f"COUNTRY eq '{country}'"
            if year:
                if "$filter" in params:
                    params["$filter"] += f" and YEAR eq '{year}'"
                else:
                    params["$filter"] = f"YEAR eq '{year}'"
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            data = response.json()
            
            records = data.get("value", [])
        
        elif "dimension" in query:
            # Fetch by dimension
            dimension = query["dimension"]
            filter_str = query.get("filter", "")
            
            url = f"{self.BASE_URL}/{dimension}"
            params = {}
            
            if filter_str:
                params["$filter"] = filter_str
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            data = response.json()
            
            records = data.get("value", [])
        
        # Transform records to standard format
        transformed_records = []
        for record in records:
            transformed_records.append({
                "indicator": record.get("Indicator", record.get("GHO", "")),
                "country": record.get("COUNTRY", ""),
                "country_code": record.get("COUNTRYCODE", ""),
                "year": record.get("YEAR", record.get("YEARCODE", "")),
                "value": record.get("Value", record.get("NumericValue", "")),
                "sex": record.get("SEX", ""),
                "age_group": record.get("AGEGROUP", "")
            })
        
        # Metadata
        metadata = {
            "row_count": len(transformed_records),
            "columns": list(transformed_records[0].keys()) if transformed_records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "WHO Global Health Observatory",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "WHO Data License",
            "api_version": "REST"
        }
        
        return ConnectorOutput(
            records=transformed_records,
            metadata=metadata,
            provenance=provenance
        )

