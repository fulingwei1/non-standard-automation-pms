# -*- coding: utf-8 -*-
"""
发票审批适配器

将发票模块接入统一审批系统
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.invoices import Invoice

from .base import ApprovalAdapter


class InvoiceApprovalAdapter(ApprovalAdapter):
    """
    发票审批适配器

    支持的条件字段:
    - entity.amount: 发票金额
    - entity.total_amount: 含税总额
    - entity.invoice_type: 发票类型
    """

    entity_type = "INVOICE"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Invoice]:
        """获取发票实体"""
        return self.db.query(Invoice).filter(Invoice.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取发票数据用于条件路由

        Returns:
            包含发票关键数据的字典
        """
        invoice = self.get_entity(entity_id)
        if not invoice:
            return {}

        return {
            "invoice_code": invoice.invoice_code,
            "status": invoice.status,
            "invoice_type": invoice.invoice_type,
            "amount": float(invoice.amount) if invoice.amount else 0,
            "tax_rate": float(invoice.tax_rate) if invoice.tax_rate else 0,
            "tax_amount": float(invoice.tax_amount) if invoice.tax_amount else 0,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "contract_id": invoice.contract_id,
            "contract_code": invoice.contract.contract_code
            if invoice.contract
            else None,
            "project_id": invoice.project_id,
            "buyer_name": invoice.buyer_name,
            "buyer_tax_no": invoice.buyer_tax_no,
            "issue_date": invoice.issue_date.isoformat()
            if invoice.issue_date
            else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """提交审批时的回调"""
        invoice = self.get_entity(entity_id)
        if invoice:
            invoice.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批通过时的回调"""
        invoice = self.get_entity(entity_id)
        if invoice:
            invoice.status = "APPROVED"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批驳回时的回调"""
        invoice = self.get_entity(entity_id)
        if invoice:
            invoice.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        invoice = self.get_entity(entity_id)
        if invoice:
            invoice.status = "DRAFT"
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        invoice = self.get_entity(entity_id)
        if invoice:
            buyer = invoice.buyer_name or "未知客户"
            return f"发票审批 - {invoice.invoice_code} ({buyer})"
        return f"发票审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("buyer_name"):
            parts.append(f"购买方: {data['buyer_name']}")
        if data.get("total_amount"):
            parts.append(f"含税金额: ¥{data['total_amount']:,.2f}")
        if data.get("invoice_type"):
            parts.append(f"类型: {data['invoice_type']}")
        if data.get("contract_code"):
            parts.append(f"合同: {data['contract_code']}")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        invoice = self.get_entity(entity_id)
        if not invoice:
            return False, "发票不存在"

        if invoice.status not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({invoice.status})不允许提交审批"

        if not invoice.amount or invoice.amount <= 0:
            return False, "发票金额必须大于0"

        if not invoice.buyer_name:
            return False, "请填写购买方名称"

        return True, ""

    # ========== 高级方法：使用 WorkflowEngine ========== #

    def submit_for_approval(
        self,
        invoice,
        initiator_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        urgency: str = "NORMAL",
        cc_user_ids: Optional[List[int]] = None,
    ) -> ApprovalInstance:
        """
        提交发票审批到统一审批引擎

        Args:
            invoice: 发票实例
            initiator_id: 发起人ID
            title: 审批标题
            summary: 审批摘要
            urgency: 紧急程度
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的ApprovalInstance
        """
        # 检查是否已经提交
        if invoice.approval_instance_id:
            logger.warning(f"发票 {invoice.invoice_code} 已经提交审批")
            return (
                self.db.query(ApprovalInstance)
                .filter(ApprovalInstance.id == invoice.approval_instance_id)
                .first()
            )

        # 构建表单数据
        form_data = {
            "invoice_id": invoice.id,
            "invoice_code": invoice.invoice_code,
            "invoice_type": invoice.invoice_type,
            "amount": float(invoice.amount) if invoice.amount else 0,
            "tax_rate": float(invoice.tax_rate) if invoice.tax_rate else 0,
            "tax_amount": float(invoice.tax_amount) if invoice.tax_amount else 0,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "contract_id": invoice.contract_id,
            "contract_code": invoice.contract.contract_code
            if invoice.contract
            else None,
            "project_id": invoice.project_id,
            "issue_date": invoice.issue_date.isoformat()
            if invoice.issue_date
            else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "buyer_name": invoice.buyer_name,
            "buyer_tax_no": invoice.buyer_tax_no,
        }

        # 创建审批实例
        approval_data = ApprovalInstanceCreate(
            template_code="SALES_INVOICE",
            entity_type="INVOICE",
            entity_id=invoice.id,
            form_data=form_data,
            title=title or f"发票审批 - {invoice.invoice_code}",
            summary=summary or f"发票审批：{invoice.invoice_code}",
            urgency=urgency,
            cc_user_ids=cc_user_ids,
        )

        # 使用统一引擎创建实例
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        workflow_engine = WorkflowEngine(self.db)

        instance = workflow_engine.create_instance(
            flow_code="SALES_INVOICE",
            business_type="SALES_INVOICE",
            business_id=invoice.id,
            business_title=invoice.invoice_code,
            submitted_by=initiator_id,
            config={"invoice": form_data},
        )

        # 更新发票，关联审批实例
        invoice.approval_instance_id = instance.id
        invoice.approval_status = instance.status
        self.db.add(invoice)
        self.db.commit()

        logger.info(f"发票 {invoice.invoice_code} 已提交审批，实例ID: {instance.id}")

        return instance

    def create_invoice_approval(
        self,
        instance: ApprovalInstance,
        task: ApprovalTask,
    ) -> Optional[InvoiceApproval]:
        """创建发票审批记录"""
        from app.models.sales.invoices import InvoiceApproval

        # 检查是否已存在
        existing = (
            self.db.query(InvoiceApproval)
            .filter(
                InvoiceApproval.invoice_id == instance.entity_id,
                InvoiceApproval.approval_level == task.node_order,
            )
            .first()
        )

        if existing:
            return existing

        # 获取审批人
        approver = (
            self.db.query(User).filter(User.id == task.assignee_id).first()
            if task.assignee_id
            else None
        )

        # 计算到期时间
        due_date = task.due_at or (datetime.now() + timedelta(hours=48))

        # 创建新记录
        approval = InvoiceApproval(
            invoice_id=instance.entity_id,
            approval_level=task.node_order,
            approval_role=task.node_name or "",
            approver_id=task.assignee_id,
            approver_name=approver.real_name if approver else "",
            approval_result=None,  # 待审批
            status="PENDING",
            due_date=due_date,
            is_overdue=False,
        )

        self.db.add(approval)
        return approval

    def update_invoice_approval_from_action(
        self,
        task: ApprovalTask,
        action: str,
        comment: Optional[str] = None,
    ) -> Optional[InvoiceApproval]:
        """更新发票审批记录"""
        approval_level = task.node_order
        approval = (
            self.db.query(invoiceApproval)
            .filter(
                InvoiceApproval.invoice_id == instance.entity_id,
                InvoiceApproval.approval_level == approval_level,
            )
            .first()
        )

        if not approval:
            logger.warning(
                f"未找到发票审批记录: entity_id={task.instance.entity_id}, level={approval_level}"
            )
            return None

        # 更新审批结果
        if action == "APPROVE":
            approval.approval_result = "APPROVED"
            approval.approval_opinion = comment
            approval.status = "APPROVED"
            approval.approved_at = datetime.now()
        elif action == "REJECT":
            approval.approval_result = "REJECTED"
            approval.approval_opinion = comment
            approval.status = "REJECTED"
            approval.approved_at = datetime.now()

        self.db.add(approval)
        self.db.commit()

        logger.info(
            f"发票审批记录已更新: entity_id={approval.invoice_id}, level={approval_level}, action={action}"
        )

        return approval
