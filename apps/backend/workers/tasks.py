"""Celery tasks for dataset processing."""
import logging
import json
from typing import Dict, Any
from workers.celery_app import celery_app
from db.session import SessionLocal
from db.models.dataset import DatasetRequest, DatasetStep, DatasetStatus, StepStatus, StepType
from services.dataset_service import update_dataset_status, update_step_status
from core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_dataset_request")
def process_dataset_request(self, dataset_id: str):
    """
    Process a dataset request: enqueue collect steps.
    
    Args:
        dataset_id: Dataset request UUID as string
    """
    db = SessionLocal()
    try:
        dataset = db.query(DatasetRequest).filter(DatasetRequest.id == dataset_id).first()
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            return
        
        # Update status to running
        update_dataset_status(db, dataset.id, DatasetStatus.RUNNING)
        
        # Enqueue collect steps
        collect_steps = [
            step for step in dataset.steps
            if step.step_type == StepType.COLLECT and step.status == StepStatus.QUEUED
        ]
        
        for step in collect_steps:
            execute_collect_step.delay(str(step.id))
        
        logger.info(f"Enqueued {len(collect_steps)} collect steps for dataset {dataset_id}")
    
    except Exception as e:
        logger.error(f"Error processing dataset request {dataset_id}: {e}", exc_info=True)
        update_dataset_status(db, dataset.id, DatasetStatus.FAILED, str(e))
    finally:
        db.close()


@celery_app.task(bind=True, name="execute_collect_step")
def execute_collect_step(self, step_id: str):
    """
    Execute a collect step.
    
    Args:
        step_id: Step UUID as string
    """
    db = SessionLocal()
    try:
        step = db.query(DatasetStep).filter(DatasetStep.id == step_id).first()
        if not step:
            logger.error(f"Step {step_id} not found")
            return
        
        # Update step status to running
        update_step_status(db, step.id, StepStatus.RUNNING)
        
        # Call collector service
        import httpx
        from core.config import settings
        
        collector_url = getattr(settings, 'collector_url', 'http://localhost:8001')
        connector_name = step.input_data.get('connector')
        query = step.input_data.get('queries', [{}])[0] if step.input_data.get('queries') else {}
        
        logger.info(f"Calling collector service for step {step_id}, connector {connector_name}")
        
        try:
            # Call collector API
            with httpx.Client(timeout=300.0) as client:
                response = client.post(
                    f"{collector_url}/collect",
                    json={
                        "connector_name": connector_name,
                        "query": query,
                        "dataset_step_id": str(step.id)
                    }
                )
                response.raise_for_status()
                result = response.json()
            
            # Save output
            output_data = {
                "row_count": result.get("row_count", 0),
                "storage_path": result.get("storage_path"),
                "metadata": result.get("metadata", {}),
                "provenance": result.get("provenance", {})
            }
            
            update_step_status(db, step.id, StepStatus.SUCCESS, output_data)
            logger.info(f"Collect step {step_id} completed: {result.get('row_count')} rows")
        
        except Exception as e:
            logger.error(f"Error calling collector service: {e}", exc_info=True)
            update_step_status(db, step.id, StepStatus.FAILED, None, str(e))
            update_dataset_status(db, step.dataset_request_id, DatasetStatus.FAILED, str(e))
            return
        
        # Check if all collect steps are done, then enqueue normalize
        dataset = step.dataset_request
        collect_steps = [s for s in dataset.steps if s.step_type == StepType.COLLECT]
        if all(s.status == StepStatus.SUCCESS for s in collect_steps):
            normalize_step = next(
                (s for s in dataset.steps if s.step_type == StepType.NORMALIZE),
                None
            )
            if normalize_step:
                execute_normalize_step.delay(str(normalize_step.id))
    
    except Exception as e:
        logger.error(f"Error executing collect step {step_id}: {e}", exc_info=True)
        update_step_status(db, step.id, StepStatus.FAILED, str(e))
        update_dataset_status(db, step.dataset_request_id, DatasetStatus.FAILED, str(e))
    finally:
        db.close()


