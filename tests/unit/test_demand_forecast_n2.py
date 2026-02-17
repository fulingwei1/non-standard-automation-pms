# -*- coding: utf-8 -*-
"""
需求预测引擎 N2 深度覆盖测试
覆盖: _detect_seasonality, _linear_regression_forecast,
      batch_forecast_for_project, get_forecast_accuracy_report,
      _generate_forecast_no, 置信区间 90/other 分支
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.shortage.demand_forecast_engine import DemandForecastEngine


@pytest.fixture
def engine():
    db = MagicMock()
    return DemandForecastEngine(db)


# ======================= _detect_seasonality =======================

class TestDetectSeasonality:
    def test_short_data_returns_one(self, engine):
        """少于14条数据时返回1.0"""
        data = [Decimal("10")] * 10
        result = engine._detect_seasonality(data)
        assert result == Decimal("1.0")

    def test_uniform_data_returns_one(self, engine):
        """均匀数据的季节性因子为1.0"""
        data = [Decimal("10")] * 20
        result = engine._detect_seasonality(data)
        assert result == Decimal("1.0")

    def test_recent_spike_increases_factor(self, engine):
        """最近7天均值高于历史时，季节性因子 > 1.0"""
        # 历史13天=5，最近7天=20
        data = [Decimal("5")] * 13 + [Decimal("20")] * 7
        result = engine._detect_seasonality(data)
        assert result > Decimal("1.0")

    def test_recent_dip_decreases_factor(self, engine):
        """最近7天均值低于历史时，因子 < 1.0"""
        data = [Decimal("20")] * 13 + [Decimal("5")] * 7
        result = engine._detect_seasonality(data)
        assert result < Decimal("1.0")

    def test_factor_capped_at_max_2(self, engine):
        """极端情况下因子被限制在2.0以内"""
        data = [Decimal("1")] * 13 + [Decimal("100")] * 7
        result = engine._detect_seasonality(data)
        assert result <= Decimal("2.0")

    def test_factor_floored_at_0_5(self, engine):
        """因子不低于0.5"""
        data = [Decimal("100")] * 13 + [Decimal("1")] * 7
        result = engine._detect_seasonality(data)
        assert result >= Decimal("0.5")

    def test_zero_historical_avg_returns_one(self, engine):
        """历史均值为0时返回1.0防止除零"""
        data = [Decimal("0")] * 14
        result = engine._detect_seasonality(data)
        assert result == Decimal("1.0")


# ======================= _linear_regression_forecast =======================

class TestLinearRegressionForecast:
    def test_single_data_point_returns_average(self, engine):
        """单数据点时返回均值"""
        data = [Decimal("50")]
        result = engine._linear_regression_forecast(data)
        assert result == Decimal("50")

    def test_two_data_points_extrapolates(self, engine):
        """两点拟合后预测第3点"""
        data = [Decimal("10"), Decimal("20")]
        result = engine._linear_regression_forecast(data)
        # slope=10, intercept=0, next_x=2 → 30
        assert result == Decimal("30")

    def test_upward_trend_extrapolates_higher(self, engine):
        """上升趋势时预测值高于最后一点"""
        data = [Decimal(str(i * 5)) for i in range(1, 11)]
        result = engine._linear_regression_forecast(data)
        assert result > data[-1]

    def test_downward_trend_floored_at_zero(self, engine):
        """下降趋势但不低于0"""
        data = [Decimal(str(max(0, 100 - i * 15))) for i in range(7)]
        result = engine._linear_regression_forecast(data)
        assert result >= Decimal("0")

    def test_uniform_data_returns_same_value(self, engine):
        """均匀数据预测值等于均值"""
        data = [Decimal("42")] * 10
        result = engine._linear_regression_forecast(data)
        assert abs(result - Decimal("42")) < Decimal("0.1")


# ======================= _calculate_confidence_interval 分支 =======================

class TestConfidenceIntervalBranches:
    def test_95_confidence_uses_1_96(self, engine):
        lower, upper = engine._calculate_confidence_interval(
            Decimal("100"), Decimal("10"), 95.0
        )
        margin = Decimal("1.96") * Decimal("10")
        assert upper == Decimal("100") + margin
        assert lower == Decimal("100") - margin

    def test_90_confidence_uses_1_645(self, engine):
        lower, upper = engine._calculate_confidence_interval(
            Decimal("100"), Decimal("10"), 90.0
        )
        margin = Decimal("1.645") * Decimal("10")
        assert upper == Decimal("100") + margin

    def test_other_confidence_uses_1_0(self, engine):
        lower, upper = engine._calculate_confidence_interval(
            Decimal("100"), Decimal("10"), 80.0
        )
        margin = Decimal("1.0") * Decimal("10")
        assert upper == Decimal("100") + margin

    def test_lower_bound_not_negative(self, engine):
        """下限不低于0"""
        lower, upper = engine._calculate_confidence_interval(
            Decimal("5"), Decimal("20"), 95.0
        )
        assert lower >= Decimal("0")


# ======================= batch_forecast_for_project =======================

class TestBatchForecastForProject:
    @patch("app.services.shortage.demand_forecast_engine.save_obj")
    def test_batch_forecast_skips_failed_materials(self, mock_save, engine):
        """失败的物料预测被跳过，不影响其他"""
        from app.core.exceptions import BusinessException

        engine.db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]

        call_count = [0]
        def forecast_side(material_id, **kwargs):
            call_count[0] += 1
            if material_id == 2:
                raise BusinessException("历史数据不足")
            mock = MagicMock()
            return mock

        engine.forecast_material_demand = forecast_side

        result = engine.batch_forecast_for_project(project_id=1)
        assert len(result) == 2  # 1 and 3 succeed, 2 fails

    def test_batch_forecast_empty_project(self, engine):
        """项目无物料时返回空列表"""
        engine.db.query.return_value.filter.return_value.all.return_value = []
        result = engine.batch_forecast_for_project(project_id=99)
        assert result == []


# ======================= get_forecast_accuracy_report =======================

class TestGetForecastAccuracyReport:
    def test_empty_forecasts_returns_zeros(self, engine):
        engine.db.query.return_value.filter.return_value.all.return_value = []
        result = engine.get_forecast_accuracy_report()
        assert result["total_forecasts"] == 0
        assert result["average_accuracy"] == 0
        assert result["within_ci_rate"] == 0

    def test_report_with_validated_forecasts(self, engine):
        f1 = MagicMock()
        f1.accuracy_score = Decimal("85")
        f1.mape = Decimal("15")
        f1.lower_bound = Decimal("80")
        f1.upper_bound = Decimal("120")
        f1.actual_demand = Decimal("100")
        f1.algorithm = "EXP_SMOOTHING"

        f2 = MagicMock()
        f2.accuracy_score = Decimal("70")
        f2.mape = Decimal("30")
        f2.lower_bound = Decimal("60")
        f2.upper_bound = Decimal("90")
        f2.actual_demand = Decimal("100")  # outside [60,90] → not in CI
        f2.algorithm = "MOVING_AVERAGE"

        engine.db.query.return_value.filter.return_value.all.return_value = [f1, f2]

        result = engine.get_forecast_accuracy_report()
        assert result["total_forecasts"] == 2
        assert result["average_accuracy"] == pytest.approx(77.5)
        assert result["average_mape"] == pytest.approx(22.5)

    def test_report_filtered_by_material_id(self, engine):
        """material_id 过滤参数被传递"""
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        engine.db.query.return_value = q

        result = engine.get_forecast_accuracy_report(material_id=5, days=60)
        assert result["total_forecasts"] == 0

    def test_within_ci_rate_calculation(self, engine):
        """正确计算置信区间命中率"""
        f_in = MagicMock()
        f_in.accuracy_score = Decimal("90")
        f_in.mape = Decimal("10")
        f_in.lower_bound = Decimal("90")
        f_in.upper_bound = Decimal("110")
        f_in.actual_demand = Decimal("100")  # within [90, 110]
        f_in.algorithm = "EXP_SMOOTHING"

        f_out = MagicMock()
        f_out.accuracy_score = Decimal("50")
        f_out.mape = Decimal("50")
        f_out.lower_bound = Decimal("90")
        f_out.upper_bound = Decimal("110")
        f_out.actual_demand = Decimal("200")  # outside
        f_out.algorithm = "EXP_SMOOTHING"

        engine.db.query.return_value.filter.return_value.all.return_value = [f_in, f_out]
        result = engine.get_forecast_accuracy_report()
        assert result["within_ci_rate"] == 50.0  # 1/2


# ======================= _generate_forecast_no =======================

class TestGenerateForecastNo:
    def test_generates_formatted_no(self, engine):
        engine.db.query.return_value.filter.return_value.scalar.return_value = 0
        no = engine._generate_forecast_no()
        assert no.startswith("FC")
        assert len(no) > 8

    def test_increments_counter(self, engine):
        engine.db.query.return_value.filter.return_value.scalar.return_value = 3
        no = engine._generate_forecast_no()
        assert no.endswith("0004")
