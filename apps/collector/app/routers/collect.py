"""Collect endpoint for dataset collection."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from connectors import get_connector
from services.storage_service import save_raw_asset
from connectors.base import ConnectorOutput

logger = logging.getLogger(__name__)
router = APIRouter()


class CollectRequest(BaseModel):
    """Collect request."""
    connector_name: str
    query: Dict[str, Any]
    dataset_step_id: str


class CollectResponse(BaseModel):
    """Collect response."""
    success: bool
    row_count: int
    storage_path: str
    metadata: Dict[str, Any]
    provenance: Dict[str, Any]


@router.post("/collect", response_model=CollectResponse)
async def collect_data(request: CollectRequest):
    """
    Collect data from external source.
    
    This endpoint is called by the backend worker to execute collect steps.
    """
    try:
        # Get connector
        connector = get_connector(request.connector_name)
        if not connector:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connector '{request.connector_name}' not found"
            )
        
        # Validate query
        if not connector.validate_query(request.query):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query parameters"
            )
        
        # Fetch data
        logger.info(f"Collecting data from {request.connector_name} for step {request.dataset_step_id}")
        output: ConnectorOutput = connector.fetch(request.query)
        
        # Save raw asset
        raw_data = {
            "records": output.records,
            "metadata": output.metadata,
            "provenance": output.provenance
        }
        
        storage_path = save_raw_asset(
            data=raw_data,
            dataset_step_id=request.dataset_step_id,
            connector_name=request.connector_name,
            file_format="json"
        )
        
        logger.info(f"Collected {output.metadata['row_count']} records from {request.connector_name}")
        
        return CollectResponse(
            success=True,
            row_count=output.metadata['row_count'],
            storage_path=storage_path,
            metadata=output.metadata,
            provenance=output.provenance
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting data: {str(e)}"
        )


@router.get("/connectors")
async def list_connectors_endpoint():
    """List available connectors."""
    from connectors import list_connectors
    return {"connectors": list_connectors()}

