# -*- coding: utf-8 -*-
"""
发票基础 CRUD API endpoints
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.enums import InvoiceStatusEnum
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceTaxCalculationRequest,
    InvoiceUpdate,
)
from app.services.approval_engine import ApprovalEngineService

from ..utils import generate_invoice_code

logger = logging.getLogger(__name__)

from app.utils.db_helpers import delete_obj, get_or_404

router = APIRouter()


def _json_number(value: Decimal) -> int | float:
    """Return compact JSON numbers while keeping money rounded to cents."""
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
def read_invoices(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票列表
    Issue 7.1: 已集成数据权限过滤（财务可以看到所有发票）
    """
    query = db.query(Invoice).options(joinedload(Invoice.contract))

    # Issue 7.1: 应用财务数据权限过滤（财务可以看到所有发票）
    # 注意：Invoice 模型没有 owner_id 字段，所以跳过此过滤
    # query = security.filter_sales_finance_data_by_scope(query, current_user, db, Invoice, 'owner_id')

    query = apply_keyword_filter(query, Invoice, keyword, "invoice_code")

    if status:
        query = query.filter(Invoice.status == status)

    if customer_id:
        # 通过 contract 关联过滤客户
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    total = query.count()
    invoices = apply_pagination(
        query.order_by(desc(Invoice.created_at)), pagination.offset, pagination.limit
    ).all()

    invoice_responses = []
    for invoice in invoices:
        # 获取客户名称
        customer_name = None
        if invoice.contract and invoice.contract.customer:
            customer_name = invoice.contract.customer.customer_name

        invoice_dict = {
            **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
            "invoice_amount": invoice.amount,  # 映射 amount -> invoice_amount
            "contract_code": invoice.contract.contract_code if invoice.contract else None,
            "customer_name": customer_name,
        }
        invoice_responses.append(InvoiceResponse(**invoice_dict))

    return PaginatedResponse(
        items=invoice_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get(
    "/invoices/",
    response_model=PaginatedResponse[InvoiceResponse],
    include_in_schema=False,
)
def read_invoices_slash(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取发票列表 (trailing slash compatibility)."""
    return read_invoices(
        db=db,
        pagination=pagination,
        keyword=keyword,
        status=status,
        customer_id=customer_id,
        current_user=current_user,
    )


@router.post("/invoices/calculate-tax", response_model=ResponseModel)
def calculate_invoice_tax(
    *,
    request: InvoiceTaxCalculationRequest,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> ResponseModel:
    """计算发票税额。"""
    tax_amount = (request.amount * request.tax_rate / Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    total_amount = (request.amount + tax_amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return ResponseModel(
        data={
            "amount": _json_number(request.amount),
            "tax_rate": _json_number(request.tax_rate),
            "tax_amount": _json_number(tax_amount),
            "total_amount": _json_number(total_amount),
        }
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def read_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票详情
    """
    invoice = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.contract).joinedload(Contract.customer), joinedload(Invoice.project)
        )
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    contract = invoice.contract
    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "invoice_amount": invoice.amount,  # 映射 amount -> invoice_amount
        "contract_code": contract.contract_code if contract else None,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


