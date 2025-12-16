"""PubMed/NCBI connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class PubMedConnector(BaseConnector):
    """Connector for PubMed/NCBI API."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self):
        super().__init__("pubmed")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate PubMed query."""
        return "term" in query or "pmid" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from PubMed API.
        
        Query format:
        {
            "term": "covid-19 vaccine",  # Search term
            "retmax": 100,  # Max results
            "retstart": 0,  # Start index
            "retmode": "xml"  # Response format
        }
        OR
        {
            "pmid": "12345678,87654321",  # Specific PMIDs
            "retmode": "xml"
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing term or pmid")
        
        retmax = query.get("retmax", 100)
        retstart = query.get("retstart", 0)
        retmode = query.get("retmode", "xml")
        
        records = []
        
        if "pmid" in query:
            # Fetch specific articles by PMID
            pmids = query["pmid"]
            if isinstance(pmids, str):
                pmids = pmids.split(",")
            
            # Fetch article details
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(str(pmid).strip() for pmid in pmids),
                "retmode": retmode
            }
            
            response = make_request_with_retry(self.client, "GET", fetch_url, params=params)
            
            # Parse XML response (simplified)
            # In production, use proper XML parser
            content = response.text
            records = self._parse_pubmed_xml(content)
        
        elif "term" in query:
            # Search and fetch
            term = query["term"]
            
            # First, search to get PMIDs
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": term,
                "retmax": retmax,
                "retstart": retstart,
                "retmode": "json"
            }
            
            search_response = make_request_with_retry(self.client, "GET", search_url, params=search_params)
            search_data = search_response.json()
            
            # Get PMIDs
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if pmids:
                # Fetch article details
                fetch_url = f"{self.BASE_URL}/efetch.fcgi"
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": retmode
                }
                
                fetch_response = make_request_with_retry(self.client, "GET", fetch_url, params=fetch_params)
                
                content = fetch_response.text
                records = self._parse_pubmed_xml(content)
        
        # Metadata
        metadata = {
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "query": query
        }
        
        # Provenance
        provenance = {
            "source": "PubMed/NCBI",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "license": "PubMed Open Access",
            "api_version": "eutils"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )
    
    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response (simplified).
        
        In production, use proper XML parser like lxml or xml.etree.
        """
        records = []
        
        # Simplified parsing - in production use proper XML parser
        # For now, return basic structure
        import re
        
        # Extract PMIDs
        pmids = re.findall(r'<PMID[^>]*>(\d+)</PMID>', xml_content)
        
        # Extract titles
        titles = re.findall(r'<ArticleTitle[^>]*>(.*?)</ArticleTitle>', xml_content, re.DOTALL)
        
        # Extract abstracts
        abstracts = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml_content, re.DOTALL)
        
        # Extract publication dates
        years = re.findall(r'<PubDate>.*?<Year>(\d+)</Year>', xml_content, re.DOTALL)
        
        # Combine into records
        for i, pmid in enumerate(pmids):
            record = {
                "pmid": pmid,
                "title": titles[i].strip() if i < len(titles) else "",
                "abstract": abstracts[i].strip() if i < len(abstracts) else "",
                "year": years[i] if i < len(years) else "",
            }
            records.append(record)
        
        return records

