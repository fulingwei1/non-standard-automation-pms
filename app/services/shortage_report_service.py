# -*- coding: utf-8 -*-
"""
缺料日报生成服务

提取缺料日报统计和生成逻辑
使用统一的 AlertRecord 表，通过 target_type='SHORTAGE' 筛选缺料预警
"""

from datetime import date
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.shortage import (
    KitCheck,
    MaterialArrival,
    ShortageReport,
)


def calculate_alert_statistics(
    db: Session,
    target_date: date
) -> Dict[str, Any]:
    """
    计算预警统计（使用统一 AlertRecord 表）

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        预警统计数据字典
    """
    # 基础查询：筛选缺料类型预警
    base_query = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'SHORTAGE'
    )

    new_alerts = base_query.filter(
        func.date(AlertRecord.created_at) == target_date
    ).count()

    resolved_alerts = base_query.filter(
        AlertRecord.handle_end_at.isnot(None),
        func.date(AlertRecord.handle_end_at) == target_date
    ).count()

    pending_alerts = base_query.filter(
        AlertRecord.status.in_(["PENDING", "PROCESSING", "pending", "handling", "escalated"])
    ).count()

    # 检查 is_overdue 需要从 alert_data JSON 中提取
    # 简化处理：暂时返回 0，实际项目中可能需要更复杂的 JSON 查询
    overdue_alerts = 0

    # 按预警级别统计（同时支持新旧级别命名）
    level_counts = {}
    level_mapping = {
        'level1': ['level1', 'INFO'],
        'level2': ['level2', 'WARNING'],
        'level3': ['level3', 'CRITICAL'],
        'level4': ['level4', 'URGENT']
    }
    for level_key, level_values in level_mapping.items():
        level_counts[level_key] = base_query.filter(
            AlertRecord.alert_level.in_(level_values)
        ).count()

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
    计算响应与解决耗时统计（使用统一 AlertRecord 表）

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        响应时间统计数据字典
    """
    alerts_for_response = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'SHORTAGE',
        func.date(AlertRecord.created_at) == target_date
    ).all()

    response_minutes = [
        (alert.handle_start_at - alert.created_at).total_seconds() / 60.0
        for alert in alerts_for_response
        if alert.handle_start_at and alert.created_at
    ]
    avg_response_minutes = int(round(
        sum(response_minutes) / len(response_minutes), 0
    )) if response_minutes else 0

    resolved_alerts_list = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'SHORTAGE',
        AlertRecord.handle_end_at.isnot(None),
        func.date(AlertRecord.handle_end_at) == target_date
    ).all()

    resolve_hours = [
        (alert.handle_end_at - alert.created_at).total_seconds() / 3600.0
        for alert in resolved_alerts_list
        if alert.handle_end_at and alert.created_at
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
    计算停工影响统计（使用统一 AlertRecord 表）

    停工信息存储在 alert_data JSON 中：
    - impact_type: 影响类型 (stop/delay/delivery)
    - estimated_delay_days: 预计延迟天数

    Args:
        db: 数据库会话
        target_date: 目标日期

    Returns:
        停工统计数据字典
    """
    import json

    alerts = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'SHORTAGE',
        func.date(AlertRecord.created_at) == target_date
    ).all()

    stoppage_count = 0
    total_delay_days = 0

    for alert in alerts:
        alert_data = {}
        if alert.alert_data:
            try:
                alert_data = json.loads(alert.alert_data) if isinstance(alert.alert_data, str) else alert.alert_data
            except (json.JSONDecodeError, TypeError):
                alert_data = {}

        if alert_data.get('impact_type') == 'stop':
            stoppage_count += 1
            total_delay_days += alert_data.get('estimated_delay_days', 0) or 0

    stoppage_hours = round(total_delay_days * 24, 2)

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
