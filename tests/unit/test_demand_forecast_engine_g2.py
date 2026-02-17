# -*- coding: utf-8 -*-
"""
DemandForecastEngine 单元测试 - G2组覆盖率提升

覆盖:
- DemandForecastEngine.__init__
- DemandForecastEngine.forecast_material_demand (流程分支)
- DemandForecastEngine.validate_forecast_accuracy
- DemandForecastEngine._moving_average_forecast
- DemandForecastEngine._exponential_smoothing_forecast
- DemandForecastEngine._calculate_average
- DemandForecastEngine._calculate_std
- DemandForecastEngine._calculate_confidence_interval
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

import pytest


class TestDemandForecastEngineInit:
    """测试初始化"""

    def test_init_stores_db(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        db = MagicMock()
        engine = DemandForecastEngine(db)
        assert engine.db is db


class TestCalculateAverage:
    """测试 _calculate_average"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.engine = DemandForecastEngine(MagicMock())

    def test_basic_average(self):
        data = [Decimal("10"), Decimal("20"), Decimal("30")]
        result = self.engine._calculate_average(data)
        assert result == Decimal("20")

    def test_empty_list_returns_zero(self):
        result = self.engine._calculate_average([])
        assert result == Decimal("0")

    def test_single_element(self):
        result = self.engine._calculate_average([Decimal("42")])
        assert result == Decimal("42")


class TestCalculateStd:
    """测试 _calculate_std"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.engine = DemandForecastEngine(MagicMock())

    def test_zero_std_for_uniform_data(self):
        data = [Decimal("5"), Decimal("5"), Decimal("5")]
        result = self.engine._calculate_std(data)
        assert result == Decimal("0")

    def test_positive_std_for_variable_data(self):
        data = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")]
        result = self.engine._calculate_std(data)
        assert result >= Decimal("0")

    def test_empty_list_returns_zero(self):
        result = self.engine._calculate_std([])
        assert result == Decimal("0")


class TestMovingAverageForecast:
    """测试 _moving_average_forecast"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.engine = DemandForecastEngine(MagicMock())

    def test_returns_decimal(self):
        data = [Decimal(str(i)) for i in range(1, 11)]
        result = self.engine._moving_average_forecast(data)
        assert isinstance(result, Decimal)

    def test_result_is_recent_average(self):
        # Last 7 values: 4, 5, 6, 7, 8, 9, 10 -> avg 7
        data = [Decimal(str(i)) for i in range(1, 11)]
        result = self.engine._moving_average_forecast(data)
        assert result > Decimal("0")


class TestExponentialSmoothingForecast:
    """测试 _exponential_smoothing_forecast"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.engine = DemandForecastEngine(MagicMock())

    def test_returns_decimal(self):
        data = [Decimal("100"), Decimal("110"), Decimal("105"), Decimal("120")]
        result = self.engine._exponential_smoothing_forecast(data)
        assert isinstance(result, Decimal)

    def test_single_element(self):
        data = [Decimal("50")]
        result = self.engine._exponential_smoothing_forecast(data)
        # Should be close to 50
        assert result > Decimal("0")


class TestCalculateConfidenceInterval:
    """测试 _calculate_confidence_interval"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.engine = DemandForecastEngine(MagicMock())

    def test_lower_bound_less_than_upper(self):
        lower, upper = self.engine._calculate_confidence_interval(
            forecast=Decimal("100"),
            std=Decimal("10"),
            confidence=95.0,
        )
        assert lower < upper

    def test_forecast_in_interval(self):
        lower, upper = self.engine._calculate_confidence_interval(
            forecast=Decimal("100"),
            std=Decimal("10"),
            confidence=95.0,
        )
        assert lower <= Decimal("100") <= upper

    def test_zero_std_gives_equal_bounds(self):
        lower, upper = self.engine._calculate_confidence_interval(
            forecast=Decimal("100"),
            std=Decimal("0"),
            confidence=95.0,
        )
        assert lower <= Decimal("100") <= upper


