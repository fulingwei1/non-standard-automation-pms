# -*- coding: utf-8 -*-
"""
测试 Acceptance 状态机
"""

import pytest
from unittest.mock import Mock, patch

from app.core.state_machine.acceptance import AcceptanceStateMachine


class TestAcceptanceStateMachine:
    """测试 Acceptance 状态机"""

    @pytest.fixture
    def mock_order(self):
        """创建模拟的 AcceptanceOrder 对象"""
        order = Mock()
        order.id = 1
        order.status = "DRAFT"
        order.order_no = "ACC-001"
        order.acceptance_type = "FAT"
        order.total_items = 10
        order.actual_start_date = None
        order.actual_end_date = None
        order.overall_result = None
        order.conclusion = None
        order.conditions = None
        order.location = None
        order.__class__.__name__ = "AcceptanceOrder"
        return order

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

    def test_acceptance_state_machine_initialization(self, mock_order, mock_db):
        """测试状态机初始化"""
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        assert state_machine.model == mock_order
        assert state_machine.db == mock_db
        assert state_machine.state_field == "status"
        assert state_machine.current_state == "DRAFT"

    def test_submit_transition(self, mock_order, mock_db, mock_user):
        """测试提交转换 (DRAFT → PENDING)"""
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "PENDING",
                current_user=mock_user,
            )

        assert result is True
        assert mock_order.status == "PENDING"

    def test_submit_fails_without_items(self, mock_order, mock_db, mock_user):
        """测试没有检查项时提交失败"""
        mock_order.total_items = 0
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        with pytest.raises(ValueError, match="验收单没有检查项"):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("PENDING", current_user=mock_user)

    def test_start_from_draft(self, mock_order, mock_db, mock_user):
        """测试从草稿直接开始 (DRAFT → IN_PROGRESS)"""
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "IN_PROGRESS",
                current_user=mock_user,
                location="工厂车间",
            )

        assert result is True
        assert mock_order.status == "IN_PROGRESS"
        assert mock_order.actual_start_date is not None
        assert mock_order.location == "工厂车间"

    def test_start_from_pending(self, mock_order, mock_db, mock_user):
        """测试从待验收开始 (PENDING → IN_PROGRESS)"""
        mock_order.status = "PENDING"
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "IN_PROGRESS",
                current_user=mock_user,
            )

        assert result is True
        assert mock_order.status == "IN_PROGRESS"
        assert mock_order.actual_start_date is not None

    def test_complete_pass(self, mock_order, mock_db, mock_user):
        """测试完成并通过 (IN_PROGRESS → PASSED)"""
        mock_order.status = "IN_PROGRESS"
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        # Mock所有业务逻辑方法
        with patch.object(state_machine, '_validate_required_items'), \
             patch.object(state_machine, '_validate_blocking_issues'), \
             patch.object(state_machine, '_trigger_invoice'), \
             patch.object(state_machine, '_handle_acceptance_status_transition'), \
             patch.object(state_machine, '_handle_progress_integration'), \
             patch.object(state_machine, '_check_auto_stage_transition'), \
             patch.object(state_machine, '_trigger_warranty_period'), \
             patch.object(state_machine, '_trigger_bonus_calculation'), \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "PASSED",
                current_user=mock_user,
                conclusion="验收通过",
                auto_trigger_invoice=True,
            )

        assert result is True
        assert mock_order.status == "PASSED"
        assert mock_order.overall_result == "PASSED"
        assert mock_order.actual_end_date is not None
        assert mock_order.conclusion == "验收通过"

    def test_complete_fail(self, mock_order, mock_db, mock_user):
        """测试完成但失败 (IN_PROGRESS → FAILED)"""
        mock_order.status = "IN_PROGRESS"
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        # Mock业务逻辑方法
        with patch.object(state_machine, '_validate_required_items'), \
             patch.object(state_machine, '_handle_acceptance_status_transition'), \
             patch.object(state_machine, '_handle_progress_integration'), \
             patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "FAILED",
                current_user=mock_user,
                overall_result="CONDITIONAL_PASS",
                conclusion="有条件通过",
                conditions="需整改项目完成后复检",
            )

        assert result is True
        assert mock_order.status == "FAILED"
        assert mock_order.overall_result == "CONDITIONAL_PASS"
        assert mock_order.actual_end_date is not None
        assert mock_order.conclusion == "有条件通过"
        assert mock_order.conditions == "需整改项目完成后复检"

    def test_invalid_transition(self, mock_order, mock_db, mock_user):
        """测试无效的状态转换"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        # 尝试从 DRAFT 直接到 PASSED（无效）
        with pytest.raises(InvalidStateTransitionError):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("PASSED", current_user=mock_user)

    def test_get_allowed_transitions(self, mock_order, mock_db):
        """测试获取允许的状态转换"""
        state_machine = AcceptanceStateMachine(mock_order, mock_db)

        # DRAFT 状态允许的转换
        allowed = state_machine.get_allowed_transitions()
        assert "PENDING" in allowed
        assert "IN_PROGRESS" in allowed

        # IN_PROGRESS 状态允许的转换
        mock_order.status = "IN_PROGRESS"
        state_machine = AcceptanceStateMachine(mock_order, mock_db)
        allowed = state_machine.get_allowed_transitions()
        assert "PASSED" in allowed
        assert "FAILED" in allowed


def test_acceptance_state_machine_import():
    """测试 AcceptanceStateMachine 可以正确导入"""
    from app.core.state_machine.acceptance import AcceptanceStateMachine

    assert AcceptanceStateMachine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
