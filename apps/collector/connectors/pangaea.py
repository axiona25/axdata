"""PANGAEA connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class PANGAEAConnector(BaseConnector):
    """Connector for PANGAEA Data Publisher."""
    
    BASE_URL = "https://ws.pangaea.de"
    
    def __init__(self):
        super().__init__("pangaea")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate PANGAEA query."""
        return "dataset_id" in query or "search" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from PANGAEA.
        
        Query format:
        {
            "dataset_id": "10.1594/PANGAEA.123456"
        }
        OR
        {
            "search": "climate change",
            "limit": 100
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset_id or search")
        
        records = []
        
        if "dataset_id" in query:
            # Fetch specific dataset
            dataset_id = query["dataset_id"]
            # Remove DOI prefix if present
            if dataset_id.startswith("10.1594/PANGAEA."):
                dataset_id = dataset_id.replace("10.1594/PANGAEA.", "")
            
            url = f"{self.BASE_URL}/oai/provider"
            params = {
                "verb": "GetRecord",
                "metadataPrefix": "pan_mcp",
                "identifier": f"oai:pangaea.de:doi/10.1594/PANGAEA.{dataset_id}"
            }
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            # Parse OAI-PMH XML response (simplified)
            # In production, use proper XML parser
            content = response.text
            records = self._parse_pangaea_xml(content, dataset_id)
        
        elif "search" in query:
            # Search datasets
            search_term = query["search"]
            limit = query.get("limit", 100)
            
            url = f"{self.BASE_URL}/oai/provider"
            # Try different metadataPrefix if pan_mcp doesn't work
            metadata_prefixes = ["pan_mcp", "oai_dc", "datacite"]
            records = []
            
            for prefix in metadata_prefixes:
                params = {
                    "verb": "ListRecords",
                    "metadataPrefix": prefix,
                    "from": "2020-01-01"  # Add from date to limit results
                }
                
                try:
                    response = make_request_with_retry(self.client, "GET", url, params=params)
                    content = response.text
                    
                    # Check for errors in XML
                    if "<error" in content.lower():
                        continue  # Try next prefix
                    
                    # Parse OAI-PMH XML response
                    parsed_records = self._parse_pangaea_search_xml(content, limit)
                    if parsed_records:
                        records = parsed_records
                        break
                except:
                    continue  # Try next prefix
            
            # If still no records, try to extract identifiers anyway
            if not records:
                try:
                    response = make_request_with_retry(self.client, "GET", url, params={
                        "verb": "ListIdentifiers",
                        "metadataPrefix": "oai_dc"
                    })
                    content = response.text
                    records = self._parse_pangaea_search_xml(content, limit)
                except:
                    pass
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "PANGAEA",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "PANGAEA Data License",
            "api_version": "OAI-PMH"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )
    
    def _parse_pangaea_xml(self, xml_content: str, dataset_id: str) -> List[Dict[str, Any]]:
        """Parse PANGAEA XML response."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            records = []
            # PANGAEA OAI-PMH structure
            # Find all record elements
            for record in root.findall('.//{http://www.openarchives.org/OAI/2.0/}record'):
                metadata = record.find('.//{http://www.openarchives.org/OAI/2.0/}metadata')
                if metadata is not None:
                    # Extract dataset info
                    dataset_info = {}
                    # Try to find common fields
                    for elem in metadata.iter():
                        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        text = elem.text if elem.text else ""
                        if text.strip():
                            dataset_info[tag] = text.strip()
                    
                    if dataset_info:
                        dataset_info['dataset_id'] = dataset_id
                        records.append(dataset_info)
            
            return records if records else []
        except Exception as e:
            # Fallback to simple regex parsing
            import re
            records = []
            
            # Extract basic metadata
        title_match = re.search(r'<dc:title[^>]*>(.*?)</dc:title>', xml_content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        
        creator_match = re.search(r'<dc:creator[^>]*>(.*?)</dc:creator>', xml_content, re.DOTALL)
        creator = creator_match.group(1).strip() if creator_match else ""
        
        date_match = re.search(r'<dc:date[^>]*>(.*?)</dc:date>', xml_content, re.DOTALL)
        date = date_match.group(1).strip() if date_match else ""
        
        record = {
            "dataset_id": dataset_id,
            "title": title,
            "creator": creator,
            "date": date
        }
        records.append(record)
        
        return records
    
    def _parse_pangaea_search_xml(self, xml_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse PANGAEA search XML response (simplified)."""
        import re
        
        records = []
        
        # Extract all record identifiers
        identifiers = re.findall(r'<identifier[^>]*>(.*?)</identifier>', xml_content)
        
        for identifier in identifiers[:limit]:
            # Extract dataset ID from identifier
            dataset_id_match = re.search(r'PANGAEA\.(\d+)', identifier)
            dataset_id = dataset_id_match.group(1) if dataset_id_match else ""
            
            if dataset_id:
                record = {
                    "dataset_id": dataset_id,
                    "identifier": identifier
                }
                records.append(record)
        
        return records