@celery_app.task(bind=True, name="execute_normalize_step")
def execute_normalize_step(self, step_id: str):
    """
    Execute a normalize step.
    
    Args:
        step_id: Step UUID as string
    """
    db = SessionLocal()
    try:
        step = db.query(DatasetStep).filter(DatasetStep.id == step_id).first()
        if not step:
            logger.error(f"Step {step_id} not found")
            return
        
        update_step_status(db, step.id, StepStatus.RUNNING)
        
        # Get dataset to determine domain
        dataset = step.dataset_request
        domain = dataset.domain
        
        # Get normalizer
        from normalizers.registry import get_normalizer
        normalizer = get_normalizer(domain)
        
        if not normalizer:
            raise ValueError(f"No normalizer found for domain: {domain}")
        
        # Get records from previous collect steps (raw assets)
        collect_steps = [
            s for s in dataset.steps
            if s.step_type == StepType.COLLECT and s.status == StepStatus.SUCCESS
        ]
        
        # Build raw_assets list for normalizer
        raw_assets = []
        for collect_step in collect_steps:
            if collect_step.output_data:
                # Load data from storage (in production, use proper loader)
                storage_path = collect_step.output_data.get("storage_path")
                metadata = collect_step.output_data.get("metadata", {})
                provenance = collect_step.output_data.get("provenance", {})
                
                # For now, create asset structure
                # In production, load actual data from storage_path
                asset = {
                    "data": [],  # Will be loaded from storage in production
                    "source": {
                        "connector": collect_step.input_data.get("connector"),
                        "queries": collect_step.input_data.get("queries", [])
                    },
                    "metadata": metadata,
                    "provenance": provenance,
                    "storage_path": storage_path
                }
                raw_assets.append(asset)
        
        # Get dataset plan
        plan = dataset.plan_json if isinstance(dataset.plan_json, dict) else {}
        
        # Apply normalization using normalizer interface
        normalized_data = normalizer.normalize(raw_assets, plan)
        
        # Validate normalized data
        normalizer.validate(normalized_data)
        
        # Build data dictionary
        data_dictionary_columns = normalizer.build_data_dictionary(normalized_data)
        
        # Convert to records format (for compatibility)
        if hasattr(normalized_data, 'to_dict'):
            # It's a DataFrame
            normalized_records = normalized_data.to_dict('records')
        elif isinstance(normalized_data, list):
            normalized_records = normalized_data
        else:
            normalized_records = []
        
        output_data = {
            "normalized_row_count": len(normalized_records),
            "data_dictionary_columns": data_dictionary_columns,
            "transformations_applied": len(transformations),
            "records": normalized_records  # In production, save to storage
        }
        
        update_step_status(db, step.id, StepStatus.SUCCESS, output_data)
        
        # Enqueue export step
        dataset = step.dataset_request
        export_step = next(
            (s for s in dataset.steps if s.step_type == StepType.EXPORT),
            None
        )
        if export_step:
            execute_export_step.delay(str(export_step.id))
    
    except Exception as e:
        logger.error(f"Error executing normalize step {step_id}: {e}", exc_info=True)
        update_step_status(db, step.id, StepStatus.FAILED, str(e))
        update_dataset_status(db, step.dataset_request_id, DatasetStatus.FAILED, str(e))
    finally:
        db.close()


