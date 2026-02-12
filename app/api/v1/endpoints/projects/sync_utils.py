# -*- coding: utf-8 -*-
"""
项目模块 - 同步工具函数

包含ERP同步、开票申请同步等
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business_support import InvoiceRequest
from app.models.project import Project, ProjectPaymentPlan


def _sync_invoice_request_receipt_status(db: Session, plan: ProjectPaymentPlan) -> None:
    """根据收款计划实收金额同步开票申请回款状态"""
    invoice_requests = db.query(InvoiceRequest).filter(
        InvoiceRequest.payment_plan_id == plan.id,
        InvoiceRequest.status == "APPROVED"
    ).all()
    if not invoice_requests:
        return

    planned_amount = plan.planned_amount or Decimal("0")
    actual_amount = plan.actual_amount or Decimal("0")

    if planned_amount and actual_amount >= planned_amount:
        receipt_status = "PAID"
    elif actual_amount > 0:
        receipt_status = "PARTIAL"
    else:
        receipt_status = "UNPAID"

    for invoice_request in invoice_requests:
        if invoice_request.receipt_status != receipt_status:
            invoice_request.receipt_status = receipt_status
            invoice_request.receipt_updated_at = datetime.now(timezone.utc)
            db.add(invoice_request)


def _sync_to_erp_system(project: Project, erp_order_no: Optional[str] = None) -> Dict[str, Any]:
    """
    同步项目数据到ERP系统

    这是一个可扩展的ERP接口框架。实际使用时需要根据具体的ERP系统
    （如SAP、Oracle、金蝶、用友等）实现相应的API调用。

    Args:
        project: 项目对象
        erp_order_no: ERP订单号（可选）

    Returns:
        dict: 同步结果 {'success': bool, 'erp_order_no': str, 'error': str}
    """
    # 检查是否配置了ERP接口
    erp_api_url = getattr(settings, 'ERP_API_URL', None)
    getattr(settings, 'ERP_API_KEY', None)

    # 如果没有配置ERP接口，返回模拟成功
    if not erp_api_url:
        # 生成模拟ERP订单号
        generated_order_no = erp_order_no or f"ERP-{project.project_code}"
        return {
            'success': True,
            'erp_order_no': generated_order_no,
            'message': 'ERP接口未配置，使用模拟同步'
        }

    # 实际ERP集成逻辑（待实现）
    return {
        'success': True,
        'erp_order_no': erp_order_no or f"ERP-{project.project_code}",
        'message': 'ERP同步功能框架已就绪，请配置实际ERP接口'
    }
