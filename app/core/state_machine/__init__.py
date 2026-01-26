# -*- coding: utf-8 -*-
"""
统一状态机框架

提供可复用的状态机实现，支持：
- 声明式状态转换规则
- 状态转换验证
- 前后钩子（before/after hooks）
- 与 SQLAlchemy 模型无缝集成
- 状态转换日志记录
"""

from .base import StateMachine
from .decorators import transition, before_transition, after_transition
from .exceptions import (
    StateMachineException,
    StateTransitionError,
    InvalidStateTransitionError,
    StateMachineValidationError,
)
from .ecn import EcnStateMachine

__all__ = [
    "StateMachine",
    "StateMachineException",
    "StateTransitionError",
    "InvalidStateTransitionError",
    "StateMachineValidationError",
    "transition",
    "before_transition",
    "after_transition",
    "EcnStateMachine",
]
