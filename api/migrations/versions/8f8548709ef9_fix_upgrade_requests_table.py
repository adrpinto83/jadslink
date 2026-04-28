"""fix_upgrade_requests_table

Revision ID: 8f8548709ef9
Revises: 03da7e1a34f5
Create Date: 2026-04-27 02:09:21.246811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f8548709ef9'
down_revision = '03da7e1a34f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index is already created in the exchange_rates table creation
    # No-op for MySQL compatibility
    pass


def downgrade() -> None:
    # No-op - index stays as created in table creation
    pass
