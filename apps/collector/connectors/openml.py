"""OpenML connector."""
import httpx
from typing import Dict, Any, List
from datetime import datetime
from connectors.base import BaseConnector, ConnectorOutput
from client.http_client import get_client, make_request_with_retry


class OpenMLConnector(BaseConnector):
    """Connector for OpenML API."""
    
    BASE_URL = "https://www.openml.org/api/v1"
    
    def __init__(self):
        super().__init__("openml")
        self.client = get_client()
    
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """Validate OpenML query."""
        return "dataset_id" in query or "search" in query
    
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from OpenML API.
        
        Query format:
        {
            "dataset_id": "12345"
        }
        OR
        {
            "search": "classification",
            "limit": 100,
            "offset": 0
        }
        """
        if not self.validate_query(query):
            raise ValueError("Invalid query: missing dataset_id or search")
        
        records = []
        
        if "dataset_id" in query:
            # Fetch specific dataset
            dataset_id = query["dataset_id"]
            url = f"{self.BASE_URL}/data/{dataset_id}"
            
            response = make_request_with_retry(self.client, "GET", url)
            data = response.json()
            
            # Get dataset metadata
            record = {
                "dataset_id": dataset_id,
                "name": data.get("name", ""),
                "version": data.get("version", ""),
                "description": data.get("description", ""),
                "format": data.get("format", ""),
                "upload_date": data.get("upload_date", ""),
                "licence": data.get("licence", ""),
                "url": data.get("url", ""),
                "file_id": data.get("file_id", ""),
                "default_target_attribute": data.get("default_target_attribute", ""),
                "row_id_attribute": data.get("row_id_attribute", ""),
                "ignore_attribute": data.get("ignore_attribute", []),
                "version_label": data.get("version_label", ""),
                "citation": data.get("citation", ""),
                "visibility": data.get("visibility", ""),
                "original_data_url": data.get("original_data_url", ""),
                "paper_url": data.get("paper_url", ""),
                "update_comment": data.get("update_comment", ""),
                "creator": data.get("creator", ""),
                "contributor": data.get("contributor", ""),
                "collection_date": data.get("collection_date", ""),
                "language": data.get("language", ""),
                "number_of_instances": data.get("number_of_instances", 0),
                "number_of_features": data.get("number_of_features", 0),
                "number_of_classes": data.get("number_of_classes", 0),
                "number_of_missing_values": data.get("number_of_missing_values", 0)
            }
            records.append(record)
        
        elif "search" in query:
            # Search datasets
            search_term = query["search"]
            limit = query.get("limit", 100)
            offset = query.get("offset", 0)
            
            url = f"{self.BASE_URL}/data/list"
            params = {
                "q": search_term,
                "limit": limit,
                "offset": offset,
                "format": "json"  # Request JSON format
            }
            
            response = make_request_with_retry(self.client, "GET", url, params=params)
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            datasets = []
            
            if "json" in content_type.lower():
                try:
                    data = response.json()
                    # Handle different response formats
                    if isinstance(data, dict):
                        datasets = data.get("data", {}).get("dataset", [])
                        if not datasets and "datasets" in data:
                            datasets = data.get("datasets", [])
                    elif isinstance(data, list):
                        datasets = data
                except:
                    datasets = []
            else:
                # OpenML returns XML by default - parse it
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)
                    # Parse OpenML XML structure
                    # Namespace handling
                    ns = {'oml': 'http://openml.org/openml'}
                    
                    # Find all dataset elements
                    dataset_elements = root.findall('.//oml:dataset', ns)
                    for ds_elem in dataset_elements:
                        dataset = {}
                        # Extract common fields
                        for child in ds_elem:
                            tag = child.tag.replace('{http://openml.org/openml}', '')
                            text = child.text if child.text else ""
                            dataset[tag] = text
                        if dataset:
                            datasets.append(dataset)
                except Exception as e:
                    # If XML parsing fails, return empty
                    datasets = []
            for dataset in datasets:
                record = {
                    "dataset_id": dataset.get("did", ""),
                    "name": dataset.get("name", ""),
                    "version": dataset.get("version", ""),
                    "status": dataset.get("status", ""),
                    "format": dataset.get("format", ""),
                    "number_of_instances": dataset.get("NumberOfInstances", 0),
                    "number_of_features": dataset.get("NumberOfFeatures", 0),
                    "number_of_classes": dataset.get("NumberOfClasses", 0)
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
            "source": "OpenML",
            "query": query,
            "retrieved_at": datetime.utcnow().isoformat(),
            "url": str(response.url) if 'response' in locals() else "",
            "license": "OpenML License",
            "api_version": "v1"
        }
        
        return ConnectorOutput(
            records=records,
            metadata=metadata,
            provenance=provenance
        )

