# -*- coding: utf-8 -*-
"""
测试 Milestone 状态机
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from app.core.state_machine.milestone import MilestoneStateMachine


class TestMilestoneStateMachine:
    """测试 Milestone 状态机"""

    @pytest.fixture
    def mock_milestone(self):
        """创建模拟的 Milestone 对象"""
        milestone = Mock()
        milestone.id = 1
        milestone.status = "PENDING"
        milestone.milestone_code = "M001"
        milestone.milestone_name = "设计评审"
        milestone.project_id = 100
        milestone.planned_date = date(2025, 2, 1)
        milestone.actual_date = None
        milestone.__class__.__name__ = "ProjectMilestone"
        return milestone

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库会话"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = Mock()
        user.id = 10
        user.name = "测试用户"
        user.username = "testuser"
        user.real_name = "测试用户"
        user.has_permission = Mock(return_value=True)
        return user

    def test_milestone_state_machine_initialization(self, mock_milestone, mock_db):
        """测试状态机初始化"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        assert state_machine.model == mock_milestone
        assert state_machine.db == mock_db
        assert state_machine.state_field == "status"
        assert state_machine.current_state == "PENDING"

    def test_complete_transition(self, mock_milestone, mock_db, mock_user):
        """测试完成里程碑的状态转换 (PENDING → COMPLETED)"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # Mock 业务逻辑方法
        with patch.object(state_machine, '_ensure_can_complete'), \
             patch.object(state_machine, '_auto_trigger_invoice'), \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "COMPLETED",
                current_user=mock_user,
                actual_date=date(2025, 2, 5),
                auto_trigger_invoice=True,
            )

        # 验证
        assert result is True
        assert mock_milestone.status == "COMPLETED"
        assert mock_milestone.actual_date == date(2025, 2, 5)

    def test_complete_transition_without_actual_date(self, mock_milestone, mock_db, mock_user):
        """测试完成里程碑但不提供实际日期（应使用今天）"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # Mock 业务逻辑方法
        with patch.object(state_machine, '_ensure_can_complete'), \
             patch.object(state_machine, '_auto_trigger_invoice'), \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "COMPLETED",
                current_user=mock_user,
                auto_trigger_invoice=True,
            )

        # 验证
        assert result is True
        assert mock_milestone.status == "COMPLETED"
        assert mock_milestone.actual_date == date.today()

    def test_complete_transition_without_invoice_trigger(self, mock_milestone, mock_db, mock_user):
        """测试完成里程碑但不触发开票"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # Mock 业务逻辑方法
        with patch.object(state_machine, '_ensure_can_complete'), \
             patch.object(state_machine, '_auto_trigger_invoice') as mock_invoice, \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "COMPLETED",
                current_user=mock_user,
                auto_trigger_invoice=False,
            )

        # 验证
        assert result is True
        assert mock_milestone.status == "COMPLETED"
        # 验证没有调用开票方法
        mock_invoice.assert_not_called()

    def test_invalid_transition_from_completed(self, mock_milestone, mock_db, mock_user):
        """测试从 COMPLETED 状态无法再次完成"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        mock_milestone.status = "COMPLETED"
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # 尝试从 COMPLETED 再次完成（无效）
        with pytest.raises(InvalidStateTransitionError):
            with patch.object(state_machine, '_ensure_can_complete'), \
                 patch.object(state_machine, '_auto_trigger_invoice'), \
                 patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("COMPLETED", current_user=mock_user)

    def test_get_allowed_transitions(self, mock_milestone, mock_db):
        """测试获取允许的状态转换"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # PENDING 状态允许的转换
        allowed = state_machine.get_allowed_transitions()
        assert "COMPLETED" in allowed

    def test_auto_trigger_invoice_called_when_enabled(self, mock_milestone, mock_db, mock_user):
        """测试启用自动开票时调用开票方法"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # Mock 业务逻辑方法
        with patch.object(state_machine, '_ensure_can_complete'), \
             patch.object(state_machine, '_auto_trigger_invoice') as mock_invoice, \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "COMPLETED",
                current_user=mock_user,
                auto_trigger_invoice=True,  # 启用自动开票
            )

        # 验证开票方法被调用
        mock_invoice.assert_called_once()

    def test_ensure_can_complete_validation(self, mock_milestone, mock_db, mock_user):
        """测试完成前验证逻辑"""
        state_machine = MilestoneStateMachine(mock_milestone, mock_db)

        # Mock 业务逻辑方法
        with patch.object(state_machine, '_ensure_can_complete') as mock_check, \
             patch.object(state_machine, '_auto_trigger_invoice'), \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "COMPLETED",
                current_user=mock_user,
            )

        # 验证完成前检查被调用
        mock_check.assert_called_once()


def test_milestone_state_machine_import():
    """测试 MilestoneStateMachine 可以正确导入"""
    from app.core.state_machine.milestone import MilestoneStateMachine

    assert MilestoneStateMachine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
