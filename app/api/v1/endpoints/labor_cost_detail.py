# -*- coding: utf-8 -*-
"""人工成本明细分析 API"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()

DEFAULT_HOURLY_RATE = 200


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
            round(project["labor_cost"] / total_labor_cost * 100, 2)
            if total_labor_cost > 0
            else 0
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
    sql = text(
        """
        SELECT
            u.id AS engineer_id,
            COALESCE(u.real_name, u.username) AS engineer_name,
            COUNT(wo.id) AS work_order_count,
            COUNT(DISTINCT wo.project_id) AS project_count,
            SUM(COALESCE(wo.actual_hours, wo.standard_hours, 0)) AS total_hours,
            SUM(COALESCE(wo.actual_hours, wo.standard_hours, 0) * :hourly_rate) AS estimated_labor_cost,
            SUM(CASE WHEN wo.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_orders,
            SUM(CASE WHEN wo.status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress_orders
        FROM work_order wo
        JOIN users u ON wo.assigned_to = u.id
        WHERE wo.project_id IS NOT NULL
        GROUP BY u.id, u.real_name, u.username
        ORDER BY estimated_labor_cost DESC, total_hours DESC
        """
    )
    rows = db.execute(sql, {"hourly_rate": DEFAULT_HOURLY_RATE}).fetchall()

    engineers = []
    total_work_orders = 0
    total_hours = 0.0
    total_cost = 0.0

    for row in rows:
        work_order_count = int(row.work_order_count or 0)
        completed_orders = int(row.completed_orders or 0)
        in_progress_orders = int(row.in_progress_orders or 0)
        engineer_hours = float(row.total_hours or 0)
        engineer_cost = float(row.estimated_labor_cost or 0)

        total_work_orders += work_order_count
        total_hours += engineer_hours
        total_cost += engineer_cost

        engineers.append(
            {
                "engineer_id": row.engineer_id,
                "engineer_name": row.engineer_name or f"工程师#{row.engineer_id}",
                "work_order_count": work_order_count,
                "project_count": int(row.project_count or 0),
                "total_hours": round(engineer_hours, 2),
                "estimated_labor_cost": round(engineer_cost, 2),
                "completed_orders": completed_orders,
                "in_progress_orders": in_progress_orders,
                "completion_rate": (
                    round(completed_orders / work_order_count * 100, 2)
                    if work_order_count > 0
                    else 0
                ),
            }
        )

    return {
        "summary": {
            "total_engineers": len(engineers),
            "total_work_orders": total_work_orders,
            "total_hours": round(total_hours, 2),
            "total_estimated_labor_cost": round(total_cost, 2),
            "hourly_rate_used": DEFAULT_HOURLY_RATE,
            "avg_cost_per_hour": round(total_cost / total_hours, 2)
            if total_hours > 0
            else 0,
        },
        "engineers": engineers,
    }


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
            "avg_cost_per_record": round(total_labor_cost / len(details), 2)
            if details
            else 0,
            "latest_cost_date": latest_date,
        },
        "by_source": by_source,
        "details": details,
    }
