"""Add app_assets table for branding assets.

Revision ID: 010_app_assets
Revises: 009_invoice_packages
Create Date: 2025-12-14 21:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "010_app_assets"
down_revision = "009_invoice_packages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_app_assets_key", "app_assets", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_app_assets_key", table_name="app_assets")
    op.drop_table("app_assets")

