"""Package and bundle endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from db.session import get_db
from db.models.user import User
from db.models.package import DatasetPackage, UserPackage, PackageStatus, PackageSize
from db.models.payment import Payment, PaymentStatus
from core.dependencies import get_current_active_user
from schemas.package import (
    DatasetPackageResponse,
    PackageListResponse,
    PackageSelectionRequest,
    UserPackageResponse,
    UserPackageCreate
)
from services.package_service import (
    get_available_packages,
    create_user_package,
    get_user_active_package,
    check_package_eligibility
)
from services.wallet_service import debit_wallet, get_wallet_totals
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/packages", tags=["packages"])


@router.get("", response_model=PackageListResponse)
async def list_packages(
    db: Session = Depends(get_db)
):
    """List all available dataset packages."""
    packages = get_available_packages(db)
    
    return PackageListResponse(
        packages=[
            DatasetPackageResponse(
                id=pkg.id,
                name=pkg.name,
                size=pkg.size,
                dataset_count=pkg.dataset_count,
                price=float(pkg.price),
                currency=pkg.currency,
                description=pkg.description,
                is_active=pkg.is_active
            )
            for pkg in packages
        ],
        total=len(packages)
    )


@router.get("/my-package", response_model=UserPackageResponse)
async def get_my_active_package(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's active package (if any)."""
    user_package = get_user_active_package(db, current_user.id)
    
    if not user_package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active package found. Please purchase a package first."
        )
    
    return UserPackageResponse(
        id=user_package.id,
        user_id=user_package.user_id,
        package=DatasetPackageResponse(
            id=user_package.package.id,
            name=user_package.package.name,
            size=user_package.package.size,
            dataset_count=user_package.package.dataset_count,
            price=float(user_package.package.price),
            currency=user_package.package.currency,
            description=user_package.package.description,
            is_active=user_package.package.is_active
        ),
        selected_domains=user_package.selected_domains,
        total_datasets=user_package.total_datasets,
        remaining_datasets=user_package.remaining_datasets,
        used_datasets=user_package.used_datasets,
        status=user_package.status,
        purchased_at=user_package.purchased_at,
        expires_at=user_package.expires_at,
        activated_at=user_package.activated_at
    )


@router.get("/my-packages", response_model=List[UserPackageResponse])
async def get_my_packages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all user's purchased packages (history), newest first."""
    user_packages = (
        db.query(UserPackage)
        .filter(UserPackage.user_id == current_user.id)
        .order_by(UserPackage.purchased_at.desc())
        .all()
    )

    return [
        UserPackageResponse(
            id=up.id,
            user_id=up.user_id,
            package=DatasetPackageResponse(
                id=up.package.id,
                name=up.package.name,
                size=up.package.size,
                dataset_count=up.package.dataset_count,
                price=float(up.package.price),
                currency=up.package.currency,
                description=up.package.description,
                is_active=up.package.is_active,
            ),
            selected_domains=up.selected_domains,
            total_datasets=up.total_datasets,
            remaining_datasets=up.remaining_datasets,
            used_datasets=up.used_datasets,
            status=up.status,
            purchased_at=up.purchased_at,
            expires_at=up.expires_at,
            activated_at=up.activated_at,
        )
        for up in user_packages
    ]


