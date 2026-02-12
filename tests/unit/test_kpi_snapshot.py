# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from app.services.strategy.kpi_service.snapshot import _get_current_period, _calculate_trend, create_kpi_snapshot


class TestGetCurrentPeriod:
    def test_daily(self):
        result = _get_current_period("DAILY")
        assert len(result) == 10  # YYYY-MM-DD

    def test_weekly(self):
        result = _get_current_period("WEEKLY")
        assert "-W" in result

    def test_monthly(self):
        result = _get_current_period("MONTHLY")
        assert len(result) == 7  # YYYY-MM

    def test_quarterly(self):
        result = _get_current_period("QUARTERLY")
        assert "-Q" in result

    def test_yearly(self):
        result = _get_current_period("YEARLY")
        assert len(result) == 4


class TestCalculateTrend:
    def test_insufficient_history(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        assert _calculate_trend(db, 1) is None

    def test_trend_up(self):
        db = MagicMock()
        h1 = MagicMock(); h1.value = 100
        h2 = MagicMock(); h2.value = 80
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        assert _calculate_trend(db, 1) == "UP"

    def test_trend_down(self):
        db = MagicMock()
        h1 = MagicMock(); h1.value = 60
        h2 = MagicMock(); h2.value = 80
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        assert _calculate_trend(db, 1) == "DOWN"

    def test_trend_stable(self):
        db = MagicMock()
        h1 = MagicMock(); h1.value = 80
        h2 = MagicMock(); h2.value = 80
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        assert _calculate_trend(db, 1) == "STABLE"


class TestCreateKpiSnapshot:
    @patch("app.services.strategy.kpi_service.snapshot.get_kpi")
    def test_kpi_not_found(self, mock_get):
        mock_get.return_value = None
        db = MagicMock()
        assert create_kpi_snapshot(db, 999, "MANUAL") is None
