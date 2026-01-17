# -*- coding: utf-8 -*-
"""
发票多级审批 API endpoints (旧版 - 保持兼容性)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Invoice, InvoiceApproval
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import InvoiceApprovalResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put("/invoices/{invoice_id}/approve", response_model=ResponseModel)
def approve_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开票审批（单级审批，兼容旧接口）
    """
    # 检查审批权限
    if not security.has_sales_approval_access(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批发票"
        )

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if approved:
        invoice.status = "APPROVED"
    else:
        invoice.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="发票审批完成" if approved else "发票已驳回")


@router.put("/invoices/{invoice_id}/submit-approval", response_model=ResponseModel)
def submit_invoice_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交发票审批（创建多级审批记录）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查是否已有审批记录
    existing_approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).count()
    if existing_approvals > 0:
        raise HTTPException(status_code=400, detail="发票已提交审批，请勿重复提交")

    # 根据发票金额确定审批流程
    invoice_amount = float(invoice.total_amount or invoice.amount or 0)

    # 审批流程：根据金额确定审批层级
    # 小于10万：财务（1级）
    # 10-50万：财务（1级）+ 财务经理（2级）
    # 大于50万：财务（1级）+ 财务经理（2级）+ 财务总监（3级）

    approval_levels = []
    if invoice_amount < 100000:
        approval_levels = [1]  # 财务
    elif invoice_amount < 500000:
        approval_levels = [1, 2]  # 财务 + 财务经理
    else:
        approval_levels = [1, 2, 3]  # 财务 + 财务经理 + 财务总监

    # 创建审批记录
    role_map = {1: "财务", 2: "财务经理", 3: "财务总监"}
    for level in approval_levels:
        approval = InvoiceApproval(
            invoice_id=invoice_id,
            approval_level=level,
            approval_role=role_map.get(level, "审批人"),
            status="PENDING",
            due_date=datetime.now() + timedelta(days=2)  # 默认2天审批期限
        )
        db.add(approval)

    invoice.status = "APPLIED"
    db.commit()

    return ResponseModel(code=200, message="发票已提交审批", data={"approval_levels": len(approval_levels)})


@router.get("/invoices/{invoice_id}/approvals", response_model=List[InvoiceApprovalResponse])
def get_invoice_approvals(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批记录列表
    """
    approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).order_by(InvoiceApproval.approval_level).all()

    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None

        result.append(InvoiceApprovalResponse(
            id=approval.id,
            invoice_id=approval.invoice_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            status=approval.status,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))

    return result


@router.put("/invoice-approvals/{approval_id}/approve", response_model=InvoiceApprovalResponse)
def approve_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        pending_approvals = db.query(InvoiceApproval).filter(
            InvoiceApproval.invoice_id == approval.invoice_id,
            InvoiceApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新发票状态
            invoice.status = "APPROVED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/invoice-approvals/{approval_id}/reject", response_model=InvoiceApprovalResponse)
def reject_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，发票状态变为被拒
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        invoice.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )
