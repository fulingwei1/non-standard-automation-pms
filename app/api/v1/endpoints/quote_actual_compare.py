# -*- coding: utf-8 -*-
"""报价 vs 实际成本对比分析"""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/list", summary="全项目报价vs实际对比")
def compare_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    sql = text("""
        SELECT p.id, p.project_name, p.project_code, p.product_category, p.stage,
               p.contract_amount, p.budget_amount, p.actual_cost
        FROM projects p
        WHERE p.is_active = 1 AND p.contract_amount > 0
        ORDER BY p.id
    """)
    rows = db.execute(sql).fetchall()

    projects = []
    for r in rows:
        contract = float(r.contract_amount or 0)
        budget = float(r.budget_amount or 0)
        actual = float(r.actual_cost or 0)

        # Cost breakdown
        cost_sql = text("""
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type ORDER BY total DESC
        """)
        breakdown = {c.cost_type: float(c.total) for c in db.execute(cost_sql, {"pid": r.id}).fetchall()}

        planned_margin = round((contract - budget) / contract * 100, 2) if contract > 0 else 0
        actual_margin = round((contract - actual) / contract * 100, 2) if contract > 0 else 0
        budget_var = round((actual - budget) / budget * 100, 2) if budget > 0 else 0

        projects.append({
            "project_id": r.id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "product_category": r.product_category,
            "stage": r.stage,
            "contract_amount": contract,
            "budget_amount": budget,
            "actual_cost": actual,
            "planned_margin": planned_margin,
            "actual_margin": actual_margin,
            "margin_gap": round(actual_margin - planned_margin, 2),
            "budget_variance_pct": budget_var,
            "overrun": actual > budget,
            "cost_breakdown": breakdown,
        })

    total_contract = sum(p["contract_amount"] for p in projects)
    total_budget = sum(p["budget_amount"] for p in projects)
    total_actual = sum(p["actual_cost"] for p in projects)

    return {
        "summary": {
            "total_projects": len(projects),
            "total_contract": total_contract,
            "total_budget": total_budget,
            "total_actual": total_actual,
            "overall_planned_margin": round((total_contract - total_budget) / total_contract * 100, 2) if total_contract else 0,
            "overall_actual_margin": round((total_contract - total_actual) / total_contract * 100, 2) if total_contract else 0,
            "overrun_count": sum(1 for p in projects if p["overrun"]),
        },
        "projects": projects,
    }


@router.get("/{project_id}", summary="单项目详细对比")
def compare_detail(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
) -> Any:
    proj_sql = text("SELECT * FROM projects WHERE id = :pid")
    p = db.execute(proj_sql, {"pid": project_id}).fetchone()
    if not p:
        return {"error": "项目不存在"}

    # Monthly cost accumulation
    monthly_sql = text("""
        SELECT strftime('%Y-%m', cost_date) as month, cost_type, SUM(amount) as total
        FROM project_costs WHERE project_id = :pid AND cost_date IS NOT NULL
        GROUP BY month, cost_type ORDER BY month
    """)
    monthly_rows = db.execute(monthly_sql, {"pid": project_id}).fetchall()

    monthly = {}
    for r in monthly_rows:
        if r.month not in monthly:
            monthly[r.month] = {"month": r.month, "total": 0}
        monthly[r.month][r.cost_type] = float(r.total)
        monthly[r.month]["total"] += float(r.total)

    # Cost type breakdown
    type_sql = text("""
        SELECT cost_type, SUM(amount) as total, COUNT(*) as records
        FROM project_costs WHERE project_id = :pid
        GROUP BY cost_type ORDER BY total DESC
    """)
    types = [
        {"cost_type": r.cost_type, "amount": float(r.total), "records": r.records}
        for r in db.execute(type_sql, {"pid": project_id}).fetchall()
    ]

    contract = float(p.contract_amount or 0)
    budget = float(p.budget_amount or 0)
    actual = float(p.actual_cost or 0)

    return {
        "project": {
            "id": p.id, "name": p.project_name, "code": p.project_code,
            "contract_amount": contract, "budget_amount": budget, "actual_cost": actual,
            "planned_margin": round((contract - budget) / contract * 100, 2) if contract else 0,
            "actual_margin": round((contract - actual) / contract * 100, 2) if contract else 0,
        },
        "cost_breakdown": types,
        "monthly_trend": sorted(monthly.values(), key=lambda x: x["month"]),
    }
