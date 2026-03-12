# -*- coding: utf-8 -*-
"""
合同管理端点 - 从合同创建项目
创建日期：2026-01-25
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db
from app.common.query_filters import build_like_conditions
from app.models.project import Project
from app.models.project.financial import ProjectMilestone
from app.models.project.financial import ProjectPaymentPlan as PaymentPlan
from app.models.sales.contracts import Contract
from app.utils.json_helpers import safe_json_loads

from ..utils.gate_validation import validate_g4_contract_to_project

logger = logging.getLogger(__name__)

# 允许创建项目的合同状态
ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/{contract_id}/create-project")
async def create_project_from_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    从合同创建项目，自动绑定付款节点到里程碑

    功能说明：
    1. 查询合同（包含客户信息）
    2. 验证合同状态和 G4 阶段门条件
    3. 创建项目
    4. 从合同的payment_nodes字段提取付款节点列表
    5. 如果有付款节点，为每个节点创建收款计划和对应里程碑
    6. 将合同金额同步到项目
    7. 同步SOW/验收标准到项目
    """

    # 1. 查询合同（包含客户信息和交付物）
    result = await db.execute(
        select(Contract)
        .options(
            selectinload(Contract.customer),
            selectinload(Contract.deliverables),
        )
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail=f"合同不存在: {contract_id}")

    # 2. 验证合同状态（只有已签署/执行中的合同才能创建项目）
    if contract.status not in ALLOWED_CONTRACT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"合同状态为 '{contract.status}'，只有已签署(signed)或执行中(executing)的合同才能创建项目",
        )

    # 3. G4 阶段门验证
    deliverables = contract.deliverables or []
    g4_passed, g4_errors = validate_g4_contract_to_project(contract, deliverables, db=None)
    if not g4_passed:
        # G4 验证失败返回详细错误信息
        raise HTTPException(
            status_code=400,
            detail=f"G4 阶段门验证失败: {'; '.join(g4_errors)}",
        )

    customer = contract.customer

    # 4. 安全解析付款节点（使用 safe_json_loads 避免 JSON 解析异常）
    payment_nodes = safe_json_loads(
        contract.payment_nodes,
        default=[],
        field_name="payment_nodes",
    )

    # 5. 使用事务保护创建项目及相关数据
    try:
        async with db.begin_nested():
            # 创建项目
            project = Project(
                code=await _generate_project_code(db),
                name=f"{contract.contract_code}-{customer.name}",
                customer_id=customer.id,
                contract_id=contract.id,
                amount=contract.contract_amount,
                sow_text=contract.sow_text or "",
                acceptance_criteria=contract.acceptance_criteria or [],
                stage="S1",  # 需求进入
                status="ST01",  # 未启动
                health_status="H1",  # 正常
            )

            db.add(project)
            await db.flush()

            # 处理付款节点
            milestone_count = 0
            if payment_nodes:
                milestone_count = len(payment_nodes)

                for idx, node in enumerate(payment_nodes, 1):
                    # 计算里程碑序号
                    milestone_seq = idx + 1

                    # 创建收款计划
                    payment_plan = PaymentPlan(
                        project_id=project.id,
                        contract_id=contract.id,
                        node_name=node.get("name", f"付款节点{milestone_seq}"),
                        percentage=node.get("percentage", 0),
                        amount=(
                            contract.contract_amount * node.get("percentage", 0) / 100
                            if node.get("percentage")
                            else 0
                        ),
                        due_date=node.get("due_date"),
                        status="PENDING",
                    )

                    db.add(payment_plan)
                    await db.flush()

                    # 创建对应的里程碑
                    milestone = ProjectMilestone(
                        project_id=project.id,
                        name=f"M{milestone_seq}",
                        description=node.get("description", f"付款里程碑{milestone_seq}"),
                        planned_date=node.get("due_date"),
                        sequence=milestone_seq,
                        status="NOT_STARTED",
                    )

                    db.add(milestone)
                    await db.flush()

        await db.commit()

        logger.info(
            "合同 %s 成功创建项目 %s，付款节点数: %d",
            contract.contract_code,
            project.code,
            milestone_count,
        )

        return {
            "success": True,
            "message": "项目创建成功，付款节点已关联到里程碑",
            "project_id": project.id,
            "project_code": project.code,
            "payment_plans_count": milestone_count,
            "milestones_count": milestone_count,
        }

    except Exception as e:
        await db.rollback()
        logger.error("从合同 %s 创建项目失败: %s", contract_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"创建项目失败: {str(e)}",
        )


# 辅助函数
async def _generate_project_code(db: AsyncSession) -> str:
    """生成项目编码"""
    from datetime import datetime

    now = datetime.now()
    year = now.year
    month = now.month

    # 查找当月已有项目编码
    month_prefix = f"PJ{year:04d}{month:02d}"
    month_conditions = build_like_conditions(
        Project,
        f"{month_prefix}%",
        "code",
        use_ilike=False,
    )

    # 获取当月最后一个编码
    result = await db.execute(
        select(Project.code).where(month_conditions[0]).order_by(Project.code.desc()).limit(1)
    )
    last_project_code = result.scalar_one_or_none()

    seq_num = 1
    if last_project_code:
        # 提取序号数字部分（格式：PJyyyymm###）
        try:
            seq_num = int(last_project_code[-3:]) + 1
        except (ValueError, IndexError, TypeError):
            seq_num = 1

    seq_str = f"{seq_num:03d}"
    project_code = f"{month_prefix}{seq_str}"

    return project_code
