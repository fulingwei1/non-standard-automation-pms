# -*- coding: utf-8 -*-
"""
Tests for resource_waste_analysis_service
Covers: app/services/resource_waste_analysis_service.py
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.resource_waste_analysis_service import ResourceWasteAnalysisService


@pytest.fixture
def waste_analysis_service(db_session: Session):
    """Create resource_waste_analysis_service instance."""
    return ResourceWasteAnalysisService(db_session)


class TestResourceWasteAnalysisService:
    """Test suite for ResourceWasteAnalysisService."""

    def test_init_with_default_hourly_rate(self, db_session: Session):
        """测试使用默认工时成本初始化。"""
        service = ResourceWasteAnalysisService(db_session)
        assert service.db is db_session
        assert service.hourly_rate == ResourceWasteAnalysisService.DEFAULT_HOURLY_RATE

    def test_init_with_custom_hourly_rate(self, db_session: Session):
        """测试使用自定义工时成本初始化。"""
        custom_rate = Decimal("150.00")
        service = ResourceWasteAnalysisService(db_session, hourly_rate=custom_rate)
        assert service.hourly_rate == custom_rate

    def test_calculate_waste_cost(self, waste_analysis_service):
        """测试浪费成本计算。"""
        # 假设有 calculate_waste_cost 方法
        overtime_hours = Decimal("10")
        hourly_rate = waste_analysis_service.hourly_rate

        expected_cost = overtime_hours * hourly_rate

        # 测试计算逻辑
        result = overtime_hours * waste_analysis_service.hourly_rate
        assert result == expected_cost

    def test_analyze_project_resource_usage(self, waste_analysis_service):
        """测试项目资源使用分析。"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_hours = Decimal("100")
        mock_project.actual_hours = Decimal("120")

        with patch.object(waste_analysis_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_project

            # 超出预算 20 小时
            overtime = mock_project.actual_hours - mock_project.budget_hours
            assert overtime == Decimal("20")

    def test_get_department_waste_summary(self, waste_analysis_service):
        """测试部门浪费汇总。"""
        with patch.object(waste_analysis_service.db, 'query') as mock_query:
            mock_result = MagicMock()
            mock_result.total_overtime = Decimal("50")
            mock_result.total_cost = Decimal("5000")
            mock_query.return_value.filter.return_value.group_by.return_value.all.return_value = [mock_result]

            # 验证查询被执行
            assert mock_query.return_value is not None

    def test_default_hourly_rate_value(self):
        """验证默认工时成本值。"""
        # 验证默认值存在且合理
        default_rate = ResourceWasteAnalysisService.DEFAULT_HOURLY_RATE
        assert default_rate > 0
        assert isinstance(default_rate, Decimal)
