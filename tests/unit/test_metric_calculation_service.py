# -*- coding: utf-8 -*-
"""
Tests for metric_calculation_service service
Covers: app/services/metric_calculation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 181 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.metric_calculation_service import MetricCalculationService
from app.models.management_rhythm import ReportMetricDefinition


@pytest.fixture
def metric_calculation_service(db_session: Session):
    """创建 MetricCalculationService 实例"""
    return MetricCalculationService(db_session)


@pytest.fixture
def mock_metric_definition(db_session: Session):
    """创建测试用的指标定义"""
    metric_def = ReportMetricDefinition(
        metric_code="TEST_METRIC",
        metric_name="测试指标",
        data_source="Project",
        calculation_type="COUNT",
        is_active=True,
        unit="个",
        format_type="NUMBER",
        decimal_places=0
    )
    db_session.add(metric_def)
    db_session.commit()
    db_session.refresh(metric_def)
    return metric_def


class TestMetricCalculationService:
    """Test suite for MetricCalculationService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = MetricCalculationService(db_session)
        assert service is not None
        assert service.db == db_session
        assert 'Project' in service.data_source_map
        assert 'Lead' in service.data_source_map
        assert len(service.data_source_map) > 0

    def test_format_metric_value_number(self, metric_calculation_service):
        """测试格式化数字类型指标值"""
        result = metric_calculation_service.format_metric_value(123.456, 'NUMBER', 2)
        assert result == "123.46"
        
        result = metric_calculation_service.format_metric_value(100, 'NUMBER', 0)
        assert result == "100"

    def test_format_metric_value_percentage(self, metric_calculation_service):
        """测试格式化百分比类型指标值"""
        result = metric_calculation_service.format_metric_value(85.5, 'PERCENTAGE', 1)
        assert result == "85.5%"
        
        result = metric_calculation_service.format_metric_value(100, 'PERCENTAGE', 0)
        assert result == "100%"

    def test_format_metric_value_currency(self, metric_calculation_service):
        """测试格式化货币类型指标值"""
        result = metric_calculation_service.format_metric_value(12345.67, 'CURRENCY', 2)
        assert "12345.67" in result
        assert "¥" in result or "元" in result
        
        result = metric_calculation_service.format_metric_value(Decimal('1000.5'), 'CURRENCY', 2)
        assert "1000.50" in result

    def test_format_metric_value_none(self, metric_calculation_service):
        """测试格式化None值"""
        result = metric_calculation_service.format_metric_value(None, 'NUMBER', 2)
        assert result == "-"

    def test_format_metric_value_default(self, metric_calculation_service):
        """测试格式化默认类型"""
        result = metric_calculation_service.format_metric_value("test", 'UNKNOWN', 2)
        assert result == "test"

    def test_calculate_metric_not_found(self, metric_calculation_service):
        """测试计算不存在的指标"""
        with pytest.raises(ValueError, match="指标定义不存在"):
            metric_calculation_service.calculate_metric(
                "NON_EXISTENT",
                date.today() - timedelta(days=30),
                date.today()
            )

    def test_calculate_metric_invalid_data_source(self, metric_calculation_service, db_session):
        """测试计算不支持的数据源"""
        metric_def = ReportMetricDefinition(
            metric_code="INVALID_METRIC",
            metric_name="无效指标",
            data_source="InvalidSource",
            calculation_type="COUNT",
            is_active=True
        )
        db_session.add(metric_def)
        db_session.commit()
        
        with pytest.raises(ValueError, match="不支持的数据源"):
            metric_calculation_service.calculate_metric(
                "INVALID_METRIC",
                date.today() - timedelta(days=30),
                date.today()
            )

    def test_calculate_metric_count_type(self, metric_calculation_service, db_session, mock_metric_definition):
        """测试COUNT类型指标计算"""
        # Mock查询结果
        with patch.object(metric_calculation_service.db, 'query') as mock_query:
            mock_query_result = MagicMock()
            mock_query_result.filter.return_value = mock_query_result
            mock_query_result.count.return_value = 10
            mock_query.return_value = mock_query_result
            
            result = metric_calculation_service.calculate_metric(
                "TEST_METRIC",
                date.today() - timedelta(days=30),
                date.today()
            )
            
            assert result is not None
            assert result['metric_code'] == "TEST_METRIC"
            assert result['value'] == 10
            assert result['metric_name'] == "测试指标"

    def test_calculate_metric_sum_type_missing_field(self, metric_calculation_service, db_session):
        """测试SUM类型缺少data_field"""
        metric_def = ReportMetricDefinition(
            metric_code="SUM_METRIC",
            metric_name="求和指标",
            data_source="Project",
            calculation_type="SUM",
            data_field=None,  # 缺少字段
            is_active=True
        )
        db_session.add(metric_def)
        db_session.commit()
        
        with patch.object(metric_calculation_service.db, 'query') as mock_query:
            mock_query_result = MagicMock()
            mock_query_result.filter.return_value = mock_query_result
            mock_query.return_value = mock_query_result
            
            with pytest.raises(ValueError, match="需要指定data_field"):
                metric_calculation_service.calculate_metric(
                    "SUM_METRIC",
                    date.today() - timedelta(days=30),
                    date.today()
                )

    def test_calculate_metrics_batch_success(self, metric_calculation_service, db_session, mock_metric_definition):
        """测试批量计算指标 - 成功场景"""
        # 创建另一个指标定义
        metric_def2 = ReportMetricDefinition(
            metric_code="TEST_METRIC_2",
            metric_name="测试指标2",
            data_source="Project",
            calculation_type="COUNT",
            is_active=True
        )
        db_session.add(metric_def2)
        db_session.commit()
        
        with patch.object(metric_calculation_service.db, 'query') as mock_query:
            mock_query_result = MagicMock()
            mock_query_result.filter.return_value = mock_query_result
            mock_query_result.count.return_value = 5
            mock_query.return_value = mock_query_result
            
            results = metric_calculation_service.calculate_metrics_batch(
                ["TEST_METRIC", "TEST_METRIC_2"],
                date.today() - timedelta(days=30),
                date.today()
            )
            
            assert len(results) == 2
            assert "TEST_METRIC" in results
            assert "TEST_METRIC_2" in results
            assert results["TEST_METRIC"]['value'] == 5

    def test_calculate_metrics_batch_with_error(self, metric_calculation_service, db_session, mock_metric_definition):
        """测试批量计算指标 - 包含错误"""
        with patch.object(metric_calculation_service.db, 'query') as mock_query:
            # 第一个指标成功
            mock_query_result1 = MagicMock()
            mock_query_result1.filter.return_value = mock_query_result1
            mock_query_result1.count.return_value = 5
            
            # 第二个指标失败（指标不存在）
            mock_query.return_value = mock_query_result1
            
            results = metric_calculation_service.calculate_metrics_batch(
                ["TEST_METRIC", "NON_EXISTENT"],
                date.today() - timedelta(days=30),
                date.today()
            )
            
            assert len(results) == 2
            assert "TEST_METRIC" in results
            assert results["TEST_METRIC"]['value'] == 5
            assert "NON_EXISTENT" in results
            assert 'error' in results["NON_EXISTENT"]
            assert results["NON_EXISTENT"]['value'] is None

    def test_calculate_metric_with_filter_conditions(self, metric_calculation_service, db_session, mock_metric_definition):
        """测试带筛选条件的指标计算"""
        with patch.object(metric_calculation_service.db, 'query') as mock_query:
            mock_query_result = MagicMock()
            mock_query_result.filter.return_value = mock_query_result
            mock_query_result.count.return_value = 3
            mock_query.return_value = mock_query_result
            
            filter_conditions = {
                'filters': [
                    {'field': 'status', 'operator': '=', 'value': 'ACTIVE'}
                ]
            }
            
            result = metric_calculation_service.calculate_metric(
                "TEST_METRIC",
                date.today() - timedelta(days=30),
                date.today(),
                filter_conditions=filter_conditions
            )
            
            assert result is not None
            assert result['value'] == 3
