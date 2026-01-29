"""
Metric Calculation Service Tests
指标计算服务测试
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from decimal import Decimal
from app.models.management_rhythm import ReportMetricDefinition
from app.services.metric_calculation_service import MetricCalculationService


@pytest.fixture
def service(db_session):
    """创建MetricCalculationService实例"""
    return MetricCalculationService(db_session)


@pytest.fixture
def mock_metric_def():
    """Mock指标定义"""
    return Mock(spec=ReportMetricDefinition, **{
        'metric_code': 'TOTAL_PROJECTS',
        'metric_name': '总项目数',
        'data_source': 'Project',
        'calculation_type': 'COUNT',
        'data_field': None,
        'filter_conditions': None,
        'calculation_formula': None,
        'unit': '个',
        'format_type': 'NUMBER',
        'decimal_places': 0,
        'is_active': True
    })


@pytest.mark.unit
class TestMetricCalculationService:
    """指标计算服务测试"""
    
    def test_init(self, db_session):
        """测试服务初始化"""
        service = MetricCalculationService(db_session)
        assert service.db == db_session
        assert 'Project' in service.data_source_map
        assert 'Lead' in service.data_source_map
    
    def test_format_metric_value_number(self, service):
        """测试格式化NUMBER类型"""
        result = service.format_metric_value(12345.6789, 'NUMBER', 2)
        assert result == '12345.68'
    
    def test_format_metric_value_percentage(self, service):
        """测试格式化PERCENTAGE类型"""
        result = service.format_metric_value(85.6789, 'PERCENTAGE', 2)
        assert result == '85.68%'
    
    def test_format_metric_value_currency(self, service):
        """测试格式化CURRENCY类型"""
        result = service.format_metric_value(12345.67, 'CURRENCY', 2)
        assert result == '¥12,345.67'
    
    def test_format_metric_value_none(self, service):
        """测试格式化None值"""
        result = service.format_metric_value(None, 'NUMBER', 2)
        assert result == '-'

    def test_format_metric_value_integer(self, service):
        """测试格式化整数值"""
        result = service.format_metric_value(100, 'NUMBER', 0)
        assert result == '100'

    def test_format_metric_value_decimal(self, service):
        """测试格式化Decimal类型"""
        result = service.format_metric_value(Decimal('1234.56'), 'CURRENCY', 2)
        assert '1,234.56' in result

    def test_format_metric_value_zero(self, service):
        """测试格式化零值"""
        result = service.format_metric_value(0, 'NUMBER', 2)
        assert '0' in result  # Could be '0' or '0.00' depending on implementation

    def test_calculate_metric_not_found(self, service):
        """测试计算不存在的指标"""
        with pytest.raises(ValueError) as exc_info:
            service.calculate_metric(
                metric_code='NON_EXISTENT',
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 31)
            )
        assert '指标定义不存在' in str(exc_info.value)

    def test_data_source_map_contains_expected_models(self, service):
        """测试数据源映射包含预期模型"""
        expected_models = [
            'Project', 'Lead', 'Opportunity', 'Contract', 'Invoice',
            'PurchaseOrder', 'Material', 'Ecn', 'Issue', 'Timesheet'
        ]
        for model in expected_models:
            assert model in service.data_source_map

    def test_format_metric_value_large_number(self, service):
        """测试格式化大数值"""
        result = service.format_metric_value(1234567890.12, 'CURRENCY', 2)
        assert '1,234,567,890.12' in result

    def test_format_metric_value_negative(self, service):
        """测试格式化负数"""
        result = service.format_metric_value(-100.5, 'NUMBER', 1)
        assert '-100.5' in result

    def test_format_metric_value_percentage_small(self, service):
        """测试格式化小百分比"""
        result = service.format_metric_value(0.5, 'PERCENTAGE', 2)
        assert '0.50%' in result


@pytest.mark.unit
class TestMetricCalculationEdgeCases:
    """指标计算边界情况测试"""

    def test_service_with_mock_db(self):
        """测试使用mock数据库"""
        mock_db = MagicMock()
        service = MetricCalculationService(mock_db)
        assert service.db == mock_db

    def test_format_unknown_type(self, db_session):
        """测试格式化未知类型"""
        service = MetricCalculationService(db_session)
        # Should handle unknown type gracefully
        result = service.format_metric_value(100, 'UNKNOWN_TYPE', 2)
        assert result is not None

    def test_calculate_metric_invalid_data_source(self, db_session):
        """测试无效数据源"""
        service = MetricCalculationService(db_session)
        mock_def = Mock()
        mock_def.metric_code = 'TEST'
        mock_def.data_source = 'InvalidModel'
        mock_def.is_active = True

        # Mock the query to return our mock definition
        db_session.query = MagicMock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_def

        with pytest.raises(ValueError) as exc_info:
            service.calculate_metric(
                metric_code='TEST',
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 31)
            )
        assert '不支持的数据源' in str(exc_info.value)
