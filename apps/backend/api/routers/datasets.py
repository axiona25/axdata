"""Dataset endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from db.session import get_db
from db.models.user import User
from db.models.dataset import DatasetRequest, DatasetStatus
from db.models.audit_log import AuditLog, AuditAction
from core.dependencies import get_current_active_user
from schemas.dataset import (
    DatasetRequestCreate,
    DatasetRequestResponse,
    DatasetRequestDetailResponse,
    DatasetProgressResponse,
    DatasetStepResponse
)
from services.dataset_service import create_dataset_request_from_plan
from workers.tasks import process_dataset_request
from schemas.dataset_plan import DatasetPlan
from schemas.ds_spec_schema import DatasetSpecCreate, DatasetSpecResponse
from services.axdata_service import convert_dataset_plan_to_ds_spec, create_dataset_with_axdata_pipeline
from db.models.payment import Payment, PaymentStatus
from services.preview_service import get_dataset_preview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("", response_model=DatasetRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a dataset request from a DatasetPlan."""
    try:
        chat_session_id = None
        if dataset_data.chat_session_id:
            chat_session_id = uuid.UUID(dataset_data.chat_session_id)

        # Dataset creation is always allowed; credits (if any) will be consumed inside the service.
        dataset = create_dataset_request_from_plan(
            db=db,
            user_id=current_user.id,
            plan=dataset_data.plan,
            chat_session_id=chat_session_id
        )
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        audit = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DATASET_CREATE,
            resource_type="dataset",
            resource_id=dataset.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            extra_metadata={
                "dataset_id": str(dataset.id),
                "title": dataset.title,
                "domain": dataset.domain
            }
        )
        db.add(audit)
        db.commit()
        
        # Enqueue AXDATA pipeline processing
        from workers.axdata_tasks import process_axdata_dataset_request
        process_axdata_dataset_request.delay(str(dataset.id))
        
        return DatasetRequestResponse(
            id=str(dataset.id),
            user_id=str(dataset.user_id),
            chat_session_id=str(dataset.chat_session_id) if dataset.chat_session_id else None,
            title=dataset.title,
            domain=dataset.domain,
            status=dataset.status.value,
            error_message=dataset.error_message,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            step_count=len(dataset.steps)
        )
    
    except Exception as e:
        logger.error(f"Error creating dataset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dataset: {str(e)}"
        )


@router.get("", response_model=List[DatasetRequestResponse])
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    domain_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List user's dataset requests with filters.
    
    Filters:
    - status_filter: Filter by status
    - domain_filter: Filter by domain
    - start_date: Filter datasets created from this date
    - end_date: Filter datasets created until this date
    """
    query = db.query(DatasetRequest).filter(DatasetRequest.user_id == current_user.id)
    
    if status_filter:
        try:
            status_enum = DatasetStatus(status_filter)
            query = query.filter(DatasetRequest.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    if domain_filter:
        query = query.filter(DatasetRequest.domain == domain_filter)
    
    if start_date:
        query = query.filter(DatasetRequest.created_at >= start_date)
    
    if end_date:
        query = query.filter(DatasetRequest.created_at <= end_date)
    
    datasets = query.order_by(DatasetRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        DatasetRequestResponse(
            id=str(d.id),
            user_id=str(d.user_id),
            chat_session_id=str(d.chat_session_id) if d.chat_session_id else None,
            title=d.title,
            domain=d.domain,
            status=d.status.value,
            error_message=d.error_message,
            created_at=d.created_at,
            updated_at=d.updated_at,
            step_count=len(d.steps)
        )
        for d in datasets
    ]


@router.get("/{dataset_id}/access")
async def dataset_access(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Access policy for a dataset.

    - Dataset can always be created and processed.
    - Full preview + download require a consumed credit (package) or a completed payment.
    - Without payment/credit: preview is limited to 15% and should be watermarked.
    """
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    has_completed_payment = db.query(Payment).filter(
        Payment.dataset_request_id == dataset.id,
        Payment.status == PaymentStatus.COMPLETED
    ).first() is not None

    is_unlocked = dataset.status == DatasetStatus.PAID or has_completed_payment

    return {
        "dataset_id": str(dataset.id),
        "status": dataset.status.value,
        "can_download": bool(is_unlocked),
        "can_preview_full": bool(is_unlocked),
        "preview_percent": 100 if is_unlocked else 15,
        "watermark": False if is_unlocked else True,
        "message": "OK" if is_unlocked else "Preview limited. Purchase a package to unlock full access."
    }


