# -*- coding: utf-8 -*-
"""
发票管理 API endpoints - 旧版兼容接口
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import InvoiceResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/invoices_old", response_model=PaginatedResponse[InvoiceResponse])
def read_invoices_old(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票列表（旧版）
    Issue 7.1: 已集成数据权限过滤（财务和销售总监可以看到所有发票）

    注意：此接口保留用于向后兼容，建议使用 /invoices 接口
    """
    query = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    )

    # Issue 7.1: 应用财务数据权限过滤（财务和销售总监可以看到所有发票）
    query = security.filter_sales_finance_data_by_scope(query, current_user, db, Invoice, 'owner_id')

    query = apply_keyword_filter(query, Invoice, keyword, "invoice_code")

    if status:
        query = query.filter(Invoice.status == status)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    total = query.count()
    invoices = query.order_by(desc(Invoice.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    invoice_responses = []
    for invoice in invoices:
        contract = invoice.contract
        project = invoice.project
        customer = contract.customer if contract else None
        invoice_dict = {
            **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
            "contract_code": contract.contract_code if contract else None,
            "project_code": project.project_code if project else None,
            "project_name": project.project_name if project else None,
            "customer_name": customer.customer_name if customer else None,
        }
        invoice_responses.append(InvoiceResponse(**invoice_dict))

    return PaginatedResponse(
        items=invoice_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )
