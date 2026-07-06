# -*- coding: utf-8 -*-
"""人工成本明细分析 API"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.production.worker import Worker
from app.models.production.work_order import WorkOrder
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService

router = APIRouter()


@router.get("/summary", summary="按项目汇总人工成本")
def labor_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    sql = text(
        """
        SELECT
            p.id AS project_id,
            p.project_name,
            p.project_code,
            COUNT(pc.id) AS record_count,
            COALESCE(SUM(pc.amount), 0) AS total_labor_cost,
            MIN(pc.cost_date) AS first_cost_date,
            MAX(pc.cost_date) AS last_cost_date
        FROM project_costs pc
        JOIN projects p ON pc.project_id = p.id
        WHERE LOWER(pc.cost_type) = 'labor'
        GROUP BY p.id, p.project_name, p.project_code
        ORDER BY total_labor_cost DESC, p.id ASC
        """
    )
    rows = db.execute(sql).fetchall()

    projects = []
    total_labor_cost = 0.0
    total_records = 0

    for row in rows:
        labor_cost = float(row.total_labor_cost or 0)
        record_count = int(row.record_count or 0)
        total_labor_cost += labor_cost
        total_records += record_count
        projects.append(
            {
                "project_id": row.project_id,
                "project_name": row.project_name,
                "project_code": row.project_code,
                "record_count": record_count,
                "labor_cost": round(labor_cost, 2),
                "first_cost_date": row.first_cost_date,
                "last_cost_date": row.last_cost_date,
            }
        )

    for project in projects:
        project["labor_cost_pct"] = (
            round(project["labor_cost"] / total_labor_cost * 100, 2) if total_labor_cost > 0 else 0
        )

    return {
        "summary": {
            "total_projects": len(projects),
            "total_records": total_records,
            "total_labor_cost": round(total_labor_cost, 2),
            "avg_labor_cost_per_project": (
                round(total_labor_cost / len(projects), 2) if projects else 0
            ),
        },
        "projects": projects,
    }


@router.get("/by-engineer", summary="按工程师汇总人工成本")
def labor_cost_by_engineer(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    rows = (
        db.query(WorkOrder, Worker, User)
        .join(Worker, WorkOrder.assigned_to == Worker.id)
        .outerjoin(User, Worker.user_id == User.id)
        .filter(WorkOrder.project_id.isnot(None))
        .all()
    )

    grouped: dict[int, dict[str, Any]] = {}
    total_work_orders = 0
    total_hours = Decimal("0")
    total_cost = Decimal("0")

    for work_order, worker, linked_user in rows:
        engineer_id = linked_user.id if linked_user else worker.id
        engineer_name = (
            linked_user.display_name
            if linked_user
            else worker.worker_name or f"工程师#{worker.id}"
        )
        stats = grouped.setdefault(
            engineer_id,
            {
                "engineer_id": engineer_id,
                "engineer_name": engineer_name,
                "work_order_count": 0,
                "project_ids": set(),
                "total_hours": Decimal("0"),
                "estimated_labor_cost": Decimal("0"),
                "completed_orders": 0,
                "in_progress_orders": 0,
            },
        )

        hours = _work_order_hours(work_order)
        hourly_rate = _resolve_work_order_hourly_rate(db, work_order, worker)
        cost = hours * hourly_rate

        stats["work_order_count"] += 1
        stats["project_ids"].add(work_order.project_id)
        stats["total_hours"] += hours
        stats["estimated_labor_cost"] += cost
        if work_order.status == "COMPLETED":
            stats["completed_orders"] += 1
        if work_order.status == "IN_PROGRESS":
            stats["in_progress_orders"] += 1

        total_work_orders += 1
        total_hours += hours
        total_cost += cost

    engineers = []
    for stats in grouped.values():
        work_order_count = stats["work_order_count"]
        engineers.append(
            {
                "engineer_id": stats["engineer_id"],
                "engineer_name": stats["engineer_name"],
                "work_order_count": work_order_count,
                "project_count": len(stats["project_ids"]),
                "total_hours": round(float(stats["total_hours"]), 2),
                "estimated_labor_cost": round(float(stats["estimated_labor_cost"]), 2),
                "completed_orders": stats["completed_orders"],
                "in_progress_orders": stats["in_progress_orders"],
                "completion_rate": (
                    round(stats["completed_orders"] / work_order_count * 100, 2)
                    if work_order_count > 0
                    else 0
                ),
            }
        )
    engineers.sort(
        key=lambda item: (item["estimated_labor_cost"], item["total_hours"]), reverse=True
    )

    return {
        "summary": {
            "total_engineers": len(engineers),
            "total_work_orders": total_work_orders,
            "total_hours": round(float(total_hours), 2),
            "total_estimated_labor_cost": round(float(total_cost), 2),
            "hourly_rate_used": (
                round(float(total_cost / total_hours), 2) if total_hours > 0 else 0
            ),
            "rate_source": "hourly_rate_service",
            "avg_cost_per_hour": (
                round(float(total_cost / total_hours), 2) if total_hours > 0 else 0
            ),
        },
        "engineers": engineers,
    }


def _work_order_hours(work_order: WorkOrder) -> Decimal:
    hours = work_order.actual_hours
    if hours is None:
        hours = work_order.standard_hours
    return Decimal(str(hours or 0))


def _work_order_rate_date(work_order: WorkOrder) -> date | None:
    for value in (
        work_order.actual_end_time,
        work_order.actual_start_time,
        work_order.plan_end_date,
        work_order.plan_start_date,
    ):
        if value is None:
            continue
        if hasattr(value, "date"):
            return value.date()
        if isinstance(value, date):
            return value
    return None


def _resolve_work_order_hourly_rate(
    db: Session, work_order: WorkOrder, worker: Worker
) -> Decimal:
    rate_date = _work_order_rate_date(work_order)
    if worker.user_id:
        return HourlyRateService.get_user_hourly_rate(db, worker.user_id, rate_date)
    if worker.hourly_rate is not None:
        return Decimal(str(worker.hourly_rate))
    return HourlyRateService.DEFAULT_HOURLY_RATE


@router.get("/{project_id}", summary="单项目人工成本明细")
def labor_cost_project_detail(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
) -> Any:
    project_sql = text(
        """
        SELECT id, project_name, project_code
        FROM projects
        WHERE id = :project_id
        """
    )
    project_row = db.execute(project_sql, {"project_id": project_id}).fetchone()
    if not project_row:
        return {"error": "项目不存在"}

    detail_sql = text(
        """
        SELECT
            pc.id,
            pc.cost_date,
            pc.amount,
            pc.cost_category,
            pc.source_type,
            pc.source_no,
            pc.description
        FROM project_costs pc
        WHERE pc.project_id = :project_id
          AND LOWER(pc.cost_type) = 'labor'
        ORDER BY pc.cost_date DESC, pc.id DESC
        """
    )
    detail_rows = db.execute(detail_sql, {"project_id": project_id}).fetchall()

    details = []
    total_labor_cost = 0.0
    for row in detail_rows:
        amount = float(row.amount or 0)
        total_labor_cost += amount
        details.append(
            {
                "id": row.id,
                "cost_date": row.cost_date,
                "amount": round(amount, 2),
                "cost_category": row.cost_category,
                "source_type": row.source_type,
                "source_no": row.source_no,
                "description": row.description,
            }
        )

    source_sql = text(
        """
        SELECT
            COALESCE(pc.source_type, 'manual') AS source_type,
            COUNT(pc.id) AS record_count,
            COALESCE(SUM(pc.amount), 0) AS amount
        FROM project_costs pc
        WHERE pc.project_id = :project_id
          AND LOWER(pc.cost_type) = 'labor'
        GROUP BY COALESCE(pc.source_type, 'manual')
        ORDER BY amount DESC
        """
    )
    source_rows = db.execute(source_sql, {"project_id": project_id}).fetchall()
    by_source = [
        {
            "source_type": row.source_type,
            "record_count": int(row.record_count or 0),
            "amount": round(float(row.amount or 0), 2),
        }
        for row in source_rows
    ]

    latest_date = details[0]["cost_date"] if details else None
    return {
        "project": {
            "project_id": project_row.id,
            "project_name": project_row.project_name,
            "project_code": project_row.project_code,
        },
        "summary": {
            "record_count": len(details),
            "total_labor_cost": round(total_labor_cost, 2),
            "avg_cost_per_record": round(total_labor_cost / len(details), 2) if details else 0,
            "latest_cost_date": latest_date,
        },
        "by_source": by_source,
        "details": details,
    }
