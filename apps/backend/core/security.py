"""Security utilities for authentication."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash. Bcrypt has a 72-byte limit, so we truncate if necessary."""
    # Bcrypt has a 72-byte limit, truncate if necessary for verification
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, ensuring we don't break UTF-8 characters
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and truncated[-1] & 0b11000000 == 0b10000000:
            truncated = truncated[:-1]
        password_bytes = truncated
    
    # Use bcrypt directly to avoid passlib's initialization issues
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password. Bcrypt has a 72-byte limit, so we truncate if necessary."""
    # Bcrypt has a 72-byte limit, truncate if necessary
    # Convert to bytes first to check actual byte length
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, ensuring we don't break UTF-8 characters
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and truncated[-1] & 0b11000000 == 0b10000000:
            truncated = truncated[:-1]
        password_bytes = truncated
    
    # Use bcrypt directly to avoid passlib's initialization issues
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