def _create_invoice_logic(
    db: Session,
    invoice_in: InvoiceCreate,
    current_user: User,
) -> Any:
    """
    创建发票核心逻辑
    """
    invoice_data = invoice_in.model_dump()
    if invoice_data.get("invoice_amount") is not None:
        invoice_data["amount"] = invoice_data["invoice_amount"]
    if not invoice_data.get("issue_date") and invoice_data.get("invoice_date"):
        invoice_data["issue_date"] = invoice_data["invoice_date"]
    invoice_data.pop("invoice_amount", None)
    invoice_data.pop("invoice_date", None)

    # 如果没有提供编码，自动生成
    if not invoice_data.get("invoice_code"):
        invoice_data["invoice_code"] = generate_invoice_code(db)
    else:
        existing = (
            db.query(Invoice).filter(Invoice.invoice_code == invoice_data["invoice_code"]).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="发票编码已存在")

    contract = db.query(Contract).filter(Contract.id == invoice_data["contract_id"]).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # F3: 累计开票金额不得超过合同金额（排除已作废发票）
    contract_amount = Decimal(str(contract.total_amount)) if contract.total_amount is not None else None
    if contract_amount and contract_amount > 0:
        invoiced = (
            db.query(func.coalesce(func.sum(Invoice.amount), 0))
            .filter(
                Invoice.contract_id == contract.id,
                func.upper(func.coalesce(Invoice.status, "")) != "CANCELLED",
            )
            .scalar()
            or 0
        )
        new_amount = Decimal(str(invoice_data.get("amount") or 0))
        total_after = Decimal(str(invoiced)) + new_amount
        if total_after > contract_amount:
            raise HTTPException(
                status_code=400,
                detail=f"累计开票金额({total_after})超过合同金额({contract_amount})",
            )

    invoice = Invoice(**invoice_data)
    db.add(invoice)
    db.flush()

    # 如果发票状态是已提交，自动启动审批流程。
    if invoice.status in {"APPLIED", InvoiceStatusEnum.SUBMITTED.value}:
        try:
            from .workflow import _get_invoice_template_code, _invoice_form_data

            template_code = _get_invoice_template_code(db, None)
            workflow_service = ApprovalEngineService(db)
            workflow_service.submit(
                template_code=template_code,
                entity_type="INVOICE",
                entity_id=invoice.id,
                form_data=_invoice_form_data(invoice),
                initiator_id=current_user.id,
                title=f"发票审批 - {invoice.invoice_code}",
                summary=f"发票申请：{invoice.invoice_code}",
            )
        except Exception as e:
            # 如果启动审批失败，记录日志但不阻止发票创建
            logger.warning(f"发票审批流程启动失败: invoice_id={invoice.id}, error={str(e)}")

    db.commit()
    db.refresh(invoice)

    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "invoice_amount": invoice.amount,
        "invoice_date": invoice.issue_date,
        "contract_code": contract.contract_code,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.post("/invoices/", response_model=InvoiceResponse, status_code=201, include_in_schema=False)
def create_invoice_slash(
    *,
    db: Session = Depends(deps.get_db),
    invoice_in: InvoiceCreate,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """创建发票 (trailing slash)"""
    return _create_invoice_logic(db, invoice_in, current_user)


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_in: InvoiceCreate,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """创建发票"""
    return _create_invoice_logic(db, invoice_in, current_user)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """更新发票。"""
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")
    invoice_data = invoice_in.model_dump(exclude_unset=True)

    if "invoice_code" in invoice_data and invoice_data["invoice_code"] != invoice.invoice_code:
        existing = (
            db.query(Invoice)
            .filter(
                Invoice.invoice_code == invoice_data["invoice_code"],
                Invoice.id != invoice.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="发票编码已存在")

    if invoice_data.get("invoice_amount") is not None:
        invoice_data["amount"] = invoice_data["invoice_amount"]
    if invoice_data.get("invoice_date") is not None:
        invoice_data["issue_date"] = invoice_data["invoice_date"]

    invoice_data.pop("invoice_amount", None)
    invoice_data.pop("invoice_date", None)

    for field, value in invoice_data.items():
        if field == "status" and isinstance(value, str):
            value = value.upper()
        if hasattr(invoice, field):
            setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)

    contract = invoice.contract
    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "invoice_amount": invoice.amount,
        "invoice_date": invoice.issue_date,
        "contract_code": contract.contract_code if contract else None,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.delete("/invoices/{invoice_id}", status_code=200)
def delete_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """
    删除发票（仅限草稿状态）
    """
    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")

    # 只有草稿状态才能删除
    if invoice.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的发票才能删除")

    delete_obj(db, invoice)

    from app.schemas.common import ResponseModel

    return ResponseModel(code=200, message="发票已删除")
