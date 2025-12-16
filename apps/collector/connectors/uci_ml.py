"""UCI Machine Learning Repository connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class UCIMLConnector(BaseConnector):
    """Connector for UCI ML Repository.
    
    Note: UCI ML Repository doesn't have an official API.
    This connector provides a structured interface for accessing
    dataset metadata and download links.
    """
    
    BASE_URL = "https://archive.ics.uci.edu"
    
    def __init__(self):
        super().__init__("uci_ml")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate UCI ML query."""
        return "dataset" in query or "search" in query or "dataset_id" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from UCI ML Repository.
        
        Query format:
        {
            "dataset": "iris",
            "dataset_id": "53"
        }
        OR
        {
            "search": "classification",
            "limit": 100
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset, dataset_id, or search")
        
        records = []
        
        if "dataset_id" in query or "dataset" in query:
            # Fetch specific dataset metadata
            dataset_id = query.get("dataset_id", "")
            dataset_name = query.get("dataset", "")
            
            # UCI ML Repository uses HTML pages
            # This is a simplified version - full implementation may require HTML parsing
            if dataset_id:
                url = f"{self.BASE_URL}/ml/datasets.php?task=download&format=xml&id={dataset_id}"
            elif dataset_name:
                url = f"{self.BASE_URL}/ml/datasets/{dataset_name}"
            else:
                raise ValueError("Either dataset_id or dataset name required")
            
            response = make_request_with_retry(self.client, "GET", url)
            
            # Parse response (may be HTML or XML)
            content = response.text
            records = self._parse_uci_dataset(content, dataset_id or dataset_name)
        
        elif "search" in query:
            # Search datasets
            search_term = query["search"]
            limit = query.get("limit", 100)
            
            # UCI ML Repository search page
            url = f"{self.BASE_URL}/ml/datasets.php"
            params = {
                "task": "search",
                "query": search_term
            }
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            content = response.text
            records = self._parse_uci_search(content, limit)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "UCI Machine Learning Repository",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "UCI ML Repository License",
            "api_version": "Web",
            "note": "UCI ML Repository uses web interface, parsing may be limited"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )
    
    def _parse_uci_dataset(self, content: str, dataset_identifier: str) -> List[Dict[str, Any]]:
        """Parse UCI ML dataset page (simplified)."""
        import re
        
        records = []
        
        # Extract basic metadata (simplified parsing)
        # Full implementation would use HTML parser like BeautifulSoup
        
        name_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
        name = name_match.group(1).strip() if name_match else dataset_identifier
        
        # Extract number of instances
        instances_match = re.search(r'Number of Instances[^:]*:\s*(\d+)', content, re.IGNORECASE)
        instances = instances_match.group(1) if instances_match else ""
        
        # Extract number of attributes
        attributes_match = re.search(r'Number of Attributes[^:]*:\s*(\d+)', content, re.IGNORECASE)
        attributes = attributes_match.group(1) if attributes_match else ""
        
        record = {
            "dataset_id": dataset_identifier,
            "name": name,
            "number_of_instances": instances,
            "number_of_attributes": attributes,
            "status": "metadata_retrieved",
            "note": "Full parsing requires HTML parser (BeautifulSoup, etc.)"
        }
        records.append(record)
        
        return records
    
    def _parse_uci_search(self, content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse UCI ML search results (simplified)."""
        import re
        
        records = []
        
        # Extract dataset links (simplified)
        dataset_links = re.findall(r'href="datasets\.php\?task=download[^"]*id=(\d+)"', content)
        
        for dataset_id in dataset_links[:limit]:
            record = {
                "dataset_id": dataset_id,
                "status": "found",
                "note": "Full parsing requires HTML parser"
            }
            records.append(record)
        
        return records

