# -*- coding: utf-8 -*-
"""
状态机装饰器

提供声明式定义状态转换规则的装饰器
"""

from functools import wraps, update_wrapper
from typing import Any, Callable, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    pass


def transition(
    from_state,
    to_state,
    validator: Optional[Callable] = None,
    required_permission: Optional[str] = None,       # 新增：所需权限
    required_role: Optional[str] = None,             # 新增：所需角色
    action_type: Optional[str] = None,               # 新增：操作类型
    notify_users: Optional[List[str]] = None,        # 新增：通知用户类型
    notification_template: Optional[str] = None,     # 新增：通知模板
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
):
    """
    增强的状态转换装饰器

    Args:
        from_state: 起始状态（支持枚举或字符串）
        to_state: 目标状态（支持枚举或字符串）
        validator: 状态转换验证函数，返回 (is_valid, reason)
        required_permission: 所需权限（如 "ecn:approve"）
        required_role: 所需角色（如 "PROJECT_MANAGER"）
        action_type: 操作类型，用于审计日志分类（如 "SUBMIT", "APPROVE"）
        notify_users: 通知用户类型列表（如 ["assignee", "reporter"]）
        notification_template: 通知模板名称
        on_success: 转换成功后的回调
        on_failure: 转换失败后的回调

    Returns:
        装饰后的方法

    示例:
        @transition(
            from_state="DRAFT",
            to_state="PENDING_REVIEW",
            required_permission="ecn:submit",
            action_type="SUBMIT",
            notify_users=["approvers"],
            notification_template="ecn_submitted"
        )
        def submit_for_review(self, from_state, to_state, **kwargs):
            pass
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                args = args[1:]
            return method(*args, **kwargs)

        wrapper._is_transition = True
        wrapper._from_state = from_state
        wrapper._to_state = to_state
        wrapper._validator = validator
        wrapper._on_success = on_success
        wrapper._on_failure = on_failure
        # 新增属性
        wrapper._required_permission = required_permission
        wrapper._required_role = required_role
        wrapper._action_type = action_type
        wrapper._notify_users = notify_users
        wrapper._notification_template = notification_template
        return wrapper

    return decorator


def before_transition(hook: Callable):
    """
    状态转换前钩子装饰器

    Args:
        hook: 钩子函数，签名: (from_state, to_state, **kwargs)

    Returns:
        装饰后的方法
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method, assigned=("_before_hook",))
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                return method(args[0], *args[1:], **kwargs)
            else:
                return method(*args, **kwargs)

        wrapper._before_hook = hook
        return wrapper

    return decorator


def after_transition(hook: Callable):
    """
    状态转换后钩子装饰器

    Args:
        hook: 钩子函数，签名: (from_state, to_state, **kwargs)

    Returns:
        装饰后的方法
    """

    def decorator(method: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                return method(args[0], *args[1:], **kwargs)
            else:
                return method(*args, **kwargs)

        wrapper._after_hook = hook
        wrapper = update_wrapper(
            wrapper,
            method,
            assigned=("__module__", "__name__", "__qualname__", "__doc__"),
        )
        return wrapper

    return decorator
