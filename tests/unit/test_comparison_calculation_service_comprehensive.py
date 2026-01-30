# -*- coding: utf-8 -*-
"""
ComparisonCalculationService 综合单元测试

测试覆盖:
- calculate_mom_comparison: 计算环比（与上月对比）
- calculate_yoy_comparison: 计算同比（与去年同期对比）
- calculate_annual_yoy_comparison: 计算年度同比
- calculate_comparisons_batch: 批量计算对比数据
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestComparisonCalculationServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService"):
            service = ComparisonCalculationService(mock_db)

        assert service.db == mock_db


class TestCalculateMomComparison:
    """测试 calculate_mom_comparison 方法"""

    def test_calculates_month_over_month_correctly(self):
        """测试正确计算环比"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 100, "metric_name": "测试指标", "unit": "个", "format_type": "NUMBER"},
                {"value": 80, "metric_name": "测试指标", "unit": "个", "format_type": "NUMBER"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["current_value"] == 100
        assert result["previous_value"] == 80
        assert result["change"] == 20
        assert result["change_rate"] == 25.0  # (100-80)/80 * 100
        assert result["is_increase"] is True
        assert result["current_period"] == "2026-03"
        assert result["previous_period"] == "2026-02"

    def test_handles_january_previous_month(self):
        """测试处理1月的上月（12月）"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 100, "metric_name": "测试指标"},
                {"value": 90, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 1)

        assert result["current_period"] == "2026-01"
        assert result["previous_period"] == "2025-12"

    def test_handles_zero_previous_value(self):
        """测试处理上期值为零"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 100, "metric_name": "测试指标"},
                {"value": 0, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["change_rate"] == 100  # 从0增长到正数

    def test_handles_zero_both_values(self):
        """测试处理两期都为零"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 0, "metric_name": "测试指标"},
                {"value": 0, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["change_rate"] == 0
        assert result["is_increase"] is False
        assert result["is_decrease"] is False

    def test_identifies_decrease(self):
        """测试识别下降"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 80, "metric_name": "测试指标"},
                {"value": 100, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["change"] == -20
        assert result["is_increase"] is False
        assert result["is_decrease"] is True


class TestCalculateYoyComparison:
    """测试 calculate_yoy_comparison 方法"""

    def test_calculates_year_over_year_correctly(self):
        """测试正确计算同比"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 120, "metric_name": "测试指标", "unit": "万元", "format_type": "CURRENCY"},
                {"value": 100, "metric_name": "测试指标", "unit": "万元", "format_type": "CURRENCY"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_yoy_comparison("METRIC001", 2026, 6)

        assert result["current_value"] == 120
        assert result["previous_value"] == 100
        assert result["change"] == 20
        assert result["change_rate"] == 20.0  # (120-100)/100 * 100
        assert result["current_period"] == "2026-06"
        assert result["previous_period"] == "2025-06"

    def test_compares_same_month_different_year(self):
        """测试对比不同年份的相同月份"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 200, "metric_name": "测试指标"},
                {"value": 150, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_yoy_comparison("METRIC001", 2026, 12)

        assert result["current_period"] == "2026-12"
        assert result["previous_period"] == "2025-12"


class TestCalculateAnnualYoyComparison:
    """测试 calculate_annual_yoy_comparison 方法"""

    def test_calculates_annual_comparison_correctly(self):
        """测试正确计算年度同比"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 1000, "metric_name": "年度指标", "unit": "万元", "format_type": "CURRENCY"},
                {"value": 800, "metric_name": "年度指标", "unit": "万元", "format_type": "CURRENCY"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_annual_yoy_comparison("ANNUAL_METRIC", 2026)

        assert result["current_value"] == 1000
        assert result["previous_value"] == 800
        assert result["change"] == 200
        assert result["change_rate"] == 25.0
        assert result["current_period"] == "2026"
        assert result["previous_period"] == "2025"

    def test_uses_full_year_period(self):
        """测试使用全年周期"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 500, "metric_name": "测试指标"},
                {"value": 500, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_annual_yoy_comparison("ANNUAL_METRIC", 2026)

        # Verify metric_service.calculate_metric was called with full year dates
        calls = mock_metric_service.calculate_metric.call_args_list
        assert calls[0][0][1] == date(2026, 1, 1)  # Current year start
        assert calls[0][0][2] == date(2026, 12, 31)  # Current year end
        assert calls[1][0][1] == date(2025, 1, 1)  # Previous year start
        assert calls[1][0][2] == date(2025, 12, 31)  # Previous year end


class TestCalculateComparisonsBatch:
    """测试 calculate_comparisons_batch 方法"""

    def test_calculates_batch_for_month(self):
        """测试批量计算月度对比"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        mock_metric_def = MagicMock()
        mock_metric_def.metric_code = "METRIC001"
        mock_metric_def.metric_name = "测试指标"
        mock_metric_def.support_mom = True
        mock_metric_def.support_yoy = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_metric_def

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.return_value = {
                "value": 100, "metric_name": "测试指标"
            }
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["METRIC001"],
                year=2026,
                month=3,
                enable_mom=True,
                enable_yoy=True
            )

        assert "METRIC001" in result
        assert "mom" in result["METRIC001"]
        assert "yoy" in result["METRIC001"]

    def test_calculates_batch_for_year(self):
        """测试批量计算年度对比"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        mock_metric_def = MagicMock()
        mock_metric_def.metric_code = "ANNUAL001"
        mock_metric_def.metric_name = "年度指标"
        mock_metric_def.support_mom = False
        mock_metric_def.support_yoy = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_metric_def

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.return_value = {
                "value": 1000, "metric_name": "年度指标"
            }
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["ANNUAL001"],
                year=2026,
                month=None,  # Annual comparison
                enable_yoy=True
            )

        assert "ANNUAL001" in result
        assert "yoy" in result["ANNUAL001"]

    def test_skips_metric_when_not_found(self):
        """测试指标不存在时跳过"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.comparison_calculation_service.MetricCalculationService"):
            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["NONEXISTENT"],
                year=2026,
                month=3
            )

        assert "NONEXISTENT" not in result or result.get("NONEXISTENT") is None

    def test_respects_enable_flags(self):
        """测试尊重启用标志"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        mock_metric_def = MagicMock()
        mock_metric_def.metric_code = "METRIC001"
        mock_metric_def.metric_name = "测试指标"
        mock_metric_def.support_mom = True
        mock_metric_def.support_yoy = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_metric_def

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.return_value = {
                "value": 100, "metric_name": "测试指标"
            }
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["METRIC001"],
                year=2026,
                month=3,
                enable_mom=False,  # Disabled
                enable_yoy=True
            )

        assert "METRIC001" in result
        assert "mom" not in result["METRIC001"]
        assert "yoy" in result["METRIC001"]

    def test_handles_calculation_error(self):
        """测试处理计算错误"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        mock_metric_def = MagicMock()
        mock_metric_def.metric_code = "METRIC001"
        mock_metric_def.metric_name = "测试指标"
        mock_metric_def.support_mom = True
        mock_metric_def.support_yoy = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_metric_def

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = Exception("计算错误")
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["METRIC001"],
                year=2026,
                month=3
            )

        assert "METRIC001" in result
        assert "mom_error" in result["METRIC001"]

    def test_respects_metric_support_flags(self):
        """测试尊重指标支持标志"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        mock_metric_def = MagicMock()
        mock_metric_def.metric_code = "METRIC001"
        mock_metric_def.metric_name = "测试指标"
        mock_metric_def.support_mom = False  # Not supported
        mock_metric_def.support_yoy = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_metric_def

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.return_value = {
                "value": 100, "metric_name": "测试指标"
            }
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_comparisons_batch(
                ["METRIC001"],
                year=2026,
                month=3,
                enable_mom=True,  # Enabled but not supported
                enable_yoy=True
            )

        assert "METRIC001" in result
        # MoM should not be calculated because metric doesn't support it
        assert "mom" not in result["METRIC001"]
        assert "yoy" in result["METRIC001"]


class TestChangeRateFormatting:
    """测试变化率格式化"""

    def test_formats_positive_change_rate(self):
        """测试格式化正变化率"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 110, "metric_name": "测试指标"},
                {"value": 100, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["change_rate_formatted"] == "+10.00%"

    def test_formats_negative_change_rate(self):
        """测试格式化负变化率"""
        from app.services.comparison_calculation_service import ComparisonCalculationService

        mock_db = MagicMock()

        with patch("app.services.comparison_calculation_service.MetricCalculationService") as MockMetricService:
            mock_metric_service = MagicMock()
            mock_metric_service.calculate_metric.side_effect = [
                {"value": 90, "metric_name": "测试指标"},
                {"value": 100, "metric_name": "测试指标"},
            ]
            MockMetricService.return_value = mock_metric_service

            service = ComparisonCalculationService(mock_db)
            result = service.calculate_mom_comparison("METRIC001", 2026, 3)

        assert result["change_rate_formatted"] == "-10.00%"
