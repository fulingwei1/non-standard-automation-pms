# -*- coding: utf-8 -*-
"""
采购工作流服务

基于 BaseApprovalWorkflowService 实现，只需定义业务特定的配置和数据映射。
"""

from typing import Any, Dict, List, Optional

from app.models.purchase import PurchaseOrder
from app.services.base_approval_workflow import BaseApprovalWorkflowService


class PurchaseWorkflowService(BaseApprovalWorkflowService):
    """采购工作流服务"""

    entity_type = "PURCHASE_ORDER"
    template_code = "PURCHASE_ORDER_APPROVAL"
    model_class = PurchaseOrder
    entity_label = "采购订单"

    def _get_submittable_statuses(self) -> List[str]:
        return ["DRAFT", "REJECTED"]

    def _build_form_data(self, entity: PurchaseOrder) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no,
            "order_title": entity.order_title,
            "amount_with_tax": float(entity.amount_with_tax) if entity.amount_with_tax else 0,
            "supplier_id": entity.supplier_id,
            "project_id": entity.project_id,
        }

    def _build_pending_item(self, task: Any, entity: Optional[PurchaseOrder]) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no if entity else None,
            "order_title": entity.order_title if entity else None,
            "amount_with_tax": float(entity.amount_with_tax)
            if entity and entity.amount_with_tax
            else 0,
            "supplier_name": entity.supplier.vendor_name
            if entity and entity.supplier
            else None,
        }

    def _build_history_item(self, task: Any, entity: Optional[PurchaseOrder]) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no if entity else None,
            "order_title": entity.order_title if entity else None,
            "amount_with_tax": float(entity.amount_with_tax)
            if entity and entity.amount_with_tax
            else 0,
        }
