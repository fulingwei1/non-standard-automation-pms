# -*- coding: utf-8 -*-
"""
缺料日报生成服务

提取缺料日报统计和生成逻辑
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.shortage import (
    KitCheck,
    MaterialArrival,
    ShortageAlert,
    ShortageDailyReport,
    ShortageReport,
)


def calculate_alert_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算预警统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        预警统计数据字典
    """
    new_alerts = db.query(func.count(ShortageAlert.id)).filter(
        func.date(ShortageAlert.created_at) == target_date
    ).scalar() or 0

    resolved_alerts = db.query(func.count(ShortageAlert.id)).filter(
        ShortageAlert.resolve_time.isnot(None),
        func.date(ShortageAlert.resolve_time) == target_date
    ).scalar() or 0

    pending_alerts = db.query(func.count(ShortageAlert.id)).filter(
        ShortageAlert.status.in_(["pending", "handling", "escalated"])
    ).scalar() or 0

    overdue_alerts = db.query(func.count(ShortageAlert.id)).filter(
        ShortageAlert.is_overdue == True
    ).scalar() or 0

    level_counts = {}
    for level in ['level1', 'level2', 'level3', 'level4']:
        level_counts[level] = db.query(func.count(ShortageAlert.id)).filter(
            ShortageAlert.alert_level == level
        ).scalar() or 0

    return {
        'new_alerts': new_alerts,
        'resolved_alerts': resolved_alerts,
        'pending_alerts': pending_alerts,
        'overdue_alerts': overdue_alerts,
        'level_counts': level_counts
    }


def calculate_report_statistics(
    db: Session,
    target_date: date
) -> Dict[str, int]:
    """
    计算上报统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        上报统计数据字典
    """
    new_reports = db.query(func.count(ShortageReport.id)).filter(
        func.date(ShortageReport.report_time) == target_date
    ).scalar() or 0

    resolved_reports = db.query(func.count(ShortageReport.id)).filter(
        ShortageReport.resolved_at.isnot(None),
        func.date(ShortageReport.resolved_at) == target_date
    ).scalar() or 0

    return {
        'new_reports': new_reports,
        'resolved_reports': resolved_reports
    }


def calculate_kit_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算齐套统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        齐套统计数据字典
    """
    kit_checks = db.query(KitCheck).filter(
        func.date(KitCheck.check_time) == target_date
    ).all()

    total_work_orders = len(kit_checks)
    kit_complete_count = len([k for k in kit_checks if (k.kit_status or '').lower() == 'complete'])
    kit_rate = round(
        sum(float(k.kit_rate or 0) for k in kit_checks) / total_work_orders,
        2
    ) if total_work_orders else 0.0

    return {
        'total_work_orders': total_work_orders,
        'kit_complete_count': kit_complete_count,
        'kit_rate': kit_rate
    }


def calculate_arrival_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算到货统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        到货统计数据字典
    """
    expected_arrivals = db.query(func.count(MaterialArrival.id)).filter(
        MaterialArrival.expected_date == target_date
    ).scalar() or 0

    actual_arrivals = db.query(func.count(MaterialArrival.id)).filter(
        MaterialArrival.actual_date == target_date
    ).scalar() or 0

    delayed_arrivals = db.query(func.count(MaterialArrival.id)).filter(
        MaterialArrival.actual_date == target_date,
        MaterialArrival.is_delayed == True
    ).scalar() or 0

    on_time_rate = round(
        ((actual_arrivals - delayed_arrivals) / actual_arrivals) * 100,
        2
    ) if actual_arrivals else 0.0

    return {
        'expected_arrivals': expected_arrivals,
        'actual_arrivals': actual_arrivals,
        'delayed_arrivals': delayed_arrivals,
        'on_time_rate': on_time_rate
    }


def calculate_response_time_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算响应与解决耗时统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        响应时间统计数据字典
    """
    alerts_for_response = db.query(ShortageAlert).filter(
        func.date(ShortageAlert.created_at) == target_date
    ).all()

    response_minutes = [
        (alert.handle_start_time - alert.created_at).total_seconds() / 60.0
        for alert in alerts_for_response
        if alert.handle_start_time and alert.created_at
    ]
    avg_response_minutes = int(round(
        sum(response_minutes) / len(response_minutes), 0
    )) if response_minutes else 0

    resolved_alerts_list = db.query(ShortageAlert).filter(
        ShortageAlert.resolve_time.isnot(None),
        func.date(ShortageAlert.resolve_time) == target_date
    ).all()

    resolve_hours = [
        (alert.resolve_time - alert.created_at).total_seconds() / 3600.0
        for alert in resolved_alerts_list
        if alert.resolve_time and alert.created_at
    ]
    avg_resolve_hours = round(
        sum(resolve_hours) / len(resolve_hours), 2
    ) if resolve_hours else 0.0

    return {
        'avg_response_minutes': avg_response_minutes,
        'avg_resolve_hours': avg_resolve_hours
    }


def calculate_stoppage_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算停工影响统计

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        停工统计数据字典
    """
    stoppage_alerts = db.query(ShortageAlert).filter(
        func.date(ShortageAlert.created_at) == target_date,
        ShortageAlert.impact_type == 'stop'
    ).all()

    stoppage_count = len(stoppage_alerts)
    stoppage_hours = round(
        sum((alert.estimated_delay_days or 0) * 24 for alert in stoppage_alerts),
        2
    )

    return {
        'stoppage_count': stoppage_count,
        'stoppage_hours': stoppage_hours
    }


def build_daily_report_data(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    构建缺料日报数据

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        日报数据字典
    """
    alert_stats = calculate_alert_statistics(db, target_date)
    report_stats = calculate_report_statistics(db, target_date)
    kit_stats = calculate_kit_statistics(db, target_date)
    arrival_stats = calculate_arrival_statistics(db, target_date)
    response_stats = calculate_response_time_statistics(db, target_date)
    stoppage_stats = calculate_stoppage_statistics(db, target_date)

    return {
        **alert_stats,
        **report_stats,
        **kit_stats,
        **arrival_stats,
        **response_stats,
        **stoppage_stats
    }
