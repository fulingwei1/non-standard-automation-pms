# -*- coding: utf-8 -*-
"""
Tests for comparison_calculation_service service
Covers: app/services/comparison_calculation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 88 lines
Batch: 3
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.comparison_calculation_service import ComparisonCalculationService
from app.models.management_rhythm import ReportMetricDefinition


@pytest.fixture
def comparison_calculation_service(db_session: Session):
    """创建 ComparisonCalculationService 实例"""
    return ComparisonCalculationService(db_session)


@pytest.fixture
def test_metric_definition(db_session: Session):
    """创建测试指标定义"""
    metric = ReportMetricDefinition(
        metric_code="TEST_METRIC",
        metric_name="测试指标",
        category="TEST",
        data_source="test_table",
        calculation_type="COUNT",
        support_mom=True,
        support_yoy=True
    )
    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)
    return metric


class TestComparisonCalculationService:
    """Test suite for ComparisonCalculationService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = ComparisonCalculationService(db_session)
        assert service is not None
        assert service.db == db_session
        assert service.metric_service is not None

    def test_calculate_mom_comparison_success(self, comparison_calculation_service, test_metric_definition):
        """测试计算环比 - 成功场景"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 80, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_mom_comparison(
            metric_code="TEST_METRIC",
            year=2024,
            month=2
            )
            
            assert result is not None
            assert result['metric_code'] == "TEST_METRIC"
            assert result['current_value'] == 100
            assert result['previous_value'] == 80
            assert result['change'] == 20
            assert result['is_increase'] is True
            assert result['is_decrease'] is False

    def test_calculate_mom_comparison_january(self, comparison_calculation_service, test_metric_definition):
        """测试计算环比 - 1月（跨年）"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 90, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_mom_comparison(
            metric_code="TEST_METRIC",
            year=2024,
            month=1
            )
            
            assert result is not None
            assert result['previous_period'] == "2023-12"

    def test_calculate_mom_comparison_decrease(self, comparison_calculation_service, test_metric_definition):
        """测试计算环比 - 下降"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 80, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_mom_comparison(
            metric_code="TEST_METRIC",
            year=2024,
            month=2
            )
            
            assert result['change'] == -20
            assert result['is_increase'] is False
            assert result['is_decrease'] is True

    def test_calculate_mom_comparison_zero_previous(self, comparison_calculation_service, test_metric_definition):
        """测试计算环比 - 上月为0"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 0, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_mom_comparison(
            metric_code="TEST_METRIC",
            year=2024,
            month=2
            )
            
            assert result['change_rate'] == 100.0

    def test_calculate_yoy_comparison_success(self, comparison_calculation_service, test_metric_definition):
        """测试计算同比 - 成功场景"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 150, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 120, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_yoy_comparison(
            metric_code="TEST_METRIC",
            year=2024,
            month=2
            )
            
            assert result is not None
            assert result['current_period'] == "2024-02"
            assert result['previous_period'] == "2023-02"
            assert result['current_value'] == 150
            assert result['previous_value'] == 120
            assert result['change'] == 30

    def test_calculate_annual_yoy_comparison_success(self, comparison_calculation_service, test_metric_definition):
        """测试计算年度同比 - 成功场景"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
            {'value': 1200, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'},
            {'value': 1000, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            ]
            
            result = comparison_calculation_service.calculate_annual_yoy_comparison(
            metric_code="TEST_METRIC",
            year=2024
            )
            
            assert result is not None
            assert result['current_period'] == "2024"
            assert result['previous_period'] == "2023"
            assert result['current_value'] == 1200
            assert result['previous_value'] == 1000
            assert result['change'] == 200

    def test_calculate_comparisons_batch_monthly(self, comparison_calculation_service, test_metric_definition):
        """测试批量计算对比 - 月度"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.return_value = {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            
            result = comparison_calculation_service.calculate_comparisons_batch(
            metric_codes=["TEST_METRIC"],
            year=2024,
            month=2,
            enable_mom=True,
            enable_yoy=True
            )
            
            assert result is not None
            assert "TEST_METRIC" in result
            assert 'mom' in result["TEST_METRIC"] or 'mom_error' in result["TEST_METRIC"]
            assert 'yoy' in result["TEST_METRIC"] or 'yoy_error' in result["TEST_METRIC"]

    def test_calculate_comparisons_batch_annual(self, comparison_calculation_service, test_metric_definition):
        """测试批量计算对比 - 年度"""
        with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
            mock_calc.return_value = {'value': 1000, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            
            result = comparison_calculation_service.calculate_comparisons_batch(
            metric_codes=["TEST_METRIC"],
            year=2024,
            month=None,
            enable_mom=False,
            enable_yoy=True
            )
            
            assert result is not None
            assert "TEST_METRIC" in result

    def test_calculate_comparisons_batch_metric_not_found(self, comparison_calculation_service):
        """测试批量计算对比 - 指标不存在"""
        result = comparison_calculation_service.calculate_comparisons_batch(
        metric_codes=["NONEXISTENT_METRIC"],
        year=2024,
        month=2
        )
        
        assert result is not None
        assert "NONEXISTENT_METRIC" not in result or len(result) == 0

    def test_calculate_comparisons_batch_multiple_metrics(self, comparison_calculation_service, db_session):
        """测试批量计算对比 - 多个指标"""
        # 创建多个指标
        for i in range(2):
            metric = ReportMetricDefinition(
            metric_code=f"METRIC_{i}",
            metric_name=f"指标{i}",
            category="TEST",
            data_source="test_table",
            calculation_type="COUNT",
            support_mom=True,
            support_yoy=True
            )
            db_session.add(metric)
            db_session.commit()
        
            with patch.object(comparison_calculation_service.metric_service, 'calculate_metric') as mock_calc:
                mock_calc.return_value = {'value': 100, 'metric_name': '测试指标', 'unit': '', 'format_type': 'NUMBER'}
            
                result = comparison_calculation_service.calculate_comparisons_batch(
                metric_codes=["METRIC_0", "METRIC_1"],
                year=2024,
                month=2
                )
            
                assert result is not None
                assert len(result) == 2
