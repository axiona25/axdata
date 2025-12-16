"""Payment models."""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from db.session import Base


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(str, enum.Enum):
    """Payment provider."""
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Payment(Base):
    """Payment model.
    
    Can be used for:
    - Single dataset payment (dataset_request_id required)
    - Package payment (user_package_id required)
    """
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    dataset_request_id = Column(UUID(as_uuid=True), ForeignKey("dataset_requests.id"), nullable=True, index=True)  # Nullable for packages
    user_package_id = Column(UUID(as_uuid=True), ForeignKey("user_packages.id"), nullable=True, index=True)  # For package payments
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="eur")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    provider = Column(SQLEnum(PaymentProvider), nullable=False, default=PaymentProvider.STRIPE)
    provider_ref = Column(String(255), nullable=True, unique=True)  # Stripe payment intent ID
    provider_checkout_session_id = Column(String(255), nullable=True, index=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    payment_metadata = Column("metadata", JSON, nullable=True)  # Stored as 'metadata' in DB
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    dataset_request = relationship("DatasetRequest", backref="payments")
    user_package = relationship("UserPackage", foreign_keys=[user_package_id], backref="payments")

    # Indexes
    __table_args__ = (
        Index('ix_payments_provider_ref', 'provider_ref'),
        Index('ix_payments_idempotency_key', 'idempotency_key'),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"

