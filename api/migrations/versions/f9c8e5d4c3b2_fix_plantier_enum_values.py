"""Fix plantier enum values to match model

Revision ID: f9c8e5d4c3b2
Revises: e18b438d12e0
Create Date: 2026-04-26 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9c8e5d4c3b2'
down_revision = 'e18b438d12e0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL-specific enum migration - skip for MySQL
    # MySQL handles ENUMs as column constraints, not separate types
    pass


def downgrade() -> None:
    # PostgreSQL-specific enum migration - skip for MySQL
    pass
