# -*- coding: utf-8 -*-
"""RPT-04: finance reports must not return demo fallbacks."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.finance_reports import (
    get_cash_flow,
    get_cost_analysis,
    get_monthly_trend,
    get_project_profitability,
)
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import Project, ProjectCost


def _row_by_category(rows: list[dict], category: str) -> dict:
    return next(row for row in rows if row["category"] == category)


def test_finance_reports_return_empty_lists_when_no_real_data(db_session: Session):
    user = object()

    assert get_monthly_trend(year=2026, db=db_session, current_user=user) == []
    assert get_cost_analysis(period="month", db=db_session, current_user=user) == []
    assert get_project_profitability(limit=10, db=db_session, current_user=user) == []
    assert (
        get_cash_flow(period="month", year=2026, db=db_session, current_user=user)
        == []
    )


def test_cost_analysis_uses_approved_budget_items_not_cost_multiplier(
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-RPT04-{suffix}",
        project_name="RPT04 finance report",
        status="IN_PROGRESS",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()

    budget = ProjectBudget(
        budget_no=f"BUD-RPT04-{suffix}",
        project_id=project.id,
        budget_name="RPT04 approved budget",
        budget_type="INITIAL",
        total_amount=Decimal("430.00"),
        status="APPROVED",
        is_active=True,
    )
    db_session.add(budget)
    db_session.flush()

    db_session.add_all(
        [
            ProjectBudgetItem(
                budget_id=budget.id,
                item_no=1,
                cost_category="材料成本",
                cost_item="材料",
                budget_amount=Decimal("130.00"),
            ),
            ProjectBudgetItem(
                budget_id=budget.id,
                item_no=2,
                cost_category="人工成本",
                cost_item="工时",
                budget_amount=Decimal("300.00"),
            ),
            ProjectCost(
                project_id=project.id,
                cost_type="MATERIAL",
                cost_category="材料成本",
                amount=Decimal("100.00"),
                cost_date=date(2026, 1, 10),
                cost_basis="ACTUAL",
            ),
            ProjectCost(
                project_id=project.id,
                cost_type="MATERIAL",
                cost_category="材料成本",
                amount=Decimal("999.00"),
                cost_date=date(2026, 1, 11),
                cost_basis="PLAN",
            ),
        ]
    )
    db_session.commit()

    rows = get_cost_analysis(period="month", db=db_session, current_user=object())

    material = _row_by_category(rows, "材料成本")
    labor = _row_by_category(rows, "人工成本")
    assert material["amount"] == 100.0
    assert material["budget"] == 130.0
    assert material["variance"] == -30.0
    assert labor["amount"] == 0.0
    assert labor["budget"] == 300.0
    assert labor["variance"] == -300.0
