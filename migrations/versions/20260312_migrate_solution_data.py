# -*- coding: utf-8 -*-
"""迁移现有方案数据到版本表

本迁移将现有的 presale_ai_solution 数据迁移到 solution_versions 表：
1. 为每个现有方案创建 V1.0 版本
2. 设置 current_version_id
3. 尝试关联现有的成本估算

Revision ID: 20260312_migrate_data
Revises: 20260312_binding
Create Date: 2026-03-12

注意：此迁移为数据迁移，需要在结构迁移之后执行
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = "20260312_migrate_data"
down_revision = "20260312_binding"
branch_labels = None
depends_on = None


def upgrade():
    """迁移现有数据"""
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # ========== 1. 迁移 presale_ai_solution 到 solution_versions ==========
        # 查询所有现有方案
        result = session.execute(
            text("""
                SELECT
                    id,
                    generated_solution,
                    architecture_diagram,
                    topology_diagram,
                    signal_flow_diagram,
                    bom_list,
                    technical_parameters,
                    process_flow,
                    solution_description,
                    confidence_score,
                    quality_score,
                    ai_model_used,
                    generation_time_seconds,
                    prompt_tokens,
                    completion_tokens,
                    status,
                    reviewed_by,
                    reviewed_at,
                    review_comments,
                    created_by,
                    created_at
                FROM presale_ai_solution
            """)
        )

        solutions = result.fetchall()
        print(f"[数据迁移] 发现 {len(solutions)} 个方案需要迁移")

        for sol in solutions:
            # 将方案状态映射到版本状态
            version_status = "approved" if sol.status == "approved" else "draft"

            # 插入版本记录
            session.execute(
                text("""
                    INSERT INTO solution_versions (
                        solution_id,
                        version_no,
                        generated_solution,
                        architecture_diagram,
                        topology_diagram,
                        signal_flow_diagram,
                        bom_list,
                        technical_parameters,
                        process_flow,
                        solution_description,
                        confidence_score,
                        quality_score,
                        ai_model_used,
                        generation_time_seconds,
                        prompt_tokens,
                        completion_tokens,
                        status,
                        approved_by,
                        approved_at,
                        approval_comments,
                        change_summary,
                        created_by,
                        created_at
                    ) VALUES (
                        :solution_id,
                        'V1.0',
                        :generated_solution,
                        :architecture_diagram,
                        :topology_diagram,
                        :signal_flow_diagram,
                        :bom_list,
                        :technical_parameters,
                        :process_flow,
                        :solution_description,
                        :confidence_score,
                        :quality_score,
                        :ai_model_used,
                        :generation_time_seconds,
                        :prompt_tokens,
                        :completion_tokens,
                        :status,
                        :approved_by,
                        :approved_at,
                        :approval_comments,
                        '初始版本（从历史数据迁移）',
                        :created_by,
                        :created_at
                    )
                """),
                {
                    "solution_id": sol.id,
                    "generated_solution": sol.generated_solution,
                    "architecture_diagram": sol.architecture_diagram,
                    "topology_diagram": sol.topology_diagram,
                    "signal_flow_diagram": sol.signal_flow_diagram,
                    "bom_list": sol.bom_list,
                    "technical_parameters": sol.technical_parameters,
                    "process_flow": sol.process_flow,
                    "solution_description": sol.solution_description,
                    "confidence_score": sol.confidence_score,
                    "quality_score": sol.quality_score,
                    "ai_model_used": sol.ai_model_used,
                    "generation_time_seconds": sol.generation_time_seconds,
                    "prompt_tokens": sol.prompt_tokens,
                    "completion_tokens": sol.completion_tokens,
                    "status": version_status,
                    "approved_by": sol.reviewed_by,
                    "approved_at": sol.reviewed_at,
                    "approval_comments": sol.review_comments,
                    "created_by": sol.created_by,
                    "created_at": sol.created_at,
                },
            )

        # ========== 2. 更新 presale_ai_solution.current_version_id ==========
        session.execute(
            text("""
                UPDATE presale_ai_solution s
                SET current_version_id = (
                    SELECT sv.id
                    FROM solution_versions sv
                    WHERE sv.solution_id = s.id
                    ORDER BY sv.created_at DESC
                    LIMIT 1
                )
            """)
        )

        # ========== 3. 关联现有成本估算到方案版本 ==========
        # 通过 solution_id 查找对应的版本
        session.execute(
            text("""
                UPDATE presale_ai_cost_estimation ce
                SET solution_version_id = (
                    SELECT sv.id
                    FROM solution_versions sv
                    WHERE sv.solution_id = ce.solution_id
                    ORDER BY sv.created_at DESC
                    LIMIT 1
                )
                WHERE ce.solution_id IS NOT NULL
            """)
        )

        # 统计关联结果
        result = session.execute(
            text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN solution_version_id IS NOT NULL THEN 1 ELSE 0 END) as linked
                FROM presale_ai_cost_estimation
            """)
        )
        row = result.fetchone()
        print(f"[数据迁移] 成本估算关联完成: {row.linked}/{row.total}")

        session.commit()
        print("[数据迁移] 迁移完成")

    except Exception as e:
        session.rollback()
        print(f"[数据迁移] 迁移失败: {e}")
        raise


def downgrade():
    """回滚数据迁移

    注意：数据迁移回滚会删除 solution_versions 中的数据，
    但不会恢复 presale_ai_solution 中被删除的内容字段。
    建议在生产环境执行前做好备份。
    """
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # 1. 清空 current_version_id
        session.execute(
            text("UPDATE presale_ai_solution SET current_version_id = NULL")
        )

        # 2. 清空成本估算的 solution_version_id
        session.execute(
            text("UPDATE presale_ai_cost_estimation SET solution_version_id = NULL")
        )

        # 3. 删除迁移创建的版本数据
        session.execute(
            text("DELETE FROM solution_versions WHERE change_summary = '初始版本（从历史数据迁移）'")
        )

        session.commit()
        print("[数据迁移回滚] 完成")

    except Exception as e:
        session.rollback()
        print(f"[数据迁移回滚] 失败: {e}")
        raise
