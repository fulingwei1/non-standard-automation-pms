# -*- coding: utf-8 -*-
"""
外协工作流服务

基于 BaseApprovalWorkflowService 实现，只需定义业务特定的配置和数据映射。
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.outsourcing import OutsourcingOrder
from app.services.base_approval_workflow import BaseApprovalWorkflowService

logger = logging.getLogger(__name__)


class OutsourcingWorkflowService(BaseApprovalWorkflowService):
    """外协工作流服务"""

    entity_type = "OUTSOURCING_ORDER"
    template_code = "OUTSOURCING_ORDER_APPROVAL"
    model_class = OutsourcingOrder
    entity_label = "外协订单"

    def _get_submittable_statuses(self) -> List[str]:
        return ["DRAFT", "REJECTED"]

    def _build_form_data(self, entity: OutsourcingOrder) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no,
            "order_title": entity.order_title,
            "order_type": entity.order_type,
            "amount_with_tax": float(entity.amount_with_tax) if entity.amount_with_tax else 0,
            "vendor_id": entity.vendor_id,
            "project_id": entity.project_id,
            "machine_id": entity.machine_id,
        }

    def _build_pending_item(self, task: Any, entity: Optional[OutsourcingOrder]) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no if entity else None,
            "order_title": entity.order_title if entity else None,
            "order_type": entity.order_type if entity else None,
            "amount_with_tax": float(entity.amount_with_tax)
            if entity and entity.amount_with_tax
            else 0,
            "vendor_name": entity.vendor.vendor_name
            if entity and hasattr(entity, "vendor") and entity.vendor
            else None,
            "project_name": entity.project.project_name
            if entity and hasattr(entity, "project") and entity.project
            else None,
        }

    def _build_history_item(self, task: Any, entity: Optional[OutsourcingOrder]) -> Dict[str, Any]:
        return {
            "order_no": entity.order_no if entity else None,
            "order_title": entity.order_title if entity else None,
            "order_type": entity.order_type if entity else None,
            "amount_with_tax": float(entity.amount_with_tax)
            if entity and entity.amount_with_tax
            else 0,
        }

    def _on_approved(self, entity_id: int, approver_id: int) -> None:
        """审批通过后触发成本归集"""
        try:
            from app.services.cost_collection_service import CostCollectionService

            CostCollectionService.collect_from_outsourcing_order(
                self.db, entity_id, created_by=approver_id
            )
        except Exception as e:
            logger.error(
                f"Failed to collect cost from outsourcing order {entity_id}: {e}"
            )
