# -*- coding: utf-8 -*-
"""ecn_material_impact_tracking - ECN物料影响跟踪

Revision ID: ecnmi20260328001
Revises: pmf20260328001
Create Date: 2026-03-28

新增表:
- ecn_material_dispositions: ECN物料处置决策表
- ecn_execution_progress: ECN执行进度表
- ecn_stakeholders: ECN相关人员表
"""

from alembic import op
import sqlalchemy as sa

revision = "ecnmi20260328001"
down_revision = "pmf20260328001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- ecn_material_dispositions 表 ---
    op.create_table(
        "ecn_material_dispositions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ecn_id", sa.Integer(), nullable=False, comment="ECN ID"),
        sa.Column("affected_material_id", sa.Integer(), comment="受影响物料记录ID"),
        sa.Column("material_id", sa.Integer(), comment="物料ID"),
        sa.Column("material_code", sa.String(50), nullable=False, comment="物料编码"),
        sa.Column("material_name", sa.String(200), nullable=False, comment="物料名称"),
        sa.Column("specification", sa.String(500), comment="规格型号"),
        sa.Column(
            "material_status", sa.String(20), nullable=False,
            comment="物料当前状态: NOT_PURCHASED/ORDERED/IN_TRANSIT/IN_STOCK",
        ),
        sa.Column("purchase_order_id", sa.Integer(), comment="采购订单ID"),
        sa.Column("purchase_order_no", sa.String(50), comment="采购订单号"),
        sa.Column("supplier_id", sa.Integer(), comment="供应商ID"),
        sa.Column("supplier_name", sa.String(200), comment="供应商名称"),
        sa.Column("affected_quantity", sa.Numeric(10, 4), server_default="0", comment="受影响数量"),
        sa.Column("unit_price", sa.Numeric(12, 4), server_default="0", comment="单价"),
        sa.Column("potential_loss", sa.Numeric(14, 2), server_default="0", comment="潜在损失金额"),
        sa.Column(
            "disposition", sa.String(20),
            comment="处置方式: CONTINUE_USE/REWORK/SCRAP/RETURN/PENDING",
        ),
        sa.Column("disposition_reason", sa.Text(), comment="处置原因"),
        sa.Column("disposition_cost", sa.Numeric(14, 2), server_default="0", comment="处置成本"),
        sa.Column("actual_loss", sa.Numeric(14, 2), server_default="0", comment="实际损失金额"),
        sa.Column("decided_by", sa.Integer(), comment="决策人"),
        sa.Column("decided_at", sa.DateTime(), comment="决策时间"),
        sa.Column(
            "status", sa.String(20), server_default="PENDING",
            comment="处理状态: PENDING/DECIDED/IN_PROGRESS/COMPLETED",
        ),
        sa.Column("completed_at", sa.DateTime(), comment="处理完成时间"),
        sa.Column("remark", sa.Text(), comment="备注"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["ecn_id"], ["ecn.id"]),
        sa.ForeignKeyConstraint(["affected_material_id"], ["ecn_affected_materials.id"]),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        comment="ECN物料处置决策表",
    )
    op.create_index("idx_mat_disp_ecn", "ecn_material_dispositions", ["ecn_id"])
    op.create_index("idx_mat_disp_material", "ecn_material_dispositions", ["material_id"])
    op.create_index("idx_mat_disp_status", "ecn_material_dispositions", ["status"])
    op.create_index("idx_mat_disp_po", "ecn_material_dispositions", ["purchase_order_id"])

    # --- ecn_execution_progress 表 ---
    op.create_table(
        "ecn_execution_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ecn_id", sa.Integer(), nullable=False, comment="ECN ID"),
        sa.Column(
            "phase", sa.String(30), nullable=False,
            comment="执行阶段: NOTIFY_SUPPLIER/PURCHASE_CHANGE/MATERIAL_DISPOSITION/VERIFICATION/CLOSE",
        ),
        sa.Column("phase_name", sa.String(100), comment="阶段名称"),
        sa.Column("phase_order", sa.Integer(), server_default="0", comment="阶段顺序"),
        sa.Column(
            "status", sa.String(20), server_default="PENDING",
            comment="状态: PENDING/IN_PROGRESS/COMPLETED/BLOCKED/SKIPPED",
        ),
        sa.Column("progress_pct", sa.Integer(), server_default="0", comment="进度百分比(0-100)"),
        sa.Column("planned_start", sa.Date(), comment="计划开始"),
        sa.Column("planned_end", sa.Date(), comment="计划结束"),
        sa.Column("actual_start", sa.DateTime(), comment="实际开始"),
        sa.Column("actual_end", sa.DateTime(), comment="实际完成"),
        sa.Column("estimated_completion", sa.Date(), comment="预计完成日期"),
        sa.Column("assignee_id", sa.Integer(), comment="负责人"),
        sa.Column("is_blocked", sa.Boolean(), server_default="0", comment="是否阻塞"),
        sa.Column("block_reason", sa.Text(), comment="阻塞原因"),
        sa.Column("block_resolved_at", sa.DateTime(), comment="阻塞解除时间"),
        sa.Column("summary", sa.Text(), comment="阶段摘要"),
        sa.Column("details", sa.JSON(), comment="详细信息(JSON)"),
        sa.Column("remark", sa.Text(), comment="备注"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["ecn_id"], ["ecn.id"]),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        comment="ECN执行进度表",
    )
    op.create_index("idx_exec_prog_ecn", "ecn_execution_progress", ["ecn_id"])
    op.create_index("idx_exec_prog_phase", "ecn_execution_progress", ["phase"])
    op.create_index("idx_exec_prog_status", "ecn_execution_progress", ["status"])

    # --- ecn_stakeholders 表 ---
    op.create_table(
        "ecn_stakeholders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ecn_id", sa.Integer(), nullable=False, comment="ECN ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column(
            "role", sa.String(30), nullable=False,
            comment="角色: PROJECT_MANAGER/PURCHASER/SUPPLIER_CONTACT/DESIGNER/APPROVER/OBSERVER",
        ),
        sa.Column("role_name", sa.String(100), comment="角色名称"),
        sa.Column("source", sa.String(30), server_default="AUTO", comment="添加来源: AUTO/MANUAL"),
        sa.Column("source_reason", sa.String(200), comment="添加原因"),
        sa.Column("is_subscribed", sa.Boolean(), server_default="1", comment="是否订阅通知"),
        sa.Column("subscription_types", sa.JSON(), comment="订阅的通知类型列表(JSON)"),
        sa.Column("can_view_detail", sa.Boolean(), server_default="1", comment="可查看ECN详情"),
        sa.Column("can_view_progress", sa.Boolean(), server_default="1", comment="可查看执行进度"),
        sa.Column("remark", sa.Text(), comment="备注"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["ecn_id"], ["ecn.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        comment="ECN相关人员表",
    )
    op.create_index("idx_stakeholder_ecn", "ecn_stakeholders", ["ecn_id"])
    op.create_index("idx_stakeholder_user", "ecn_stakeholders", ["user_id"])
    op.create_index("idx_stakeholder_role", "ecn_stakeholders", ["role"])


def downgrade() -> None:
    op.drop_table("ecn_stakeholders")
    op.drop_table("ecn_execution_progress")
    op.drop_table("ecn_material_dispositions")
