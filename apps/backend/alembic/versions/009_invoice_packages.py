"""Update Invoice model to support packages.

Revision ID: 009_invoice_packages
Revises: 008_payment_packages
Create Date: 2025-12-14 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_invoice_packages'
down_revision = '008_payment_packages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make dataset_request_id nullable in invoices
    op.alter_column('invoices', 'dataset_request_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)


def downgrade() -> None:
    # Make dataset_request_id NOT NULL again (will fail if there are NULL values)
    op.alter_column('invoices', 'dataset_request_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)

