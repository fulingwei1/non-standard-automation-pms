# -*- coding: utf-8 -*-
"""
自定义 Jinja2 过滤器

为报告表达式提供常用过滤器
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment


def register_filters(env: Environment) -> None:
    """
    注册所有自定义过滤器

    Args:
        env: Jinja2 环境
    """
    # 列表操作过滤器
    env.filters["sum_by"] = filter_sum_by
    env.filters["avg_by"] = filter_avg_by
    env.filters["count_by"] = filter_count_by
    env.filters["group_by"] = filter_group_by
    env.filters["sort_by"] = filter_sort_by
    env.filters["unique"] = filter_unique
    env.filters["pluck"] = filter_pluck

    # 数值格式化过滤器
    env.filters["currency"] = filter_currency
    env.filters["percentage"] = filter_percentage
    env.filters["round_num"] = filter_round_num

    # 日期过滤器
    env.filters["date_format"] = filter_date_format
    env.filters["days_ago"] = filter_days_ago
    env.filters["days_until"] = filter_days_until

    # 字符串过滤器
    env.filters["truncate_text"] = filter_truncate_text
    env.filters["status_label"] = filter_status_label

    # 条件过滤器
    env.filters["default_if_none"] = filter_default_if_none
    env.filters["coalesce"] = filter_coalesce


# === 列表操作过滤器 ===

def filter_sum_by(items: List[Dict], field: str) -> float:
    """
    按字段求和

    Usage: {{ items | sum_by('amount') }}
    """
    if not items:
        return 0
    return sum(item.get(field, 0) or 0 for item in items)


def filter_avg_by(items: List[Dict], field: str) -> float:
    """
    按字段求平均

    Usage: {{ items | avg_by('score') }}
    """
    if not items:
        return 0
    values = [item.get(field, 0) or 0 for item in items]
    return sum(values) / len(values) if values else 0


def filter_count_by(items: List[Dict], field: str, value: Any) -> int:
    """
    统计字段值匹配的数量

    Usage: {{ items | count_by('status', 'DONE') }}
    """
    if not items:
        return 0
    return sum(1 for item in items if item.get(field) == value)


def filter_group_by(items: List[Dict], field: str) -> Dict[Any, List[Dict]]:
    """
    按字段分组

    Usage: {{ items | group_by('category') }}
    """
    result: Dict[Any, List[Dict]] = {}
    for item in items:
        key = item.get(field)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def filter_sort_by(items: List[Dict], field: str, reverse: bool = False) -> List[Dict]:
    """
    按字段排序

    Usage: {{ items | sort_by('created_at', true) }}
    """
    return sorted(items, key=lambda x: x.get(field, ""), reverse=reverse)


def filter_unique(items: List[Dict], field: str) -> List[Any]:
    """
    提取唯一值

    Usage: {{ items | unique('category') }}
    """
    seen = set()
    result = []
    for item in items:
        value = item.get(field)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def filter_pluck(items: List[Dict], field: str) -> List[Any]:
    """
    提取字段值列表

    Usage: {{ items | pluck('id') }}
    """
    return [item.get(field) for item in items]


# === 数值格式化过滤器 ===

def filter_currency(value: Optional[float], symbol: str = "¥", decimals: int = 2) -> str:
    """
    货币格式化

    Usage: {{ amount | currency('$', 2) }}
    """
    if value is None:
        return f"{symbol}0.00"
    return f"{symbol}{value:,.{decimals}f}"


def filter_percentage(value: Optional[float], decimals: int = 1) -> str:
    """
    百分比格式化

    Usage: {{ ratio | percentage(2) }}
    """
    if value is None:
        return "0%"
    return f"{value:.{decimals}f}%"


def filter_round_num(value: Optional[float], decimals: int = 2) -> float:
    """
    数值四舍五入

    Usage: {{ score | round_num(1) }}
    """
    if value is None:
        return 0
    return round(value, decimals)


# === 日期过滤器 ===

def filter_date_format(value: Any, format_str: str = "%Y-%m-%d") -> str:
    """
    日期格式化

    Usage: {{ created_at | date_format('%Y年%m月%d日') }}
    """
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if isinstance(value, (date, datetime)):
        return value.strftime(format_str)
    return str(value)


def filter_days_ago(value: Any) -> int:
    """
    计算距今天数

    Usage: {{ created_at | days_ago }}
    """
    if value is None:
        return 0
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return 0
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return (date.today() - value).days
    return 0


def filter_days_until(value: Any) -> int:
    """
    计算剩余天数

    Usage: {{ deadline | days_until }}
    """
    if value is None:
        return 0
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return 0
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return (value - date.today()).days
    return 0


# === 字符串过滤器 ===

def filter_truncate_text(value: Optional[str], length: int = 50, suffix: str = "...") -> str:
    """
    截断文本

    Usage: {{ description | truncate_text(30) }}
    """
    if not value:
        return ""
    if len(value) <= length:
        return value
    return value[:length] + suffix


def filter_status_label(value: Optional[str]) -> str:
    """
    状态标签转中文

    Usage: {{ status | status_label }}
    """
    status_map = {
        "PENDING": "待处理",
        "IN_PROGRESS": "进行中",
        "DONE": "已完成",
        "COMPLETED": "已完成",
        "CANCELLED": "已取消",
        "BLOCKED": "已阻塞",
        "ON_HOLD": "暂停",
        "APPROVED": "已批准",
        "REJECTED": "已拒绝",
        "DRAFT": "草稿",
        "SUBMITTED": "已提交",
    }
    return status_map.get(value, value or "")


# === 条件过滤器 ===

def filter_default_if_none(value: Any, default: Any = "") -> Any:
    """
    空值默认值

    Usage: {{ name | default_if_none('未知') }}
    """
    return value if value is not None else default


def filter_coalesce(*values: Any) -> Any:
    """
    返回第一个非空值

    Usage: {{ coalesce(name, nickname, '匿名') }}
    """
    for v in values:
        if v is not None:
            return v
    return None
