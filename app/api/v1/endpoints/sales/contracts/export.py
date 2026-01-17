# -*- coding: utf-8 -*-
"""
合同导出 API endpoints
包括：Excel导出、PDF导出
"""

import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectPaymentPlan
from app.models.sales import Contract, ContractDeliverable, Opportunity
from app.models.user import User

router = APIRouter()


@router.get("/contracts/export")
def export_contracts(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.3: 导出合同列表（Excel）
    """
    from app.services.excel_export_service import (
        ExcelExportService,
        create_excel_response,
    )

    query = db.query(Contract)
    if keyword:
        query = query.filter(or_(Contract.contract_code.contains(keyword), Contract.contract_name.contains(keyword), Contract.opportunity.has(Opportunity.opp_name.contains(keyword))))
    if status:
        query = query.filter(Contract.status == status)
    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if owner_id:
        query = query.filter(Contract.owner_id == owner_id)

    contracts = query.order_by(Contract.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "contract_code", "label": "合同编码", "width": 15},
        {"key": "contract_name", "label": "合同名称", "width": 30},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "contract_amount", "label": "合同金额", "width": 15, "format": export_service.format_currency},
        {"key": "signed_date", "label": "签订日期", "width": 12, "format": export_service.format_date},
        {"key": "delivery_deadline", "label": "交期", "width": 12, "format": export_service.format_date},
        {"key": "status", "label": "状态", "width": 12},
        {"key": "project_code", "label": "项目编码", "width": 15},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = [{
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name or '',
        "customer_name": contract.customer.customer_name if contract.customer else '',
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
        "signed_date": contract.signed_date,
        "delivery_deadline": contract.delivery_deadline,
        "status": contract.status,
        "project_code": contract.project.project_code if contract.project else '',
        "owner_name": contract.owner.real_name if contract.owner else '',
        "created_at": contract.created_at,
    } for contract in contracts]

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="合同列表", title="合同列表")
    filename = f"合同列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/contracts/{contract_id}/pdf")
def export_contract_pdf(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出合同 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()

    # 准备数据
    contract_data = {
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name or '',
        "customer_name": contract.customer.customer_name if contract.customer else '',
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
        "signed_date": contract.signed_date,
        "delivery_deadline": contract.delivery_deadline,
        "status": contract.status,
    }

    deliverable_list = [{
        "deliverable_name": d.deliverable_name or '',
        "quantity": float(d.quantity) if d.quantity else 0,
        "unit": d.unit or '',
        "remark": d.remark or '',
    } for d in deliverables]

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_contract_to_pdf(contract_data, deliverable_list)

    filename = f"合同_{contract.contract_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
