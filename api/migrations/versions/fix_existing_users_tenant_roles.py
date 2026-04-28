"""Fix existing users tenant roles - assign owner to first user of each tenant

Revision ID: fix_tenant_roles_001
Revises: e160bea57250
Create Date: 2026-04-27 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_tenant_roles_001'
down_revision = 'e160bea57250'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Assign tenant_role to existing users:
    - Superadmin users: no change (tenant_role stays NULL)
    - Operator users: assign 'owner' if they're the first user of their tenant, else 'collaborator'
    """

    # SQL raw para asignar roles
    # Para cada tenant, el usuario creado primero (por created_at) es 'owner'
    # Los demás son 'collaborator'

    connection = op.get_bind()

    # Primero, asignar 'owner' al primer usuario de cada tenant (por fecha de creación)
    op.execute("""
        UPDATE users u
        SET tenant_role = 'owner'
        WHERE u.role = 'operator'
        AND u.tenant_role IS NULL
        AND u.id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY tenant_id ORDER BY created_at ASC) as rn
                FROM users
                WHERE role = 'operator' AND tenant_id IS NOT NULL
            ) ranked
            WHERE rn = 1
        )
    """)

    # Luego, asignar 'collaborator' a los demás usuarios operator sin rol asignado
    op.execute("""
        UPDATE users
        SET tenant_role = 'collaborator'
        WHERE role = 'operator' AND tenant_role IS NULL
    """)

    # Superadmin users no necesitan tenant_role (dejar NULL)


def downgrade() -> None:
    """
    Reset tenant roles to NULL for all users
    """
    op.execute("UPDATE users SET tenant_role = NULL WHERE role = 'operator'")
