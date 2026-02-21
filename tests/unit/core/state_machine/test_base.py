# -*- coding: utf-8 -*-
"""
状态机基类测试
"""

import pytest
from datetime import datetime
from enum import Enum
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)


# 测试枚举
class TestStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


# 测试用的具体状态机实现
class TestStateMachine(StateMachine):
    """测试用的状态机实现"""
    
    def _register_transitions(self):
        """注册测试用的状态转换"""
        # 手动注册转换（模拟装饰器效果）
        def draft_to_submitted(self, from_state, to_state, **kwargs):
            pass
        
        def submitted_to_approved(self, from_state, to_state, **kwargs):
            pass
        
        def submitted_to_rejected(self, from_state, to_state, **kwargs):
            pass
        
        # 设置转换属性
        draft_to_submitted._is_transition = True
        draft_to_submitted._from_state = "draft"
        draft_to_submitted._to_state = "submitted"
        
        submitted_to_approved._is_transition = True
        submitted_to_approved._from_state = "submitted"
        submitted_to_approved._to_state = "approved"
        
        submitted_to_rejected._is_transition = True
        submitted_to_rejected._from_state = "submitted"
        submitted_to_rejected._to_state = "rejected"
        
        self._transitions = {
            ("draft", "submitted"): draft_to_submitted,
            ("submitted", "approved"): submitted_to_approved,
            ("submitted", "rejected"): submitted_to_rejected,
        }


class TestStateMachineInit:
    """测试状态机初始化"""
    
    def test_init_with_defaults(self):
        """测试默认参数初始化"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        assert sm.model == model
        assert sm.db == db
        assert sm.state_field == "status"
        assert isinstance(sm._transitions, dict)
        assert isinstance(sm._before_hooks, list)
        assert isinstance(sm._after_hooks, list)
        assert isinstance(sm._transition_history, list)
    
    def test_init_with_custom_state_field(self):
        """测试自定义状态字段"""
        model = Mock()
        model.custom_status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db, state_field="custom_status")
        
        assert sm.state_field == "custom_status"
    
    def test_current_state_string(self):
        """测试获取字符串类型的当前状态"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        assert sm.current_state == "draft"
    
    def test_current_state_enum(self):
        """测试获取枚举类型的当前状态"""
        model = Mock()
        model.status = TestStatus.DRAFT
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        assert sm.current_state == "draft"


