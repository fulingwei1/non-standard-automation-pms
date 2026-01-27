# -*- coding: utf-8 -*-
"""
时薪配置服务单元测试

测试 HourlyRateService 的核心功能:
- 获取用户时薪（按优先级）
- 批量获取用户时薪
- 获取时薪配置历史
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.hourly_rate_service import HourlyRateService


class TestHourlyRateService:
    """时薪配置服务测试"""

    def test_default_hourly_rate_constant(self):
        """测试默认时薪常量"""
        assert HourlyRateService.DEFAULT_HOURLY_RATE == Decimal("100")


class TestGetUserHourlyRate:
    """获取用户时薪测试"""

    def test_get_hourly_rate_user_not_found(self, db_session: Session):
        """测试用户不存在时返回默认时薪"""
        rate = HourlyRateService.get_user_hourly_rate(db_session, user_id=99999)
        assert rate == HourlyRateService.DEFAULT_HOURLY_RATE

    def test_get_hourly_rate_valid_user(self, db_session: Session, test_user):
        """测试获取有效用户的时薪"""
        rate = HourlyRateService.get_user_hourly_rate(db_session, user_id=test_user.id)
        assert isinstance(rate, Decimal)
        assert rate > 0

    def test_get_hourly_rate_with_work_date(self, db_session: Session, test_user):
        """测试指定工作日期获取时薪"""
        work_date = date.today() - timedelta(days=30)
        rate = HourlyRateService.get_user_hourly_rate(
        db_session, user_id=test_user.id, work_date=work_date
        )
        assert isinstance(rate, Decimal)

    def test_get_hourly_rate_future_date(self, db_session: Session, test_user):
        """测试未来日期获取时薪"""
        future_date = date.today() + timedelta(days=365)
        rate = HourlyRateService.get_user_hourly_rate(
        db_session, user_id=test_user.id, work_date=future_date
        )
        assert isinstance(rate, Decimal)

    def test_get_hourly_rate_default_work_date(self, db_session: Session, test_user):
        """测试不指定工作日期时使用今天"""
        rate = HourlyRateService.get_user_hourly_rate(db_session, user_id=test_user.id)
        assert isinstance(rate, Decimal)


class TestGetUsersHourlyRates:
    """批量获取用户时薪测试"""

    def test_get_rates_empty_list(self, db_session: Session):
        """测试空用户列表"""
        rates = HourlyRateService.get_users_hourly_rates(db_session, user_ids=[])
        assert rates == {}

    def test_get_rates_single_user(self, db_session: Session, test_user):
        """测试单个用户"""
        rates = HourlyRateService.get_users_hourly_rates(
        db_session, user_ids=[test_user.id]
        )
        assert test_user.id in rates
        assert isinstance(rates[test_user.id], Decimal)

    def test_get_rates_multiple_users(self, db_session: Session, test_user, test_pm_user):
        """测试多个用户"""
        rates = HourlyRateService.get_users_hourly_rates(
        db_session, user_ids=[test_user.id, test_pm_user.id]
        )
        assert len(rates) == 2
        assert test_user.id in rates
        assert test_pm_user.id in rates

    def test_get_rates_with_invalid_user(self, db_session: Session, test_user):
        """测试包含无效用户ID"""
        rates = HourlyRateService.get_users_hourly_rates(
        db_session, user_ids=[test_user.id, 99999]
        )
        assert len(rates) == 2
        assert rates[99999] == HourlyRateService.DEFAULT_HOURLY_RATE

    def test_get_rates_with_work_date(self, db_session: Session, test_user):
        """测试指定工作日期批量获取"""
        work_date = date.today() - timedelta(days=30)
        rates = HourlyRateService.get_users_hourly_rates(
        db_session, user_ids=[test_user.id], work_date=work_date
        )
        assert test_user.id in rates


class TestGetHourlyRateHistory:
    """获取时薪配置历史测试"""

    def test_get_history_no_filters(self, db_session: Session):
        """测试无筛选条件获取历史"""
        history = HourlyRateService.get_hourly_rate_history(db_session)
        assert isinstance(history, list)

    def test_get_history_by_user(self, db_session: Session, test_user):
        """测试按用户筛选历史"""
        history = HourlyRateService.get_hourly_rate_history(
        db_session, user_id=test_user.id
        )
        assert isinstance(history, list)

    def test_get_history_by_role(self, db_session: Session):
        """测试按角色筛选历史"""
        history = HourlyRateService.get_hourly_rate_history(db_session, role_id=1)
        assert isinstance(history, list)

    def test_get_history_by_dept(self, db_session: Session):
        """测试按部门筛选历史"""
        history = HourlyRateService.get_hourly_rate_history(db_session, dept_id=1)
        assert isinstance(history, list)

    def test_get_history_by_date_range(self, db_session: Session):
        """测试按日期范围筛选历史"""
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        history = HourlyRateService.get_hourly_rate_history(
        db_session, start_date=start_date, end_date=end_date
        )
        assert isinstance(history, list)

    def test_get_history_structure(self, db_session: Session):
        """测试历史记录数据结构"""
        history = HourlyRateService.get_hourly_rate_history(db_session)
        for item in history:
            assert "id" in item
            assert "config_type" in item
            assert "hourly_rate" in item
            assert "is_active" in item


class TestHourlyRatePriority:
    """时薪配置优先级测试"""

    def test_priority_returns_decimal(self, db_session: Session, test_user):
        """测试优先级逻辑返回正确类型"""
        rate = HourlyRateService.get_user_hourly_rate(db_session, user_id=test_user.id)
        assert isinstance(rate, Decimal)

    def test_fallback_to_default(self, db_session: Session):
        """测试回退到默认值"""
        # 使用不存在的用户ID应该返回默认值
        rate = HourlyRateService.get_user_hourly_rate(db_session, user_id=99999)
        assert rate == HourlyRateService.DEFAULT_HOURLY_RATE
