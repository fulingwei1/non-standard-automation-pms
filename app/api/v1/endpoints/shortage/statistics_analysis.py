# -*- coding: utf-8 -*-
"""
缺料统计 - 缺料原因分析和齐套率统计
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.shortage import ShortageReport
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/shortage/cause-analysis", response_model=ResponseModel)
def get_cause_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料原因分析
    """
    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    query = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) >= start_date,
        func.date(ShortageReport.report_time) <= end_date
    )

    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)

    reports = query.all()

    # 按解决方案类型统计
    by_solution = {}
    for report in reports:
        solution = report.solution_type or 'UNKNOWN'
        if solution not in by_solution:
            by_solution[solution] = {
                "solution_type": solution,
                "count": 0,
                "total_shortage_qty": 0.0,
                "avg_resolve_time": 0.0
            }
        by_solution[solution]["count"] += 1
        by_solution[solution]["total_shortage_qty"] += float(report.shortage_qty)

        # 计算平均解决时间
        if report.resolved_at and report.report_time:
            resolve_time = (report.resolved_at - report.report_time).total_seconds() / 3600  # 小时
            by_solution[solution]["avg_resolve_time"] += resolve_time

    # 计算平均解决时间
    for key, stats in by_solution.items():
        if stats["count"] > 0:
            stats["avg_resolve_time"] = round(stats["avg_resolve_time"] / stats["count"], 2)

    # 按紧急程度统计
    by_urgent = {}
    for report in reports:
        level = report.urgent_level
        if level not in by_urgent:
            by_urgent[level] = {
                "urgent_level": level,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_urgent[level]["count"] += 1
        by_urgent[level]["total_shortage_qty"] += float(report.shortage_qty)

    # 按项目统计
    by_project = {}
    for report in reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        project_name = project.project_name if project else f"项目{report.project_id}"
        if project_name not in by_project:
            by_project[project_name] = {
                "project_id": report.project_id,
                "project_name": project_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_project[project_name]["count"] += 1
        by_project[project_name]["total_shortage_qty"] += float(report.shortage_qty)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_reports": len(reports),
            "by_solution": list(by_solution.values()),
            "by_urgent": list(by_urgent.values()),
            "by_project": list(by_project.values())
        }
    )


@router.get("/shortage/statistics/kit-rate", response_model=ResponseModel)
def get_kit_rate_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: Optional[str] = Query("project", description="分组方式: project/workshop/day"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    齐套率统计
    按项目/车间/时间维度统计齐套率
    """
    from app.services.kit_rate_statistics_service import (
        calculate_daily_kit_statistics,
        calculate_date_range,
        calculate_project_kit_statistics,
        calculate_summary_statistics,
        calculate_workshop_kit_statistics,
    )

    # 默认使用当前月
    today = date.today()
    if not start_date or not end_date:
        default_start, default_end = calculate_date_range(today)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 获取项目列表
    query = db.query(Project).filter(Project.is_active == True)
    if project_id:
        query = query.filter(Project.id == project_id)
    projects = query.all()

    statistics = []

    if group_by == "project":
        # 按项目统计
        for project in projects:
            stat = calculate_project_kit_statistics(db, project)
            if stat:
                statistics.append(stat)

    elif group_by == "workshop":
        # 按车间统计
        statistics = calculate_workshop_kit_statistics(db, workshop_id, projects)

    elif group_by == "day":
        # 按日期统计
        statistics = calculate_daily_kit_statistics(db, start_date, end_date, projects)

    # 计算汇总
    summary = calculate_summary_statistics(statistics, group_by)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "group_by": group_by,
            "statistics": statistics,
            "summary": summary
        }
    )
