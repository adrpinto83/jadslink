"""Add UpgradeRequest model for payment tracking

Revision ID: e18b438d12e0
Revises: e8207eb00a46
Create Date: 2026-04-26 16:13:16.618979

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e18b438d12e0'
down_revision = 'e8207eb00a46'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'upgrade_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('upgrade_type', sa.Enum('extra_tickets', 'plan_upgrade', name='upgradetype'), nullable=False),
        sa.Column('ticket_quantity', sa.Integer(), nullable=True),
        sa.Column('new_plan_tier', sa.String(length=50), nullable=True),
        sa.Column('payment_method', sa.Enum('pago_movil', 'card', name='paymentmethod'), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('amount_vef', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('exchange_rate', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('status', sa.Enum('pending_payment', 'payment_received', 'approved', 'rejected', 'cancelled', name='paymentstatus'), nullable=False),
        sa.Column('payment_details', sa.JSON(), nullable=True),
        sa.Column('banco_origen', sa.String(length=100), nullable=True),
        sa.Column('cédula_pagador', sa.String(length=20), nullable=True),
        sa.Column('referencia_pago', sa.String(length=50), nullable=True),
        sa.Column('comprobante_url', sa.String(length=500), nullable=True),
        sa.Column('últimos_4_digitos', sa.String(length=4), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('reminder_count', sa.Integer(), nullable=False),
        sa.Column('last_reminder_at', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('upgrade_requests')
