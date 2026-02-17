# -*- coding: utf-8 -*-
"""
发票导出 API endpoints
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Invoice
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/invoices/export")
def export_invoices(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.4: 导出发票列表（Excel）
    """
    from app.services.excel_export_service import (
        ExcelExportService,
        create_excel_response,
    )

    query = db.query(Invoice)
    if keyword:
        query = query.filter(or_(
            Invoice.invoice_code.contains(keyword),
            Invoice.contract.has(Contract.contract_code.contains(keyword))
        ))
    if status:
        query = query.filter(Invoice.status == status)
    if customer_id:
        query = query.filter(Invoice.contract.has(Contract.customer_id == customer_id))

    invoices = query.order_by(Invoice.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "invoice_code", "label": "发票编码", "width": 15},
        {"key": "contract_code", "label": "合同编码", "width": 15},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "invoice_type", "label": "发票类型", "width": 12},
        {"key": "amount", "label": "发票金额", "width": 15, "format": export_service.format_currency},
        {"key": "paid_amount", "label": "已收金额", "width": 15, "format": export_service.format_currency},
        {"key": "unpaid_amount", "label": "未收金额", "width": 15, "format": export_service.format_currency},
        {"key": "issue_date", "label": "开票日期", "width": 12, "format": export_service.format_date},
        {"key": "due_date", "label": "到期日期", "width": 12, "format": export_service.format_date},
        {"key": "payment_status", "label": "收款状态", "width": 12},
        {"key": "status", "label": "发票状态", "width": 12},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = []
    for invoice in invoices:
        total_amount = float(invoice.total_amount or invoice.amount or 0)
        paid_amount = float(invoice.paid_amount or 0)
        unpaid_amount = total_amount - paid_amount
        data.append({
            "invoice_code": invoice.invoice_code,
            "contract_code": invoice.contract.contract_code if invoice.contract else '',
            "customer_name": invoice.contract.customer.customer_name if invoice.contract and invoice.contract.customer else '',
            "invoice_type": invoice.invoice_type or '',
            "amount": total_amount,
            "paid_amount": paid_amount,
            "unpaid_amount": unpaid_amount,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "payment_status": invoice.payment_status or '',
            "status": invoice.status,
            "created_at": invoice.created_at,
        })

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="发票列表", title="发票列表")
    filename = f"发票列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/invoices/{invoice_id}/pdf")
def export_invoice_pdf(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出发票 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response
from app.utils.db_helpers import get_or_404

    invoice = get_or_404(db, Invoice, invoice_id, detail="发票不存在")

    # 准备数据
    total_amount = float(invoice.total_amount or invoice.amount or 0)
    paid_amount = float(invoice.paid_amount or 0)

    invoice_data = {
        "invoice_code": invoice.invoice_code,
        "contract_code": invoice.contract.contract_code if invoice.contract else '',
        "customer_name": invoice.contract.customer.customer_name if invoice.contract and invoice.contract.customer else '',
        "invoice_type": invoice.invoice_type or '',
        "total_amount": total_amount,
        "amount": total_amount,
        "paid_amount": paid_amount,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date,
        "payment_status": invoice.payment_status or '',
        "status": invoice.status,
    }

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_invoice_to_pdf(invoice_data)

    filename = f"发票_{invoice.invoice_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
