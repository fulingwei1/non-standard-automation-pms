# -*- coding: utf-8 -*-
"""
催款优先级 API

提供智能催款优先级排序接口。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.collection_priority_service import (
    CollectionPriorityService,
    CollectionUrgency,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/priority", response_model=ResponseModel)
def get_collection_priority_list(
    db: Session = Depends(deps.get_db),
    urgency: Optional[str] = Query(
        None,
        description="紧急程度过滤: critical, high, medium, low",
    ),
    include_non_overdue: bool = Query(
        False,
        description="是否包含未逾期的应收",
    ),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取催款优先级排序列表

    系统自动分析用户负责的应收账款，按优先级排序：
    - 综合评分：金额 + 逾期天数 + 客户信用 + 历史付款率
    - 紧急程度：critical（紧急）、high（高）、medium（中）、low（低）
    - 风险等级：high（高风险）、medium（中风险）、low（低风险）

    返回包含催款建议和行动要点的列表。
    """
    service = CollectionPriorityService(db)
    items = service.get_prioritized_collections(
        user_id=current_user.id,
        include_non_overdue=include_non_overdue,
        limit=limit,
    )

    # 按紧急程度过滤
    if urgency:
        try:
            urgency_filter = CollectionUrgency(urgency)
            items = [item for item in items if item.urgency == urgency_filter]
        except ValueError:
            pass

    # 转换为字典格式
    result_items = []
    for item in items:
        result_items.append({
            "invoice_id": item.invoice_id,
            "invoice_code": item.invoice_code,
            "contract_id": item.contract_id,
            "contract_code": item.contract_code,
            "customer_id": item.customer_id,
            "customer_name": item.customer_name,
            "invoice_amount": item.invoice_amount,
            "paid_amount": item.paid_amount,
            "unpaid_amount": item.unpaid_amount,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "overdue_days": item.overdue_days,
            "urgency": item.urgency.value,
            "risk": item.risk.value,
            "priority_score": item.priority_score,
            "customer_credit_level": item.customer_credit_level,
            "historical_payment_rate": item.historical_payment_rate,
            "suggestion": item.suggestion,
            "action_points": item.action_points,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": result_items,
            "total": len(result_items),
        },
    )


@router.get("/priority/summary", response_model=ResponseModel)
def get_collection_priority_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取催款优先级汇总

    返回各维度的统计数据：
    - 按紧急程度统计
    - 按风险等级统计
    - 按账龄统计
    - 优先级最高的5项

    适合在首页或仪表盘展示。
    """
    service = CollectionPriorityService(db)
    summary = service.get_collection_summary(current_user.id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data=summary,
    )


@router.get("/priority/critical", response_model=ResponseModel)
def get_critical_collections(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取紧急催款项（需立即处理）

    仅返回紧急程度为 critical 的催款项，适合早晨查看当日任务。
    """
    service = CollectionPriorityService(db)
    items = service.get_prioritized_collections(
        user_id=current_user.id,
        limit=20,
    )

    critical_items = [item for item in items if item.urgency == CollectionUrgency.CRITICAL]

    result_items = []
    for item in critical_items:
        result_items.append({
            "invoice_id": item.invoice_id,
            "invoice_code": item.invoice_code,
            "customer_name": item.customer_name,
            "unpaid_amount": item.unpaid_amount,
            "overdue_days": item.overdue_days,
            "risk": item.risk.value,
            "suggestion": item.suggestion,
            "action_points": item.action_points,
        })

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "items": result_items,
            "count": len(result_items),
            "tip": "这些是需要立即处理的紧急催款项" if result_items else "暂无紧急催款项 👍",
        },
    )