class TestCanTransitionTo:
    """测试 can_transition_to 方法"""
    
    def test_can_transition_valid(self):
        """测试有效的状态转换"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        can_transition, reason = sm.can_transition_to("submitted")
        
        assert can_transition is True
        assert reason == ""
    
    def test_can_transition_same_state(self):
        """测试转换到相同状态"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        can_transition, reason = sm.can_transition_to("draft")
        
        assert can_transition is False
        assert reason == "已经是目标状态"
    
    def test_can_transition_invalid_rule(self):
        """测试未定义的状态转换规则"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        can_transition, reason = sm.can_transition_to("approved")
        
        assert can_transition is False
        assert "未定义从 'draft' 到 'approved' 的状态转换规则" in reason
    
    def test_can_transition_with_enum(self):
        """测试使用枚举作为目标状态"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        can_transition, reason = sm.can_transition_to(TestStatus.SUBMITTED)
        
        assert can_transition is True
        assert reason == ""
    
    def test_can_transition_with_validator_pass(self):
        """测试验证器通过的情况"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加验证器
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._validator = lambda self, from_state, to_state: (True, "")
        
        can_transition, reason = sm.can_transition_to("submitted")
        
        assert can_transition is True
        assert reason == ""
    
    def test_can_transition_with_validator_fail(self):
        """测试验证器失败的情况"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加验证器
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._validator = lambda self, from_state, to_state: (False, "缺少必填字段")
        
        can_transition, reason = sm.can_transition_to("submitted")
        
        assert can_transition is False
        assert "VALIDATION_FAILED:缺少必填字段" in reason
    
    def test_can_transition_with_validator_exception(self):
        """测试验证器抛出异常的情况"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加会抛出异常的验证器
        def failing_validator(self, from_state, to_state):
            raise ValueError("验证错误")
        
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._validator = failing_validator
        
        can_transition, reason = sm.can_transition_to("submitted")
        
        assert can_transition is False
        assert "VALIDATION_FAILED:验证失败" in reason


class TestTransitionTo:
    """测试 transition_to 方法"""
    
    def test_transition_success(self):
        """测试成功的状态转换"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        result = sm.transition_to("submitted")
        
        assert result is True
        assert model.status == "submitted"
        assert len(sm._transition_history) == 1
        assert sm._transition_history[0]["from_state"] == "draft"
        assert sm._transition_history[0]["to_state"] == "submitted"
    
    def test_transition_invalid_rule(self):
        """测试无效的状态转换规则"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            sm.transition_to("approved")
        
        assert "未定义从 'draft' 到 'approved' 的状态转换规则" in str(exc_info.value)
        assert model.status == "draft"  # 状态未改变
    
    def test_transition_with_enum(self):
        """测试使用枚举作为目标状态"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        result = sm.transition_to(TestStatus.SUBMITTED)
        
        assert result is True
        assert model.status == "submitted"
    
    def test_transition_with_enum_string(self):
        """测试使用枚举字符串表示"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 模拟 str(SomeEnum.VALUE) 产生的格式
        result = sm.transition_to("TestStatus.submitted")
        
        assert result is True
        assert model.status == "submitted"
    
    def test_transition_with_validation_failure(self):
        """测试验证失败的情况"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加验证器
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._validator = lambda self, from_state, to_state: (False, "缺少必填字段")
        
        with pytest.raises(StateMachineValidationError) as exc_info:
            sm.transition_to("submitted")
        
        assert "缺少必填字段" in str(exc_info.value)
        assert model.status == "draft"  # 状态未改变
    
    @patch('app.core.state_machine.base.StateMachinePermissionChecker')
    def test_transition_with_permission_check_pass(self, mock_checker_class):
        """测试权限检查通过"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="test_user")
        
        # 设置 mock
        mock_checker = Mock()
        mock_checker.check_permission.return_value = (True, "")
        mock_checker_class.return_value = mock_checker
        
        sm = TestStateMachine(model, db)
        sm._permission_checker = mock_checker
        
        # 添加权限要求
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._required_permission = "submit_document"
        
        result = sm.transition_to("submitted", current_user=current_user)
        
        assert result is True
        assert model.status == "submitted"
        mock_checker.check_permission.assert_called_once()
    
    @patch('app.core.state_machine.base.StateMachinePermissionChecker')
    def test_transition_with_permission_check_fail(self, mock_checker_class):
        """测试权限检查失败"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="test_user")
        
        # 设置 mock
        mock_checker = Mock()
        mock_checker.check_permission.return_value = (False, "权限不足")
        mock_checker_class.return_value = mock_checker
        
        sm = TestStateMachine(model, db)
        sm._permission_checker = mock_checker
        
        # 添加权限要求
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._required_permission = "submit_document"
        
        with pytest.raises(PermissionDeniedError):
            sm.transition_to("submitted", current_user=current_user)
        
        assert model.status == "draft"  # 状态未改变
    
    def test_transition_with_before_hooks(self):
        """测试 before hooks 执行"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加 before hook
        before_hook = Mock()
        sm._before_hooks.append(before_hook)
        
        sm.transition_to("submitted")
        
        before_hook.assert_called_once_with("draft", "submitted")
    
    def test_transition_with_after_hooks(self):
        """测试 after hooks 执行"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加 after hook
        after_hook = Mock()
        sm._after_hooks.append(after_hook)
        
        sm.transition_to("submitted")
        
        after_hook.assert_called_once_with("draft", "submitted")
    
    def test_transition_with_hook_exception(self):
        """测试 hook 抛出异常但不影响转换"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 添加会抛出异常的 hook
        failing_hook = Mock(side_effect=Exception("Hook error"))
        sm._before_hooks.append(failing_hook)
        
        # 转换应该继续
        result = sm.transition_to("submitted")
        
        assert result is True
        assert model.status == "submitted"
    
    @patch('app.core.state_machine.base.StateMachine._create_audit_log')
    def test_transition_with_audit_log(self, mock_audit_log):
        """测试创建审计日志"""
        model = Mock()
        model.status = "draft"
        model.id = 123
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="test_user")
        
        sm = TestStateMachine(model, db)
        
        # 添加 action_type
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._action_type = "SUBMIT"
        
        sm.transition_to(
            "submitted",
            current_user=current_user,
            comment="测试提交"
        )
        
        mock_audit_log.assert_called_once_with(
            from_state="draft",
            to_state="submitted",
            operator=current_user,
            action_type="SUBMIT",
            comment="测试提交"
        )
    
    @patch('app.core.state_machine.base.StateMachine._send_notifications')
    def test_transition_with_notifications(self, mock_send_notif):
        """测试发送通知"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="test_user")
        
        sm = TestStateMachine(model, db)
        
        # 添加通知配置
        transition_func = sm._transitions[("draft", "submitted")]
        transition_func._notify_users = ["approver", "creator"]
        transition_func._notification_template = "document_submitted"
        
        sm.transition_to("submitted", current_user=current_user)
        
        mock_send_notif.assert_called_once()
        args = mock_send_notif.call_args[1]
        assert args["from_state"] == "draft"
        assert args["to_state"] == "submitted"
        assert args["notify_user_types"] == ["approver", "creator"]
        assert args["template"] == "document_submitted"
    
    def test_transition_rollback_on_error(self):
        """测试转换失败时状态回滚"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        # 模拟转换函数抛出异常
        transition_func = sm._transitions[("draft", "submitted")]
        original_func = transition_func
        sm._transitions[("draft", "submitted")] = Mock(side_effect=ValueError("转换错误"))
        
        with pytest.raises(ValueError):
            sm.transition_to("submitted")
        
        # 状态应该回滚
        assert model.status == "draft"


class TestGetAllowedTransitions:
    """测试 get_allowed_transitions 方法"""
    
    def test_get_allowed_transitions(self):
        """测试获取允许的转换"""
        model = Mock()
        model.status = "submitted"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        allowed = sm.get_allowed_transitions()
        
        assert set(allowed) == {"approved", "rejected"}
    
    def test_get_allowed_transitions_no_options(self):
        """测试没有允许的转换"""
        model = Mock()
        model.status = "approved"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        allowed = sm.get_allowed_transitions()
        
        assert allowed == []


class TestGetTransitionHistory:
    """测试 get_transition_history 方法"""
    
    def test_get_transition_history_empty(self):
        """测试空历史"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        history = sm.get_transition_history()
        
        assert history == []
    
    def test_get_transition_history_with_records(self):
        """测试有记录的历史"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = TestStateMachine(model, db)
        
        sm.transition_to("submitted")
        
        history = sm.get_transition_history()
        
        assert len(history) == 1
        assert history[0]["from_state"] == "draft"
        assert history[0]["to_state"] == "submitted"
        assert "timestamp" in history[0]


class TestCreateAuditLog:
    """测试 _create_audit_log 方法"""
    
    @patch('app.core.state_machine.base.StateTransitionLog')
    def test_create_audit_log(self, mock_log_class):
        """测试创建审计日志"""
        model = Mock()
        model.status = "draft"
        model.id = 123
        model.__class__.__name__ = "TestModel"
        db = Mock(spec=Session)
        current_user = Mock(id=1, name="Test User")
        
        sm = TestStateMachine(model, db)
        
        sm._create_audit_log(
            from_state="draft",
            to_state="submitted",
            operator=current_user,
            action_type="SUBMIT",
            comment="测试提交"
        )
        
        mock_log_class.assert_called_once()
        call_kwargs = mock_log_class.call_args[1]
        assert call_kwargs["entity_type"] == "TESTMODEL"
        assert call_kwargs["entity_id"] == 123
        assert call_kwargs["from_state"] == "draft"
        assert call_kwargs["to_state"] == "submitted"
        assert call_kwargs["operator_id"] == 1
        assert call_kwargs["operator_name"] == "Test User"
        assert call_kwargs["action_type"] == "SUBMIT"
        assert call_kwargs["comment"] == "测试提交"
        
        db.add.assert_called_once()
        db.flush.assert_called_once()
    
    @patch('app.core.state_machine.base.StateTransitionLog')
    def test_create_audit_log_with_username(self, mock_log_class):
        """测试使用 username 的审计日志"""
        model = Mock()
        model.status = "draft"
        model.id = 123
        model.__class__.__name__ = "TestModel"
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="testuser")
        del current_user.name  # 确保没有 name 属性
        
        sm = TestStateMachine(model, db)
        
        sm._create_audit_log(
            from_state="draft",
            to_state="submitted",
            operator=current_user,
            action_type="SUBMIT",
            comment=None
        )
        
        call_kwargs = mock_log_class.call_args[1]
        assert call_kwargs["operator_name"] == "testuser"


class TestSendNotifications:
    """测试 _send_notifications 方法"""
    
    @patch('app.core.state_machine.base.StateMachineNotifier')
    def test_send_notifications(self, mock_notifier_class):
        """测试发送通知"""
        model = Mock()
        model.status = "draft"
        model.id = 123
        model.__class__.__name__ = "TestModel"
        db = Mock(spec=Session)
        current_user = Mock(id=1, username="testuser")
        
        mock_notifier = Mock()
        mock_notifier_class.return_value = mock_notifier
        
        sm = TestStateMachine(model, db)
        sm._notifier = mock_notifier
        
        sm._send_notifications(
            from_state="draft",
            to_state="submitted",
            operator=current_user,
            notify_user_types=["approver"],
            template="document_submitted"
        )
        
        mock_notifier.send_transition_notification.assert_called_once()


class TestGetEntityType:
    """测试 _get_entity_type 方法"""
    
    def test_get_entity_type(self):
        """测试获取实体类型"""
        model = Mock()
        model.__class__.__name__ = "Issue"
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        entity_type = sm._get_entity_type()
        
        assert entity_type == "ISSUE"


class TestGetEntityId:
    """测试 _get_entity_id 方法"""
    
    def test_get_entity_id(self):
        """测试获取实体ID"""
        model = Mock()
        model.id = 123
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        entity_id = sm._get_entity_id()
        
        assert entity_id == 123
    
    def test_get_entity_id_no_id_attribute(self):
        """测试模型没有 id 属性"""
        model = Mock()
        del model.id
        model.status = "draft"
        model.__class__.__name__ = "TestModel"
        db = Mock(spec=Session)
        
        sm = StateMachine(model, db)
        
        with pytest.raises(AttributeError) as exc_info:
            sm._get_entity_id()
        
        assert "TestModel" in str(exc_info.value)
        assert "没有 'id' 属性" in str(exc_info.value)


class TestCreateFactoryMethod:
    """测试 create 工厂方法"""
    
    def test_create(self):
        """测试工厂方法"""
        model = Mock()
        model.status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine.create(model, db)
        
        assert isinstance(sm, StateMachine)
        assert sm.model == model
        assert sm.db == db
    
    def test_create_with_custom_state_field(self):
        """测试带自定义状态字段的工厂方法"""
        model = Mock()
        model.custom_status = "draft"
        db = Mock(spec=Session)
        
        sm = StateMachine.create(model, db, state_field="custom_status")
        
        assert sm.state_field == "custom_status"
