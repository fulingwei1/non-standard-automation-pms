# -*- coding: utf-8 -*-
"""Tests for overtime_calculation_service.py"""
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

from app.services.overtime_calculation_service import OvertimeCalculationService


class TestCalculateOvertimePay:
    def setup_method(self):
        self.db = MagicMock()
        self.service = OvertimeCalculationService(self.db)

    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_normal_no_pay(self, mock_rate):
        result = self.service.calculate_overtime_pay(1, date(2025, 1, 6), Decimal("8"), "NORMAL")
        assert result == Decimal("0")

    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_overtime_pay(self, mock_rate):
        result = self.service.calculate_overtime_pay(1, date(2025, 1, 6), Decimal("2"), "OVERTIME")
        assert result == Decimal("2") * Decimal("100") * Decimal("0.5")

    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_weekend_pay(self, mock_rate):
        result = self.service.calculate_overtime_pay(1, date(2025, 1, 4), Decimal("8"), "WEEKEND")
        assert result == Decimal("8") * Decimal("100") * Decimal("1.0")

    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_holiday_pay(self, mock_rate):
        result = self.service.calculate_overtime_pay(1, date(2025, 1, 1), Decimal("8"), "HOLIDAY")
        assert result == Decimal("8") * Decimal("100") * Decimal("2.0")

    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_unknown_type(self, mock_rate):
        result = self.service.calculate_overtime_pay(1, date(2025, 1, 1), Decimal("8"), "UNKNOWN")
        assert result == Decimal("0")


class TestCalculateUserMonthlyOvertimePay:
    def setup_method(self):
        self.db = MagicMock()
        self.service = OvertimeCalculationService(self.db)

    @patch("app.services.overtime_calculation_service.get_month_range_by_ym", return_value=(date(2025, 1, 1), date(2025, 1, 31)))
    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_user_not_found(self, mock_rate, mock_range):
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.calculate_user_monthly_overtime_pay(999, 2025, 1)
        assert result == {'error': '用户不存在'}

    @patch("app.services.overtime_calculation_service.get_month_range_by_ym", return_value=(date(2025, 1, 1), date(2025, 1, 31)))
    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_basic_calculation(self, mock_rate, mock_range):
        user = MagicMock(id=1, real_name="张三", username="zhangsan")
        ts = MagicMock(user_id=1, hours=8, overtime_type="OVERTIME",
                       work_date=date(2025, 1, 6), work_content="加班",
                       department_id=1, department_name="技术部")
        self.db.query.return_value.filter.return_value.all.return_value = [ts]
        self.db.query.return_value.filter.return_value.first.return_value = user
        result = self.service.calculate_user_monthly_overtime_pay(1, 2025, 1)
        assert result['user_id'] == 1
        assert result['overtime_hours'] == 8.0


class TestGetOvertimeStatistics:
    def setup_method(self):
        self.db = MagicMock()
        self.service = OvertimeCalculationService(self.db)

    @patch("app.services.overtime_calculation_service.get_month_range_by_ym", return_value=(date(2025, 1, 1), date(2025, 1, 31)))
    @patch("app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate", return_value=Decimal("100"))
    def test_empty(self, mock_rate, mock_range):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.service.get_overtime_statistics(2025, 1)
        assert result['total_overtime_hours'] == 0
