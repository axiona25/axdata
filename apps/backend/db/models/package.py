"""Package and bundle models for dataset purchases."""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime
from db.session import Base


class PackageSize(str, enum.Enum):
    """Package sizes (number of datasets)."""
    SINGLE = "1"
    SMALL = "3"
    MEDIUM = "5"
    LARGE = "7"
    XL = "10"
    XXL = "15"
    XXXL = "20"
    MEGA = "50"
    ULTRA = "100"


class PackageStatus(str, enum.Enum):
    """Package status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"  # All datasets used
    CANCELLED = "cancelled"


class DatasetPackage(Base):
    """Predefined dataset packages/bundles."""
    __tablename__ = "dataset_packages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)  # e.g., "Starter Pack", "Researcher Bundle"
    size = Column(SQLEnum(PackageSize), nullable=False)  # Number of datasets
    dataset_count = Column(Integer, nullable=False)  # 1, 3, 5, 7, 10, 15, 20, 50, 100
    price = Column(Numeric(10, 2), nullable=False)  # Price in EUR
    currency = Column(String(3), default="EUR", nullable=False)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    package_metadata = Column("metadata", JSON, nullable=True)  # Additional package info (renamed to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_packages = relationship("UserPackage", back_populates="package", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DatasetPackage(id={self.id}, name={self.name}, size={self.size}, datasets={self.dataset_count})>"


class UserPackage(Base):
    """User's purchased package with remaining credits."""
    __tablename__ = "user_packages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    package_id = Column(UUID(as_uuid=True), ForeignKey("dataset_packages.id", ondelete="CASCADE"), nullable=False)
    
    # Selected domains/categories for this package
    selected_domains = Column(JSON, nullable=False)  # List of domain strings: ["economics", "biomedical", ...]
    
    # Credits tracking
    total_datasets = Column(Integer, nullable=False)  # Total datasets in package
    remaining_datasets = Column(Integer, nullable=False)  # Remaining credits
    used_datasets = Column(Integer, default=0, nullable=False)  # Used credits
    
    # Status and dates
    status = Column(SQLEnum(PackageStatus), default=PackageStatus.ACTIVE, nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    activated_at = Column(DateTime, nullable=True)  # When user started using it
    
    # Payment reference
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    
    # Relationships
    user = relationship("User", backref="packages")
    package = relationship("DatasetPackage", back_populates="user_packages")
    payment = relationship("Payment", foreign_keys=[payment_id])
    dataset_requests = relationship("DatasetRequest", back_populates="user_package", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserPackage(id={self.id}, user_id={self.user_id}, package={self.package.name}, remaining={self.remaining_datasets})>"
    
    def can_create_dataset(self) -> bool:
        """Check if user can create another dataset with this package."""
        return (
            self.status == PackageStatus.ACTIVE and
            self.remaining_datasets > 0 and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    def consume_credit(self):
        """Consume one dataset credit."""
        if not self.can_create_dataset():
            raise ValueError("Cannot consume credit: package exhausted or expired")
        
        self.remaining_datasets -= 1
        self.used_datasets += 1
        
        if self.remaining_datasets == 0:
            self.status = PackageStatus.EXHAUSTED

