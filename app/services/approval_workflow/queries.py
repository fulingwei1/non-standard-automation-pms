# -*- coding: utf-8 -*-
"""
审批查询模块
提供审批记录和历史的查询功能
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_

from app.models.sales import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflowStep,
)


class ApprovalQueriesMixin:
    """审批查询功能混入类"""

    def get_current_step(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取当前审批步骤信息

        Args:
            record_id: 审批记录ID

        Returns:
            Optional[Dict[str, Any]]: 当前步骤信息
        """
        record = self.db.query(ApprovalRecord).filter(
            ApprovalRecord.id == record_id
        ).first()

        if not record:
            return None

        # 获取工作流步骤
        step = self.db.query(ApprovalWorkflowStep).filter(
            and_(
                ApprovalWorkflowStep.workflow_id == record.workflow_id,
                ApprovalWorkflowStep.step_order == record.current_step
            )
        ).first()

        if not step:
            return None

        return {
            "step_order": step.step_order,
            "step_name": step.step_name,
            "approver_role": step.approver_role,
            "approver_id": step.approver_id,
            "is_required": step.is_required,
            "can_delegate": step.can_delegate,
            "can_withdraw": step.can_withdraw,
            "due_hours": step.due_hours
        }

    def get_approval_history(self, record_id: int) -> List[ApprovalHistory]:
        """
        获取审批历史

        Args:
            record_id: 审批记录ID

        Returns:
            List[ApprovalHistory]: 审批历史列表
        """
        return self.db.query(ApprovalHistory).filter(
            ApprovalHistory.approval_record_id == record_id
        ).order_by(ApprovalHistory.step_order, ApprovalHistory.action_at).all()

    def get_approval_record(
        self,
        entity_type: str,
        entity_id: int
    ) -> Optional[ApprovalRecord]:
        """
        获取实体的审批记录

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            Optional[ApprovalRecord]: 审批记录，如果没有则返回None
        """
        return self.db.query(ApprovalRecord).filter(
            and_(
                ApprovalRecord.entity_type == entity_type,
                ApprovalRecord.entity_id == entity_id
            )
        ).order_by(ApprovalRecord.created_at.desc()).first()
