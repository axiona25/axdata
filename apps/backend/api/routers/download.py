"""Download endpoints for datasets and invoices."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import uuid
import logging

from db.session import get_db
from db.models.user import User
from db.models.dataset import DatasetRequest, DatasetStatus
from db.models.payment import Payment, PaymentStatus
from db.models.audit_log import AuditLog, AuditAction
from core.dependencies import get_current_active_user
from services.storage_service import generate_signed_url
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/download", tags=["download"])


def log_audit(
    db: Session,
    user_id: uuid.UUID,
    action: AuditAction,
    resource_type: str = None,
    resource_id: uuid.UUID = None,
    trace_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    metadata: dict = None
):
    """Create audit log entry."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        trace_id=trace_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_metadata=metadata or {}
    )
    db.add(audit)
    db.commit()


@router.get("/datasets/{dataset_id}")
async def download_dataset(
    dataset_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download dataset bundle.
    
    Requires:
    - Ownership verification
    - Payment verification (status = paid)
    """
    # Get dataset
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check payment status
    if dataset.status != DatasetStatus.PAID:
        # Check if there's a completed payment
        payment = db.query(Payment).filter(
            Payment.dataset_request_id == dataset.id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment required to download this dataset"
            )
    
    # Get bundle path from export step
    export_step = next(
        (s for s in dataset.steps if s.step_type.value == "export" and s.status.value == "success"),
        None
    )
    
    if not export_step or not export_step.output_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset bundle not found"
        )
    
    bundle_path = export_step.output_data.get("bundle_path")
    if not bundle_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle path not found"
        )
    
    # Generate signed URL
    try:
        signed_url = generate_signed_url(
            s3_key=bundle_path,
            expiration=settings.signed_url_ttl
        )
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        log_audit(
            db=db,
            user_id=current_user.id,
            action=AuditAction.DATASET_DOWNLOAD,
            resource_type="dataset",
            resource_id=dataset.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "dataset_id": str(dataset.id),
                "dataset_title": dataset.title,
                "bundle_path": bundle_path,
                "file_size": export_step.output_data.get("file_size")
            }
        )
        
        logger.info(f"Generated download URL for dataset {dataset_id} for user {current_user.id}")
        
        return {
            "download_url": signed_url,
            "expires_in": settings.signed_url_ttl,
            "dataset_id": dataset_id,
            "file_size": export_step.output_data.get("file_size"),
            "trace_id": trace_id
        }
    
    except Exception as e:
        logger.error(f"Error generating download URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating download URL"
        )

