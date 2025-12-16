"""Connector registry."""
from typing import Dict, Optional
from connectors.base import BaseConnector

_registry: Dict[str, BaseConnector] = {}


def register_connector(connector: BaseConnector):
    """
    Register a connector.
    
    Args:
        connector: Connector instance
    """
    _registry[connector.name.lower()] = connector


def get_connector(name: str) -> Optional[BaseConnector]:
    """
    Get connector by name.
    
    Args:
        name: Connector name
    
    Returns:
        Connector instance or None if not found
    """
    return _registry.get(name.lower())


def list_connectors() -> list[str]:
    """
    List all registered connector names.
    
    Returns:
        List of connector names
    """
    return list(_registry.keys())

