"""Add payments table

Revision ID: 004_payments
Revises: 003_dataset_requests_steps
Create Date: 2024-12-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_payments'
down_revision = '003_dataset_requests_steps'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='eur'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('provider', sa.String(20), nullable=False, server_default='stripe'),
        sa.Column('provider_ref', sa.String(255), nullable=True),
        sa.Column('provider_checkout_session_id', sa.String(255), nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['dataset_request_id'], ['dataset_requests.id'], ),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_dataset_request_id', 'payments', ['dataset_request_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_provider_checkout_session_id', 'payments', ['provider_checkout_session_id'])
    op.create_index('ix_payments_provider_ref', 'payments', ['provider_ref'])
    op.create_index('ix_payments_idempotency_key', 'payments', ['idempotency_key'])
    op.create_unique_constraint('uq_payments_provider_ref', 'payments', ['provider_ref'])
    op.create_unique_constraint('uq_payments_idempotency_key', 'payments', ['idempotency_key'])


def downgrade() -> None:
    op.drop_constraint('uq_payments_idempotency_key', 'payments', type_='unique')
    op.drop_constraint('uq_payments_provider_ref', 'payments', type_='unique')
    op.drop_index('ix_payments_idempotency_key', table_name='payments')
    op.drop_index('ix_payments_provider_ref', table_name='payments')
    op.drop_index('ix_payments_provider_checkout_session_id', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_dataset_request_id', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_table('payments')

