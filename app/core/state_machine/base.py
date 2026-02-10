# -*- coding: utf-8 -*-
"""
状态机基类

提供统一的状态转换管理、验证和钩子机制
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from sqlalchemy.orm import Session

from .exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from .permissions import StateMachinePermissionChecker
from .notifications import StateMachineNotifier
from app.services.notification_service import NotificationPriority

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

        # 初始化权限检查器和通知服务
        self._permission_checker = StateMachinePermissionChecker()
        self._notifier = StateMachineNotifier()

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

        # 支持枚举类型
        from enum import Enum as _Enum
        if isinstance(target_state, _Enum):
            target_state = target_state.value
        else:
            target_state = str(target_state)
            if "." in target_state:
                target_state = target_state.rsplit(".", 1)[-1]

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
                    return False, f"VALIDATION_FAILED:{reason}"
            except Exception as e:
                logger.error(f"状态转换验证失败: {e}")
                return False, f"VALIDATION_FAILED:验证失败: {str(e)}"

        return True, ""

    def transition_to(
        self,
        target_state: str,
        current_user: Optional[Any] = None,
        comment: Optional[str] = None,
        action_type: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        执行状态转换（增强版）

        Args:
            target_state: 目标状态
            current_user: 当前操作用户（可选，用于权限检查和审计）
            comment: 转换备注/原因（可选）
            action_type: 操作类型（可选，如SUBMIT/APPROVE/REJECT等）
            **kwargs: 传递给钩子和转换函数的额外参数

        Returns:
            bool: 转换是否成功

        Raises:
            InvalidStateTransitionError: 状态转换无效
            StateMachineValidationError: 状态验证失败
            PermissionDeniedError: 权限不足
        """
        from_state = self.current_state
        # 支持枚举类型作为 target_state 参数
        from enum import Enum as _Enum
        if isinstance(target_state, _Enum):
            target_state = target_state.value
        else:
            target_state = str(target_state)
            # 处理 str(SomeEnum.VALUE) 产生的 "SomeEnum.VALUE" 格式
            if "." in target_state:
                target_state = target_state.rsplit(".", 1)[-1]
        to_state = target_state

        # 1. 获取转换函数和元数据
        transition_key = (from_state, to_state)
        if transition_key not in self._transitions:
            raise InvalidStateTransitionError(
                from_state, target_state, f"未定义从 '{from_state}' 到 '{target_state}' 的状态转换规则"
            )

        transition_func = self._transitions[transition_key]

        # 2. 权限检查（使用装饰器定义的权限要求）
        if hasattr(transition_func, "_required_permission") or hasattr(
            transition_func, "_required_role"
        ):
            required_permission = getattr(transition_func, "_required_permission", None)
            required_role = getattr(transition_func, "_required_role", None)

            has_permission, reason = self._permission_checker.check_permission(
                current_user=current_user,
                required_permission=required_permission,
                required_role=required_role,
            )

            if not has_permission:
                raise PermissionDeniedError(reason)

        # 3. 验证转换是否有效
        can_transition, reason = self.can_transition_to(target_state)
        if not can_transition:
            # Check if it's a validation failure vs invalid transition
            if reason.startswith("VALIDATION_FAILED:"):
                actual_reason = reason[len("VALIDATION_FAILED:"):]
                raise StateMachineValidationError(actual_reason)
            raise InvalidStateTransitionError(from_state, target_state, reason)

        try:
            # 4. 执行 before hooks
            for hook in self._before_hooks:
                try:
                    # Note: hooks are bound methods, so self is already bound
                    hook(from_state, to_state, **kwargs)
                except Exception as e:
                    logger.warning(f"before transition hook 失败: {e}")

            # 5. 再次验证（业务验证器）
            if hasattr(transition_func, "_validator") and transition_func._validator:
                validator = transition_func._validator
                is_valid, reason = validator(self, from_state, to_state)
                if not is_valid:
                    raise StateMachineValidationError(reason)

            # 6. 执行转换函数
            try:
                transition_func(self, from_state, to_state, **kwargs)
            except TypeError as e:
                logger.error(
                    f"transition_func type error: {e}. args: self={type(self).__name__}, "
                    f"from_state={from_state}, to_state={to_state}"
                )
                raise

            # 7. 更新状态字段
            setattr(self.model, self.state_field, target_state)

            # 8. 创建审计日志
            if current_user:
                # 从装饰器获取action_type（如果未提供）
                if not action_type and hasattr(transition_func, "_action_type"):
                    action_type = transition_func._action_type

                self._create_audit_log(
                    from_state=from_state,
                    to_state=to_state,
                    operator=current_user,
                    action_type=action_type,
                    comment=comment,
                )

            # 9. 记录内存中的转换历史
            self._record_transition(from_state, target_state, **kwargs)

            # 10. 发送通知
            if hasattr(transition_func, "_notify_users") and transition_func._notify_users:
                notify_users = transition_func._notify_users
                template = getattr(transition_func, "_notification_template", None)

                self._send_notifications(
                    from_state=from_state,
                    to_state=to_state,
                    operator=current_user,
                    notify_user_types=notify_users,
                    template=template,
                )

            # 11. 执行 after hooks
            for hook in self._after_hooks:
                try:
                    # Note: hooks are bound methods, so self is already bound
                    hook(from_state, target_state, **kwargs)
                except Exception as e:
                    logger.warning(f"after transition hook 失败: {e}")

            return True

        except Exception as e:
            # 回滚内存中的状态变更，保持与数据库一致
            setattr(self.model, self.state_field, from_state)
            logger.error(f"状态转换失败，已回滚内存状态: {e}", exc_info=True)
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
        记录状态转换历史（内存）

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

    def _create_audit_log(
        self,
        from_state: str,
        to_state: str,
        operator: Any,
        action_type: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        """
        创建状态转换审计日志（数据库）

        Args:
            from_state: 源状态
            to_state: 目标状态
            operator: 操作人对象
            action_type: 操作类型（如SUBMIT、APPROVE等）
            comment: 备注信息
        """
        try:
            from app.models.state_machine import StateTransitionLog

            # 获取实体类型和ID
            entity_type = self._get_entity_type()
            entity_id = self._get_entity_id()

            # 获取操作人信息
            operator_id = operator.id if hasattr(operator, 'id') else None
            operator_name = None
            if hasattr(operator, 'name'):
                operator_name = operator.name
            elif hasattr(operator, 'username'):
                operator_name = operator.username

            # 创建审计日志
            log = StateTransitionLog(
                entity_type=entity_type,
                entity_id=entity_id,
                from_state=from_state,
                to_state=to_state,
                operator_id=operator_id,
                operator_name=operator_name,
                action_type=action_type,
                comment=comment,
            )

            self.db.add(log)
            self.db.commit()

            logger.info(
                f"状态转换审计日志已创建: {entity_type}:{entity_id} "
                f"{from_state}→{to_state} by {operator_name}"
            )

        except Exception as e:
            logger.error(f"创建状态转换审计日志失败: {e}")
            self.db.rollback()

    def _send_notifications(
        self,
        from_state: str,
        to_state: str,
        operator: Optional[Any],
        notify_user_types: List[str],
        template: Optional[str] = None,
    ):
        """
        发送状态转换通知

        Args:
            from_state: 源状态
            to_state: 目标状态
            operator: 操作人
            notify_user_types: 通知用户类型列表
            template: 通知模板名称
        """
        try:
            entity_type = self._get_entity_type()
            entity_id = self._get_entity_id()

            self._notifier.send_transition_notification(
                db=self.db,
                entity=self.model,
                entity_type=entity_type,
                entity_id=entity_id,
                from_state=from_state,
                to_state=to_state,
                operator=operator,
                notify_user_types=notify_user_types,
                template=template,
                priority=NotificationPriority.NORMAL,
            )

        except Exception as e:
            logger.error(f"发送状态转换通知失败: {e}")

    def _get_entity_type(self) -> str:
        """
        获取实体类型（从模型类名推断）

        Returns:
            实体类型字符串（如ISSUE、ECN、PROJECT等）
        """
        # 从模型类名获取
        class_name = self.model.__class__.__name__
        # 转换为大写（Issue -> ISSUE, Ecn -> ECN）
        return class_name.upper()

    def _get_entity_id(self) -> int:
        """
        获取实体ID

        Returns:
            实体ID
        """
        if hasattr(self.model, 'id'):
            return self.model.id
        else:
            raise AttributeError(f"模型 {self.model.__class__.__name__} 没有 'id' 属性")

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
