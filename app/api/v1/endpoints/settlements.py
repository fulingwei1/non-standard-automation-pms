# -*- coding: utf-8 -*-
"""Project settlement compatibility endpoints used by the settlement page."""

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.models.project.financial import ProjectPaymentPlan
from app.models.sales.contracts import Contract
from app.services.cost.cost_basis import actual_project_cost_filter

router = APIRouter()


def _money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return (
        parsed
        if parsed == parsed and parsed not in (float("inf"), float("-inf"))
        else 0.0
    )


def _safe_margin(profit: float, revenue: float) -> float:
    return round(profit / revenue * 100, 2) if revenue > 0 else 0.0


def _status_from_project(project: Project) -> tuple[str, str]:
    if project.final_payment_completed:
        return "SETTLED", "已结算"
    if project.invoice_issued:
        return "CONFIRMED", "已确认"
    if project.stage in {"S6", "S7", "CLOSING"}:
        return "PENDING", "待确认"
    return "DRAFT", "草稿"


def _demo_rows() -> list[dict[str, Any]]:
    today = date.today().isoformat()
    return [
        {
            "id": 1,
            "settlementNo": "SET-2026-001",
            "projectName": "新能源电池包EOL测试线",
            "customerName": "演示客户A",
            "contractNo": "HT-2026-001",
            "contractAmount": 4_800_000.0,
            "materialCost": 2_050_000.0,
            "laborCost": 680_000.0,
            "outsourcingCost": 420_000.0,
            "expenseCost": 160_000.0,
            "otherCost": 90_000.0,
            "totalCost": 3_400_000.0,
            "grossProfit": 1_400_000.0,
            "grossMargin": 29.17,
            "receivedAmount": 3_600_000.0,
            "receivableAmount": 1_200_000.0,
            "status": "PENDING",
            "statusLabel": "待确认",
            "settlementDate": today,
            "settledBy": "系统演示",
            "milestones": [
                {
                    "name": "预付款",
                    "amount": 1_440_000.0,
                    "received": True,
                    "receivedDate": today,
                },
                {
                    "name": "发货款",
                    "amount": 1_920_000.0,
                    "received": True,
                    "receivedDate": today,
                },
                {
                    "name": "验收款",
                    "amount": 1_200_000.0,
                    "received": False,
                    "dueDate": today,
                },
            ],
        }
    ]


def _project_cost_totals(
    db: Session, project_id: int, project_actual_cost: Any
) -> dict[str, float]:
    totals = {
        "materialCost": 0.0,
        "laborCost": 0.0,
        "outsourcingCost": 0.0,
        "expenseCost": 0.0,
        "otherCost": 0.0,
    }

    category_map = {
        "material": "materialCost",
        "材料": "materialCost",
        "bom": "materialCost",
        "purchase": "materialCost",
        "采购": "materialCost",
        "labor": "laborCost",
        "人工": "laborCost",
        "outsourcing": "outsourcingCost",
        "外协": "outsourcingCost",
        "travel": "expenseCost",
        "差旅": "expenseCost",
        "expense": "expenseCost",
        "费用": "expenseCost",
    }

    for cost in (
        db.query(ProjectCost)
        .filter(ProjectCost.project_id == project_id, actual_project_cost_filter())
        .all()
    ):
        raw_category = f"{cost.cost_type or ''} {cost.cost_category or ''}".lower()
        key = next(
            (
                target
                for marker, target in category_map.items()
                if marker in raw_category
            ),
            "otherCost",
        )
        totals[key] += _money(cost.amount)

    for cost in (
        db.query(FinancialProjectCost)
        .filter(FinancialProjectCost.project_id == project_id)
        .all()
    ):
        raw_category = f"{cost.cost_type or ''} {cost.cost_category or ''}".lower()
        key = next(
            (
                target
                for marker, target in category_map.items()
                if marker in raw_category
            ),
            "otherCost",
        )
        totals[key] += _money(cost.amount)

    known_total = sum(totals.values())
    model_total = _money(project_actual_cost)
    if known_total <= 0 and model_total > 0:
        totals["otherCost"] += model_total
    return totals


