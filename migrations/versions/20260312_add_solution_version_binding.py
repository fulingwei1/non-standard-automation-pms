# -*- coding: utf-8 -*-
"""添加方案版本和成本-报价绑定

本迁移实现 成本-方案-报价 三位一体绑定：
1. 创建 solution_versions 表（方案版本控制）
2. 为 presale_ai_solution 添加 current_version_id
3. 为 presale_ai_cost_estimation 添加 solution_version_id 和审批字段
4. 为 quote_versions 添加绑定字段

Revision ID: 20260312_binding
Revises: 20260312_add_sales_indexes
Create Date: 2026-03-12
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "20260312_binding"
down_revision = "20260312_add_sales_indexes"
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库结构"""

    # ========== 1. 创建 solution_versions 表 ==========
    op.create_table(
        "solution_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="主键ID"),
        sa.Column("solution_id", sa.Integer(), nullable=False, comment="方案ID"),
        sa.Column("version_no", sa.String(20), nullable=False, comment="版本号"),
        # 方案内容
        sa.Column("generated_solution", sa.JSON(), nullable=True, comment="生成的完整方案"),
        sa.Column("architecture_diagram", sa.Text(), nullable=True, comment="系统架构图"),
        sa.Column("topology_diagram", sa.Text(), nullable=True, comment="设备拓扑图"),
        sa.Column("signal_flow_diagram", sa.Text(), nullable=True, comment="信号流程图"),
        sa.Column("bom_list", sa.JSON(), nullable=True, comment="BOM清单"),
        sa.Column("technical_parameters", sa.JSON(), nullable=True, comment="技术参数表"),
        sa.Column("process_flow", sa.Text(), nullable=True, comment="工艺流程说明"),
        sa.Column("solution_description", sa.Text(), nullable=True, comment="方案描述"),
        # 变更信息
        sa.Column("change_summary", sa.Text(), nullable=True, comment="变更摘要"),
        sa.Column("change_reason", sa.String(200), nullable=True, comment="变更原因"),
        sa.Column("parent_version_id", sa.Integer(), nullable=True, comment="父版本ID"),
        # 审批状态
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
            comment="状态：draft/pending_review/approved/rejected",
        ),
        sa.Column("approved_by", sa.Integer(), nullable=True, comment="审批人ID"),
        sa.Column("approved_at", sa.DateTime(), nullable=True, comment="审批时间"),
        sa.Column("approval_comments", sa.Text(), nullable=True, comment="审批意见"),
        # AI 元数据
        sa.Column("ai_model_used", sa.String(100), nullable=True, comment="使用的AI模型"),
        sa.Column("confidence_score", sa.DECIMAL(3, 2), nullable=True, comment="置信度评分"),
        sa.Column("quality_score", sa.DECIMAL(3, 2), nullable=True, comment="质量评分"),
        sa.Column("generation_time_seconds", sa.DECIMAL(6, 2), nullable=True, comment="生成耗时"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True, comment="Prompt tokens"),
        sa.Column("completion_tokens", sa.Integer(), nullable=True, comment="Completion tokens"),
        # 时间戳
        sa.Column("created_by", sa.Integer(), nullable=False, comment="创建人ID"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        # 约束
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["solution_id"],
            ["presale_ai_solution.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"],
            ["solution_versions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.UniqueConstraint("solution_id", "version_no", name="uq_solution_version"),
        comment="方案版本表",
    )

    op.create_index("idx_sv_solution_id", "solution_versions", ["solution_id"])
    op.create_index("idx_sv_status", "solution_versions", ["status"])
    op.create_index("idx_sv_created_at", "solution_versions", ["created_at"])

    # ========== 2. 为 presale_ai_solution 添加 current_version_id ==========
    op.add_column(
        "presale_ai_solution",
        sa.Column("current_version_id", sa.Integer(), nullable=True, comment="当前生效版本ID"),
    )
    # 注意：外键约束使用 use_alter=True 避免循环依赖
    op.create_foreign_key(
        "fk_solution_current_version",
        "presale_ai_solution",
        "solution_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ========== 3. 为 presale_ai_cost_estimation 添加绑定和审批字段 ==========
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column(
            "solution_version_id",
            sa.Integer(),
            nullable=True,
            comment="方案版本ID",
        ),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column("version_no", sa.String(20), server_default="V1", comment="成本估算版本号"),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column(
            "status",
            sa.String(20),
            server_default="draft",
            comment="状态：draft/pending_review/approved/rejected",
        ),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column("approved_by", sa.Integer(), nullable=True, comment="审批人ID"),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column("approved_at", sa.DateTime(), nullable=True, comment="审批时间"),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column("approval_comments", sa.Text(), nullable=True, comment="审批意见"),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column(
            "is_bound_to_quote",
            sa.Boolean(),
            server_default="0",
            comment="是否已绑定报价",
        ),
    )
    op.add_column(
        "presale_ai_cost_estimation",
        sa.Column("bound_quote_version_id", sa.Integer(), nullable=True, comment="绑定的报价版本ID"),
    )

    op.create_foreign_key(
        "fk_ce_solution_version",
        "presale_ai_cost_estimation",
        "solution_versions",
        ["solution_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ce_approved_by",
        "presale_ai_cost_estimation",
        "users",
        ["approved_by"],
        ["id"],
    )
    op.create_index("idx_ce_solution_version", "presale_ai_cost_estimation", ["solution_version_id"])
    op.create_index("idx_ce_status", "presale_ai_cost_estimation", ["status"])

    # ========== 4. 为 quote_versions 添加绑定字段 ==========
    op.add_column(
        "quote_versions",
        sa.Column("solution_version_id", sa.Integer(), nullable=True, comment="方案版本ID"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("cost_estimation_id", sa.Integer(), nullable=True, comment="成本估算ID"),
    )
    op.add_column(
        "quote_versions",
        sa.Column(
            "binding_status",
            sa.String(20),
            server_default="valid",
            comment="绑定状态：valid/outdated/invalid",
        ),
    )
    op.add_column(
        "quote_versions",
        sa.Column("binding_validated_at", sa.DateTime(), nullable=True, comment="最后验证时间"),
    )
    op.add_column(
        "quote_versions",
        sa.Column("binding_warning", sa.Text(), nullable=True, comment="绑定警告信息"),
    )

    op.create_foreign_key(
        "fk_qv_solution_version",
        "quote_versions",
        "solution_versions",
        ["solution_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_qv_cost_estimation",
        "quote_versions",
        "presale_ai_cost_estimation",
        ["cost_estimation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_qv_solution_version", "quote_versions", ["solution_version_id"])
    op.create_index("idx_qv_cost_estimation", "quote_versions", ["cost_estimation_id"])
    op.create_index("idx_qv_binding_status", "quote_versions", ["binding_status"])


def downgrade():
    """回滚数据库结构"""

    # ========== 4. 移除 quote_versions 绑定字段 ==========
    op.drop_index("idx_qv_binding_status", "quote_versions")
    op.drop_index("idx_qv_cost_estimation", "quote_versions")
    op.drop_index("idx_qv_solution_version", "quote_versions")
    op.drop_constraint("fk_qv_cost_estimation", "quote_versions", type_="foreignkey")
    op.drop_constraint("fk_qv_solution_version", "quote_versions", type_="foreignkey")
    op.drop_column("quote_versions", "binding_warning")
    op.drop_column("quote_versions", "binding_validated_at")
    op.drop_column("quote_versions", "binding_status")
    op.drop_column("quote_versions", "cost_estimation_id")
    op.drop_column("quote_versions", "solution_version_id")

    # ========== 3. 移除 presale_ai_cost_estimation 字段 ==========
    op.drop_index("idx_ce_status", "presale_ai_cost_estimation")
    op.drop_index("idx_ce_solution_version", "presale_ai_cost_estimation")
    op.drop_constraint("fk_ce_approved_by", "presale_ai_cost_estimation", type_="foreignkey")
    op.drop_constraint("fk_ce_solution_version", "presale_ai_cost_estimation", type_="foreignkey")
    op.drop_column("presale_ai_cost_estimation", "bound_quote_version_id")
    op.drop_column("presale_ai_cost_estimation", "is_bound_to_quote")
    op.drop_column("presale_ai_cost_estimation", "approval_comments")
    op.drop_column("presale_ai_cost_estimation", "approved_at")
    op.drop_column("presale_ai_cost_estimation", "approved_by")
    op.drop_column("presale_ai_cost_estimation", "status")
    op.drop_column("presale_ai_cost_estimation", "version_no")
    op.drop_column("presale_ai_cost_estimation", "solution_version_id")

    # ========== 2. 移除 presale_ai_solution.current_version_id ==========
    op.drop_constraint("fk_solution_current_version", "presale_ai_solution", type_="foreignkey")
    op.drop_column("presale_ai_solution", "current_version_id")

    # ========== 1. 删除 solution_versions 表 ==========
    op.drop_index("idx_sv_created_at", "solution_versions")
    op.drop_index("idx_sv_status", "solution_versions")
    op.drop_index("idx_sv_solution_id", "solution_versions")
    op.drop_table("solution_versions")
