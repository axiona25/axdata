"""Chat endpoints with OpenAI integration."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
import json
import logging

from db.session import get_db
from db.models.user import User
from db.models.chat import ChatSession, ChatMessage
from core.dependencies import get_current_active_user
from schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse
)
from schemas.dataset_plan import DatasetPlan
from services.openai_service import chat_completion_stream, chat_completion_with_tool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ChatSessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).count()
    
    return ChatSessionListResponse(
        sessions=[
            ChatSessionResponse(
                id=str(s.id),
                user_id=str(s.user_id),
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages)
            )
            for s in sessions
        ],
        total=total
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat session details."""
    session = db.query(ChatSession).filter(
        ChatSession.id == uuid.UUID(session_id),
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return ChatSessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages)
    )


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages for a session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == uuid.UUID(session_id),
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return [
        ChatMessageResponse(
            id=str(msg.id),
            session_id=str(msg.session_id),
            role=msg.role,
            content=msg.content,
            metadata=msg.message_metadata,
            created_at=msg.created_at
        )
        for msg in session.messages
    ]


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def create_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new message in a session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == uuid.UUID(session_id),
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    try:
        # Create user message
        user_message = ChatMessage(
            session_id=session.id,
            role=message_data.role,
            content=message_data.content
        )
        db.add(user_message)
        
        # Update session title if first message
        if not session.title and message_data.role == "user":
            # Use first 50 chars of message as title
            session.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
        
        db.flush()
        
        # Get all messages for context
        all_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at).all()
        
        # Prepare messages for OpenAI
        messages_for_openai = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in all_messages
        ]
        
        # Get response from OpenAI
        try:
            full_response, dataset_plan = chat_completion_with_tool(
                messages_for_openai,
                str(session.id),
                str(current_user.id)
            )
            
            # Create assistant message
            assistant_metadata = None
            if dataset_plan:
                assistant_metadata = {
                    "dataset_plan": dataset_plan.dict(),
                    "tool_called": "create_dataset_plan"
                }
            
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_response,
                message_metadata=assistant_metadata
            )
            db.add(assistant_message)
            db.commit()
            
            db.refresh(user_message)
            return ChatMessageResponse(
                id=str(user_message.id),
                session_id=str(user_message.session_id),
                role=user_message.role,
                content=user_message.content,
                metadata=user_message.message_metadata,
                created_at=user_message.created_at
            )
        
        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating response: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating message: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages/stream")
async def create_message_stream(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a message and stream the response."""
    session = db.query(ChatSession).filter(
        ChatSession.id == uuid.UUID(session_id),
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Create user message
    user_message = ChatMessage(
        session_id=session.id,
        role=message_data.role,
        content=message_data.content
    )
    db.add(user_message)
    
    # Update session title if first message
    if not session.title and message_data.role == "user":
        session.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
    
    db.commit()
    db.refresh(user_message)
    
    # Get all messages for context
    all_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at).all()
    
    # Prepare messages for OpenAI
    messages_for_openai = [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in all_messages
    ]
    
    def generate_stream():
        """Generate streaming response."""
        full_response = ""
        dataset_plan = None
        
        try:
            # Stream response and collect tool calls
            tool_calls_data = []
            for chunk in chat_completion_stream(
                messages_for_openai,
                str(session.id),
                str(current_user.id)
            ):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # After streaming, try to get DatasetPlan from non-streaming call
            # This ensures we capture tool calls properly
            try:
                _, dataset_plan = chat_completion_with_tool(
                    messages_for_openai,
                    str(session.id),
                    str(current_user.id)
                )
            except Exception as e:
                logger.warning(f"Could not extract DatasetPlan from tool call: {e}")
            
            # Save assistant message with DatasetPlan in metadata if found
            assistant_metadata = None
            if dataset_plan:
                assistant_metadata = {
                    "dataset_plan": dataset_plan.dict(),
                    "tool_called": "create_dataset_plan"
                }
                # Send DatasetPlan to frontend
                yield f"data: {json.dumps({'dataset_plan': dataset_plan.dict()})}\n\n"
            
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_response,
                message_metadata=assistant_metadata
            )
            db.add(assistant_message)
            db.commit()
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            error_msg = str(e)
            # Check if it's an OpenAI API error
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                error_msg = "OpenAI API key not configured. Please check backend configuration."
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

