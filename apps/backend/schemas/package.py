"""Package and bundle schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from db.models.package import PackageSize, PackageStatus
from schemas.dataset_plan import Domain


class DatasetPackageResponse(BaseModel):
    """Dataset package response."""
    id: UUID
    name: str
    size: PackageSize
    dataset_count: int
    price: float
    currency: str
    description: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class PackageSelectionRequest(BaseModel):
    """Request to select a package and domains."""
    package_id: UUID = Field(..., description="Selected package ID")
    selected_domains: List[Domain] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="List of domains/categories for dataset creation"
    )


class UserPackageResponse(BaseModel):
    """User package response."""
    id: UUID
    user_id: UUID
    package: DatasetPackageResponse
    selected_domains: List[str]
    total_datasets: int
    remaining_datasets: int
    used_datasets: int
    status: PackageStatus
    purchased_at: datetime
    expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPackageCreate(BaseModel):
    """Create user package from package selection."""
    package_id: UUID
    selected_domains: List[Domain]
    payment_id: Optional[UUID] = None  # If already paid


class PackageListResponse(BaseModel):
    """List of available packages."""
    packages: List[DatasetPackageResponse]
    total: int

