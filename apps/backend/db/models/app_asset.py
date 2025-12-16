"""Application assets (e.g., product logo) stored in DB."""

import uuid

from sqlalchemy import Column, DateTime, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.session import Base


class AppAsset(Base):
    """Store app-level assets like logos in the database."""

    __tablename__ = "app_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "logo"
    content_type = Column(String(100), nullable=False)  # e.g., "image/png"
    data = Column(LargeBinary, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

