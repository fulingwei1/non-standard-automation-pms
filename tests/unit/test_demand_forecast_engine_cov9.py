# -*- coding: utf-8 -*-
"""第九批: test_demand_forecast_engine_cov9.py - DemandForecastEngine 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date, timedelta

pytest.importorskip("app.services.shortage.demand_forecast_engine")

from app.services.shortage.demand_forecast_engine import DemandForecastEngine


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def engine(mock_db):
    return DemandForecastEngine(db=mock_db)


class TestDemandForecastEngineInit:
    def test_init(self, engine, mock_db):
        assert engine.db is mock_db


class TestCalculateAverage:
    """测试均值计算"""

    def test_calculate_average_normal(self, engine):
        data = [Decimal("10"), Decimal("20"), Decimal("30")]
        result = engine._calculate_average(data)
        assert result == Decimal("20")

    def test_calculate_average_empty(self, engine):
        result = engine._calculate_average([])
        assert result == Decimal("0")

    def test_calculate_average_single(self, engine):
        data = [Decimal("15")]
        result = engine._calculate_average(data)
        assert result == Decimal("15")


class TestCalculateStd:
    """测试标准差计算"""

    def test_calculate_std_uniform(self, engine):
        data = [Decimal("10"), Decimal("10"), Decimal("10")]
        result = engine._calculate_std(data)
        assert result == Decimal("0")

    def test_calculate_std_varied(self, engine):
        data = [Decimal("5"), Decimal("10"), Decimal("15")]
        result = engine._calculate_std(data)
        assert result > Decimal("0")

    def test_calculate_std_single(self, engine):
        result = engine._calculate_std([Decimal("5")])
        assert result == Decimal("0")


class TestMovingAverageForecast:
    """测试移动平均预测"""

    def test_moving_average_basic(self, engine):
        data = [Decimal("10"), Decimal("12"), Decimal("14"), Decimal("16"), Decimal("18")]
        result = engine._moving_average_forecast(data, window=3)
        assert isinstance(result, Decimal)
        assert result > Decimal("0")

    def test_moving_average_insufficient_data(self, engine):
        data = [Decimal("10")]
        result = engine._moving_average_forecast(data, window=3)
        assert isinstance(result, Decimal)


class TestExponentialSmoothingForecast:
    """测试指数平滑预测"""

    def test_exp_smoothing_basic(self, engine):
        data = [Decimal("10"), Decimal("12"), Decimal("11"), Decimal("13")]
        result = engine._exponential_smoothing_forecast(data)
        assert isinstance(result, Decimal)
        assert result > Decimal("0")

    def test_exp_smoothing_single(self, engine):
        data = [Decimal("20")]
        result = engine._exponential_smoothing_forecast(data)
        assert result == Decimal("20")


class TestLinearRegressionForecast:
    """测试线性回归预测"""

    def test_linear_regression_increasing(self, engine):
        data = [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40")]
        result = engine._linear_regression_forecast(data)
        assert isinstance(result, Decimal)
        assert result > Decimal("30")  # Should extrapolate upward


class TestGenerateForecastNo:
    """测试预测编号生成"""

    def test_generate_forecast_no(self, engine, mock_db):
        # Uses query(func.count()).filter().scalar()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 3
        result = engine._generate_forecast_no()
        assert isinstance(result, str)
        assert result.startswith("FC")
        assert len(result) > 0


class TestBatchForecastForProject:
    """测试批量预测"""

    def test_batch_forecast_returns_list(self, engine, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = engine.batch_forecast_for_project(project_id=1)
        assert isinstance(result, list)


class TestDetectSeasonality:
    """测试季节性检测"""

    def test_detect_seasonality_flat(self, engine):
        data = [Decimal("10")] * 12
        result = engine._detect_seasonality(data)
        assert isinstance(result, Decimal)

    def test_detect_seasonality_varied(self, engine):
        data = [Decimal(str(i * 5)) for i in range(1, 13)]
        result = engine._detect_seasonality(data)
        assert result >= Decimal("0")
