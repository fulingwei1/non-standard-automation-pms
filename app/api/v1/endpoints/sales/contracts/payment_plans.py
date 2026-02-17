# -*- coding: utf-8 -*-
"""
合同收款计划 API endpoints
包括：收款计划查询
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.project import ProjectPaymentPlan
from app.models.sales import Contract
from app.models.user import User
from app.schemas.project import ProjectPaymentPlanResponse
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/contracts/{contract_id}/payment-plans", response_model=List[ProjectPaymentPlanResponse])
def get_contract_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同的收款计划列表
    """

    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    # 查询收款计划
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.contract_id == contract_id
    ).options(
        joinedload(ProjectPaymentPlan.milestone),
        joinedload(ProjectPaymentPlan.project)
    ).order_by(ProjectPaymentPlan.payment_no).all()

    result = []
    for plan in payment_plans:
        plan_dict = {
            **{c.name: getattr(plan, c.name) for c in plan.__table__.columns},
            "project_code": plan.project.project_code if plan.project else None,
            "project_name": plan.project.project_name if plan.project else None,
            "contract_code": contract.contract_code,
            "milestone_code": plan.milestone.milestone_code if plan.milestone else None,
            "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
        }
        result.append(ProjectPaymentPlanResponse(**plan_dict))

    return result
