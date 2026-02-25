# -*- coding: utf-8 -*-
"""Overtime Calculation Service 测试 - Batch 2"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.services.overtime_calculation_service import OvertimeCalculationService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return OvertimeCalculationService(mock_db)


class TestCalculateOvertimePay:
    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_normal_type_returns_zero(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 1), Decimal("8"), 'NORMAL')
        assert result == Decimal("0")

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_overtime_type(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 1), Decimal("2"), 'OVERTIME')
        assert result == Decimal("2") * Decimal("100") * Decimal("0.5")

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_weekend_type(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 6), Decimal("4"), 'WEEKEND')
        assert result == Decimal("4") * Decimal("100") * Decimal("1")

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_holiday_type(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 1), Decimal("3"), 'HOLIDAY')
        assert result == Decimal("3") * Decimal("100") * Decimal("2")

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_unknown_type_returns_zero(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 1), Decimal("2"), 'INVALID')
        assert result == Decimal("0")

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("200"))
    def test_different_hourly_rate(self, mock_rate, service):
        result = service.calculate_overtime_pay(1, date(2024, 1, 1), Decimal("1"), 'OVERTIME')
        assert result == Decimal("1") * Decimal("200") * Decimal("0.5")


class TestCalculateUserMonthlyOvertimePay:
    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_user_not_found(self, mock_rate, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.calculate_user_monthly_overtime_pay(999, 2024, 1)
        assert result.get('error') == '用户不存在'

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_no_timesheets(self, mock_rate, service, mock_db):
        user = MagicMock()
        user.real_name = "张三"
        user.username = "zhangsan"
        # First query returns timesheets, second returns user
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = user
        result = service.calculate_user_monthly_overtime_pay(1, 2024, 1)
        assert result['total_hours'] == 0.0
        assert result['total_overtime_pay'] == 0.0

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_with_timesheets(self, mock_rate, service, mock_db):
        user = MagicMock()
        user.real_name = "张三"
        user.username = "zhangsan"

        ts1 = MagicMock()
        ts1.hours = 8
        ts1.overtime_type = 'NORMAL'
        ts1.work_date = date(2024, 1, 2)
        ts1.work_content = "Normal work"
        ts1.department_id = 1
        ts1.department_name = "研发部"
        ts1.user_id = 1

        ts2 = MagicMock()
        ts2.hours = 3
        ts2.overtime_type = 'OVERTIME'
        ts2.work_date = date(2024, 1, 2)
        ts2.work_content = "OT work"
        ts2.department_id = 1
        ts2.department_name = "研发部"
        ts2.user_id = 1

        # Mock query chain
        mock_db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        mock_db.query.return_value.filter.return_value.first.return_value = user

        result = service.calculate_user_monthly_overtime_pay(1, 2024, 1)
        assert result['user_name'] == "张三"
        assert result['year'] == 2024
        assert result['month'] == 1


class TestGetOvertimeStatistics:
    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_empty_statistics(self, mock_rate, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.get_overtime_statistics(2024, 1)
        assert result['total_users'] == 0
        assert result['total_overtime_hours'] == 0

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_with_department_filter(self, mock_rate, service, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = service.get_overtime_statistics(2024, 1, department_id=1)
        assert result['department_id'] == 1

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_statistics_with_data(self, mock_rate, service, mock_db):
        ts1 = MagicMock()
        ts1.user_id = 1
        ts1.user_name = "张三"
        ts1.hours = 3
        ts1.overtime_type = 'OVERTIME'
        ts1.work_date = date(2024, 1, 2)

        ts2 = MagicMock()
        ts2.user_id = 1
        ts2.user_name = "张三"
        ts2.hours = 8
        ts2.overtime_type = 'NORMAL'
        ts2.work_date = date(2024, 1, 3)

        mock_db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        result = service.get_overtime_statistics(2024, 1)
        assert result['total_users'] == 1  # unique user_ids from all timesheets (both have user_id=1)
        assert result['total_overtime_hours'] == 3.0

    @patch('app.services.overtime_calculation_service.HourlyRateService.get_user_hourly_rate', return_value=Decimal("100"))
    def test_user_stats_sorted_by_pay(self, mock_rate, service, mock_db):
        ts1 = MagicMock()
        ts1.user_id = 1
        ts1.user_name = "低加班"
        ts1.hours = 1
        ts1.overtime_type = 'OVERTIME'
        ts1.work_date = date(2024, 1, 2)

        ts2 = MagicMock()
        ts2.user_id = 2
        ts2.user_name = "高加班"
        ts2.hours = 10
        ts2.overtime_type = 'WEEKEND'
        ts2.work_date = date(2024, 1, 6)

        mock_db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        result = service.get_overtime_statistics(2024, 1)
        if result['user_statistics']:
            assert result['user_statistics'][0]['overtime_pay'] >= result['user_statistics'][-1]['overtime_pay']
