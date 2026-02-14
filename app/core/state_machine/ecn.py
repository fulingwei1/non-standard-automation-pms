# -*- coding: utf-8 -*-
"""
ECN状态机实现

工程变更通知（ECN）状态机，基于状态机框架实现

状态定义（来自 EcnStatusEnum）：
- DRAFT: 草稿
- PENDING_REVIEW: 待审核
- APPROVED: 已批准
- REJECTED: 已拒绝
- IMPLEMENTED: 已实施
- CANCELLED: 已取消
"""

import logging

from app.core.state_machine import StateMachine
from app.core.state_machine.decorators import (
    transition,
    before_transition,
    after_transition,
)

logger = logging.getLogger(__name__)

# 定义状态常量（字符串）
DRAFT = "DRAFT"
PENDING_REVIEW = "PENDING_REVIEW"
APPROVED = "APPROVED"
REJECTED = "REJECTED"
IMPLEMENTED = "IMPLEMENTED"
COMPLETED = "COMPLETED"
CANCELLED = "CANCELLED"

# 状态转换到操作类型的映射
TRANSITION_ACTION_MAP = {
    (DRAFT, PENDING_REVIEW): "SUBMIT",
    (DRAFT, CANCELLED): "CANCEL",
    (PENDING_REVIEW, APPROVED): "APPROVE",
    (PENDING_REVIEW, REJECTED): "REJECT",
    (APPROVED, IMPLEMENTED): "IMPLEMENT",
    (IMPLEMENTED, COMPLETED): "COMPLETE",
    (IMPLEMENTED, CANCELLED): "CANCEL_IMPLEMENTED",
    (COMPLETED, CANCELLED): "CANCEL_COMPLETED",
    (REJECTED, DRAFT): "REVISE",
    (REJECTED, CANCELLED): "CANCEL",
}

# 状态中文标签
STATUS_LABELS = {
    DRAFT: "草稿",
    PENDING_REVIEW: "待审核",
    APPROVED: "已批准",
    REJECTED: "已拒绝",
    IMPLEMENTED: "已实施",
    COMPLETED: "已完成",
    CANCELLED: "已取消",
}


