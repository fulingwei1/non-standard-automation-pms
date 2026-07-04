# -*- coding: utf-8 -*-
"""Financial report endpoints used by the financial reports page."""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.models.project.financial import ProjectPaymentPlan
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.services.cost.cost_basis import actual_project_cost_filter

router = APIRouter()


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


def _status_from_margin(margin: float) -> str:
    if margin >= 30:
        return "good"
    if margin >= 20:
        return "warning"
    return "critical"


def _is_actual_project_cost(cost: ProjectCost) -> bool:
    return (getattr(cost, "cost_basis", None) or "ACTUAL").upper() == "ACTUAL"


def _amount_parts(
    *,
    amount_without_tax: Any = None,
    tax_amount: Any = None,
    amount_with_tax: Any = None,
    fallback_amount: Any = None,
) -> dict[str, float]:
    net = _money(amount_without_tax)
    tax = _money(tax_amount)
    gross = _money(amount_with_tax)
    fallback = _money(fallback_amount)
    if gross <= 0 and fallback > 0:
        gross = fallback
    if net <= 0 and gross > 0:
        net = gross - tax if tax > 0 else gross
    if gross <= 0 and net > 0:
        gross = net + tax
    return {"net": net, "tax": tax, "gross": gross}


def _contract_parts(contract: Contract) -> dict[str, float]:
    return _amount_parts(
        amount_without_tax=getattr(contract, "amount_without_tax", None),
        tax_amount=getattr(contract, "tax_amount", None),
        amount_with_tax=getattr(contract, "amount_with_tax", None),
        fallback_amount=contract.total_amount,
    )


def _cost_parts(cost: Any) -> dict[str, float]:
    amount = _money(getattr(cost, "amount", None))
    tax = _money(getattr(cost, "tax_amount", None))
    return {"net": amount, "tax": tax, "gross": amount + tax}


def _invoice_parts(invoice: Invoice) -> dict[str, float]:
    return _amount_parts(
        amount_without_tax=invoice.amount,
        tax_amount=invoice.tax_amount,
        amount_with_tax=invoice.total_amount,
        fallback_amount=invoice.amount,
    )


def _paid_parts(
    parts: dict[str, float],
    paid_amount: Any,
    *,
    default_to_full: bool = True,
) -> dict[str, float]:
    paid_gross = _money(paid_amount)
    if paid_gross <= 0:
        if not default_to_full:
            return {"net": 0.0, "tax": 0.0, "gross": 0.0}
        paid_gross = parts["gross"]
    if parts["gross"] <= 0 or paid_gross == parts["gross"]:
        return {"net": parts["net"], "tax": parts["tax"], "gross": paid_gross}
    ratio = paid_gross / parts["gross"]
    paid_net = parts["net"] * ratio
    paid_tax = parts["tax"] * ratio
    return {"net": paid_net, "tax": paid_tax, "gross": paid_gross}


def _add_parts(totals: dict[str, float], parts: dict[str, float]) -> None:
    totals["net"] += parts["net"]
    totals["tax"] += parts["tax"]
    totals["gross"] += parts["gross"]


def _zero_parts_by_month() -> defaultdict[str, dict[str, float]]:
    return defaultdict(lambda: {"net": 0.0, "tax": 0.0, "gross": 0.0})


def _round_parts(parts: dict[str, float]) -> dict[str, float]:
    return {
        "net": round(parts["net"], 2),
        "tax": round(parts["tax"], 2),
        "gross": round(parts["gross"], 2),
    }


def _project_cost_parts(project: Project) -> dict[str, float]:
    totals = {"net": 0.0, "tax": 0.0, "gross": 0.0}
    model_total = _money(project.actual_cost)
    if model_total > 0:
        _add_parts(totals, _amount_parts(fallback_amount=model_total))
    else:
        for cost in project.costs.all():
            if _is_actual_project_cost(cost):
                _add_parts(totals, _cost_parts(cost))
    for cost in project.financial_costs.all():
        _add_parts(totals, _cost_parts(cost))
    return totals


