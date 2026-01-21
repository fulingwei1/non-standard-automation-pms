# -*- coding: utf-8 -*-
"""
发票审批适配器

将发票模块接入统一审批系统
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
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
            "contract_code": invoice.contract.contract_code if invoice.contract else None,
            "project_id": invoice.project_id,
            "buyer_name": invoice.buyer_name,
            "buyer_tax_no": invoice.buyer_tax_no,
            "issue_date": invoice.issue_date.isoformat() if invoice.issue_date else None,
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
