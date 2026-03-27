# -*- coding: utf-8 -*-
"""project_material_fusion - 项目与物料深度融合字段

Revision ID: pmf20260328001
Revises: None
Create Date: 2026-03-28

新增字段:
- projects: kitting_rate, material_status, shortage_items_count
- bom_items: kitting_status, expected_arrival_date, actual_arrival_date
"""

from alembic import op
import sqlalchemy as sa

revision = "pmf20260328001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- projects 表 ---
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(
            sa.Column("kitting_rate", sa.Numeric(5, 1), server_default="0", comment="物料齐套率(0-100%)")
        )
        batch_op.add_column(
            sa.Column("material_status", sa.String(20), server_default="待采购", comment="物料状态")
        )
        batch_op.add_column(
            sa.Column("shortage_items_count", sa.Integer(), server_default="0", comment="缺料项数量")
        )

    # --- bom_items 表 ---
    with op.batch_alter_table("bom_items") as batch_op:
        batch_op.add_column(
            sa.Column("kitting_status", sa.String(20), server_default="PENDING", comment="齐套状态")
        )
        batch_op.add_column(
            sa.Column("expected_arrival_date", sa.Date(), nullable=True, comment="预计到货日期")
        )
        batch_op.add_column(
            sa.Column("actual_arrival_date", sa.Date(), nullable=True, comment="实际到货日期")
        )


def downgrade() -> None:
    with op.batch_alter_table("bom_items") as batch_op:
        batch_op.drop_column("actual_arrival_date")
        batch_op.drop_column("expected_arrival_date")
        batch_op.drop_column("kitting_status")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("shortage_items_count")
        batch_op.drop_column("material_status")
        batch_op.drop_column("kitting_rate")
