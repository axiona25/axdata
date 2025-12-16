"""Chat schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageCreate(BaseModel):
    """Create chat message request."""
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="user", pattern="^(user|assistant|system)$")


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: str
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Create chat session request."""
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """List of chat sessions."""
    sessions: List[ChatSessionResponse]
    total: int

