# -*- coding: utf-8 -*-
"""
项目统计服务
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.project import Project


def calculate_status_statistics(query) -> Dict[str, int]:
    """
    按状态统计项目
    
    Returns:
        Dict[str, int]: 状态到数量的映射
    """
    status_stats = (
        query.with_entities(Project.status, func.count(Project.id).label('count'))
        .group_by(Project.status)
        .all()
    )
    return {status: count for status, count in status_stats if status}


def calculate_stage_statistics(query) -> Dict[str, int]:
    """
    按阶段统计项目
    
    Returns:
        Dict[str, int]: 阶段到数量的映射
    """
    stage_stats = (
        query.with_entities(Project.stage, func.count(Project.id).label('count'))
        .group_by(Project.stage)
        .all()
    )
    return {stage: count for stage, count in stage_stats if stage}


def calculate_health_statistics(query) -> Dict[str, int]:
    """
    按健康度统计项目
    
    Returns:
        Dict[str, int]: 健康度到数量的映射
    """
    health_stats = (
        query.with_entities(Project.health, func.count(Project.id).label('count'))
        .group_by(Project.health)
        .all()
    )
    return {health: count for health, count in health_stats if health}


def calculate_pm_statistics(query) -> List[Dict[str, Any]]:
    """
    按项目经理统计项目
    
    Returns:
        List[Dict]: 项目经理统计列表
    """
    pm_query = query.filter(Project.pm_id.isnot(None))
    pm_stats = (
        pm_query.with_entities(
            Project.pm_id, Project.pm_name, func.count(Project.id).label('count')
        )
        .group_by(Project.pm_id, Project.pm_name)
        .all()
    )
    
    return [
        {
            "pm_id": pm_id,
            "pm_name": pm_name or "未分配",
            "count": count
        }
        for pm_id, pm_name, count in pm_stats
    ]


def calculate_customer_statistics(query) -> List[Dict[str, Any]]:
    """
    按客户统计项目
    
    Returns:
        List[Dict]: 客户统计列表
    """
    customer_query = query.filter(Project.customer_id.isnot(None))
    customer_stats = (
        customer_query.with_entities(
            Project.customer_id,
            Project.customer_name,
            func.count(Project.id).label('count'),
            func.sum(Project.contract_amount).label('total_amount')
        )
        .group_by(Project.customer_id, Project.customer_name)
        .all()
    )
    
    return [
        {
            "customer_id": customer_id,
            "customer_name": customer_name or "未知客户",
            "count": count,
            "total_amount": float(total_amount or 0),
        }
        for customer_id, customer_name, count, total_amount in customer_stats
    ]


def calculate_monthly_statistics(
    query,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    按月份统计项目
    
    Returns:
        List[Dict]: 月份统计列表
    """
    month_query = query.filter(
        Project.created_at >= datetime.combine(start_date, datetime.min.time()),
        Project.created_at <= datetime.combine(end_date, datetime.max.time())
    )
    
    # 尝试使用extract（适用于大多数数据库）
    try:
        month_stats = (
            month_query.with_entities(
                extract('year', Project.created_at).label('year'),
                extract('month', Project.created_at).label('month'),
                func.count(Project.id).label('count'),
                func.sum(Project.contract_amount).label('total_amount')
            )
            .group_by(
                extract('year', Project.created_at),
                extract('month', Project.created_at)
            )
            .order_by(
                extract('year', Project.created_at),
                extract('month', Project.created_at)
            )
            .all()
        )
    except:
        # 如果extract不支持，使用字符串格式化（SQLite）
        month_stats = (
            month_query.with_entities(
                func.strftime('%Y', Project.created_at).label('year'),
                func.strftime('%m', Project.created_at).label('month'),
                func.count(Project.id).label('count'),
                func.sum(Project.contract_amount).label('total_amount')
            )
            .group_by(
                func.strftime('%Y', Project.created_at),
                func.strftime('%m', Project.created_at)
            )
            .order_by(
                func.strftime('%Y', Project.created_at),
                func.strftime('%m', Project.created_at)
            )
            .all()
        )
    
    return [
        {
            "year": int(year),
            "month": int(month),
            "month_label": f"{int(year)}-{int(month):02d}",
            "count": count,
            "total_amount": float(total_amount or 0),
        }
        for year, month, count, total_amount in month_stats
    ]


def build_project_statistics(
    db: Session,
    query,
    group_by: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date]
) -> Dict[str, Any]:
    """
    构建项目统计数据
    
    Returns:
        Dict[str, Any]: 统计数据字典
    """
    # 总体统计
    total_projects = query.count()
    avg_progress = query.with_entities(func.avg(Project.progress_pct)).scalar() or 0
    
    stats_data = {
        "total": total_projects,
        "average_progress": float(avg_progress),
        "by_status": calculate_status_statistics(query),
        "by_stage": calculate_stage_statistics(query),
        "by_health": calculate_health_statistics(query),
        "by_pm": calculate_pm_statistics(query),
    }
    
    # 按客户统计
    if group_by == "customer":
        stats_data["by_customer"] = calculate_customer_statistics(query)
    
    # 按月份统计
    if group_by == "month":
        # 如果没有指定日期范围，默认统计最近12个月
        if not start_date or not end_date:
            today = date.today()
            end_date = today
            start_date = date(today.year - 1, today.month, 1)
        
        stats_data["by_month"] = calculate_monthly_statistics(query, start_date, end_date)
    
    return stats_data
