"""Add lead context to presale support tickets

Revision ID: presale_ticket_lead_context
Revises: presale_tender_project_id
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "presale_ticket_lead_context"
down_revision = "presale_tender_project_id"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "presale_support_ticket",
        sa.Column("lead_id", sa.Integer(), nullable=True, comment="关联线索ID"),
    )
    op.create_index(
        "idx_presale_ticket_lead",
        "presale_support_ticket",
        ["lead_id"],
    )


def downgrade():
    op.drop_index("idx_presale_ticket_lead", table_name="presale_support_ticket")
    op.drop_column("presale_support_ticket", "lead_id")
