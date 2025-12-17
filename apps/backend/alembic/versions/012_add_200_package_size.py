"""Add HYPER (200) package size.

Revision ID: 012_add_200_package_size
Revises: 011_wallet_transactions
Create Date: 2025-12-17
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "012_add_200_package_size"
down_revision = "011_wallet_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum alteration (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE packagesize ADD VALUE 'HYPER';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    # Downgrade for enum values is not supported in PostgreSQL without recreating the type.
    pass

