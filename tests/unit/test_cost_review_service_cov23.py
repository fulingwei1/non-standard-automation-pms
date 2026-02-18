# -*- coding: utf-8 -*-
"""第二十三批：cost_review_service 单元测试"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.cost_review_service")

from app.services.cost_review_service import CostReviewService


def _make_db():
    return MagicMock()


def _mock_project(pid=1, stage="S9", status="ST30", project_code="P001",
                  budget_amount=Decimal("100000"), actual_cost=None,
                  planned_start=None, planned_end=None, actual_start=None, actual_end=None):
    p = MagicMock()
    p.id = pid
    p.stage = stage
    p.status = status
    p.project_code = project_code
    p.budget_amount = budget_amount
    p.actual_cost = actual_cost
    p.planned_start_date = planned_start or date(2024, 1, 1)
    p.planned_end_date = planned_end or date(2024, 6, 30)
    p.actual_start_date = actual_start or date(2024, 1, 5)
    p.actual_end_date = actual_end or date(2024, 7, 10)
    p.plan_duration = None
    return p


class TestGenerateCostReviewReport:
    def test_project_not_found_raises(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            CostReviewService.generate_cost_review_report(db, 999, 1)

    def test_project_not_closed_raises(self):
        db = _make_db()
        proj = _mock_project(stage="S5", status="IN_PROGRESS")
        db.query.return_value.filter.return_value.first.return_value = proj
        with pytest.raises(ValueError, match="未结项"):
            CostReviewService.generate_cost_review_report(db, 1, 1)

    def test_existing_review_raises(self):
        db = _make_db()
        proj = _mock_project()
        existing = MagicMock()

        call_count = [0]
        def side_effect(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = proj
            elif call_count[0] == 2:
                q.filter.return_value.first.return_value = existing
            else:
                q.filter.return_value.first.return_value = None
                q.filter.return_value.all.return_value = []
                q.filter.return_value.count.return_value = 0
            return q

        db.query.side_effect = side_effect
        with pytest.raises(ValueError, match="已存在"):
            CostReviewService.generate_cost_review_report(db, 1, 1)


class TestGenerateReviewNo:
    def test_format_without_previous(self):
        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = CostReviewService._generate_review_no(db)
        assert result.startswith("REV-")
        parts = result.split("-")
        assert len(parts) == 3
        assert parts[2] == "001"

    def test_increments_sequence(self):
        db = _make_db()
        prev = MagicMock()
        prev.review_no = "REV-260101-005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = prev
        result = CostReviewService._generate_review_no(db)
        assert result.endswith("-006")


class TestGenerateCostSummary:
    def test_overbudget_summary(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("115000"), Decimal("15000"),
            {"材料费": Decimal("60000")}, {}, 2
        )
        assert "超支" in result

    def test_under_budget_summary(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("90000"), Decimal("-10000"),
            {}, {}, 0
        )
        assert "良好" in result or "低于预算" in result

    def test_within_budget_summary(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("101000"), Decimal("1000"),
            {}, {}, 0
        )
        assert "基本一致" in result

    def test_ecn_count_included(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("102000"), Decimal("2000"),
            {}, {}, 3
        )
        assert "3" in result
