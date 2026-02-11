# -*- coding: utf-8 -*-
"""Tests for cost_review_service.py"""
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date
import pytest

from app.services.cost_review_service import CostReviewService


class TestGenerateCostReviewReport:
    def setup_method(self):
        self.db = MagicMock()

    def test_project_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            CostReviewService.generate_cost_review_report(self.db, 999, 1)

    def test_project_not_completed(self):
        project = MagicMock(stage="S3", status="ST10")
        self.db.query.return_value.filter.return_value.first.return_value = project
        with pytest.raises(ValueError, match="未结项"):
            CostReviewService.generate_cost_review_report(self.db, 1, 1)

    def test_existing_review(self):
        project = MagicMock(stage="S9", status="ST30")
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.side_effect = [project, existing]
        with pytest.raises(ValueError, match="已存在"):
            CostReviewService.generate_cost_review_report(self.db, 1, 1)

    @patch.object(CostReviewService, '_generate_review_no', return_value="REV-250101-001")
    @patch.object(CostReviewService, '_generate_cost_summary', return_value="总结")
    def test_successful_generation(self, mock_summary, mock_no):
        project = MagicMock(
            id=1, stage="S9", status="ST30", project_code="P001",
            planned_start_date=date(2024, 1, 1), planned_end_date=date(2024, 6, 30),
            actual_start_date=date(2024, 1, 15), actual_end_date=date(2024, 7, 15),
            actual_cost=Decimal("100000"), budget_amount=Decimal("90000")
        )
        budget = MagicMock(total_amount=Decimal("90000"))
        reviewer = MagicMock(real_name="张三", username="zhangsan")

        self.db.query.return_value.filter.return_value.first.side_effect = [
            project,  # project
            None,     # no existing review
            budget,   # budget
            reviewer, # reviewer (User query)
        ]
        self.db.query.return_value.filter.return_value.all.return_value = []  # costs
        self.db.query.return_value.filter.return_value.count.return_value = 2  # ecn_count

        result = CostReviewService.generate_cost_review_report(self.db, 1, 1)
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()


class TestGenerateReviewNo:
    def test_first_review(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = CostReviewService._generate_review_no(db)
        assert result.startswith("REV-")
        assert result.endswith("-001")

    def test_increment(self):
        db = MagicMock()
        latest = MagicMock(review_no="REV-250101-005")
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = latest
        result = CostReviewService._generate_review_no(db)
        assert result.endswith("-006")


class TestGenerateCostSummary:
    def test_over_budget(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("120000"), Decimal("20000"),
            {"人工": Decimal("80000"), "物料": Decimal("40000")}, {}, 3
        )
        assert "超出预算" in result
        assert "工程变更" in result

    def test_under_budget(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("90000"), Decimal("-10000"),
            {}, {}, 0
        )
        assert "成本控制良好" in result

    def test_on_budget(self):
        result = CostReviewService._generate_cost_summary(
            Decimal("100000"), Decimal("101000"), Decimal("1000"),
            {}, {}, 0
        )
        assert "基本一致" in result
