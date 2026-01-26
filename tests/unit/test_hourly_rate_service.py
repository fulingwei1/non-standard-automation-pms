# -*- coding: utf-8 -*-
"""
HourlyRateService 单元测试
测试时薪配置服务的各项功能
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.hourly_rate import HourlyRateConfig
from app.models.organization import Department
from app.models.user import User, UserRole
from app.services.hourly_rate_service import HourlyRateService


class TestGetUserHourlyRate:
    """测试获取用户时薪"""

    def test_user_not_found_returns_default(self):
        """测试用户不存在时返回默认时薪"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=999)

        assert result == HourlyRateService.DEFAULT_HOURLY_RATE

    def test_user_has_personal_config(self):
        """测试用户有个人时薪配置"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = None

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.hourly_rate = Decimal("150")

        # 第一次查询返回用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        # 第二次查询返回用户配置
        query_config = MagicMock()
        query_config.filter.return_value.order_by.return_value.first.return_value = mock_config

        mock_db.query.side_effect = [query_user, query_config]

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1)

        assert result == Decimal("150")

    def test_user_has_role_config(self):
        """测试用户有角色时薪配置"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = None

        mock_user_role = Mock(spec=UserRole)
        mock_user_role.role_id = 10

        mock_role_config = Mock(spec=HourlyRateConfig)
        mock_role_config.hourly_rate = Decimal("120")

        # 查询用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        # 查询用户配置 - 返回None
        query_user_config = MagicMock()
        query_user_config.filter.return_value.order_by.return_value.first.return_value = None

        # 查询用户角色
        query_roles = MagicMock()
        query_roles.filter.return_value.all.return_value = [mock_user_role]

        # 查询角色配置
        query_role_config = MagicMock()
        query_role_config.filter.return_value.order_by.return_value.first.return_value = mock_role_config

        mock_db.query.side_effect = [query_user, query_user_config, query_roles, query_role_config]

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1)

        assert result == Decimal("120")

    def test_user_has_department_config(self):
        """测试用户有部门时薪配置"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = "技术部"

        mock_dept = Mock(spec=Department)
        mock_dept.id = 5

        mock_dept_config = Mock(spec=HourlyRateConfig)
        mock_dept_config.hourly_rate = Decimal("110")

        # 查询用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        # 查询用户配置 - 返回None
        query_user_config = MagicMock()
        query_user_config.filter.return_value.order_by.return_value.first.return_value = None

        # 查询用户角色 - 返回空
        query_roles = MagicMock()
        query_roles.filter.return_value.all.return_value = []

        # 查询部门
        query_dept = MagicMock()
        query_dept.filter.return_value.first.return_value = mock_dept

        # 查询部门配置
        query_dept_config = MagicMock()
        query_dept_config.filter.return_value.order_by.return_value.first.return_value = mock_dept_config

        mock_db.query.side_effect = [query_user, query_user_config, query_roles, query_dept, query_dept_config]

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1)

        assert result == Decimal("110")

    def test_user_uses_default_config(self):
        """测试使用默认时薪配置"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = None

        mock_default_config = Mock(spec=HourlyRateConfig)
        mock_default_config.hourly_rate = Decimal("80")

        # 查询用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        # 用户配置 - None
        query_user_config = MagicMock()
        query_user_config.filter.return_value.order_by.return_value.first.return_value = None

        # 角色 - 空
        query_roles = MagicMock()
        query_roles.filter.return_value.all.return_value = []

        # 默认配置
        query_default = MagicMock()
        query_default.filter.return_value.order_by.return_value.first.return_value = mock_default_config

        mock_db.query.side_effect = [query_user, query_user_config, query_roles, query_default]

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1)

        assert result == Decimal("80")

    def test_no_config_returns_hardcoded_default(self):
        """测试无任何配置时返回硬编码默认值"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = None

        # 所有查询都返回None或空
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_user
        query_mock.filter.return_value.order_by.return_value.first.return_value = None
        query_mock.filter.return_value.all.return_value = []
        mock_db.query.return_value = query_mock

        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1)

        assert result == HourlyRateService.DEFAULT_HOURLY_RATE
        assert result == Decimal("100")

    def test_with_specific_work_date(self):
        """测试指定工作日期获取时薪"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.department = None

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.hourly_rate = Decimal("200")

        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        query_config = MagicMock()
        query_config.filter.return_value.order_by.return_value.first.return_value = mock_config

        mock_db.query.side_effect = [query_user, query_config]

        work_date = date(2024, 6, 15)
        result = HourlyRateService.get_user_hourly_rate(mock_db, user_id=1, work_date=work_date)

        assert result == Decimal("200")


