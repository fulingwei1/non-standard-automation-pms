# -*- coding: utf-8 -*-
"""
指标计算服务单元测试
覆盖: app/services/metric_calculation_service.py
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.metric_calculation_service import MetricCalculationService
    return MetricCalculationService(mock_db)


def make_metric_def(
    code="test_metric",
    name="测试指标",
    data_source="Project",
    calculation_type="COUNT",
    data_field=None,
    unit="个",
    format_type="NUMBER",
    decimal_places=2,
    filter_conditions=None,
    calculation_formula=None,
    is_active=True,
):
    m = MagicMock()
    m.metric_code = code
    m.metric_name = name
    m.data_source = data_source
    m.calculation_type = calculation_type
    m.data_field = data_field
    m.unit = unit
    m.format_type = format_type
    m.decimal_places = decimal_places
    m.filter_conditions = filter_conditions
    m.calculation_formula = calculation_formula
    m.is_active = is_active
    return m


# ─── calculate_metric ─────────────────────────────────────────────────────────

class TestCalculateMetric:
    def test_metric_not_found_raises(self, service, mock_db):
        """指标定义不存在应报错"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="指标定义不存在"):
            service.calculate_metric("unknown_metric", date(2024, 1, 1), date(2024, 1, 31))

    def test_unsupported_data_source_raises(self, service, mock_db):
        """不支持的数据源应报错"""
        metric_def = make_metric_def(data_source="UnsupportedModel")
        mock_db.query.return_value.filter.return_value.first.return_value = metric_def
        with pytest.raises(ValueError, match="不支持的数据源"):
            service.calculate_metric("test", date(2024, 1, 1), date(2024, 1, 31))

    def test_count_calculation(self, service, mock_db):
        """COUNT 类型计算"""
        metric_def = make_metric_def(calculation_type="COUNT")
        mock_db.query.return_value.filter.return_value.first.return_value = metric_def

        # Setup the model query chain
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 42
        mock_db.query.return_value = q
        mock_db.query.return_value.filter.return_value.first.return_value = metric_def

        # Reset with proper side effects
        call_count = [0]
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                m = MagicMock()
                m.filter.return_value = m
                m.first.return_value = metric_def
                return m
            else:
                m = MagicMock()
                m.filter.return_value = m
                m.count.return_value = 42
                return m

        mock_db.query.side_effect = query_side_effect
        result = service.calculate_metric("test_metric", date(2024, 1, 1), date(2024, 1, 31))
        assert result["metric_code"] == "test_metric"
        assert result["value"] == 42

    def test_unsupported_calculation_type_raises(self, service, mock_db):
        """不支持的计算类型应报错"""
        metric_def = make_metric_def(calculation_type="UNKNOWN")

        call_count = [0]
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                m = MagicMock()
                m.filter.return_value = m
                m.first.return_value = metric_def
                return m
            else:
                m = MagicMock()
                m.filter.return_value = m
                return m

        mock_db.query.side_effect = query_side_effect
        with pytest.raises(ValueError, match="不支持的计算类型"):
            service.calculate_metric("test_metric", date(2024, 1, 1), date(2024, 1, 31))

    def test_sum_without_data_field_raises(self, service, mock_db):
        """SUM 计算类型未指定 data_field 应报错"""
        metric_def = make_metric_def(calculation_type="SUM", data_field=None)

        call_count = [0]
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                m = MagicMock()
                m.filter.return_value = m
                m.first.return_value = metric_def
                return m
            else:
                m = MagicMock()
                m.filter.return_value = m
                return m

        mock_db.query.side_effect = query_side_effect
        with pytest.raises(ValueError, match="SUM计算类型需要指定"):
            service.calculate_metric("test_metric", date(2024, 1, 1), date(2024, 1, 31))


# ─── calculate_metrics_batch ──────────────────────────────────────────────────

class TestCalculateMetricsBatch:
    def test_batch_calculation_handles_errors(self, service, mock_db):
        """批量计算时，单个失败不影响其他"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        results = service.calculate_metrics_batch(
            ["metric_a", "metric_b"],
            date(2024, 1, 1),
            date(2024, 1, 31),
        )
        assert "metric_a" in results
        assert results["metric_a"]["error"] is not None
        assert "metric_b" in results


# ─── format_metric_value ──────────────────────────────────────────────────────

class TestFormatMetricValue:
    def test_format_number(self, service):
        assert service.format_metric_value(3.14159, "NUMBER", 2) == "3.14"

    def test_format_percentage(self, service):
        assert service.format_metric_value(85.5, "PERCENTAGE", 1) == "85.5%"

    def test_format_currency(self, service):
        result = service.format_metric_value(100000.0, "CURRENCY", 2)
        assert "¥" in result
        assert "100,000.00" in result

    def test_format_none_returns_dash(self, service):
        assert service.format_metric_value(None, "NUMBER") == "-"

    def test_format_integer_number(self, service):
        assert service.format_metric_value(42, "NUMBER") == "42"

    def test_format_unknown_type(self, service):
        assert service.format_metric_value("raw", "UNKNOWN") == "raw"


# ─── _apply_filter_conditions ────────────────────────────────────────────────

class TestApplyFilterConditions:
    def test_no_filters_key_returns_query(self, service):
        """没有 filters key 时直接返回 query"""
        query = MagicMock()
        model = MagicMock()
        result = service._apply_filter_conditions(
            query, model, {"other": "data"}, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result == query

    def test_empty_filter_conditions(self, service):
        """空 filter_conditions 直接返回 query"""
        query = MagicMock()
        model = MagicMock()
        result = service._apply_filter_conditions(
            query, model, None, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert result == query

    def test_equal_operator(self, service):
        """= 操作符筛选"""
        query = MagicMock()
        query.filter.return_value = query

        from app.models.project import Project
        conditions = {"filters": [{"field": "status", "operator": "=", "value": "ACTIVE"}]}
        result = service._apply_filter_conditions(
            query, Project, conditions, date(2024, 1, 1), date(2024, 1, 31)
        )
        # Should have called filter
        query.filter.assert_called()

    def test_in_operator_with_list(self, service):
        """IN 操作符（列表）"""
        query = MagicMock()
        query.filter.return_value = query

        from app.models.project import Project
        conditions = {"filters": [{"field": "status", "operator": "IN", "value": ["ACTIVE", "COMPLETED"]}]}
        result = service._apply_filter_conditions(
            query, Project, conditions, date(2024, 1, 1), date(2024, 1, 31)
        )
        query.filter.assert_called()

    def test_period_start_value_substitution(self, service):
        """period_start 特殊值应被替换"""
        query = MagicMock()
        query.filter.return_value = query

        from app.models.project import Project
        conditions = {"filters": [{"field": "created_at", "operator": ">=", "value": "period_start"}]}
        result = service._apply_filter_conditions(
            query, Project, conditions, date(2024, 1, 1), date(2024, 1, 31)
        )
        query.filter.assert_called()

    def test_unknown_field_skipped(self, service):
        """不存在的字段应跳过，不报错"""
        query = MagicMock()

        from app.models.project import Project
        conditions = {"filters": [{"field": "nonexistent_field_xyz", "operator": "=", "value": "X"}]}
        result = service._apply_filter_conditions(
            query, Project, conditions, date(2024, 1, 1), date(2024, 1, 31)
        )
        # No filter call because field doesn't exist
        query.filter.assert_not_called()
