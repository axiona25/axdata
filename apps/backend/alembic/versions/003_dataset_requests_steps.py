"""Add dataset_requests and dataset_steps tables

Revision ID: 003_dataset_requests_steps
Revises: 002_chat_sessions_messages
Create Date: 2024-12-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_dataset_requests_steps'
down_revision = '002_chat_sessions_messages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dataset_requests table
    op.create_table(
        'dataset_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(50), nullable=False),
        sa.Column('plan_json', postgresql.JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ),
    )
    op.create_index('ix_dataset_requests_user_id', 'dataset_requests', ['user_id'])
    op.create_index('ix_dataset_requests_chat_session_id', 'dataset_requests', ['chat_session_id'])
    op.create_index('ix_dataset_requests_status', 'dataset_requests', ['status'])
    
    # Create dataset_steps table
    op.create_table(
        'dataset_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_type', sa.String(20), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('input_data', postgresql.JSON(), nullable=True),
        sa.Column('output_data', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dataset_request_id'], ['dataset_requests.id'], ),
    )
    op.create_index('ix_dataset_steps_dataset_request_id', 'dataset_steps', ['dataset_request_id'])
    op.create_index('ix_dataset_steps_status', 'dataset_steps', ['status'])


def downgrade() -> None:
    op.drop_index('ix_dataset_steps_status', table_name='dataset_steps')
    op.drop_index('ix_dataset_steps_dataset_request_id', table_name='dataset_steps')
    op.drop_table('dataset_steps')
    op.drop_index('ix_dataset_requests_status', table_name='dataset_requests')
    op.drop_index('ix_dataset_requests_chat_session_id', table_name='dataset_requests')
    op.drop_index('ix_dataset_requests_user_id', table_name='dataset_requests')
    op.drop_table('dataset_requests')

