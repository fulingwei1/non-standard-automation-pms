# -*- coding: utf-8 -*-
"""Hourly Rate Service 测试 - Batch 2"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, call
import pytest

from app.services.hourly_rate_service import HourlyRateService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = 1
    u.department = "研发部"
    return u


class TestGetUserHourlyRate:
    def test_user_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = HourlyRateService.get_user_hourly_rate(mock_db, 999)
        assert result == Decimal("100")

    def test_user_config_found(self, mock_db, mock_user):
        config = MagicMock()
        config.hourly_rate = Decimal("150")
        # first query: User, second: HourlyRateConfig
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = config
        result = HourlyRateService.get_user_hourly_rate(mock_db, 1, date(2024, 6, 1))
        assert result == Decimal("150")

    def test_default_work_date(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = HourlyRateService.get_user_hourly_rate(mock_db, 1)
        assert result == Decimal("100")

    def test_fallback_to_default_rate(self, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []  # no roles
        result = HourlyRateService.get_user_hourly_rate(mock_db, 1, date(2024, 6, 1))
        # Will eventually fall back to DEFAULT_HOURLY_RATE
        assert isinstance(result, Decimal)


class TestGetUsersHourlyRates:
    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_batch(self, mock_method, mock_db):
        mock_method.side_effect = [Decimal("100"), Decimal("200")]
        result = HourlyRateService.get_users_hourly_rates(mock_db, [1, 2])
        assert result == {1: Decimal("100"), 2: Decimal("200")}

    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_empty(self, mock_method, mock_db):
        result = HourlyRateService.get_users_hourly_rates(mock_db, [])
        assert result == {}

    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_with_date(self, mock_method, mock_db):
        mock_method.return_value = Decimal("150")
        result = HourlyRateService.get_users_hourly_rates(mock_db, [1], work_date=date(2024, 1, 1))
        mock_method.assert_called_with(mock_db, 1, date(2024, 1, 1))


class TestGetHourlyRateHistory:
    def test_empty_history(self, mock_db):
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        result = HourlyRateService.get_hourly_rate_history(mock_db)
        assert result == []

    def test_with_user_filter(self, mock_db):
        config = MagicMock()
        config.id = 1
        config.config_type = "USER"
        config.user_id = 1
        config.role_id = None
        config.dept_id = None
        config.hourly_rate = Decimal("120")
        config.effective_date = date(2024, 1, 1)
        config.expiry_date = None
        config.is_active = True
        config.remark = "个人配置"
        config.created_at = None
        config.updated_at = None

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [config]
        result = HourlyRateService.get_hourly_rate_history(mock_db, user_id=1)
        assert len(result) == 1
        assert result[0]["hourly_rate"] == Decimal("120")

    def test_with_date_filter(self, mock_db):
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = HourlyRateService.get_hourly_rate_history(
            mock_db, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        assert result == []

    def test_with_role_filter(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = HourlyRateService.get_hourly_rate_history(mock_db, role_id=1)
        assert result == []

    def test_with_dept_filter(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = HourlyRateService.get_hourly_rate_history(mock_db, dept_id=1)
        assert result == []

    def test_default_hourly_rate_constant(self):
        assert HourlyRateService.DEFAULT_HOURLY_RATE == Decimal("100")
