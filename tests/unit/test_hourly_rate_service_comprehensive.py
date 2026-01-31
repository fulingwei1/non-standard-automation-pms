# -*- coding: utf-8 -*-
"""
HourlyRateService 综合单元测试

测试覆盖:
- get_user_hourly_rate: 获取用户时薪（用户>角色>部门>默认）
- get_users_hourly_rates: 批量获取多用户时薪
- get_hourly_rate_history: 获取时薪配置历史
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetUserHourlyRate:
    """测试 get_user_hourly_rate 方法"""

    def test_returns_default_when_user_not_found(self):
        """测试用户不存在时返回默认值"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = HourlyRateService.get_user_hourly_rate(mock_db, 999)

        assert result == Decimal("100")

    def test_returns_user_config_rate(self):
        """测试返回用户配置时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        mock_user_config = MagicMock()
        mock_user_config.hourly_rate = Decimal("150")

        # Setup query chain
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # User query
                query_mock.filter.return_value.first.return_value = mock_user
            else:
                # User config query
                query_mock.filter.return_value.order_by.return_value.first.return_value = mock_user_config
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = HourlyRateService.get_user_hourly_rate(mock_db, 1)

        assert result == Decimal("150")

    def test_returns_role_config_rate(self):
        """测试返回角色配置时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.department = None

        mock_user_role = MagicMock()
        mock_user_role.role_id = 10

        mock_role_config = MagicMock()
        mock_role_config.hourly_rate = Decimal("120")

        # Setup query chain
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # User query
                query_mock.filter.return_value.first.return_value = mock_user
            elif call_count[0] == 2:
                # User config query - returns None
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif call_count[0] == 3:
                # UserRole query
                query_mock.filter.return_value.all.return_value = [mock_user_role]
            elif call_count[0] == 4:
                # Role config query
                query_mock.filter.return_value.order_by.return_value.first.return_value = mock_role_config
            else:
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = HourlyRateService.get_user_hourly_rate(mock_db, 1)

        assert result == Decimal("120")

    def test_returns_dept_config_rate(self):
        """测试返回部门配置时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.department = "研发部"

        mock_dept = MagicMock()
        mock_dept.id = 5

        mock_dept_config = MagicMock()
        mock_dept_config.hourly_rate = Decimal("110")

        # Setup complex query chain
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                # User query
                query_mock.filter.return_value.first.return_value = mock_user
            elif call_count[0] == 2:
                # User config query - returns None
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif call_count[0] == 3:
                # UserRole query - returns empty
                query_mock.filter.return_value.all.return_value = []
            elif call_count[0] == 4:
                # Department query
                query_mock.filter.return_value.first.return_value = mock_dept
            elif call_count[0] == 5:
                # Dept config query
                query_mock.filter.return_value.order_by.return_value.first.return_value = mock_dept_config
            else:
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = HourlyRateService.get_user_hourly_rate(mock_db, 1)

        assert result == Decimal("110")

    def test_returns_default_config_rate(self):
        """测试返回默认配置时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.department = None

        mock_default_config = MagicMock()
        mock_default_config.hourly_rate = Decimal("80")

        # All configs return None except default
        call_count = [0]
        def query_side_effect(model):
            query_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                query_mock.filter.return_value.first.return_value = mock_user
            elif call_count[0] == 2:
                # User config - None
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            elif call_count[0] == 3:
                # UserRole - empty
                query_mock.filter.return_value.all.return_value = []
            elif call_count[0] == 4:
                # Default config
                query_mock.filter.return_value.order_by.return_value.first.return_value = mock_default_config
            else:
                query_mock.filter.return_value.order_by.return_value.first.return_value = None
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = HourlyRateService.get_user_hourly_rate(mock_db, 1)

        assert result == Decimal("80")

    def test_uses_work_date_for_filtering(self):
        """测试使用工作日期筛选"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        mock_config = MagicMock()
        mock_config.hourly_rate = Decimal("130")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_config

        work_date = date.today() - timedelta(days=30)
        result = HourlyRateService.get_user_hourly_rate(mock_db, 1, work_date)

        assert result == Decimal("130")


class TestGetUsersHourlyRates:
    """测试 get_users_hourly_rates 方法"""

    def test_returns_rates_for_multiple_users(self):
        """测试返回多用户时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        mock_config = MagicMock()
        mock_config.hourly_rate = Decimal("100")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_config

        result = HourlyRateService.get_users_hourly_rates(mock_db, [1, 2, 3])

        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_returns_empty_dict_for_empty_list(self):
        """测试空列表返回空字典"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()

        result = HourlyRateService.get_users_hourly_rates(mock_db, [])

        assert result == {}

    def test_uses_work_date_parameter(self):
        """测试使用工作日期参数"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_user = MagicMock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        work_date = date(2026, 1, 15)
        result = HourlyRateService.get_users_hourly_rates(mock_db, [1], work_date)

        assert 1 in result


class TestGetHourlyRateHistory:
    """测试 get_hourly_rate_history 方法"""

    def test_returns_all_history(self):
        """测试返回所有历史"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()

        mock_config1 = MagicMock()
        mock_config1.id = 1
        mock_config1.config_type = "USER"
        mock_config1.user_id = 10
        mock_config1.role_id = None
        mock_config1.dept_id = None
        mock_config1.hourly_rate = Decimal("150")
        mock_config1.effective_date = date(2026, 1, 1)
        mock_config1.expiry_date = None
        mock_config1.is_active = True
        mock_config1.remark = "个人配置"
        mock_config1.created_at = date(2026, 1, 1)
        mock_config1.updated_at = date(2026, 1, 1)

        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_config1]

        result = HourlyRateService.get_hourly_rate_history(mock_db)

        assert len(result) == 1
        assert result[0]["config_type"] == "USER"
        assert result[0]["hourly_rate"] == Decimal("150")

    def test_filters_by_user_id(self):
        """测试按用户ID筛选"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = HourlyRateService.get_hourly_rate_history(mock_db, user_id=10)

        assert result == []

    def test_filters_by_role_id(self):
        """测试按角色ID筛选"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = HourlyRateService.get_hourly_rate_history(mock_db, role_id=5)

        assert result == []

    def test_filters_by_dept_id(self):
        """测试按部门ID筛选"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = HourlyRateService.get_hourly_rate_history(mock_db, dept_id=3)

        assert result == []

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.hourly_rate_service import HourlyRateService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = HourlyRateService.get_hourly_rate_history(
            mock_db,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        assert result == []


class TestDefaultHourlyRate:
    """测试默认时薪常量"""

    def test_default_rate_is_100(self):
        """测试默认时薪为100"""
        from app.services.hourly_rate_service import HourlyRateService

        assert HourlyRateService.DEFAULT_HOURLY_RATE == Decimal("100")
