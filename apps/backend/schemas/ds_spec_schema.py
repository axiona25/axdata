"""DS-SPEC schema for API endpoints."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from axdata.spec.ds_spec import DatasetSpec


class DatasetSpecCreate(BaseModel):
    """Create dataset from DS-SPEC."""
    ds_spec: Dict[str, Any]  # Will be validated as DatasetSpec
    chat_session_id: Optional[str] = None
    
    def to_ds_spec(self) -> DatasetSpec:
        """Convert to DatasetSpec."""
        return DatasetSpec(**self.ds_spec)


class DatasetSpecResponse(BaseModel):
    """Response for dataset creation from DS-SPEC."""
    dataset_id: str
    template: str
    selected_sources: List[str]
    raw_count: int
    status: str
