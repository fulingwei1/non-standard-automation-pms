# -*- coding: utf-8 -*-
"""
第四十五批覆盖：resource_waste_analysis/waste_calculation.py
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.resource_waste_analysis.waste_calculation")

from app.services.resource_waste_analysis.waste_calculation import WasteCalculationMixin


class MockWasteService(WasteCalculationMixin):
    def __init__(self, db, hourly_rate=Decimal("100")):
        self.db = db
        self.hourly_rate = hourly_rate


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return MockWasteService(mock_db)


def _make_project(outcome="WON", loss_reason=None):
    p = MagicMock()
    p.id = 1
    p.outcome = outcome
    p.loss_reason = loss_reason
    return p


class TestWasteCalculationMixin:
    def test_no_projects_returns_zero_stats(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 1, 31))

        assert result["total_leads"] == 0
        assert result["won_leads"] == 0
        assert result["wasted_hours"] == 0.0
        assert result["wasted_cost"] == Decimal("0")
        assert result["waste_rate"] == 0

    def test_won_projects_counted_correctly(self, service, mock_db):
        from app.models.enums import LeadOutcomeEnum
        mock_pending = MagicMock()
        mock_pending.value = "PENDING"
        won_project = _make_project(outcome=LeadOutcomeEnum.WON.value)

        with patch.object(LeadOutcomeEnum, "PENDING", mock_pending, create=True), \
             patch("app.services.resource_waste_analysis.waste_calculation.WorkLog") as mock_wl:
            mock_wl.project_id = MagicMock()
            mock_wl.work_hours = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = [won_project]
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
            result = service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 1, 31))
        assert result["won_leads"] == 1
        assert result["lost_leads"] == 0

    def test_lost_projects_counted_correctly(self, service, mock_db):
        from app.models.enums import LeadOutcomeEnum
        mock_pending = MagicMock()
        mock_pending.value = "PENDING"
        lost_project = _make_project(outcome=LeadOutcomeEnum.LOST.value, loss_reason="PRICE_TOO_HIGH")

        with patch.object(LeadOutcomeEnum, "PENDING", mock_pending, create=True), \
             patch("app.services.resource_waste_analysis.waste_calculation.WorkLog") as mock_wl:
            mock_wl.project_id = MagicMock()
            mock_wl.work_hours = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = [lost_project]
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
            result = service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 1, 31))
        assert result["lost_leads"] == 1
        assert "PRICE_TOO_HIGH" in result["loss_reasons"]

    def test_win_rate_with_mixed_projects(self, service, mock_db):
        from app.models.enums import LeadOutcomeEnum
        mock_pending = MagicMock()
        mock_pending.value = "PENDING"
        projects = [
            _make_project(outcome=LeadOutcomeEnum.WON.value),
            _make_project(outcome=LeadOutcomeEnum.WON.value),
            _make_project(outcome=LeadOutcomeEnum.LOST.value),
        ]

        with patch.object(LeadOutcomeEnum, "PENDING", mock_pending, create=True), \
             patch("app.services.resource_waste_analysis.waste_calculation.WorkLog") as mock_wl:
            mock_wl.project_id = MagicMock()
            mock_wl.work_hours = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = projects
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
            result = service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 1, 31))
        assert abs(result["win_rate"] - round(2/3, 3)) < 0.001

    def test_wasted_cost_calculated_with_hourly_rate(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 1, 31))
        # 0 wasted hours * 100 hourly rate = 0
        assert result["wasted_cost"] == Decimal("0")

    def test_period_string_format(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.calculate_waste_by_period(date(2024, 3, 1), date(2024, 3, 31))
        assert "2024-03-01" in result["period"]
        assert "2024-03-31" in result["period"]
