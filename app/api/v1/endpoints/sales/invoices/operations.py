# -*- coding: utf-8 -*-
"""
发票操作 API endpoints
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.approval import ApprovalInstance
from app.models.enums import InvoiceStatusEnum, WorkflowTypeEnum
from app.models.sales import Invoice
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import InvoiceIssueRequest
from app.services.sales.invoice_operation_audit import (
    invoice_audit_value,
    log_invoice_operation,
)
from app.utils.number_generator import generate_sequential_no

logger = logging.getLogger(__name__)

from app.utils.db_helpers import get_or_404

router = APIRouter()

RED_CREDIT_INVOICE_TYPE = "RED_CREDIT"
REVERSED_PAYMENT_STATUS = "REVERSED"


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _append_remark(invoice: Invoice, line: str) -> None:
    invoice.remark = f"{invoice.remark or ''}\n{line}".strip()


def _generate_red_credit_invoice_code(db: Session) -> str:
    return generate_sequential_no(
        db=db,
        model_class=Invoice,
        no_field="invoice_code",
        prefix="INV-R",
        date_format="%y%m%d",
        separator="-",
        seq_length=3,
    )


def _create_red_credit_invoice(db: Session, invoice: Invoice, reason: Optional[str]) -> Invoice:
    paid_amount = _money(invoice.paid_amount)
    original_amount = _money(invoice.amount)
    original_tax_amount = _money(invoice.tax_amount) if invoice.tax_amount is not None else None
    original_total_amount = _money(
        invoice.total_amount if invoice.total_amount is not None else invoice.amount
    )
    reason_text = reason or "未填写"

    red_invoice = Invoice(
        invoice_code=_generate_red_credit_invoice_code(db),
        contract_id=invoice.contract_id,
        project_id=invoice.project_id,
        payment_id=invoice.payment_id,
        invoice_type=RED_CREDIT_INVOICE_TYPE,
        amount=-original_amount,
        tax_rate=invoice.tax_rate,
        tax_amount=-original_tax_amount if original_tax_amount is not None else None,
        total_amount=-original_total_amount,
        status=InvoiceStatusEnum.ISSUED.value,
        payment_status=REVERSED_PAYMENT_STATUS,
        issue_date=date.today(),
        paid_amount=-paid_amount,
        paid_date=invoice.paid_date,
        buyer_name=invoice.buyer_name,
        buyer_tax_no=invoice.buyer_tax_no,
        approval_status="APPROVED",
        remark=(
            f"红冲发票，原发票: {invoice.invoice_code}({invoice.id}); "
            f"作废原因: {reason_text}"
        ),
    )
    db.add(red_invoice)
    db.flush()
    return red_invoice


def _latest_invoice_approval_instance(db: Session, invoice: Invoice) -> ApprovalInstance | None:
    if invoice.approval_instance_id:
        instance = (
            db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.id == invoice.approval_instance_id,
                ApprovalInstance.entity_type == WorkflowTypeEnum.INVOICE.value,
                ApprovalInstance.entity_id == invoice.id,
            )
            .first()
        )
        if instance:
            return instance

    return (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == WorkflowTypeEnum.INVOICE.value,
            ApprovalInstance.entity_id == invoice.id,
        )
        .order_by(ApprovalInstance.created_at.desc(), ApprovalInstance.id.desc())
        .first()
    )


def _require_invoice_ready_to_issue(db: Session, invoice: Invoice) -> None:
    current_status = (invoice.status or "").upper()
    if current_status != InvoiceStatusEnum.APPROVED.value:
        raise HTTPException(status_code=400, detail="发票尚未处于已审批状态，无法开票")

    instance = _latest_invoice_approval_instance(db, invoice)
    if not instance or instance.status != "APPROVED":
        raise HTTPException(status_code=400, detail="发票尚未通过审批，无法开票")


@router.post("/invoices/{invoice_id}/issue", response_model=ResponseModel)
def issue_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    issue_request: InvoiceIssueRequest,
    current_user: User = Depends(security.require_permission("finance:update")),
) -> Any:
    """
    开票
    """
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")
    _require_invoice_ready_to_issue(db, invoice)
    old_value = invoice_audit_value(invoice)

    invoice.issue_date = issue_request.issue_date
    invoice.status = InvoiceStatusEnum.ISSUED.value
    invoice.payment_status = "PENDING"

    # 如果没有设置到期日期，默认设置为开票日期后30天
    if not invoice.due_date and invoice.issue_date:
        invoice.due_date = invoice.issue_date + timedelta(days=30)

    log_invoice_operation(
        db,
        invoice,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=invoice_audit_value(invoice),
        operation_desc="开具发票",
        remark=f"issue_date={invoice.issue_date.isoformat() if invoice.issue_date else ''}",
    )
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
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")

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

    return ResponseModel(
        code=200,
        message="收款记录成功",
        data={"paid_amount": float(new_paid), "payment_status": invoice.payment_status},
    )


def _void_invoice_logic(
    db: Session,
    invoice_id: int,
    reason: Optional[str],
    current_user: User,
) -> ResponseModel:
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")

    # 只有已开票或已审批的发票才能作废
    if invoice.status not in [
        InvoiceStatusEnum.ISSUED.value,
        InvoiceStatusEnum.APPROVED.value,
    ]:
        raise HTTPException(status_code=400, detail="只有已开票或已审批的发票才能作废")

    old_value = invoice_audit_value(invoice)
    red_invoice = None
    if invoice.status == InvoiceStatusEnum.ISSUED.value:
        red_invoice = _create_red_credit_invoice(db, invoice, reason)
        log_invoice_operation(
            db,
            red_invoice,
            SalesOperationType.CREATE,
            current_user,
            new_value=invoice_audit_value(red_invoice),
            operation_desc="生成红冲发票",
            remark=f"original_invoice_id={invoice.id}; reason={reason or ''}",
        )

    invoice.status = InvoiceStatusEnum.CANCELLED.value
    if reason:
        _append_remark(invoice, f"作废原因: {reason}")
    if red_invoice:
        _append_remark(invoice, f"红冲发票: {red_invoice.invoice_code}")

    log_invoice_operation(
        db,
        invoice,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=invoice_audit_value(invoice),
        operation_desc="作废发票",
        remark=reason,
    )
    db.commit()

    if red_invoice:
        return ResponseModel(
            code=200,
            message="发票已作废并生成红冲发票",
            data={
                "invoice_id": invoice.id,
                "red_invoice_id": red_invoice.id,
                "red_invoice_code": red_invoice.invoice_code,
            },
        )

    return ResponseModel(code=200, message="发票已作废")


@router.put("/invoices/{invoice_id}/void", response_model=ResponseModel)
def void_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    reason: Optional[str] = Query(None, description="作废原因"),
    current_user: User = Depends(security.require_permission("finance:update")),
) -> Any:
    """
    作废发票
    """
    return _void_invoice_logic(db, invoice_id, reason, current_user)


@router.post("/invoices/{invoice_id}/cancel", response_model=ResponseModel, include_in_schema=False)
def cancel_invoice_legacy(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    cancel_request: Optional[dict[str, Any]] = Body(default=None),
    current_user: User = Depends(security.require_permission("finance:update")),
) -> Any:
    """旧版发票作废入口，兼容 POST /invoices/{id}/cancel。"""
    payload = cancel_request or {}
    reason = payload.get("reason") or payload.get("cancel_reason")
    return _void_invoice_logic(db, invoice_id, reason, current_user)
