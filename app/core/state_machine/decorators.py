# -*- coding: utf-8 -*-
"""
状态机装饰器

提供声明式定义状态转换规则的装饰器
"""

from functools import wraps, update_wrapper
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass


def transition(
    from_state,
    to_state,
    validator: Optional[Callable] = None,
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
):
    """
    状态转换装饰器

    Args:
        from_state: 起始状态（支持枚举或字符串）
        to_state: 目标状态（支持枚举或字符串）
        validator: 状态转换验证函数，返回 (is_valid, reason)
        on_success: 转换成功后的回调
        on_failure: 转换失败后的回调

    Returns:
        装饰后的方法
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
