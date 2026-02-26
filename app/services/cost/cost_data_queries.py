# -*- coding: utf-8 -*-
"""
成本公共数据查询层

提取各成本服务共用的数据库查询逻辑，减少重复代码。
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.project import FinancialProjectCost, Project, ProjectCost


def get_project_budget_stats(db: Session) -> Dict[str, float]:
    """
    获取全局预算统计

    Returns:
        dict with keys: total_budget, total_actual_cost, total_contract_amount, total_projects
    """
    stats = db.query(
        func.sum(Project.budget_amount).label("total_budget"),
        func.sum(Project.actual_cost).label("total_actual_cost"),
        func.sum(Project.contract_amount).label("total_contract_amount"),
        func.count(Project.id).label("total_projects"),
    ).filter(
        Project.stage.notin_(["S0", "S9"])
    ).first()

    return {
        "total_budget": float(stats.total_budget or 0),
        "total_actual_cost": float(stats.total_actual_cost or 0),
        "total_contract_amount": float(stats.total_contract_amount or 0),
        "total_projects": int(stats.total_projects or 0),
    }


def get_project_actual_cost_from_records(
    db: Session, project_id: int
) -> Decimal:
    """
    从 ProjectCost + FinancialProjectCost 合计项目实际成本
    """
    pc = db.query(func.sum(ProjectCost.amount)).filter(
        ProjectCost.project_id == project_id
    ).scalar() or Decimal("0")

    fc = db.query(func.sum(FinancialProjectCost.amount)).filter(
        FinancialProjectCost.project_id == project_id
    ).scalar() or Decimal("0")

    return Decimal(str(pc)) + Decimal(str(fc))


def get_monthly_cost_data(
    db: Session,
    project_id: int,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    获取项目月度成本数据（合并 ProjectCost 和 FinancialProjectCost），
    返回按月排序的列表，包含 monthly_cost 和 cumulative_cost。
    """
    # ProjectCost
    q1 = (
        db.query(
            func.date_format(ProjectCost.cost_date, "%Y-%m").label("month"),
            func.sum(ProjectCost.amount).label("monthly_cost"),
        )
        .filter(ProjectCost.project_id == project_id)
        .filter(ProjectCost.cost_date.isnot(None))
    )
    if start_month:
        q1 = q1.filter(func.date_format(ProjectCost.cost_date, "%Y-%m") >= start_month)
    if end_month:
        q1 = q1.filter(func.date_format(ProjectCost.cost_date, "%Y-%m") <= end_month)
    result1 = q1.group_by("month").all()

    # FinancialProjectCost
    q2 = (
        db.query(
            FinancialProjectCost.cost_month.label("month"),
            func.sum(FinancialProjectCost.amount).label("monthly_cost"),
        )
        .filter(FinancialProjectCost.project_id == project_id)
        .filter(FinancialProjectCost.cost_month.isnot(None))
    )
    if start_month:
        q2 = q2.filter(FinancialProjectCost.cost_month >= start_month)
    if end_month:
        q2 = q2.filter(FinancialProjectCost.cost_month <= end_month)
    result2 = q2.group_by("month").all()

    # 合并
    monthly_dict: Dict[str, float] = {}
    for row in result1:
        monthly_dict[row.month] = monthly_dict.get(row.month, 0) + float(row.monthly_cost or 0)
    for row in result2:
        monthly_dict[row.month] = monthly_dict.get(row.month, 0) + float(row.monthly_cost or 0)

    # 排序 + 累计
    cumulative = 0.0
    result = []
    for month in sorted(monthly_dict.keys()):
        cost = monthly_dict[month]
        cumulative += cost
        result.append({
            "month": month,
            "monthly_cost": cost,
            "cumulative_cost": cumulative,
        })
    return result


def get_month_cost_total(
    db: Session,
    month_start: date,
    month_end: date,
    project_id: Optional[int] = None,
) -> float:
    """
    获取指定月份的成本合计（全局或单项目）
    """
    q1 = db.query(func.sum(ProjectCost.amount)).filter(
        and_(ProjectCost.cost_date >= month_start, ProjectCost.cost_date <= month_end)
    )
    q2 = db.query(func.sum(FinancialProjectCost.amount)).filter(
        and_(FinancialProjectCost.cost_date >= month_start, FinancialProjectCost.cost_date <= month_end)
    )
    if project_id:
        q1 = q1.filter(ProjectCost.project_id == project_id)
        q2 = q2.filter(FinancialProjectCost.project_id == project_id)

    return float(q1.scalar() or 0) + float(q2.scalar() or 0)


def get_cost_by_type(
    db: Session, project_id: int, cost_type: str
) -> Decimal:
    """按类型获取项目成本"""
    result = db.query(func.sum(ProjectCost.amount)).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.cost_type == cost_type,
    ).scalar() or Decimal("0")
    return Decimal(str(result))
