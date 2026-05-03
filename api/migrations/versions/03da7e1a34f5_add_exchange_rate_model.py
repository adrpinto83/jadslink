"""add_exchange_rate_model

Revision ID: 03da7e1a34f5
Revises: eb6f7ed4e560
Create Date: 2026-04-26 19:13:06.419438

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql
import uuid


# revision identifiers, used by Alembic.
revision = '03da7e1a34f5'
down_revision = 'eb6f7ed4e560'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.String(36), nullable=False, default=uuid.uuid4),
        sa.Column('rate', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for active rates lookup
    op.create_index('idx_exchange_rates_active', 'exchange_rates', ['is_active', 'created_at'])

    # Insert initial rate
    op.execute(
        "INSERT INTO exchange_rates (id, rate, source, is_active, notes, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 36.50, 'manual', true, 'Initial system rate', now(), now())"
    )


def downgrade() -> None:
    op.drop_index('idx_exchange_rates_active', table_name='exchange_rates')
    op.drop_table('exchange_rates')
