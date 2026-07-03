# -*- coding: utf-8 -*-
"""
审批引擎核心类和内部方法
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.approval import (
    ApprovalActionLog,
    ApprovalCountersignResult,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)

from ..delegate import ApprovalDelegateService
from ..executor import ApprovalNodeExecutor
from ..notify import ApprovalNotifyService
from ..router import ApprovalRouterService


TERMINAL_INSTANCE_STATUSES = {"APPROVED", "REJECTED", "CANCELLED", "TERMINATED"}


class ApprovalEngineCore:
    """审批引擎核心类（内部方法）"""

    def __init__(self, db: Session):
        self.db = db
        self.router = ApprovalRouterService(db)
        self.executor = ApprovalNodeExecutor(db)
        self.notify = ApprovalNotifyService(db)
        self.delegate_service = ApprovalDelegateService(db)

    def _generate_instance_no(self, template_code: str) -> str:
        """生成审批单号（兼容同日前缀的旧随机编号）。"""
        now = datetime.now()
        prefix = f"AP{now.strftime('%y%m%d')}"

        query = self.db.query(ApprovalInstance.instance_no)
        query = apply_like_filter(
            query,
            ApprovalInstance,
            f"{prefix}%",
            "instance_no",
            use_ilike=False,
        )
        existing_numbers = [row[0] for row in query.with_for_update().all()]

        max_seq = 0
        existing_set = set()
        for instance_no in existing_numbers:
            if not instance_no:
                continue
            existing_set.add(instance_no)
            suffix = instance_no[len(prefix) :]
            if suffix.isdigit():
                max_seq = max(max_seq, int(suffix))

        next_seq = max_seq + 1
        candidate = f"{prefix}{next_seq:04d}"
        while candidate in existing_set:
            next_seq += 1
            candidate = f"{prefix}{next_seq:04d}"

        return candidate

    def _get_first_node(self, flow_id: int) -> Optional[ApprovalNodeDefinition]:
        """获取流程的第一个节点"""
        return (
            self.db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == flow_id,
                ApprovalNodeDefinition.is_active,
                ApprovalNodeDefinition.node_type == "APPROVAL",
            )
            .order_by(ApprovalNodeDefinition.node_order)
            .first()
        )

    def _get_previous_node(
        self,
        current_node: ApprovalNodeDefinition,
    ) -> Optional[ApprovalNodeDefinition]:
        """获取上一个审批节点"""
        return (
            self.db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == current_node.flow_id,
                ApprovalNodeDefinition.node_order < current_node.node_order,
                ApprovalNodeDefinition.is_active,
                ApprovalNodeDefinition.node_type == "APPROVAL",
            )
            .order_by(ApprovalNodeDefinition.node_order.desc())
            .first()
        )

    def _create_node_tasks(
        self,
        instance: ApprovalInstance,
        node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ):
        """为节点创建审批任务"""
        # 解析审批人
        approver_ids = self.router.resolve_approvers(node, context)

        if not approver_ids:
            # 如果没有审批人，跳过此节点
            self._advance_to_next_node(instance, None)
            return

        # 固定用户节点是显式点名审批人，发起时不做全局代理静默替换。
        should_apply_delegate = (
            getattr(node, "can_delegate", True) and node.approver_type != "FIXED_USER"
        )
        processed_approver_ids = []
        for approver_id in approver_ids:
            delegate_config = (
                self.delegate_service.get_active_delegate(
                    user_id=approver_id,
                    template_id=instance.template_id,
                )
                if should_apply_delegate
                else None
            )
            if delegate_config:
                processed_approver_ids.append(delegate_config.delegate_id)
            else:
                processed_approver_ids.append(approver_id)

        # 创建任务
        tasks = self.executor.create_tasks_for_node(
            instance=instance,
            node=node,
            approver_ids=processed_approver_ids,
        )

        # 通知审批人
        for task in tasks:
            if task.status == "PENDING":
                self.notify.notify_pending(task)

        # 处理节点配置的抄送
        cc_config = node.notify_config or {}
        cc_user_ids = cc_config.get("cc_user_ids", [])
        if cc_user_ids:
            self.executor.create_cc_records(
                instance=instance,
                node_id=node.id,
                cc_user_ids=cc_user_ids,
                cc_source="FLOW",
            )

    def _advance_to_next_node(
        self,
        instance: ApprovalInstance,
        current_task: Optional[ApprovalTask],
    ):
        """流转到下一节点"""
        if current_task:
            current_node = current_task.node
        else:
            current_node = (
                self.db.query(ApprovalNodeDefinition)
                .filter(ApprovalNodeDefinition.id == instance.current_node_id)
                .first()
            )

        if not current_node:
            return

        # 构建上下文
        context = {
            "form_data": instance.form_data,
            "initiator": {
                "id": instance.initiator_id,
                "dept_id": instance.initiator_dept_id,
            },
        }

        # 获取下一节点
        next_nodes = self.router.get_next_nodes(current_node, context)

        if not next_nodes:
            # 没有下一节点，审批完成
            instance.status = "APPROVED"
            instance.completed_at = datetime.now()
            if current_task:
                instance.final_approver_id = current_task.assignee_id

            # 调用适配器的通过回调
            self._call_adapter_callback(instance, "on_approved")

            self.notify.notify_approved(instance)
            return

        # 处理下一节点
        next_node = next_nodes[0]
        instance.current_node_id = next_node.id

        self._create_node_tasks(instance, next_node, context)

    def _call_adapter_callback(
        self,
        instance: ApprovalInstance,
        callback_name: str,
    ):
        """调用适配器回调方法"""
        from ..adapters import get_adapter

        try:
            adapter = get_adapter(instance.entity_type, self.db)
            callback = getattr(adapter, callback_name, None)
            if callback:
                callback(instance.entity_id, instance)
        except ValueError:
            # 未配置适配器的业务类型，忽略
            pass

    def _return_to_node(
        self,
        instance: ApprovalInstance,
        target_node: ApprovalNodeDefinition,
    ):
        """退回到指定节点"""
        # 取消当前所有待处理任务
        self.db.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.status == "PENDING",
        ).update({"status": "CANCELLED"}, synchronize_session=False)

        # 更新当前节点
        instance.current_node_id = target_node.id

        # 创建新任务
        context = {
            "form_data": instance.form_data,
            "initiator": {
                "id": instance.initiator_id,
                "dept_id": instance.initiator_dept_id,
            },
        }
        self._create_node_tasks(instance, target_node, context)

    def _get_task_approval_mode(self, task: ApprovalTask) -> str:
        """获取任务所在节点审批模式，兼容测试中不完整的 mock。"""
        node = getattr(task, "node", None)
        mode = getattr(node, "approval_mode", None)
        return mode if isinstance(mode, str) and mode else "SINGLE"

    def _get_countersign_final_result(self, task: ApprovalTask) -> Optional[str]:
        """读取会签汇总结果；非会签节点返回 None。"""
        if self._get_task_approval_mode(task) != "AND_SIGN":
            return None

        result = (
            self.db.query(ApprovalCountersignResult)
            .filter(
                ApprovalCountersignResult.instance_id == task.instance_id,
                ApprovalCountersignResult.node_id == task.node_id,
            )
            .first()
        )
        return result.final_result if result else None

    def _cancel_pending_instance_tasks(
        self,
        instance_id: int,
        exclude_task_id: Optional[int] = None,
    ):
        """取消实例下仍待处理的任务，用于实例进入终态时清理旧待办。"""
        query = self.db.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.status == "PENDING",
        )
        if exclude_task_id is not None:
            query = query.filter(ApprovalTask.id != exclude_task_id)
        query.update({"status": "CANCELLED"}, synchronize_session=False)

    def _complete_instance_as_rejected(
        self,
        instance: ApprovalInstance,
        exclude_task_id: Optional[int] = None,
    ):
        """将实例置为驳回终态，并清理剩余待办，避免后续任务复活实例。"""
        self._cancel_pending_instance_tasks(instance.id, exclude_task_id=exclude_task_id)
        instance.status = "REJECTED"
        instance.completed_at = datetime.now()

    def _ensure_instance_not_terminal(self, instance: ApprovalInstance):
        """终态实例禁止继续处理审批任务。"""
        status = getattr(instance, "status", None)
        if isinstance(status, str) and status.upper() in TERMINAL_INSTANCE_STATUSES:
            raise ValueError(f"审批实例已结束: {status}")

    def _get_and_validate_task(
        self,
        task_id: int,
        user_id: int,
    ) -> ApprovalTask:
        """获取并验证任务"""
        task = self.db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.assignee_id != user_id:
            raise ValueError("无权操作此任务")

        if task.status != "PENDING":
            raise ValueError(f"任务状态不正确: {task.status}")

        self._ensure_instance_not_terminal(task.instance)

        return task

    def _get_affected_user_ids(self, instance: ApprovalInstance) -> List[int]:
        """获取受影响的用户ID列表（用于撤回通知）"""
        # 获取所有待处理任务的审批人
        tasks = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.instance_id == instance.id,
                ApprovalTask.status == "PENDING",
            )
            .all()
        )

        return [task.assignee_id for task in tasks]

    def _log_action(
        self,
        instance_id: int,
        operator_id: int,
        action: str,
        task_id: Optional[int] = None,
        node_id: Optional[int] = None,
        operator_name: Optional[str] = None,
        comment: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        action_detail: Optional[Dict] = None,
        before_status: Optional[str] = None,
        after_status: Optional[str] = None,
    ):
        """记录操作日志"""
        log = ApprovalActionLog(
            instance_id=instance_id,
            task_id=task_id,
            node_id=node_id,
            operator_id=operator_id,
            operator_name=operator_name,
            action=action,
            action_detail=action_detail,
            comment=comment,
            attachments=attachments,
            before_status=before_status,
            after_status=after_status,
            action_at=datetime.now(),
        )
        self.db.add(log)
