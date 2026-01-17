# -*- coding: utf-8 -*-
"""
预警响应时效分析服务
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.project import Project
from app.models.user import User


def calculate_response_times(
    acknowledged_alerts: List[AlertRecord]
) -> List[Dict[str, Any]]:
    """
    计算响应时间（确认时间 - 触发时间）

    Returns:
        List[Dict]: 包含 alert、minutes、hours 的列表
    """
    response_times = []
    for alert in acknowledged_alerts:
        if alert.triggered_at and alert.acknowledged_at:
            delta = alert.acknowledged_at - alert.triggered_at
            minutes = delta.total_seconds() / 60
            response_times.append({
                'alert': alert,
                'minutes': minutes,
                'hours': minutes / 60,
            })
    return response_times


def calculate_resolve_times(
    resolved_alerts: List[AlertRecord]
) -> List[Dict[str, Any]]:
    """
    计算解决时间（处理完成时间 - 确认时间）

    Returns:
        List[Dict]: 包含 alert、minutes、hours 的列表
    """
    resolve_times = []
    for alert in resolved_alerts:
        if alert.acknowledged_at and alert.handle_end_at:
            delta = alert.handle_end_at - alert.acknowledged_at
            minutes = delta.total_seconds() / 60
            resolve_times.append({
                'alert': alert,
                'minutes': minutes,
                'hours': minutes / 60,
            })
    return resolve_times


def calculate_response_distribution(
    response_times: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    计算响应时效分布

    Returns:
        dict: 包含 <1小时、1-4小时、4-8小时、>8小时 的分布
    """
    distribution = {
        '<1小时': 0,
        '1-4小时': 0,
        '4-8小时': 0,
        '>8小时': 0,
    }
    for rt in response_times:
        hours = rt['hours']
        if hours < 1:
            distribution['<1小时'] += 1
        elif hours < 4:
            distribution['1-4小时'] += 1
        elif hours < 8:
            distribution['4-8小时'] += 1
        else:
            distribution['>8小时'] += 1
    return distribution


def calculate_level_metrics(
    response_times: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """
    按级别统计响应时效

    Returns:
        dict: 级别名称到统计指标的映射
    """
    response_by_level = {}
    for rt in response_times:
        level = rt['alert'].alert_level or 'UNKNOWN'
        if level not in response_by_level:
            response_by_level[level] = []
        response_by_level[level].append(rt['hours'])

    level_metrics = {}
    for level, times in response_by_level.items():
        level_metrics[level] = {
            'count': len(times),
            'avg_hours': sum(times) / len(times) if times else 0,
            'min_hours': min(times) if times else 0,
            'max_hours': max(times) if times else 0,
        }
    return level_metrics


def calculate_type_metrics(
    response_times: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """
    按类型统计响应时效

    Returns:
        dict: 类型名称到统计指标的映射
    """
    response_by_type = {}
    for rt in response_times:
        rule = rt['alert'].rule
        rule_type = rule.rule_type if rule else 'UNKNOWN'
        if rule_type not in response_by_type:
            response_by_type[rule_type] = []
        response_by_type[rule_type].append(rt['hours'])

    type_metrics = {}
    for rule_type, times in response_by_type.items():
        type_metrics[rule_type] = {
            'count': len(times),
            'avg_hours': sum(times) / len(times) if times else 0,
            'min_hours': min(times) if times else 0,
            'max_hours': max(times) if times else 0,
        }
    return type_metrics


def calculate_project_metrics(
    response_times: List[Dict[str, Any]],
    db: Session
) -> Dict[str, Dict[str, Any]]:
    """
    按项目统计响应时效

    Returns:
        dict: 项目名称到统计指标的映射
    """
    response_by_project = {}
    for rt in response_times:
        alert = rt['alert']
        if alert.project_id:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_name = project.project_name if project else f"项目{alert.project_id}"
            if project_name not in response_by_project:
                response_by_project[project_name] = {
                    'project_id': alert.project_id,
                    'times': [],
                }
            response_by_project[project_name]['times'].append(rt['hours'])

    project_metrics = {}
    for project_name, data in response_by_project.items():
        times = data['times']
        project_metrics[project_name] = {
            'project_id': data['project_id'],
            'count': len(times),
            'avg_hours': sum(times) / len(times) if times else 0,
            'min_hours': min(times) if times else 0,
            'max_hours': max(times) if times else 0,
        }
    return project_metrics


def calculate_handler_metrics(
    response_times: List[Dict[str, Any]],
    db: Session
) -> Dict[str, Dict[str, Any]]:
    """
    按责任人统计响应时效

    Returns:
        dict: 责任人名称到统计指标的映射
    """
    response_by_handler = {}
    for rt in response_times:
        alert = rt['alert']
        handler_id = alert.acknowledged_by
        if handler_id:
            handler = db.query(User).filter(User.id == handler_id).first()
            handler_name = handler.username if handler else f"用户{handler_id}"
            if handler_name not in response_by_handler:
                response_by_handler[handler_name] = {
                    'user_id': handler_id,
                    'times': [],
                }
            response_by_handler[handler_name]['times'].append(rt['hours'])

    handler_metrics = {}
    for handler_name, data in response_by_handler.items():
        times = data['times']
        handler_metrics[handler_name] = {
            'user_id': data['user_id'],
            'count': len(times),
            'avg_hours': sum(times) / len(times) if times else 0,
            'min_hours': min(times) if times else 0,
            'max_hours': max(times) if times else 0,
        }
    return handler_metrics


def generate_response_rankings(
    project_metrics: Dict[str, Dict[str, Any]],
    handler_metrics: Dict[str, Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    生成响应时效排行榜

    Returns:
        dict: 包含最快/最慢项目和责任人的排行榜
    """
    # 最快的项目（平均响应时间最短）
    fastest_projects = sorted(
        [(name, data) for name, data in project_metrics.items()],
        key=lambda x: x[1]['avg_hours']
    )[:5]

    # 最慢的项目（平均响应时间最长）
    slowest_projects = sorted(
        [(name, data) for name, data in project_metrics.items()],
        key=lambda x: x[1]['avg_hours'],
        reverse=True
    )[:5]

    # 最快的责任人（平均响应时间最短）
    fastest_handlers = sorted(
        [(name, data) for name, data in handler_metrics.items()],
        key=lambda x: x[1]['avg_hours']
    )[:5]

    # 最慢的责任人（平均响应时间最长）
    slowest_handlers = sorted(
        [(name, data) for name, data in handler_metrics.items()],
        key=lambda x: x[1]['avg_hours'],
        reverse=True
    )[:5]

    return {
        'fastest_projects': [
            {
                'project_name': name,
                'project_id': data['project_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'count': data['count'],
            }
            for name, data in fastest_projects
        ],
        'slowest_projects': [
            {
                'project_name': name,
                'project_id': data['project_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'count': data['count'],
            }
            for name, data in slowest_projects
        ],
        'fastest_handlers': [
            {
                'handler_name': name,
                'user_id': data['user_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'count': data['count'],
            }
            for name, data in fastest_handlers
        ],
        'slowest_handlers': [
            {
                'handler_name': name,
                'user_id': data['user_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'count': data['count'],
            }
            for name, data in slowest_handlers
        ],
    }
