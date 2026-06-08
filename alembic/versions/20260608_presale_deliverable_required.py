"""Add required flag to presale deliverables

Revision ID: presale_deliverable_required
Revises: quote_version_presale_context
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


revision = "presale_deliverable_required"
down_revision = "quote_version_presale_context"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "presale_ticket_deliverable",
        sa.Column(
            "is_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="是否关键交付物",
        ),
    )


def downgrade():
    op.drop_column("presale_ticket_deliverable", "is_required")
