# -*- coding: utf-8 -*-
"""
状态机框架异常定义
"""


class StateMachineException(Exception):
    """状态机基础异常"""

    pass


class StateTransitionError(StateMachineException):
    """状态转换失败异常"""

    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        message = f"Cannot transition from '{from_state}' to '{to_state}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class InvalidStateTransitionError(StateTransitionError):
    """无效的状态转换异常（转换未被定义）"""

    pass


class StateMachineValidationError(StateMachineException):
    """状态机验证失败异常"""

    pass


class PermissionDeniedError(StateMachineException):
    """权限拒绝异常"""

    def __init__(self, reason: str = ""):
        self.reason = reason
        message = "Permission denied"
        if reason:
            message += f": {reason}"
        super().__init__(message)
