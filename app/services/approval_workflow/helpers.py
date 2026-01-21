# -*- coding: utf-8 -*-
"""
审批辅助方法模块
提供审批人权限验证等辅助功能
"""

from sqlalchemy import and_

from app.models.enums import ApprovalActionEnum
from app.models.sales import ApprovalHistory, ApprovalWorkflowStep
from app.models.user import User


class ApprovalHelpersMixin:
    """审批辅助方法功能混入类"""

    def _validate_approver(
        self,
        step: ApprovalWorkflowStep,
        approver_id: int
    ) -> bool:
        """
        验证审批人是否有权限审批当前步骤

        Args:
            step: 审批步骤配置
            approver_id: 审批人ID

        Returns:
            bool: 是否有权限
        """
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver or not approver.is_active:
            return False

        # 超级管理员可以审批所有步骤
        if approver.is_superuser:
            return True

        # 1. 检查是否是指定审批人
        if step.approver_id and step.approver_id == approver_id:
            return True

        # 2. 检查角色匹配
        if step.approver_role:
            # 查询用户的角色
            from app.models.user import Role, UserRole

            user_roles = self.db.query(UserRole).filter(
                UserRole.user_id == approver_id
            ).all()

            role_codes = [ur.role.role_code for ur in user_roles if ur.role]

            # 检查是否有所需角色
            if step.approver_role in role_codes:
                return True

        # 3. 检查是否有委托权限（检查审批历史中是否有委托给当前用户的记录）
        # 如果原审批人将步骤委托给了当前用户
        if step.approver_id and step.approver_id != approver_id:
            delegation_history = self.db.query(ApprovalHistory).filter(
                and_(
                    ApprovalHistory.step_order == step.step_order,
                    ApprovalHistory.action == ApprovalActionEnum.DELEGATE,
                    ApprovalHistory.approver_id == step.approver_id,
                    ApprovalHistory.delegate_to_id == approver_id
                )
            ).first()

            if delegation_history:
                return True

        return False
