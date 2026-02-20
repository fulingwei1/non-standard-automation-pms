# -*- coding: utf-8 -*-
"""
验收单审批业务逻辑服务
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.approval import ApprovalInstance, ApprovalTask
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)


class AcceptanceApprovalService:
    """验收单审批服务"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = ApprovalEngineService(db)

    def submit_orders_for_approval(
        self,
        order_ids: List[int],
        initiator_id: int,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量提交验收单审批

        Args:
            order_ids: 验收单ID列表
            initiator_id: 发起人ID
            urgency: 紧急程度
            comment: 提交备注

        Returns:
            (成功列表, 失败列表)
        """
        results = []
        errors = []

        for order_id in order_ids:
            order = (
                self.db.query(AcceptanceOrder)
                .filter(AcceptanceOrder.id == order_id)
                .first()
            )
            if not order:
                errors.append({"order_id": order_id, "error": "验收单不存在"})
                continue

            # 验证状态：只有已完成或被驳回的验收单可以提交审批
            if order.status not in ["COMPLETED", "REJECTED"]:
                errors.append(
                    {
                        "order_id": order_id,
                        "error": f"当前状态 '{order.status}' 不允许提交审批，需要先完成验收",
                    }
                )
                continue

            # 验证是否有验收结论
            if not order.overall_result:
                errors.append(
                    {"order_id": order_id, "error": "验收单没有验收结论，无法提交审批"}
                )
                continue

            try:
                instance = self.engine.submit(
                    template_code="ACCEPTANCE_ORDER_APPROVAL",
                    entity_type="ACCEPTANCE_ORDER",
                    entity_id=order_id,
                    form_data={
                        "order_no": order.order_no,
                        "acceptance_type": order.acceptance_type,
                        "overall_result": order.overall_result,
                        "pass_rate": float(order.pass_rate) if order.pass_rate else 0,
                        "passed_items": order.passed_items or 0,
                        "failed_items": order.failed_items or 0,
                        "total_items": order.total_items or 0,
                        "project_id": order.project_id,
                        "machine_id": order.machine_id,
                        "conclusion": order.conclusion,
                        "conditions": order.conditions,
                    },
                    initiator_id=initiator_id,
                    urgency=urgency,
                )
                results.append(
                    {
                        "order_id": order_id,
                        "order_no": order.order_no,
                        "acceptance_type": order.acceptance_type,
                        "instance_id": instance.id,
                        "status": "submitted",
                    }
                )
            except Exception as e:
                errors.append({"order_id": order_id, "error": str(e)})

        return results, errors

    def get_pending_tasks(
        self,
        user_id: int,
        acceptance_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取待审批任务

        Args:
            user_id: 用户ID
            acceptance_type: 验收类型筛选
            offset: 分页偏移
            limit: 分页限制

        Returns:
            (任务列表, 总数)
        """
        tasks = self.engine.get_pending_tasks(
            user_id=user_id, entity_type="ACCEPTANCE_ORDER"
        )

        # 如果指定了验收类型筛选
        if acceptance_type:
            filtered_tasks = []
            for task in tasks:
                order = (
                    self.db.query(AcceptanceOrder)
                    .filter(AcceptanceOrder.id == task.instance.entity_id)
                    .first()
                )
                if order and order.acceptance_type == acceptance_type:
                    filtered_tasks.append(task)
            tasks = filtered_tasks

        total = len(tasks)
        paginated_tasks = tasks[offset : offset + limit]

        # 类型映射
        type_name_map = {"FAT": "出厂验收", "SAT": "现场验收", "FINAL": "终验收"}
        result_name_map = {
            "PASSED": "合格",
            "FAILED": "不合格",
            "CONDITIONAL": "有条件通过",
        }

        items = []
        for task in paginated_tasks:
            instance = task.instance
            order = (
                self.db.query(AcceptanceOrder)
                .filter(AcceptanceOrder.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "acceptance_type": order.acceptance_type if order else None,
                    "acceptance_type_name": type_name_map.get(order.acceptance_type)
                    if order
                    else None,
                    "overall_result": order.overall_result if order else None,
                    "result_name": result_name_map.get(order.overall_result)
                    if order
                    else None,
                    "pass_rate": float(order.pass_rate)
                    if order and order.pass_rate
                    else 0,
                    "project_name": order.project.project_name
                    if order and hasattr(order, "project") and order.project
                    else None,
                    "machine_code": order.machine.machine_code
                    if order and hasattr(order, "machine") and order.machine
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

        return items, total

    def perform_approval_action(
        self, task_id: int, action: str, approver_id: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行审批操作

        Args:
            task_id: 审批任务ID
            action: 操作类型 (approve/reject)
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            操作结果
        """
        if action == "approve":
            result = self.engine.approve(
                task_id=task_id, approver_id=approver_id, comment=comment
            )
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

    def batch_approval(
        self,
        task_ids: List[int],
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量审批操作

        Args:
            task_ids: 审批任务ID列表
            action: 操作类型 (approve/reject)
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            (成功列表, 失败列表)
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                if action == "approve":
                    self.engine.approve(
                        task_id=task_id, approver_id=approver_id, comment=comment
                    )
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

        return results, errors

    def get_approval_status(self, order_id: int) -> Dict[str, Any]:
        """
        获取验收单审批状态

        Args:
            order_id: 验收单ID

        Returns:
            审批状态信息
        """
        order = (
            self.db.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == order_id)
            .first()
        )
        if not order:
            raise ValueError("验收单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
                ApprovalInstance.entity_id == order_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return {
                "order_id": order_id,
                "order_no": order.order_no,
                "acceptance_type": order.acceptance_type,
                "status": order.status,
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
                    "assignee_name": task.assignee.real_name
                    if task.assignee
                    else None,
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
            "acceptance_type": order.acceptance_type,
            "overall_result": order.overall_result,
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
            order_id: 验收单ID
            user_id: 用户ID
            reason: 撤回原因

        Returns:
            撤回结果
        """
        order = (
            self.db.query(AcceptanceOrder)
            .filter(AcceptanceOrder.id == order_id)
            .first()
        )
        if not order:
            raise ValueError("验收单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
                ApprovalInstance.entity_id == order_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise ValueError("没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise PermissionError("只能撤回自己提交的审批")

        self.engine.withdraw(instance_id=instance.id, user_id=user_id)

        return {
            "order_id": order_id,
            "order_no": order.order_no,
            "status": "withdrawn",
        }

    def get_approval_history(
        self,
        user_id: int,
        acceptance_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取审批历史

        Args:
            user_id: 用户ID
            acceptance_type: 验收类型筛选
            status_filter: 状态筛选
            offset: 分页偏移
            limit: 分页限制

        Returns:
            (历史列表, 总数)
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "ACCEPTANCE_ORDER",
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

        type_name_map = {"FAT": "出厂验收", "SAT": "现场验收", "FINAL": "终验收"}
        result_name_map = {
            "PASSED": "合格",
            "FAILED": "不合格",
            "CONDITIONAL": "有条件通过",
        }

        items = []
        for task in tasks:
            instance = task.instance
            order = (
                self.db.query(AcceptanceOrder)
                .filter(AcceptanceOrder.id == instance.entity_id)
                .first()
            )

            # 如果指定了验收类型筛选
            if acceptance_type and order and order.acceptance_type != acceptance_type:
                continue

            items.append(
                {
                    "task_id": task.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "acceptance_type": order.acceptance_type if order else None,
                    "acceptance_type_name": type_name_map.get(order.acceptance_type)
                    if order
                    else None,
                    "overall_result": order.overall_result if order else None,
                    "result_name": result_name_map.get(order.overall_result)
                    if order
                    else None,
                    "action": task.action,
                    "status": task.status,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return items, total
