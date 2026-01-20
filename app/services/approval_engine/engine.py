# -*- coding: utf-8 -*-
"""
审批引擎核心服务

提供审批流程的完整生命周期管理
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalActionLog,
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.user import User

from .delegate import ApprovalDelegateService
from .executor import ApprovalNodeExecutor
from .notify import ApprovalNotifyService
from .router import ApprovalRouterService


class ApprovalEngineService:
    """审批引擎核心服务"""

    def __init__(self, db: Session):
        self.db = db
        self.router = ApprovalRouterService(db)
        self.executor = ApprovalNodeExecutor(db)
        self.notify = ApprovalNotifyService(db)
        self.delegate_service = ApprovalDelegateService(db)

    # ==================== 审批发起 ====================

    def submit(
        self,
        template_code: str,
        entity_type: str,
        entity_id: int,
        form_data: Dict[str, Any],
        initiator_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        urgency: str = "NORMAL",
        cc_user_ids: Optional[List[int]] = None,
    ) -> ApprovalInstance:
        """
        提交审批

        Args:
            template_code: 审批模板编码
            entity_type: 业务实体类型（如QUOTE/CONTRACT/ECN）
            entity_id: 业务实体ID
            form_data: 表单数据
            initiator_id: 发起人ID
            title: 审批标题
            summary: 审批摘要
            urgency: 紧急程度（NORMAL/URGENT/CRITICAL）
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的审批实例
        """
        # 1. 获取模板
        template = (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code == template_code,
                ApprovalTemplate.is_active == True,
            )
            .first()
        )

        if not template:
            raise ValueError(f"审批模板不存在: {template_code}")

        # 2. 获取发起人信息
        initiator = self.db.query(User).filter(User.id == initiator_id).first()
        if not initiator:
            raise ValueError(f"发起人不存在: {initiator_id}")

        # 3. 构建上下文
        context = {
            "form_data": form_data,
            "initiator": {
                "id": initiator.id,
                "name": initiator.name,
                "dept_id": initiator.department_id,
            },
            "entity": {"type": entity_type, "id": entity_id},
        }

        # 4. 选择审批流程
        flow = self.router.select_flow(template.id, context)
        if not flow:
            raise ValueError(f"未找到适用的审批流程: {template_code}")

        # 5. 创建审批实例
        instance_no = self._generate_instance_no(template_code)
        instance = ApprovalInstance(
            instance_no=instance_no,
            template_id=template.id,
            flow_id=flow.id,
            entity_type=entity_type,
            entity_id=entity_id,
            initiator_id=initiator_id,
            initiator_name=initiator.name,
            initiator_dept_id=initiator.department_id,
            form_data=form_data,
            status="PENDING",
            urgency=urgency,
            title=title or f"{template.template_name} - {initiator.name}",
            summary=summary,
            submitted_at=datetime.now(),
        )
        self.db.add(instance)
        self.db.flush()

        # 6. 记录操作日志
        self._log_action(
            instance_id=instance.id,
            operator_id=initiator_id,
            operator_name=initiator.name,
            action="SUBMIT",
            comment=None,
        )

        # 7. 创建第一个节点的任务
        first_node = self._get_first_node(flow.id)
        if first_node:
            instance.current_node_id = first_node.id
            self._create_node_tasks(instance, first_node, context)

        # 8. 处理抄送
        if cc_user_ids:
            self.executor.create_cc_records(
                instance=instance,
                node_id=None,
                cc_user_ids=cc_user_ids,
                cc_source="INITIATOR",
                added_by=initiator_id,
            )

        self.db.commit()
        return instance

    def save_draft(
        self,
        template_code: str,
        entity_type: str,
        entity_id: int,
        form_data: Dict[str, Any],
        initiator_id: int,
        title: Optional[str] = None,
    ) -> ApprovalInstance:
        """保存审批草稿"""
        template = (
            self.db.query(ApprovalTemplate)
            .filter(
                ApprovalTemplate.template_code == template_code,
                ApprovalTemplate.is_active == True,
            )
            .first()
        )

        if not template:
            raise ValueError(f"审批模板不存在: {template_code}")

        initiator = self.db.query(User).filter(User.id == initiator_id).first()

        instance = ApprovalInstance(
            instance_no=self._generate_instance_no(template_code),
            template_id=template.id,
            entity_type=entity_type,
            entity_id=entity_id,
            initiator_id=initiator_id,
            initiator_name=initiator.name if initiator else None,
            form_data=form_data,
            status="DRAFT",
            title=title,
        )
        self.db.add(instance)
        self.db.commit()

        return instance

    # ==================== 审批操作 ====================

    def approve(
        self,
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
            eval_data: 评估数据（ECN��景）

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
        self,
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
        self,
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
        self,
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
        self,
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

    def add_cc(
        self,
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
            operator_name=operator.name if operator else None,
            action="ADD_CC",
            action_detail={"cc_user_ids": cc_user_ids},
        )

        # 通知抄送人
        for record in records:
            self.notify.notify_cc(record)

        self.db.commit()
        return records

    def withdraw(
        self,
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

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            operator_id=initiator_id,
            operator_name=initiator.name if initiator else None,
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
        self,
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

        # 记录日志
        self._log_action(
            instance_id=instance.id,
            operator_id=operator_id,
            operator_name=operator.name if operator else None,
            action="TERMINATE",
            comment=comment,
            before_status=old_status,
            after_status="TERMINATED",
        )

        self.db.commit()
        return instance

    def remind(
        self,
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
        task = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.id == task_id)
            .first()
        )

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
            operator_name=reminder.name if reminder else None,
            action="REMIND",
        )

        # 发送催办通知
        self.notify.notify_remind(
            task,
            reminder_id=reminder_id,
            reminder_name=reminder.name if reminder else None,
        )

        self.db.commit()
        return True

    def add_comment(
        self,
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
            user_name=user.name if user else None,
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
            operator_name=user.name if user else None,
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
                commenter_name=user.name if user else "匿名",
                comment_content=content,
                mentioned_user_ids=mentioned_user_ids,
            )

        self.db.commit()
        return comment

    # ==================== 查询方法 ====================

    def get_pending_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取用户待审批的任务"""
        query = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalTask.status == "PENDING",
            )
            .order_by(ApprovalTask.created_at.desc())
        )

        total = query.count()
        tasks = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": tasks,
        }

    def get_initiated_instances(
        self,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取用户发起的审批"""
        query = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.initiator_id == user_id,
        )

        if status:
            query = query.filter(ApprovalInstance.status == status)

        query = query.order_by(ApprovalInstance.created_at.desc())

        total = query.count()
        instances = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": instances,
        }

    def get_cc_records(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取抄送给用户的记录"""
        query = self.db.query(ApprovalCarbonCopy).filter(
            ApprovalCarbonCopy.cc_user_id == user_id,
        )

        if is_read is not None:
            query = query.filter(ApprovalCarbonCopy.is_read == is_read)

        query = query.order_by(ApprovalCarbonCopy.created_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": records,
        }

    def mark_cc_as_read(self, cc_id: int, user_id: int) -> bool:
        """标记抄送为已读"""
        cc = (
            self.db.query(ApprovalCarbonCopy)
            .filter(
                ApprovalCarbonCopy.id == cc_id,
                ApprovalCarbonCopy.cc_user_id == user_id,
            )
            .first()
        )

        if cc:
            cc.is_read = True
            cc.read_at = datetime.now()

            self._log_action(
                instance_id=cc.instance_id,
                operator_id=user_id,
                action="READ_CC",
            )

            self.db.commit()
            return True

        return False

    # ==================== 内部方法 ====================

    def _generate_instance_no(self, template_code: str) -> str:
        """生成审批单号"""
        now = datetime.now()
        prefix = f"AP{now.strftime('%y%m%d')}"

        # 查询今天的最大序号
        max_no = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.instance_no.like(f"{prefix}%"))
            .count()
        )

        return f"{prefix}{max_no + 1:04d}"

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
            self.notify.notify_approved(instance)
            return

        # 处理下一节点
        next_node = next_nodes[0]
        instance.current_node_id = next_node.id

        self._create_node_tasks(instance, next_node, context)

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
