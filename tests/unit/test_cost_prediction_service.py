# -*- coding: utf-8 -*-
"""
成本预测服务单元测试
覆盖传统EAC预测、风险分析、数据质量评分等核心方法
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.cost_prediction_service import CostPredictionService


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    with patch("app.services.cost_prediction_service.EVMCalculator"):
        svc = CostPredictionService(db=mock_db, glm_api_key="fake-key")
    svc.ai_predictor = None  # 禁用AI
    return svc


def make_evm_data(cpi=None, bac=1000, ac=500, ev=400, is_verified=True):
    evm = MagicMock()
    evm.cost_performance_index = Decimal(str(cpi)) if cpi is not None else None
    evm.budget_at_completion = Decimal(str(bac))
    evm.actual_cost = Decimal(str(ac))
    evm.earned_value = Decimal(str(ev))
    evm.is_verified = is_verified
    return evm


class TestTraditionalEACPrediction:
    """_traditional_eac_prediction 传统EAC预测"""

    def test_standard_eac_formula(self, service):
        # EAC = AC + (BAC - EV) / CPI = 500 + (1000-400)/0.8 = 500+750 = 1250
        evm = make_evm_data(cpi=0.8, bac=1000, ac=500, ev=400)
        result = service._traditional_eac_prediction(evm)
        assert result["predicted_eac"] == pytest.approx(1250.0, rel=1e-3)
        assert result["confidence"] == 70.0

    def test_none_cpi_triggers_fallback_path(self, service):
        # CPI=None 由 `or Decimal('1')` 处理为1，EAC = AC + (BAC - EV) / 1
        evm = make_evm_data(cpi=None, bac=1000, ac=500, ev=400)
        result = service._traditional_eac_prediction(evm)
        # EAC = 500 + (1000-400)/1 = 1100
        assert result["predicted_eac"] == pytest.approx(1100.0)

    def test_low_cpi_raises_eac_significantly(self, service):
        # CPI=0.5 → EAC = 500 + (1000-400)/0.5 = 1700
        evm = make_evm_data(cpi=0.5, bac=1000, ac=500, ev=400)
        result = service._traditional_eac_prediction(evm)
        assert result["predicted_eac"] == pytest.approx(1700.0, rel=1e-3)

    def test_bounds_are_around_prediction(self, service):
        evm = make_evm_data(cpi=1.0, bac=1000, ac=500, ev=500)
        result = service._traditional_eac_prediction(evm)
        assert result["eac_lower_bound"] < result["predicted_eac"]
        assert result["eac_upper_bound"] > result["predicted_eac"]


class TestTraditionalRiskAnalysis:
    """_traditional_risk_analysis 传统风险分析"""

    def test_low_risk_when_cpi_above_095(self, service):
        evm = make_evm_data(cpi=1.0)
        result = service._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "LOW"
        assert result["overrun_probability"] == 20.0

    def test_medium_risk_when_cpi_085_to_095(self, service):
        evm = make_evm_data(cpi=0.90)
        result = service._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "MEDIUM"
        assert result["overrun_probability"] == 50.0

    def test_high_risk_when_cpi_075_to_085(self, service):
        evm = make_evm_data(cpi=0.80)
        result = service._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "HIGH"
        assert result["overrun_probability"] == 75.0

    def test_critical_risk_when_cpi_below_075(self, service):
        evm = make_evm_data(cpi=0.70)
        result = service._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "CRITICAL"
        assert result["overrun_probability"] == 90.0

    def test_risk_score_inverse_of_cpi(self, service):
        evm_low_cpi = make_evm_data(cpi=0.7)
        evm_high_cpi = make_evm_data(cpi=1.0)
        r1 = service._traditional_risk_analysis(evm_low_cpi, [])
        r2 = service._traditional_risk_analysis(evm_high_cpi, [])
        assert r1["risk_score"] > r2["risk_score"]


class TestCalculateDataQuality:
    """_calculate_data_quality 数据质量评分"""

    def test_full_score_with_rich_verified_data(self, service):
        history = [make_evm_data(is_verified=True) for _ in range(6)]
        score = service._calculate_data_quality(history)
        assert score == Decimal("100")

    def test_penalty_for_insufficient_history(self, service):
        history = [make_evm_data(is_verified=True) for _ in range(2)]
        score = service._calculate_data_quality(history)
        assert score == Decimal("70")  # -30 for < 3 records

    def test_penalty_for_unverified_records(self, service):
        history = [make_evm_data(is_verified=False) for _ in range(6)]
        score = service._calculate_data_quality(history)
        # -5 per unverified record × 6 = -30
        assert score == Decimal("70")

    def test_score_never_below_zero(self, service):
        history = [make_evm_data(is_verified=False) for _ in range(30)]
        score = service._calculate_data_quality(history)
        assert score >= Decimal("0")
