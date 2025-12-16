"""Invoice models."""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON, Enum as SQLEnum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from db.session import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status."""
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice model."""
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, unique=True, index=True)
    dataset_request_id = Column(UUID(as_uuid=True), ForeignKey("dataset_requests.id"), nullable=True, index=True)  # Nullable for package payments
    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="eur")
    invoice_date = Column(Date, nullable=False, server_default=func.current_date())
    due_date = Column(Date, nullable=True)
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT, index=True)
    storage_path = Column(String(500), nullable=True)  # PDF path in S3
    invoice_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    payment = relationship("Payment", backref="invoice")
    dataset_request = relationship("DatasetRequest", backref="invoices")

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number}, status={self.status})>"

