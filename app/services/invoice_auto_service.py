# -*- coding: utf-8 -*-
"""
发票自动服务
Issue 7.4: 里程碑验收自动触发开票
实现验收完成后自动创建发票申请的功能
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.business_support import InvoiceRequest
from app.models.notification import Notification
from app.models.project import Project, ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract, Invoice
from app.models.user import User

logger = logging.getLogger(__name__)


class InvoiceAutoService:
    """发票自动服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_and_create_invoice_request(
        self,
        acceptance_order_id: int,
        auto_create: bool = False,
    ) -> Dict[str, Any]:
        """
        检查验收完成后的收款计划，自动创建发票申请

        Args:
            acceptance_order_id: 验收单ID
            auto_create: 是否自动创建发票（True）还是只创建发票申请（False，默认）

        Returns:
            处理结果字典
        """
        order = self.db.query(AcceptanceOrder).filter(
            AcceptanceOrder.id == acceptance_order_id
        ).first()

        if not order:
            return {
                "success": False,
                "message": "验收单不存在",
                "invoice_requests": []
            }

        # 只处理验收通过的订单
        if order.overall_result != "PASSED" or order.status != "COMPLETED":
            return {
                "success": True,
                "message": "验收未通过或未完成，无需开票",
                "invoice_requests": []
            }

        # 查找关联的里程碑
        # 根据验收类型匹配里程碑类型
        milestone_type_map = {
            "FAT": "FAT_PASS",
            "SAT": "SAT_PASS",
            "FINAL": "FINAL_ACCEPTANCE",
        }
        milestone_type = milestone_type_map.get(order.acceptance_type)

        if not milestone_type:
            return {
                "success": True,
                "message": "验收类型不支持自动开票",
                "invoice_requests": []
            }

        # 查找关联的里程碑
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == order.project_id,
            ProjectMilestone.milestone_type == milestone_type,
            ProjectMilestone.status == "COMPLETED"
        ).all()

        if not milestones:
            return {
                "success": True,
                "message": "未找到关联的里程碑",
                "invoice_requests": []
            }

        created_requests = []

        for milestone in milestones:
            # 查找关联的收款计划
            payment_plans = self.db.query(ProjectPaymentPlan).filter(
                ProjectPaymentPlan.milestone_id == milestone.id,
                ProjectPaymentPlan.status.in_(["PENDING", "INVOICED"]),
                ProjectPaymentPlan.payment_type == "ACCEPTANCE"
            ).all()

            for plan in payment_plans:
                # 检查是否已开票
                if plan.invoice_id:
                    continue

                # 检查收款计划是否已到期
                if plan.planned_date and plan.planned_date > date.today():
                    # 如果配置允许提前开票，可以继续；否则跳过
                    # 这里简化处理，如果计划日期未到，跳过
                    continue

                # 检查交付物是否齐全（简化处理：检查合同交付物）
                if not self._check_deliverables_complete(plan):
                    logger.warning(f"收款计划 {plan.id} 的交付物不齐全，跳过自动开票")
                    continue

                # 检查验收问题：存在未闭环阻塞问题时阻止开票
                if not self._check_acceptance_issues_resolved(order):
                    logger.warning(
                        f"验收单 {order.id} 存在未闭环的阻塞问题，无法开票。"
                        f"收款计划 {plan.id} 跳过自动开票"
                    )
                    continue

                # 创建发票申请或直接创建发票
                if auto_create:
                    result = self._create_invoice_directly(plan, order, milestone)
                else:
                    result = self._create_invoice_request(plan, order, milestone)

                if result.get("success"):
                    created_requests.append(result)

        if created_requests:
            self.db.commit()

            # 发送通知
            self._send_invoice_notifications(order, created_requests, auto_create)

            # 记录日志
            self._log_auto_invoice(order, created_requests, auto_create)

        return {
            "success": True,
            "message": f"已创建 {len(created_requests)} 个发票{'申请' if not auto_create else ''}",
            "invoice_requests": created_requests
        }

    def _check_deliverables_complete(self, plan: ProjectPaymentPlan) -> bool:
        """
        检查交付物是否齐全

        简化实现：检查合同交付物是否都已交付
        """
        if not plan.contract_id:
            return True  # 如果没有合同，默认交付物齐全

        contract = self.db.query(Contract).filter(
            Contract.id == plan.contract_id
        ).first()

        if not contract:
            return True

        # 检查合同交付物（这里简化处理，实际应该检查所有必需交付物）
        # 如果有交付物表，可以检查交付状态
        # 这里默认返回 True，表示交付物齐全
        return True

    def _check_acceptance_issues_resolved(self, order: AcceptanceOrder) -> bool:
        """
        检查验收问题是否已全部解决

        规则：存在未闭环的阻塞问题时，不能开票

        Args:
            order: 验收单对象

        Returns:
            bool: True表示所有阻塞问题已解决，可以开票；False表示存在未解决的阻塞问题
        """
        from app.models.acceptance import AcceptanceIssue

        # 查找所有阻塞问题
        blocking_issues = self.db.query(AcceptanceIssue).filter(
            AcceptanceIssue.order_id == order.id,
            AcceptanceIssue.is_blocking == True,
            AcceptanceIssue.status.in_(["OPEN", "PROCESSING", "RESOLVED", "DEFERRED"])
        ).all()

        if not blocking_issues:
            return True  # 没有阻塞问题，可以开票

        # 检查是否有未闭环的阻塞问题
        for issue in blocking_issues:
            if issue.status == "RESOLVED":
                # 已解决的问题需要验证通过才能算闭环
                if issue.verified_result != "VERIFIED":
                    return False  # 存在已解决但未验证的问题
            else:
                # OPEN, PROCESSING, DEFERRED 状态的问题都算未闭环
                return False

        return True  # 所有阻塞问题都已解决并验证通过

    def _create_invoice_request(
        self,
        plan: ProjectPaymentPlan,
        order: AcceptanceOrder,
        milestone: ProjectMilestone,
    ) -> Dict[str, Any]:
        """
        创建发票申请

        Args:
            plan: 收款计划
            order: 验收单
            milestone: 里程碑

        Returns:
            创建结果字典
        """
        # 检查是否已有发票申请
        existing_request = self.db.query(InvoiceRequest).filter(
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
            contract = self.db.query(Contract).filter(
                Contract.id == plan.contract_id
            ).first()

        if not contract:
            return {
                "success": False,
                "message": "收款计划未关联合同"
            }

        # 生成申请编号
        from sqlalchemy import desc
        today = datetime.now()
        month_str = today.strftime("%y%m")
        prefix = f"IR{month_str}-"
        max_request = (
            self.db.query(InvoiceRequest)
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

        self.db.add(invoice_request)
        self.db.flush()

        return {
            "success": True,
            "message": "发票申请已创建",
            "request_id": invoice_request.id,
            "request_no": request_no,
            "amount": float(total_amount)
        }

    def _create_invoice_directly(
        self,
        plan: ProjectPaymentPlan,
        order: AcceptanceOrder,
        milestone: ProjectMilestone,
    ) -> Dict[str, Any]:
        """
        直接创建发票（自动开票模式）

        Args:
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
            contract = self.db.query(Contract).filter(
                Contract.id == plan.contract_id
            ).first()

        if not contract:
            return {
                "success": False,
                "message": "收款计划未关联合同"
            }

        # 生成发票编码
        from sqlalchemy import desc

        from app.models.sales import Invoice as InvoiceModel
        today = datetime.now()
        month_str = today.strftime("%y%m")
        prefix = f"INV{month_str}-"
        max_invoice = (
            self.db.query(InvoiceModel)
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

        self.db.add(invoice)
        self.db.flush()

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

    def _send_invoice_notifications(
        self,
        order: AcceptanceOrder,
        created_items: List[Dict[str, Any]],
        auto_create: bool,
    ) -> None:
        """
        发送开票通知给：财务、销售

        Args:
            order: 验收单
            created_items: 创建的发票申请或发票列表
            auto_create: 是否自动创建发票
        """
        try:
            # 获取项目信息
            project = order.project
            if not project:
                return

            # 获取合同信息
            contract = None
            if project.contract_id:
                contract = self.db.query(Contract).filter(
                    Contract.id == project.contract_id
                ).first()

            # 确定通知对象
            recipient_ids = set()

            # 1. 财务
            from app.models.user import Role, UserRole
            finance_role_ids = self.db.query(Role.id).filter(
                Role.role_code.in_(["FINANCE", "财务", "FINANCE_MANAGER", "财务经理"])
            ).all()
            finance_role_ids = [r[0] for r in finance_role_ids]
            if finance_role_ids:
                finance_user_ids = self.db.query(UserRole.user_id).filter(
                    UserRole.role_id.in_(finance_role_ids)
                ).all()
                for uid in finance_user_ids:
                    recipient_ids.add(uid[0])

            # 2. 销售（合同负责人）
            if contract and contract.owner_id:
                recipient_ids.add(contract.owner_id)

            # 构建通知内容
            item_type = "发票" if auto_create else "发票申请"
            item_list = [f"{item.get('invoice_code') or item.get('request_no')}（金额：¥{item.get('amount', 0):,.2f}）" for item in created_items]

            notification_content = (
                f"验收通过自动触发开票：\n"
                f"项目：{project.project_code} - {project.project_name}\n"
                f"验收单：{order.order_no}\n"
                f"已创建 {len(created_items)} 个{item_type}：\n"
                f"{chr(10).join(item_list)}\n"
                f"请及时处理。"
            )

            # 创建通知记录
            for user_id in recipient_ids:
                notification = Notification(
                    user_id=user_id,
                    title=f"验收通过自动触发{item_type}",
                    content=notification_content,
                    notification_type="INVOICE_AUTO",
                    source_type="acceptance",
                    source_id=order.id,
                )
                self.db.add(notification)

            self.db.commit()
            logger.info(f"已发送开票通知给 {len(recipient_ids)} 个用户")

        except Exception as e:
            logger.error(f"发送开票通知失败: {e}", exc_info=True)

    def _log_auto_invoice(
        self,
        order: AcceptanceOrder,
        created_items: List[Dict[str, Any]],
        auto_create: bool,
    ) -> None:
        """
        记录自动开票日志

        Args:
            order: 验收单
            created_items: 创建的发票申请或发票列表
            auto_create: 是否自动创建发票
        """
        try:
            log_entry = {
                "acceptance_order_id": order.id,
                "acceptance_order_no": order.order_no,
                "project_id": order.project_id,
                "auto_create": auto_create,
                "created_items": created_items,
                "created_at": datetime.now().isoformat()
            }

            # 将日志记录到验收单的备注中（简化实现）
            import json
            if order.conditions:
                try:
                    log_list = json.loads(order.conditions)
                    if not isinstance(log_list, list):
                        log_list = []
                except (json.JSONDecodeError, TypeError):
                    log_list = []
            else:
                log_list = []

            log_list.append(log_entry)
            order.conditions = json.dumps(log_list, ensure_ascii=False)

            logger.info(f"验收单 {order.order_no} 自动开票日志已记录")

        except Exception as e:
            logger.error(f"记录自动开票日志失败: {e}", exc_info=True)
