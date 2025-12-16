"""Audit log schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    trace_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[dict]  # Maps to extra_metadata in model
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs."""
    logs: list[AuditLogResponse]
    total: int

