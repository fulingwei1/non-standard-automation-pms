# -*- coding: utf-8 -*-
"""
缺料统计 - 自动生成
从 shortage.py 拆分
"""

# -*- coding: utf-8 -*-
"""
缺料管理 API endpoints
包含：缺料上报、到货跟踪、物料替代、物料调拨、缺料统计
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import require_shortage_report_access
from app.models.machine import Machine
from app.models.material import Material
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.models.shortage import (
    ArrivalFollowUp,
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageDailyReport,
    ShortageReport,
)
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    ArrivalFollowUpResponse,
    MaterialArrivalCreate,
    MaterialArrivalResponse,
    MaterialSubstitutionCreate,
    MaterialSubstitutionResponse,
    MaterialTransferCreate,
    MaterialTransferResponse,
    ShortageReportCreate,
    ShortageReportResponse,
)

router = APIRouter()


def _build_shortage_daily_report(report: ShortageDailyReport) -> Dict[str, Any]:
    """序列化缺料日报"""
    return {
        "date": report.report_date.isoformat(),
        "alerts": {
            "new": report.new_alerts,
            "resolved": report.resolved_alerts,
            "pending": report.pending_alerts,
            "overdue": report.overdue_alerts,
            "levels": {
                "level1": report.level1_count,
                "level2": report.level2_count,
                "level3": report.level3_count,
                "level4": report.level4_count,
            }
        },
        "reports": {
            "new": report.new_reports,
            "resolved": report.resolved_reports,
        },
        "kit": {
            "total_work_orders": report.total_work_orders,
            "complete_count": report.kit_complete_count,
            "kit_rate": float(report.kit_rate) if report.kit_rate else 0.0,
        },
        "arrivals": {
            "expected": report.expected_arrivals,
            "actual": report.actual_arrivals,
            "delayed": report.delayed_arrivals,
            "on_time_rate": float(report.on_time_rate) if report.on_time_rate else 0.0,
        },
        "response": {
            "avg_response_minutes": report.avg_response_minutes,
            "avg_resolve_hours": float(report.avg_resolve_hours) if report.avg_resolve_hours else 0.0,
        },
        "stoppage": {
            "count": report.stoppage_count,
            "hours": float(report.stoppage_hours) if report.stoppage_hours else 0.0,
        },
    }


def generate_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
    from app.models.shortage import ShortageReport
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=ShortageReport,
        no_field='report_no',
        prefix='SR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：ARR-yymmdd-xxx"""
    from app.models.shortage import MaterialArrival
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialArrival,
        no_field='arrival_no',
        prefix='ARR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
    from app.models.shortage import MaterialSubstitution
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialSubstitution,
        no_field='substitution_no',
        prefix='SUB',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_transfer_no(db: Session) -> str:
    """生成调拨单号：TRF-yymmdd-xxx"""
    from app.models.shortage import MaterialTransfer
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialTransfer,
        no_field='transfer_no',
        prefix='TRF',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )




from fastapi import APIRouter

router = APIRouter(
    prefix="/shortage",
    tags=["statistics"]
)

# 共 7 个路由

# ==================== 缺料统计 ====================

