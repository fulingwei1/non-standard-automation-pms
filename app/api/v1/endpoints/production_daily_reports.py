# -*- coding: utf-8 -*-
"""生产日报兼容端点。"""
from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.production import ProductionDailyReport, WorkReport, WorkOrder, Worker, Workshop
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import ProductionDailyReportResponse

router = APIRouter()


def _safe_rate(numerator: float, denominator: float) -> float:
    return round((numerator / denominator * 100) if denominator else 0.0, 2)


def _to_response(
    report_date: date,
    workshop_id: Optional[int],
    workshop_name: Optional[str],
    plan_qty: int,
    completed_qty: int,
    plan_hours: float,
    actual_hours: float,
    overtime_hours: float,
    should_attend: int,
    actual_attend: int,
    leave_count: int,
    total_qty: int,
    qualified_qty: int,
    new_exception_count: int,
    resolved_exception_count: int,
    summary: Optional[str],
    *,
    report_id: int = 0,
    completion_rate: Optional[float] = None,
    efficiency: Optional[float] = None,
    pass_rate: Optional[float] = None,
    created_by: Optional[int] = None,
    created_at=None,
    updated_at=None,
) -> ProductionDailyReportResponse:
    return ProductionDailyReportResponse(
        id=report_id,
        report_date=report_date,
        workshop_id=workshop_id,
        workshop_name=workshop_name,
        plan_qty=plan_qty,
        completed_qty=completed_qty,
        completion_rate=completion_rate if completion_rate is not None else _safe_rate(completed_qty, plan_qty),
        plan_hours=round(plan_hours, 2),
        actual_hours=round(actual_hours, 2),
        overtime_hours=round(overtime_hours, 2),
        efficiency=efficiency if efficiency is not None else _safe_rate(actual_hours, plan_hours),
        should_attend=should_attend,
        actual_attend=actual_attend,
        leave_count=max(leave_count, 0),
        total_qty=total_qty,
        qualified_qty=qualified_qty,
        pass_rate=pass_rate if pass_rate is not None else _safe_rate(qualified_qty, total_qty),
        new_exception_count=new_exception_count,
        resolved_exception_count=resolved_exception_count,
        summary=summary,
        created_by=created_by,
        created_at=created_at,
        updated_at=updated_at,
    )


