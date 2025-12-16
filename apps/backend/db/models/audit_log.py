"""Audit log models."""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from db.session import Base


class AuditAction(str, enum.Enum):
    """Audit action types."""
    DATASET_DOWNLOAD = "dataset_download"
    INVOICE_DOWNLOAD = "invoice_download"
    DATASET_CREATE = "dataset_create"
    DATASET_UPDATE = "dataset_update"
    DATASET_DELETE = "dataset_delete"
    PAYMENT_CREATE = "payment_create"
    PAYMENT_COMPLETE = "payment_complete"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_UPDATE = "user_update"


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)  # e.g., "dataset", "invoice", "payment"
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    trace_id = Column(String(100), nullable=True, index=True)  # For request tracing
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)  # Additional context (renamed to avoid SQLAlchemy conflict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, user_id={self.user_id})>"

