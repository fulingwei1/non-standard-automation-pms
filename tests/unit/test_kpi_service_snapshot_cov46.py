# -*- coding: utf-8 -*-
"""第四十六批 - KPI服务快照单元测试"""
import pytest
from datetime import date
from decimal import Decimal

pytest.importorskip("app.services.strategy.kpi_service.snapshot",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.kpi_service.snapshot import (
    _get_current_period,
    _calculate_trend,
    create_kpi_snapshot,
)


class TestGetCurrentPeriod:
    def test_daily_format(self):
        result = _get_current_period("DAILY")
        today = date.today()
        assert result == today.strftime("%Y-%m-%d")

    def test_weekly_format(self):
        result = _get_current_period("WEEKLY")
        today = date.today()
        expected = f"{today.year}-W{today.isocalendar()[1]:02d}"
        assert result == expected

    def test_monthly_format(self):
        result = _get_current_period("MONTHLY")
        today = date.today()
        assert result == today.strftime("%Y-%m")

    def test_quarterly_format(self):
        result = _get_current_period("QUARTERLY")
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        assert result == f"{today.year}-Q{quarter}"

    def test_annual_format(self):
        result = _get_current_period("ANNUAL")
        assert result == str(date.today().year)


class TestCalculateTrend:
    def test_returns_none_when_less_than_two_records(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = _calculate_trend(db, 1)
        assert result is None

    def test_returns_up_when_increased(self):
        db = MagicMock()
        h1 = MagicMock()
        h1.value = Decimal("80")
        h2 = MagicMock()
        h2.value = Decimal("60")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        result = _calculate_trend(db, 1)
        assert result == "UP"

    def test_returns_down_when_decreased(self):
        db = MagicMock()
        h1 = MagicMock()
        h1.value = Decimal("40")
        h2 = MagicMock()
        h2.value = Decimal("60")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        result = _calculate_trend(db, 1)
        assert result == "DOWN"

    def test_returns_stable_when_equal(self):
        db = MagicMock()
        h1 = MagicMock()
        h1.value = Decimal("50")
        h2 = MagicMock()
        h2.value = Decimal("50")
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        result = _calculate_trend(db, 1)
        assert result == "STABLE"


class TestCreateKpiSnapshot:
    def test_returns_none_when_kpi_not_found(self):
        db = MagicMock()
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=None):
            result = create_kpi_snapshot(db, 99, "MANUAL")
        assert result is None

    def test_creates_and_returns_history(self):
        db = MagicMock()
        kpi = MagicMock()
        kpi.frequency = "MONTHLY"
        kpi.current_value = Decimal("75")
        kpi.target_value = Decimal("100")

        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi), \
             patch("app.services.strategy.kpi_service.snapshot.calculate_kpi_completion_rate",
                   return_value=75.0), \
             patch("app.services.strategy.kpi_service.snapshot.get_health_level",
                   return_value="H2"):
            result = create_kpi_snapshot(db, 1, "MANUAL", recorded_by=5, remark="test")

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
