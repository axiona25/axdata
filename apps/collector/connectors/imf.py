"""IMF (International Monetary Fund) Data connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class IMFConnector(BaseConnector):
    """Connector for IMF Data API (SDMX)."""
    
    BASE_URL = "https://www.imf.org/external/datamapper/api/v1"
    
    def __init__(self):
        super().__init__("imf")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate IMF query."""
        return "dataset" in query or "indicator" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from IMF Data API.
        
        Query format:
        {
            "dataset": "IFS",  # International Financial Statistics
            "indicator": "NGDP_R_SA_XDC",  # Real GDP
            "country": "US;FR;IT",
            "start_period": "2000",
            "end_period": "2024"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset or indicator")
        
        dataset = query.get("dataset", "IFS")
        indicator = query.get("indicator", "")
        country = query.get("country", "all")
        start_period = query.get("start_period", "2000")
        end_period = query.get("end_period", "2024")
        
        # IMF uses DataMapper API v1 (REST API)
        # Try new API endpoint: /api/v1/{indicator}/{country}
        if indicator and country != "all":
            # Format: /api/v1/{indicator}/{country}
            # Country code should be ISO 3166-1 alpha-2 (e.g., US, FR, IT)
            # Replace semicolon separator with comma for multiple countries
            countries = country.replace(";", ",") if ";" in country else country
            url = f"{self.BASE_URL}/{indicator}/{countries}"
            params = {}
        elif indicator:
            # Indicator only - get all countries
            url = f"{self.BASE_URL}/{indicator}"
            params = {}
        else:
            # Fallback - try to list available dataflows
            # For now, return empty with note
            records = []
            metadata = {
                "row_count": 0,
                "columns": [],
                "dataset": dataset,
                "indicator": indicator,
                "country": country,
                "note": "IMF query requires indicator. Please provide an indicator code."
            }
            provenance = {
                "source": "IMF Data",
                "query": query,
                "retrieved_at": datetime.utcnow().isoformat(),
                "url": "",
                "license": "IMF Data License",
                "api_version": "SDMX",
                "note": "Indicator required"
            }
            return ConnectorOutput(
                records=records,
                metadata=metadata,
                provenance=provenance
            )
        
        # Fetch data with retry
        response = make_request_with_retry(self.client, "GET", url, params=params)
        
        data = response.json()
        
        # Parse IMF DataMapper API response
        records = []
        # IMF DataMapper returns structure like:
        # { "values": { "country_code": [{"date": "2020", "value": 123.45}, ...] } }
        if isinstance(data, dict):
            # Check if it's the DataMapper format
            if "values" in data:
                values_dict = data["values"]
                for country_code, data_list in values_dict.items():
                    if isinstance(data_list, list):
                        for entry in data_list:
                            record = {
                                "country": country_code,
                                "period": entry.get("date", ""),
                                "value": entry.get("value"),
                                "indicator": indicator,
                                "dataset": dataset
                            }
                            records.append(record)
            # Alternative: check if data is already a list
            elif isinstance(data, list):
                records = data
            # Check for SDMX format (fallback)
            elif "dataSets" in data and len(data["dataSets"]) > 0:
                dataset_data = data["dataSets"][0]
                series = dataset_data.get("series", {})
                
                for series_key, series_values in series.items():
                    observations = series_values.get("observations", {})
                    
                    for obs_key, obs_value in observations.items():
                        record = {
                            "series_key": series_key,
                            "period": obs_key,
                            "value": obs_value[0] if isinstance(obs_value, list) else obs_value,
                            "dataset": dataset,
                            "indicator": indicator
                        }
                        records.append(record)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "dataset": dataset,
            "indicator": indicator,
            "country": country
        }
        
        # Provenance
        provenance = {
            "source": "IMF Data",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url),
            "license": "IMF Data License",
            "api_version": "SDMX"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

