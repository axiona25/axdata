"""Add dataset packages and user packages.

Revision ID: 007_packages
Revises: 006_audit_logs
Create Date: 2025-12-14 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '007_packages'
down_revision = '006_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dataset_packages table
    op.create_table(
        'dataset_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('size', sa.Enum('SINGLE', 'SMALL', 'MEDIUM', 'LARGE', 'XL', 'XXL', 'XXXL', 'MEGA', 'ULTRA', name='packagesize'), nullable=False),
        sa.Column('dataset_count', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR', nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create user_packages table
    op.create_table(
        'user_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('package_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dataset_packages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_domains', postgresql.JSON(), nullable=False),
        sa.Column('total_datasets', sa.Integer(), nullable=False),
        sa.Column('remaining_datasets', sa.Integer(), nullable=False),
        sa.Column('used_datasets', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'EXHAUSTED', 'CANCELLED', name='packagestatus'), server_default='ACTIVE', nullable=False),
        sa.Column('purchased_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=True),
    )
    
    # Add user_package_id to dataset_requests
    op.add_column('dataset_requests', sa.Column('user_package_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_packages.id', ondelete='SET NULL'), nullable=True))
    
    # Create indexes
    op.create_index('ix_user_packages_user_id', 'user_packages', ['user_id'])
    op.create_index('ix_user_packages_status', 'user_packages', ['status'])
    op.create_index('ix_dataset_packages_is_active', 'dataset_packages', ['is_active'])
    
    # Insert default packages
    op.execute("""
        INSERT INTO dataset_packages (id, name, size, dataset_count, price, currency, description, is_active, created_at, updated_at)
        VALUES
            (gen_random_uuid(), 'Single Dataset', 'SINGLE', 1, 9.99, 'EUR', 'Perfect for trying out the service', true, now(), now()),
            (gen_random_uuid(), 'Starter Pack', 'SMALL', 3, 24.99, 'EUR', 'Great for small research projects', true, now(), now()),
            (gen_random_uuid(), 'Researcher Bundle', 'MEDIUM', 5, 39.99, 'EUR', 'Ideal for individual researchers', true, now(), now()),
            (gen_random_uuid(), 'Team Pack', 'LARGE', 7, 54.99, 'EUR', 'Perfect for small teams', true, now(), now()),
            (gen_random_uuid(), 'Lab Package', 'XL', 10, 74.99, 'EUR', 'For research labs and groups', true, now(), now()),
            (gen_random_uuid(), 'Department Bundle', 'XXL', 15, 99.99, 'EUR', 'For departments and larger teams', true, now(), now()),
            (gen_random_uuid(), 'Institution Pack', 'XXXL', 20, 129.99, 'EUR', 'For institutions and organizations', true, now(), now()),
            (gen_random_uuid(), 'Enterprise Bundle', 'MEGA', 50, 299.99, 'EUR', 'For large-scale research projects', true, now(), now()),
            (gen_random_uuid(), 'Ultra Package', 'ULTRA', 100, 499.99, 'EUR', 'Maximum value for heavy users', true, now(), now());
    """)


def downgrade() -> None:
    op.drop_index('ix_dataset_packages_is_active', table_name='dataset_packages')
    op.drop_index('ix_user_packages_status', table_name='user_packages')
    op.drop_index('ix_user_packages_user_id', table_name='user_packages')
    op.drop_column('dataset_requests', 'user_package_id')
    op.drop_table('user_packages')
    op.drop_table('dataset_packages')
    op.execute("DROP TYPE IF EXISTS packagestatus")
    op.execute("DROP TYPE IF EXISTS packagesize")