@router.get("/{dataset_id}/preview")
async def dataset_preview(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Real preview rows extracted from bundle.

    Returns:
    - meta: { can_download, preview_percent, watermark, ... }
    - rows: list of dict rows (already gated when locked)
    """
    try:
        meta, rows = get_dataset_preview(
            db=db,
            dataset_id=uuid.UUID(dataset_id),
            user_id=current_user.id,
            max_rows=100,
        )
        return {"meta": meta, "rows": rows}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating preview for dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating dataset preview")


@router.get("/{dataset_id}", response_model=DatasetRequestDetailResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dataset request details."""
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return DatasetRequestDetailResponse(
        id=str(dataset.id),
        user_id=str(dataset.user_id),
        chat_session_id=str(dataset.chat_session_id) if dataset.chat_session_id else None,
        title=dataset.title,
        domain=dataset.domain,
        status=dataset.status.value,
        error_message=dataset.error_message,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        steps=[
            DatasetStepResponse(
                id=str(step.id),
                dataset_request_id=str(step.dataset_request_id),
                step_type=step.step_type.value,
                step_order=step.step_order,
                status=step.status.value,
                input_data=step.input_data,
                output_data=step.output_data,
                error_message=step.error_message,
                started_at=step.started_at,
                completed_at=step.completed_at
            )
            for step in dataset.steps
        ],
        plan=dataset.plan_json
    )


@router.get("/{dataset_id}/progress", response_model=DatasetProgressResponse)
async def get_dataset_progress(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dataset processing progress."""
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Calculate progress
    total_steps = len(dataset.steps)
    completed_steps = sum(1 for s in dataset.steps if s.status.value in ["success", "failed"])
    progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    # Find current step
    current_step = None
    for step in sorted(dataset.steps, key=lambda s: s.step_order):
        if step.status.value == "running":
            current_step = step.step_type.value
            break
        elif step.status.value == "queued":
            current_step = step.step_type.value
            break
    
    return DatasetProgressResponse(
        dataset_id=str(dataset.id),
        status=dataset.status.value,
        progress_percentage=round(progress_percentage, 2),
        current_step=current_step,
        steps=[
            DatasetStepResponse(
                id=str(step.id),
                dataset_request_id=str(step.dataset_request_id),
                step_type=step.step_type.value,
                step_order=step.step_order,
                status=step.status.value,
                input_data=step.input_data,
                output_data=step.output_data,
                error_message=step.error_message,
                started_at=step.started_at,
                completed_at=step.completed_at
            )
            for step in dataset.steps
        ],
        error_message=dataset.error_message
    )


@router.post("/{dataset_id}/clone", response_model=DatasetRequestResponse, status_code=status.HTTP_201_CREATED)
async def clone_dataset(
    dataset_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clone an existing dataset request (creates new request with same plan)."""
    # Get original dataset
    original = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Load plan from original
    plan = DatasetPlan(**original.plan_json)
    
    # Create new dataset from plan
    try:
        new_dataset = create_dataset_request_from_plan(
            db=db,
            user_id=current_user.id,
            plan=plan,
            chat_session_id=None
        )
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        audit = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DATASET_CREATE,
            resource_type="dataset",
            resource_id=new_dataset.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            extra_metadata={
                "dataset_id": str(new_dataset.id),
                "cloned_from": str(original.id),
                "title": new_dataset.title
            }
        )
        db.add(audit)
        db.commit()
        
        # Enqueue processing
        process_dataset_request.delay(str(new_dataset.id))
        
        return DatasetRequestResponse(
            id=str(new_dataset.id),
            user_id=str(new_dataset.user_id),
            chat_session_id=str(new_dataset.chat_session_id) if new_dataset.chat_session_id else None,
            title=new_dataset.title,
            domain=new_dataset.domain,
            status=new_dataset.status.value,
            error_message=new_dataset.error_message,
            created_at=new_dataset.created_at,
            updated_at=new_dataset.updated_at,
            step_count=len(new_dataset.steps)
        )
    
    except Exception as e:
        logger.error(f"Error cloning dataset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cloning dataset: {str(e)}"
        )


@router.get("/{dataset_id}/history")
async def get_dataset_history(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dataset history (steps timeline)."""
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == uuid.UUID(dataset_id),
        DatasetRequest.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Get audit logs for this dataset
    audit_logs = db.query(AuditLog).filter(
        AuditLog.resource_type == "dataset",
        AuditLog.resource_id == dataset.id,
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.created_at.asc()).all()
    
    # Build history
    history = []
    
    # Add dataset creation
    history.append({
        "timestamp": dataset.created_at,
        "action": "created",
        "status": dataset.status.value,
        "details": {"title": dataset.title}
    })
    
    # Add steps
    for step in sorted(dataset.steps, key=lambda s: s.step_order):
        if step.started_at:
            history.append({
                "timestamp": step.started_at,
                "action": f"step_{step.step_type.value}_started",
                "status": step.status.value,
                "details": {"step_order": step.step_order, "step_type": step.step_type.value}
            })
        
        if step.completed_at:
            history.append({
                "timestamp": step.completed_at,
                "action": f"step_{step.step_type.value}_completed",
                "status": step.status.value,
                "details": {"step_order": step.step_order, "step_type": step.step_type.value}
            })
    
    # Add audit events
    for log in audit_logs:
        history.append({
            "timestamp": log.created_at,
            "action": log.action.value,
            "status": None,
            "details": log.extra_metadata or {}
        })
    
    # Sort by timestamp
    history.sort(key=lambda x: x["timestamp"])
    
    return {
        "dataset_id": str(dataset.id),
        "title": dataset.title,
        "history": history
    }


@router.post(
    "/from-ds-spec",
    response_model=DatasetSpecResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create dataset from DS-SPEC",
    description="""
    Create a dataset request from DS-SPEC (AXDATA Dataset Specification v1.0).
    
    This endpoint uses the AXDATA pipeline to automatically:
    1. **Select template** - Chooses one of 8 universal templates (tabular, time_series, panel, etc.)
    2. **Select sources** - Filters and ranks 25+ public API sources based on DS-SPEC criteria
    3. **Collect data** - Fetches data from selected sources via collector service
    4. **Normalize** - Applies domain-specific standards (SDMX, CDISC, FAIR, etc.)
    5. **Transform** - Converts to selected template format
    6. **Package** - Creates ZIP with metadata.json, schema.json, quality.json, compliance.json, provenance.json
    
    **DS-SPEC Structure:**
    - `version`: "1.0" (required)
    - `request`: Query text and language
    - `sector`: Dataset sector (health, economy, physics, etc.)
    - `dimensions`: Time, geo, entity dimensions
    - `variables`: List of variables to include
    - `output`: Template preference, formats, quality/compliance settings
    
    **Example DS-SPEC:**
    ```json
    {
      "version": "1.0",
      "request": {
        "query_text": "GDP per capita in EU countries 2020-2024",
        "language": "it"
      },
      "sector": "economy",
      "dimensions": {
        "time": {"enabled": true, "start": "2020", "end": "2024", "granularity": "year"},
        "geo": {"enabled": true, "scope": "EU", "level": "country"},
        "entity": {"kind": "country", "tracking": false}
      },
      "variables": [
        {"name": "gdp_per_capita", "type": "numeric", "unit": "EUR"}
      ],
      "output": {
        "template": "auto",
        "formats": ["csv", "parquet"],
        "quality": {"min_completeness": 0.9},
        "compliance": {"allow_pii": false}
      }
    }
    ```
    
    **Response:**
    - Returns dataset request with status "running"
    - Dataset is processed asynchronously via Celery worker
    - Check progress via `/api/v1/datasets/{dataset_id}/progress`
    
    **Error Responses:**
    - `400`: Invalid DS-SPEC format
    - `402`: No active package or insufficient credits
    - `500`: Pipeline error (check error_message in response)
    """
)
async def create_dataset_from_ds_spec(
    ds_spec_data: DatasetSpecCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate and convert DS-SPEC
        ds_spec = ds_spec_data.to_ds_spec()
        
        # Extract sector (used as domain label)
        sector = ds_spec.sector

        # Credits are optional. If available, consume one and attach the user_package_id; otherwise keep it gated.
        from services.package_service import get_user_active_package, consume_package_credit
        user_package = get_user_active_package(db, current_user.id)
        if user_package and user_package.can_create_dataset():
            consume_package_credit(db, user_package)
        else:
            user_package = None
        
        # Run AXDATA pipeline
        pipeline_result = create_dataset_with_axdata_pipeline(
            ds_spec=ds_spec,
            top_n_sources=3
        )
        
        if "error" in pipeline_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=pipeline_result.get("error", "Pipeline error")
            )
        
        # Create dataset request in DB
        chat_session_id = None
        if ds_spec_data.chat_session_id:
            chat_session_id = uuid.UUID(ds_spec_data.chat_session_id)
        
        dataset = DatasetRequest(
            user_id=current_user.id,
            chat_session_id=chat_session_id,
            user_package_id=user_package.id if user_package else None,
            title=ds_spec.request.query_text[:255],  # Truncate if needed
            domain=sector,
            plan_json=ds_spec.model_dump() if hasattr(ds_spec, 'model_dump') else ds_spec.dict() if hasattr(ds_spec, 'dict') else ds_spec,  # Store DS-SPEC as plan
            status=DatasetStatus.RUNNING  # Pipeline is running
        )
        db.add(dataset)
        db.flush()
        
        # Store pipeline result in dataset metadata
        # Convert DS-SPEC to dict
        ds_spec_dict = ds_spec.model_dump() if hasattr(ds_spec, 'model_dump') else ds_spec.dict() if hasattr(ds_spec, 'dict') else ds_spec
        
        dataset.plan_json = {
            **ds_spec_dict,
            "pipeline_result": pipeline_result
        }
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        audit = AuditLog(
            user_id=current_user.id,
            action=AuditAction.DATASET_CREATE,
            resource_type="dataset",
            resource_id=dataset.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            extra_metadata={
                "dataset_id": str(dataset.id),
                "title": dataset.title,
                "domain": dataset.domain,
                "template": pipeline_result.get("template"),
                "sources": pipeline_result.get("selected_sources", [])
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(dataset)
        
        return DatasetSpecResponse(
            dataset_id=str(dataset.id),
            template=pipeline_result.get("template", "tabular"),
            selected_sources=pipeline_result.get("selected_sources", []),
            raw_count=pipeline_result.get("raw_count", 0),
            status=dataset.status.value
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dataset from DS-SPEC: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dataset: {str(e)}"
        )


@router.post("/convert-plan-to-ds-spec")
async def convert_plan_to_ds_spec_endpoint(
    plan_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Convert DatasetPlan to DS-SPEC.
    
    This endpoint is used by the frontend wizard to convert a DatasetPlan
    (generated by OpenAI from chat) into a DS-SPEC for dataset creation.
    
    Args:
        plan_data: Dictionary with "plan" key containing DatasetPlan
    
    Returns:
        DS-SPEC dictionary ready for dataset creation
    """
    try:
        plan_dict = plan_data.get("plan", plan_data)
        
        # Validate it's a DatasetPlan
        try:
            plan = DatasetPlan(**plan_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid DatasetPlan: {str(e)}"
            )
        
        # Convert to DS-SPEC
        ds_spec = convert_dataset_plan_to_ds_spec(plan.dict())
        
        # Return as dictionary
        return ds_spec.model_dump()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting plan to DS-SPEC: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting plan: {str(e)}"
        )

