# -*- coding: utf-8 -*-
"""
合同管理端点 - 从合同创建项目
创建日期：2026-01-25
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales.contracts import Contract
from app.models.project import Project
from app.common.query_filters import build_like_conditions
from app.api.deps import get_db, get_current_active_user

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.models.customer import Customer
from app.models.project import PaymentPlan
from app.models.project import ProjectMilestone


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/{contract_id}/create-project")
async def create_project_from_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=get_current_active_user,
):
    """
    从合同创建项目，自动绑定付款节点到里程碑

    功能说明：
    1. 查询合同（包含客户信息）
    2. 创建项目
    3. 从合同的payment_nodes字段提取付款节点列表
    4. 如果有付款节点，为每个节点创建收款计划和对应里程碑
    5. 将合同金额同步到项目
    6. 同步SOW/验收标准到项目
    """

    # 1. 查询合同
    result = await db.execute(
        select(Contract)
        .options(selectinload(Customer))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail=f"合同不存在: {contract_id}")

    customer = contract.customer

    # 2. 检查合同是否有付款节点
    payment_nodes = contract.payment_nodes or []
    if payment_nodes:
        if isinstance(payment_nodes, list):
            payment_nodes = payment_nodes
        elif isinstance(payment_nodes, str):
            import json

            try:
                payment_nodes = json.loads(payment_nodes)
            except (json.JSONDecodeError, TypeError, ValueError):
                payment_nodes = []

    # 3. 创建项目
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

    # 4. 处理付款节点
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
                amount=contract.contract_amount * node.get("percentage", 0) / 100
                if node.get("percentage")
                else 0,
                due_date=node.get("due_date"),
                status="PENDING",
            )

            db.add(payment_plan)
            await db.flush()

            # 创建对应的里程碑（简化逻辑，实际应根据WBS模板创建）
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

        return {
            "project_id": project.id,
            "project_code": project.code,
            "payment_plans_count": milestone_count,
            "milestones_count": milestone_count,
        }

    await db.commit()

    return {
        "success": True,
        "message": "项目创建成功，付款节点已关联到里程碑",
        "project_id": project.id,
        "project_code": project.code,
        "payment_plans_count": len(payment_nodes) if payment_nodes else 0,
        "milestones_count": len(payment_nodes) if payment_nodes else 0,
    }


# 辅助函数
async def _generate_project_code(db: AsyncSession) -> str:
    """生成项目编码"""
    pj_conditions = build_like_conditions(Project, "PJ%", "code", use_ilike=False)
    result = await db.execute(
        select(func.count(Project.id)).where(pj_conditions[0])
    )
    result.scalar() + 1

    # 格式：PJyymmddxxx
    from datetime import datetime

    now = datetime.now()

    # 获取日期部分
    year = now.year
    month = now.month

    # 获取序号
    month_conditions = build_like_conditions(
        Project,
        f"PJ{year:04d}{month:02d}%",
        "code",
        use_ilike=False,
    )
    await db.execute(
        select(func.count(Project.id)).where(month_conditions[0])
    )
    last_seq = result.scalar()

    # 格式化序号为3位
    last_seq + 1

    # 获取对应的数字部分
    # 获取最后创建项目的序号
    result = await db.execute(
        select(Project.code)
        .where(month_conditions[0])
        .order_by(Project.id.desc())
        .limit(1)
    )
    last_project_code = result.scalar_one()

    seq_num = 1
    if last_project_code:
        # 提取序号数字部分
        try:
            seq_num = int(last_project_code[5:9])  # 格式：PJyymmddxxx，提取后3位数字
        except (ValueError, IndexError, TypeError):
            seq_num = 1

    # 计算填充序号
    seq_str = f"{seq_num:03d}"

    # 如果序号重复，则递增
    result = await db.execute(
        select(func.count(Project.id)).where(
            Project.code == f"PJ{year:04d}{month:02d}{seq_str}"
        )
    )
    existing_count = result.scalar()

    if existing_count > 0:
        # 序号递增
        seq_num += 1
        if seq_num >= 999:
            seq_num = 1
        seq_str = f"{seq_num:03d}"

    # 生成完整编码
    project_code = f"PJ{year:04d}{month:02d}{seq_str}"

    return project_code
