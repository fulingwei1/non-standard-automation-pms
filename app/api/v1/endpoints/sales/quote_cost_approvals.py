# -*- coding: utf-8 -*-
"""
成本审批 - 自动生成
从 sales/quotes.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.sales import (

from app.schemas.sales import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/quotes/{quote_id}/cost-approval",
    tags=["cost_approvals"]
)

# 共 5 个路由

@router.get("/quotes/project-cycle-estimate", response_model=ResponseModel)
def estimate_project_cycle(
    *,
    contract_amount: Optional[float] = Query(None, description="合同金额（用于估算）"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    complexity_level: str = Query("MEDIUM", description="复杂度：SIMPLE/MEDIUM/COMPLEX"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目周期估算API

    根据项目类型、金额、复杂度估算项目周期
    返回各阶段工期建议
    """
    from app.services.delivery_validation_service import DeliveryValidationService

    cycle_estimate = DeliveryValidationService.estimate_project_cycle(
        db=None,  # 不需要数据库
        contract_amount=contract_amount,
        project_type=project_type,
        complexity_level=complexity_level
    )

    return ResponseModel(
        code=200,
        message="项目周期估算完成",
        data=cycle_estimate
    )


# ==================== 成本审批 ====================


@router.post("/quotes/{quote_id}/cost-approval/submit", response_model=QuoteCostApprovalResponse, status_code=201)
def submit_cost_approval(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_in: QuoteCostApprovalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交成本审批
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == approval_in.quote_version_id).first()
    if not version or version.quote_id != quote_id:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 执行成本检查
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    total_price = float(version.total_price or 0)
    gross_margin = float(version.gross_margin or 0) if version.gross_margin else ((total_price - total_cost) / total_price * 100 if total_price > 0 else 0)

    # 判断毛利率状态
    margin_threshold = 20.0 if approval_in.approval_level == 1 else 15.0
    if gross_margin >= margin_threshold:
        margin_status = "PASS"
    elif gross_margin >= 15.0:
        margin_status = "WARNING"
    else:
        margin_status = "FAIL"

    # 创建审批记录
    approval = QuoteCostApproval(
        quote_id=quote_id,
        quote_version_id=approval_in.quote_version_id,
        approval_status="PENDING",
        approval_level=approval_in.approval_level,
        current_approver_id=None,  # 根据审批层级确定审批人
        total_price=total_price,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_threshold=margin_threshold,
        margin_status=margin_status,
        cost_complete=len(items) > 0 and all(item.cost and item.cost > 0 for item in items),
        delivery_check=all(item.lead_time_days for item in items if item.item_type in ['硬件', '外购件']),
        risk_terms_check=bool(version.risk_terms),
        approval_comment=approval_in.comment
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.post("/quotes/{quote_id}/cost-approval/{approval_id}/approve", response_model=QuoteCostApprovalResponse)
def approve_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_id: int,
    action: QuoteCostApprovalAction,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过
    """
    approval = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.id == approval_id,
        QuoteCostApproval.quote_id == quote_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="审批记录不是待审批状态")

    approval.approval_status = "APPROVED"
    approval.approved_by = current_user.id
    approval.approved_at = datetime.now()
    approval.approval_comment = action.comment

    # 如果是最低层级审批通过，更新报价版本状态
    if approval.approval_level == 1:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == approval.quote_version_id).first()
        if version:
            version.cost_breakdown_complete = approval.cost_complete
            version.margin_warning = approval.margin_status in ["WARNING", "FAIL"]

    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.post("/quotes/{quote_id}/cost-approval/{approval_id}/reject", response_model=QuoteCostApprovalResponse)
def reject_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_id: int,
    action: QuoteCostApprovalAction,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    if not action.reason:
        raise HTTPException(status_code=400, detail="驳回原因不能为空")

    approval = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.id == approval_id,
        QuoteCostApproval.quote_id == quote_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="审批记录不是待审批状态")

    approval.approval_status = "REJECTED"
    approval.approved_by = current_user.id
    approval.approved_at = datetime.now()
    approval.rejected_reason = action.reason
    approval.approval_comment = action.comment

    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.get("/quotes/{quote_id}/cost-approval/history", response_model=List[QuoteCostApprovalResponse])
def get_cost_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本审批历史
    """
    approvals = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.quote_id == quote_id
    ).order_by(desc(QuoteCostApproval.created_at)).all()

    result = []
    for approval in approvals:
        approval_dict = {
            **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
            "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
            "approved_by_name": approval.approver.real_name if approval.approver else None
        }
        result.append(QuoteCostApprovalResponse(**approval_dict))

    return result



