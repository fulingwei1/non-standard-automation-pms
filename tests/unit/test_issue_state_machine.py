# -*- coding: utf-8 -*-
"""
测试 Issue 状态机迁移
"""

import pytest
from unittest.mock import Mock, patch

from app.core.state_machine.issue import IssueStateMachine


class TestIssueStateMachine:
    """测试 Issue 状态机"""

    @pytest.fixture
    def mock_issue(self):
        """创建模拟的 Issue 对象"""
        issue = Mock()
        issue.id = 1
        issue.status = "OPEN"
        issue.issue_no = "ISS-001"
        issue.title = "测试问题"
        issue.is_blocking = False
        issue.project_id = None
        issue.category = "BUG"
        issue.issue_type = "BUG"
        issue.__class__.__name__ = "Issue"
        return issue

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

    def test_issue_state_machine_initialization(self, mock_issue, mock_db):
        """测试状态机初始化"""
        state_machine = IssueStateMachine(mock_issue, mock_db)

        assert state_machine.model == mock_issue
        assert state_machine.db == mock_db
        assert state_machine.state_field == "status"
        assert state_machine.current_state == "OPEN"

    def test_assign_transition(self, mock_issue, mock_db, mock_user):
        """测试分配问题的状态转换 (OPEN → IN_PROGRESS)"""
        state_machine = IssueStateMachine(mock_issue, mock_db)

        # 执行转换
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "IN_PROGRESS",
                current_user=mock_user,
                assignee_id=20,
                assignee_name="新负责人",
                due_date="2025-02-01",
            )

        # 验证
        assert result is True
        assert mock_issue.status == "IN_PROGRESS"
        assert mock_issue.assignee_id == 20
        assert mock_issue.assignee_name == "新负责人"

    def test_resolve_transition(self, mock_issue, mock_db, mock_user):
        """测试解决问题的状态转换 (IN_PROGRESS → RESOLVED)"""
        mock_issue.status = "IN_PROGRESS"
        state_machine = IssueStateMachine(mock_issue, mock_db)

        # 执行转换
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "RESOLVED",
                current_user=mock_user,
                solution="已修复",
                resolved_by=10,
                resolved_by_name="测试用户",
            )

        # 验证
        assert result is True
        assert mock_issue.status == "RESOLVED"
        assert mock_issue.solution == "已修复"
        assert mock_issue.resolved_by == 10
        assert mock_issue.resolved_at is not None

    def test_verify_pass_transition(self, mock_issue, mock_db, mock_user):
        """测试验证通过的状态转换 (RESOLVED → CLOSED)"""
        mock_issue.status = "RESOLVED"
        state_machine = IssueStateMachine(mock_issue, mock_db)

        # 执行转换
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "CLOSED",
                current_user=mock_user,
                verified_by=10,
                verified_by_name="测试用户",
            )

        # 验证
        assert result is True
        assert mock_issue.status == "CLOSED"
        assert mock_issue.verified_result == "VERIFIED"
        assert mock_issue.verified_at is not None

    def test_verify_fail_transition(self, mock_issue, mock_db, mock_user):
        """测试验证失败的状态转换 (RESOLVED → IN_PROGRESS)"""
        mock_issue.status = "RESOLVED"
        state_machine = IssueStateMachine(mock_issue, mock_db)

        # 执行转换
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "IN_PROGRESS",
                current_user=mock_user,
                verified_by=10,
                verified_by_name="测试用户",
            )

        # 验证
        assert result is True
        assert mock_issue.status == "IN_PROGRESS"
        assert mock_issue.verified_result == "FAILED"

    def test_invalid_transition(self, mock_issue, mock_db, mock_user):
        """测试无效的状态转换"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        state_machine = IssueStateMachine(mock_issue, mock_db)

        # 尝试从 OPEN 直接到 RESOLVED（无效）
        with pytest.raises(InvalidStateTransitionError):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("RESOLVED", current_user=mock_user)

    def test_get_allowed_transitions(self, mock_issue, mock_db):
        """测试获取允许的状态转换"""
        state_machine = IssueStateMachine(mock_issue, mock_db)

        # OPEN 状态允许的转换
        allowed = state_machine.get_allowed_transitions()
        assert "IN_PROGRESS" in allowed
        assert "CLOSED" in allowed

    def test_blocking_issue_closes_alerts(self, mock_issue, mock_db, mock_user):
        """测试阻塞问题解决时关闭预警"""
        mock_issue.status = "IN_PROGRESS"
        mock_issue.is_blocking = True

        state_machine = IssueStateMachine(mock_issue, mock_db)

        # Mock 关闭预警的方法
        with patch.object(state_machine, '_close_blocking_alerts') as mock_close, \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "RESOLVED",
                current_user=mock_user,
                solution="已修复",
                resolved_by=10,
                resolved_by_name="测试用户",
            )

        # 验证关闭预警被调用
        mock_close.assert_called_once()


def test_issue_state_machine_import():
    """测试 IssueStateMachine 可以正确导入"""
    from app.core.state_machine.issue import IssueStateMachine

    assert IssueStateMachine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
