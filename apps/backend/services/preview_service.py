"""Dataset preview service (extract sample rows from bundle)."""
from __future__ import annotations

import io
import zipfile
import csv
from typing import List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from uuid import UUID

from db.models.dataset import DatasetRequest, DatasetStep, StepType, StepStatus
from db.models.payment import Payment, PaymentStatus
from services.storage_service import s3_client
from core.config import settings


def _is_unlocked(db: Session, dataset: DatasetRequest) -> bool:
    if dataset.status.value == "paid":
        return True
    paid = db.query(Payment).filter(
        Payment.dataset_request_id == dataset.id,
        Payment.status == PaymentStatus.COMPLETED
    ).first()
    return paid is not None


def get_dataset_preview(
    db: Session,
    dataset_id: UUID,
    user_id: UUID,
    max_rows: int = 100,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Return preview metadata and rows.

    If locked, only 15% of the extracted rows are returned and watermark flag is true.
    """
    dataset = db.query(DatasetRequest).filter(
        DatasetRequest.id == dataset_id,
        DatasetRequest.user_id == user_id
    ).first()
    if not dataset:
        raise ValueError("Dataset not found")

    export_step = db.query(DatasetStep).filter(
        DatasetStep.dataset_request_id == dataset.id,
        DatasetStep.step_type == StepType.EXPORT,
        DatasetStep.status == StepStatus.SUCCESS
    ).first()

    if not export_step or not export_step.output_data or not export_step.output_data.get("bundle_path"):
        raise ValueError("Dataset bundle not available yet")

    bundle_path = export_step.output_data["bundle_path"]

    obj = s3_client.get_object(Bucket=settings.s3_bucket, Key=bundle_path)
    zip_bytes = obj["Body"].read()

    # Extract dataset.csv from bundle.zip
    csv_bytes: bytes | None = None
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        # Prefer dataset.csv at root or under common folders
        candidates = [n for n in zf.namelist() if n.lower().endswith("dataset.csv")]
        if not candidates:
            # fallback: any csv
            candidates = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not candidates:
            raise ValueError("No CSV found in bundle")
        csv_name = sorted(candidates, key=len)[0]
        csv_bytes = zf.read(csv_name)

    rows: List[Dict[str, Any]] = []
    with io.StringIO(csv_bytes.decode("utf-8", errors="replace")) as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(r)

    unlocked = _is_unlocked(db, dataset)
    preview_percent = 100 if unlocked else 15
    watermark = not unlocked

    # Apply gating on returned rows
    if not unlocked and rows:
        visible = max(1, round(len(rows) * (preview_percent / 100.0)))
        rows = rows[:visible]

    meta = {
        "dataset_id": str(dataset.id),
        "status": dataset.status.value,
        "can_download": bool(unlocked),
        "preview_percent": preview_percent,
        "watermark": watermark,
        "row_count": export_step.output_data.get("row_count"),
    }
    return meta, rows

