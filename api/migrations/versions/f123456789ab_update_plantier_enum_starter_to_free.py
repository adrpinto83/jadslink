"""Update PlanTier enum from starter to free

Revision ID: f123456789ab
Revises: e60378fd8260
Create Date: 2026-04-21

"""
from alembic import op
import sqlalchemy as sa

revision = 'f123456789ab'
down_revision = 'e60378fd8260'
branch_labels = None
depends_on = None

def upgrade():
    # For PostgreSQL: Update the enum type
    op.execute("ALTER TYPE plantier ADD VALUE 'free' BEFORE 'starter'")

    # Update all 'starter' values to 'free'
    op.execute("UPDATE tenants SET plan_tier = 'free' WHERE plan_tier = 'starter'")

    # Drop the old value (if database supports it)
    # Note: PostgreSQL doesn't allow direct enum value deletion, so we'll keep 'starter' but it won't be used

def downgrade():
    # Revert all 'free' values back to 'starter'
    op.execute("UPDATE tenants SET plan_tier = 'starter' WHERE plan_tier = 'free'")
