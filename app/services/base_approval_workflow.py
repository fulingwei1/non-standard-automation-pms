# -*- coding: utf-8 -*-
"""
审批工作流基类服务

提取采购、外协、合同、ECN、验收、报价等审批工作流的公共逻辑。
各业务域只需继承此基类并实现少量抽象方法即可获得完整的审批工作流能力。

解决 Issue #22: 审批流程重复
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)


class BaseApprovalWorkflowService(ABC):
    """
    审批工作流基类

    子类需实现:
    - entity_type: 实体类型标识 (如 "PURCHASE_ORDER")
    - template_code: 审批模板代码
    - model_class: SQLAlchemy 模型类
    - entity_label: 实体中文名 (如 "采购订单")
    - _get_submittable_statuses(): 允许提交审批的状态列表
    - _build_form_data(entity): 构建审批表单数据
    - _build_pending_item(task, entity): 构建待审批列表项
    - _build_history_item(task, entity): 构建历史记录项
    - _build_status_response(entity, instance, task_history): 构建状态响应
    """

    # ---- 子类必须定义的类属性 ----
    entity_type: str  # e.g. "PURCHASE_ORDER"
    template_code: str  # e.g. "PURCHASE_ORDER_APPROVAL"
    model_class: Type  # e.g. PurchaseOrder
    entity_label: str  # e.g. "采购订单"

    def __init__(self, db: Session):
        self.db = db
        self.engine = ApprovalEngineService(db)

    # ---- 子类必须实现的抽象方法 ----

    @abstractmethod
    def _get_submittable_statuses(self) -> List[str]:
        """返回允许提交审批的状态列表"""
        ...

    @abstractmethod
    def _build_form_data(self, entity: Any) -> Dict[str, Any]:
        """从实体构建审批表单数据"""
        ...

    @abstractmethod
    def _build_pending_item(self, task: Any, entity: Any) -> Dict[str, Any]:
        """构建待审批列表中的单个条目"""
        ...

    @abstractmethod
    def _build_history_item(self, task: Any, entity: Any) -> Dict[str, Any]:
        """构建审批历史中的单个条目"""
        ...

    # ---- 子类可选覆盖的钩子 ----

    def _get_entity_no(self, entity: Any) -> Optional[str]:
        """获取实体编号，默认尝试 order_no"""
        for attr in ("order_no", "contract_no", "quote_no", "ecn_no"):
            if hasattr(entity, attr):
                return getattr(entity, attr)
        return str(entity.id)

    def _on_approved(self, entity_id: int, approver_id: int) -> None:
        """审批通过后的回调（如触发成本归集），默认无操作"""
        pass

    def _on_rejected(self, entity_id: int, approver_id: int) -> None:
        """审批驳回后的回调，默认无操作"""
        pass

    # ---- 公共方法（所有子类共享） ----

    def submit_orders_for_approval(
        self,
        order_ids: List[int],
        initiator_id: int,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """提交实体审批"""
        results = []
        errors = []

        for order_id in order_ids:
            entity = (
                self.db.query(self.model_class)
                .filter(self.model_class.id == order_id)
                .first()
            )
            if not entity:
                errors.append({"order_id": order_id, "error": f"{self.entity_label}不存在"})
                continue

            current_status = getattr(entity, "status", None)
            if current_status not in self._get_submittable_statuses():
                errors.append(
                    {
                        "order_id": order_id,
                        "error": f"当前状态 '{current_status}' 不允许提交审批",
                    }
                )
                continue

            try:
                instance = self.engine.submit(
                    template_code=self.template_code,
                    entity_type=self.entity_type,
                    entity_id=order_id,
                    form_data=self._build_form_data(entity),
                    initiator_id=initiator_id,
                    urgency=urgency,
                )
                results.append(
                    {
                        "order_id": order_id,
                        "order_no": self._get_entity_no(entity),
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
        """获取待审批任务列表"""
        tasks = self.engine.get_pending_tasks(
            user_id=user_id, entity_type=self.entity_type
        )

        total = len(tasks)
        paginated_tasks = tasks[offset : offset + limit]

        items = []
        for task in paginated_tasks:
            instance = task.instance
            entity = (
                self.db.query(self.model_class)
                .filter(self.model_class.id == instance.entity_id)
                .first()
            )

            base_item = {
                "task_id": task.id,
                "instance_id": instance.id,
                "order_id": instance.entity_id,
                "initiator_name": instance.initiator.real_name
                if instance.initiator
                else None,
                "submitted_at": instance.created_at.isoformat()
                if instance.created_at
                else None,
                "urgency": instance.urgency,
                "node_name": task.node.node_name if task.node else None,
            }
            # 合并子类的扩展字段
            base_item.update(self._build_pending_item(task, entity))
            items.append(base_item)

        return {"items": items, "total": total}

    def perform_approval_action(
        self,
        task_id: int,
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行审批操作"""
        if action == "approve":
            result = self.engine.approve(
                task_id=task_id, approver_id=approver_id, comment=comment
            )
            if hasattr(result, "status") and result.status == "APPROVED":
                self._on_approved(result.entity_id, approver_id)
        elif action == "reject":
            result = self.engine.reject(
                task_id=task_id, approver_id=approver_id, comment=comment
            )
            if hasattr(result, "status") and result.status == "REJECTED":
                self._on_rejected(result.entity_id, approver_id)
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
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批量审批操作"""
        results = []
        errors = []

        for task_id in task_ids:
            try:
                self.perform_approval_action(
                    task_id=task_id,
                    action=action,
                    approver_id=approver_id,
                    comment=comment,
                )
                results.append({"task_id": task_id, "status": "success"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_approval_status(self, order_id: int) -> Dict[str, Any]:
        """查询审批状态"""
        entity = (
            self.db.query(self.model_class)
            .filter(self.model_class.id == order_id)
            .first()
        )
        if not entity:
            raise ValueError(f"{self.entity_label}不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == self.entity_type,
                ApprovalInstance.entity_id == order_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        entity_no = self._get_entity_no(entity)

        if not instance:
            return {
                "order_id": order_id,
                "order_no": entity_no,
                "order_status": getattr(entity, "status", None),
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
            "order_no": entity_no,
            "order_status": getattr(entity, "status", None),
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
        """撤回审批"""
        entity = (
            self.db.query(self.model_class)
            .filter(self.model_class.id == order_id)
            .first()
        )
        if not entity:
            raise ValueError(f"{self.entity_label}不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == self.entity_type,
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
            "order_no": self._get_entity_no(entity),
            "status": "withdrawn",
        }

    def get_approval_history(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取审批历史"""
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == self.entity_type,
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
            entity = (
                self.db.query(self.model_class)
                .filter(self.model_class.id == instance.entity_id)
                .first()
            )

            base_item = {
                "task_id": task.id,
                "order_id": instance.entity_id,
                "action": task.action,
                "status": task.status,
                "comment": task.comment,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
            }
            base_item.update(self._build_history_item(task, entity))
            items.append(base_item)

        return {"items": items, "total": total}
