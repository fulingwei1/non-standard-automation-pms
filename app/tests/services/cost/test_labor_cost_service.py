# -*- coding: utf-8 -*-
"""
工时成本服务测试

测试 LaborCostService 的核心功能：
- 用户时薪获取
- 项目工时成本计算
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app.models.project import Project
from app.services.cost.labor_cost_service import LaborCostService


class TestLaborCostService:
    """工时成本服务测试类"""

    def test_service_initialization(self, db_session):
        """测试服务初始化"""
        service = LaborCostService(db_session)
        
        assert service.db is not None
        assert service.DEFAULT_HOURLY_RATE == Decimal("100")

    @patch('app.services.hourly_rate_service.HourlyRateService.get_user_hourly_rate')
    def test_get_user_hourly_rate(self, mock_get_rate, db_session, test_user):
        """测试获取用户时薪"""
        mock_get_rate.return_value = Decimal("150")
        
        rate = LaborCostService.get_user_hourly_rate(db_session, test_user.id)
        
        assert rate == Decimal("150")
        mock_get_rate.assert_called_once()

    @patch('app.services.hourly_rate_service.HourlyRateService.get_user_hourly_rate')
    def test_get_user_hourly_rate_with_date(self, mock_get_rate, db_session, test_user):
        """测试带日期的获取用户时薪"""
        test_date = date(2025, 1, 15)
        mock_get_rate.return_value = Decimal("200")
        
        rate = LaborCostService.get_user_hourly_rate(db_session, test_user.id, test_date)
        
        assert rate == Decimal("200")
        mock_get_rate.assert_called_once_with(db_session, test_user.id, test_date)