"""Celery application configuration."""
from celery import Celery
from core.config import settings

# Create Celery app
celery_app = Celery(
    "dataset_portal",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
    include=["workers.tasks", "workers.purge_tasks"]
)

# Load beat schedule
from workers.celerybeat_schedule import beat_schedule
celery_app.conf.beat_schedule = beat_schedule
celery_app.conf.timezone = 'UTC'

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

