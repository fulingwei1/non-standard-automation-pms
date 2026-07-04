"""add sales tax basis fields

Revision ID: 20260704_sales_tax_basis
Revises: 20260312_binding
Create Date: 2026-07-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_sales_tax_basis"
down_revision = "20260312_binding"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "quote_versions",
        sa.Column("amount_without_tax", sa.Numeric(12, 2), nullable=True, comment="不含税金额"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True, server_default="0", comment="税率(%)"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=True, server_default="0", comment="税额"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("amount_with_tax", sa.Numeric(12, 2), nullable=True, comment="含税金额"),
    )

    op.add_column(
        "contracts",
        sa.Column("amount_without_tax", sa.Numeric(15, 2), nullable=True, comment="不含税金额"),
    )
    op.add_column(
        "contracts",
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True, server_default="0", comment="税率(%)"),
    )
    op.add_column(
        "contracts",
        sa.Column("tax_amount", sa.Numeric(15, 2), nullable=True, server_default="0", comment="税额"),
    )
    op.add_column(
        "contracts",
        sa.Column("amount_with_tax", sa.Numeric(15, 2), nullable=True, comment="含税金额"),
    )


def downgrade():
    op.drop_column("contracts", "amount_with_tax")
    op.drop_column("contracts", "tax_amount")
    op.drop_column("contracts", "tax_rate")
    op.drop_column("contracts", "amount_without_tax")
    op.drop_column("quote_versions", "amount_with_tax")
    op.drop_column("quote_versions", "tax_amount")
    op.drop_column("quote_versions", "tax_rate")
    op.drop_column("quote_versions", "amount_without_tax")
