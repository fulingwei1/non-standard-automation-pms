# -*- coding: utf-8 -*-
"""
N1组深度覆盖: CostPredictionService / GLM5CostPredictor
补充 _traditional_risk_analysis, _calculate_data_quality,
get_latest_prediction, get_prediction_history,
GLM5CostPredictor._parse_* / _summarize_evm_history 等分支
"""
import json
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.cost_prediction_service import (
    CostPredictionService,
    GLM5CostPredictor,
)


# ============================================================
# Helper builders
# ============================================================

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.cost_prediction_service.EVMCalculator"):
        svc = CostPredictionService(db=mock_db, glm_api_key="fake-key")
    svc.ai_predictor = None  # 禁用 AI
    return svc


def make_evm_data(cpi=1.0, bac=1000, ac=500, ev=400, is_verified=True, pv=600):
    evm = MagicMock()
    evm.cost_performance_index = Decimal(str(cpi))
    evm.budget_at_completion = Decimal(str(bac))
    evm.actual_cost = Decimal(str(ac))
    evm.earned_value = Decimal(str(ev))
    evm.planned_value = Decimal(str(pv))
    evm.schedule_performance_index = Decimal("1.0")
    evm.actual_percent_complete = Decimal("50")
    evm.is_verified = is_verified
    return evm


def make_predictor():
    return GLM5CostPredictor(api_key="fake-key")


# ============================================================
# 1. _traditional_risk_analysis - 4个风险等级分支
# ============================================================

class TestTraditionalRiskAnalysis:
    def test_low_risk_when_cpi_high(self, service):
        evm = make_evm_data(cpi=1.0)
        result = service._traditional_risk_analysis(evm, [])
        assert result["risk_level"] == "LOW"
        assert result["overrun_probability"] == 20.0

    def test_medium_risk(self, service):
        evm = make_evm_data(cpi=0.90)
        result = service._traditional_risk_analysis(evm, [])
        assert result["risk_level"] == "MEDIUM"
        assert result["overrun_probability"] == 50.0

    def test_high_risk(self, service):
        evm = make_evm_data(cpi=0.80)
        result = service._traditional_risk_analysis(evm, [])
        assert result["risk_level"] == "HIGH"
        assert result["overrun_probability"] == 75.0

    def test_critical_risk_when_cpi_very_low(self, service):
        evm = make_evm_data(cpi=0.70)
        result = service._traditional_risk_analysis(evm, [])
        assert result["risk_level"] == "CRITICAL"
        assert result["overrun_probability"] == 90.0

    def test_risk_score_formula(self, service):
        evm = make_evm_data(cpi=0.8)
        result = service._traditional_risk_analysis(evm, [])
        # risk_score = 100 - cpi*100 = 100 - 80 = 20
        assert result["risk_score"] == pytest.approx(20.0, rel=1e-3)

    def test_has_required_keys(self, service):
        evm = make_evm_data(cpi=0.9)
        result = service._traditional_risk_analysis(evm, [])
        for key in ["overrun_probability", "risk_level", "risk_score",
                    "risk_factors", "trend_analysis", "cost_trend",
                    "key_concerns", "early_warning_signals"]:
            assert key in result


# ============================================================
# 2. _calculate_data_quality - 不同数量/验证状态
# ============================================================

class TestCalculateDataQuality:
    def test_empty_history_penalized(self, service):
        score = service._calculate_data_quality([])
        assert score == Decimal("70")  # -30

    def test_two_records_penalized_less(self, service):
        evms = [make_evm_data() for _ in range(2)]
        score = service._calculate_data_quality(evms)
        assert score == Decimal("70")  # 只有2个, < 3

    def test_five_records_medium_penalty(self, service):
        evms = [make_evm_data(is_verified=True) for _ in range(5)]
        score = service._calculate_data_quality(evms)
        assert score == Decimal("85")  # -15

    def test_twelve_records_no_penalty(self, service):
        evms = [make_evm_data(is_verified=True) for _ in range(12)]
        score = service._calculate_data_quality(evms)
        assert score == Decimal("100")

    def test_unverified_records_penalized(self, service):
        evms = [make_evm_data(is_verified=False) for _ in range(12)]
        score = service._calculate_data_quality(evms)
        # 100 - 12*5 = 40
        assert score == Decimal("40")

    def test_score_not_below_zero(self, service):
        # 大量未验证数据不应导致负分
        evms = [make_evm_data(is_verified=False) for _ in range(30)]
        score = service._calculate_data_quality(evms)
        assert score == Decimal("0")


