# -*- coding: utf-8 -*-
"""
预警统计 - 概览统计
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.alert import AlertRecord
from app.models.project import Project
from app.models.user import User

router = APIRouter()


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
    query = db.query(AlertRecord).options(joinedload(AlertRecord.rule))

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

    # 按类型统计（rule_type 在 AlertRule 模型上，需要通过关系访问）
    by_type = {}
    for alert in alerts:
        rule_type = alert.rule.rule_type if alert.rule else "UNKNOWN"
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
