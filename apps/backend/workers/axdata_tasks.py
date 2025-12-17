"""Celery tasks for AXDATA pipeline processing."""
import logging
import uuid
from typing import Dict, Any
from pathlib import Path
from workers.celery_app import celery_app
from db.session import SessionLocal
from db.models.dataset import DatasetRequest, DatasetStatus
from services.dataset_service import update_dataset_status
from services.axdata_service import create_dataset_with_axdata_pipeline, package_dataset_from_pipeline
from services.storage_service import s3_client, save_bundle_to_storage
from core.config import settings
from axdata.spec.ds_spec import DatasetSpec
import tempfile
import shutil

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_axdata_dataset_request")
def process_axdata_dataset_request(self, dataset_id: str):
    """
    Process an AXDATA dataset request using the full pipeline.
    
    This task:
    1. Loads DS-SPEC from dataset
    2. Runs AXDATA pipeline (collect → transform → package)
    3. Packages dataset with standard structure
    4. Saves to storage
    5. Updates dataset status
    
    Args:
        dataset_id: Dataset request UUID as string
    """
    db = SessionLocal()
    try:
        dataset = db.query(DatasetRequest).filter(DatasetRequest.id == dataset_id).first()
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            return
        
        # Check if this is an AXDATA dataset (has DS-SPEC)
        plan_json = dataset.plan_json if isinstance(dataset.plan_json, dict) else {}
        
        if not (plan_json.get("version") == "1.0" and "dimensions" in plan_json):
            logger.warning(f"Dataset {dataset_id} is not an AXDATA dataset, skipping AXDATA pipeline")
            return
        
        # Update status to running
        update_dataset_status(db, dataset.id, DatasetStatus.RUNNING)
        
        # Load DS-SPEC
        try:
            ds_spec = DatasetSpec(**plan_json)
        except Exception as e:
            logger.error(f"Invalid DS-SPEC in dataset {dataset_id}: {e}")
            update_dataset_status(db, dataset.id, DatasetStatus.FAILED, f"Invalid DS-SPEC: {e}")
            return
        
        # Run AXDATA pipeline
        logger.info(f"Running AXDATA pipeline for dataset {dataset_id}")
        pipeline_result = create_dataset_with_axdata_pipeline(
            ds_spec=ds_spec,
            top_n_sources=3
        )
        
        if "error" in pipeline_result:
            error_msg = pipeline_result.get("error", "Pipeline error")
            logger.error(f"Pipeline error for dataset {dataset_id}: {error_msg}")
            update_dataset_status(db, dataset.id, DatasetStatus.FAILED, error_msg)
            return
        
        # Package dataset
        logger.info(f"Packaging dataset {dataset_id}")
        with tempfile.TemporaryDirectory() as tmpdir:
            packaged = package_dataset_from_pipeline(
                pipeline_result=pipeline_result,
                ds_spec=ds_spec,
                out_dir=tmpdir,
                dataset_filename="dataset.csv"
            )
            
            # Read ZIP file
            zip_path = Path(packaged["zip_path"])
            if not zip_path.exists():
                raise FileNotFoundError(f"Package ZIP not found: {zip_path}")
            
            zip_bytes = zip_path.read_bytes()
            
            # Save to storage
            bundle_path = save_bundle_to_storage(
                bundle_data=zip_bytes,
                dataset_id=str(dataset.id),
                bucket=settings.s3_bucket,
                s3_client=s3_client
            )
            
            logger.info(f"Dataset {dataset_id} packaged and saved to {bundle_path}")
        
        # Update dataset with pipeline result
        dataset.plan_json = {
            **plan_json,
            "pipeline_result": pipeline_result,
            "bundle_path": bundle_path
        }

        # If dataset has a consumed credit (user_package_id set), mark as PAID; else keep gated.
        final_status = DatasetStatus.PAID if dataset.user_package_id else DatasetStatus.READY_FOR_PAYMENT
        update_dataset_status(db, dataset.id, final_status)
        
        logger.info(f"AXDATA pipeline completed for dataset {dataset_id}")
    
    except Exception as e:
        logger.error(f"Error processing AXDATA dataset {dataset_id}: {e}", exc_info=True)
        update_dataset_status(db, dataset.id, DatasetStatus.FAILED, str(e))
    finally:
        db.close()
