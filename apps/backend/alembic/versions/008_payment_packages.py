"""Update Payment model to support packages.

Revision ID: 008_payment_packages
Revises: 007_packages
Create Date: 2025-12-14 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_payment_packages'
down_revision = '007_packages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make dataset_request_id nullable
    op.alter_column('payments', 'dataset_request_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)
    
    # Add user_package_id column
    op.add_column('payments', sa.Column('user_package_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_payments_user_package_id',
        'payments', 'user_packages',
        ['user_package_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index
    op.create_index('ix_payments_user_package_id', 'payments', ['user_package_id'])
    
    # Add check constraint: either dataset_request_id or user_package_id must be set
    op.execute("""
        ALTER TABLE payments 
        ADD CONSTRAINT chk_payment_target 
        CHECK (
            (dataset_request_id IS NOT NULL AND user_package_id IS NULL) OR
            (dataset_request_id IS NULL AND user_package_id IS NOT NULL)
        )
    """)


def downgrade() -> None:
    # Remove check constraint
    op.execute("ALTER TABLE payments DROP CONSTRAINT IF EXISTS chk_payment_target")
    
    # Remove index
    op.drop_index('ix_payments_user_package_id', table_name='payments')
    
    # Remove foreign key
    op.drop_constraint('fk_payments_user_package_id', 'payments', type_='foreignkey')
    
    # Remove column
    op.drop_column('payments', 'user_package_id')
    
    # Make dataset_request_id NOT NULL again (will fail if there are NULL values)
    op.alter_column('payments', 'dataset_request_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)

