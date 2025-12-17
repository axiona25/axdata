"""Dataset orchestration service."""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from db.models.dataset import DatasetRequest, DatasetStep, DatasetStatus, StepStatus, StepType
from schemas.dataset_plan import DatasetPlan
from services.package_service import get_user_active_package, consume_package_credit
import uuid

logger = logging.getLogger(__name__)


def create_dataset_request_from_plan(
    db: Session,
    user_id: uuid.UUID,
    plan: DatasetPlan,
    chat_session_id: Optional[uuid.UUID] = None
) -> DatasetRequest:
    """
    Create a dataset request from a DatasetPlan.
    
    Args:
        db: Database session
        user_id: User ID
        plan: DatasetPlan
        chat_session_id: Optional chat session ID
    
    Returns:
        Created DatasetRequest
    
    Notes:
        - Dataset creation is always allowed.
        - If user has an active package with remaining credits, one credit is consumed and the dataset is marked as payable/unlocked.
        - If user has no credits, the dataset will be gated (status will end in READY_FOR_PAYMENT).
    """
    # Try to attach an active package (consumption-based, domains not enforced)
    user_package = get_user_active_package(db, user_id)
    if user_package and user_package.can_create_dataset():
        consume_package_credit(db, user_package)
    else:
        user_package = None
    
    # Create dataset request
    dataset_request = DatasetRequest(
        user_id=user_id,
        chat_session_id=chat_session_id,
        user_package_id=user_package.id if user_package else None,
        title=plan.title,
        domain=plan.domain.value,
        plan_json=plan.dict(),
        status=DatasetStatus.DRAFT
    )
    db.add(dataset_request)
    db.flush()
    
    # Create steps from plan
    steps = []
    
    # Collect step for each source
    for idx, source in enumerate(plan.sources):
        step = DatasetStep(
            dataset_request_id=dataset_request.id,
            step_type=StepType.COLLECT,
            step_order=idx,
            status=StepStatus.QUEUED,
            input_data={
                "connector": source.connector,
                "queries": source.queries
            }
        )
        steps.append(step)
        db.add(step)
    
    # Normalize step
    if plan.transformations:
        normalize_step = DatasetStep(
            dataset_request_id=dataset_request.id,
            step_type=StepType.NORMALIZE,
            step_order=len(steps),
            status=StepStatus.QUEUED,
            input_data={
                "transformations": [t.dict() for t in plan.transformations]
            }
        )
        steps.append(normalize_step)
        db.add(normalize_step)
    
    # Export step
    export_step = DatasetStep(
        dataset_request_id=dataset_request.id,
        step_type=StepType.EXPORT,
        step_order=len(steps),
        status=StepStatus.QUEUED,
        input_data={
            "outputs": plan.outputs,
            "documentation": plan.documentation
        }
    )
    steps.append(export_step)
    db.add(export_step)
    
    db.commit()
    db.refresh(dataset_request)
    
    logger.info(f"Created dataset request {dataset_request.id} with {len(steps)} steps")
    
    return dataset_request


def update_dataset_status(
    db: Session,
    dataset_id: uuid.UUID,
    new_status: DatasetStatus,
    error_message: Optional[str] = None
) -> DatasetRequest:
    """
    Update dataset request status with state machine validation.
    
    Args:
        db: Database session
        dataset_id: Dataset request ID
        new_status: New status
        error_message: Optional error message
    
    Returns:
        Updated DatasetRequest
    """
    dataset = db.query(DatasetRequest).filter(DatasetRequest.id == dataset_id).first()
    if not dataset:
        raise ValueError(f"Dataset {dataset_id} not found")
    
    # State machine transitions
    valid_transitions = {
        DatasetStatus.DRAFT: [DatasetStatus.RUNNING, DatasetStatus.FAILED],
        DatasetStatus.RUNNING: [DatasetStatus.READY_FOR_PAYMENT, DatasetStatus.PAID, DatasetStatus.FAILED],
        DatasetStatus.READY_FOR_PAYMENT: [DatasetStatus.PAID, DatasetStatus.FAILED],
        DatasetStatus.PAID: [DatasetStatus.DELIVERED, DatasetStatus.FAILED],
        DatasetStatus.DELIVERED: [],
        DatasetStatus.FAILED: []
    }
    
    if new_status not in valid_transitions.get(dataset.status, []):
        raise ValueError(
            f"Invalid transition from {dataset.status} to {new_status}"
        )
    
    dataset.status = new_status
    if error_message:
        dataset.error_message = error_message
    
    db.commit()
    db.refresh(dataset)
    
    logger.info(f"Updated dataset {dataset_id} status: {dataset.status} -> {new_status}")
    
    return dataset


def update_step_status(
    db: Session,
    step_id: uuid.UUID,
    new_status: StepStatus,
    output_data: Optional[dict] = None,
    error_message: Optional[str] = None
) -> DatasetStep:
    """
    Update dataset step status.
    
    Args:
        db: Database session
        step_id: Step ID
        new_status: New status
        output_data: Optional output data
        error_message: Optional error message
    
    Returns:
        Updated DatasetStep
    """
    step = db.query(DatasetStep).filter(DatasetStep.id == step_id).first()
    if not step:
        raise ValueError(f"Step {step_id} not found")
    
    step.status = new_status
    if output_data:
        step.output_data = output_data
    if error_message:
        step.error_message = error_message
    
    from datetime import datetime
    if new_status == StepStatus.RUNNING and not step.started_at:
        step.started_at = datetime.utcnow()
    if new_status in [StepStatus.SUCCESS, StepStatus.FAILED]:
        step.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(step)
    
    logger.info(f"Updated step {step_id} status: {step.status} -> {new_status}")
    
    return step

