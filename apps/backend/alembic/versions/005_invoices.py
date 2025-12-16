"""Add invoices table

Revision ID: 005_invoices
Revises: 004_payments
Create Date: 2024-12-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_invoices'
down_revision = '004_payments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_number', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('dataset_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='eur'),
        sa.Column('invoice_date', sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.ForeignKeyConstraint(['dataset_request_id'], ['dataset_requests.id'], ),
    )
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'])
    op.create_index('ix_invoices_user_id', 'invoices', ['user_id'])
    op.create_index('ix_invoices_payment_id', 'invoices', ['payment_id'])
    op.create_index('ix_invoices_dataset_request_id', 'invoices', ['dataset_request_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])


def downgrade() -> None:
    op.drop_index('ix_invoices_status', table_name='invoices')
    op.drop_index('ix_invoices_dataset_request_id', table_name='invoices')
    op.drop_index('ix_invoices_payment_id', table_name='invoices')
    op.drop_index('ix_invoices_user_id', table_name='invoices')
    op.drop_index('ix_invoices_invoice_number', table_name='invoices')
    op.drop_table('invoices')

