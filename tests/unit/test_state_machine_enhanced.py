# -*- coding: utf-8 -*-
"""
状态机框架增强功能单元测试

测试覆盖：
- StateTransitionLog 模型创建和查询
- StateMachinePermissionChecker 权限检查
- StateMachineNotifier 通知服务
- StateMachine 基类增强功能
- 向后兼容性验证
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session


class TestStateTransitionLog:
    """StateTransitionLog 模型测试（需要数据库）"""

    @pytest.mark.skip(reason="需要完整的数据库初始化，暂时跳过")
    def test_create_state_transition_log(self, db_session: Session):
        """测试创建状态转换日志"""
        from app.models.state_machine import StateTransitionLog
        from app.models.user import User

        # 创建测试用户
        from app.models.organization import Employee
        emp = Employee(
            employee_code="EMP-SM-001",
            name="test_user",
            department="测试部",
            role="ENGINEER",
            phone="18800000000",
        )
        db_session.add(emp)
        db_session.flush()

        user = User(
            employee_id=emp.id,
            username="test_user",
            email="test@example.com",
            password_hash="hashed_pass",
            real_name="test_user",
        )
        db_session.add(user)
        db_session.commit()

        # 创建状态转换日志
        log = StateTransitionLog(
            entity_type="ISSUE",
            entity_id=123,
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator_id=user.id,
            operator_name="测试用户",
            action_type="ASSIGN",
            comment="分配给开发人员",
        )

        db_session.add(log)
        db_session.commit()

        # 验证
        assert log.id is not None
        assert log.entity_type == "ISSUE"
        assert log.entity_id == 123
        assert log.from_state == "OPEN"
        assert log.to_state == "IN_PROGRESS"
        assert log.operator_id == user.id
        assert log.action_type == "ASSIGN"
        assert log.comment == "分配给开发人员"

    def test_state_transition_log_model_structure(self):
        """测试 StateTransitionLog 模型结构（不需要数据库）"""
        from app.models.state_machine import StateTransitionLog

        # 验证模型类存在
        assert StateTransitionLog is not None
        assert hasattr(StateTransitionLog, '__tablename__')
        assert StateTransitionLog.__tablename__ == 'state_transition_logs'

        # 验证字段存在
        assert hasattr(StateTransitionLog, 'entity_type')
        assert hasattr(StateTransitionLog, 'entity_id')
        assert hasattr(StateTransitionLog, 'from_state')
        assert hasattr(StateTransitionLog, 'to_state')
        assert hasattr(StateTransitionLog, 'operator_id')
        assert hasattr(StateTransitionLog, 'action_type')
        assert hasattr(StateTransitionLog, 'comment')
        assert hasattr(StateTransitionLog, 'extra_data')


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

    def test_role_check_with_roles_attribute(self):
        """测试使用 roles 属性的角色检查（字符串列表）"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟有角色的用户
        user_with_role = Mock()
        user_with_role.roles = ["PROJECT_MANAGER", "DEVELOPER"]
        del user_with_role.has_role

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_with_role, required_role="PROJECT_MANAGER"
        )

        assert has_perm is True
        assert reason == ""

    def test_role_check_with_role_objects(self):
        """测试使用 Role 对象列表的角色检查"""
        from app.core.state_machine.permissions import StateMachinePermissionChecker

        # 模拟 Role 对象
        role1 = Mock()
        role1.name = "PROJECT_MANAGER"
        role2 = Mock()
        role2.name = "DEVELOPER"

        user_with_role = Mock()
        user_with_role.roles = [role1, role2]
        del user_with_role.has_role

        has_perm, reason = StateMachinePermissionChecker.check_permission(
            current_user=user_with_role, required_role="PROJECT_MANAGER"
        )

        assert has_perm is True
        assert reason == ""

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
        entity = Mock()
        entity.created_by_id = 10

        recipients = notifier.resolve_notification_recipients(entity, ["creator"])
        assert recipients == [10]

        # 测试 created_by 关系
        entity2 = Mock()
        del entity2.created_by_id
        creator = Mock()
        creator.id = 20
        entity2.created_by = creator

        recipients = notifier.resolve_notification_recipients(entity2, ["creator"])
        assert recipients == [20]

    def test_resolve_assignee_recipient(self):
        """测试解析负责人接收者"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        entity = Mock()
        entity.assignee_id = 30

        recipients = notifier.resolve_notification_recipients(entity, ["assignee"])
        assert recipients == [30]

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

    def test_resolve_approvers_list(self):
        """测试解析审批人列表"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        approver1 = Mock()
        approver1.id = 40
        approver2 = Mock()
        approver2.id = 50

        entity = Mock()
        entity.approvers = [approver1, approver2]

        recipients = notifier.resolve_notification_recipients(entity, ["approvers"])
        assert set(recipients) == {40, 50}

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

    def test_build_notification_content_with_template(self):
        """测试使用模板构建通知内容"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        entity = Mock()
        entity.title = "ECN-001"

        title, content = notifier.build_notification_content(
            entity_type="ECN",
            entity=entity,
            from_state="DRAFT",
            to_state="PENDING_REVIEW",
            template="ecn_submitted",
        )

        assert "ECN" in title or "已提交" in title
        assert "ECN-001" in content

    @patch("app.core.state_machine.notifications.StateMachineNotifier._notifier")
    def test_send_transition_notification(self, mock_notifier_attr):
        """测试发送状态转换通知"""
        from app.core.state_machine.notifications import StateMachineNotifier

        notifier = StateMachineNotifier()

        # Mock notification service
        mock_notification_service = Mock()
        mock_notification_service.send_notification = Mock(return_value=True)
        notifier.notification_service = mock_notification_service

        db_session = Mock()
        entity = Mock()
        entity.id = 100
        entity.title = "测试问题"
        entity.assignee_id = 20
        entity.reporter_id = 30

        operator = Mock()
        operator.name = "操作员"

        result = notifier.send_transition_notification(
            db=db_session,
            entity=entity,
            entity_type="ISSUE",
            entity_id=100,
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator=operator,
            notify_user_types=["assignee", "reporter"],
        )

        # 应该发送了2次通知（assignee和reporter）
        assert mock_notification_service.send_notification.call_count == 2

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

    @pytest.fixture
    def mock_issue(self):
        """创建模拟的 Issue 对象"""
        issue = Mock()
        issue.id = 1
        issue.status = "OPEN"
        issue.title = "测试问题"
        issue.__class__.__name__ = "Issue"
        return issue

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟的数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = Mock()
        user.id = 10
        user.name = "测试用户"
        user.has_permission = Mock(return_value=True)
        user.has_role = Mock(return_value=True)
        return user

    def test_transition_with_permission_check_success(
        self, mock_issue, mock_db_session, mock_user
    ):
        """测试带权限检查的状态转换（成功）"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition

        class IssueStateMachine(StateMachine):
            @transition(
                from_state="OPEN",
                to_state="IN_PROGRESS",
                required_permission="issue:assign",
            )
            def assign(self, from_state, to_state, **kwargs):
                pass

        state_machine = IssueStateMachine(mock_issue, mock_db_session)

        # 执行转换（应该成功）
        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "IN_PROGRESS", current_user=mock_user
            )

        assert result is True
        assert mock_issue.status == "IN_PROGRESS"
        mock_user.has_permission.assert_called_with("issue:assign")

    def test_transition_with_permission_check_failure(
        self, mock_issue, mock_db_session
    ):
        """测试带权限检查的状态转换（失败）"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition
        from app.core.state_machine.exceptions import PermissionDeniedError

        class IssueStateMachine(StateMachine):
            @transition(
                from_state="OPEN",
                to_state="IN_PROGRESS",
                required_permission="issue:assign",
            )
            def assign(self, from_state, to_state, **kwargs):
                pass

        state_machine = IssueStateMachine(mock_issue, mock_db_session)

        # 创建无权限的用户
        user_without_permission = Mock()
        user_without_permission.has_permission = Mock(return_value=False)

        # 执行转换（应该失败）
        with pytest.raises(PermissionDeniedError) as exc_info:
            state_machine.transition_to(
                "IN_PROGRESS", current_user=user_without_permission
            )

        assert "缺少权限" in str(exc_info.value)
        assert mock_issue.status == "OPEN"  # 状态未改变

    def test_transition_creates_audit_log(self, mock_issue, mock_db_session, mock_user):
        """测试状态转换创建审计日志"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition

        class IssueStateMachine(StateMachine):
            @transition(
                from_state="OPEN",
                to_state="IN_PROGRESS",
                action_type="ASSIGN",
            )
            def assign(self, from_state, to_state, **kwargs):
                pass

        state_machine = IssueStateMachine(mock_issue, mock_db_session)

        with patch.object(state_machine, '_create_audit_log') as mock_create_log, \
             patch.object(state_machine, '_send_notifications'):
            state_machine.transition_to(
                "IN_PROGRESS",
                current_user=mock_user,
                comment="分配给开发人员",
            )

        # 验证审计日志被创建
        mock_create_log.assert_called_once_with(
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator=mock_user,
            action_type="ASSIGN",
            comment="分配给开发人员",
        )

    def test_transition_sends_notifications(self, mock_issue, mock_db_session, mock_user):
        """测试状态转换发送通知"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition

        class IssueStateMachine(StateMachine):
            @transition(
                from_state="OPEN",
                to_state="IN_PROGRESS",
                notify_users=["assignee", "reporter"],
                notification_template="issue_status_changed",
            )
            def assign(self, from_state, to_state, **kwargs):
                pass

        state_machine = IssueStateMachine(mock_issue, mock_db_session)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications') as mock_send:
            state_machine.transition_to("IN_PROGRESS", current_user=mock_user)

        # 验证通知被发送
        mock_send.assert_called_once_with(
            from_state="OPEN",
            to_state="IN_PROGRESS",
            operator=mock_user,
            notify_user_types=["assignee", "reporter"],
            template="issue_status_changed",
        )

    def test_backward_compatibility(self, mock_issue, mock_db_session):
        """测试向后兼容性（不传 current_user）"""
        from app.core.state_machine.base import StateMachine
        from app.core.state_machine.decorators import transition

        class IssueStateMachine(StateMachine):
            @transition(from_state="OPEN", to_state="IN_PROGRESS")
            def assign(self, from_state, to_state, **kwargs):
                pass

        state_machine = IssueStateMachine(mock_issue, mock_db_session)

        # 不传 current_user（向后兼容）
        result = state_machine.transition_to("IN_PROGRESS")

        assert result is True
        assert mock_issue.status == "IN_PROGRESS"

    def test_get_entity_type(self, mock_issue, mock_db_session):
        """测试获取实体类型"""
        from app.core.state_machine.base import StateMachine

        state_machine = StateMachine(mock_issue, mock_db_session)
        entity_type = state_machine._get_entity_type()

        assert entity_type == "ISSUE"

    def test_get_entity_id(self, mock_issue, mock_db_session):
        """测试获取实体ID"""
        from app.core.state_machine.base import StateMachine

        state_machine = StateMachine(mock_issue, mock_db_session)
        entity_id = state_machine._get_entity_id()

        assert entity_id == 1
