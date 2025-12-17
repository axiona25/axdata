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
    # Only expose commercial packages (Acquisto N. X Dataset) to the UI.
    # This prevents legacy bundles (e.g., Enterprise/Department/Ultra) from appearing.
    commercial_counts = {1, 3, 5, 10, 20, 50, 100, 200}
    packages = db.query(DatasetPackage).filter(
        DatasetPackage.is_active == True,
        DatasetPackage.dataset_count.in_(commercial_counts)
    ).order_by(DatasetPackage.dataset_count.asc()).all()
    return packages


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
    
    # Packages are consumption-based; domains are optional.
    normalized_domains = selected_domains or ["all"]

    user_package = UserPackage(
        user_id=user_id,
        package_id=package_id,
        selected_domains=normalized_domains,
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
    
    # Domain restriction removed: allow any domain if package has "all"
    if user_package.selected_domains and "all" not in user_package.selected_domains:
        if domain not in user_package.selected_domains:
            return False, user_package, f"Domain '{domain}' not included in your package."
    
    return True, user_package, "OK"


def ensure_default_commercial_packages(db: Session) -> None:
    """
    Ensure the commercial packages exist (idempotent).

    Commercial catalog (unit promo price * dataset_count):
    - 1 x €15
    - 3 x €12
    - 5 x €10
    - 10 x €8
    - 20 x €6
    - 50 x €4.5
    - 100 x €3
    - 200 x €2.5
    """
    desired = [
        ("Acquisto N. 1 Dataset", 1, 15.0, PackageSize.SINGLE),
        ("Acquisto N. 3 Dataset", 3, 12.0, PackageSize.SMALL),
        ("Acquisto N. 5 Dataset", 5, 10.0, PackageSize.MEDIUM),
        ("Acquisto N. 10 Dataset", 10, 8.0, PackageSize.XL),
        ("Acquisto N. 20 Dataset", 20, 6.0, PackageSize.XXXL),
        ("Acquisto N. 50 Dataset", 50, 4.5, PackageSize.MEGA),
        ("Acquisto N. 100 Dataset", 100, 3.0, PackageSize.ULTRA),
        ("Acquisto N. 200 Dataset", 200, 2.5, PackageSize.HYPER),
    ]

    all_pkgs = db.query(DatasetPackage).all()
    existing = {p.dataset_count: p for p in all_pkgs}
    changed = False

    for name, count, unit_price, size in desired:
        total_price = round(unit_price * count, 2)
        pkg = existing.get(count)
        if not pkg:
            db.add(DatasetPackage(
                name=name,
                size=size,
                dataset_count=count,
                price=total_price,
                currency="EUR",
                description=f"Promo € {unit_price} c.u. · Totale € {total_price}",
                is_active=True,
            ))
            changed = True
        else:
            # Keep it aligned with commercial catalog
            new_desc = f"Promo € {unit_price} c.u. · Totale € {total_price}"
            if (
                pkg.name != name or
                int(pkg.dataset_count) != int(count) or
                float(pkg.price) != float(total_price) or
                pkg.currency != "EUR" or
                pkg.size != size or
                pkg.description != new_desc or
                pkg.is_active is not True
            ):
                pkg.name = name
                pkg.size = size
                pkg.dataset_count = count
                pkg.price = total_price
                pkg.currency = "EUR"
                pkg.description = new_desc
                pkg.is_active = True
                changed = True

    if changed:
        db.commit()
        logger.info("✅ Ensured commercial packages catalog")

    # Deactivate any other packages not part of the commercial catalog (avoid confusion in UI)
    desired_counts = {c for _, c, _, _ in desired}
    deactivate_changed = False
    for pkg in all_pkgs:
        if pkg.dataset_count not in desired_counts and pkg.is_active:
            pkg.is_active = False
            deactivate_changed = True
    if deactivate_changed:
        db.commit()
        logger.info("✅ Deactivated non-commercial packages")


def consume_package_credit(db: Session, user_package: UserPackage) -> None:
    """Consume one dataset credit from user package."""
    if not user_package.can_create_dataset():
        raise ValueError("Cannot consume credit: package exhausted or expired")
    
    user_package.consume_credit()
    db.commit()
    
    logger.info(f"Consumed credit from package {user_package.id}. Remaining: {user_package.remaining_datasets}")

