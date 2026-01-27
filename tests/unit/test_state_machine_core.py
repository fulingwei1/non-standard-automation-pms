# -*- coding: utf-8 -*-
"""
状态机框架增强功能单元测试（简化版）

只测试核心逻辑，不依赖数据库
"""

import pytest
from unittest.mock import Mock, patch


class TestStateMachinePermissionChecker:
    """StateMachinePermissionChecker 权限检查测试"""

    def test_no_permission_required(self):
        """测试无权限要求时直接通过"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        user = Mock()
        has_perm, reason = StateMachinePermissionChecker.check_permission(user)

        assert has_perm is True
        assert reason == ""

    def test_permission_check_without_user(self):
        """测试需要权限但未提供用户时拒绝"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=None, required_permission="issue:assign"
        )

        assert has_perm is False
        assert "未提供操作人信息" in reason

    def test_permission_check_with_has_permission_method(self):
        """测试使用 has_permission 方法的权限检查"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟有权限的用户
        user_with_permission = Mock()
        user_with_permission.has_permission = Mock(return_value=True)

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_with_permission, required_permission="issue:assign"
        )

        assert has_perm is True
        assert reason == ""
        user_with_permission.has_permission.assert_called_once_with("issue:assign")

        # 模拟无权限的用户
        user_without_permission = Mock()
        user_without_permission.has_permission = Mock(return_value=False)

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_without_permission, required_permission="issue:assign"
        )

        assert has_perm is False
        assert "缺少权限: issue:assign" in reason

    def test_permission_check_with_permissions_attribute(self):
        """测试使用 permissions 属性的权限检查"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟有权限的用户（使用列表）
        user_with_permission = Mock()
        user_with_permission.permissions = ["issue:assign", "issue:close"]
        del user_with_permission.has_permission  # 确保没有 has_permission 方法

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_with_permission, required_permission="issue:assign"
        )

        assert has_perm is True
        assert reason == ""

        # 模拟无权限的用户
        user_without_permission = Mock()
        user_without_permission.permissions = ["issue:view"]
        del user_without_permission.has_permission

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_without_permission, required_permission="issue:assign"
        )

        assert has_perm is False
        assert "缺少权限: issue:assign" in reason

    def test_role_check_with_has_role_method(self):
        """测试使用 has_role 方法的角色检查"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟有角色的用户
        user_with_role = Mock()
        user_with_role.has_role = Mock(return_value=True)

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_with_role, required_role="PROJECT_MANAGER"
        )

        assert has_perm is True
        assert reason == ""
        user_with_role.has_role.assert_called_once_with("PROJECT_MANAGER")

    def test_hybrid_permission_and_role_check(self):
        """测试同时检查权限和角色"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟同时有权限和角色的用户
        user = Mock()
        user.has_permission = Mock(return_value=True)
        user.has_role = Mock(return_value=True)

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user,
            required_permission="ecn:approve",
            required_role="PROJECT_MANAGER",
        )

        assert has_perm is True
        assert reason == ""

        # 有权限但无角色
        user2 = Mock()
        user2.has_permission = Mock(return_value=True)
        user2.has_role = Mock(return_value=False)

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user2,
            required_permission="ecn:approve",
            required_role="PROJECT_MANAGER",
        )

        assert has_perm is False
        assert "缺少角色" in reason


class TestStateMachineNotifier:
    """StateMachineNotifier 通知服务测试"""

    def test_resolve_creator_recipient(self):
        """测试解析创建人接收者"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        # 测试 created_by_id 字段
        entity = Mock(spec=['created_by_id'])
        entity.created_by_id = 10

        recipients = notifier.resolve_notification_recipients(entity, ["creator"])
        assert recipients == [10]

        # 测试 created_by 关系
        entity2 = Mock(spec=['created_by'])
        creator = Mock()
        creator.id = 20
        entity2.created_by = creator

        recipients = notifier.resolve_notification_recipients(entity2, ["creator"])
        assert recipients == [20]

    def test_resolve_multiple_recipient_types(self):
        """测试解析多种接收人类型"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        entity = Mock()
        entity.created_by_id = 10
        entity.assignee_id = 20
        entity.reporter_id = 30

        recipients = notifier.resolve_notification_recipients(
            entity, ["creator", "assignee", "reporter"]
        )

        assert set(recipients) == {10, 20, 30}

    def test_build_notification_content_default(self):
        """测试构建默认通知内容"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        entity = Mock()
        entity.title = "测试问题"

        operator = Mock()
        operator.name = "张三"

        title, content = notifier.build_notification_content(
            entity_type="ISSUE",
            entity=entity,
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator=operator,
        )

        assert "ISSUE" in title
        assert "状态变更" in title
        assert "测试问题" in content
        assert "OPEN" in content
        assert "IN_PROGRESS" in content
        assert "张三" in content

    def test_build_entity_link(self):
        """测试构建实体跳转链接"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        link = notifier._build_entity_link("ISSUE", 123)
        assert link == "/issues/123"

        link = notifier._build_entity_link("ECN", 456)
        assert link == "/ecn/456"

        link = notifier._build_entity_link("PROJECT", 789)
        assert link == "/projects/789"


