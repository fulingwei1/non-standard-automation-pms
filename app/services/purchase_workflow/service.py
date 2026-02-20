# -*- coding: utf-8 -*-
"""
采购工作流服务

封装采购订单审批流程的业务逻辑。
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.purchase import PurchaseOrder
from app.services.approval_engine import ApprovalEngineService
from app.utils.db_helpers import get_or_404


class PurchaseWorkflowService:
    """采购工作流服务"""

    def __init__(self, db: Session):
        """初始化服务"""
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
        提交采购订单审批

        Args:
            order_ids: 采购订单ID列表
            initiator_id: 提交人用户ID
            urgency: 紧急程度 LOW/NORMAL/HIGH/URGENT
            comment: 提交备注

        Returns:
            包含成功和失败结果的字典
        """
        results = []
        errors = []

        for order_id in order_ids:
            order = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
            if not order:
                errors.append({"order_id": order_id, "error": "采购订单不存在"})
                continue

            if order.status not in ["DRAFT", "REJECTED"]:
                errors.append(
                    {"order_id": order_id, "error": f"当前状态 '{order.status}' 不允许提交审批"}
                )
                continue

            try:
                instance = self.engine.submit(
                    template_code="PURCHASE_ORDER_APPROVAL",
                    entity_type="PURCHASE_ORDER",
                    entity_id=order_id,
                    form_data={
                        "order_no": order.order_no,
                        "order_title": order.order_title,
                        "amount_with_tax": float(order.amount_with_tax) if order.amount_with_tax else 0,
                        "supplier_id": order.supplier_id,
                        "project_id": order.project_id,
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
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取待审批的采购订单列表

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            包含任务列表和分页信息的字典
        """
        tasks = self.engine.get_pending_tasks(
            user_id=user_id, entity_type="PURCHASE_ORDER"
        )

        # 分页
        total = len(tasks)
        paginated_tasks = tasks[offset : offset + limit]

        items = []
        for task in paginated_tasks:
            instance = task.instance
            order = (
                self.db.query(PurchaseOrder)
                .filter(PurchaseOrder.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "order_title": order.order_title if order else None,
                    "amount_with_tax": float(order.amount_with_tax)
                    if order and order.amount_with_tax
                    else 0,
                    "supplier_name": order.supplier.vendor_name
                    if order and order.supplier
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

        return {
            "items": items,
            "total": total,
        }

    def perform_approval_action(
        self,
        task_id: int,
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行审批操作

        Args:
            task_id: 审批任务ID
            action: 操作类型 approve/reject
            approver_id: 审批人用户ID
            comment: 审批意见

        Returns:
            审批结果字典

        Raises:
            HTTPException: 操作类型不支持
        """
        if action == "approve":
            result = self.engine.approve(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        elif action == "reject":
            result = self.engine.reject(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的操作类型: {action}"
            )

        return {
            "task_id": task_id,
            "action": action,
            "instance_status": result.status if hasattr(result, "status") else None,
        }

    def perform_batch_approval(
        self,
        task_ids: List[int],
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量审批操作

        Args:
            task_ids: 审批任务ID列表
            action: 操作类型 approve/reject
            approver_id: 审批人用户ID
            comment: 审批意见

        Returns:
            包含成功和失败结果的字典
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                if action == "approve":
                    self.engine.approve(
                        task_id=task_id,
                        approver_id=approver_id,
                        comment=comment,
                    )
                elif action == "reject":
                    self.engine.reject(
                        task_id=task_id,
                        approver_id=approver_id,
                        comment=comment,
                    )
                else:
                    errors.append({"task_id": task_id, "error": f"不支持的操作: {action}"})
                    continue

                results.append({"task_id": task_id, "status": "success"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_approval_status(self, order_id: int) -> Dict[str, Any]:
        """
        查询采购订单审批状态

        Args:
            order_id: 采购订单ID

        Returns:
            审批状态信息字典
        """
        order = get_or_404(self.db, PurchaseOrder, order_id, "采购订单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "PURCHASE_ORDER",
                ApprovalInstance.entity_id == order_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return {
                "order_id": order_id,
                "order_no": order.order_no,
                "status": order.status,
                "approval_instance": None,
            }

        # 获取审批任务历史
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
        self,
        order_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        撤回审批

        Args:
            order_id: 采购订单ID
            user_id: 用户ID
            reason: 撤回原因

        Returns:
            撤回结果字典

        Raises:
            HTTPException: 无可撤回的审批或无权限
        """
        order = get_or_404(self.db, PurchaseOrder, order_id, "采购订单不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "PURCHASE_ORDER",
                ApprovalInstance.entity_id == order_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise HTTPException(status_code=400, detail="没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise HTTPException(status_code=403, detail="只能撤回自己提交的审批")

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
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取审批历史

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量
            status_filter: 状态筛选

        Returns:
            包含历史记录和分页信息的字典
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "PURCHASE_ORDER",
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
                self.db.query(PurchaseOrder)
                .filter(PurchaseOrder.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "order_id": instance.entity_id,
                    "order_no": order.order_no if order else None,
                    "order_title": order.order_title if order else None,
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

        return {
            "items": items,
            "total": total,
        }
