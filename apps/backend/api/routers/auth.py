"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid
from db.session import get_db
from db.models.user import User, UserProfile
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from core.dependencies import get_current_active_user
from core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# Request/Response models
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    payment_method: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    """Email verification request."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: EmailStr


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.flush()  # Get user.id
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            preferences={
                "phone": user_data.phone,
                "date_of_birth": user_data.date_of_birth,
                "address": user_data.address,
                "country": user_data.country,
                "language": user_data.language,
                "payment_method": user_data.payment_method,
                "verification_token": str(uuid.uuid4()),  # Generate verification token
            }
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        
        # Send verification email
        import logging
        logger = logging.getLogger(__name__)
        verification_token = profile.preferences.get("verification_token")
        verification_url = (
            f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/verify-email"
            f"?token={verification_token}&email={user.email}"
        )
        logger.info(f"Registration completed for {user.email}. Verification URL: {verification_url}")
        
        try:
            from services.email_service import email_service
            if email_service.enabled:
                success = email_service.send_verification_email(user.email, verification_url)
                if success:
                    logger.info(f"✅ Verification email sent successfully to {user.email}")
                else:
                    logger.warning(f"⚠️ Failed to send verification email to {user.email} (check email service configuration)")
            else:
                logger.warning(f"⚠️ Email service is disabled. Verification URL for {user.email}: {verification_url}")
        except Exception as email_error:
            # Log email error but don't fail registration
            logger.error(f"❌ Error sending verification email to {user.email}: {str(email_error)}", exc_info=True)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error registering user: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    from core.security import decode_token
    
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout (token revocation handled client-side)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    try:
        # Explicitly convert UUID to string for Pydantic serialization
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in /me endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user information: {str(e)}"
        )


@router.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email."""
    import logging
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    user = db.query(User).filter(User.email == request_data.email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token (in production, use a more secure method)
    reset_token = str(uuid.uuid4())
    
    # Store token in user preferences or a separate table
    # For now, we'll use a simple approach with user preferences
    if not user.profile:
        from db.models.user import UserProfile
        profile = UserProfile(user_id=user.id, preferences={})
        db.add(profile)
        db.flush()
    
    user.profile.preferences = user.profile.preferences or {}
    user.profile.preferences["password_reset_token"] = reset_token
    user.profile.preferences["password_reset_expires"] = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    db.commit()
    
    # Send email with reset link
    reset_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/reset-password?token={reset_token}"
    logger.info(f"Password reset requested for {user.email}. Reset URL: {reset_url}")
    
    from services.email_service import email_service
    email_service.send_password_reset_email(user.email, reset_url)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Find user with matching reset token
    users = db.query(User).join(UserProfile).all()
    user = None
    
    for u in users:
        if (u.profile and 
            u.profile.preferences and 
            u.profile.preferences.get("password_reset_token") == reset_data.token):
            # Check if token is expired
            expires_str = u.profile.preferences.get("password_reset_expires")
            if expires_str:
                expires = datetime.fromisoformat(expires_str)
                if datetime.utcnow() > expires:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reset token has expired"
                    )
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    
    # Clear reset token
    user.profile.preferences.pop("password_reset_token", None)
    user.profile.preferences.pop("password_reset_expires", None)
    
    db.commit()
    
    logger.info(f"Password reset completed for user {user.email}")
    
    return {"message": "Password has been reset successfully"}


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify user email with token."""
    import logging
    from sqlalchemy import text
    
    logger = logging.getLogger(__name__)
    
    token = verification_data.token
    logger.info(f"Verification attempt with token: {token[:8]}... (full: {token})")
    
    # First, let's check all tokens in the database for debugging
    all_tokens = db.execute(
        text("""
            SELECT u.email, up.preferences->>'verification_token' as token
            FROM users u
            JOIN user_profiles up ON u.id = up.user_id
            WHERE up.preferences->>'verification_token' IS NOT NULL
        """)
    ).fetchall()
    logger.info(f"All tokens in DB: {[(r.email, r.token[:8] if r.token else 'None') for r in all_tokens]}")
    
    # Find user with matching verification token using SQL query for better performance
    result = db.execute(
        text("""
            SELECT u.id, u.email, u.is_verified, up.preferences->>'verification_token' as db_token
            FROM users u
            JOIN user_profiles up ON u.id = up.user_id
            WHERE up.preferences->>'verification_token' = :token
            LIMIT 1
        """),
        {"token": token}
    ).fetchone()
    
    if not result:
        logger.warning(f"Verification token not found: {token[:8]}... (full: {token})")
        # Try to find if token exists but with different format
        all_users = db.execute(
            text("""
                SELECT u.email, up.preferences
                FROM users u
                JOIN user_profiles up ON u.id = up.user_id
            """)
        ).fetchall()
        for user_row in all_users:
            prefs = user_row.preferences or {}
            stored_token = prefs.get("verification_token")
            if stored_token:
                logger.info(f"User {user_row.email} has token: {stored_token[:8]}... (full: {stored_token})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user_id = result.id
    user_email = result.email
    is_already_verified = result.is_verified
    
    if is_already_verified:
        logger.info(f"User {user_email} already verified")
        return {"message": "Email already verified"}
    
    # Get user object and mark as verified
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark as verified
    user.is_verified = True
    
    # Clear verification token
    if user.profile and user.profile.preferences:
        user.profile.preferences.pop("verification_token", None)
    
    db.commit()
    
    logger.info(f"✅ Email verified successfully for user {user.email}")
    
    return {"message": "Email verified successfully"}


@router.post("/verify-email/resend")
async def resend_verification_email(
    request_data: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend verification email."""
    import logging
    import asyncio
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    # Note: This endpoint allows multiple resend requests to help users who didn't receive emails
    # Rate limiting is handled globally by slowapi middleware if configured
    
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if not user:
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Check last email send time to avoid rate limiting from SendGrid
    # SendGrid may block if too many emails are sent in a short time
    last_send_key = f"last_verification_email_send_{user.id}"
    # Note: In production, use Redis for this. For now, we'll just log and add a small delay
    logger.info(f"Resend verification email requested for {user.email}")
    
    # Reuse existing token if present to avoid breaking older links; otherwise generate a new one
    existing_token = None
    if user.profile and user.profile.preferences:
        existing_token = user.profile.preferences.get("verification_token")

    verification_token = existing_token or str(uuid.uuid4())
    if existing_token:
        logger.info(f"Reusing existing verification token for {user.email}: {verification_token[:8]}...")
    else:
        logger.info(f"Generated new verification token for {user.email}: {verification_token[:8]}...")
    
    # Store token in user preferences
    if not user.profile:
        from db.models.user import UserProfile
        profile = UserProfile(user_id=user.id, preferences={})
        db.add(profile)
        db.flush()
        user.profile = profile
    
    user.profile.preferences = user.profile.preferences or {}
    user.profile.preferences["verification_token"] = verification_token
    db.commit()
    db.refresh(user.profile)  # Refresh to ensure data is loaded
    
    # Verify token was saved
    saved_token = user.profile.preferences.get("verification_token")
    if saved_token != verification_token:
        logger.error(f"❌ Token mismatch! Generated: {verification_token[:8]}..., Saved: {saved_token[:8] if saved_token else 'None'}...")
    else:
        logger.info(f"✅ Token saved successfully: {verification_token[:8]}...")
    
    # Send email with verification link
    verification_url = (
        f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/verify-email"
        f"?token={verification_token}&email={user.email}"
    )
    logger.info(f"Verification email requested for {user.email}. Verification URL: {verification_url}")
    
    from services.email_service import email_service
    
    # Add a small delay to avoid SendGrid rate limiting (max 1 email per second recommended)
    await asyncio.sleep(1)
    
    # Send email with detailed logging
    try:
        logger.info(f"Attempting to send verification email to {user.email}...")
        success = email_service.send_verification_email(user.email, verification_url)
        if success:
            logger.info(f"✅ Verification email sent successfully to {user.email}")
        else:
            logger.error(f"❌ Failed to send verification email to {user.email} (send_verification_email returned False)")
            # If email sending failed, it might be due to SendGrid rate limiting
            # Log this for debugging
            logger.warning(f"⚠️ Email sending failed for {user.email}. This might be due to SendGrid rate limiting.")
    except Exception as e:
        logger.error(f"❌ Exception while sending verification email to {user.email}: {str(e)}", exc_info=True)
        # Check if it's a rate limit error
        error_str = str(e).lower()
        if "rate" in error_str or "limit" in error_str or "429" in error_str:
            logger.error(f"🚫 SendGrid rate limit detected for {user.email}. Please wait before retrying.")
        # Don't raise - still return success to prevent email enumeration
    
    return {"message": "If the email exists, a verification link has been sent"}

