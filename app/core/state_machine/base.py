# -*- coding: utf-8 -*-
"""
状态机基类

提供统一的状态转换管理、验证和钩子机制
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple, TYPE_CHECKING

from sqlalchemy.orm import Session

from .exceptions import (
    InvalidStateTransitionError,
    StateMachineValidationError,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class StateMachine:
    """
    状态机基类

    提供以下功能:
    - 状态转换规则定义和验证
    - 状态转换历史记录
    - 前/后钩子支持
    - 与 SQLAlchemy 模型集成
    """

    def __init__(self, model: Any, db: Session, state_field: str = "status"):
        """
        初始化状态机

        Args:
            model: SQLAlchemy 模型实例
            db: 数据库会话
            state_field: 模型中存储状态的字段名，默认为 'status'
        """
        self.model = model
        self.db = db
        self.state_field = state_field
        self._transitions: Dict[Tuple[str, str], Callable] = {}
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []
        self._transition_history: List[Dict[str, Any]] = []

        self._register_transitions()

    @property
    def current_state(self):
        """获取当前状态（支持枚举类型）"""
        state_value = getattr(self.model, self.state_field)
        # 如果是枚举类型，转换为字符串
        from enum import Enum

        if isinstance(state_value, Enum):
            return state_value.value
        return state_value

    def can_transition_to(self, target_state: str) -> Tuple[bool, str]:
        """
        检查是否可以转换到目标状态

        Args:
            target_state: 目标状态

        Returns:
            Tuple[bool, str]: (是否可转换, 原因说明)
        """
        from_state = self.current_state

        if from_state == target_state:
            return False, "已经是目标状态"

        transition_key = (from_state, target_state)
        if transition_key not in self._transitions:
            return False, f"未定义从 '{from_state}' 到 '{target_state}' 的状态转换规则"

        transition_func = self._transitions[transition_key]

        if hasattr(transition_func, "_validator") and transition_func._validator:
            validator = transition_func._validator
            try:
                is_valid, reason = validator(self, from_state, target_state)
                if not is_valid:
                    return False, reason
            except Exception as e:
                logger.error(f"状态转换验证失败: {e}")
                return False, f"验证失败: {str(e)}"

        return True, ""

    def transition_to(self, target_state: str, **kwargs: Any) -> bool:
        """
        执行状态转换

        Args:
            target_state: 目标状态
            **kwargs: 传递给钩子和转换函数的额外参数

        Returns:
            bool: 转换是否成功

        Raises:
            InvalidStateTransitionError: 状态转换无效
            StateMachineValidationError: 状态验证失败
        """
        from_state = self.current_state
        target_state = str(target_state)
        to_state = target_state

        can_transition, reason = self.can_transition_to(target_state)
        if not can_transition:
            raise InvalidStateTransitionError(from_state, target_state, reason)

        try:
            for hook in self._before_hooks:
                try:
                    hook(self, from_state, to_state, **kwargs)
                except Exception as e:
                    logger.warning(f"before transition hook 失败: {e}")

            transition_key = (from_state, to_state)
            transition_func = self._transitions[transition_key]

            if hasattr(transition_func, "_validator") and transition_func._validator:
                validator = transition_func._validator
                is_valid, reason = validator(self, from_state, to_state)
                if not is_valid:
                    raise StateMachineValidationError(reason)

            try:
                # Pass self explicitly since transition_func is an instance method
                transition_func(self, from_state, to_state, **kwargs)
            except TypeError as e:
                logger.error(
                    f"transition_func type error: {e}. args: self={type(self).__name__}, from_state={from_state}, to_state={to_state}"
                )
                raise

            setattr(self.model, self.state_field, target_state)

            self._record_transition(from_state, target_state, **kwargs)

            for hook in self._after_hooks:
                try:
                    hook(self, from_state, target_state, **kwargs)
                except Exception as e:
                    logger.warning(f"after transition hook 失败: {e}")

            return True

        except Exception as e:
            logger.error(f"状态转换失败: {e}", exc_info=True)
            raise

    def get_allowed_transitions(self) -> List[str]:
        """
        获取当前状态允许的所有转换目标状态

        Returns:
            List[str]: 允许的目标状态列表
        """
        current = self.current_state
        return [
            to_state
            for (from_state, to_state) in self._transitions
            if from_state == current
        ]

    def get_transition_history(self) -> List[Dict[str, Any]]:
        """
        获取状态转换历史

        Returns:
            List[Dict]: 转换历史记录列表
        """
        return self._transition_history

    def _register_transitions(self):
        """注册所有定义的状态转换"""
        for attr_name in dir(self):
            # Get attribute from instance to ensure methods are callable with correct self
            # Filter out attributes not from this class's definition (like 'db' or 'model')
            # Check if attribute is defined in the class (not dynamically created)
            attr = getattr(self, attr_name)
            # Skip if attribute doesn't have __module__ (indicates it's a class method/function)
            # or if it's a MagicMock (which is dynamically created)
            if not hasattr(attr, "__module__") or type(attr).__name__ == "MagicMock":
                continue

            if hasattr(attr, "_is_transition") and attr._is_transition:
                from_state = attr._from_state
                to_state = attr._to_state
                transition_key = (from_state, to_state)
                self._transitions[transition_key] = attr

            if hasattr(attr, "_before_hook"):
                self._before_hooks.append(attr)

            if hasattr(attr, "_after_hook"):
                self._after_hooks.append(attr)

    def _record_transition(self, from_state: str, to_state: str, **kwargs: Any):
        """
        记录状态转换历史

        Args:
            from_state: 起始状态
            to_state: 目标状态
            **kwargs: 额外信息
        """
        record = {
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": datetime.now(),
            **kwargs,
        }
        self._transition_history.append(record)

    @classmethod
    def create(
        cls, model: Any, db: Session, state_field: str = "status"
    ) -> "StateMachine":
        """
        工厂方法：为给定模型创建状态机实例

        Args:
            model: SQLAlchemy 模型实例
            db: 数据库会话
            state_field: 状态字段名

        Returns:
            StateMachine: 状态机实例
        """
        return cls(model, db, state_field)
