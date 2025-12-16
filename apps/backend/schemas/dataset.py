"""Dataset request schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from db.models.dataset import DatasetStatus, StepStatus, StepType
from schemas.dataset_plan import DatasetPlan


class DatasetRequestCreate(BaseModel):
    """Create dataset request from DatasetPlan."""
    plan: DatasetPlan
    chat_session_id: Optional[str] = None


class DatasetRequestResponse(BaseModel):
    """Dataset request response."""
    id: str
    user_id: str
    chat_session_id: Optional[str]
    title: str
    domain: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    step_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class DatasetStepResponse(BaseModel):
    """Dataset step response."""
    id: str
    dataset_request_id: str
    step_type: str
    step_order: int
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DatasetRequestDetailResponse(BaseModel):
    """Detailed dataset request response with steps."""
    id: str
    user_id: str
    chat_session_id: Optional[str]
    title: str
    domain: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    steps: List[DatasetStepResponse]
    plan: Dict[str, Any]


class DatasetProgressResponse(BaseModel):
    """Dataset progress response."""
    dataset_id: str
    status: str
    progress_percentage: float
    current_step: Optional[str]
    steps: List[DatasetStepResponse]
    error_message: Optional[str]

