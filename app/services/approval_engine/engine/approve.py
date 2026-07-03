# -*- coding: utf-8 -*-
"""
审批处理功能（通过、驳回、退回、转审、加签）
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.models.approval import ApprovalCountersignResult, ApprovalNodeDefinition, ApprovalTask
from app.models.user import User

from .core import ApprovalEngineCore


class ApprovalProcessMixin:
    """审批处理功能混入类"""

    def _get_task_approval_mode(self: ApprovalEngineCore, task: ApprovalTask) -> str:
        """获取任务所在节点审批模式，兼容只混入本类的单元测试。"""
        node = getattr(task, "node", None)
        mode = getattr(node, "approval_mode", None)
        return mode if isinstance(mode, str) and mode else "SINGLE"

    def _get_countersign_final_result(self: ApprovalEngineCore, task: ApprovalTask) -> Optional[str]:
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
        self: ApprovalEngineCore,
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
        self: ApprovalEngineCore,
        instance,
        exclude_task_id: Optional[int] = None,
    ):
        """将实例置为驳回终态，并清理剩余待办，避免后续任务复活实例。"""
        self._cancel_pending_instance_tasks(instance.id, exclude_task_id=exclude_task_id)
        instance.status = "REJECTED"
        instance.completed_at = datetime.now()

    def approve(
        self: ApprovalEngineCore,
        task_id: int,
        approver_id: int,
        comment: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        eval_data: Optional[Dict] = None,
    ) -> ApprovalTask:
        """
        审批通过

        Args:
            task_id: 任务ID
            approver_id: 审批人ID
            comment: 审批意见
            attachments: 附件列表
            eval_data: 评估数据（ECN场景）

        Returns:
            更新后的任务
        """
        task = self._get_and_validate_task(task_id, approver_id)
        instance = task.instance

        # 获取审批人信息
        approver = self.db.query(User).filter(User.id == approver_id).first()

        # 处理审批
        can_proceed, error = self.executor.process_approval(
            task=task,
            action="APPROVE",
            comment=comment,
            attachments=attachments,
            eval_data=eval_data,
        )
        if error:
            raise ValueError(error)

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=approver_id,
            operator_name=approver.real_name or approver.username if approver else None,
            action="APPROVE",
            comment=comment,
            attachments=attachments,
            before_status=instance.status,
        )

        if can_proceed:
            if self._get_countersign_final_result(task) == "FAILED":
                self._complete_instance_as_rejected(instance, exclude_task_id=task.id)
                self._call_adapter_callback(instance, "on_rejected")
                self.notify.notify_rejected(
                    instance,
                    rejector_name=approver.real_name or approver.username if approver else None,
                    reject_comment="会签未通过",
                )
            else:
                # 流转到下一节点
                self._advance_to_next_node(instance, task)

        self.db.commit()
        return task

    def _reject_instance_to_start(
        self: ApprovalEngineCore,
        instance,
        task: ApprovalTask,
        approver: Optional[User],
        comment: str,
    ):
        """驳回到发起人并进入终态。"""
        self._complete_instance_as_rejected(instance, exclude_task_id=task.id)

        # 调用适配器的驳回回调
        self._call_adapter_callback(instance, "on_rejected")

        # 通知发起人
        self.notify.notify_rejected(
            instance,
            rejector_name=approver.real_name or approver.username if approver else None,
            reject_comment=comment,
        )

    def _advance_after_positive_aggregate_result(
        self: ApprovalEngineCore,
        instance,
        task: ApprovalTask,
    ):
        """会签汇总通过时继续流转。"""
        self._advance_to_next_node(instance, task)

    def reject(
        self: ApprovalEngineCore,
        task_id: int,
        approver_id: int,
        comment: str,
        reject_to: str = "START",
        attachments: Optional[List[Dict]] = None,
    ) -> ApprovalTask:
        """
        审批驳回

        Args:
            task_id: 任务ID
            approver_id: 审批人ID
            comment: 驳回原因（必填）
            reject_to: 驳回目标（START=发起人/PREV=上一节点/节点ID）
            attachments: 附件

        Returns:
            更新后的任务
        """
        if not comment:
            raise ValueError("驳回原因不能为空")

        task = self._get_and_validate_task(task_id, approver_id)
        instance = task.instance
        node = task.node

        approver = self.db.query(User).filter(User.id == approver_id).first()

        # 处理审批
        can_proceed, error = self.executor.process_approval(
            task=task,
            action="REJECT",
            comment=comment,
            attachments=attachments,
        )
        if error:
            raise ValueError(error)

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=approver_id,
            operator_name=approver.real_name or approver.username if approver else None,
            action="REJECT",
            comment=comment,
            attachments=attachments,
            before_status=instance.status,
            action_detail={"reject_to": reject_to},
        )

        # 根据驳回目标处理
        if reject_to == "START":
            approval_mode = self._get_task_approval_mode(task)
            if approval_mode in {"OR_SIGN", "AND_SIGN"} and not can_proceed:
                self.db.commit()
                return task

            if self._get_countersign_final_result(task) == "PASSED":
                self._advance_after_positive_aggregate_result(instance, task)
            else:
                self._reject_instance_to_start(instance, task, approver, comment)
        elif reject_to == "PREV":
            # 退回到上一节点
            prev_node = self._get_previous_node(node)
            if prev_node:
                self._return_to_node(instance, prev_node)
            else:
                self._complete_instance_as_rejected(instance, exclude_task_id=task.id)
        else:
            # 退回到指定节点
            try:
                target_node_id = int(reject_to)
                target_node = (
                    self.db.query(ApprovalNodeDefinition)
                    .filter(ApprovalNodeDefinition.id == target_node_id)
                    .first()
                )
                if target_node:
                    self._return_to_node(instance, target_node)
                else:
                    self._complete_instance_as_rejected(instance, exclude_task_id=task.id)
            except ValueError:
                self._complete_instance_as_rejected(instance, exclude_task_id=task.id)

        self.db.commit()
        return task

    def return_to(
        self: ApprovalEngineCore,
        task_id: int,
        approver_id: int,
        target_node_id: int,
        comment: str,
    ) -> ApprovalTask:
        """
        退回到指定节点

        Args:
            task_id: 任务ID
            approver_id: 操作人ID
            target_node_id: 目标节点ID
            comment: 退回原因

        Returns:
            更新后的任务
        """
        task = self._get_and_validate_task(task_id, approver_id)
        instance = task.instance

        approver = self.db.query(User).filter(User.id == approver_id).first()

        # 更新任务状态
        task.action = "RETURN"
        task.comment = comment
        task.status = "COMPLETED"
        task.completed_at = datetime.now()
        task.return_to_node_id = target_node_id

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=approver_id,
            operator_name=approver.real_name or approver.username if approver else None,
            action="RETURN",
            comment=comment,
            action_detail={"return_to_node_id": target_node_id},
        )

        # 退回到目标节点
        target_node = (
            self.db.query(ApprovalNodeDefinition)
            .filter(ApprovalNodeDefinition.id == target_node_id)
            .first()
        )

        if target_node:
            self._return_to_node(instance, target_node)

        self.db.commit()
        return task

    def transfer(
        self: ApprovalEngineCore,
        task_id: int,
        from_user_id: int,
        to_user_id: int,
        comment: Optional[str] = None,
    ) -> ApprovalTask:
        """
        转审

        Args:
            task_id: 任务ID
            from_user_id: 转出人ID
            to_user_id: 转入人ID
            comment: 转审说明

        Returns:
            更新后的任务
        """
        task = self._get_and_validate_task(task_id, from_user_id)
        instance = task.instance
        node = task.node

        if not node.can_transfer:
            raise ValueError("当前节点不允许转审")

        from_user = self.db.query(User).filter(User.id == from_user_id).first()
        to_user = self.db.query(User).filter(User.id == to_user_id).first()

        if not to_user:
            raise ValueError(f"转审目标用户不存在: {to_user_id}")

        # 更新原任务
        task.status = "TRANSFERRED"
        task.completed_at = datetime.now()

        # 创建新任务
        new_task = ApprovalTask(
            instance_id=instance.id,
            node_id=node.id,
            task_type=task.task_type,
            task_order=task.task_order,
            assignee_id=to_user_id,
            assignee_name=to_user.real_name or to_user.username,
            assignee_type="TRANSFERRED",
            original_assignee_id=from_user_id,
            status="PENDING",
            due_at=task.due_at,
            is_countersign=task.is_countersign,
        )
        self.db.add(new_task)
        self.db.flush()

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=from_user_id,
            operator_name=from_user.real_name or from_user.username if from_user else None,
            action="TRANSFER",
            comment=comment,
            action_detail={"from_user_id": from_user_id, "to_user_id": to_user_id},
        )

        # 通知新审批人
        self.notify.notify_transferred(
            new_task,
            from_user_id=from_user_id,
            from_user_name=from_user.real_name or from_user.username if from_user else None,
        )

        self.db.commit()
        return new_task

    def add_approver(
        self: ApprovalEngineCore,
        task_id: int,
        operator_id: int,
        approver_ids: List[int],
        position: str = "AFTER",
        comment: Optional[str] = None,
    ) -> List[ApprovalTask]:
        """
        加签

        Args:
            task_id: 当前任务ID
            operator_id: 操作人ID
            approver_ids: 要添加的审批人ID列表
            position: 加签位置（BEFORE=前加签/AFTER=后加签）
            comment: 加签说明

        Returns:
            新创建的任务列表
        """
        task = self._get_and_validate_task(task_id, operator_id)
        instance = task.instance
        node = task.node

        if not node.can_add_approver:
            raise ValueError("当前节点不允许加签")

        operator = self.db.query(User).filter(User.id == operator_id).first()
        new_tasks = []

        for approver_id in approver_ids:
            approver = self.db.query(User).filter(User.id == approver_id).first()
            if not approver:
                continue

            assignee_type = "ADDED_BEFORE" if position == "BEFORE" else "ADDED_AFTER"

            new_task = ApprovalTask(
                instance_id=instance.id,
                node_id=node.id,
                task_type="APPROVAL",
                task_order=task.task_order,
                assignee_id=approver_id,
                assignee_name=approver.real_name or approver.username,
                assignee_type=assignee_type,
                status="PENDING" if position == "BEFORE" else "SKIPPED",
                due_at=task.due_at,
            )
            self.db.add(new_task)
            new_tasks.append(new_task)

        self.db.flush()

        # 如果是前加签，当前任务变为等待状态
        if position == "BEFORE":
            task.status = "SKIPPED"

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=operator_id,
            operator_name=operator.real_name or operator.username if operator else None,
            action="ADD_APPROVER_BEFORE" if position == "BEFORE" else "ADD_APPROVER_AFTER",
            comment=comment,
            action_detail={"approver_ids": approver_ids, "position": position},
        )

        # 通知新审批人
        for new_task in new_tasks:
            if new_task.status == "PENDING":
                self.notify.notify_add_approver(
                    new_task,
                    added_by_name=operator.real_name or operator.username if operator else None,
                    position=position,
                )

        self.db.commit()
        return new_tasks
