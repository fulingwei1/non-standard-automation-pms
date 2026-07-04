# -*- coding: utf-8 -*-
"""
发货单审批适配器

将商务支持发货单接入统一审批系统。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.business_support import DeliveryOrder

from .base import ApprovalAdapter


class DeliveryOrderApprovalAdapter(ApprovalAdapter):
    """发货单审批适配器。"""

    entity_type = "DELIVERY_ORDER"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[DeliveryOrder]:
        return self.db.query(DeliveryOrder).filter(DeliveryOrder.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        delivery_order = self.get_entity(entity_id)
        if not delivery_order:
            return {}

        return {
            "delivery_no": delivery_order.delivery_no,
            "order_id": delivery_order.order_id,
            "order_no": delivery_order.order_no,
            "contract_id": delivery_order.contract_id,
            "customer_id": delivery_order.customer_id,
            "customer_name": delivery_order.customer_name,
            "project_id": delivery_order.project_id,
            "delivery_date": (
                delivery_order.delivery_date.isoformat()
                if delivery_order.delivery_date
                else None
            ),
            "delivery_type": delivery_order.delivery_type,
            "delivery_amount": (
                float(delivery_order.delivery_amount)
                if delivery_order.delivery_amount is not None
                else 0
            ),
            "approval_status": delivery_order.approval_status,
            "delivery_status": delivery_order.delivery_status,
            "special_approval": bool(delivery_order.special_approval),
            "special_approval_reason": delivery_order.special_approval_reason,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        delivery_order = self.get_entity(entity_id)
        if delivery_order:
            delivery_order.approval_status = "pending"
            if delivery_order.delivery_status not in {"printed", "shipped", "received"}:
                delivery_order.delivery_status = "draft"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        delivery_order = self.get_entity(entity_id)
        if delivery_order:
            delivery_order.approval_status = "approved"
            delivery_order.delivery_status = "approved"
            delivery_order.approved_by = instance.final_approver_id
            delivery_order.approved_at = instance.completed_at or datetime.now()
            delivery_order.approval_comment = instance.final_comment
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        delivery_order = self.get_entity(entity_id)
        if delivery_order:
            delivery_order.approval_status = "rejected"
            delivery_order.delivery_status = "draft"
            delivery_order.approved_by = instance.final_approver_id
            delivery_order.approved_at = instance.completed_at or datetime.now()
            delivery_order.approval_comment = instance.final_comment
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        delivery_order = self.get_entity(entity_id)
        if delivery_order:
            delivery_order.approval_status = "pending"
            delivery_order.delivery_status = "draft"
            self.db.flush()

    def generate_title(self, entity_id: int) -> str:
        delivery_order = self.get_entity(entity_id)
        if not delivery_order:
            return f"发货单审批 - #{entity_id}"
        return f"发货单审批 - {delivery_order.delivery_no}"

    def generate_summary(self, entity_id: int) -> str:
        delivery_order = self.get_entity(entity_id)
        if not delivery_order:
            return ""

        amount = (
            f"¥{delivery_order.delivery_amount:,.2f}"
            if delivery_order.delivery_amount is not None
            else "未填写"
        )
        parts = [
            f"送货单号: {delivery_order.delivery_no}",
            f"客户: {delivery_order.customer_name or '未指定'}",
            f"发货金额: {amount}",
        ]
        if delivery_order.project_id:
            parts.append(f"项目ID: {delivery_order.project_id}")
        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        delivery_order = self.get_entity(entity_id)
        if not delivery_order:
            return False, "发货单不存在"
        if delivery_order.delivery_status in {"shipped", "received"}:
            return False, "已发货或已签收的发货单不能提交审批"
        if delivery_order.approval_status == "approved":
            return False, "发货单已审批通过"
        if not delivery_order.project_id:
            return False, "发货单必须关联项目后才能提交审批"
        if delivery_order.delivery_amount is None or delivery_order.delivery_amount <= 0:
            return False, "发货金额必须大于0"
        return True, None
