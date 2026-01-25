# -*- coding: utf-8 -*-
"""
状态机异常类单元测试
"""

import pytest
from app.core.state_machine.exceptions import (
    StateMachineException,
    StateTransitionError,
    InvalidStateTransitionError,
    StateMachineValidationError,
)


class TestStateMachineException:
    """StateMachineException 测试"""

    def test_exception_is_exception(self):
        """测试基类是异常"""
        assert issubclass(StateMachineException, Exception)

    def test_exception_can_be_raised(self):
        """测试异常可以被抛出"""
        with pytest.raises(StateMachineException) as exc_info:
            raise StateMachineException("Test message")
        assert str(exc_info.value) == "Test message"

    def test_exception_with_custom_message(self):
        """测试带自定义消息的异常"""
        msg = "Custom error message"
        with pytest.raises(StateMachineException) as exc_info:
            raise StateMachineException(msg)
        assert msg in str(exc_info.value)


class TestStateTransitionError:
    """StateTransitionError 测试"""

    def test_error_is_state_machine_exception(self):
        """测试是状态机异常的子类"""
        assert issubclass(StateTransitionError, StateMachineException)

    def test_error_can_be_raised(self):
        """测试错误可以被抛出"""
        with pytest.raises(StateTransitionError) as exc_info:
            raise StateTransitionError("Transition failed")
        assert "Transition failed" in str(exc_info.value)

    def test_error_inheritance_chain(self):
        """测试异常继承链"""
        assert issubclass(StateTransitionError, Exception)
        assert issubclass(StateTransitionError, StateMachineException)


class TestInvalidStateTransitionError:
    """InvalidStateTransitionError 测试"""

    def test_error_is_state_transition_error(self):
        """测试是状态转换错误的子类"""
        assert issubclass(InvalidStateTransitionError, StateTransitionError)

    def test_error_can_be_raised(self):
        """测试错误可以被抛出"""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            raise InvalidStateTransitionError(
                "DRAFT", "COMPLETED", "Invalid transition"
            )
        assert "DRAFT" in str(exc_info.value)
        assert "COMPLETED" in str(exc_info.value)

    def test_error_with_states_in_message(self):
        """测试错误消息包含状态信息"""
        from_state = "DRAFT"
        to_state = "APPROVED"
        msg = "Cannot transition"
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            raise InvalidStateTransitionError(from_state, to_state, msg)
        error_msg = str(exc_info.value)
        assert from_state in error_msg
        assert to_state in error_msg
        assert msg in error_msg


class TestStateMachineValidationError:
    """StateMachineValidationError 测试"""

    def test_error_is_state_machine_exception(self):
        """测试是状态机异常的子类"""
        assert issubclass(StateMachineValidationError, StateMachineException)

    def test_error_can_be_raised(self):
        """测试错误可以被抛出"""
        with pytest.raises(StateMachineValidationError) as exc_info:
            raise StateMachineValidationError("Validation failed")
        assert "Validation failed" in str(exc_info.value)

    def test_error_inheritance_chain(self):
        """测试异常继承链"""
        assert issubclass(StateMachineValidationError, Exception)
        assert issubclass(StateMachineValidationError, StateMachineException)


class TestExceptionInteractions:
    """异常交互测试"""

    def test_catch_specific_exception_type(self):
        """测试捕获特定异常类型"""
        with pytest.raises(InvalidStateTransitionError):
            raise InvalidStateTransitionError("DRAFT", "APPROVED", "Invalid")

    def test_exception_does_not_catch_other_exceptions(self):
        """测试异常不会捕获其他异常"""
        with pytest.raises(ValueError):
            raise ValueError("Not a state machine error")

    def test_exception_message_format(self):
        """测试异常消息格式"""
        from_state = "DRAFT"
        to_state = "APPROVED"
        reason = "Invalid transition reason"

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            raise InvalidStateTransitionError(from_state, to_state, reason)

        error_str = str(exc_info.value)
        # 验证所有关键信息都在消息中
        assert from_state in error_str
        assert to_state in error_str
        assert reason in error_str
