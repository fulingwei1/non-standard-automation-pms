# -*- coding: utf-8 -*-
"""
预警处理效率分析服务
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.project import Project
from app.models.user import User
from app.services.alert_rule_engine import AlertRuleEngine


def calculate_basic_metrics(
    all_alerts: List[AlertRecord],
    engine: AlertRuleEngine
) -> Dict[str, float]:
    """
    计算基础效率指标

    Returns:
        dict: 包含处理率、及时处理率、升级率、重复预警率的字典
    """
    total_count = len(all_alerts)

    if total_count == 0:
        return {
            'processing_rate': 0,
            'timely_processing_rate': 0,
            'escalation_rate': 0,
            'duplicate_rate': 0
        }

    # 已处理预警（状态为 RESOLVED 或 CLOSED）
    processed_alerts = [a for a in all_alerts if a.status in ['RESOLVED', 'CLOSED']]
    processed_count = len(processed_alerts)

    # 处理率
    processing_rate = processed_count / total_count if total_count > 0 else 0

    # 及时处理率（在响应时限内处理）
    timely_processed = 0
    for alert in processed_alerts:
        if alert.triggered_at and alert.acknowledged_at:
            response_time = (alert.acknowledged_at - alert.triggered_at).total_seconds() / 3600
            timeout_hours = engine.RESPONSE_TIMEOUT.get(alert.alert_level, 8)
            if response_time <= timeout_hours:
                timely_processed += 1

    timely_processing_rate = timely_processed / total_count if total_count > 0 else 0

    # 升级率
    escalated_alerts = [a for a in all_alerts if a.is_escalated]
    escalation_rate = len(escalated_alerts) / total_count if total_count > 0 else 0

    # 重复预警率（相同规则、相同目标、在短时间内重复触发）
    duplicate_count = 0
    seen_combinations = {}
    for alert in all_alerts:
        key = (alert.rule_id, alert.target_type, alert.target_id)
        if key in seen_combinations:
            # 检查是否在24小时内重复
            prev_alert = seen_combinations[key]
            if alert.triggered_at and prev_alert.triggered_at:
                time_diff = (alert.triggered_at - prev_alert.triggered_at).total_seconds() / 3600
                if time_diff < 24:  # 24小时内重复
                    duplicate_count += 1
        else:
            seen_combinations[key] = alert

    duplicate_rate = duplicate_count / total_count if total_count > 0 else 0

    return {
        'processing_rate': processing_rate,
        'timely_processing_rate': timely_processing_rate,
        'escalation_rate': escalation_rate,
        'duplicate_rate': duplicate_rate
    }


def calculate_project_metrics(
    all_alerts: List[AlertRecord],
    db: Session,
    engine: AlertRuleEngine
) -> Dict[str, Dict[str, Any]]:
    """
    按项目统计处理效率

    Returns:
        dict: 项目名称到效率指标的映射
    """
    efficiency_by_project = {}
    for alert in all_alerts:
        if alert.project_id:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_name = project.project_name if project else f"项目{alert.project_id}"
            if project_name not in efficiency_by_project:
                efficiency_by_project[project_name] = {
                    'project_id': alert.project_id,
                    'total': 0,
                    'processed': 0,
                    'timely_processed': 0,
                    'escalated': 0,
                    'duplicate': 0,
                }

            data = efficiency_by_project[project_name]
            data['total'] += 1
            if alert.status in ['RESOLVED', 'CLOSED']:
                data['processed'] += 1
                # 检查是否及时处理
                if alert.triggered_at and alert.acknowledged_at:
                    response_time = (alert.acknowledged_at - alert.triggered_at).total_seconds() / 3600
                    timeout_hours = engine.RESPONSE_TIMEOUT.get(alert.alert_level, 8)
                    if response_time <= timeout_hours:
                        data['timely_processed'] += 1
            if alert.is_escalated:
                data['escalated'] += 1

    # 计算项目效率指标
    project_metrics = {}
    for project_name, data in efficiency_by_project.items():
        project_metrics[project_name] = {
            'project_id': data['project_id'],
            'total': data['total'],
            'processing_rate': data['processed'] / data['total'] if data['total'] > 0 else 0,
            'timely_processing_rate': data['timely_processed'] / data['total'] if data['total'] > 0 else 0,
            'escalation_rate': data['escalated'] / data['total'] if data['total'] > 0 else 0,
            'efficiency_score': (
                (data['processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (data['timely_processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (1 - data['escalated'] / data['total'] if data['total'] > 0 else 0) * 0.2
            ) * 100,  # 效率得分（0-100）
        }

    return project_metrics


def calculate_handler_metrics(
    all_alerts: List[AlertRecord],
    db: Session,
    engine: AlertRuleEngine
) -> Dict[str, Dict[str, Any]]:
    """
    按责任人统计处理效率

    Returns:
        dict: 责任人名称到效率指标的映射
    """
    efficiency_by_handler = {}
    for alert in all_alerts:
        handler_id = alert.handler_id or alert.acknowledged_by
        if handler_id:
            handler = db.query(User).filter(User.id == handler_id).first()
            handler_name = handler.username if handler else f"用户{handler_id}"
            if handler_name not in efficiency_by_handler:
                efficiency_by_handler[handler_name] = {
                    'user_id': handler_id,
                    'total': 0,
                    'processed': 0,
                    'timely_processed': 0,
                    'escalated': 0,
                }

            data = efficiency_by_handler[handler_name]
            data['total'] += 1
            if alert.status in ['RESOLVED', 'CLOSED']:
                data['processed'] += 1
                # 检查是否及时处理
                if alert.triggered_at and alert.acknowledged_at:
                    response_time = (alert.acknowledged_at - alert.triggered_at).total_seconds() / 3600
                    timeout_hours = engine.RESPONSE_TIMEOUT.get(alert.alert_level, 8)
                    if response_time <= timeout_hours:
                        data['timely_processed'] += 1
            if alert.is_escalated:
                data['escalated'] += 1

    # 计算责任人效率指标
    handler_metrics = {}
    for handler_name, data in efficiency_by_handler.items():
        handler_metrics[handler_name] = {
            'user_id': data['user_id'],
            'total': data['total'],
            'processing_rate': data['processed'] / data['total'] if data['total'] > 0 else 0,
            'timely_processing_rate': data['timely_processed'] / data['total'] if data['total'] > 0 else 0,
            'escalation_rate': data['escalated'] / data['total'] if data['total'] > 0 else 0,
            'efficiency_score': (
                (data['processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (data['timely_processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (1 - data['escalated'] / data['total'] if data['total'] > 0 else 0) * 0.2
            ) * 100,  # 效率得分（0-100）
        }

    return handler_metrics


def calculate_type_metrics(
    all_alerts: List[AlertRecord],
    engine: AlertRuleEngine
) -> Dict[str, Dict[str, Any]]:
    """
    按类型统计处理效率

    Returns:
        dict: 类型名称到效率指标的映射
    """
    efficiency_by_type = {}
    for alert in all_alerts:
        rule = alert.rule
        rule_type = rule.rule_type if rule else 'UNKNOWN'
        if rule_type not in efficiency_by_type:
            efficiency_by_type[rule_type] = {
                'total': 0,
                'processed': 0,
                'timely_processed': 0,
                'escalated': 0,
            }

        data = efficiency_by_type[rule_type]
        data['total'] += 1
        if alert.status in ['RESOLVED', 'CLOSED']:
            data['processed'] += 1
            # 检查是否及时处理
            if alert.triggered_at and alert.acknowledged_at:
                response_time = (alert.acknowledged_at - alert.triggered_at).total_seconds() / 3600
                timeout_hours = engine.RESPONSE_TIMEOUT.get(alert.alert_level, 8)
                if response_time <= timeout_hours:
                    data['timely_processed'] += 1
        if alert.is_escalated:
            data['escalated'] += 1

    # 计算类型效率指标
    type_metrics = {}
    for rule_type, data in efficiency_by_type.items():
        type_metrics[rule_type] = {
            'total': data['total'],
            'processing_rate': data['processed'] / data['total'] if data['total'] > 0 else 0,
            'timely_processing_rate': data['timely_processed'] / data['total'] if data['total'] > 0 else 0,
            'escalation_rate': data['escalated'] / data['total'] if data['total'] > 0 else 0,
            'efficiency_score': (
                (data['processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (data['timely_processed'] / data['total'] if data['total'] > 0 else 0) * 0.4 +
                (1 - data['escalated'] / data['total'] if data['total'] > 0 else 0) * 0.2
            ) * 100,  # 效率得分（0-100）
        }

    return type_metrics


def generate_rankings(
    project_metrics: Dict[str, Dict[str, Any]],
    handler_metrics: Dict[str, Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    生成效率排行榜

    Returns:
        dict: 包含最佳/最差项目和责任人的排行榜
    """
    # 效率最高的项目（效率得分最高，至少5个预警）
    best_projects = sorted(
        [(name, data) for name, data in project_metrics.items() if data['total'] >= 5],
        key=lambda x: x[1]['efficiency_score'],
        reverse=True
    )[:5]

    # 效率最低的项目（效率得分最低，至少5个预警）
    worst_projects = sorted(
        [(name, data) for name, data in project_metrics.items() if data['total'] >= 5],
        key=lambda x: x[1]['efficiency_score']
    )[:5]

    # 效率最高的责任人（效率得分最高，至少5个预警）
    best_handlers = sorted(
        [(name, data) for name, data in handler_metrics.items() if data['total'] >= 5],
        key=lambda x: x[1]['efficiency_score'],
        reverse=True
    )[:5]

    # 效率最低的责任人（效率得分最低，至少5个预警）
    worst_handlers = sorted(
        [(name, data) for name, data in handler_metrics.items() if data['total'] >= 5],
        key=lambda x: x[1]['efficiency_score']
    )[:5]

    return {
        'best_projects': [
            {
                'project_name': name,
                'project_id': data['project_id'],
                'efficiency_score': data['efficiency_score'],
                'processing_rate': data['processing_rate'],
                'timely_processing_rate': data['timely_processing_rate'],
                'total': data['total'],
            }
            for name, data in best_projects
        ],
        'worst_projects': [
            {
                'project_name': name,
                'project_id': data['project_id'],
                'efficiency_score': data['efficiency_score'],
                'processing_rate': data['processing_rate'],
                'timely_processing_rate': data['timely_processing_rate'],
                'total': data['total'],
            }
            for name, data in worst_projects
        ],
        'best_handlers': [
            {
                'handler_name': name,
                'user_id': data['user_id'],
                'efficiency_score': data['efficiency_score'],
                'processing_rate': data['processing_rate'],
                'timely_processing_rate': data['timely_processing_rate'],
                'total': data['total'],
            }
            for name, data in best_handlers
        ],
        'worst_handlers': [
            {
                'handler_name': name,
                'user_id': data['user_id'],
                'efficiency_score': data['efficiency_score'],
                'processing_rate': data['processing_rate'],
                'timely_processing_rate': data['timely_processing_rate'],
                'total': data['total'],
            }
            for name, data in worst_handlers
        ],
    }
