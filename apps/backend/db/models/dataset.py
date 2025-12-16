"""Dataset request and step models."""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from db.session import Base


class DatasetStatus(str, enum.Enum):
    """Dataset request status."""
    DRAFT = "draft"
    RUNNING = "running"
    READY_FOR_PAYMENT = "ready_for_payment"
    PAID = "paid"
    DELIVERED = "delivered"
    FAILED = "failed"


class StepStatus(str, enum.Enum):
    """Dataset step status."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class StepType(str, enum.Enum):
    """Dataset step type."""
    COLLECT = "collect"
    NORMALIZE = "normalize"
    EXPORT = "export"


class DatasetRequest(Base):
    """Dataset request model."""
    __tablename__ = "dataset_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True, index=True)
    user_package_id = Column(UUID(as_uuid=True), ForeignKey("user_packages.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    domain = Column(String(50), nullable=False)
    plan_json = Column(JSON, nullable=False)  # DatasetPlan serialized
    status = Column(SQLEnum(DatasetStatus), nullable=False, default=DatasetStatus.DRAFT, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    steps = relationship("DatasetStep", back_populates="dataset_request", cascade="all, delete-orphan", order_by="DatasetStep.step_order")
    user_package = relationship("UserPackage", back_populates="dataset_requests")

    def __repr__(self):
        return f"<DatasetRequest(id={self.id}, title={self.title}, status={self.status})>"


class DatasetStep(Base):
    """Dataset step model."""
    __tablename__ = "dataset_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_request_id = Column(UUID(as_uuid=True), ForeignKey("dataset_requests.id"), nullable=False, index=True)
    step_type = Column(SQLEnum(StepType), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(SQLEnum(StepStatus), nullable=False, default=StepStatus.QUEUED, index=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset_request = relationship("DatasetRequest", back_populates="steps")

    def __repr__(self):
        return f"<DatasetStep(id={self.id}, type={self.step_type}, status={self.status})>"

