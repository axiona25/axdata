"""Base connector interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ConnectorOutput:
    """Standard output format for all connectors."""
    records: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    provenance: Dict[str, Any]


class BaseConnector(ABC):
    """Base class for all connectors."""
    
    def __init__(self, name: str):
        """
        Initialize connector.
        
        Args:
            name: Connector name
        """
        self.name = name
    
    @abstractmethod
    def validate_query(self, query: Dict[str, Any]) -> bool:
        """
        Validate query parameters.
        
        Args:
            query: Query parameters
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch(self, query: Dict[str, Any]) -> ConnectorOutput:
        """
        Fetch data from the source.
        
        Args:
            query: Query parameters
        
        Returns:
            ConnectorOutput with records, metadata, and provenance
        """
        pass
    
    def connect(self) -> bool:
        """
        Test connection to the source.
        
        Returns:
            True if connection successful
        """
        return True

