# -*- coding: utf-8 -*-
"""
STATISTICS - 自动生成
从 alerts.py 拆分
"""

from typing import Any, List, Optional

from datetime import date, datetime, timedelta

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload, selectinload

from sqlalchemy import or_, and_, func, case

from app.api import deps

from app.core import security

from app.core.config import settings

from app.models.user import User

from app.models.project import Project, Machine

from app.models.issue import Issue

from app.models.alert import (
    AlertRule, AlertRuleTemplate, AlertRecord, AlertNotification,
    ExceptionEvent, ExceptionAction, ExceptionEscalation,
    AlertStatistics, ProjectHealthSnapshot, AlertSubscription
)
from app.schemas.alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertRecordHandle, AlertRecordResponse, AlertRecordListResponse,
    ExceptionEventCreate, ExceptionEventUpdate, ExceptionEventResolve,
    ExceptionEventVerify, ExceptionEventResponse, ExceptionEventListResponse,
    ProjectHealthResponse, AlertStatisticsResponse,
    AlertSubscriptionCreate, AlertSubscriptionUpdate, AlertSubscriptionResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter(tags=["statistics"])

# ==================== 路由定义 ====================
# 共 5 个路由

@router.get("/alerts/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警统计分析
    """
    query = db.query(AlertRecord)
    
    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)
    
    if start_date:
        query = query.filter(AlertRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AlertRecord.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    alerts = query.all()
    
    # 按级别统计
    by_level = {}
    for alert in alerts:
        level = alert.alert_level or "UNKNOWN"
        by_level[level] = by_level.get(level, 0) + 1
    
    # 按类型统计
    by_type = {}
    for alert in alerts:
        rule_type = alert.rule_type or "UNKNOWN"
        by_type[rule_type] = by_type.get(rule_type, 0) + 1
    
    # 按状态统计
    by_status = {}
    for alert in alerts:
        status = alert.status or "UNKNOWN"
        by_status[status] = by_status.get(status, 0) + 1
    
    # 按项目统计
    by_project = {}
    for alert in alerts:
        if alert.project_id:
            project = db.query(Project).filter(Project.id == alert.project_id).first()
            project_name = project.project_name if project else f"项目{alert.project_id}"
            by_project[project_name] = by_project.get(project_name, 0) + 1
    
    # 趋势统计（按日期）
    by_date = {}
    for alert in alerts:
        if alert.created_at:
            date_key = alert.created_at.date().isoformat()
            by_date[date_key] = by_date.get(date_key, 0) + 1
    
    return {
        "total_alerts": len(alerts),
        "by_level": by_level,
        "by_type": by_type,
        "by_status": by_status,
        "by_project": by_project,
        "by_date": dict(sorted(by_date.items())),
        "summary": {
            "open_count": by_status.get("OPEN", 0),
            "acknowledged_count": by_status.get("ACKNOWLEDGED", 0),
            "resolved_count": by_status.get("RESOLVED", 0),
            "critical_count": by_level.get("CRITICAL", 0),
            "high_count": by_level.get("HIGH", 0),
        }
    }


@router.get("/alerts/statistics/trends", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_trends(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    period: str = Query("DAILY", description="统计周期: DAILY/WEEKLY/MONTHLY"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警趋势分析数据
    
    返回多维度趋势数据：
    - 按日期统计（日/周/月）
    - 按级别统计趋势
    - 按类型统计趋势
    - 按状态统计趋势
    """
    from datetime import timedelta
    from app.services.alert_trend_service import (
        build_trend_statistics,
        build_summary_statistics,
        generate_date_range
    )
    
    # 默认时间范围：最近30天
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = db.query(AlertRecord).filter(
        AlertRecord.triggered_at.isnot(None)
    )
    
    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)
    
    query = query.filter(
        AlertRecord.triggered_at >= datetime.combine(start_date, datetime.min.time()),
        AlertRecord.triggered_at <= datetime.combine(end_date, datetime.max.time())
    )
    
    alerts = query.all()
    
    # 构建趋势统计
    trend_stats = build_trend_statistics(alerts, period)
    date_trends = trend_stats['date_trends']
    level_trends = trend_stats['level_trends']
    type_trends = trend_stats['type_trends']
    status_trends = trend_stats['status_trends']
    
    # 生成完整的时间序列
    date_range = generate_date_range(start_date, end_date, period)
    
    # 构建趋势数据数组
    trends_data = []
    for date_key in date_range:
        trends_data.append({
            "date": date_key,
            "total": date_trends.get(date_key, 0),
            "by_level": level_trends.get(date_key, {}),
            "by_type": type_trends.get(date_key, {}),
            "by_status": status_trends.get(date_key, {}),
        })
    
    # 汇总统计
    summary_stats = build_summary_statistics(alerts)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trends": trends_data,
        "summary": {
            "total": len(alerts),
            "by_level": summary_stats['by_level'],
            "by_type": summary_stats['by_type'],
            "by_status": summary_stats['by_status'],
        }
    }


@router.get("/alerts/statistics/dashboard", response_model=dict, status_code=status.HTTP_200_OK)
def get_alert_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    预警中心仪表板统计数据
    返回：活跃预警统计、今日新增/关闭数量等
    """
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 活跃预警统计（按级别）
    active_query = db.query(AlertRecord).filter(
        AlertRecord.status.in_(["PENDING", "ACKNOWLEDGED"])
    )
    
    total_active = active_query.count()
    
    urgent_count = active_query.filter(AlertRecord.alert_level == "URGENT").count()
    critical_count = active_query.filter(AlertRecord.alert_level == "CRITICAL").count()
    warning_count = active_query.filter(AlertRecord.alert_level == "WARNING").count()
    info_count = active_query.filter(AlertRecord.alert_level == "INFO").count()
    
    # 今日新增预警
    today_new = db.query(AlertRecord).filter(
        AlertRecord.triggered_at >= today_start,
        AlertRecord.triggered_at <= today_end
    ).count()
    
    # 今日关闭的预警
    today_closed = db.query(AlertRecord).filter(
        AlertRecord.status == "CLOSED",
        AlertRecord.handle_end_at >= today_start,
        AlertRecord.handle_end_at <= today_end
    ).count()
    
    # 今日处理的预警（包括已解决和已关闭）
    today_processed = db.query(AlertRecord).filter(
        AlertRecord.status.in_(["RESOLVED", "CLOSED"]),
        AlertRecord.handle_end_at >= today_start,
        AlertRecord.handle_end_at <= today_end
    ).count()
    
    return {
        "active_alerts": {
            "total": total_active,
            "urgent": urgent_count,
            "critical": critical_count,
            "warning": warning_count,
            "info": info_count,
        },
        "today_new": today_new,
        "today_closed": today_closed,
        "today_processed": today_processed,
    }


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
        calculate_response_times,
        calculate_resolve_times,
        calculate_response_distribution,
        calculate_level_metrics,
        calculate_type_metrics,
        calculate_project_metrics,
        calculate_handler_metrics,
        generate_response_rankings
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
    from app.services.alert_rule_engine import AlertRuleEngine
    from app.services.alert_efficiency_service import (
        calculate_basic_metrics,
        calculate_project_metrics,
        calculate_handler_metrics,
        calculate_type_metrics,
        generate_rankings
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