@celery_app.task(bind=True, name="execute_export_step")
def execute_export_step(self, step_id: str):
    """
    Execute an export step.
    
    Args:
        step_id: Step UUID as string
    """
    db = SessionLocal()
    try:
        step = db.query(DatasetStep).filter(DatasetStep.id == step_id).first()
        if not step:
            logger.error(f"Step {step_id} not found")
            return
        
        update_step_status(db, step.id, StepStatus.RUNNING)
        
        # Get dataset
        dataset = step.dataset_request
        
        # Get normalized records from normalize step
        normalize_step = next(
            (s for s in dataset.steps if s.step_type == StepType.NORMALIZE),
            None
        )
        
        if not normalize_step or normalize_step.status != StepStatus.SUCCESS:
            raise ValueError("Normalize step must be completed before export")
        
        records = normalize_step.output_data.get("records", [])
        
        # Generate manifest
        from services.export_service import (
            generate_manifest,
            generate_data_dictionary,
            create_bundle
        )
        from services.storage_service import s3_client, save_bundle_to_storage
        
        # Get sources from collect steps
        collect_steps = [
            s for s in dataset.steps
            if s.step_type == StepType.COLLECT and s.status == StepStatus.SUCCESS
        ]
        sources = []
        provenance_list = []
        for collect_step in collect_steps:
            if collect_step.output_data:
                sources.append({
                    "connector": collect_step.input_data.get("connector"),
                    "row_count": collect_step.output_data.get("metadata", {}).get("row_count", 0)
                })
                provenance_list.append(collect_step.output_data.get("provenance", {}))
        
        # Get normalizer metadata for enhanced manifest
        from normalizers.registry import get_normalizer_metadata
        normalizer_metadata = get_normalizer_metadata(dataset.domain)
        
        # Extract methodology and coverage from plan if available
        plan = dataset.plan_json if isinstance(dataset.plan_json, dict) else {}
        methodology = plan.get("methodology") or (normalizer_metadata.get("description") if normalizer_metadata else None)
        
        # Generate FAIR-compliant manifest
        manifest = generate_manifest(
            dataset_id=str(dataset.id),
            title=dataset.title,
            domain=dataset.domain,
            sources=sources,
            transformations=normalize_step.input_data.get("transformations", []),
            outputs=step.input_data.get("outputs", []),
            row_count=len(records),
            created_at=dataset.created_at,
            methodology=methodology,
            license=plan.get("license"),
            citation=plan.get("citation"),
            geographic_coverage=plan.get("geographic_coverage"),
            temporal_coverage=plan.get("temporal_coverage"),
            version=plan.get("version", "1.0")
        )
        
        # Generate comprehensive data dictionary with domain-specific metadata
        indicators_metadata = plan.get("indicators_metadata", {})
        data_dictionary = generate_data_dictionary(
            records=records,
            domain=dataset.domain,
            indicators_metadata=indicators_metadata
        )
        
        # Generate comprehensive provenance
        from services.export_service import generate_provenance
        provenance = generate_provenance(
            sources=sources,
            transformations=normalize_step.input_data.get("transformations", []),
            created_at=dataset.created_at,
            dataset_id=str(dataset.id)
        )
        
        # Generate README if domain-specific documentation needed
        readme_content = None
        if dataset.domain in ["physics", "math"]:
            # Physics and ML datasets benefit from scientific README
            readme_content = f"""# {dataset.title}

## Dataset Overview

**Domain**: {dataset.domain}
**Version**: {manifest.get('version', '1.0')}
**Created**: {manifest.get('created_at', 'unknown')}
**Rows**: {manifest.get('row_count', 0)}

## Standards Compliance

This dataset follows:
- **FAIR Principles**: Findable, Accessible, Interoperable, Reusable
- **Domain Standard**: {manifest.get('standards', {}).get('domain_standard', 'FAIR Data Principles')}

## Methodology

{manifest.get('methodology', 'See manifest.json for details')}

## Files

- `{dataset.id}.csv` - CSV format
- `{dataset.id}.json` - JSON format
- `{dataset.id}.parquet` - Parquet format (if available)
- `manifest.json` - Complete dataset metadata (FAIR-compliant)
- `data_dictionary.json` - Column definitions and metadata
- `provenance.json` - Data lineage and transformations

## Citation

{manifest.get('citation', 'Please cite according to source licenses')}

## License

{manifest.get('license', 'See source licenses')}
"""
        
        # Check if dataset uses AXDATA DS-SPEC and use appropriate packager
        from services.axdata_export_integration import integrate_axdata_export
        
        bundle_data = integrate_axdata_export(
            records=records,
            dataset_id=str(dataset.id),
            plan_json=plan,
            sources=sources,
            outputs=step.input_data.get("outputs", []),
            use_axdata_if_available=True
        )
        
        # Save bundle to storage
        from core.config import settings
        bundle_path = save_bundle_to_storage(
            bundle_data=bundle_data,
            dataset_id=str(dataset.id),
            bucket=settings.s3_bucket,
            s3_client=s3_client
        )
        
        output_data = {
            "formats": step.input_data.get("outputs", []),
            "bundle_path": bundle_path,
            "file_size": len(bundle_data),
            "row_count": len(records)
        }
        
        update_step_status(db, step.id, StepStatus.SUCCESS, output_data)
        
        # Update dataset status to ready_for_payment
        update_dataset_status(db, step.dataset_request_id, DatasetStatus.READY_FOR_PAYMENT)
        
        logger.info(f"Dataset {step.dataset_request_id} ready for payment")
    
    except Exception as e:
        logger.error(f"Error executing export step {step_id}: {e}", exc_info=True)
        update_step_status(db, step.id, StepStatus.FAILED, str(e))
        update_dataset_status(db, step.dataset_request_id, DatasetStatus.FAILED, str(e))
    finally:
        db.close()

