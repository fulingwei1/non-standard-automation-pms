# -*- coding: utf-8 -*-
"""
合同导出 API endpoints
包括：Excel导出、PDF导出
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, ContractDeliverable, Opportunity
from app.models.user import User
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/contracts/expiring")
def get_expiring_contracts(
    *,
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=3650, description="未来多少天内到期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取即将到期合同（兼容 /sales/contracts/expiring）。"""
    threshold = datetime.now().date() + timedelta(days=days)

    contracts = (
        db.query(Contract)
        .filter(Contract.expiry_date.isnot(None))
        .filter(Contract.expiry_date <= threshold)
        .order_by(Contract.expiry_date.asc())
        .all()
    )

    return {
        "items": [
            {
                "id": c.id,
                "contract_code": c.contract_code,
                "contract_name": c.contract_name,
                "expiry_date": c.expiry_date,
                "status": c.status,
            }
            for c in contracts
        ],
        "total": len(contracts),
        "days": days,
    }


@router.get("/contracts/statistics")
def get_contract_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取合同统计（兼容 /sales/contracts/statistics）。"""
    total_contracts = db.query(func.count(Contract.id)).scalar() or 0
    total_amount = db.query(func.coalesce(func.sum(Contract.total_amount), 0)).scalar() or 0

    status_rows = (
        db.query(Contract.status, func.count(Contract.id))
        .group_by(Contract.status)
        .all()
    )

    status_breakdown = {status or "unknown": count for status, count in status_rows}

    return {
        "total_contracts": int(total_contracts),
        "total_amount": float(total_amount),
        "status_breakdown": status_breakdown,
    }


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
        query = query.filter(
            or_(
                Contract.contract_code.contains(keyword),
                Contract.contract_name.contains(keyword),
                Contract.opportunity.has(Opportunity.opp_name.contains(keyword)),
            )
        )
    if status:
        query = query.filter(Contract.status == status)
    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if owner_id:
        query = query.filter(Contract.sales_owner_id == owner_id)

    contracts = query.order_by(Contract.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "contract_code", "label": "合同编码", "width": 15},
        {"key": "contract_name", "label": "合同名称", "width": 30},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {
            "key": "contract_amount",
            "label": "合同金额",
            "width": 15,
            "format": export_service.format_currency,
        },
        {
            "key": "signed_date",
            "label": "签订日期",
            "width": 12,
            "format": export_service.format_date,
        },
        {
            "key": "delivery_deadline",
            "label": "交期",
            "width": 12,
            "format": export_service.format_date,
        },
        {"key": "status", "label": "状态", "width": 12},
        {"key": "project_code", "label": "项目编码", "width": 15},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {
            "key": "created_at",
            "label": "创建时间",
            "width": 18,
            "format": export_service.format_date,
        },
    ]

    data = [
        {
            "contract_code": contract.contract_code,
            "contract_name": contract.contract_name or "",
            "customer_name": contract.customer.customer_name if contract.customer else "",
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "signed_date": contract.signing_date,
            "delivery_deadline": contract.delivery_deadline,
            "status": contract.status,
            "project_code": contract.project.project_code if contract.project else "",
            "owner_name": contract.sales_owner.real_name if contract.sales_owner else "",
            "created_at": contract.created_at,
        }
        for contract in contracts
    ]

    excel_data = export_service.export_to_excel(
        data=data, columns=columns, sheet_name="合同列表", title="合同列表"
    )
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

    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    )

    # 准备数据
    contract_data = {
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name or "",
        "customer_name": contract.customer.customer_name if contract.customer else "",
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
        "signed_date": contract.signing_date,
        "delivery_deadline": contract.delivery_deadline,
        "status": contract.status,
    }

    deliverable_list = [
        {
            "deliverable_name": d.deliverable_name or "",
            "quantity": float(d.quantity) if d.quantity else 0,
            "unit": d.unit or "",
            "remark": d.remark or "",
        }
        for d in deliverables
    ]

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_contract_to_pdf(contract_data, deliverable_list)

    filename = f"合同_{contract.contract_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
