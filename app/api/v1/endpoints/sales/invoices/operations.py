# -*- coding: utf-8 -*-
"""
发票操作 API endpoints
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ApprovalRecordStatusEnum,
    InvoiceStatusEnum,
    WorkflowTypeEnum,
)
from app.models.sales import Invoice
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import InvoiceIssueRequest
from app.services.approval_engine import ApprovalEngineService as ApprovalWorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/invoices/{invoice_id}/issue", response_model=ResponseModel)
def issue_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    issue_request: InvoiceIssueRequest,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    开票
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查是否已通过审批（如果启用了审批工作流）
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
    )

    if record and record.status != ApprovalRecordStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="发票尚未通过审批，无法开票")

    invoice.issue_date = issue_request.issue_date
    invoice.status = InvoiceStatusEnum.ISSUED
    invoice.payment_status = "PENDING"

    # 如果没有设置到期日期，默认设置为开票日期后30天
    if not invoice.due_date and invoice.issue_date:
        invoice.due_date = invoice.issue_date + timedelta(days=30)

    db.commit()

    # 发送发票开具通知
    try:
        from app.services.sales_reminder import notify_invoice_issued
        notify_invoice_issued(db, invoice.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        logger.warning(f"发票开具通知发送失败，不影响主流程: {e}", exc_info=True)

    return ResponseModel(code=200, message="发票开票成功")


@router.post("/invoices/{invoice_id}/receive-payment", response_model=ResponseModel)
def receive_payment(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    paid_amount: str = Query(..., description="收款金额"),
    paid_date: date = Query(..., description="收款日期"),
    remark: Optional[str] = Query(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    记录发票收款
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能记录收款")

    # 更新收款信息
    current_paid = invoice.paid_amount or Decimal("0")
    paid_amount_decimal = Decimal(str(paid_amount))
    new_paid = current_paid + paid_amount_decimal
    invoice.paid_amount = new_paid
    invoice.paid_date = paid_date

    # 更新收款状态
    total = invoice.total_amount or invoice.amount or Decimal("0")
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"
    else:
        invoice.payment_status = "PENDING"

    if remark:
        invoice.remark = (invoice.remark or "") + f"\n收款备注: {remark}"

    db.commit()

    return ResponseModel(code=200, message="收款记录成功", data={
        "paid_amount": float(new_paid),
        "payment_status": invoice.payment_status
    })


@router.put("/invoices/{invoice_id}/void", response_model=ResponseModel)
def void_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    reason: Optional[str] = Query(None, description="作废原因"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    作废发票
    """
    from app.models.enums import InvoiceStatusEnum

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有已开票或已审批的发票才能作废
    if invoice.status not in [InvoiceStatusEnum.ISSUED, InvoiceStatusEnum.APPROVED]:
        raise HTTPException(status_code=400, detail="只有已开票或已审批的发票才能作废")

    # 如果已收款，不能作废
    if invoice.paid_amount and invoice.paid_amount > 0:
        raise HTTPException(status_code=400, detail="已收款的发票不能作废，请先处理收款")

    invoice.status = InvoiceStatusEnum.VOIDED
    if reason:
        invoice.remark = (invoice.remark or "") + f"\n作废原因: {reason}"

    db.commit()

    return ResponseModel(code=200, message="发票已作废")
