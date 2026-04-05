# -*- coding: utf-8 -*-
"""
合同里程碑提醒 API

提供合同关键节点监控接口。
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.contract_milestone_service import (
    ContractMilestoneService,
    MilestoneType,
    MilestoneUrgency,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/milestones", response_model=ResponseModel)
def get_contract_milestones(
    db: Session = Depends(deps.get_db),
    types: Optional[List[str]] = Query(
        None,
        description="里程碑类型过滤: payment, delivery, warranty, contract",
    ),
    urgency: Optional[str] = Query(
        None,
        description="紧急程度过滤: overdue, urgent, warning, upcoming",
    ),
    days_ahead: int = Query(60, ge=7, le=180, description="提前天数"),
    include_overdue: bool = Query(True, description="是否包含已过期"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同里程碑列表

    监控的里程碑类型：
    - payment: 付款节点
    - delivery: 交付节点
    - warranty: 质保到期
    - contract: 合同到期

    紧急程度：
    - overdue: 已过期
    - urgent: 紧急（7天内）
    - warning: 预警（14天内）
    - upcoming: 即将到来（30天内）
    """
    # 转换类型参数
    type_filters = None
    if types:
        type_filters = []
        for t in types:
            try:
                type_filters.append(MilestoneType(t))
            except ValueError:
                pass

    service = ContractMilestoneService(db)
    milestones = service.get_upcoming_milestones(
        user_id=current_user.id,
        include_types=type_filters,
        days_ahead=days_ahead,
        include_overdue=include_overdue,
        limit=limit,
    )

    # 按紧急程度过滤
    if urgency:
        try:
            urgency_filter = MilestoneUrgency(urgency)
            milestones = [m for m in milestones if m.urgency == urgency_filter]
        except ValueError:
            pass

    # 转换为字典
    items = []
    for m in milestones:
        items.append({
            "contract_id": m.contract_id,
            "contract_code": m.contract_code,
            "contract_name": m.contract_name,
            "customer_name": m.customer_name,
            "milestone_type": m.milestone_type.value,
            "milestone_name": m.milestone_name,
            "due_date": m.due_date.isoformat(),
            "days_until": m.days_until,
            "urgency": m.urgency.value,
            "amount": m.amount,
            "suggestion": m.suggestion,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "total": len(items),
        },
    )


@router.get("/milestones/summary", response_model=ResponseModel)
def get_milestone_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取里程碑汇总统计

    返回：
    - 按紧急程度统计
    - 按类型统计
    - 紧急待处理项列表

    适合在仪表盘展示。
    """
    service = ContractMilestoneService(db)
    summary = service.get_milestone_summary(current_user.id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data=summary,
    )


@router.get("/milestones/overdue", response_model=ResponseModel)
def get_overdue_milestones(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取已过期的里程碑

    仅返回已过期的里程碑，这些需要立即处理。
    """
    service = ContractMilestoneService(db)
    milestones = service.get_upcoming_milestones(
        user_id=current_user.id,
        include_overdue=True,
        limit=50,
    )

    overdue = [m for m in milestones if m.urgency == MilestoneUrgency.OVERDUE]

    items = []
    for m in overdue:
        items.append({
            "contract_id": m.contract_id,
            "contract_code": m.contract_code,
            "customer_name": m.customer_name,
            "milestone_type": m.milestone_type.value,
            "milestone_name": m.milestone_name,
            "due_date": m.due_date.isoformat(),
            "days_overdue": abs(m.days_until),
            "amount": m.amount,
            "suggestion": m.suggestion,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "count": len(items),
            "tip": "这些里程碑已过期，需要立即处理" if items else "暂无过期里程碑 👍",
        },
    )


@router.get("/milestones/payments", response_model=ResponseModel)
def get_payment_milestones(
    db: Session = Depends(deps.get_db),
    days_ahead: int = Query(30, ge=7, le=90, description="提前天数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取付款节点里程碑

    专门用于付款节点跟踪，包含金额信息。
    """
    service = ContractMilestoneService(db)
    milestones = service.get_upcoming_milestones(
        user_id=current_user.id,
        include_types=[MilestoneType.PAYMENT],
        days_ahead=days_ahead,
        include_overdue=True,
        limit=50,
    )

    items = []
    total_amount = 0

    for m in milestones:
        items.append({
            "contract_id": m.contract_id,
            "contract_code": m.contract_code,
            "customer_name": m.customer_name,
            "milestone_name": m.milestone_name,
            "due_date": m.due_date.isoformat(),
            "days_until": m.days_until,
            "urgency": m.urgency.value,
            "amount": m.amount,
            "suggestion": m.suggestion,
        })
        if m.amount:
            total_amount += m.amount

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": items,
            "total": len(items),
            "total_amount": total_amount,
            "summary": {
                "overdue_count": len([m for m in milestones if m.urgency == MilestoneUrgency.OVERDUE]),
                "urgent_count": len([m for m in milestones if m.urgency == MilestoneUrgency.URGENT]),
            },
        },
    )
