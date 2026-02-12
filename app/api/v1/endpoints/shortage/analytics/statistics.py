# -*- coding: utf-8 -*-
"""
统计分析 - statistics.py

合并来源:
- app/api/v1/endpoints/shortage/statistics.py (聚合器)
- app/api/v1/endpoints/shortage/statistics_analysis.py
- app/api/v1/endpoints/shortage/statistics_supplier.py
- app/api/v1/endpoints/shortage/statistics_helpers.py (辅助函数)
- app/api/v1/endpoints/shortage_alerts/statistics.py (部分)

路由:
- GET    /overview              统计概览（按状态/级别）
- GET    /cause-analysis        缺料原因分析
- GET    /kit-rate              齐套率统计
- GET    /supplier-delivery     供应商交期分析
"""
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.core import security
from app.models.material import MaterialShortage
from app.models.project import Project
from app.models.shortage import MaterialArrival, ShortageReport
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


# ============================================================
# 辅助函数
# ============================================================

def _calculate_default_date_range(today: date) -> tuple[date, date]:
    """计算默认日期范围（当前月）"""
    start_date, end_date = get_month_range(today)
    return start_date, end_date


# ============================================================
# 统计概览
# ============================================================

@router.get("/overview", response_model=ResponseModel)
def get_statistics_overview(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料统计概览
    同时统计系统检测的缺料预警和人工上报的缺料
    """
    result = {
        "alerts": {},  # 系统检测的缺料预警 (MaterialShortage)
        "reports": {}  # 人工上报的缺料 (ShortageReport)
    }

    # === 系统检测的缺料预警 (MaterialShortage) ===
    alert_query = db.query(MaterialShortage)
    if project_id:
        alert_query = alert_query.filter(MaterialShortage.project_id == project_id)

    # 按状态统计
    alert_status_stats = {}
    status_counts = (
        db.query(MaterialShortage.status, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.status)
        .all()
    )
    for status, count in status_counts:
        alert_status_stats[status] = count

    # 按预警级别统计
    alert_level_stats = {}
    level_counts = (
        db.query(MaterialShortage.alert_level, func.count(MaterialShortage.id))
        .filter(MaterialShortage.project_id == project_id if project_id else True)
        .group_by(MaterialShortage.alert_level)
        .all()
    )
    for level, count in level_counts:
        alert_level_stats[level] = count

    alert_total = alert_query.count()
    alert_unresolved = alert_query.filter(MaterialShortage.status != "RESOLVED").count()

    result["alerts"] = {
        "total": alert_total,
        "unresolved": alert_unresolved,
        "resolved": alert_total - alert_unresolved,
        "by_status": alert_status_stats,
        "by_level": alert_level_stats,
    }

    # === 人工上报的缺料 (ShortageReport) ===
    report_query = db.query(ShortageReport)
    if project_id:
        report_query = report_query.filter(ShortageReport.project_id == project_id)

    report_total = report_query.count()
    report_status_stats = {}
    report_status_counts = (
        db.query(ShortageReport.status, func.count(ShortageReport.id))
        .filter(ShortageReport.project_id == project_id if project_id else True)
        .group_by(ShortageReport.status)
        .all()
    )
    for status, count in report_status_counts:
        report_status_stats[status] = count

    # 按紧急程度统计
    report_urgent_stats = {}
    urgent_counts = (
        db.query(ShortageReport.urgent_level, func.count(ShortageReport.id))
        .filter(ShortageReport.project_id == project_id if project_id else True)
        .group_by(ShortageReport.urgent_level)
        .all()
    )
    for level, count in urgent_counts:
        report_urgent_stats[level] = count

    result["reports"] = {
        "total": report_total,
        "by_status": report_status_stats,
        "by_urgent": report_urgent_stats,
    }

    return ResponseModel(code=200, message="success", data=result)


# ============================================================
# 缺料原因分析
# ============================================================

@router.get("/cause-analysis", response_model=ResponseModel)
def get_cause_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料原因分析
    分析缺料的解决方案类型分布、紧急程度分布、项目分布
    """
    today = date.today()
    if not start_date or not end_date:
        default_start, default_end = _calculate_default_date_range(today)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 查询人工上报的缺料
    query = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) >= start_date,
        func.date(ShortageReport.report_time) <= end_date
    )

    if project_id:
        query = query.filter(ShortageReport.project_id == project_id)

    reports = query.all()

    # 按解决方案类型统计
    by_solution: Dict[str, Dict[str, Any]] = {}
    for report in reports:
        solution = report.solution_type or 'UNKNOWN'
        if solution not in by_solution:
            by_solution[solution] = {
                "solution_type": solution,
                "count": 0,
                "total_shortage_qty": 0.0,
                "avg_resolve_time_hours": 0.0,
                "_total_resolve_time": 0.0
            }
        by_solution[solution]["count"] += 1
        by_solution[solution]["total_shortage_qty"] += float(report.shortage_qty)

        # 计算解决时间
        if report.resolved_at and report.report_time:
            resolve_hours = (report.resolved_at - report.report_time).total_seconds() / 3600
            by_solution[solution]["_total_resolve_time"] += resolve_hours

    # 计算平均解决时间
    for stats in by_solution.values():
        if stats["count"] > 0:
            stats["avg_resolve_time_hours"] = round(stats["_total_resolve_time"] / stats["count"], 2)
        del stats["_total_resolve_time"]

    # 按紧急程度统计
    by_urgent: Dict[str, Dict[str, Any]] = {}
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
    by_project: Dict[str, Dict[str, Any]] = {}
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


