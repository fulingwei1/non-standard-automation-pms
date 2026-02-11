# -*- coding: utf-8 -*-
"""
项目里程碑状态机

状态转换规则：
- PENDING → COMPLETED: 完成里程碑（自动触发开票）
"""

from datetime import date
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.project import ProjectMilestone


class MilestoneStateMachine(StateMachine):
    """项目里程碑状态机"""

    def __init__(self, milestone: ProjectMilestone, db: Session):
        """初始化里程碑状态机"""
        super().__init__(milestone, db, state_field='status')

    @transition(
        from_state="PENDING",
        to_state="COMPLETED",
        required_permission="milestone:update",
        action_type="COMPLETE",
        notify_users=["owner", "project_manager"],
        notification_template="milestone_completed",
    )
    def complete(self, from_state: str, to_state: str, **kwargs):
        """
        完成里程碑

        Args:
            actual_date: 实际完成日期（可选，默认当前日期）
            auto_trigger_invoice: 是否自动触发开票（默认True）
        """
        # 设置实际完成日期
        actual_date = kwargs.get('actual_date')
        if actual_date:
            self.model.actual_date = actual_date
        elif not self.model.actual_date:
            self.model.actual_date = date.today()

        # 执行业务逻辑：完成前检查
        self._ensure_can_complete()

        # 执行业务逻辑：自动触发开票
        auto_trigger_invoice = kwargs.get('auto_trigger_invoice', True)
        if auto_trigger_invoice:
            self._auto_trigger_invoice()

    # ==================== 业务逻辑辅助方法 ====================

    def _ensure_can_complete(self):
        """检查里程碑是否满足完成条件"""
        try:
            import logging
            from app.services.progress_integration_service import ProgressIntegrationService
            from fastapi import HTTPException

            integration_service = ProgressIntegrationService(self.db)
            can_complete, missing_items = integration_service.check_milestone_completion_requirements(
                self.model
            )

            if not can_complete:
                raise HTTPException(
                    status_code=400,
                    detail=f"里程碑不满足完成条件：{', '.join(missing_items)}"
                )
        except ImportError:
            # 如果服务不存在，跳过检查
            import logging
            logging.warning("ProgressIntegrationService 不存在，跳过完成条件检查")
        except Exception as e:
            import logging
            logging.error(f"检查里程碑完成条件失败: {str(e)}")

    def _auto_trigger_invoice(self):
        """自动触发开票（完成里程碑时）"""
        try:
            import logging
            from decimal import Decimal
            from datetime import timedelta
            from app.models.project import ProjectPaymentPlan
            from app.models.sales import Contract, Invoice
            from app.models.enums import InvoiceStatusEnum

            # 查找关联的待开票收款计划
            payment_plans = (
                self.db.query(ProjectPaymentPlan)
                .filter(
                    ProjectPaymentPlan.milestone_id == self.model.id,
                    ProjectPaymentPlan.status == "PENDING",
                )
                .all()
            )

            if not payment_plans:
                logging.info(f"里程碑 {self.model.milestone_code} 没有关联的待开票收款计划")
                return

            # 为每个收款计划创建发票
            for plan in payment_plans:
                if plan.invoice_id:
                    continue  # 已有发票，跳过

                # 获取合同信息
                contract = None
                if plan.contract_id:
                    contract = self.db.query(Contract).filter(Contract.id == plan.contract_id).first()

                if not contract:
                    logging.warning(f"收款计划 {plan.id} 没有关联合同，跳过开票")
                    continue

                # 生成发票编码
                invoice_code = self._generate_invoice_code()

                # 创建发票
                invoice = Invoice(
                    invoice_code=invoice_code,
                    contract_id=contract.id,
                    project_id=plan.project_id,
                    payment_id=None,
                    invoice_type="NORMAL",
                    amount=plan.planned_amount,
                    tax_rate=Decimal("13"),
                    tax_amount=plan.planned_amount * Decimal("13") / Decimal("100"),
                    total_amount=plan.planned_amount * Decimal("113") / Decimal("100"),
                    status=InvoiceStatusEnum.DRAFT,
                    payment_status="PENDING",
                    issue_date=date.today(),
                    due_date=date.today() + timedelta(days=30),
                    buyer_name=contract.customer.customer_name if contract.customer else None,
                    buyer_tax_no=contract.customer.tax_no if contract.customer else None,
                )
                self.db.add(invoice)
                self.db.flush()

                # 更新收款计划
                plan.invoice_id = invoice.id
                plan.invoice_no = invoice_code
                plan.invoice_date = date.today()
                plan.invoice_amount = invoice.total_amount
                plan.status = "INVOICED"
                self.db.add(plan)

                logging.info(
                    f"里程碑 {self.model.milestone_code} 自动触发开票: {invoice_code}"
                )

        except Exception as e:
            import logging
            # 开票失败不影响里程碑完成
            logging.warning(f"自动触发开票失败：{str(e)}")

    def _generate_invoice_code(self) -> str:
        """生成发票编码"""
        from datetime import datetime
        from sqlalchemy import desc
        from app.models.sales import Invoice

        today = datetime.now()
        prefix = f"INV-{today.strftime('%y%m%d')}-"

        max_invoice_query = apply_like_filter(
            self.db.query(Invoice),
            Invoice,
            f"{prefix}%",
            "invoice_code",
            use_ilike=False,
        )
        max_invoice = max_invoice_query.order_by(desc(Invoice.invoice_code)).first()

        if max_invoice:
            try:
                seq = int(max_invoice.invoice_code.split("-")[-1]) + 1
            except (ValueError, TypeError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"
