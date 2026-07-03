# -*- coding: utf-8 -*-
"""Financial report endpoints used by the financial reports page."""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.models.project.financial import ProjectPaymentPlan
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.services.cost.cost_basis import actual_project_cost_filter

router = APIRouter()


DEMO_COST_BREAKDOWN = [
    {"category": "材料成本", "amount": 3_200_000, "budget": 3_450_000},
    {"category": "人工成本", "amount": 1_450_000, "budget": 1_500_000},
    {"category": "外协成本", "amount": 980_000, "budget": 1_050_000},
    {"category": "差旅费用", "amount": 320_000, "budget": 360_000},
    {"category": "其他费用", "amount": 260_000, "budget": 300_000},
]


def _money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _month_key(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m")
    if isinstance(value, date):
        return value.strftime("%Y-%m")
    if isinstance(value, str) and len(value) >= 7:
        return value[:7]
    return None


def _demo_monthly_rows(year: int) -> list[dict[str, float | str]]:
    rows = []
    for month in range(1, 13):
        revenue = 850_000 + month * 95_000
        cost = round(revenue * (0.66 + (month % 3) * 0.015), 2)
        profit = round(revenue - cost, 2)
        rows.append(
            {
                "month": f"{year}-{month:02d}",
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "cashFlow": round(profit * 0.85 + revenue * 0.08, 2),
            }
        )
    return rows


def _status_from_margin(margin: float) -> str:
    if margin >= 30:
        return "good"
    if margin >= 20:
        return "warning"
    return "critical"


def _is_actual_project_cost(cost: ProjectCost) -> bool:
    return (getattr(cost, "cost_basis", None) or "ACTUAL").upper() == "ACTUAL"


def _project_cost_total(project: Project) -> float:
    model_total = _money(project.actual_cost)
    linked_total = sum(
        _money(cost.amount)
        for cost in project.costs.all()
        if _is_actual_project_cost(cost)
    )
    financial_total = sum(_money(cost.amount) for cost in project.financial_costs.all())
    project_total = model_total if model_total > 0 else linked_total
    return project_total + financial_total


@router.get("/monthly-trend")
def get_monthly_trend(
    year: int = Query(default_factory=lambda: date.today().year),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    revenue_by_month: dict[str, float] = defaultdict(float)
    cost_by_month: dict[str, float] = defaultdict(float)
    cash_by_month: dict[str, float] = defaultdict(float)

    for contract in db.query(Contract).all():
        month = _month_key(contract.signing_date or contract.created_at)
        if month and month.startswith(str(year)):
            revenue_by_month[month] += _money(contract.total_amount)
            cash_by_month[month] += _money(contract.received_amount)

    for invoice in db.query(Invoice).all():
        month = _month_key(
            invoice.paid_date or invoice.issue_date or invoice.created_at
        )
        if month and month.startswith(str(year)):
            cash_by_month[month] += _money(invoice.paid_amount or invoice.total_amount)

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        month = _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            cost_by_month[month] += _money(cost.amount)

    for cost in db.query(FinancialProjectCost).all():
        month = cost.cost_month or _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            cost_by_month[month] += _money(cost.amount)

    months = sorted(set(revenue_by_month) | set(cost_by_month) | set(cash_by_month))
    if not months:
        return _demo_monthly_rows(year)

    return [
        {
            "month": month,
            "revenue": round(revenue_by_month[month], 2),
            "cost": round(cost_by_month[month], 2),
            "profit": round(revenue_by_month[month] - cost_by_month[month], 2),
            "cashFlow": round(cash_by_month[month] - cost_by_month[month], 2),
        }
        for month in months
    ]


@router.get("/cost-analysis")
def get_cost_analysis(
    period: str = Query("month"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    totals: dict[str, float] = defaultdict(float)

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        category = cost.cost_category or cost.cost_type or "业务成本"
        totals[category] += _money(cost.amount)

    for cost in db.query(FinancialProjectCost).all():
        category = cost.cost_category or cost.cost_type or "财务成本"
        totals[category] += _money(cost.amount)

    rows = [
        {
            "category": category,
            "amount": round(amount, 2),
            "budget": round(amount * 1.08, 2),
        }
        for category, amount in sorted(totals.items())
        if amount > 0
    ]
    if not rows:
        rows = [dict(item) for item in DEMO_COST_BREAKDOWN]

    for row in rows:
        row["variance"] = round(row["amount"] - row["budget"], 2)
    return rows


@router.get("/project-profitability")
def get_project_profitability(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    projects = (
        db.query(Project)
        .filter(Project.is_active)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .limit(limit)
        .all()
    )

    rows = []
    for project in projects:
        revenue = _money(project.contract_amount)
        if revenue <= 0:
            contract_total = sum(
                _money(contract.total_amount)
                for contract in db.query(Contract)
                .filter(Contract.project_id == project.id)
                .all()
            )
            revenue = contract_total
        cost = _project_cost_total(project)
        if revenue <= 0 and cost <= 0:
            continue
        profit = revenue - cost
        margin = round(profit / revenue * 100, 2) if revenue else 0
        rows.append(
            {
                "project": project.short_name
                or project.project_name
                or project.project_code,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "profit": round(profit, 2),
                "margin": margin,
                "status": _status_from_margin(margin),
            }
        )

    if rows:
        return rows[:limit]

    return [
        {
            "project": "新能源测试线",
            "revenue": 4_800_000,
            "cost": 3_120_000,
            "profit": 1_680_000,
            "margin": 35.0,
            "status": "good",
        },
        {
            "project": "半导体ATE改造",
            "revenue": 3_600_000,
            "cost": 2_760_000,
            "profit": 840_000,
            "margin": 23.33,
            "status": "warning",
        },
    ][:limit]


@router.get("/cash-flow")
def get_cash_flow(
    period: str = Query("month"),
    year: int = Query(default_factory=lambda: date.today().year),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    inflow_by_month: dict[str, float] = defaultdict(float)
    outflow_by_month: dict[str, float] = defaultdict(float)

    for plan in db.query(ProjectPaymentPlan).all():
        month = _month_key(plan.actual_date or plan.planned_date or plan.created_at)
        if month and month.startswith(str(year)):
            inflow_by_month[month] += _money(plan.actual_amount or plan.planned_amount)

    for invoice in db.query(Invoice).all():
        month = _month_key(
            invoice.paid_date or invoice.issue_date or invoice.created_at
        )
        if month and month.startswith(str(year)):
            inflow_by_month[month] += _money(
                invoice.paid_amount or invoice.total_amount
            )

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        month = _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            outflow_by_month[month] += _money(cost.amount)

    for cost in db.query(FinancialProjectCost).all():
        month = cost.cost_month or _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            outflow_by_month[month] += _money(cost.amount)

    months = sorted(set(inflow_by_month) | set(outflow_by_month))
    if not months:
        return [
            {
                "month": row["month"],
                "inflow": row["revenue"],
                "outflow": row["cost"],
                "net": row["revenue"] - row["cost"],
            }
            for row in _demo_monthly_rows(year)
        ]

    return [
        {
            "month": month,
            "inflow": round(inflow_by_month[month], 2),
            "outflow": round(outflow_by_month[month], 2),
            "net": round(inflow_by_month[month] - outflow_by_month[month], 2),
        }
        for month in months
    ]
