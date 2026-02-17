# -*- coding: utf-8 -*-
"""指标计算服务测试"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.metric_calculation_service import MetricCalculationService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return MetricCalculationService(db)


class TestInit:
    def test_data_source_map(self, service):
        assert "Project" in service.data_source_map
        assert "Lead" in service.data_source_map
        assert len(service.data_source_map) > 10


class TestCalculateMetric:
    def test_metric_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="指标定义不存在"):
            service.calculate_metric("UNKNOWN", date(2026, 1, 1), date(2026, 1, 31))

    def test_unsupported_data_source(self, service, db):
        metric_def = MagicMock(
            metric_code="TEST", metric_name="Test", data_source="UnknownModel",
            is_active=True
        )
        db.query.return_value.filter.return_value.first.return_value = metric_def
        with pytest.raises(ValueError, match="不支持的数据源"):
            service.calculate_metric("TEST", date(2026, 1, 1), date(2026, 1, 31))

    def test_count_calculation(self, service, db):
        metric_def = MagicMock(
            metric_code="TEST", metric_name="Test", data_source="Project",
            is_active=True, calculation_type="COUNT", filter_conditions=None,
            unit="个", format_type="NUMBER", decimal_places=0
        )
        db.query.return_value.filter.return_value.first.return_value = metric_def
        db.query.return_value.filter.return_value.count.return_value = 5
        result = service.calculate_metric("TEST", date(2026, 1, 1), date(2026, 1, 31))
        assert result["metric_code"] == "TEST"


class TestCalculateByType:
    def test_count(self, service):
        query = MagicMock()
        query.count.return_value = 42
        metric_def = MagicMock(calculation_type="COUNT")
        result = service._calculate_by_type(query, MagicMock, metric_def)
        assert result == 42

    def test_sum(self, service):
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = 100.5
        metric_def = MagicMock(calculation_type="SUM", data_field="amount", metric_code="T")
        model = MagicMock()
        result = service._calculate_by_type(query, model, metric_def)
        assert result == 100.5

    def test_sum_none(self, service):
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = None
        metric_def = MagicMock(calculation_type="SUM", data_field="amount", metric_code="T")
        model = MagicMock()
        result = service._calculate_by_type(query, model, metric_def)
        assert result == 0.0

    def test_sum_no_field(self, service):
        metric_def = MagicMock(calculation_type="SUM", data_field=None, metric_code="T")
        with pytest.raises(ValueError):
            service._calculate_by_type(MagicMock(), MagicMock, metric_def)

    def test_avg(self, service):
        query = MagicMock()
        query.with_entities.return_value.scalar.return_value = 50.0
        metric_def = MagicMock(calculation_type="AVG", data_field="score", metric_code="T")
        result = service._calculate_by_type(query, MagicMock(), metric_def)
        assert result == 50.0

    def test_unsupported_type(self, service):
        metric_def = MagicMock(calculation_type="UNKNOWN")
        with pytest.raises(ValueError, match="不支持的计算类型"):
            service._calculate_by_type(MagicMock(), MagicMock, metric_def)


class TestCalculateRatio:
    def test_empty_formula(self, service):
        metric_def = MagicMock(calculation_formula="", metric_code="T")
        with pytest.raises(ValueError):
            service._calculate_ratio(MagicMock(), MagicMock, metric_def)

    def test_completed_ratio(self, service):
        query = MagicMock()
        query.count.return_value = 10
        query.filter.return_value.count.return_value = 7
        metric_def = MagicMock(calculation_formula="COMPLETED COUNT()", metric_code="T")
        model = MagicMock()
        result = service._calculate_ratio(query, model, metric_def)
        assert result == 70.0

    def test_zero_total(self, service):
        query = MagicMock()
        query.count.return_value = 0
        metric_def = MagicMock(calculation_formula="COMPLETED COUNT()", metric_code="T")
        result = service._calculate_ratio(query, MagicMock, metric_def)
        assert result == 0.0


class TestCalculateCustom:
    def test_no_formula(self, service):
        metric_def = MagicMock(calculation_formula=None, metric_code="T")
        with pytest.raises(ValueError):
            service._calculate_custom(MagicMock(), MagicMock, metric_def)

    def test_with_formula(self, service):
        metric_def = MagicMock(calculation_formula="some formula", metric_code="T")
        result = service._calculate_custom(MagicMock(), MagicMock, metric_def)
        assert result == 0.0


class TestBatchCalculate:
    def test_batch(self, service, db):
        # Make calculate_metric raise for one and succeed for another
        with patch.object(service, 'calculate_metric') as mock_calc:
            mock_calc.side_effect = [
                {"metric_code": "A", "value": 10},
                ValueError("error")
            ]
            results = service.calculate_metrics_batch(["A", "B"], date(2026, 1, 1), date(2026, 1, 31))
            assert "A" in results
            assert "B" in results
            assert results["B"]["value"] is None


class TestFormatMetricValue:
    def test_none(self, service):
        assert service.format_metric_value(None, "NUMBER") == "-"

    def test_number(self, service):
        assert service.format_metric_value(3.14159, "NUMBER", 2) == "3.14"

    def test_percentage(self, service):
        assert service.format_metric_value(85.5, "PERCENTAGE", 1) == "85.5%"

    def test_currency(self, service):
        result = service.format_metric_value(1000, "CURRENCY", 2)
        assert "¥" in result

    def test_unknown_format(self, service):
        assert service.format_metric_value(42, "UNKNOWN") == "42"


# =============================================================================
# 补充测试 A组覆盖率提升 (2026-02-17)
# =============================================================================

class TestCalculateByTypeAdditional:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.metric_calculation_service import MetricCalculationService
        self.svc = MetricCalculationService(self.db)

    def test_sum_calculates_value(self):
        query = MagicMock()
        metric_def = MagicMock(
            calculation_type="SUM",
            data_field="total_amount",
            metric_code="TEST_SUM"
        )
        query.with_entities.return_value.scalar.return_value = 50000.0
        from app.services.metric_calculation_service import MetricCalculationService
        from app.models.sales import Contract

        result = self.svc._calculate_by_type(query, Contract, metric_def)
        assert result == 50000.0

    def test_sum_returns_zero_when_none(self):
        query = MagicMock()
        metric_def = MagicMock(
            calculation_type="SUM",
            data_field="total_amount",
            metric_code="TEST_SUM"
        )
        query.with_entities.return_value.scalar.return_value = None
        from app.models.sales import Contract
        result = self.svc._calculate_by_type(query, Contract, metric_def)
        assert result == 0.0

    def test_avg_calculates_value(self):
        query = MagicMock()
        metric_def = MagicMock(
            calculation_type="AVG",
            data_field="progress",
            metric_code="TEST_AVG"
        )
        query.with_entities.return_value.scalar.return_value = 75.0
        from app.models.project import Project
        result = self.svc._calculate_by_type(query, Project, metric_def)
        assert result == 75.0

    def test_count_type_returns_count(self):
        query = MagicMock()
        query.count.return_value = 10
        metric_def = MagicMock(calculation_type="COUNT")
        from app.models.project import Project
        result = self.svc._calculate_by_type(query, Project, metric_def)
        assert result == 10

    def test_unknown_calculation_type_raises(self):
        query = MagicMock()
        metric_def = MagicMock(
            calculation_type="INVALID",
            metric_code="BAD"
        )
        from app.models.project import Project
        with pytest.raises(ValueError, match="不支持的计算类型"):
            self.svc._calculate_by_type(query, Project, metric_def)

    def test_sum_requires_data_field(self):
        query = MagicMock()
        metric_def = MagicMock(
            calculation_type="SUM",
            data_field=None,
            metric_code="TEST_NO_FIELD"
        )
        from app.models.project import Project
        with pytest.raises(ValueError, match="需要指定data_field"):
            self.svc._calculate_by_type(query, Project, metric_def)


class TestApplyFilterConditions:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.metric_calculation_service import MetricCalculationService
        self.svc = MetricCalculationService(self.db)

    def test_returns_query_unchanged_when_no_filters_key(self):
        from app.models.project import Project
        query = MagicMock()
        result = self.svc._apply_filter_conditions(
            query, Project, {"other": "data"},
            date(2026, 1, 1), date(2026, 1, 31)
        )
        # query returned unchanged
        assert result is query

    def test_filter_eq_operator(self):
        from app.models.project import Project
        query = MagicMock()
        query.filter.return_value = query

        filter_conditions = {
            "filters": [
                {"field": "status", "operator": "=", "value": "ACTIVE"}
            ]
        }
        result = self.svc._apply_filter_conditions(
            query, Project, filter_conditions,
            date(2026, 1, 1), date(2026, 1, 31)
        )
        # At minimum, no exception should be raised
        assert result is not None

    def test_filter_in_operator_list(self):
        from app.models.project import Project
        query = MagicMock()
        query.filter.return_value = query

        filter_conditions = {
            "filters": [
                {"field": "status", "operator": "IN", "value": ["ACTIVE", "PENDING"]}
            ]
        }
        result = self.svc._apply_filter_conditions(
            query, Project, filter_conditions,
            date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result is not None

    def test_filter_period_start_substituted(self):
        from app.models.project import Project
        query = MagicMock()
        query.filter.return_value = query

        period_start = date(2026, 1, 1)
        period_end = date(2026, 1, 31)
        filter_conditions = {
            "filters": [
                {"field": "created_at", "operator": ">=", "value": "period_start"}
            ]
        }
        # Should not raise
        result = self.svc._apply_filter_conditions(
            query, Project, filter_conditions,
            period_start, period_end
        )
        assert result is not None


class TestCalculateMetricsBatch:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.metric_calculation_service import MetricCalculationService
        self.svc = MetricCalculationService(self.db)

    def test_batch_partial_failure(self):
        with patch.object(self.svc, "calculate_metric") as mock:
            mock.side_effect = [
                {"metric_code": "M1", "value": 100},
                ValueError("指标定义不存在"),
            ]
            results = self.svc.calculate_metrics_batch(
                ["M1", "M2"], date(2026, 1, 1), date(2026, 1, 31)
            )
        assert results["M1"]["value"] == 100
        assert results["M2"]["value"] is None
        assert "error" in results["M2"]

    def test_batch_all_success(self):
        with patch.object(self.svc, "calculate_metric") as mock:
            mock.side_effect = [
                {"metric_code": "A", "value": 5},
                {"metric_code": "B", "value": 10},
            ]
            results = self.svc.calculate_metrics_batch(
                ["A", "B"], date(2026, 1, 1), date(2026, 1, 31)
            )
        assert len(results) == 2
        assert results["A"]["value"] == 5
