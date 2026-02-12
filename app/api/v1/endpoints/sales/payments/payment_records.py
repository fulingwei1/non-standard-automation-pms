# -*- coding: utf-8 -*-
"""
回款记录管理 endpoints
"""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/payments", response_model=PaginatedResponse)
def get_payment_records(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    payment_status: Optional[str] = Query(None, description="收款状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款记录列表（基于发票）
    Issue 7.1: 已集成数据权限过滤（财务和销售总监可以看到所有收款数据）
    """
    query = db.query(Invoice).filter(Invoice.status == "ISSUED")

    # Issue 7.1: 应用财务数据权限过滤（财务和销售总监可以看到所有收款数据）
    query = security.filter_sales_finance_data_by_scope(query, current_user, db, Invoice, 'owner_id')

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    if project_id:
        query = query.filter(Invoice.project_id == project_id)

    if customer_id:
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    if payment_status:
        query = query.filter(Invoice.payment_status == payment_status)

    if start_date:
        query = query.filter(Invoice.paid_date >= start_date)

    if end_date:
        query = query.filter(Invoice.paid_date <= end_date)

    total = query.count()
    invoices = apply_pagination(query.order_by(desc(Invoice.paid_date)), pagination.offset, pagination.limit).all()

    items = []
    for invoice in invoices:
        contract = invoice.contract
        items.append({
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "project_id": invoice.project_id,
            "project_code": invoice.project.project_code if invoice.project else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(invoice.total_amount or invoice.amount or 0),
            "paid_amount": float(invoice.paid_amount or 0),
            "unpaid_amount": float((invoice.total_amount or invoice.amount or 0) - (invoice.paid_amount or 0)),
            "payment_status": invoice.payment_status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "paid_date": invoice.paid_date,
            "overdue_days": (date.today() - invoice.due_date).days if invoice.due_date and invoice.due_date < date.today() and invoice.payment_status in ["PENDING", "PARTIAL"] else None,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/payments", response_model=ResponseModel)
def create_payment_record(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int = Query(..., description="发票ID"),
    paid_amount: Decimal = Query(..., description="收款金额"),
    paid_date: date = Query(..., description="收款日期"),
    payment_method: Optional[str] = Query(None, description="收款方式"),
    bank_account: Optional[str] = Query(None, description="收款账户"),
    remark: Optional[str] = Query(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    登记回款
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能登记回款")

    # 更新收款信息
    current_paid = invoice.paid_amount or Decimal("0")
    new_paid = current_paid + paid_amount
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

    # 更新备注
    payment_note = f"收款记录: {paid_date}, 金额: {paid_amount}"
    if payment_method:
        payment_note += f", 方式: {payment_method}"
    if bank_account:
        payment_note += f", 账户: {bank_account}"
    if remark:
        payment_note += f", 备注: {remark}"

    invoice.remark = (invoice.remark or "") + f"\n{payment_note}"

    db.commit()

    return ResponseModel(
        code=200,
        message="回款登记成功",
        data={
            "invoice_id": invoice.id,
            "paid_amount": float(new_paid),
            "payment_status": invoice.payment_status,
            "unpaid_amount": float(total - new_paid)
        }
    )


@router.get("/payments/{payment_id}", response_model=ResponseModel)
def get_payment_detail(
    *,
    db: Session = Depends(deps.get_db),
    payment_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款详情（基于发票ID）
    """
    invoice = db.query(Invoice).options(
        joinedload(Invoice.contract),
        joinedload(Invoice.project)
    ).filter(Invoice.id == payment_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    contract = invoice.contract
    project = invoice.project

    total = invoice.total_amount or invoice.amount or Decimal("0")
    paid = invoice.paid_amount or Decimal("0")
    unpaid = total - paid

    overdue_days = None
    if invoice.due_date and invoice.due_date < date.today() and invoice.payment_status in ["PENDING", "PARTIAL"]:
        overdue_days = (date.today() - invoice.due_date).days

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "contract_id": invoice.contract_id,
            "contract_code": contract.contract_code if contract else None,
            "project_id": invoice.project_id,
            "project_code": project.project_code if project else None,
            "customer_id": contract.customer_id if contract else None,
            "customer_name": contract.customer.customer_name if contract and contract.customer else None,
            "invoice_amount": float(total),
            "paid_amount": float(paid),
            "unpaid_amount": float(unpaid),
            "payment_status": invoice.payment_status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "paid_date": invoice.paid_date,
            "overdue_days": overdue_days,
            "remark": invoice.remark,
        }
    )


@router.put("/payments/{payment_id}/match-invoice", response_model=ResponseModel)
def match_payment_to_invoice(
    *,
    db: Session = Depends(deps.get_db),
    payment_id: int,
    invoice_id: int = Query(..., description="发票ID"),
    match_amount: Optional[Decimal] = Query(None, description="核销金额，不指定则核销全部未收金额"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    核销发票（将回款记录与发票关联）
    注意：这里 payment_id 实际上是发票ID，用于保持API路径一致性
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能核销")

    total = invoice.total_amount or invoice.amount or Decimal("0")
    current_paid = invoice.paid_amount or Decimal("0")
    unpaid = total - current_paid

    if match_amount:
        if match_amount > unpaid:
            raise HTTPException(status_code=400, detail=f"核销金额不能超过未收金额 {unpaid}")
        new_paid = current_paid + match_amount
    else:
        # 核销全部未收金额
        new_paid = total

    invoice.paid_amount = new_paid
    invoice.paid_date = date.today()

    # 更新收款状态
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"

    db.commit()

    return ResponseModel(
        code=200,
        message="发票核销成功",
        data={
            "invoice_id": invoice.id,
            "matched_amount": float(match_amount or unpaid),
            "paid_amount": float(new_paid),
            "payment_status": invoice.payment_status
        }
    )