# ============================================================
# 3. get_latest_prediction
# ============================================================

class TestGetLatestPrediction:
    def test_found(self, service, mock_db):
        pred = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = pred
        result = service.get_latest_prediction(project_id=1)
        assert result is pred

    def test_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = service.get_latest_prediction(project_id=999)
        assert result is None


# ============================================================
# 4. get_prediction_history
# ============================================================

class TestGetPredictionHistory:
    def test_returns_list(self, service, mock_db):
        preds = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = preds
        result = service.get_prediction_history(project_id=1)
        assert len(result) == 2

    def test_with_limit(self, service, mock_db):
        preds = [MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = preds
        result = service.get_prediction_history(project_id=1, limit=1)
        assert len(result) == 1

    def test_empty_returns_list(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = service.get_prediction_history(project_id=99)
        assert result == []


# ============================================================
# 5. GLM5CostPredictor._summarize_evm_history
# ============================================================

class TestSummarizeEVMHistory:
    def test_empty_history(self):
        predictor = make_predictor()
        result = predictor._summarize_evm_history([])
        assert "无历史数据" in result

    def test_short_history(self):
        predictor = make_predictor()
        history = [
            {"period": "2025-01", "cpi": 0.9, "spi": 1.0, "ac": 500, "ev": 450}
        ]
        result = predictor._summarize_evm_history(history)
        assert "2025-01" in result

    def test_declining_cpi_detected(self):
        predictor = make_predictor()
        history = [
            {"period": f"2025-0{i}", "cpi": 1.0 - i * 0.1, "spi": 1.0, "ac": 500, "ev": 500}
            for i in range(1, 4)
        ]
        result = predictor._summarize_evm_history(history)
        assert "下降" in result

    def test_rising_cpi_detected(self):
        predictor = make_predictor()
        history = [
            {"period": f"2025-0{i}", "cpi": 0.7 + i * 0.1, "spi": 1.0, "ac": 500, "ev": 500}
            for i in range(1, 4)
        ]
        result = predictor._summarize_evm_history(history)
        assert "上升" in result

    def test_volatile_cpi_detected(self):
        predictor = make_predictor()
        history = [
            {"period": "2025-01", "cpi": 1.0, "spi": 1.0, "ac": 500, "ev": 500},
            {"period": "2025-02", "cpi": 0.7, "spi": 1.0, "ac": 500, "ev": 500},
            {"period": "2025-03", "cpi": 0.9, "spi": 1.0, "ac": 500, "ev": 500},
        ]
        result = predictor._summarize_evm_history(history)
        assert "波动" in result


# ============================================================
# 6. GLM5CostPredictor._parse_eac_prediction
# ============================================================

class TestParseEACPrediction:
    def test_valid_json_parsed(self):
        predictor = make_predictor()
        response = json.dumps({
            "predicted_eac": 1200,
            "confidence": 80,
            "prediction_method": "AI",
            "eac_lower_bound": 1100,
            "eac_upper_bound": 1300,
            "eac_most_likely": 1200,
            "reasoning": "趋势分析",
            "key_assumptions": ["CPI稳定"],
            "uncertainty_factors": ["物价波动"]
        })
        project_data = {"bac": 1000, "current_cpi": 0.9,
                        "current_ac": 500, "current_ev": 450}
        result = predictor._parse_eac_prediction(response, project_data)
        assert result["predicted_eac"] == pytest.approx(1200.0)
        assert result["confidence"] == 80.0

    def test_invalid_json_falls_back_to_cpi(self):
        predictor = make_predictor()
        project_data = {"bac": 1000, "current_cpi": 0.8,
                        "current_ac": 500, "current_ev": 400}
        result = predictor._parse_eac_prediction("invalid json", project_data)
        assert result["prediction_method"] == "CPI_BASED_FALLBACK"
        assert result["confidence"] == 50.0

    def test_zero_cpi_uses_bac_fallback(self):
        predictor = make_predictor()
        project_data = {"bac": 1000, "current_cpi": 0,
                        "current_ac": 500, "current_ev": 400}
        result = predictor._parse_eac_prediction("not json", project_data)
        # cpi=0 时 EAC = BAC * 1.2 = 1200
        assert result["predicted_eac"] == pytest.approx(1200.0)

    def test_json_with_text_wrapper(self):
        predictor = make_predictor()
        response = 'Here is the result: {"predicted_eac": 1500, "confidence": 75} done'
        project_data = {"bac": 1000, "current_cpi": 1.0,
                        "current_ac": 500, "current_ev": 450}
        result = predictor._parse_eac_prediction(response, project_data)
        assert result["predicted_eac"] == pytest.approx(1500.0)


# ============================================================
# 7. GLM5CostPredictor._parse_risk_analysis
# ============================================================

class TestParseRiskAnalysis:
    def test_valid_json(self):
        predictor = make_predictor()
        data = {
            "overrun_probability": 60,
            "risk_level": "HIGH",
            "risk_score": 70,
            "risk_factors": [{"factor": "进度延误"}],
            "trend_analysis": "CPI下降",
            "cost_trend": "DECLINING",
            "key_concerns": ["资源不足"],
            "early_warning_signals": ["CPI < 0.9"]
        }
        result = predictor._parse_risk_analysis(json.dumps(data))
        assert result["risk_level"] == "HIGH"
        assert result["overrun_probability"] == 60.0

    def test_invalid_json_returns_defaults(self):
        predictor = make_predictor()
        result = predictor._parse_risk_analysis("not json")
        assert result["risk_level"] == "MEDIUM"
        assert result["overrun_probability"] == 50.0
        assert result["cost_trend"] == "STABLE"

    def test_json_wrapped_in_text(self):
        predictor = make_predictor()
        response = 'analysis: {"overrun_probability": 30, "risk_level": "LOW"} end'
        result = predictor._parse_risk_analysis(response)
        assert result["risk_level"] == "LOW"


# ============================================================
# 8. GLM5CostPredictor._parse_optimization_suggestions
# ============================================================

class TestParseOptimizationSuggestions:
    def test_valid_list(self):
        predictor = make_predictor()
        data = [
            {"title": "优化建议1", "type": "RESOURCE_OPTIMIZATION",
             "priority": "HIGH", "description": "减少人力"}
        ]
        result = predictor._parse_optimization_suggestions(json.dumps(data))
        assert len(result) == 1
        assert result[0]["title"] == "优化建议1"

    def test_invalid_json_returns_default(self):
        predictor = make_predictor()
        result = predictor._parse_optimization_suggestions("invalid")
        assert len(result) == 1
        assert result[0]["type"] == "PROCESS_IMPROVEMENT"

    def test_dict_wrapped_in_list(self):
        """单个 dict 响应时应包装为列表"""
        predictor = make_predictor()
        data = {"title": "单条建议", "type": "SCOPE_ADJUSTMENT",
                "priority": "MEDIUM", "description": "缩小范围"}
        result = predictor._parse_optimization_suggestions(json.dumps(data))
        assert isinstance(result, list)
        assert len(result) == 1


# ============================================================
# 9. create_prediction - project not found / no evm data
# ============================================================

class TestCreatePrediction:
    def test_project_not_found_raises(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            service.create_prediction(project_id=999)

    def test_no_evm_data_raises(self, service, mock_db):
        project = MagicMock()
        # First call returns project, second call returns None (no EVM)
        mock_db.query.return_value.filter.return_value.first.side_effect = [project, None]
        with pytest.raises(ValueError, match="无EVM数据"):
            service.create_prediction(project_id=1)
