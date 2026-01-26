# -*- coding: utf-8 -*-
"""
审批其他操作（加抄送、撤回、终止、催办、评论）
"""

from datetime import datetime
from typing import Dict, List, Optional

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalInstance,
    ApprovalTask,
)
from app.models.user import User

from .core import ApprovalEngineCore


class ApprovalActionsMixin:
    """审批其他操作功能混入类"""

    def add_cc(
        self: ApprovalEngineCore,
        instance_id: int,
        operator_id: int,
        cc_user_ids: List[int],
    ) -> List[ApprovalCarbonCopy]:
        """
        加抄送

        Args:
            instance_id: 审批实例ID
            operator_id: 操作人ID
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的抄送记录列表
        """
        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == instance_id)
            .first()
        )

        if not instance:
            raise ValueError(f"审批实例不存在: {instance_id}")

        operator = self.db.query(User).filter(User.id == operator_id).first()

        records = self.executor.create_cc_records(
            instance=instance,
            node_id=instance.current_node_id,
            cc_user_ids=cc_user_ids,
            cc_source="APPROVER",
            added_by=operator_id,
        )

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            operator_id=operator_id,
            operator_name=operator.real_name or operator.username if operator else None,
            action="ADD_CC",
            action_detail={"cc_user_ids": cc_user_ids},
        )

        # 通知抄送人
        for record in records:
            self.notify.notify_cc(record)

        self.db.commit()
        return records

    def withdraw(
        self: ApprovalEngineCore,
        instance_id: int,
        initiator_id: int,
        comment: Optional[str] = None,
    ) -> ApprovalInstance:
        """
        撤回审批

        Args:
            instance_id: 审批实例ID
            initiator_id: 发起人ID（只有发起人可以撤回）
            comment: 撤回说明

        Returns:
            更新后的审批实例
        """
        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == instance_id)
            .first()
        )

        if not instance:
            raise ValueError(f"审批实例不存在: {instance_id}")

        if instance.initiator_id != initiator_id:
            raise ValueError("只有发起人可以撤回审批")

        if instance.status not in ("PENDING", "DRAFT"):
            raise ValueError(f"当前状态不允许撤回: {instance.status}")

        initiator = self.db.query(User).filter(User.id == initiator_id).first()

        # 获取受影响的用户
        affected_user_ids = self._get_affected_user_ids(instance)

        # 取消所有待处理任务
        self.db.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.status == "PENDING",
        ).update({"status": "CANCELLED"}, synchronize_session=False)

        # 更新实例状态
        old_status = instance.status
        instance.status = "CANCELLED"
        instance.completed_at = datetime.now()

        # 调用适配器的撤回回调
        self._call_adapter_callback(instance, "on_withdrawn")

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            operator_id=initiator_id,
            operator_name=initiator.real_name or initiator.username
            if initiator
            else None,
            action="WITHDRAW",
            comment=comment,
            before_status=old_status,
            after_status="CANCELLED",
        )

        # 通知相关人员
        self.notify.notify_withdrawn(instance, affected_user_ids)

        self.db.commit()
        return instance

    def terminate(
        self: ApprovalEngineCore,
        instance_id: int,
        operator_id: int,
        comment: str,
    ) -> ApprovalInstance:
        """
        终止审批（管理员操作）

        Args:
            instance_id: 审批实例ID
            operator_id: 操作人ID
            comment: 终止原因

        Returns:
            更新后的审批实例
        """
        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == instance_id)
            .first()
        )

        if not instance:
            raise ValueError(f"审批实例不存在: {instance_id}")

        if instance.status not in ("PENDING",):
            raise ValueError(f"当前状态不允许终止: {instance.status}")

        operator = self.db.query(User).filter(User.id == operator_id).first()

        # 取消所有待处理任务
        self.db.query(ApprovalTask).filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.status == "PENDING",
        ).update({"status": "CANCELLED"}, synchronize_session=False)

        # 更新实例状态
        old_status = instance.status
        instance.status = "TERMINATED"
        instance.completed_at = datetime.now()

        # 调用适配器的终止回调
        self._call_adapter_callback(instance, "on_terminated")

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            operator_id=operator_id,
            operator_name=operator.real_name or operator.username if operator else None,
            action="TERMINATE",
            comment=comment,
            before_status=old_status,
            after_status="TERMINATED",
        )

        self.db.commit()
        return instance

    def remind(
        self: ApprovalEngineCore,
        task_id: int,
        reminder_id: int,
    ) -> bool:
        """
        催办

        Args:
            task_id: 任务ID
            reminder_id: 催办人ID

        Returns:
            是否成功
        """
        task = self.db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.status != "PENDING":
            raise ValueError("只能催办待处理的任务")

        reminder = self.db.query(User).filter(User.id == reminder_id).first()

        # 更新催办信息
        task.remind_count = (task.remind_count or 0) + 1
        task.reminded_at = datetime.now()

        # 记录日志
        self._log_action(
            instance_id=task.instance_id,
            task_id=task.id,
            operator_id=reminder_id,
            operator_name=reminder.real_name or reminder.username if reminder else None,
            action="REMIND",
        )

        # 发送催办通知
        self.notify.notify_remind(
            task,
            reminder_id=reminder_id,
            reminder_name=reminder.real_name or reminder.username if reminder else None,
        )

        self.db.commit()
        return True

    def add_comment(
        self: ApprovalEngineCore,
        instance_id: int,
        user_id: int,
        content: str,
        parent_id: Optional[int] = None,
        reply_to_user_id: Optional[int] = None,
        mentioned_user_ids: Optional[List[int]] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> ApprovalComment:
        """
        添加评论

        Args:
            instance_id: 审批实例ID
            user_id: 评论人ID
            content: 评论内容
            parent_id: 父评论ID（回复时）
            reply_to_user_id: 回复的用户ID
            mentioned_user_ids: @提及的用户ID列表
            attachments: 附件

        Returns:
            创建的评论
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        comment = ApprovalComment(
            instance_id=instance_id,
            user_id=user_id,
            user_name=user.real_name or user.username if user else None,
            content=content,
            parent_id=parent_id,
            reply_to_user_id=reply_to_user_id,
            mentioned_user_ids=mentioned_user_ids,
            attachments=attachments,
        )
        self.db.add(comment)
        self.db.flush()

        # 记录日志
        self._log_action(
            instance_id=instance_id,
            operator_id=user_id,
            operator_name=user.real_name or user.username if user else None,
            action="COMMENT",
            comment=content,
        )

        # 通知被@的用户
        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == instance_id)
            .first()
        )
        if instance and mentioned_user_ids:
            self.notify.notify_comment(
                instance,
                commenter_name=user.real_name or user.username if user else "匿名",
                comment_content=content,
                mentioned_user_ids=mentioned_user_ids,
            )

        self.db.commit()
        return comment
