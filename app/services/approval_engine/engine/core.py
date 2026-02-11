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
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)

from ..delegate import ApprovalDelegateService
from ..executor import ApprovalNodeExecutor
from ..notify import ApprovalNotifyService
from ..router import ApprovalRouterService


class ApprovalEngineCore:
    """审批引擎核心类（内部方法）"""

    def __init__(self, db: Session):
        self.db = db
        self.router = ApprovalRouterService(db)
        self.executor = ApprovalNodeExecutor(db)
        self.notify = ApprovalNotifyService(db)
        self.delegate_service = ApprovalDelegateService(db)

    def _generate_instance_no(self, template_code: str) -> str:
        """生成审批单号（使用 SELECT FOR UPDATE 防止竞态条件）"""
        from sqlalchemy import func, text

        now = datetime.now()
        prefix = f"AP{now.strftime('%y%m%d')}"

        # 使用 SELECT FOR UPDATE 加锁查询当日最大序号，避免并发生成重复单号
        max_instance_query = self.db.query(func.max(ApprovalInstance.instance_no))
        max_instance_query = apply_like_filter(
            max_instance_query,
            ApprovalInstance,
            f"{prefix}%",
            "instance_no",
            use_ilike=False,
        )
        max_instance = max_instance_query.with_for_update().scalar()

        if max_instance:
            # 从已有最大单号提取序号并递增
            try:
                current_seq = int(max_instance[len(prefix):])
                next_seq = current_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:04d}"

    def _get_first_node(self, flow_id: int) -> Optional[ApprovalNodeDefinition]:
        """获取流程的第一个节点"""
        return (
            self.db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == flow_id,
                ApprovalNodeDefinition.is_active == True,
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
                ApprovalNodeDefinition.is_active == True,
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

        # 应用代理人
        processed_approver_ids = []
        for approver_id in approver_ids:
            delegate_config = self.delegate_service.get_active_delegate(
                user_id=approver_id,
                template_id=instance.template_id,
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

    def _get_and_validate_task(
        self,
        task_id: int,
        user_id: int,
    ) -> ApprovalTask:
        """获取并验证任务"""
        task = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.id == task_id)
            .first()
        )

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.assignee_id != user_id:
            raise ValueError("无权操作此任务")

        if task.status != "PENDING":
            raise ValueError(f"任务状态不正确: {task.status}")

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
