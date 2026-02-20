# -*- coding: utf-8 -*-
"""
外协工作流服务层

提供外协订单审批工作流的业务逻辑处理。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.outsourcing import OutsourcingOrder
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)


class OutsourcingWorkflowService:
    """外协工作流服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.engine = ApprovalEngineService(db)

    def submit_orders_for_approval(
        self,
        order_ids: List[int],
        initiator_id: int,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        提交外协订单审批

        Args:
            order_ids: 外协订单ID列表
            initiator_id: 提交人ID
            urgency: 紧急程度
            comment: 提交备注

        Returns:
            包含成功和失败结果的字典
        """
        results = []
        errors = []

        for order_id in order_ids:
            order = (
                self.db.query(OutsourcingOrder)
                .filter(OutsourcingOrder.id == order_id)
                .first()
            )
            if not order:
                errors.append({"order_id": order_id, "error": "外协订单不存在"})
                continue

            if order.status not in ["DRAFT", "REJECTED"]:
                errors.append(
                    {
                        "order_id": order_id,
                        "error": f"当前状态 '{order.status}' 不允许提交审批",
                    }
                )
                continue

            try:
                instance = self.engine.submit(
                    template_code="OUTSOURCING_ORDER_APPROVAL",
                    entity_type="OUTSOURCING_ORDER",
                    entity_id=order_id,
                    form_data={
                        "order_no": order.order_no,
                        "order_title": order.order_title,
                        "order_type": order.order_type,
                        "amount_with_tax": float(order.amount_with_tax)
                        if order.amount_with_tax
                        else 0,
                        "vendor_id": order.vendor_id,
                        "project_id": order.project_id,
                        "machine_id": order.machine_id,
                    },
                    initiator_id=initiator_id,
                    urgency=urgency,
                )
                results.append(
                    {
                        "order_id": order_id,
                        "order_no": order.order_no,
                        "instance_id": instance.id,
                        "status": "submitted",
                    }
                )
            except Exception as e:
                errors.append({"order_id": order_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_pending_tasks(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取待审批任务列表

        Args:
            user_id: 用户ID
            offset: 分页偏移
            limit: 分页大小

        Returns:
            包含任务列表和分页信息的字典
        """
        tasks = self.engine.get_pending_tasks(
            user_id=user_id, entity_type="OUTSOURCING_ORDER"
        )

        total = len(tasks)
        paginated_tasks = tasks[offset : offset + limit]

        items = []
        for task in paginated_tasks:
            instance = task.instance
            order = (
                self.db.query(OutsourcingOrder)
                .filter(OutsourcingOrder.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "order_title": order.order_title if order else None,
                    "order_type": order.order_type if order else None,
                    "amount_with_tax": float(order.amount_with_tax)
                    if order and order.amount_with_tax
                    else 0,
                    "vendor_name": order.vendor.vendor_name
                    if order and hasattr(order, "vendor") and order.vendor
                    else None,
                    "project_name": order.project.project_name
                    if order and hasattr(order, "project") and order.project
                    else None,
                    "initiator_name": instance.initiator.real_name
                    if instance.initiator
                    else None,
                    "submitted_at": instance.created_at.isoformat()
                    if instance.created_at
                    else None,
                    "urgency": instance.urgency,
                    "node_name": task.node.node_name if task.node else None,
                }
            )

        return {"items": items, "total": total}

    def perform_approval_action(
        self, task_id: int, approver_id: int, action: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行审批操作

        Args:
            task_id: 审批任务ID
            approver_id: 审批人ID
            action: 操作类型 (approve/reject)
            comment: 审批意见

        Returns:
            审批结果字典

        Raises:
            ValueError: 不支持的操作类型
        """
        if action == "approve":
            result = self.engine.approve(
                task_id=task_id, approver_id=approver_id, comment=comment
            )

            # 审批通过后触发成本归集
            if hasattr(result, "status") and result.status == "APPROVED":
                self._trigger_cost_collection(result.entity_id, approver_id)

        elif action == "reject":
            result = self.engine.reject(
                task_id=task_id, approver_id=approver_id, comment=comment
            )
        else:
            raise ValueError(f"不支持的操作类型: {action}")

        return {
            "task_id": task_id,
            "action": action,
            "instance_status": result.status if hasattr(result, "status") else None,
        }

    def perform_batch_approval(
        self,
        task_ids: List[int],
        approver_id: int,
        action: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量审批操作

        Args:
            task_ids: 审批任务ID列表
            approver_id: 审批人ID
            action: 操作类型 (approve/reject)
            comment: 审批意见

        Returns:
            包含成功和失败结果的字典
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                if action == "approve":
                    result = self.engine.approve(
                        task_id=task_id, approver_id=approver_id, comment=comment
                    )
                    if hasattr(result, "status") and result.status == "APPROVED":
                        self._trigger_cost_collection(result.entity_id, approver_id)

                elif action == "reject":
                    self.engine.reject(
                        task_id=task_id, approver_id=approver_id, comment=comment
                    )
                else:
                    errors.append(
                        {"task_id": task_id, "error": f"不支持的操作: {action}"}
                    )
                    continue

                results.append({"task_id": task_id, "status": "success"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_approval_status(self, order_id: int) -> Dict[str, Any]:
        """
        查询外协订单审批状态

        Args:
            order_id: 外协订单ID

        Returns:
            审批状态字典

        Raises:
            ValueError: 订单不存在
        """
        order = (
            self.db.query(OutsourcingOrder)
            .filter(OutsourcingOrder.id == order_id)
            .first()
        )
        if not order:
            raise ValueError("外协订单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "OUTSOURCING_ORDER",
                ApprovalInstance.entity_id == order_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return {
                "order_id": order_id,
                "order_no": order.order_no,
                "order_status": order.status,
                "approval_instance": None,
            }

        tasks = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.instance_id == instance.id)
            .order_by(ApprovalTask.created_at)
            .all()
        )

        task_history = []
        for task in tasks:
            task_history.append(
                {
                    "task_id": task.id,
                    "node_name": task.node.node_name if task.node else None,
                    "assignee_name": task.assignee.real_name if task.assignee else None,
                    "status": task.status,
                    "action": task.action,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return {
            "order_id": order_id,
            "order_no": order.order_no,
            "order_status": order.status,
            "instance_id": instance.id,
            "instance_status": instance.status,
            "urgency": instance.urgency,
            "submitted_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "completed_at": instance.completed_at.isoformat()
            if instance.completed_at
            else None,
            "task_history": task_history,
        }

    def withdraw_approval(
        self, order_id: int, user_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撤回审批

        Args:
            order_id: 外协订单ID
            user_id: 撤回操作用户ID
            reason: 撤回原因

        Returns:
            撤回结果字典

        Raises:
            ValueError: 订单不存在、没有进行中的审批或权限不足
        """
        order = (
            self.db.query(OutsourcingOrder)
            .filter(OutsourcingOrder.id == order_id)
            .first()
        )
        if not order:
            raise ValueError("外协订单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "OUTSOURCING_ORDER",
                ApprovalInstance.entity_id == order_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise ValueError("没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise ValueError("只能撤回自己提交的审批")

        self.engine.withdraw(instance_id=instance.id, user_id=user_id)

        return {
            "order_id": order_id,
            "order_no": order.order_no,
            "status": "withdrawn",
        }

    def get_approval_history(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 10,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取审批历史

        Args:
            user_id: 用户ID
            offset: 分页偏移
            limit: 分页大小
            status_filter: 状态筛选

        Returns:
            包含历史记录和分页信息的字典
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "OUTSOURCING_ORDER",
                ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
            )
        )

        if status_filter:
            query = query.filter(ApprovalTask.status == status_filter)

        total = query.count()
        tasks = (
            query.order_by(ApprovalTask.completed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for task in tasks:
            instance = task.instance
            order = (
                self.db.query(OutsourcingOrder)
                .filter(OutsourcingOrder.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "order_title": order.order_title if order else None,
                    "order_type": order.order_type if order else None,
                    "amount_with_tax": float(order.amount_with_tax)
                    if order and order.amount_with_tax
                    else 0,
                    "action": task.action,
                    "status": task.status,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return {"items": items, "total": total}

    def _trigger_cost_collection(self, order_id: int, user_id: int) -> None:
        """
        触发成本归集

        Args:
            order_id: 外协订单ID
            user_id: 触发用户ID
        """
        try:
            from app.services.cost_collection_service import CostCollectionService

            CostCollectionService.collect_from_outsourcing_order(
                self.db, order_id, created_by=user_id
            )
        except Exception as e:
            logger.error(
                f"Failed to collect cost from outsourcing order {order_id}: {e}"
            )
