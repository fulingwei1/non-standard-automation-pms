# -*- coding: utf-8 -*-
"""
Milestone Status Change Handler.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.project import ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice as InvoiceModel
from app.models.enums import InvoiceStatusEnum

logger = logging.getLogger(__name__)


class MilestoneStatusHandler:
    """处理里程碑状态变更相关的逻辑"""

    @staticmethod
    def handle_milestone_completed(
        db: Session,
        milestone: ProjectMilestone,
        from_status: Optional[str],
        to_status: str,
    ):
        """里程碑完成时触发的逻辑：自动创建发票"""
        if to_status != "COMPLETED":
            return

        logger.info(f"Triggering milestone completion logic for ID: {milestone.id}")

        # 自动触发开票逻辑 (移植自 milestones/workflow.py)
        payment_plans = (
            db.query(ProjectPaymentPlan)
            .filter(
                ProjectPaymentPlan.milestone_id == milestone.id,
                ProjectPaymentPlan.status == "PENDING",
            )
            .all()
        )

        for plan in payment_plans:
            # 检查是否已开票
            if plan.invoice_id:
                continue

            # 获取合同信息
            contract = None
            if plan.contract_id:
                contract = (
                    db.query(Contract).filter(Contract.id == plan.contract_id).first()
                )

            if contract:
                # 自动创建发票
                # 生成发票编码
                today = datetime.now()
                month_str = today.strftime("%y%m%d")
                prefix = f"INV-{month_str}-"
                max_invoice = (
                    db.query(InvoiceModel)
                    .filter(InvoiceModel.invoice_code.like(f"{prefix}%"))
                    .order_by(desc(InvoiceModel.invoice_code))
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

                invoice = InvoiceModel(
                    invoice_code=invoice_code,
                    contract_id=contract.id,
                    project_id=plan.project_id,
                    payment_id=None,  # 暂时不关联payment表
                    invoice_type="NORMAL",
                    amount=plan.planned_amount,
                    tax_rate=Decimal("13"),  # 默认税率13%
                    tax_amount=plan.planned_amount * Decimal("13") / Decimal("100"),
                    total_amount=plan.planned_amount * Decimal("113") / Decimal("100"),
                    status=InvoiceStatusEnum.DRAFT,
                    payment_status="PENDING",
                    issue_date=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    buyer_name=contract.customer.customer_name
                    if contract.customer
                    else None,
                    buyer_tax_no=contract.customer.tax_no
                    if contract.customer
                    else None,
                )
                db.add(invoice)
                db.flush()

                # 更新收款计划
                plan.invoice_id = invoice.id
                plan.invoice_no = invoice_code
                plan.invoice_date = date.today()
                plan.invoice_amount = invoice.total_amount
                plan.status = "INVOICED"

                db.add(plan)
                logger.info(
                    f"Created invoice {invoice_code} for payment plan {plan.id}"
                )


def register_milestone_handlers():
    """注册里程碑相关的状态变更处理器"""
    from app.common.workflow.engine import workflow_engine

    workflow_engine.register(
        model_name="ProjectMilestone",
        to_status="COMPLETED",
        handler=MilestoneStatusHandler.handle_milestone_completed,
    )
