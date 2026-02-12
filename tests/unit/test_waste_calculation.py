# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from decimal import Decimal
from app.services.resource_waste_analysis.waste_calculation import WasteCalculationMixin


class FakeService(WasteCalculationMixin):
    def __init__(self, db):
        self.db = db
        self.hourly_rate = Decimal("200")


class TestWasteCalculationMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.service = FakeService(self.db)

    def test_no_projects(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 3, 1))
        assert result["total_leads"] == 0
        assert result["win_rate"] == 0
        assert result["waste_rate"] == 0

    @patch("app.services.resource_waste_analysis.waste_calculation.WorkLog")
    @patch("app.services.resource_waste_analysis.waste_calculation.LeadOutcomeEnum")
    def test_with_projects(self, mock_enum, mock_worklog):
        mock_enum.WON.value = "WON"
        mock_enum.LOST.value = "LOST"
        mock_enum.ABANDONED.value = "ABANDONED"
        mock_enum.PENDING.value = "PENDING"
        mock_enum.ON_HOLD.value = "ON_HOLD"
        mock_worklog.project_id = MagicMock()
        mock_worklog.work_hours = MagicMock()

        p1 = MagicMock(); p1.id = 1; p1.outcome = "WON"; p1.loss_reason = None
        p2 = MagicMock(); p2.id = 2; p2.outcome = "LOST"; p2.loss_reason = "PRICE"
        self.db.query.return_value.filter.return_value.all.return_value = [p1, p2]
        self.db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (1, 10.0), (2, 5.0)
        ]
        result = self.service.calculate_waste_by_period(date(2024, 1, 1), date(2024, 3, 1))
        assert result["total_leads"] == 2
        assert result["won_leads"] == 1
        assert result["lost_leads"] == 1
