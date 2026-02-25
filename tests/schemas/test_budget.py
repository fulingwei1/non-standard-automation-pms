# -*- coding: utf-8 -*-
"""Tests for app/schemas/budget.py"""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.budget import (
    ProjectBudgetItemCreate,
    ProjectBudgetItemUpdate,
    ProjectBudgetCreate,
    ProjectBudgetUpdate,
    ProjectBudgetResponse,
    ProjectBudgetApproveRequest,
    ProjectCostAllocationRuleCreate,
    ProjectCostAllocationRequest,
)


class TestProjectBudgetItemCreate:
    def test_valid(self):
        i = ProjectBudgetItemCreate(
            item_no=1, cost_category="材料费", cost_item="螺丝",
            budget_amount=Decimal("1000"),
        )
        assert i.remark is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProjectBudgetItemCreate()

    def test_with_machine(self):
        i = ProjectBudgetItemCreate(
            item_no=1, cost_category="人工", cost_item="工时",
            budget_amount=Decimal("5000"), machine_id=1,
        )
        assert i.machine_id == 1


class TestProjectBudgetCreate:
    def test_valid(self):
        b = ProjectBudgetCreate(
            project_id=1, budget_name="初始预算",
            total_amount=Decimal("100000"),
        )
        assert b.budget_type == "INITIAL"
        assert b.items == []

    def test_with_items(self):
        item = ProjectBudgetItemCreate(
            item_no=1, cost_category="C", cost_item="I",
            budget_amount=Decimal("1000"),
        )
        b = ProjectBudgetCreate(
            project_id=1, budget_name="预算", total_amount=Decimal("1000"),
            items=[item],
        )
        assert len(b.items) == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProjectBudgetCreate()

    def test_with_dates(self):
        b = ProjectBudgetCreate(
            project_id=1, budget_name="B", total_amount=Decimal("1"),
            effective_date=date(2024, 1, 1), expiry_date=date(2024, 12, 31),
        )
        assert b.effective_date == date(2024, 1, 1)


class TestProjectBudgetUpdate:
    def test_all_none(self):
        b = ProjectBudgetUpdate()
        assert b.budget_name is None

    def test_partial(self):
        b = ProjectBudgetUpdate(budget_name="修改预算", total_amount=Decimal("200000"))
        assert b.total_amount == Decimal("200000")


class TestProjectBudgetApproveRequest:
    def test_approved(self):
        r = ProjectBudgetApproveRequest(approved=True, approval_note="同意")
        assert r.approved is True

    def test_rejected(self):
        r = ProjectBudgetApproveRequest(approved=False, approval_note="金额过高")
        assert r.approved is False

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProjectBudgetApproveRequest()


class TestProjectCostAllocationRuleCreate:
    def test_valid(self):
        r = ProjectCostAllocationRuleCreate(
            rule_name="按机台数分摊",
            rule_type="PROPORTION",
            allocation_basis="MACHINE_COUNT",
        )
        assert r.cost_type is None
        assert r.project_ids is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProjectCostAllocationRuleCreate()


class TestProjectCostAllocationRequest:
    def test_valid(self):
        r = ProjectCostAllocationRequest(cost_id=1)
        assert r.rule_id is None
        assert r.allocation_targets is None

    def test_with_targets(self):
        r = ProjectCostAllocationRequest(
            cost_id=1,
            allocation_targets=[{"machine_id": 1, "amount": 1000}],
        )
        assert len(r.allocation_targets) == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProjectCostAllocationRequest()