def _milestones(db: Session, project_id: int) -> tuple[list[dict[str, Any]], float]:
    plans = (
        db.query(ProjectPaymentPlan)
        .filter(ProjectPaymentPlan.project_id == project_id)
        .order_by(ProjectPaymentPlan.payment_no.asc())
        .all()
    )
    rows = []
    received_total = 0.0
    for plan in plans:
        actual_amount = _money(plan.actual_amount)
        planned_amount = _money(plan.planned_amount)
        received = actual_amount > 0 or plan.status == "COMPLETED"
        received_total += actual_amount
        rows.append(
            {
                "name": plan.payment_name,
                "amount": actual_amount if actual_amount > 0 else planned_amount,
                "received": received,
                "receivedDate": plan.actual_date.isoformat()
                if plan.actual_date
                else None,
                "dueDate": plan.planned_date.isoformat() if plan.planned_date else None,
            }
        )
    return rows, received_total


def _rows(db: Session) -> list[dict[str, Any]]:
    projects = (
        db.query(Project)
        .filter(Project.is_active)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .limit(100)
        .all()
    )
    rows = []
    for project in projects:
        contract = None
        if project.contract_id:
            contract = (
                db.query(Contract).filter(Contract.id == project.contract_id).first()
            )
        if contract is None:
            contract = (
                db.query(Contract).filter(Contract.project_id == project.id).first()
            )

        contract_amount = _money(project.contract_amount)
        if contract and contract_amount <= 0:
            contract_amount = _money(contract.total_amount)
        if contract_amount <= 0:
            contract_amount = _money(project.budget_amount)

        cost_totals = _project_cost_totals(db, project.id, project.actual_cost)
        total_cost = round(sum(cost_totals.values()), 2)
        gross_profit = round(contract_amount - total_cost, 2)
        received_amount = _money(contract.received_amount) if contract else 0.0
        milestones, milestone_received = _milestones(db, project.id)
        if milestone_received > received_amount:
            received_amount = milestone_received
        receivable_amount = max(contract_amount - received_amount, 0.0)
        status, status_label = _status_from_project(project)
        settlement_date = project.final_payment_date or project.actual_end_date

        rows.append(
            {
                "id": project.id,
                "settlementNo": f"SET-{project.project_code}",
                "projectName": project.project_name,
                "customerName": project.customer_name or "未关联客户",
                "contractNo": (contract.contract_code if contract else None)
                or project.contract_no
                or "-",
                "contractAmount": round(contract_amount, 2),
                "materialCost": round(cost_totals["materialCost"], 2),
                "laborCost": round(cost_totals["laborCost"], 2),
                "outsourcingCost": round(cost_totals["outsourcingCost"], 2),
                "expenseCost": round(cost_totals["expenseCost"], 2),
                "otherCost": round(cost_totals["otherCost"], 2),
                "totalCost": total_cost,
                "grossProfit": gross_profit,
                "grossMargin": _safe_margin(gross_profit, contract_amount),
                "receivedAmount": round(received_amount, 2),
                "receivableAmount": round(receivable_amount, 2),
                "status": status,
                "statusLabel": status_label,
                "settlementDate": settlement_date.isoformat()
                if settlement_date
                else None,
                "settledBy": project.pm_name or "项目经理",
                "milestones": milestones,
            }
        )

    return rows or _demo_rows()


@router.get("/settlements/statistics")
def get_settlement_statistics(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    rows = _rows(db)
    return {
        "totalContractAmount": round(
            sum(_money(row["contractAmount"]) for row in rows), 2
        ),
        "totalCost": round(sum(_money(row["totalCost"]) for row in rows), 2),
        "totalProfit": round(sum(_money(row["grossProfit"]) for row in rows), 2),
        "totalReceivable": round(
            sum(_money(row["receivableAmount"]) for row in rows), 2
        ),
        "count": len(rows),
    }


@router.get("/settlements")
def list_settlements(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    return _rows(db)


@router.get("/settlements/{settlement_id}")
def get_settlement(
    settlement_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    for row in _rows(db):
        if row["id"] == settlement_id:
            return row
    raise HTTPException(status_code=404, detail="结算单不存在")
