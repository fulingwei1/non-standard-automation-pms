# -*- coding: utf-8 -*-
"""
合同管理端点 - 从合同创建项目
创建日期：2026-01-25
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales.contracts import Contract
from app.services.sales.contract.status_service import normalize_contract_status
from app.services.sales.payment_plan_service import PaymentPlanService
from app.services.status_transition_service import StatusTransitionService

from ..utils.gate_validation import validate_g4_contract_to_project

logger = logging.getLogger(__name__)

# 允许创建项目的合同状态
ALLOWED_CONTRACT_STATUSES = {"SIGNED", "EXECUTING"}

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/{contract_id}/create-project")
def create_project_from_contract(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(security.require_permission("contract:create")),
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

    contract = (
        db.query(Contract)
        .options(selectinload(Contract.customer), selectinload(Contract.deliverables))
        .filter(Contract.id == contract_id)
        .first()
    )

    if not contract:
        raise HTTPException(status_code=404, detail=f"合同不存在: {contract_id}")

    # 2. 验证合同状态（只有已签署/执行中的合同才能创建项目）
    if normalize_contract_status(contract.status) not in ALLOWED_CONTRACT_STATUSES:
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

    try:
        transition_service = StatusTransitionService(db)
        project = transition_service.handle_contract_signed(
            contract_id, auto_create_project=True
        )
        if not project:
            raise HTTPException(status_code=500, detail="创建项目失败")

        db.refresh(contract)
        payment_plans = PaymentPlanService(db).generate_payment_plans_from_contract(contract)
        db.commit()

        logger.info(
            "合同 %s 通过兼容入口成功创建项目 %s，收款计划数: %d",
            contract.contract_code,
            project.project_code,
            len(payment_plans),
        )

        return {
            "success": True,
            "message": "项目创建成功，销售/售前上下文已同步",
            "project_id": project.id,
            "project_code": project.project_code,
            "payment_plans_count": len(payment_plans),
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("从合同 %s 创建项目失败: %s", contract_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"创建项目失败: {str(e)}",
        )