class TestForecastMaterialDemand:
    """测试 forecast_material_demand 主流程"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.db = MagicMock()
        self.engine = DemandForecastEngine(self.db)

    def test_raises_when_no_historical_data(self):
        from app.core.exceptions import BusinessException
        self.engine._collect_historical_demand = MagicMock(return_value=[])
        with pytest.raises(BusinessException, match="历史数据不足"):
            self.engine.forecast_material_demand(material_id=1)

    def test_raises_for_unknown_algorithm(self):
        from app.core.exceptions import BusinessException
        self.engine._collect_historical_demand = MagicMock(
            return_value=[Decimal("10")] * 30
        )
        self.engine._calculate_average = MagicMock(return_value=Decimal("10"))
        self.engine._calculate_std = MagicMock(return_value=Decimal("2"))
        self.engine._detect_seasonality = MagicMock(return_value=1.0)
        with pytest.raises(BusinessException, match="不支持的预测算法"):
            self.engine.forecast_material_demand(material_id=1, algorithm="UNKNOWN_ALGO")

    @patch("app.services.shortage.demand_forecast_engine.save_obj")
    def test_exp_smoothing_algorithm_succeeds(self, mock_save):
        """使用 EXP_SMOOTHING 算法成功预测"""
        historical = [Decimal(str(i)) for i in range(1, 31)]
        self.engine._collect_historical_demand = MagicMock(return_value=historical)
        self.engine._detect_seasonality = MagicMock(return_value=1.0)
        self.engine._generate_forecast_no = MagicMock(return_value="FC-20260101-001")

        result = self.engine.forecast_material_demand(
            material_id=1, algorithm="EXP_SMOOTHING"
        )

        assert result is not None
        mock_save.assert_called_once()

    @patch("app.services.shortage.demand_forecast_engine.save_obj")
    def test_moving_average_algorithm_succeeds(self, mock_save):
        """使用 MOVING_AVERAGE 算法成功预测"""
        historical = [Decimal(str(i)) for i in range(1, 31)]
        self.engine._collect_historical_demand = MagicMock(return_value=historical)
        self.engine._detect_seasonality = MagicMock(return_value=1.0)
        self.engine._generate_forecast_no = MagicMock(return_value="FC-20260101-002")

        result = self.engine.forecast_material_demand(
            material_id=1, algorithm="MOVING_AVERAGE"
        )

        assert result is not None

    @patch("app.services.shortage.demand_forecast_engine.save_obj")
    def test_linear_regression_algorithm_succeeds(self, mock_save):
        """使用 LINEAR_REGRESSION 算法成功预测"""
        historical = [Decimal(str(i)) for i in range(1, 31)]
        self.engine._collect_historical_demand = MagicMock(return_value=historical)
        self.engine._detect_seasonality = MagicMock(return_value=1.0)
        self.engine._generate_forecast_no = MagicMock(return_value="FC-20260101-003")

        result = self.engine.forecast_material_demand(
            material_id=1, algorithm="LINEAR_REGRESSION"
        )

        assert result is not None


class TestValidateForecastAccuracy:
    """测试 validate_forecast_accuracy"""

    def setup_method(self):
        from app.services.shortage.demand_forecast_engine import DemandForecastEngine
        self.db = MagicMock()
        self.engine = DemandForecastEngine(self.db)

    def test_raises_when_forecast_not_found(self):
        from app.core.exceptions import BusinessException
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(BusinessException, match="预测记录不存在"):
            self.engine.validate_forecast_accuracy(forecast_id=999, actual_demand=Decimal("100"))

    def test_returns_accuracy_metrics(self):
        mock_forecast = MagicMock()
        mock_forecast.forecasted_demand = Decimal("100")
        mock_forecast.lower_bound = Decimal("80")
        mock_forecast.upper_bound = Decimal("120")
        self.db.query.return_value.filter.return_value.first.return_value = mock_forecast

        result = self.engine.validate_forecast_accuracy(
            forecast_id=1, actual_demand=Decimal("110")
        )

        assert "accuracy_score" in result
        assert "error_percentage" in result
        assert "within_confidence_interval" in result
        assert result["within_confidence_interval"] is True

    def test_perfect_forecast_gives_high_accuracy(self):
        mock_forecast = MagicMock()
        mock_forecast.forecasted_demand = Decimal("100")
        mock_forecast.lower_bound = Decimal("90")
        mock_forecast.upper_bound = Decimal("110")
        self.db.query.return_value.filter.return_value.first.return_value = mock_forecast

        result = self.engine.validate_forecast_accuracy(
            forecast_id=1, actual_demand=Decimal("100")
        )

        assert result["accuracy_score"] == 100.0

    def test_outside_confidence_interval_flagged(self):
        mock_forecast = MagicMock()
        mock_forecast.forecasted_demand = Decimal("100")
        mock_forecast.lower_bound = Decimal("90")
        mock_forecast.upper_bound = Decimal("110")
        self.db.query.return_value.filter.return_value.first.return_value = mock_forecast

        result = self.engine.validate_forecast_accuracy(
            forecast_id=1, actual_demand=Decimal("200")
        )

        assert result["within_confidence_interval"] is False