def _from_model(db: Session, report: ProductionDailyReport) -> ProductionDailyReportResponse:
    workshop_name = None
    if report.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == report.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    plan_qty = int(report.plan_qty or 0)
    completed_qty = int(report.completed_qty or 0)
    plan_hours = float(report.plan_hours or 0)
    actual_hours = float(report.actual_hours or 0)
    total_qty = int(report.total_qty or 0)
    qualified_qty = int(report.qualified_qty or 0)

    completion_rate = float(report.completion_rate) if report.completion_rate is not None else None
    if completion_rate in (None, 0.0) and plan_qty > 0 and completed_qty > 0:
        completion_rate = _safe_rate(completed_qty, plan_qty)

    efficiency = float(report.efficiency) if report.efficiency is not None else None
    if efficiency in (None, 0.0) and plan_hours > 0 and actual_hours > 0:
        efficiency = _safe_rate(actual_hours, plan_hours)

    pass_rate = float(report.pass_rate) if report.pass_rate is not None else None
    if pass_rate in (None, 0.0) and total_qty > 0 and qualified_qty > 0:
        pass_rate = _safe_rate(qualified_qty, total_qty)

    return _to_response(
        report_date=report.report_date,
        workshop_id=report.workshop_id,
        workshop_name=workshop_name,
        plan_qty=plan_qty,
        completed_qty=completed_qty,
        plan_hours=plan_hours,
        actual_hours=actual_hours,
        overtime_hours=float(report.overtime_hours or 0),
        should_attend=int(report.should_attend or 0),
        actual_attend=int(report.actual_attend or 0),
        leave_count=int(report.leave_count or 0),
        total_qty=total_qty,
        qualified_qty=qualified_qty,
        new_exception_count=int(report.new_exception_count or 0),
        resolved_exception_count=int(report.resolved_exception_count or 0),
        summary=report.summary,
        report_id=report.id,
        completion_rate=completion_rate,
        efficiency=efficiency,
        pass_rate=pass_rate,
        created_by=report.created_by,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _build_computed_report(
    db: Session,
    *,
    target_date: date,
    workshop_id: Optional[int] = None,
) -> ProductionDailyReportResponse:
    start_dt = datetime.combine(target_date, time.min)
    end_dt = datetime.combine(target_date + timedelta(days=1), time.min)

    work_order_query = db.query(WorkOrder).filter(WorkOrder.created_at >= start_dt, WorkOrder.created_at < end_dt)
    work_report_query = db.query(WorkReport).filter(WorkReport.report_time >= start_dt, WorkReport.report_time < end_dt)
    worker_query = db.query(Worker)

    workshop_name = None
    if workshop_id is not None:
        work_order_query = work_order_query.filter(WorkOrder.workshop_id == workshop_id)
        worker_query = worker_query.filter(Worker.workshop_id == workshop_id)
        worker_ids = [row.id for row in worker_query.all()]
        if worker_ids:
            work_report_query = work_report_query.filter(WorkReport.worker_id.in_(worker_ids))
        else:
            work_report_query = work_report_query.filter(WorkReport.worker_id == -1)

        workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    work_orders = work_order_query.all()
    work_reports = work_report_query.all()
    workers = worker_query.all()

    plan_qty = sum(int(order.plan_qty or 0) for order in work_orders)
    completed_qty = sum(int(report.completed_qty or 0) for report in work_reports)
    qualified_qty = sum(int(report.qualified_qty or 0) for report in work_reports)
    total_qty = completed_qty
    plan_hours = sum(float(order.standard_hours or 0) for order in work_orders)
    actual_hours = sum(float(report.work_hours or 0) for report in work_reports)
    should_attend = len([worker for worker in workers if worker.is_active])
    actual_attend = len({report.worker_id for report in work_reports if report.worker_id is not None})

    return _to_response(
        report_date=target_date,
        workshop_id=workshop_id,
        workshop_name=workshop_name,
        plan_qty=plan_qty,
        completed_qty=completed_qty,
        plan_hours=plan_hours,
        actual_hours=actual_hours,
        overtime_hours=0.0,
        should_attend=should_attend,
        actual_attend=actual_attend,
        leave_count=max(should_attend - actual_attend, 0),
        total_qty=total_qty,
        qualified_qty=qualified_qty,
        new_exception_count=0,
        resolved_exception_count=0,
        summary="系统根据当日报工自动汇总",
    )


@router.get("", response_model=PaginatedResponse)
def read_production_daily_reports(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    report_date: Optional[date] = Query(None, description="指定日报日期"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """生产日报列表（兼容前端 /production-daily-reports）。"""
    query = db.query(ProductionDailyReport)

    if report_date is not None:
        query = query.filter(ProductionDailyReport.report_date == report_date)
    if start_date is not None:
        query = query.filter(ProductionDailyReport.report_date >= start_date)
    if end_date is not None:
        query = query.filter(ProductionDailyReport.report_date <= end_date)
    if workshop_id is not None:
        query = query.filter(ProductionDailyReport.workshop_id == workshop_id)

    total = query.count()
    reports = (
        query.order_by(ProductionDailyReport.report_date.desc(), ProductionDailyReport.id.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    items = [_from_model(db, report) for report in reports]

    if total == 0 and report_date is not None:
        items = [_build_computed_report(db, target_date=report_date, workshop_id=workshop_id)]
        total = 1

    return pagination.to_response(items, total)


@router.get("/latest", response_model=ProductionDailyReportResponse)
def read_latest_production_daily_report(
    db: Session = Depends(deps.get_db),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取最新生产日报（兼容前端 /production-daily-reports/latest）。"""
    query = db.query(ProductionDailyReport)
    if workshop_id is not None:
        query = query.filter(ProductionDailyReport.workshop_id == workshop_id)

    latest = query.order_by(ProductionDailyReport.report_date.desc(), ProductionDailyReport.id.desc()).first()
    if latest:
        return _from_model(db, latest)

    return _build_computed_report(db, target_date=date.today(), workshop_id=workshop_id)
