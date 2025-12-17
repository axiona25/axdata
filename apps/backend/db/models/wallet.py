"""Virtual wallet ledger models."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from db.session import Base


class WalletTxType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class WalletTxStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class WalletTransaction(Base):
    """Ledger entry for user's virtual wallet."""
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    tx_type = Column(SQLEnum(WalletTxType), nullable=False, index=True)
    status = Column(SQLEnum(WalletTxStatus), nullable=False, default=WalletTxStatus.CONFIRMED, index=True)

    amount = Column(Numeric(10, 2), nullable=False)  # always positive
    currency = Column(String(3), nullable=False, default="EUR")
    description = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="wallet_transactions")

