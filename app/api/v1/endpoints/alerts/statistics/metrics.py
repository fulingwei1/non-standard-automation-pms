# -*- coding: utf-8 -*-
"""
预警统计 - 指标分析
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.alert import AlertRecord
from app.models.user import User

router = APIRouter()


@router.get("/alerts/statistics/response-metrics", response_model=dict, status_code=status.HTTP_200_OK)
def get_response_metrics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警响应时效分析

    返回：
    - 平均响应时间（确认时间 - 触发时间）
    - 平均解决时间（处理完成时间 - 确认时间）
    - 响应时效分布（<1小时、1-4小时、4-8小时、>8小时）
    - 按级别统计响应时效
    - 按类型统计响应时效
    - 响应时效排行榜（最快/最慢的项目/责任人）
    """
    from app.services.alert_response_service import (
        calculate_handler_metrics,
        calculate_level_metrics,
        calculate_project_metrics,
        calculate_resolve_times,
        calculate_response_distribution,
        calculate_response_times,
        calculate_type_metrics,
        generate_response_rankings,
    )

    query = db.query(AlertRecord).filter(
        AlertRecord.triggered_at.isnot(None)
    )

    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)

    if start_date:
        query = query.filter(AlertRecord.triggered_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AlertRecord.triggered_at <= datetime.combine(end_date, datetime.max.time()))

    # 查询已确认的预警（用于计算响应时间）
    acknowledged_alerts = query.filter(
        AlertRecord.acknowledged_at.isnot(None),
        AlertRecord.triggered_at.isnot(None)
    ).all()

    # 查询已处理的预警（用于计算解决时间）
    resolved_alerts = query.filter(
        AlertRecord.acknowledged_at.isnot(None),
        AlertRecord.handle_end_at.isnot(None)
    ).all()

    # 计算响应时间和解决时间
    response_times = calculate_response_times(acknowledged_alerts)
    resolve_times = calculate_resolve_times(resolved_alerts)

    # 平均响应时间和解决时间
    avg_response_time = sum(rt['hours'] for rt in response_times) / len(response_times) if response_times else 0
    avg_resolve_time = sum(rt['hours'] for rt in resolve_times) / len(resolve_times) if resolve_times else 0

    # 计算各项指标
    response_distribution = calculate_response_distribution(response_times)
    level_metrics = calculate_level_metrics(response_times)
    type_metrics = calculate_type_metrics(response_times)
    project_metrics = calculate_project_metrics(response_times, db)
    handler_metrics = calculate_handler_metrics(response_times, db)
    rankings = generate_response_rankings(project_metrics, handler_metrics)

    return {
        'summary': {
            'total_acknowledged': len(acknowledged_alerts),
            'total_resolved': len(resolved_alerts),
            'avg_response_time_hours': round(avg_response_time, 2),
            'avg_resolve_time_hours': round(avg_resolve_time, 2),
        },
        'response_distribution': response_distribution,
        'by_level': {
            level: {
                'avg_hours': round(metrics['avg_hours'], 2),
                'min_hours': round(metrics['min_hours'], 2),
                'max_hours': round(metrics['max_hours'], 2),
                'count': metrics['count'],
            }
            for level, metrics in level_metrics.items()
        },
        'by_type': {
            rule_type: {
                'avg_hours': round(metrics['avg_hours'], 2),
                'min_hours': round(metrics['min_hours'], 2),
                'max_hours': round(metrics['max_hours'], 2),
                'count': metrics['count'],
            }
            for rule_type, metrics in type_metrics.items()
        },
        'by_project': {
            project_name: {
                'project_id': data['project_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'min_hours': round(data['min_hours'], 2),
                'max_hours': round(data['max_hours'], 2),
                'count': data['count'],
            }
            for project_name, data in project_metrics.items()
        },
        'by_handler': {
            handler_name: {
                'user_id': data['user_id'],
                'avg_hours': round(data['avg_hours'], 2),
                'min_hours': round(data['min_hours'], 2),
                'max_hours': round(data['max_hours'], 2),
                'count': data['count'],
            }
            for handler_name, data in handler_metrics.items()
        },
        'rankings': rankings,
    }


@router.get("/alerts/statistics/efficiency-metrics", response_model=dict, status_code=status.HTTP_200_OK)
def get_efficiency_metrics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警处理效率分析

    返回：
    - 处理率（已处理数 / 总数）
    - 及时处理率（在响应时限内处理的比例）
    - 升级率（升级预警数 / 总数）
    - 重复预警率（重复预警数 / 总数）
    - 按项目、责任人、类型统计处理效率
    - 处理效率排行榜
    """
    from app.services.alert_efficiency_service import (
        calculate_basic_metrics,
        calculate_handler_metrics,
        calculate_project_metrics,
        calculate_type_metrics,
        generate_rankings,
    )
    from app.services.alert_rule_engine import AlertRuleEngine

    query = db.query(AlertRecord).filter(
        AlertRecord.triggered_at.isnot(None)
    )

    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)

    if start_date:
        query = query.filter(AlertRecord.triggered_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AlertRecord.triggered_at <= datetime.combine(end_date, datetime.max.time()))

    all_alerts = query.all()
    total_count = len(all_alerts)

    if total_count == 0:
        return {
            'summary': {
                'total': 0,
                'processed_count': 0,
                'processing_rate': 0,
                'timely_processing_rate': 0,
                'escalation_rate': 0,
                'duplicate_rate': 0,
            },
            'by_project': {},
            'by_handler': {},
            'by_type': {},
            'rankings': {
                'best_projects': [],
                'worst_projects': [],
                'best_handlers': [],
                'worst_handlers': [],
            },
        }

    # 初始化引擎
    engine = AlertRuleEngine(db)

    # 计算基础指标
    basic_metrics = calculate_basic_metrics(all_alerts, engine)
    processed_count = len([a for a in all_alerts if a.status in ['RESOLVED', 'CLOSED']])

    # 按维度统计
    project_metrics = calculate_project_metrics(all_alerts, db, engine)
    handler_metrics = calculate_handler_metrics(all_alerts, db, engine)
    type_metrics = calculate_type_metrics(all_alerts, engine)

    # 生成排行榜
    rankings = generate_rankings(project_metrics, handler_metrics)

    # 格式化返回数据
    return {
        'summary': {
            'total': total_count,
            'processed_count': processed_count,
            'processing_rate': round(basic_metrics['processing_rate'], 4),
            'timely_processing_rate': round(basic_metrics['timely_processing_rate'], 4),
            'escalation_rate': round(basic_metrics['escalation_rate'], 4),
            'duplicate_rate': round(basic_metrics['duplicate_rate'], 4),
        },
        'by_project': {
            project_name: {
                'project_id': data['project_id'],
                'total': data['total'],
                'processing_rate': round(data['processing_rate'], 4),
                'timely_processing_rate': round(data['timely_processing_rate'], 4),
                'escalation_rate': round(data['escalation_rate'], 4),
                'efficiency_score': round(data['efficiency_score'], 2),
            }
            for project_name, data in project_metrics.items()
        },
        'by_handler': {
            handler_name: {
                'user_id': data['user_id'],
                'total': data['total'],
                'processing_rate': round(data['processing_rate'], 4),
                'timely_processing_rate': round(data['timely_processing_rate'], 4),
                'escalation_rate': round(data['escalation_rate'], 4),
                'efficiency_score': round(data['efficiency_score'], 2),
            }
            for handler_name, data in handler_metrics.items()
        },
        'by_type': {
            rule_type: {
                'total': data['total'],
                'processing_rate': round(data['processing_rate'], 4),
                'timely_processing_rate': round(data['timely_processing_rate'], 4),
                'escalation_rate': round(data['escalation_rate'], 4),
            }
            for rule_type, data in type_metrics.items()
        },
        'rankings': rankings,
    }
