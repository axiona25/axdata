"""EU Clinical Trials Register connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class EUClinicalTrialsConnector(BaseConnector):
    """Connector for EU Clinical Trials Register."""
    
    BASE_URL = "https://www.clinicaltrialsregister.eu/ctr-search/search"
    
    def __init__(self):
        super().__init__("eu_clinical_trials")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate EU Clinical Trials query."""
        return "query" in query or "eudract_number" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from EU Clinical Trials Register.
        
        Query format:
        {
            "query": "covid-19",
            "limit": 100
        }
        OR
        {
            "eudract_number": "2020-001234-56"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing query or eudract_number")
        
        records = []
        
        if "eudract_number" in query:
            # Fetch specific trial
            eudract_number = query["eudract_number"]
            url = f"{self.BASE_URL}"
            params = {
                "query": eudract_number,
                "page": 1
            }
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            # EU Clinical Trials Register uses HTML, so we need to parse it
            # This is a simplified version - full implementation may require HTML parsing
            content = response.text
            records = self._parse_eu_trials_html(content, eudract_number)
        
        elif "query" in query:
            # Search trials
            search_query = query["query"]
            limit = query.get("limit", 100)
            
            url = f"{self.BASE_URL}"
            params = {
                "query": search_query,
                "page": 1
            }
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            content = response.text
            records = self._parse_eu_trials_search_html(content, limit)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "EU Clinical Trials Register",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "EU Clinical Trials Register Public Data",
            "api_version": "Web",
            "note": "EU Clinical Trials Register uses web interface, parsing may be limited"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )
    
    def _parse_eu_trials_html(self, html_content: str, eudract_number: str) -> List[Dict[str, Any]]:
        """Parse EU Clinical Trials HTML response (simplified)."""
        import re
        
        records = []
        
        # Extract basic information (simplified parsing)
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        
        record = {
            "eudract_number": eudract_number,
            "title": title,
            "status": "retrieved",
            "note": "Full parsing requires HTML parser (BeautifulSoup, etc.)"
        }
        records.append(record)
        
        return records
    
    def _parse_eu_trials_search_html(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse EU Clinical Trials search HTML response (improved)."""
        import re
        
        records = []
        
        # Try multiple patterns for EudraCT numbers
        # Pattern 1: EudraCT Number: XXXX-XXXXXX-XX (most common format)
        pattern1 = r'<span[^>]*class="label"[^>]*>EudraCT\s+Number:</span>\s*(\d{4}-\d{6}-\d{2})'
        # Pattern 2: EudraCT Number: XXXX-XXXXXX-XX (without HTML tags)
        pattern2 = r'EudraCT\s+Number[:\s]+(\d{4}-\d{6}-\d{2})'
        # Pattern 3: Just the number format (be careful with this one)
        pattern3 = r'\b(\d{4}-\d{6}-\d{2})\b'
        
        eudract_numbers = set()
        
        # Try pattern 1 first (most specific, from HTML structure)
        matches = re.findall(pattern1, html_content, re.IGNORECASE)
        eudract_numbers.update(matches)
        
        # Try pattern 2
        if len(eudract_numbers) < limit:
            matches2 = re.findall(pattern2, html_content, re.IGNORECASE)
            eudract_numbers.update(matches2)
        
        # Try pattern 3 only if we haven't found enough
        if len(eudract_numbers) < limit:
            matches3 = re.findall(pattern3, html_content)
            # Filter to match EudraCT format (4-6-2 digits)
            for match in matches3:
                if len(match) == 13 and match.count('-') == 2:
                    parts = match.split('-')
                    if len(parts[0]) == 4 and len(parts[1]) == 6 and len(parts[2]) == 2:
                        # Additional validation: check if it looks like a valid EudraCT number
                        # Usually starts with year (2000-2099)
                        year = int(parts[0])
                        if 2000 <= year <= 2099:
                            eudract_numbers.add(match)
        
        # Extract trial titles if possible (look for common patterns)
        titles = re.findall(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
        title = titles[0].strip() if titles else ""
        
        # Create records
        eudract_list = list(eudract_numbers)[:limit]
        for eudract_number in eudract_list:
            record = {
                "eudract_number": eudract_number,
                "title": title if len(eudract_list) == 1 else "",
                "status": "found",
                "source": "EU Clinical Trials Register"
            }
            records.append(record)
        
        # If no numbers found but we got a response, return at least one record with metadata
        if not records:
            record = {
                "query": "covid-19",
                "status": "search_completed",
                "note": "EudraCT numbers could not be extracted from HTML. Full parsing may require HTML parser library.",
                "source": "EU Clinical Trials Register"
            }
            records.append(record)
        
        return records

