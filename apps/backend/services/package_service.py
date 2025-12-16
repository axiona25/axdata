"""Package service for managing dataset packages."""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from db.models.package import DatasetPackage, UserPackage, PackageStatus, PackageSize
from db.models.user import User

logger = logging.getLogger(__name__)


def get_available_packages(db: Session) -> List[DatasetPackage]:
    """Get all active packages."""
    return db.query(DatasetPackage).filter(
        DatasetPackage.is_active == True
    ).order_by(DatasetPackage.dataset_count.asc()).all()


def create_user_package(
    db: Session,
    user_id: UUID,
    package_id: UUID,
    selected_domains: List[str],
    payment_id: Optional[UUID] = None
) -> UserPackage:
    """Create a user package."""
    package = db.query(DatasetPackage).filter(DatasetPackage.id == package_id).first()
    if not package:
        raise ValueError(f"Package {package_id} not found")
    
    user_package = UserPackage(
        user_id=user_id,
        package_id=package_id,
        selected_domains=selected_domains,
        total_datasets=package.dataset_count,
        remaining_datasets=package.dataset_count,
        used_datasets=0,
        status=PackageStatus.ACTIVE,
        payment_id=payment_id,
        activated_at=datetime.utcnow()
    )
    
    db.add(user_package)
    db.commit()
    db.refresh(user_package)
    
    logger.info(f"Created user package {user_package.id} for user {user_id}")
    
    return user_package


def get_user_active_package(db: Session, user_id: UUID) -> Optional[UserPackage]:
    """Get user's active package (if any)."""
    return db.query(UserPackage).filter(
        UserPackage.user_id == user_id,
        UserPackage.status == PackageStatus.ACTIVE,
        UserPackage.remaining_datasets > 0
    ).order_by(UserPackage.purchased_at.desc()).first()


def check_package_eligibility(
    db: Session,
    user_id: UUID,
    domain: str
) -> tuple[bool, Optional[UserPackage], str]:
    """
    Check if user can create a dataset for the given domain.
    
    Returns:
        (can_create, user_package, message)
    """
    user_package = get_user_active_package(db, user_id)
    
    if not user_package:
        return False, None, "No active package found. Please purchase a package first."
    
    if not user_package.can_create_dataset():
        return False, user_package, "Package exhausted or expired."
    
    if domain not in user_package.selected_domains:
        return False, user_package, f"Domain '{domain}' not included in your package. Selected domains: {', '.join(user_package.selected_domains)}"
    
    return True, user_package, "OK"


def consume_package_credit(db: Session, user_package: UserPackage) -> None:
    """Consume one dataset credit from user package."""
    if not user_package.can_create_dataset():
        raise ValueError("Cannot consume credit: package exhausted or expired")
    
    user_package.consume_credit()
    db.commit()
    
    logger.info(f"Consumed credit from package {user_package.id}. Remaining: {user_package.remaining_datasets}")

