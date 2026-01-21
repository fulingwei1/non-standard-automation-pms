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