class EcnStateMachine(StateMachine):
    """
    ECN状态机

    状态转换规则：
    DRAFT → PENDING_REVIEW: 提交审核
    DRAFT → CANCELLED: 取消变更
    PENDING_REVIEW → APPROVED: 审批通过
    PENDING_REVIEW → REJECTED: 审批拒绝
    APPROVED → IMPLEMENTED: 执行变更
    REJECTED → DRAFT: 重新编辑
    REJECTED → CANCELLED: 放弃变更
    IMPLEMENTED → COMPLETED: 验证完成（如果需要）
    """

    def __init__(self, model, db):
        super().__init__(model, db, state_field="status")

    # ==================== DRAFT 状态转换 ====================

    @transition(from_state=DRAFT, to_state=PENDING_REVIEW)
    def submit_for_review(self, from_state, to_state, **kwargs):
        """
        提交审核

        验证条件：
        - 必须填写变更原因和变更描述
        - 必须选择变更类型
        - 必须指定来源（项目/设备/订单）
        """
        if not self.model.change_reason:
            raise ValueError("变更原因不能为空")
        if not self.model.change_description:
            raise ValueError("变更描述不能为空")
        if not self.model.ecn_type:
            raise ValueError("变更类型不能为空")

    @transition(from_state=DRAFT, to_state=CANCELLED)
    def cancel_draft(self, from_state, to_state, **kwargs):
        """
        取消草稿

        验证条件：
        - 无（草稿状态可以随时取消）
        """

    @transition(from_state=PENDING_REVIEW, to_state=CANCELLED)
    def cancel_pending_review(self, from_state, to_state, **kwargs):
        """
        取消待审核的ECN

        验证条件：
        - 无（待审核状态可以取消）
        """

    # ==================== PENDING_REVIEW 状态转换 ====================

    @transition(from_state=PENDING_REVIEW, to_state=APPROVED)
    def approve(self, from_state, to_state, **kwargs):
        """
        审批通过

        验证条件：
        - 必须填写审批意见
        - 必须有审批人
        """
        if not self.model.approval_note:
            raise ValueError("审批意见不能为空")
        if not self.model.approved_at:
            raise ValueError("审批时间必须设置")

    @transition(from_state=PENDING_REVIEW, to_state=REJECTED)
    def reject(self, from_state, to_state, **kwargs):
        """
        审批拒绝

        验证条件：
        - 必须填写拒绝原因（approval_note）
        """
        if not self.model.approval_note:
            raise ValueError("拒绝原因不能为空")

    # ==================== APPROVED 状态转换 ====================

    @transition(from_state=APPROVED, to_state=IMPLEMENTED)
    def implement(self, from_state, to_state, **kwargs):
        """
        执行变更

        验证条件：
        - 必须设置执行开始时间
        """
        from datetime import datetime

        if not self.model.execution_start:
            self.model.execution_start = datetime.now()

    # ==================== REJECTED 状态转换 ====================

    @transition(from_state=REJECTED, to_state=DRAFT)
    def revise(self, from_state, to_state, **kwargs):
        """
        重新编辑

        验证条件：
        - 无（被拒绝的ECN可以重新编辑）
        """

    @transition(from_state=REJECTED, to_state=CANCELLED)
    def cancel_rejected(self, from_state, to_state, **kwargs):
        """
        放弃变更

        验证条件：
        - 必须填写根本原因分析（可选）
        """

    # ==================== IMPLEMENTED 状态转换 ====================

    @transition(from_state=IMPLEMENTED, to_state=COMPLETED)
    def complete(self, from_state, to_state, **kwargs):
        """
        完成变更验证

        验证条件：
        - 必须填写执行说明
        """
        from datetime import datetime

        if not self.model.execution_note:
            raise ValueError("执行说明不能为空")
        if not self.model.execution_end:
            self.model.execution_end = datetime.now()

    @transition(from_state=IMPLEMENTED, to_state=CANCELLED)
    def cancel_implemented(self, from_state, to_state, **kwargs):
        """
        取消已实施的变更

        验证条件：
        - 需要特殊权限（ecn:cancel_implemented）- 可选
        """
        # 检查用户权限：取消已实施的ECN需要特殊权限
        current_user = kwargs.get("current_user")
        if current_user:
            try:
                from app.core.auth import check_permission

                # 检查是否有取消已实施ECN的权限
                if not check_permission(current_user, "ecn:cancel_implemented", self.db):
                    # 也检查是否为超级管理员
                    if not getattr(current_user, "is_superuser", False):
                        raise PermissionError("取消已实施的ECN需要特殊权限（ecn:cancel_implemented）")
            except ImportError:
                pass

    # ==================== COMPLETED 状态转换 ====================

    @transition(from_state=COMPLETED, to_state=CANCELLED)
    def cancel_completed(self, from_state, to_state, **kwargs):
        """
        取消已完成的变更

        验证条件：
        - 无（已完成的ECN可以取消）
        """

    # ==================== 钩子函数 ====================

    @before_transition
    def log_transition_start(self, from_state, to_state, **kwargs):
        """
        状态转换开始前的钩子

        用于：
        - 记录转换开始日志
        - 发送通知
        - 检查权限
        """
        self._log_transition(f"状态转换开始: {from_state} → {to_state}", **kwargs)

    @after_transition
    def log_transition_complete(self, from_state, to_state, **kwargs):
        """
        状态转换完成后的钩子

        用于：
        - 记录转换完成日志
        - 发送通知给相关人员
        - 更新相关数据
        """
        self._log_transition(f"状态转换完成: {from_state} → {to_state}", **kwargs)
        self._update_change_log(from_state, to_state, **kwargs)

    def _log_transition(self, message: str, **kwargs):
        """
        记录转换日志（内部方法）

        Args:
            message: 日志消息
            **kwargs: 额外参数（可包含 current_user）
        """
        try:
            from app.models.ecn import EcnLog

            # 获取操作用户ID
            current_user = kwargs.get("current_user")
            created_by = current_user.id if current_user and hasattr(current_user, "id") else None

            # 创建日志记录
            log_entry = EcnLog(
                ecn_id=self.model.id,
                log_type="TRANSITION",
                log_action="STATE_TRANSITION",
                log_content=message,
                created_by=created_by,
            )

            self.db.add(log_entry)
            # 不在这里提交，让外层事务统一管理
        except Exception as e:
            # 记录日志失败不应影响主业务流程
            logger.warning("ECN状态转换日志记录失败: %s", e)

    def _update_change_log(self, from_state: str, to_state: str, **kwargs):
        """
        更新ECN变更日志（内部方法）

        记录到ECN专用的日志表，包含更详细的业务信息。

        Args:
            from_state: 原状态
            to_state: 目标状态
            **kwargs: 额外参数（可包含 current_user）
        """
        try:
            from app.models.ecn import EcnLog

            # 获取操作用户ID
            current_user = kwargs.get("current_user")
            created_by = current_user.id if current_user and hasattr(current_user, "id") else None

            # 构建日志内容
            from_label = STATUS_LABELS.get(from_state, from_state)
            to_label = STATUS_LABELS.get(to_state, to_state)
            log_content = f"ECN状态从【{from_label}】变更为【{to_label}】"

            # 创建变更日志记录
            log_entry = EcnLog(
                ecn_id=self.model.id,
                log_type="STATUS_CHANGE",
                log_action=f"{from_state}_TO_{to_state}",
                old_status=from_state,
                new_status=to_state,
                log_content=log_content,
                created_by=created_by,
            )

            self.db.add(log_entry)
            # 不在这里提交，让外层事务统一管理
        except Exception as e:
            # 记录日志失败不应影响主业务流程
            logger.warning("ECN变更日志更新失败: %s", e)

    # ==================== 辅助方法 ====================

    def get_next_states(self):
        """
        获取当前状态允许的下一状态

        Returns:
            List[str]: 允许的状态列表
        """
        return self.get_allowed_transitions()

    def is_editable(self):
        """
        检查ECN是否可以编辑

        Returns:
            bool: 是否可以编辑
        """
        return self.current_state in [
            DRAFT,
            REJECTED,
        ]

    def is_cancellable(self):
        """
        检查ECN是否可以取消

        Returns:
            bool: 是否可以取消
        """
        return self.current_state in [
            DRAFT,
            PENDING_REVIEW,
            REJECTED,
            IMPLEMENTED,
            COMPLETED,
        ]

    def get_status_label(self):
        """
        获取当前状态的中文标签

        Returns:
            str: 状态中文标签
        """
        return STATUS_LABELS.get(self.current_state, "未知状态")
