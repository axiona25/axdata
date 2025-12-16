"""ClinicalTrials.gov connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class ClinicalTrialsConnector(BaseConnector):
    """Connector for ClinicalTrials.gov API."""
    
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    def __init__(self):
        super().__init__("clinicaltrials")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate ClinicalTrials query."""
        return "query" in query or "nct_id" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from ClinicalTrials.gov API.
        
        Query format:
        {
            "query": "covid-19 vaccine",
            "pageSize": 100,
            "pageToken": ""
        }
        OR
        {
            "nct_id": "NCT12345678"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing query or nct_id")
        
        records = []
        
        if "nct_id" in query:
            # Fetch specific trial
            nct_id = query["nct_id"]
            url = f"{self.BASE_URL}/studies/{nct_id}"
            
            response = make_request_with_retry(self.client, "GET", url)
            data = response.json()
            
            if "protocolSection" in data:
                trial = data["protocolSection"]
                record = {
                    "nct_id": nct_id,
                    "title": trial.get("identificationModule", {}).get("briefTitle", ""),
                    "official_title": trial.get("identificationModule", {}).get("officialTitle", ""),
                    "status": trial.get("statusModule", {}).get("overallStatus", ""),
                    "phase": trial.get("designModule", {}).get("phases", []),
                    "conditions": [c.get("name", "") for c in trial.get("conditionsModule", {}).get("conditions", [])],
                    "interventions": [i.get("name", "") for i in trial.get("armsInterventionsModule", {}).get("interventions", [])],
                    "enrollment": trial.get("designModule", {}).get("enrollmentInfo", {}).get("count", 0),
                    "start_date": trial.get("statusModule", {}).get("startDateStruct", {}).get("date", ""),
                    "completion_date": trial.get("statusModule", {}).get("completionDateStruct", {}).get("date", "")
                }
                records.append(record)
        
        elif "query" in query:
            # Search trials
            search_query = query["query"]
            page_size = query.get("pageSize", 100)
            page_token = query.get("pageToken", "")
            
            url = f"{self.BASE_URL}/studies"
            params = {
                "query.term": search_query,
                "pageSize": page_size,
                "format": "json"
            }
            
            if page_token:
                params["pageToken"] = page_token
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                data = response.json()
            else:
                # Try to parse as JSON anyway
                try:
                    data = response.json()
                except:
                    data = {}
            
            # Handle different response formats
            if isinstance(data, dict):
                studies = data.get("studies", [])
            elif isinstance(data, list):
                studies = data
            else:
                studies = []
            for study in studies:
                if not isinstance(study, dict):
                    continue
                    
                protocol = study.get("protocolSection", {})
                if not isinstance(protocol, dict):
                    continue
                
                ident_module = protocol.get("identificationModule", {})
                status_module = protocol.get("statusModule", {})
                design_module = protocol.get("designModule", {})
                conditions_module = protocol.get("conditionsModule", {})
                
                record = {
                    "nct_id": ident_module.get("nctId", "") if isinstance(ident_module, dict) else "",
                    "title": ident_module.get("briefTitle", "") if isinstance(ident_module, dict) else "",
                    "status": status_module.get("overallStatus", "") if isinstance(status_module, dict) else "",
                    "phase": design_module.get("phases", []) if isinstance(design_module, dict) else [],
                    "conditions": [c.get("name", "") for c in conditions_module.get("conditions", []) if isinstance(c, dict)] if isinstance(conditions_module, dict) else [],
                    "enrollment": design_module.get("enrollmentInfo", {}).get("count", 0) if isinstance(design_module, dict) and isinstance(design_module.get("enrollmentInfo"), dict) else 0
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
            "source": "ClinicalTrials.gov",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "ClinicalTrials.gov Public Domain",
            "api_version": "v2"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

