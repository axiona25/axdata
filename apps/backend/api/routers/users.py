"""User management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
import logging
from db.session import get_db
from db.models.user import User, UserProfile
from db.models.audit_log import AuditLog, AuditAction
from core.dependencies import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])


class UserProfileUpdate(BaseModel):
    """User profile update request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    preferences: Optional[dict] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    user_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    organization: Optional[str]
    preferences: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    # Convert UUID to string for Pydantic response model
    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        first_name=profile.first_name,
        last_name=profile.last_name,
        organization=profile.organization,
        preferences=profile.preferences,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Update only provided fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        db.commit()
        db.refresh(profile)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete user account (GDPR compliant).
    
    - Sets deleted_at timestamp
    - Deactivates account (is_active = False)
    - Logs audit event
    - Note: Actual data purge happens via scheduled job after retention period
    """
    try:
        from datetime import datetime, timezone
        
        # Soft delete: set deleted_at and deactivate
        current_user.deleted_at = datetime.now(timezone.utc)
        current_user.is_active = False
        db.commit()
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        audit = AuditLog(
            user_id=current_user.id,
            action=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=current_user.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            extra_metadata={
                "action": "account_deleted",
                "email": current_user.email
            }
        )
        db.add(audit)
        db.commit()
        
        logger.info(f"User {current_user.id} account soft deleted")
        
        return None
    except Exception as e:
        logger.error(f"Error deleting account: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting account"
        )

