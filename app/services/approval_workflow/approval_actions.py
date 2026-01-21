# -*- coding: utf-8 -*-
"""
审批操作模块
提供审批通过、驳回、委托、撤回等操作功能
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_

from app.models.enums import ApprovalActionEnum, ApprovalRecordStatusEnum
from app.models.sales import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflowStep,
)


class ApprovalActionsMixin:
    """审批操作功能混入类"""

    def approve_step(
        self,
        record_id: int,
        approver_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        审批通过

        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()

        if not record:
            raise ValueError("审批记录不存在")

        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法审批")

        # 获取当前步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()

        if not step:
            raise ValueError("当前审批步骤不存在")

        # 验证审批人权限
        if not self._validate_approver(step, approver_id):
            from app.models.user import User
            approver = self.db.query(User).filter(User.id == approver_id).first()
            approver_name = approver.real_name if approver else str(approver_id)
            required = step.approver_role or f"指定审批人({step.approver_id})"
            raise ValueError(f"用户 {approver_name} 无权限审批此步骤，需要: {required}")

        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.APPROVE,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)

        # 检查是否还有下一步
        next_step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step + 1
            )
        ).first()

        if next_step:
            # 还有下一步，更新当前步骤
            record.current_step += 1
        else:
            # 没有下一步，审批完成
            record.status = ApprovalRecordStatusEnum.APPROVED

        self.db.commit()
        self.db.refresh(record)

        return record

    def reject_step(
        self,
        record_id: int,
        approver_id: int,
        comment: str
    ) -> ApprovalRecord:
        """
        审批驳回

        Args:
            record_id: 审批记录ID
            approver_id: 审批人ID
            comment: 驳回原因（必填）

        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        if not comment:
            raise ValueError("驳回原因不能为空")

        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()

        if not record:
            raise ValueError("审批记录不存在")

        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法驳回")

        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.REJECT,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)

        # 更新状态为驳回
        record.status = ApprovalRecordStatusEnum.REJECTED

        self.db.commit()
        self.db.refresh(record)

        return record

    def delegate_step(
        self,
        record_id: int,
        approver_id: int,
        delegate_to_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        审批委托

        Args:
            record_id: 审批记录ID
            approver_id: 原审批人ID
            delegate_to_id: 委托给的用户ID
            comment: 委托说明

        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()

        if not record:
            raise ValueError("审批记录不存在")

        # 获取当前步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()

        if not step or not step.can_delegate:
            raise ValueError("当前步骤不允许委托")

        # 创建审批历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=approver_id,
            action=ApprovalActionEnum.DELEGATE,
            comment=comment,
            delegate_to_id=delegate_to_id,
            action_at=datetime.now()
        )
        self.db.add(history)

        # 更新当前步骤的审批人（临时）
        step.approver_id = delegate_to_id

        self.db.commit()
        self.db.refresh(record)

        return record

    def withdraw_approval(
        self,
        record_id: int,
        initiator_id: int,
        comment: Optional[str] = None
    ) -> ApprovalRecord:
        """
        撤回审批（在下一级审批前）

        Args:
            record_id: 审批记录ID
            initiator_id: 发起人ID
            comment: 撤回说明

        Returns:
            ApprovalRecord: 更新后的审批记录
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()

        if not record:
            raise ValueError("审批记录不存在")

        if record.initiator_id != initiator_id:
            raise ValueError("只有发起人才能撤回审批")

        if record.status != ApprovalRecordStatusEnum.PENDING:
            raise ValueError(f"审批记录状态为 {record.status}，无法撤回")

        # 检查是否已有审批历史（除了提交记录）
        has_approval = self.db.query(ApprovalHistory).filter(
            and_(
                ApprovalHistory.approval_record_id == record.id,
                ApprovalHistory.step_order > 0,
                ApprovalHistory.action == ApprovalActionEnum.APPROVE
            )
        ).first()

        if has_approval:
            raise ValueError("已有审批人通过，无法撤回")

        # 创建撤回历史
        history = ApprovalHistory(
            approval_record_id=record.id,
            step_order=record.current_step,
            approver_id=initiator_id,
            action=ApprovalActionEnum.WITHDRAW,
            comment=comment,
            action_at=datetime.now()
        )
        self.db.add(history)

        # 更新状态为已取消
        record.status = ApprovalRecordStatusEnum.CANCELLED

        self.db.commit()
        self.db.refresh(record)

        return record
