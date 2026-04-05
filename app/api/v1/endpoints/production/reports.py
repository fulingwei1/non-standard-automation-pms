# -*- coding: utf-8 -*-
"""生产报表兼容端点。"""
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.core import security
from app.models.production import WorkReport, Worker, Workshop
from app.models.user import User
from app.schemas.production import WorkerPerformanceReportResponse, WorkerRankingResponse

router = APIRouter()


def _resolve_period(
    start_date: Optional[date],
    end_date: Optional[date],
    period_start: Optional[date],
    period_end: Optional[date],
) -> tuple[date, date]:
    resolved_start = period_start or start_date
    resolved_end = period_end or end_date

    if not resolved_start or not resolved_end:
        default_start, default_end = get_month_range(date.today())
        resolved_start = resolved_start or default_start
        resolved_end = resolved_end or default_end

    if resolved_start > resolved_end:
        resolved_start, resolved_end = resolved_end, resolved_start

    return resolved_start, resolved_end


def _load_workers(
    db: Session,
    *,
    worker_id: Optional[int] = None,
    workshop_id: Optional[int] = None,
) -> List[Worker]:
    query = db.query(Worker)

    if worker_id is not None:
        query = query.filter(Worker.id == worker_id)
    if workshop_id is not None:
        query = query.filter(Worker.workshop_id == workshop_id)

    return query.order_by(Worker.id.asc()).all()


def _build_worker_performance_rows(
    db: Session,
    *,
    worker_id: Optional[int] = None,
    workshop_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    include_zero_rows: bool = False,
) -> List[WorkerPerformanceReportResponse]:
    resolved_start, resolved_end = _resolve_period(start_date, end_date, period_start, period_end)
    start_dt = datetime.combine(resolved_start, time.min)
    end_dt = datetime.combine(resolved_end + timedelta(days=1), time.min)

    workers = _load_workers(db, worker_id=worker_id, workshop_id=workshop_id)
    workshop_map = {
        workshop.id: workshop.workshop_name
        for workshop in db.query(Workshop).filter(Workshop.id.in_([w.workshop_id for w in workers if w.workshop_id])).all()
    }

    rows: List[WorkerPerformanceReportResponse] = []
    for worker in workers:
        reports = (
            db.query(WorkReport)
            .filter(WorkReport.worker_id == worker.id)
            .filter(WorkReport.report_time >= start_dt)
            .filter(WorkReport.report_time < end_dt)
            .all()
        )

        total_hours = round(sum(float(report.work_hours or 0) for report in reports), 2)
        total_reports = len(reports)
        completed_orders = len(
            {
                report.work_order_id
                for report in reports
                if report.report_type == "COMPLETE" or int(report.completed_qty or 0) > 0
            }
        )
        total_completed_qty = sum(int(report.completed_qty or 0) for report in reports)
        total_qualified_qty = sum(int(report.qualified_qty or 0) for report in reports)
        average_efficiency = round(total_qualified_qty / total_hours, 2) if total_hours > 0 else 0.0

        if not include_zero_rows and total_reports == 0:
            continue

        rows.append(
            WorkerPerformanceReportResponse(
                worker_id=worker.id,
                worker_code=worker.worker_no,
                worker_name=worker.worker_name,
                workshop_id=worker.workshop_id,
                workshop_name=workshop_map.get(worker.workshop_id),
                period_start=resolved_start,
                period_end=resolved_end,
                total_hours=total_hours,
                total_reports=total_reports,
                completed_orders=completed_orders,
                total_completed_qty=total_completed_qty,
                total_qualified_qty=total_qualified_qty,
                average_efficiency=average_efficiency,
            )
        )

    return rows


@router.get("/reports/worker-performance", response_model=List[WorkerPerformanceReportResponse])
def get_worker_performance_report(
    db: Session = Depends(deps.get_db),
    worker_id: Optional[int] = Query(None, description="工人ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    period_start: Optional[date] = Query(None, description="统计开始日期"),
    period_end: Optional[date] = Query(None, description="统计结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """人员绩效报表（兼容前端 /production/reports/worker-performance）。"""
    return _build_worker_performance_rows(
        db,
        worker_id=worker_id,
        workshop_id=workshop_id,
        start_date=start_date,
        end_date=end_date,
        period_start=period_start,
        period_end=period_end,
        include_zero_rows=worker_id is not None,
    )


@router.get("/reports/worker-ranking", response_model=List[WorkerRankingResponse])
def get_worker_ranking(
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("efficiency", description="排名类型：efficiency/output/quality"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    period_start: Optional[date] = Query(None, description="统计开始日期"),
    period_end: Optional[date] = Query(None, description="统计结束日期"),
    limit: int = Query(10, ge=1, le=100, description="返回前N名"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """人员绩效排名（兼容前端 /production/reports/worker-ranking）。"""
    rows = _build_worker_performance_rows(
        db,
        workshop_id=workshop_id,
        start_date=start_date,
        end_date=end_date,
        period_start=period_start,
        period_end=period_end,
        include_zero_rows=False,
    )

    ranking_type = (ranking_type or "efficiency").lower()
    rankings: list[WorkerRankingResponse] = []
    for row in rows:
        quality_rate = round(
            (row.total_qualified_qty / row.total_completed_qty * 100)
            if row.total_completed_qty > 0
            else 0.0,
            2,
        )

        if ranking_type == "output":
            score = float(row.total_completed_qty)
        elif ranking_type in {"quality", "quality_rate"}:
            score = quality_rate
        else:
            score = row.average_efficiency

        rankings.append(
            WorkerRankingResponse(
                rank=0,
                worker_id=row.worker_id,
                worker_name=row.worker_name,
                workshop_name=row.workshop_name,
                efficiency=row.average_efficiency,
                output=row.total_completed_qty,
                quality_rate=quality_rate,
                total_hours=row.total_hours,
                score=round(score, 2),
            )
        )

    rankings.sort(
        key=lambda item: (item.score, item.output, item.quality_rate, -item.worker_id),
        reverse=True,
    )

    for index, item in enumerate(rankings[:limit], start=1):
        item.rank = index

    return rankings[:limit]
