# -*- coding: utf-8 -*-
"""
发票自动服务 - 创建功能
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import desc

from app.models.acceptance import AcceptanceOrder
from app.models.business_support import InvoiceRequest
from app.models.project import ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice

logger = logging.getLogger(__name__)


def create_invoice_request(
    service: "InvoiceAutoService",
    plan: ProjectPaymentPlan,
    order: AcceptanceOrder,
    milestone: ProjectMilestone,
) -> Dict[str, Any]:
    """
    创建发票申请

    Args:
        service: InvoiceAutoService实例
        plan: 收款计划
        order: 验收单
        milestone: 里程碑

    Returns:
        创建结果字典
    """
    # 检查是否已有发票申请
    existing_request = service.db.query(InvoiceRequest).filter(
        InvoiceRequest.payment_plan_id == plan.id,
        InvoiceRequest.status.in_(["PENDING", "APPROVED"])
    ).first()

    if existing_request:
        return {
            "success": False,
            "message": "发票申请已存在",
            "request_id": existing_request.id
        }

    # 获取合同信息
    contract = None
    if plan.contract_id:
        contract = service.db.query(Contract).filter(
            Contract.id == plan.contract_id
        ).first()

    if not contract:
        return {
            "success": False,
            "message": "收款计划未关联合同"
        }

    # 生成申请编号
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"IR{month_str}-"
    max_request = (
        service.db.query(InvoiceRequest)
        .filter(InvoiceRequest.request_no.like(f"{prefix}%"))
        .order_by(desc(InvoiceRequest.request_no))
        .first()
    )
    if max_request:
        try:
            seq = int(max_request.request_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1
    request_no = f"{prefix}{seq:03d}"

    # 计算金额
    tax_rate = Decimal("13")  # 默认税率13%
    amount = plan.planned_amount
    tax_amount = amount * tax_rate / Decimal("100")
    total_amount = amount + tax_amount

    # 创建发票申请
    invoice_request = InvoiceRequest(
        request_no=request_no,
        contract_id=contract.id,
        project_id=plan.project_id,
        project_name=plan.project.project_name if plan.project else None,
        customer_id=contract.customer_id,
        customer_name=contract.customer.customer_name if contract.customer else None,
        payment_plan_id=plan.id,
        invoice_type="NORMAL",
        invoice_title=contract.customer.customer_name if contract.customer else None,
        tax_rate=tax_rate,
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency="CNY",
        expected_issue_date=date.today(),
        expected_payment_date=plan.planned_date or date.today() + timedelta(days=30),
        reason=f"验收通过自动触发：{milestone.milestone_name}（验收单：{order.order_no}）",
        status="PENDING",
        requested_by=order.created_by or 1,  # 使用验收单创建人
        requested_by_name=None,  # 可以从用户表获取
    )

    service.db.add(invoice_request)
    service.db.flush()

    return {
        "success": True,
        "message": "发票申请已创建",
        "request_id": invoice_request.id,
        "request_no": request_no,
        "amount": float(total_amount)
    }


def create_invoice_directly(
    service: "InvoiceAutoService",
    plan: ProjectPaymentPlan,
    order: AcceptanceOrder,
    milestone: ProjectMilestone,
) -> Dict[str, Any]:
    """
    直接创建发票（自动开票模式）

    Args:
        service: InvoiceAutoService实例
        plan: 收款计划
        order: 验收单
        milestone: 里程碑

    Returns:
        创建结果字典
    """
    # 检查是否已开票
    if plan.invoice_id:
        return {
            "success": False,
            "message": "已开票"
        }

    # 获取合同信息
    contract = None
    if plan.contract_id:
        contract = service.db.query(Contract).filter(
            Contract.id == plan.contract_id
        ).first()

    if not contract:
        return {
            "success": False,
            "message": "收款计划未关联合同"
        }

    # 生成发票编码
    today = datetime.now()
    month_str = today.strftime("%y%m")
    prefix = f"INV{month_str}-"
    max_invoice = (
        service.db.query(Invoice)
        .filter(Invoice.invoice_code.like(f"{prefix}%"))
        .order_by(desc(Invoice.invoice_code))
        .first()
    )
    if max_invoice:
        try:
            seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1
    invoice_code = f"{prefix}{seq:03d}"

    # 计算金额
    tax_rate = Decimal("13")
    amount = plan.planned_amount
    tax_amount = amount * tax_rate / Decimal("100")
    total_amount = amount + tax_amount

    # 创建发票
    invoice = Invoice(
        invoice_code=invoice_code,
        contract_id=contract.id,
        project_id=plan.project_id,
        invoice_type="NORMAL",
        amount=amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status="DRAFT",
        payment_status="PENDING",
        issue_date=date.today(),
        due_date=plan.planned_date or date.today() + timedelta(days=30),
        buyer_name=contract.customer.customer_name if contract.customer else None,
        buyer_tax_no=contract.customer.tax_no if contract.customer else None,
        owner_id=contract.owner_id,
    )

    service.db.add(invoice)
    service.db.flush()

    # 更新收款计划
    plan.invoice_id = invoice.id
    plan.invoice_no = invoice_code
    plan.invoice_date = date.today()
    plan.invoice_amount = total_amount
    plan.status = "INVOICED"

    return {
        "success": True,
        "message": "发票已创建",
        "invoice_id": invoice.id,
        "invoice_code": invoice_code,
        "amount": float(total_amount)
    }