def _project_revenue_parts(project: Project, db: Session) -> dict[str, float]:
    if _money(project.contract_amount) > 0:
        return _amount_parts(fallback_amount=project.contract_amount)

    totals = {"net": 0.0, "tax": 0.0, "gross": 0.0}
    for contract in db.query(Contract).filter(Contract.project_id == project.id).all():
        _add_parts(totals, _contract_parts(contract))
    return totals


def _project_cost_total(project: Project) -> float:
    return _project_cost_parts(project)["net"]


def _budget_by_cost_category(db: Session) -> dict[str, float]:
    budgets: dict[str, float] = defaultdict(float)
    budget_items = (
        db.query(ProjectBudgetItem)
        .join(ProjectBudget, ProjectBudgetItem.budget_id == ProjectBudget.id)
        .filter(ProjectBudget.is_active, ProjectBudget.status == "APPROVED")
        .all()
    )
    for item in budget_items:
        category = item.cost_category or "未分类预算"
        budgets[category] += _money(item.budget_amount)
    return budgets


@router.get("/monthly-trend")
def get_monthly_trend(
    year: int = Query(default_factory=lambda: date.today().year),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    revenue_by_month = _zero_parts_by_month()
    cost_by_month = _zero_parts_by_month()
    cash_by_month = _zero_parts_by_month()

    for contract in db.query(Contract).all():
        month = _month_key(contract.signing_date or contract.created_at)
        if month and month.startswith(str(year)):
            contract_parts = _contract_parts(contract)
            _add_parts(revenue_by_month[month], contract_parts)
            _add_parts(
                cash_by_month[month],
                _paid_parts(contract_parts, contract.received_amount, default_to_full=False),
            )

    for invoice in db.query(Invoice).all():
        month = _month_key(
            invoice.paid_date or invoice.issue_date or invoice.created_at
        )
        if month and month.startswith(str(year)):
            _add_parts(cash_by_month[month], _paid_parts(_invoice_parts(invoice), invoice.paid_amount))

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        month = _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            _add_parts(cost_by_month[month], _cost_parts(cost))

    for cost in db.query(FinancialProjectCost).all():
        month = cost.cost_month or _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            _add_parts(cost_by_month[month], _cost_parts(cost))

    months = sorted(set(revenue_by_month) | set(cost_by_month) | set(cash_by_month))
    if not months:
        return []

    rows = []
    for month in months:
        revenue = _round_parts(revenue_by_month[month])
        cost = _round_parts(cost_by_month[month])
        cash = _round_parts(cash_by_month[month])
        rows.append(
            {
                "month": month,
                "revenue": revenue["gross"],
                "revenueWithoutTax": revenue["net"],
                "revenueTaxAmount": revenue["tax"],
                "revenueWithTax": revenue["gross"],
                "cost": cost["net"],
                "costTaxAmount": cost["tax"],
                "costWithTax": cost["gross"],
                "profit": round(revenue["net"] - cost["net"], 2),
                "profitWithoutTax": round(revenue["net"] - cost["net"], 2),
                "profitWithTax": round(revenue["gross"] - cost["gross"], 2),
                "cashInflow": cash["gross"],
                "cashInflowWithoutTax": cash["net"],
                "cashInflowTaxAmount": cash["tax"],
                "cashInflowWithTax": cash["gross"],
                "cashFlow": round(cash["gross"] - cost["gross"], 2),
                "cashFlowWithoutTax": round(cash["net"] - cost["net"], 2),
                "cashFlowWithTax": round(cash["gross"] - cost["gross"], 2),
            }
        )
    return rows


@router.get("/cost-analysis")
def get_cost_analysis(
    period: str = Query("month"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    totals: defaultdict[str, dict[str, float]] = defaultdict(
        lambda: {"net": 0.0, "tax": 0.0, "gross": 0.0}
    )

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        category = cost.cost_category or cost.cost_type or "业务成本"
        _add_parts(totals[category], _cost_parts(cost))

    for cost in db.query(FinancialProjectCost).all():
        category = cost.cost_category or cost.cost_type or "财务成本"
        _add_parts(totals[category], _cost_parts(cost))

    budgets = _budget_by_cost_category(db)
    categories = sorted(set(totals) | set(budgets))
    rows = []
    for category in categories:
        parts = _round_parts(totals.get(category, {"net": 0.0, "tax": 0.0, "gross": 0.0}))
        amount = parts["net"]
        budget = budgets.get(category, 0)
        if amount <= 0 and budget <= 0:
            continue
        rows.append(
            {
                "category": category,
                "amount": round(amount, 2),
                "taxAmount": parts["tax"],
                "amountWithTax": parts["gross"],
                "budget": round(budget, 2),
            }
        )

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
        revenue_parts = _round_parts(_project_revenue_parts(project, db))
        cost_parts = _round_parts(_project_cost_parts(project))
        if revenue_parts["gross"] <= 0 and cost_parts["gross"] <= 0:
            continue
        profit_without_tax = round(revenue_parts["net"] - cost_parts["net"], 2)
        profit_with_tax = round(revenue_parts["gross"] - cost_parts["gross"], 2)
        margin = (
            round(profit_without_tax / revenue_parts["net"] * 100, 2)
            if revenue_parts["net"]
            else 0
        )
        rows.append(
            {
                "project": project.short_name
                or project.project_name
                or project.project_code,
                "revenue": revenue_parts["gross"],
                "revenueWithoutTax": revenue_parts["net"],
                "revenueTaxAmount": revenue_parts["tax"],
                "revenueWithTax": revenue_parts["gross"],
                "cost": cost_parts["net"],
                "costTaxAmount": cost_parts["tax"],
                "costWithTax": cost_parts["gross"],
                "profit": profit_without_tax,
                "profitWithoutTax": profit_without_tax,
                "profitWithTax": profit_with_tax,
                "margin": margin,
                "status": _status_from_margin(margin),
            }
        )

    if rows:
        return rows[:limit]

    return []


@router.get("/cash-flow")
def get_cash_flow(
    period: str = Query("month"),
    year: int = Query(default_factory=lambda: date.today().year),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    inflow_by_month = _zero_parts_by_month()
    outflow_by_month = _zero_parts_by_month()

    for plan in db.query(ProjectPaymentPlan).all():
        month = _month_key(plan.actual_date or plan.planned_date or plan.created_at)
        if month and month.startswith(str(year)):
            _add_parts(
                inflow_by_month[month],
                _amount_parts(fallback_amount=plan.actual_amount or plan.planned_amount),
            )

    for invoice in db.query(Invoice).all():
        month = _month_key(
            invoice.paid_date or invoice.issue_date or invoice.created_at
        )
        if month and month.startswith(str(year)):
            _add_parts(
                inflow_by_month[month],
                _paid_parts(_invoice_parts(invoice), invoice.paid_amount),
            )

    for cost in db.query(ProjectCost).filter(actual_project_cost_filter()).all():
        month = _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            _add_parts(outflow_by_month[month], _cost_parts(cost))

    for cost in db.query(FinancialProjectCost).all():
        month = cost.cost_month or _month_key(cost.cost_date or cost.created_at)
        if month and month.startswith(str(year)):
            _add_parts(outflow_by_month[month], _cost_parts(cost))

    months = sorted(set(inflow_by_month) | set(outflow_by_month))
    if not months:
        return []

    rows = []
    for month in months:
        inflow = _round_parts(inflow_by_month[month])
        outflow = _round_parts(outflow_by_month[month])
        rows.append(
            {
                "month": month,
                "inflow": inflow["gross"],
                "inflowWithoutTax": inflow["net"],
                "inflowTaxAmount": inflow["tax"],
                "inflowWithTax": inflow["gross"],
                "outflow": outflow["net"],
                "outflowTaxAmount": outflow["tax"],
                "outflowWithTax": outflow["gross"],
                "net": round(inflow["gross"] - outflow["gross"], 2),
                "netWithoutTax": round(inflow["net"] - outflow["net"], 2),
                "netWithTax": round(inflow["gross"] - outflow["gross"], 2),
            }
        )
    return rows
