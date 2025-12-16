"""Celery Beat schedule configuration."""
from celery.schedules import crontab
from core.config import settings

# Celery Beat schedule
beat_schedule = {
    'purge-deleted-users': {
        'task': 'purge_deleted_users',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (settings.user_purge_retention_days,)
    },
}

