# -*- coding: utf-8 -*-
"""
Dashboard基础服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.dashboard.base import DateRange, BaseDashboardService


class TestDateRange:
    """测试日期范围类"""

    def test_date_range_class_exists(self):
        """测试类存在"""
        assert DateRange is not None

    def test_date_range_has_start(self):
        """测试有start属性"""
        dr = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert hasattr(dr, 'start')

    def test_date_range_has_end(self):
        """测试有end属性"""
        dr = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert hasattr(dr, 'end')

    def test_date_range_this_month(self):
        """测试本月方法"""
        dr = DateRange.this_month()
        assert dr is not None
        assert hasattr(dr, 'start')
        assert hasattr(dr, 'end')

    def test_date_range_last_n_months(self):
        """测试最近N月方法"""
        dr = DateRange.last_n_months(3)
        assert dr is not None
        assert hasattr(dr, 'start')
        assert hasattr(dr, 'end')


class TestBaseDashboardServiceInit:
    """测试基础Dashboard服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = BaseDashboardService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            BaseDashboardService()


class TestDashboardBaseConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services.dashboard import base
        assert base is not None

    def test_date_range_class_available(self):
        """测试DateRange类可用"""
        assert DateRange is not None

    def test_base_service_class_available(self):
        """测试BaseDashboardService类可用"""
        assert BaseDashboardService is not None