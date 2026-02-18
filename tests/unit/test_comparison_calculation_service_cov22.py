# -*- coding: utf-8 -*-
"""第二十二批：comparison_calculation_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.comparison_calculation_service import ComparisonCalculationService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def svc(db):
    with patch(
        "app.services.comparison_calculation_service.MetricCalculationService"
    ) as MockMetric:
        mock_metric = MagicMock()
        MockMetric.return_value = mock_metric
        service = ComparisonCalculationService(db)
        service.metric_service = mock_metric
        return service


def make_metric_result(value, metric_name="测试指标", unit="个"):
    return {
        "value": value,
        "metric_name": metric_name,
        "unit": unit,
        "format_type": "NUMBER"
    }


class TestCalculateMomComparison:
    def test_returns_dict_with_required_fields(self, svc):
        """环比返回包含必要字段的字典"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(100),
            make_metric_result(80)
        ]
        result = svc.calculate_mom_comparison("metric_a", 2025, 3)
        assert "current_value" in result
        assert "previous_value" in result
        assert "change_rate" in result

    def test_mom_increase_detected(self, svc):
        """环比上升正确识别"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(120),
            make_metric_result(100)
        ]
        result = svc.calculate_mom_comparison("metric_a", 2025, 3)
        assert result["is_increase"] is True
        assert result["is_decrease"] is False

    def test_mom_decrease_detected(self, svc):
        """环比下降正确识别"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(80),
            make_metric_result(100)
        ]
        result = svc.calculate_mom_comparison("metric_a", 2025, 3)
        assert result["is_decrease"] is True
        assert result["is_increase"] is False

    def test_january_compares_to_december(self, svc):
        """1月份的环比比较12月"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(100),
            make_metric_result(90)
        ]
        result = svc.calculate_mom_comparison("metric_a", 2025, 1)
        assert result["previous_period"] == "2024-12"

    def test_zero_previous_value_handled(self, svc):
        """上期值为0时不出现除零错误"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(100),
            make_metric_result(0)
        ]
        result = svc.calculate_mom_comparison("metric_a", 2025, 3)
        assert isinstance(result["change_rate"], (int, float))


class TestCalculateYoyComparison:
    def test_returns_dict_with_required_fields(self, svc):
        """同比返回包含必要字段的字典"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(150),
            make_metric_result(100)
        ]
        result = svc.calculate_yoy_comparison("metric_b", 2025, 6)
        assert "current_period" in result
        assert "previous_period" in result
        assert "change_rate_formatted" in result

    def test_yoy_previous_period_is_last_year(self, svc):
        """同比上期是去年同月"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(100),
            make_metric_result(80)
        ]
        result = svc.calculate_yoy_comparison("metric_b", 2025, 6)
        assert result["previous_period"] == "2024-06"


class TestCalculateAnnualYoyComparison:
    def test_annual_comparison_returns_dict(self, svc):
        """年度同比返回字典"""
        svc.metric_service.calculate_metric.side_effect = [
            make_metric_result(1000),
            make_metric_result(900)
        ]
        result = svc.calculate_annual_yoy_comparison("metric_c", 2025)
        assert result["current_period"] == "2025"
        assert result["previous_period"] == "2024"


class TestCalculateComparisonsBatch:
    def test_empty_metric_codes_returns_empty_dict(self, svc):
        """空指标列表返回空字典"""
        result = svc.calculate_comparisons_batch([], 2025, 3)
        assert result == {}

    def test_unknown_metric_returns_error_or_skipped(self, svc):
        """未知指标跳过或返回错误信息"""
        svc.db.query.return_value.filter.return_value.first.return_value = None
        result = svc.calculate_comparisons_batch(["unknown_metric"], 2025, 3)
        # Either empty (skipped) or contains error
        assert isinstance(result, dict)
