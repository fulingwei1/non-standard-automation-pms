# -*- coding: utf-8 -*-
"""
状态机装饰器

提供声明式定义状态转换规则的装饰器
"""

from functools import wraps
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
                sm_instance = args[0]
                # transition_to 调用 bound method 时传入 (self, from_state, to_state)
                # 由于是 bound method，wrapper 实际收到 (self_bound, self_explicit, from_state, to_state)
                # 即 len(args) >= 4；此时去掉多余的 self，调用原方法
                if len(args) >= 4:
                    # args = (self_bound, self_explicit, from_state, to_state)
                    # 调用原方法: method(self, from_state, to_state, **kwargs)
                    return method(args[0], args[2], args[3], **kwargs)
                if len(args) >= 3:
                    # 兼容非 bound method 调用: (self, from_state, to_state)
                    return method(*args, **kwargs)
                # 当通过实例直接调用（如 sm.approve()）时，
                # 只有 args[0]=self，委托给 transition_to
                target = wrapper._to_state
                return sm_instance.transition_to(target, **kwargs)
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


def before_transition(method_or_hook: Optional[Callable] = None):
    """
    状态转换前钩子装饰器

    支持两种使用方式:
    1. @before_transition - 直接装饰方法
    2. @before_transition() - 带括号装饰方法

    Args:
        method_or_hook: 被装饰的方法（直接使用时）或None（带括号使用时）

    Returns:
        装饰后的方法
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                return method(args[0], *args[1:], **kwargs)
            else:
                return method(*args, **kwargs)

        wrapper._before_hook = True
        return wrapper

    # Support both @before_transition and @before_transition()
    if method_or_hook is not None and callable(method_or_hook):
        # Used as @before_transition (without parentheses)
        return decorator(method_or_hook)
    else:
        # Used as @before_transition() (with parentheses)
        return decorator


def after_transition(method_or_hook: Optional[Callable] = None):
    """
    状态转换后钩子装饰器

    支持两种使用方式:
    1. @after_transition - 直接装饰方法
    2. @after_transition() - 带括号装饰方法

    Args:
        method_or_hook: 被装饰的方法（直接使用时）或None（带括号使用时）

    Returns:
        装饰后的方法
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                return method(args[0], *args[1:], **kwargs)
            else:
                return method(*args, **kwargs)

        wrapper._after_hook = True
        return wrapper

    # Support both @after_transition and @after_transition()
    if method_or_hook is not None and callable(method_or_hook):
        # Used as @after_transition (without parentheses)
        return decorator(method_or_hook)
    else:
        # Used as @after_transition() (with parentheses)
        return decorator
