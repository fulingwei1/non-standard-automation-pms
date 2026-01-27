# -*- coding: utf-8 -*-
"""
状态机基类单元测试
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.core.state_machine import StateMachine
from app.core.state_machine.decorators import (
    transition,
    before_transition,
    after_transition,
)
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    StateMachineValidationError,
)


class MockModel:
    """模拟模型"""

    def __init__(self):
        self.status = "DRAFT"


class SimpleStateMachine(StateMachine):
    """简单状态机用于测试"""

    def __init__(self, model, db):
        super().__init__(model, db, state_field="status")

    @transition(from_state="DRAFT", to_state="SUBMITTED")
    def submit(self, from_state, to_state, **kwargs):
        """提交"""
        pass

    @transition(from_state="SUBMITTED", to_state="APPROVED")
    def approve(self, from_state, to_state, **kwargs):
        """批准"""
        pass

    @transition(from_state="SUBMITTED", to_state="REJECTED")
    def reject(self, from_state, to_state, **kwargs):
        """拒绝"""
        pass

    @transition(
        from_state="APPROVED",
        to_state="COMPLETED",
        validator=lambda sm, f, t: (True, ""),
    )
    def complete(self, from_state, to_state, **kwargs):
        """完成"""
        pass

    @before_transition
    def before_hook(self, from_state, to_state, **kwargs):
        """前置钩子"""
        self.before_called = True
        self.before_args = (from_state, to_state, kwargs)

    @after_transition
    def after_hook(self, from_state, to_state, **kwargs):
        """后置钩子"""
        self.after_called = True
        self.after_args = (from_state, to_state, kwargs)


class TestStateMachineBase:
    """状态机基类测试"""

    def setup_method(self):
        """每个测试前设置"""
        self.model = MockModel()
        self.db = MagicMock()
        self.sm = SimpleStateMachine(self.model, self.db)

    def test_initialization(self):
        """测试状态机初始化"""
        assert self.sm.model == self.model
        assert self.sm.db == self.db
        assert self.sm.state_field == "status"
        assert self.sm.current_state == "DRAFT"

    def test_current_state_property(self):
        """测试当前状态属性"""
        assert self.sm.current_state == "DRAFT"
        self.model.status = "SUBMITTED"
        assert self.sm.current_state == "SUBMITTED"

    def test_get_allowed_transitions(self):
        """测试获取允许的转换"""
        allowed = self.sm.get_allowed_transitions()
        assert "SUBMITTED" in allowed
        assert "APPROVED" not in allowed
        assert "REJECTED" not in allowed
        assert "COMPLETED" not in allowed

    def test_get_allowed_transitions_after_transition(self):
        """测试状态转换后获取允许的转换"""
        self.model.status = "SUBMITTED"
        allowed = self.sm.get_allowed_transitions()
        assert "SUBMITTED" not in allowed
        assert "APPROVED" in allowed
        assert "REJECTED" in allowed

    def test_can_transition_to_valid(self):
        """测试验证有效转换"""
        can, reason = self.sm.can_transition_to("SUBMITTED")
        assert can is True
        assert reason == ""

    def test_can_transition_to_same_state(self):
        """测试验证到相同状态的转换"""
        can, reason = self.sm.can_transition_to("DRAFT")
        assert can is False
        assert "已经是目标状态" in reason

    def test_can_transition_to_invalid(self):
        """测试验证无效转换"""
        can, reason = self.sm.can_transition_to("COMPLETED")
        assert can is False
        assert "未定义从" in reason

    def test_transition_to_valid(self):
        """测试有效状态转换"""
        result = self.sm.transition_to("SUBMITTED")
        assert result is True
        assert self.model.status == "SUBMITTED"
        assert len(self.sm.get_transition_history()) == 1

    def test_transition_to_invalid_raises_error(self):
        """测试无效状态转换抛出异常"""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            self.sm.transition_to("COMPLETED")
            assert "DRAFT" in str(exc_info.value)
            assert "COMPLETED" in str(exc_info.value)

    def test_transition_history(self):
        """测试转换历史"""
        self.sm.transition_to("SUBMITTED")
        history = self.sm.get_transition_history()
        assert len(history) == 1
        assert history[0]["from_state"] == "DRAFT"
        assert history[0]["to_state"] == "SUBMITTED"
        assert "timestamp" in history[0]

    def test_transition_with_kwargs(self):
        """测试带参数的状态转换"""
        self.sm.transition_to("SUBMITTED", user_id=123, note="test")
        history = self.sm.get_transition_history()
        assert history[0]["user_id"] == 123
        assert history[0]["note"] == "test"


class TestStateMachineValidation:
    """状态机验证测试"""

    def setup_method(self):
        """每个测试前设置"""
        self.model = MockModel()
        self.db = MagicMock()

        # 创建带验证器的状态机
        class ValidatedStateMachine(StateMachine):
        def __init__(self, model, db):
            super().__init__(model, db, state_field="status")
            self.validator_called = False

        def validate_transition(self, from_state, to_state):
            self.validator_called = True
            if self.model.some_condition:
                return True, ""
                return False, "验证失败: 条件不满足"

        @transition(
        from_state="DRAFT",
        to_state="SUBMITTED",
        validator=validate_transition,
        )
        def submit(self, from_state, to_state, **kwargs):
            pass

            self.sm = ValidatedStateMachine(self.model, self.db)

    def test_can_transition_to_with_valid_validator(self):
        """测试验证器通过的情况"""
        self.model.some_condition = True
        can, reason = self.sm.can_transition_to("SUBMITTED")
        assert can is True
        assert reason == ""
        assert self.sm.validator_called is True

    def test_can_transition_to_with_invalid_validator(self):
        """测试验证器失败的情况"""
        self.model.some_condition = False
        can, reason = self.sm.can_transition_to("SUBMITTED")
        assert can is False
        assert "验证失败" in reason

    def test_transition_to_with_validator_failure(self):
        """测试验证器失败时转换抛出异常"""
        self.model.some_condition = False
        with pytest.raises(StateMachineValidationError) as exc_info:
            self.sm.transition_to("SUBMITTED")
            assert "验证失败" in str(exc_info.value)


class TestStateMachineHooks:
    """状态机钩子测试"""

    def setup_method(self):
        """每个测试前设置"""
        self.model = MockModel()
        self.db = MagicMock()
        self.sm = SimpleStateMachine(self.model, self.db)

    def test_before_hook_called(self):
        """测试前置钩子被调用"""
        assert not hasattr(self.sm, "before_called")
        self.sm.transition_to("SUBMITTED")
        assert self.sm.before_called is True

    def test_after_hook_called(self):
        """测试后置钩子被调用"""
        assert not hasattr(self.sm, "after_called")
        self.sm.transition_to("SUBMITTED")
        assert self.sm.after_called is True

    def test_hooks_receive_correct_args(self):
        """测试钩子接收正确的参数"""
        self.sm.transition_to("SUBMITTED", extra_param="value")
        assert self.sm.before_args[0] == "DRAFT"
        assert self.sm.before_args[1] == "SUBMITTED"
        assert self.sm.before_args[2]["extra_param"] == "value"
        assert self.sm.after_args[0] == "DRAFT"
        assert self.sm.after_args[1] == "SUBMITTED"
        assert self.sm.after_args[2]["extra_param"] == "value"

    def test_hook_failure_does_not_prevent_transition(self):
        """测试钩子失败不阻止转换"""

        class FailingHookStateMachine(StateMachine):
        @transition(from_state="DRAFT", to_state="SUBMITTED")
        def submit(self, from_state, to_state, **kwargs):
            pass

        @before_transition
        def failing_hook(self, from_state, to_state, **kwargs):
            raise Exception("Hook failed")

            sm = FailingHookStateMachine(self.model, self.db)
            # 转换应该成功，即使钩子失败
            result = sm.transition_to("SUBMITTED")
            assert result is True
            assert self.model.status == "SUBMITTED"


class TestStateMachineFactory:
    """状态机工厂方法测试"""

    def test_create_factory_method(self):
        """测试工厂方法创建实例"""
        model = MockModel()
        db = MagicMock()

        sm = StateMachine.create(model, db, state_field="status")
        assert isinstance(sm, StateMachine)
        assert sm.model == model
        assert sm.db == db


class TestStateMachineEdgeCases:
    """状态机边界情况测试"""

    def setup_method(self):
        """每个测试前设置"""
        self.model = MockModel()
        self.db = MagicMock()
        self.sm = SimpleStateMachine(self.model, self.db)

    def test_multiple_transitions(self):
        """测试多次转换"""
        self.sm.transition_to("SUBMITTED")
        self.sm.transition_to("APPROVED")
        self.sm.transition_to("COMPLETED")
        assert self.model.status == "COMPLETED"
        history = self.sm.get_transition_history()
        assert len(history) == 3

    def test_transition_order_in_history(self):
        """测试转换历史顺序正确"""
        self.sm.transition_to("SUBMITTED", order=1)
        self.sm.transition_to("APPROVED", order=2)
        history = self.sm.get_transition_history()
        assert history[0]["order"] == 1
        assert history[1]["order"] == 2

    def test_timestamp_in_history(self):
        """测试历史记录包含时间戳"""
        before = datetime.now()
        self.sm.transition_to("SUBMITTED")
        after = datetime.now()
        history = self.sm.get_transition_history()
        assert before <= history[0]["timestamp"] <= after
