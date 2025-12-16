"""Purge tasks for GDPR compliance."""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from db.session import SessionLocal
from db.models.user import User, UserProfile
from db.models.chat import ChatSession, ChatMessage
from db.models.dataset import DatasetRequest
from db.models.payment import Payment
from db.models.invoice import Invoice
from db.models.audit_log import AuditLog
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="purge_deleted_users")
def purge_deleted_users(retention_days: int = 30):
    """
    Purge users deleted more than retention_days ago.
    
    GDPR compliant: permanently deletes user data after retention period.
    
    Args:
        retention_days: Number of days to retain deleted user data (default: 30)
    """
    db: Session = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Find users to purge
        users_to_purge = db.query(User).filter(
            User.deleted_at.isnot(None),
            User.deleted_at <= cutoff_date
        ).all()
        
        logger.info(f"Found {len(users_to_purge)} users to purge (deleted before {cutoff_date})")
        
        for user in users_to_purge:
            user_id = user.id
            
            # Delete related data
            # 1. Chat sessions and messages
            db.query(ChatMessage).filter(ChatMessage.chat_session_id.in_(
                db.query(ChatSession.id).filter(ChatSession.user_id == user_id)
            )).delete(synchronize_session=False)
            db.query(ChatSession).filter(ChatSession.user_id == user_id).delete()
            
            # 2. Dataset requests (soft delete - set status to cancelled)
            db.query(DatasetRequest).filter(DatasetRequest.user_id == user_id).update({
                DatasetRequest.status: "cancelled"
            }, synchronize_session=False)
            
            # 3. Anonymize payments (keep for accounting, remove personal data)
            db.query(Payment).filter(Payment.user_id == user_id).update({
                Payment.payment_metadata: {"anonymized": True, "user_deleted": True}
            }, synchronize_session=False)
            
            # 4. Anonymize invoices (keep for accounting)
            db.query(Invoice).filter(Invoice.user_id == user_id).update({
                Invoice.invoice_metadata: {"anonymized": True, "user_deleted": True}
            }, synchronize_session=False)
            
            # 5. Anonymize audit logs (remove user_id reference)
            db.query(AuditLog).filter(AuditLog.user_id == user_id).update({
                AuditLog.user_id: None,
                AuditLog.extra_metadata: {"anonymized": True, "original_user_deleted": True}
            }, synchronize_session=False)
            
            # 6. Delete user profile
            db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
            
            # 7. Finally, delete user
            db.delete(user)
            
            logger.info(f"Purged user {user_id} and all associated data")
        
        db.commit()
        logger.info(f"Purge completed: {len(users_to_purge)} users permanently deleted")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during user purge: {e}", exc_info=True)
        raise
    finally:
        db.close()