class TestStateMachineEnhanced:
    """StateMachine 基类增强功能测试"""

    def test_transition_decorator_attributes(self):
        """测试 @transition 装饰器添加的属性"""
        from app.core.state_machine.decorators import transition

        @transition(
            from_state="OPEN",
            to_state="IN_PROGRESS",
            required_permission="issue:assign",
            required_role="DEVELOPER",
            action_type="ASSIGN",
            notify_users=["assignee"],
            notification_template="issue_assigned",
        )
        def mock_transition(self, from_state, to_state, **kwargs):
            pass

        # 验证装饰器添加的属性
        assert mock_transition._is_transition is True
        assert mock_transition._from_state == "OPEN"
        assert mock_transition._to_state == "IN_PROGRESS"
        assert mock_transition._required_permission == "issue:assign"
        assert mock_transition._required_role == "DEVELOPER"
        assert mock_transition._action_type == "ASSIGN"
        assert mock_transition._notify_users == ["assignee"]
        assert mock_transition._notification_template == "issue_assigned"

    def test_backward_compatibility_decorator(self):
        """测试装饰器向后兼容性（所有新参数可选）"""
        from app.core.state_machine.decorators import transition

        # 只使用旧参数
        @transition(from_state="OPEN", to_state="CLOSED")
        def simple_transition(self, from_state, to_state, **kwargs):
            pass

        assert simple_transition._is_transition is True
        assert simple_transition._from_state == "OPEN"
        assert simple_transition._to_state == "CLOSED"
        # 新参数应该是 None
        assert simple_transition._required_permission is None
        assert simple_transition._required_role is None
        assert simple_transition._action_type is None
        assert simple_transition._notify_users is None

    def test_get_entity_type_and_id(self):
        """测试获取实体类型和ID"""
        from app.core.state_machine.base import StateMachine

        mock_issue = Mock()
        mock_issue.id = 1
        mock_issue.status = "OPEN"
        mock_issue.__class__.__name__ = "Issue"

        mock_db = Mock()
        state_machine = StateMachine(mock_issue, mock_db)

        # 测试获取实体类型
        entity_type = state_machine._get_entity_type()
        assert entity_type == "ISSUE"

        # 测试获取实体ID
        entity_id = state_machine._get_entity_id()
        assert entity_id == 1

    def test_permission_integration_in_transition(self):
        """测试状态转换中的权限集成"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition
        from app.core.state_machine.exceptions import PermissionDeniedError

        class TestStateMachine(StateMachine):
            @transition(
                from_state="DRAFT",
                to_state="PUBLISHED",
                required_permission="content:publish",
            )
            def publish(self, from_state, to_state, **kwargs):
                pass

        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.status = "DRAFT"
        mock_entity.__class__.__name__ = "Content"

        mock_db = Mock()
        state_machine = TestStateMachine(mock_entity, mock_db)

        # 测试无权限用户被拒绝
        user_without_permission = Mock()
        user_without_permission.has_permission = Mock(return_value=False)

        with pytest.raises(PermissionDeniedError) as exc_info:
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to(
                    "PUBLISHED", current_user=user_without_permission
                )

        assert "缺少权限" in str(exc_info.value)

    def test_backward_compatibility_without_current_user(self):
        """测试向后兼容性（不传 current_user 参数）"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition

        class TestStateMachine(StateMachine):
            @transition(from_state="OPEN", to_state="CLOSED")
            def close(self, from_state, to_state, **kwargs):
                pass

        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.status = "OPEN"
        mock_entity.__class__.__name__ = "Task"

        mock_db = Mock()
        state_machine = TestStateMachine(mock_entity, mock_db)

        # 不传 current_user（向后兼容）
        result = state_machine.transition_to("CLOSED")

        assert result is True
        assert mock_entity.status == "CLOSED"


def test_state_machine_imports():
    """测试所有状态机模块都能正确导入"""
    # 基础组件
    from app.core.state_machine.base import StateMachine
    from app.core.state_machine.decorators import transition
    from app.core.state_machine.exceptions import (
        PermissionDeniedError,
    )
    from app.core.state_machine.permissions import StateMachinePermissionChecker
    from app.core.state_machine.notifications import StateMachineNotifier

    # 验证类存在
    assert StateMachine is not None
    assert transition is not None
    assert StateMachinePermissionChecker is not None
    assert StateMachineNotifier is not None
    assert PermissionDeniedError is not None


def test_state_transition_log_model_import():
    """测试 StateTransitionLog 模型可以导入"""
    from app.models.state_machine import StateTransitionLog

    # 验证模型类存在
    assert StateTransitionLog is not None
    assert hasattr(StateTransitionLog, '__tablename__')
    assert StateTransitionLog.__tablename__ == 'state_transition_logs'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
