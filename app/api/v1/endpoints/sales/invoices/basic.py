# -*- coding: utf-8 -*-
"""
发票基础 CRUD API endpoints
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.enums import (
    InvoiceStatusEnum,
    WorkflowTypeEnum,
)
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import InvoiceCreate, InvoiceResponse
from app.services.approval_engine import ApprovalEngineService as ApprovalWorkflowService

from ..utils import generate_invoice_code
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

logger = logging.getLogger(__name__)

router = APIRouter()


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
    query = db.query(Invoice).options(
        joinedload(Invoice.contract)
    )

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
    invoices = apply_pagination(query.order_by(desc(Invoice.created_at)), pagination.offset, pagination.limit).all()

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
        pages = pagination.pages_for_total(total)
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
    invoice = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    ).filter(Invoice.id == invoice_id).first()
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


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_in: InvoiceCreate,
    current_user: User = Depends(security.require_permission("finance:read")),
) -> Any:
    """
    创建发票
    """
    invoice_data = invoice_in.model_dump()

    # 如果没有提供编码，自动生成
    if not invoice_data.get("invoice_code"):
        invoice_data["invoice_code"] = generate_invoice_code(db)
    else:
        existing = db.query(Invoice).filter(Invoice.invoice_code == invoice_data["invoice_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="发票编码已存在")

    contract = db.query(Contract).filter(Contract.id == invoice_data["contract_id"]).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    invoice = Invoice(**invoice_data)
    db.add(invoice)
    db.flush()

    # 如果发票状态是 APPLIED，自动启动审批流程
    if invoice.status == InvoiceStatusEnum.APPLIED:
        try:
            workflow_service = ApprovalWorkflowService(db)
            routing_params = {"amount": float(invoice.amount or 0)}
            record = workflow_service.start_approval(
                entity_type=WorkflowTypeEnum.INVOICE,
                entity_id=invoice.id,
                initiator_id=current_user.id,
                workflow_id=None,  # 自动选择
                routing_params=routing_params,
                comment="发票申请"
            )
            invoice.status = InvoiceStatusEnum.IN_REVIEW
        except Exception as e:
            # 如果启动审批失败，记录日志但不阻止发票创建
            logger.warning(
                f"发票审批流程启动失败: invoice_id={invoice.id}, error={str(e)}"
            )

    db.commit()
    db.refresh(invoice)

    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "contract_code": contract.contract_code,
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
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有草稿状态才能删除
    if invoice.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的发票才能删除")

    db.delete(invoice)
    db.commit()

    from app.schemas.common import ResponseModel
    return ResponseModel(code=200, message="发票已删除")
