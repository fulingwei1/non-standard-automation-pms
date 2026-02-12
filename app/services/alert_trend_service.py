# -*- coding: utf-8 -*-
"""
预警趋势分析服务

提取预警趋势统计和分析逻辑
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List


from app.common.date_range import get_month_range, month_start
from app.models.alert import AlertRecord


def get_period_key(dt: datetime, period: str) -> str:
    """
    根据 period 参数生成分组键

    Args:
        dt: 日期时间
        period: 统计周期 (DAILY/WEEKLY/MONTHLY)

    Returns:
        分组键字符串
    """
    if period == "DAILY":
        return dt.date().isoformat()
    elif period == "WEEKLY":
        # 获取该日期所在周的周一
        days_since_monday = dt.weekday()
        monday = dt.date() - timedelta(days=days_since_monday)
        return monday.isoformat()
    elif period == "MONTHLY":
        return month_start(dt.date()).isoformat()
    else:
        return dt.date().isoformat()


def generate_date_range(start: date, end: date, period: str) -> List[str]:
    """
    生成日期范围

    Args:
        start: 开始日期
        end: 结束日期
        period: 统计周期

    Returns:
        日期字符串列表
    """
    dates = []
    current = start

    while current <= end:
        if period == "DAILY":
            dates.append(current.isoformat())
            current += timedelta(days=1)
        elif period == "WEEKLY":
            # 获取该周的周一
            days_since_monday = current.weekday()
            monday = current - timedelta(days=days_since_monday)
            if monday.isoformat() not in dates:
                dates.append(monday.isoformat())
            # 跳到下一周
            current += timedelta(days=7 - days_since_monday)
        elif period == "MONTHLY":
            # 获取该月的第一天
            first_day = month_start(current)
            if first_day.isoformat() not in dates:
                dates.append(first_day.isoformat())
            # 跳到下个月
            _, m_end = get_month_range(current)
            current = m_end + timedelta(days=1)

    return sorted(dates)


def build_trend_statistics(
    alerts: List[AlertRecord],
    period: str
) -> Dict[str, Any]:
    """
    构建趋势统计数据

    Args:
        alerts: 预警记录列表
        period: 统计周期

    Returns:
        趋势统计数据字典
    """
    date_trends = {}
    level_trends = {}  # {date: {level: count}}
    type_trends = {}   # {date: {type: count}}
    status_trends = {} # {date: {status: count}}

    for alert in alerts:
        if not alert.triggered_at:
            continue

        period_key = get_period_key(alert.triggered_at, period)

        # 总数趋势
        date_trends[period_key] = date_trends.get(period_key, 0) + 1

        # 按级别统计趋势
        if period_key not in level_trends:
            level_trends[period_key] = {}
        level = alert.alert_level or "UNKNOWN"
        level_trends[period_key][level] = level_trends[period_key].get(level, 0) + 1

        # 按类型统计趋势
        if period_key not in type_trends:
            type_trends[period_key] = {}
        rule_type = alert.rule_type or "UNKNOWN"
        type_trends[period_key][rule_type] = type_trends[period_key].get(rule_type, 0) + 1

        # 按状态统计趋势
        if period_key not in status_trends:
            status_trends[period_key] = {}
        status = alert.status or "UNKNOWN"
        status_trends[period_key][status] = status_trends[period_key].get(status, 0) + 1

    return {
        'date_trends': date_trends,
        'level_trends': level_trends,
        'type_trends': type_trends,
        'status_trends': status_trends
    }


def build_summary_statistics(
    alerts: List[AlertRecord]
) -> Dict[str, Dict[str, int]]:
    """
    构建汇总统计

    Args:
        alerts: 预警记录列表

    Returns:
        汇总统计数据字典
    """
    total_by_level = {}
    total_by_type = {}
    total_by_status = {}

    for alert in alerts:
        level = alert.alert_level or "UNKNOWN"
        total_by_level[level] = total_by_level.get(level, 0) + 1

        rule_type = alert.rule_type or "UNKNOWN"
        total_by_type[rule_type] = total_by_type.get(rule_type, 0) + 1

        status = alert.status or "UNKNOWN"
        total_by_status[status] = total_by_status.get(status, 0) + 1

    return {
        'by_level': total_by_level,
        'by_type': total_by_type,
        'by_status': total_by_status
    }
