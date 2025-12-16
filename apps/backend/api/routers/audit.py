"""Audit log endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
import logging

from db.session import get_db
from db.models.user import User
from db.models.audit_log import AuditLog, AuditAction
from core.dependencies import get_current_active_user
from schemas.audit import AuditLogResponse, AuditLogListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List audit logs for current user.
    
    Filters:
    - action: Filter by action type
    - resource_type: Filter by resource type
    - resource_id: Filter by resource ID
    - start_date: Filter logs from this date
    - end_date: Filter logs until this date
    """
    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)
    
    if action:
        try:
            action_enum = AuditAction(action)
            query = query.filter(AuditLog.action == action_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}"
            )
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if resource_id:
        try:
            resource_uuid = uuid.UUID(resource_id)
            query = query.filter(AuditLog.resource_id == resource_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource_id: {resource_id}"
            )
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        logs=[
            AuditLogResponse(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                trace_id=log.trace_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                metadata=log.extra_metadata,
                created_at=log.created_at
            )
            for log in logs
        ],
        total=total
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit log details."""
    log = db.query(AuditLog).filter(
        AuditLog.id == uuid.UUID(log_id),
        AuditLog.user_id == current_user.id
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return AuditLogResponse(
        id=str(log.id),
        user_id=str(log.user_id) if log.user_id else None,
        action=log.action.value,
        resource_type=log.resource_type,
        resource_id=str(log.resource_id) if log.resource_id else None,
        trace_id=log.trace_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        metadata=log.metadata,
        created_at=log.created_at
    )