@router.post("/select", response_model=UserPackageResponse, status_code=status.HTTP_201_CREATED)
async def select_package(
    selection: PackageSelectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Select a package and domains.
    
    This creates a UserPackage record but doesn't process payment yet.
    Payment will be handled via the billing/checkout endpoint.
    """
    # Check if user already has an active package
    existing = get_user_active_package(db, current_user.id)
    if existing and existing.remaining_datasets > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have an active package with {existing.remaining_datasets} remaining datasets. Please use it or wait until it's exhausted."
        )
    
    # Get package
    package = db.query(DatasetPackage).filter(
        DatasetPackage.id == selection.package_id,
        DatasetPackage.is_active == True
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found or not available"
        )
    
    # Domains are optional (packages are consumption-based). Default handled in service.
    
    # Create user package (without payment yet)
    user_package = create_user_package(
        db=db,
        user_id=current_user.id,
        package_id=package.id,
        selected_domains=[d.value for d in selection.selected_domains] if selection.selected_domains else ["all"],
        payment_id=None  # Will be set after payment
    )
    
    logger.info(f"User {current_user.id} selected package {package.id} with domains {selection.selected_domains}")
    
    return UserPackageResponse(
        id=user_package.id,
        user_id=user_package.user_id,
        package=DatasetPackageResponse(
            id=package.id,
            name=package.name,
            size=package.size,
            dataset_count=package.dataset_count,
            price=float(package.price),
            currency=package.currency,
            description=package.description,
            is_active=package.is_active
        ),
        selected_domains=user_package.selected_domains,
        total_datasets=user_package.total_datasets,
        remaining_datasets=user_package.remaining_datasets,
        used_datasets=user_package.used_datasets,
        status=user_package.status,
        purchased_at=user_package.purchased_at,
        expires_at=user_package.expires_at,
        activated_at=user_package.activated_at
    )


@router.get("/eligibility")
async def check_eligibility(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can create a dataset.
    
    Returns:
    - has_active_package: bool
    - remaining_datasets: int
    - selected_domains: List[str]
    - can_create: bool
    """
    user_package = get_user_active_package(db, current_user.id)
    
    if not user_package:
        return {
            "has_active_package": False,
            "remaining_datasets": 0,
            "selected_domains": [],
            "can_create": False,
            "message": "No active package. Please purchase a package first."
        }
    
    can_create = user_package.can_create_dataset()
    
    return {
        "has_active_package": True,
        "remaining_datasets": user_package.remaining_datasets,
        "selected_domains": user_package.selected_domains,
        "can_create": can_create,
        "message": f"You have {user_package.remaining_datasets} dataset(s) remaining." if can_create else "Package exhausted or expired."
    }


@router.post("/purchase", response_model=UserPackageResponse, status_code=status.HTTP_201_CREATED)
async def purchase_package_with_wallet(
    payload: UserPackageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Purchase a package using the virtual wallet balance.

    Rules:
    - User must have enough wallet balance to cover the full package price.
    - Domain restrictions are ignored (consumption-based); defaults to ["all"].
    """
    package = db.query(DatasetPackage).filter(
        DatasetPackage.id == payload.package_id,
        DatasetPackage.is_active == True
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found or not available")

    # Ensure enough wallet balance
    price = Decimal(str(package.price))
    try:
        debit_wallet(db, current_user.id, price, description=f"Purchase package: {package.name}")
    except Exception as e:
        balance, _, _ = get_wallet_totals(db, current_user.id)
        raise HTTPException(status_code=402, detail=f"Insufficient wallet balance. Required € {price}, available € {balance}.")

    user_package = create_user_package(
        db=db,
        user_id=current_user.id,
        package_id=package.id,
        selected_domains=[d.value for d in payload.selected_domains] if payload.selected_domains else ["all"],
        payment_id=None,
    )

    return UserPackageResponse(
        id=user_package.id,
        user_id=user_package.user_id,
        package=DatasetPackageResponse(
            id=package.id,
            name=package.name,
            size=package.size,
            dataset_count=package.dataset_count,
            price=float(package.price),
            currency=package.currency,
            description=package.description,
            is_active=package.is_active
        ),
        selected_domains=user_package.selected_domains,
        total_datasets=user_package.total_datasets,
        remaining_datasets=user_package.remaining_datasets,
        used_datasets=user_package.used_datasets,
        status=user_package.status,
        purchased_at=user_package.purchased_at,
        expires_at=user_package.expires_at,
        activated_at=user_package.activated_at
    )

