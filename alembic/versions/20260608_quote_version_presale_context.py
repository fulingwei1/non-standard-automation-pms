"""Add presale context to quote versions

Revision ID: quote_version_presale_context
Revises: presale_ticket_lead_context
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


revision = "quote_version_presale_context"
down_revision = "presale_ticket_lead_context"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "quote_versions",
        sa.Column("presale_solution_id", sa.Integer(), nullable=True, comment="售前方案ID"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("presale_ticket_id", sa.Integer(), nullable=True, comment="售前工单ID"),
    )
    op.create_foreign_key(
        "fk_qv_presale_solution",
        "quote_versions",
        "presale_solution",
        ["presale_solution_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_qv_presale_ticket",
        "quote_versions",
        "presale_support_ticket",
        ["presale_ticket_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_qv_presale_solution",
        "quote_versions",
        ["presale_solution_id"],
    )
    op.create_index(
        "idx_qv_presale_ticket",
        "quote_versions",
        ["presale_ticket_id"],
    )


def downgrade():
    op.drop_index("idx_qv_presale_ticket", table_name="quote_versions")
    op.drop_index("idx_qv_presale_solution", table_name="quote_versions")
    op.drop_constraint("fk_qv_presale_ticket", "quote_versions", type_="foreignkey")
    op.drop_constraint("fk_qv_presale_solution", "quote_versions", type_="foreignkey")
    op.drop_column("quote_versions", "presale_ticket_id")
    op.drop_column("quote_versions", "presale_solution_id")
