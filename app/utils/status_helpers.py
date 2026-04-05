# -*- coding: utf-8 -*-
"""
状态工具函数

提供通用的状态检查、验证和查询功能，减少各服务中的状态检查代码重复。
"""

from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import BinaryExpression


def check_status_equals(
    obj: Any,
    expected: Union[str, List[str]],
    status_attr: str = "status"
) -> bool:
    """
    检查对象状态是否匹配预期值。

    Args:
        obj: 包含 status 属性的对象
        expected: 预期状态值，可以是单个值或值列表
        status_attr: 状态属性名，默认为 "status"

    Returns:
        状态是否匹配

    Examples:
        >>> check_status_equals(contract, "draft")
        True
        >>> check_status_equals(contract, ["draft", "approved"])
        True
    """
    current = getattr(obj, status_attr, None)
    if current is None:
        return False

    # 统一转换为字符串比较
    current_str = str(current.value) if hasattr(current, "value") else str(current)

    if isinstance(expected, list):
        expected_strs = [str(e.value) if hasattr(e, "value") else str(e) for e in expected]
        return current_str in expected_strs

    expected_str = str(expected.value) if hasattr(expected, "value") else str(expected)
    return current_str == expected_str


def assert_status_allows(
    obj: Any,
    allowed: Union[str, List[str]],
    error_msg: str,
    status_attr: str = "status"
) -> None:
    """
    断言对象状态是否在允许范围内，否则抛出异常。

    Args:
        obj: 包含 status 属性的对象
        allowed: 允许的状态值（单个或列表）
        error_msg: 状态不匹配时的错误消息
        status_attr: 状态属性名

    Raises:
        ValueError: 当状态不在允许范围内时

    Examples:
        >>> assert_status_allows(contract, "draft", "只能操作草稿状态的合同")
        >>> assert_status_allows(contract, ["draft", "approved"], "状态不允许此操作")
    """
    if not check_status_equals(obj, allowed, status_attr):
        raise ValueError(error_msg)


def assert_status_not(
    obj: Any,
    forbidden: Union[str, List[str]],
    error_msg: str,
    status_attr: str = "status"
) -> None:
    """
    断言对象状态不在禁止范围内，否则抛出异常。

    Args:
        obj: 包含 status 属性的对象
        forbidden: 禁止的状态值（单个或列表）
        error_msg: 状态在禁止范围内时的错误消息
        status_attr: 状态属性名

    Raises:
        ValueError: 当状态在禁止范围内时
    """
    if check_status_equals(obj, forbidden, status_attr):
        raise ValueError(error_msg)


def get_status_filter(
    model: Type,
    status: Union[str, List[str]],
    status_attr: str = "status"
) -> BinaryExpression:
    """
    构建状态过滤条件。

    Args:
        model: SQLAlchemy 模型类
        status: 要匹配的状态值（单个或列表）
        status_attr: 状态属性名

    Returns:
        SQLAlchemy 过滤条件表达式

    Examples:
        >>> query.filter(get_status_filter(Contract, "draft"))
        >>> query.filter(get_status_filter(Contract, ["draft", "approved"]))
    """
    column = getattr(model, status_attr)

    if isinstance(status, list):
        # 转换枚举值为字符串
        status_values = [str(s.value) if hasattr(s, "value") else str(s) for s in status]
        return column.in_(status_values)

    status_value = str(status.value) if hasattr(status, "value") else str(status)
    return column == status_value


def count_by_status(
    db: Session,
    model: Type,
    statuses: Optional[List[str]] = None,
    status_attr: str = "status"
) -> Dict[str, int]:
    """
    按状态统计记录数量。

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        statuses: 要统计的状态列表，None 则统计所有状态
        status_attr: 状态属性名

    Returns:
        状态到数量的映射字典

    Examples:
        >>> count_by_status(db, Contract, ["draft", "approved", "signed"])
        {"draft": 10, "approved": 5, "signed": 20}
    """
    column = getattr(model, status_attr)

    # 查询所有状态的计数
    query = db.query(column, func.count(model.id)).group_by(column)

    # 如果指定了状态列表，则过滤
    if statuses:
        status_values = [str(s.value) if hasattr(s, "value") else str(s) for s in statuses]
        query = query.filter(column.in_(status_values))

    results = query.all()

    # 转换为字典
    counts = {str(status): count for status, count in results}

    # 如果指定了状态列表，确保所有状态都有值（默认 0）
    if statuses:
        status_values = [str(s.value) if hasattr(s, "value") else str(s) for s in statuses]
        for status in status_values:
            if status not in counts:
                counts[status] = 0

    return counts


def validate_status_transition(
    current: str,
    target: str,
    allowed_transitions: Dict[str, List[str]]
) -> bool:
    """
    验证状态转换是否有效。

    Args:
        current: 当前状态
        target: 目标状态
        allowed_transitions: 状态转换规则，格式为 {当前状态: [允许的目标状态列表]}

    Returns:
        转换是否有效

    Examples:
        >>> transitions = {
        ...     "draft": ["approving", "voided"],
        ...     "approving": ["approved", "draft"],
        ...     "approved": ["signed", "voided"],
        ... }
        >>> validate_status_transition("draft", "approving", transitions)
        True
        >>> validate_status_transition("draft", "signed", transitions)
        False
    """
    # 处理枚举值
    current_str = str(current.value) if hasattr(current, "value") else str(current)
    target_str = str(target.value) if hasattr(target, "value") else str(target)

    allowed = allowed_transitions.get(current_str, [])
    allowed_strs = [str(s.value) if hasattr(s, "value") else str(s) for s in allowed]

    return target_str in allowed_strs


def assert_valid_transition(
    current: str,
    target: str,
    allowed_transitions: Dict[str, List[str]],
    error_msg_template: str = "无法从状态 {current} 转换到 {target}"
) -> None:
    """
    断言状态转换有效，否则抛出异常。

    Args:
        current: 当前状态
        target: 目标状态
        allowed_transitions: 状态转换规则
        error_msg_template: 错误消息模板，支持 {current} 和 {target} 占位符

    Raises:
        ValueError: 当状态转换无效时
    """
    if not validate_status_transition(current, target, allowed_transitions):
        current_str = str(current.value) if hasattr(current, "value") else str(current)
        target_str = str(target.value) if hasattr(target, "value") else str(target)
        raise ValueError(error_msg_template.format(current=current_str, target=target_str))


# 常用状态常量
class CommonStatus:
    """常用状态常量"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    VOIDED = "voided"
