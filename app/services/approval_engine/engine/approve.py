# -*- coding: utf-8 -*-
"""
审批处理功能（通过、驳回、退回、转审、加签）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.approval import ApprovalNodeDefinition, ApprovalTask
from app.models.user import User

from .core import ApprovalEngineCore


class ApprovalProcessMixin:
    """审批处理功能混入类"""

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

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=approver_id,
            operator_name=approver.name if approver else None,
            action="APPROVE",
            comment=comment,
            attachments=attachments,
            before_status=instance.status,
        )

        if can_proceed:
            # 流转到下一节点
            self._advance_to_next_node(instance, task)

        self.db.commit()
        return task

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
        self.executor.process_approval(
            task=task,
            action="REJECT",
            comment=comment,
            attachments=attachments,
        )

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            task_id=task.id,
            node_id=task.node_id,
            operator_id=approver_id,
            operator_name=approver.name if approver else None,
            action="REJECT",
            comment=comment,
            attachments=attachments,
            before_status=instance.status,
            action_detail={"reject_to": reject_to},
        )

        # 根据驳回目标处理
        if reject_to == "START":
            # 驳回到发起人（审批结束）
            instance.status = "REJECTED"
            instance.completed_at = datetime.now()
            # 通知发起人
            self.notify.notify_rejected(
                instance,
                rejector_name=approver.name if approver else None,
                reject_comment=comment,
            )
        elif reject_to == "PREV":
            # 退回到上一节点
            prev_node = self._get_previous_node(node)
            if prev_node:
                self._return_to_node(instance, prev_node)
            else:
                instance.status = "REJECTED"
                instance.completed_at = datetime.now()
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
                    instance.status = "REJECTED"
                    instance.completed_at = datetime.now()
            except ValueError:
                instance.status = "REJECTED"
                instance.completed_at = datetime.now()

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
            operator_name=approver.name if approver else None,
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
            assignee_name=to_user.name,
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
            operator_name=from_user.name if from_user else None,
            action="TRANSFER",
            comment=comment,
            action_detail={"from_user_id": from_user_id, "to_user_id": to_user_id},
        )

        # 通知新审批人
        self.notify.notify_transferred(
            new_task,
            from_user_id=from_user_id,
            from_user_name=from_user.name if from_user else None,
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
                assignee_name=approver.name,
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
            operator_name=operator.name if operator else None,
            action="ADD_APPROVER_BEFORE" if position == "BEFORE" else "ADD_APPROVER_AFTER",
            comment=comment,
            action_detail={"approver_ids": approver_ids, "position": position},
        )

        # 通知新审批人
        for new_task in new_tasks:
            if new_task.status == "PENDING":
                self.notify.notify_add_approver(
                    new_task,
                    added_by_name=operator.name if operator else None,
                    position=position,
                )

        self.db.commit()
        return new_tasks