# ============================================================
# 齐套率统计
# ============================================================

@router.get("/kit-rate", response_model=ResponseModel)
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
    try:
        from app.services.kit_rate_statistics_service import (
            calculate_daily_kit_statistics,
            calculate_date_range,
            calculate_project_kit_statistics,
            calculate_summary_statistics,
            calculate_workshop_kit_statistics,
        )
    except ImportError:
        return ResponseModel(
            code=501,
            message="齐套率统计服务未实现",
            data=None
        )

    today = date.today()
    if not start_date or not end_date:
        default_start, default_end = calculate_date_range(today)
        start_date = start_date or default_start
        end_date = end_date or default_end

    # 获取项目列表
    query = db.query(Project).filter(Project.is_active)
    if project_id:
        query = query.filter(Project.id == project_id)
    projects = query.all()

    statistics = []

    if group_by == "project":
        for project in projects:
            stat = calculate_project_kit_statistics(db, project)
            if stat:
                statistics.append(stat)

    elif group_by == "workshop":
        statistics = calculate_workshop_kit_statistics(db, workshop_id, projects)

    elif group_by == "day":
        statistics = calculate_daily_kit_statistics(db, start_date, end_date, projects)

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


# ============================================================
# 供应商交期分析
# ============================================================

@router.get("/supplier-delivery", response_model=ResponseModel)
def get_supplier_delivery_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    供应商交期分析
    基于到货跟踪记录分析各供应商的交期表现
    """
    today = date.today()
    if not start_date or not end_date:
        default_start, default_end = _calculate_default_date_range(today)
        start_date = start_date or default_start
        end_date = end_date or default_end

    query = db.query(MaterialArrival).filter(
        MaterialArrival.expected_date >= start_date,
        MaterialArrival.expected_date <= end_date
    )

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    arrivals = query.all()

    # 按供应商统计
    supplier_stats: Dict[str, Dict[str, Any]] = {}
    for arrival in arrivals:
        if arrival.supplier_id:
            supplier_key = str(arrival.supplier_id)
            if supplier_key not in supplier_stats:
                supplier_stats[supplier_key] = {
                    "supplier_id": arrival.supplier_id,
                    "supplier_name": arrival.supplier_name,
                    "total_orders": 0,
                    "on_time": 0,
                    "delayed": 0,
                    "avg_delay_days": 0.0,
                    "_total_delay_days": 0
                }

            supplier_stats[supplier_key]["total_orders"] += 1
            if arrival.is_delayed:
                supplier_stats[supplier_key]["delayed"] += 1
                supplier_stats[supplier_key]["_total_delay_days"] += arrival.delay_days or 0
            else:
                supplier_stats[supplier_key]["on_time"] += 1

    # 计算平均延迟天数和准时率
    for stats in supplier_stats.values():
        if stats["delayed"] > 0:
            stats["avg_delay_days"] = round(stats["_total_delay_days"] / stats["delayed"], 2)
        if stats["total_orders"] > 0:
            stats["on_time_rate"] = round(stats["on_time"] / stats["total_orders"] * 100, 2)
        else:
            stats["on_time_rate"] = 0.0
        del stats["_total_delay_days"]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_suppliers": len(supplier_stats),
            "supplier_stats": list(supplier_stats.values())
        }
    )
