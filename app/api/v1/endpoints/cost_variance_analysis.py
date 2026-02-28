# -*- coding: utf-8 -*-
"""成本偏差根因分析"""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/summary", summary="全项目成本偏差汇总")
def variance_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    sql = text("""
        SELECT p.id, p.project_name, p.project_code, p.product_category,
               p.contract_amount, p.budget_amount, p.actual_cost
        FROM projects p
        WHERE p.is_active = 1 AND p.budget_amount > 0
        ORDER BY p.id
    """)
    rows = db.execute(sql).fetchall()

    projects = []
    total_overrun = 0
    for r in rows:
        budget = float(r.budget_amount or 0)
        actual = float(r.actual_cost or 0)
        variance = actual - budget
        var_pct = round(variance / budget * 100, 2) if budget > 0 else 0

        # Per cost_type breakdown
        type_sql = text("""
            SELECT cost_type, SUM(amount) as total
            FROM project_costs WHERE project_id = :pid
            GROUP BY cost_type
        """)
        breakdown = {}
        for c in db.execute(type_sql, {"pid": r.id}).fetchall():
            breakdown[c.cost_type] = float(c.total)

        if variance > 0:
            total_overrun += variance

        projects.append({
            "project_id": r.id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "product_category": r.product_category,
            "budget": budget,
            "actual": actual,
            "variance": round(variance, 2),
            "variance_pct": var_pct,
            "overrun": variance > 0,
            "cost_breakdown": breakdown,
        })

    overrun_projects = [p for p in projects if p["overrun"]]
    worst = max(projects, key=lambda x: x["variance_pct"]) if projects else None

    return {
        "summary": {
            "total_projects": len(projects),
            "overrun_count": len(overrun_projects),
            "on_budget_count": len(projects) - len(overrun_projects),
            "total_overrun_amount": round(total_overrun, 2),
            "worst_project": worst["project_name"] if worst else None,
            "worst_variance": worst["variance_pct"] if worst else 0,
        },
        "projects": projects,
    }


@router.get("/patterns", summary="跨项目偏差模式分析")
def variance_patterns(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # Which cost_type has highest average overrun
    sql = text("""
        SELECT pc.cost_type,
               COUNT(DISTINCT pc.project_id) as project_count,
               SUM(pc.amount) as total_cost,
               AVG(pc.amount) as avg_per_record
        FROM project_costs pc
        JOIN projects p ON pc.project_id = p.id
        WHERE p.is_active = 1
        GROUP BY pc.cost_type
        ORDER BY total_cost DESC
    """)
    by_type = [
        {
            "cost_type": r.cost_type,
            "project_count": r.project_count,
            "total_cost": round(float(r.total_cost), 2),
            "avg_per_record": round(float(r.avg_per_record), 2),
        }
        for r in db.execute(sql).fetchall()
    ]

    # By product category
    cat_sql = text("""
        SELECT p.product_category,
               COUNT(*) as count,
               AVG(CASE WHEN p.budget_amount > 0 
                   THEN (p.actual_cost - p.budget_amount) * 100.0 / p.budget_amount ELSE 0 END) as avg_variance
        FROM projects p
        WHERE p.is_active = 1 AND p.budget_amount > 0
        GROUP BY p.product_category
        ORDER BY avg_variance DESC
    """)
    by_category = [
        {
            "category": r.product_category or "未分类",
            "count": r.count,
            "avg_variance_pct": round(float(r.avg_variance), 2),
        }
        for r in db.execute(cat_sql).fetchall()
    ]

    # Insights
    insights = []
    if by_type:
        top = by_type[0]
        insights.append(f"💰 {top['cost_type']}成本占比最大，共¥{top['total_cost']/10000:.1f}万")
    for cat in by_category:
        if cat["avg_variance_pct"] > 10:
            insights.append(f"⚠️ {cat['category']}类项目平均超支{cat['avg_variance_pct']}%")
        elif cat["avg_variance_pct"] < -5:
            insights.append(f"✅ {cat['category']}类项目平均节余{abs(cat['avg_variance_pct'])}%")

    return {
        "by_cost_type": by_type,
        "by_category": by_category,
        "insights": insights,
    }


@router.get("/{project_id}", summary="单项目偏差深度分析")
def variance_detail(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
) -> Any:
    p_sql = text("SELECT * FROM projects WHERE id = :pid")
    p = db.execute(p_sql, {"pid": project_id}).fetchone()
    if not p:
        return {"error": "项目不存在"}

    budget = float(p.budget_amount or 0)
    actual = float(p.actual_cost or 0)

    # Breakdown by type
    type_sql = text("""
        SELECT cost_type, SUM(amount) as total, COUNT(*) as records,
               MIN(cost_date) as first_date, MAX(cost_date) as last_date
        FROM project_costs WHERE project_id = :pid
        GROUP BY cost_type ORDER BY total DESC
    """)
    breakdown = [
        {
            "cost_type": r.cost_type,
            "amount": float(r.total),
            "records": r.records,
            "pct_of_total": round(float(r.total) / actual * 100, 1) if actual > 0 else 0,
            "first_date": r.first_date,
            "last_date": r.last_date,
        }
        for r in db.execute(type_sql, {"pid": project_id}).fetchall()
    ]

    # Monthly trend
    monthly_sql = text("""
        SELECT strftime('%Y-%m', cost_date) as month, SUM(amount) as total
        FROM project_costs WHERE project_id = :pid AND cost_date IS NOT NULL
        GROUP BY month ORDER BY month
    """)
    cumulative = 0
    monthly = []
    for r in db.execute(monthly_sql, {"pid": project_id}).fetchall():
        cumulative += float(r.total)
        monthly.append({"month": r.month, "amount": float(r.total), "cumulative": round(cumulative, 2)})

    # Top cost records
    top_sql = text("""
        SELECT cost_type, amount, description, cost_date, source_no
        FROM project_costs WHERE project_id = :pid
        ORDER BY amount DESC LIMIT 5
    """)
    top_costs = [
        {"cost_type": r.cost_type, "amount": float(r.amount), "description": r.description,
         "date": r.cost_date, "source": r.source_no}
        for r in db.execute(top_sql, {"pid": project_id}).fetchall()
    ]

    return {
        "project": {
            "name": p.project_name, "code": p.project_code,
            "budget": budget, "actual": actual,
            "variance": round(actual - budget, 2),
            "variance_pct": round((actual - budget) / budget * 100, 2) if budget > 0 else 0,
        },
        "cost_breakdown": breakdown,
        "monthly_trend": monthly,
        "top_costs": top_costs,
    }
