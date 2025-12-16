"""CollectorRequest v1.0 Pydantic schema."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(1000, ge=1, le=10000)


class CollectionOptions(BaseModel):
    """Optional collection options."""
    save_to_storage: bool = Field(True, description="Whether to save raw data to object storage")
    include_metadata: bool = Field(True, description="Whether to include detailed metadata")
    timeout_seconds: int = Field(300, ge=1, le=600, description="Request timeout in seconds")


class CollectorRequest(BaseModel):
    """
    Standard request format from Backend to API Collector.
    """
    connector_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Connector identifier (must match registered connector)"
    )
    query_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for this query (from DatasetPlan)"
    )
    params: Dict[str, Any] = Field(
        ...,
        description="Query parameters specific to connector (structure varies by connector)"
    )
    dataset_step_id: Optional[UUID] = Field(
        None,
        description="Optional: Backend dataset step ID for traceability"
    )
    pagination: Optional[PaginationParams] = None
    options: Optional[CollectionOptions] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "connector_name": "eurostat",
                "query_id": "q1",
                "params": {
                    "dataset": "prc_hicp_midx",
                    "geo": ["IT", "FR"],
                    "time": ["2020", "2024"]
                },
                "dataset_step_id": "123e4567-e89b-12d3-a456-426614174000",
                "pagination": {
                    "page": 1,
                    "page_size": 1000
                },
                "options": {
                    "save_to_storage": True,
                    "include_metadata": True,
                    "timeout_seconds": 300
                }
            }
        }

