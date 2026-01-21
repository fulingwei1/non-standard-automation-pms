# -*- coding: utf-8 -*-
"""
合同审批适配器

将合同模块接入统一审批系统
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.sales.contracts import Contract

from .base import ApprovalAdapter


class ContractApprovalAdapter(ApprovalAdapter):
    """
    合同审批适配器

    支持的条件字段:
    - entity.contract_amount: 合同金额
    - entity.customer_name: 客户名称
    - entity.payment_terms: 付款条款类型
    """

    entity_type = "CONTRACT"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Contract]:
        """获取合同实体"""
        return self.db.query(Contract).filter(Contract.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取合同数据用于条件路由

        Returns:
            包含合同关键数据的字典
        """
        contract = self.get_entity(entity_id)
        if not contract:
            return {}

        return {
            "contract_code": contract.contract_code,
            "customer_contract_no": contract.customer_contract_no,
            "status": contract.status,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "customer_id": contract.customer_id,
            "customer_name": contract.customer.name if contract.customer else None,
            "project_id": contract.project_id,
            "signed_date": contract.signed_date.isoformat() if contract.signed_date else None,
            "owner_id": contract.owner_id,
            "owner_name": contract.owner.name if contract.owner else None,
            "payment_terms_summary": contract.payment_terms_summary,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """提交审批时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批通过时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "APPROVED"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批驳回时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "DRAFT"
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        contract = self.get_entity(entity_id)
        if contract:
            customer_name = contract.customer.name if contract.customer else "未知客户"
            return f"合同审批 - {contract.contract_code} ({customer_name})"
        return f"合同审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("customer_name"):
            parts.append(f"客户: {data['customer_name']}")
        if data.get("contract_amount"):
            parts.append(f"合同金额: ¥{data['contract_amount']:,.2f}")
        if data.get("signed_date"):
            parts.append(f"签订日期: {data['signed_date']}")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        contract = self.get_entity(entity_id)
        if not contract:
            return False, "合同不存在"

        if contract.status not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({contract.status})不允许提交审批"

        if not contract.contract_amount or contract.contract_amount <= 0:
            return False, "合同金额必须大于0"

        return True, ""