@router.get("/shortage/dashboard", response_model=ResponseModel)
def get_shortage_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料看板
    """
    # 统计缺料上报
    total_reports = db.query(ShortageReport).count()
    reported = db.query(ShortageReport).filter(ShortageReport.status == 'REPORTED').count()
    confirmed = db.query(ShortageReport).filter(ShortageReport.status == 'CONFIRMED').count()
    handling = db.query(ShortageReport).filter(ShortageReport.status == 'HANDLING').count()
    resolved = db.query(ShortageReport).filter(ShortageReport.status == 'RESOLVED').count()

    # 统计紧急缺料
    urgent_reports = db.query(ShortageReport).filter(
        ShortageReport.urgent_level.in_(['URGENT', 'CRITICAL']),
        ShortageReport.status != 'RESOLVED'
    ).count()

    # 统计到货跟踪
    total_arrivals = db.query(MaterialArrival).count()
    pending_arrivals = db.query(MaterialArrival).filter(MaterialArrival.status == 'PENDING').count()
    delayed_arrivals = db.query(MaterialArrival).filter(MaterialArrival.is_delayed == True).count()

    # 统计物料替代
    total_substitutions = db.query(MaterialSubstitution).count()
    pending_substitutions = db.query(MaterialSubstitution).filter(
        MaterialSubstitution.status.in_(['DRAFT', 'TECH_PENDING', 'PROD_PENDING'])
    ).count()

    # 统计物料调拨
    total_transfers = db.query(MaterialTransfer).count()
    pending_transfers = db.query(MaterialTransfer).filter(
        MaterialTransfer.status.in_(['DRAFT', 'PENDING'])
    ).count()

    # 最近缺料上报
    recent_reports = db.query(ShortageReport).order_by(desc(ShortageReport.created_at)).limit(10).all()
    recent_reports_list = []
    for report in recent_reports:
        project = db.query(Project).filter(Project.id == report.project_id).first()
        recent_reports_list.append({
            'id': report.id,
            'report_no': report.report_no,
            'project_name': project.project_name if project else None,
            'material_name': report.material_name,
            'shortage_qty': float(report.shortage_qty),
            'urgent_level': report.urgent_level,
            'status': report.status,
            'report_time': report.report_time
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "reports": {
                "total": total_reports,
                "reported": reported,
                "confirmed": confirmed,
                "handling": handling,
                "resolved": resolved,
                "urgent": urgent_reports
            },
            "arrivals": {
                "total": total_arrivals,
                "pending": pending_arrivals,
                "delayed": delayed_arrivals
            },
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions
            },
            "transfers": {
                "total": total_transfers,
                "pending": pending_transfers
            },
            "recent_reports": recent_reports_list
        }
    )


@router.get("/shortage/supplier-delivery", response_model=ResponseModel)
def get_supplier_delivery_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    供应商交期分析
    """
    from datetime import timedelta

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    query = db.query(MaterialArrival).filter(
        MaterialArrival.expected_date >= start_date,
        MaterialArrival.expected_date <= end_date
    )

    if supplier_id:
        query = query.filter(MaterialArrival.supplier_id == supplier_id)

    arrivals = query.all()

    # 按供应商统计
    supplier_stats = {}
    for arrival in arrivals:
        if arrival.supplier_id:
            supplier_key = f"{arrival.supplier_id}_{arrival.supplier_name}"
            if supplier_key not in supplier_stats:
                supplier_stats[supplier_key] = {
                    "supplier_id": arrival.supplier_id,
                    "supplier_name": arrival.supplier_name,
                    "total_orders": 0,
                    "on_time": 0,
                    "delayed": 0,
                    "avg_delay_days": 0.0
                }

            supplier_stats[supplier_key]["total_orders"] += 1
            if arrival.is_delayed:
                supplier_stats[supplier_key]["delayed"] += 1
                supplier_stats[supplier_key]["avg_delay_days"] += arrival.delay_days or 0
            else:
                supplier_stats[supplier_key]["on_time"] += 1

    # 计算平均延迟天数
    for key, stats in supplier_stats.items():
        if stats["delayed"] > 0:
            stats["avg_delay_days"] = round(stats["avg_delay_days"] / stats["delayed"], 2)
        stats["on_time_rate"] = round(stats["on_time"] / stats["total_orders"] * 100, 2) if stats["total_orders"] > 0 else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "supplier_stats": list(supplier_stats.values())
        }
    )


@router.get("/shortage/daily-report", response_model=ResponseModel)
def get_daily_report(
    db: Session = Depends(deps.get_db),
    report_date: Optional[date] = Query(None, description="报表日期（默认：今天）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料日报
    """
    if not report_date:
        report_date = date.today()

    # 统计当日缺料上报
    daily_reports = db.query(ShortageReport).filter(
        func.date(ShortageReport.report_time) == report_date
    ).all()

    # 按紧急程度统计
    by_urgent = {}
    for report in daily_reports:
        level = report.urgent_level
        if level not in by_urgent:
            by_urgent[level] = 0
        by_urgent[level] += 1

    # 按状态统计
    by_status = {}
    for report in daily_reports:
        status = report.status
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1

    # 按物料统计
    by_material = {}
    for report in daily_reports:
        material_key = f"{report.material_id}_{report.material_name}"
        if material_key not in by_material:
            by_material[material_key] = {
                "material_id": report.material_id,
                "material_name": report.material_name,
                "count": 0,
                "total_shortage_qty": 0.0
            }
        by_material[material_key]["count"] += 1
        by_material[material_key]["total_shortage_qty"] += float(report.shortage_qty)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_date": str(report_date),
            "total_reports": len(daily_reports),
            "by_urgent": by_urgent,
            "by_status": by_status,
            "by_material": list(by_material.values())
        }
    )


@router.get("/shortage/daily-report/latest", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_latest_shortage_daily_report(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最新缺料日报（定时生成）
    """
    latest_date = db.query(func.max(ShortageDailyReport.report_date)).scalar()
    if not latest_date:
        return ResponseModel(data=None)

    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == latest_date
    ).first()

    if not report:
        return ResponseModel(data=None)

    return ResponseModel(data=_build_shortage_daily_report(report))


@router.get("/shortage/daily-report/by-date", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_shortage_daily_report_by_date(
    *,
    db: Session = Depends(deps.get_db),
    report_date: date = Query(..., description="报表日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按日期获取缺料日报（定时生成的数据）
    """
    report = db.query(ShortageDailyReport).filter(
        ShortageDailyReport.report_date == report_date
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="指定日期不存在缺料日报")

    return ResponseModel(data=_build_shortage_daily_report(report))


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
    from datetime import timedelta

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

