from datetime import date
from decimal import Decimal

from app.schemas.rd_project import (
    RdCostAllocationRuleResponse,
    RdCostResponse,
    RdCostTypeResponse,
    RdProjectCategoryResponse,
    RdProjectResponse,
)


TODAY = date(2026, 4, 14)


def test_rd_project_category_response_normalizes_none_fields():
    schema = RdProjectCategoryResponse(
        id=1,
        category_code="CAT-001",
        category_name="自研",
        category_type="SELF",
        sort_order=None,
        is_active=None,
    )

    assert schema.sort_order == 0
    assert schema.is_active is True


def test_rd_project_response_normalizes_none_fields():
    schema = RdProjectResponse(
        id=1,
        project_no="RD-001",
        project_name="视觉检测平台",
        category_type="SELF",
        initiation_date=TODAY,
        budget_amount=None,
        status=None,
        approval_status=None,
        total_cost=None,
        total_hours=None,
        participant_count=None,
    )

    assert schema.budget_amount == Decimal("0")
    assert schema.status == "DRAFT"
    assert schema.approval_status == "PENDING"
    assert schema.total_cost == Decimal("0")
    assert schema.total_hours == Decimal("0")
    assert schema.participant_count == 0


def test_rd_cost_type_response_normalizes_none_fields():
    schema = RdCostTypeResponse(
        id=1,
        type_code="LABOR",
        type_name="人工费",
        category="LABOR",
        sort_order=None,
        is_active=None,
        is_deductible=None,
        deduction_rate=None,
    )

    assert schema.sort_order == 0
    assert schema.is_active is True
    assert schema.is_deductible is True
    assert schema.deduction_rate == Decimal("100")


def test_rd_cost_response_normalizes_none_fields():
    schema = RdCostResponse(
        id=1,
        cost_no="COST-001",
        rd_project_id=1,
        cost_type_id=1,
        cost_date=TODAY,
        cost_amount=Decimal("1000"),
        is_allocated=None,
        status=None,
    )

    assert schema.is_allocated is False
    assert schema.status == "DRAFT"


def test_rd_cost_allocation_rule_response_normalizes_none_fields():
    schema = RdCostAllocationRuleResponse(
        id=1,
        rule_name="按工时分摊",
        rule_type="PROPORTION",
        allocation_basis="HOURS",
        is_active=None,
    )

    assert schema.is_active is True
