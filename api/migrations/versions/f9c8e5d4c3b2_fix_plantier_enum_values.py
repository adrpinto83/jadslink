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
    # Drop the old enum type (if it has constraints)
    op.execute("ALTER TYPE plantier RENAME TO plantier_old")

    # Create the new enum type with correct values
    op.execute("CREATE TYPE plantier AS ENUM ('free', 'basic', 'pro')")

    # Update the column to use the new enum
    op.execute("ALTER TABLE tenants ALTER COLUMN plan_tier TYPE plantier USING plan_tier::text::plantier")

    # Drop the old enum type
    op.execute("DROP TYPE plantier_old")


def downgrade() -> None:
    # Drop the new enum type
    op.execute("ALTER TYPE plantier RENAME TO plantier_new")

    # Create the old enum type
    op.execute("CREATE TYPE plantier AS ENUM ('starter', 'pro', 'enterprise')")

    # Update the column to use the old enum
    op.execute("ALTER TABLE tenants ALTER COLUMN plan_tier TYPE plantier USING plan_tier::text::plantier")

    # Drop the new enum type
    op.execute("DROP TYPE plantier_new")