class TestGetUsersHourlyRates:
    """测试批量获取用户时薪"""

    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_batch_get_rates(self, mock_get_rate):
        """测试批量获取多个用户时薪"""
        mock_db = MagicMock(spec=Session)

        # 设置不同用户返回不同时薪
        mock_get_rate.side_effect = [
            Decimal("100"),
            Decimal("150"),
            Decimal("120")
        ]

        result = HourlyRateService.get_users_hourly_rates(
            mock_db,
            user_ids=[1, 2, 3]
        )

        assert len(result) == 3
        assert result[1] == Decimal("100")
        assert result[2] == Decimal("150")
        assert result[3] == Decimal("120")

    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_batch_get_rates_empty_list(self, mock_get_rate):
        """测试空用户列表"""
        mock_db = MagicMock(spec=Session)

        result = HourlyRateService.get_users_hourly_rates(
            mock_db,
            user_ids=[]
        )

        assert result == {}
        mock_get_rate.assert_not_called()

    @patch.object(HourlyRateService, 'get_user_hourly_rate')
    def test_batch_get_rates_with_work_date(self, mock_get_rate):
        """测试批量获取时指定工作日期"""
        mock_db = MagicMock(spec=Session)
        mock_get_rate.return_value = Decimal("100")

        work_date = date(2024, 6, 15)
        result = HourlyRateService.get_users_hourly_rates(
            mock_db,
            user_ids=[1, 2],
            work_date=work_date
        )

        # 验证传递了正确的工作日期
        assert mock_get_rate.call_count == 2
        mock_get_rate.assert_any_call(mock_db, 1, work_date)
        mock_get_rate.assert_any_call(mock_db, 2, work_date)


class TestGetHourlyRateHistory:
    """测试获取时薪配置历史"""

    def test_get_history_no_filters(self):
        """测试无筛选条件获取历史"""
        mock_db = MagicMock(spec=Session)

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.id = 1
        mock_config.config_type = "USER"
        mock_config.user_id = 1
        mock_config.role_id = None
        mock_config.dept_id = None
        mock_config.hourly_rate = Decimal("150")
        mock_config.effective_date = date(2024, 1, 1)
        mock_config.expiry_date = None
        mock_config.is_active = True
        mock_config.remark = "测试配置"
        mock_config.created_at = None
        mock_config.updated_at = None

        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_config]

        result = HourlyRateService.get_hourly_rate_history(mock_db)

        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['config_type'] == "USER"
        assert result[0]['hourly_rate'] == Decimal("150")

    def test_get_history_with_user_filter(self):
        """测试按用户筛选历史"""
        mock_db = MagicMock(spec=Session)

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.id = 1
        mock_config.config_type = "USER"
        mock_config.user_id = 5
        mock_config.role_id = None
        mock_config.dept_id = None
        mock_config.hourly_rate = Decimal("120")
        mock_config.effective_date = None
        mock_config.expiry_date = None
        mock_config.is_active = True
        mock_config.remark = None
        mock_config.created_at = None
        mock_config.updated_at = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_config]
        mock_db.query.return_value = query_mock

        result = HourlyRateService.get_hourly_rate_history(mock_db, user_id=5)

        assert len(result) == 1
        assert result[0]['user_id'] == 5

    def test_get_history_with_role_filter(self):
        """测试按角色筛选历史"""
        mock_db = MagicMock(spec=Session)

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.id = 2
        mock_config.config_type = "ROLE"
        mock_config.user_id = None
        mock_config.role_id = 10
        mock_config.dept_id = None
        mock_config.hourly_rate = Decimal("130")
        mock_config.effective_date = None
        mock_config.expiry_date = None
        mock_config.is_active = True
        mock_config.remark = None
        mock_config.created_at = None
        mock_config.updated_at = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_config]
        mock_db.query.return_value = query_mock

        result = HourlyRateService.get_hourly_rate_history(mock_db, role_id=10)

        assert len(result) == 1
        assert result[0]['role_id'] == 10

    def test_get_history_with_dept_filter(self):
        """测试按部门筛选历史"""
        mock_db = MagicMock(spec=Session)

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.id = 3
        mock_config.config_type = "DEPT"
        mock_config.user_id = None
        mock_config.role_id = None
        mock_config.dept_id = 5
        mock_config.hourly_rate = Decimal("110")
        mock_config.effective_date = None
        mock_config.expiry_date = None
        mock_config.is_active = True
        mock_config.remark = None
        mock_config.created_at = None
        mock_config.updated_at = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_config]
        mock_db.query.return_value = query_mock

        result = HourlyRateService.get_hourly_rate_history(mock_db, dept_id=5)

        assert len(result) == 1
        assert result[0]['dept_id'] == 5

    def test_get_history_with_date_range(self):
        """测试按日期范围筛选历史"""
        mock_db = MagicMock(spec=Session)

        mock_config = Mock(spec=HourlyRateConfig)
        mock_config.id = 4
        mock_config.config_type = "USER"
        mock_config.user_id = 1
        mock_config.role_id = None
        mock_config.dept_id = None
        mock_config.hourly_rate = Decimal("140")
        mock_config.effective_date = date(2024, 1, 1)
        mock_config.expiry_date = date(2024, 12, 31)
        mock_config.is_active = True
        mock_config.remark = None
        mock_config.created_at = None
        mock_config.updated_at = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_config]
        mock_db.query.return_value = query_mock

        result = HourlyRateService.get_hourly_rate_history(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        assert len(result) == 1

    def test_get_history_empty_result(self):
        """测试无历史记录"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        result = HourlyRateService.get_hourly_rate_history(mock_db)

        assert result == []


class TestDefaultHourlyRate:
    """测试默认时薪常量"""

    def test_default_rate_value(self):
        """测试默认时薪值"""
        assert HourlyRateService.DEFAULT_HOURLY_RATE == Decimal("100")

    def test_default_rate_is_decimal(self):
        """测试默认时薪是Decimal类型"""
        assert isinstance(HourlyRateService.DEFAULT_HOURLY_RATE, Decimal)
