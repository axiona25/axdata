"""add wallet transactions

Revision ID: 011_wallet_transactions
Revises: 010_app_assets
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "011_wallet_transactions"
down_revision = "010_app_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tx_type", sa.Enum("credit", "debit", name="wallettxtype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "confirmed", "failed", name="wallettxstatus"), nullable=False, server_default="confirmed"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_wallet_transactions_user_id", "wallet_transactions", ["user_id"])
    op.create_index("ix_wallet_transactions_tx_type", "wallet_transactions", ["tx_type"])
    op.create_index("ix_wallet_transactions_status", "wallet_transactions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_wallet_transactions_status", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_tx_type", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_user_id", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")
    op.execute("DROP TYPE IF EXISTS wallettxstatus")
    op.execute("DROP TYPE IF EXISTS wallettxtype")

