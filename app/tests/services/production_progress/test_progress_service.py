# -*- coding: utf-8 -*-
"""
生产进度服务测试
目标覆盖率: 60%+
测试用例数: 6个
"""
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.services.production_progress_service import ProductionProgressService


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock()


@pytest.fixture
def progress_service(mock_db):
    """创建生产进度服务实例"""
    return ProductionProgressService(mock_db)


class TestProductionProgressService:
    """生产进度服务测试类"""

    def test_service_initialization(self, mock_db):
        """测试服务初始化"""
        service = ProductionProgressService(mock_db)
        assert service is not None
        assert service.db == mock_db


class TestDeviationCalculation:
    """进度偏差计算测试类"""

    def test_calculate_deviation_percentage_positive(self, progress_service):
        """测试偏差百分比计算-提前"""
        deviation = 10
        plan_progress = 50

        result = progress_service.calculate_deviation_percentage(deviation, plan_progress)
        assert isinstance(result, Decimal)

    def test_calculate_deviation_percentage_negative(self, progress_service):
        """测试偏差百分比计算-滞后"""
        deviation = -10
        plan_progress = 50

        result = progress_service.calculate_deviation_percentage(deviation, plan_progress)
        assert isinstance(result, Decimal)

    def test_calculate_deviation_percentage_zero_plan(self, progress_service):
        """测试偏差百分比计算-计划进度为0"""
        deviation = 10
        plan_progress = 0

        result = progress_service.calculate_deviation_percentage(deviation, plan_progress)
        assert result == Decimal("0")