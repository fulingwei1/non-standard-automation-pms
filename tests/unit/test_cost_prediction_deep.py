# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 成本预测服务"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.cost.cost_prediction_service import CostPredictionService, GLM5CostPredictor


class TestGLM5CostPredictorDeep:
    def test_parse_eac_prediction_with_embedded_json(self):
        predictor = GLM5CostPredictor(api_key="test-key")
        response = '分析如下```json {"predicted_eac": 1200, "confidence": 88, "prediction_method": "AI"} ```'

        result = predictor._parse_eac_prediction(response, {"bac": 1000})

        assert result["predicted_eac"] == 1200.0
        assert result["confidence"] == 88.0
        assert result["prediction_method"] == "AI"
        assert result["eac_most_likely"] == 1200.0

    def test_parse_eac_prediction_fallback_when_json_invalid(self):
        predictor = GLM5CostPredictor(api_key="test-key")

        result = predictor._parse_eac_prediction(
            "not-json",
            {"bac": 1000, "current_cpi": 0, "current_ac": 200, "current_ev": 100},
        )

        assert result["prediction_method"] == "CPI_BASED_FALLBACK"
        assert result["predicted_eac"] == 1200.0
        assert result["confidence"] == 50.0

    def test_parse_risk_analysis_fallback(self):
        predictor = GLM5CostPredictor(api_key="test-key")

        result = predictor._parse_risk_analysis("oops")

        assert result["risk_level"] == "MEDIUM"
        assert result["overrun_probability"] == 50.0
        assert result["key_concerns"] == ["AI风险分析不可用"]

    def test_parse_optimization_suggestions_wraps_dict(self):
        predictor = GLM5CostPredictor(api_key="test-key")

        result = predictor._parse_optimization_suggestions('{"title": "降本", "type": "PROCESS_IMPROVEMENT"}')

        assert isinstance(result, list)
        assert result[0]["title"] == "降本"

    def test_summarize_evm_history_detects_improving_trend(self):
        predictor = GLM5CostPredictor(api_key="test-key")
        history = [
            {"period": "2026-01", "cpi": 0.8, "spi": 0.9, "ac": 100, "ev": 80},
            {"period": "2026-02", "cpi": 0.9, "spi": 0.95, "ac": 200, "ev": 180},
            {"period": "2026-03", "cpi": 1.0, "spi": 1.0, "ac": 300, "ev": 300},
        ]

        summary = predictor._summarize_evm_history(history)

        assert "CPI持续上升" in summary
        assert "2026-03" in summary


class TestCostPredictionServiceDeep:
    def test_traditional_eac_prediction_with_positive_cpi(self):
        service = CostPredictionService(Mock(), glm_api_key=None)
        latest_evm = SimpleNamespace(
            cost_performance_index=Decimal("0.8"),
            budget_at_completion=Decimal("1000"),
            actual_cost=Decimal("400"),
            earned_value=Decimal("300"),
        )

        result = service._traditional_eac_prediction(latest_evm)

        assert result["predicted_eac"] == 1275.0
        assert result["confidence"] == 70.0

    @pytest.mark.parametrize(
        ("cpi", "expected_level", "expected_probability"),
        [
            (Decimal("0.96"), "LOW", 20.0),
            (Decimal("0.90"), "MEDIUM", 50.0),
            (Decimal("0.80"), "HIGH", 75.0),
            (Decimal("0.70"), "CRITICAL", 90.0),
        ],
    )
    def test_traditional_risk_analysis_thresholds(self, cpi, expected_level, expected_probability):
        service = CostPredictionService(Mock(), glm_api_key=None)
        latest_evm = SimpleNamespace(cost_performance_index=cpi)

        result = service._traditional_risk_analysis(latest_evm, [])

        assert result["risk_level"] == expected_level
        assert result["overrun_probability"] == expected_probability

    def test_calculate_data_quality_penalizes_short_and_unverified_history(self):
        service = CostPredictionService(Mock(), glm_api_key=None)
        history = [
            SimpleNamespace(is_verified=True),
            SimpleNamespace(is_verified=False),
        ]

        result = service._calculate_data_quality(history)

        assert result == Decimal("65")

    def test_generate_optimization_suggestions_creates_records(self):
        db = Mock()
        service = CostPredictionService(db, glm_api_key=None)
        service.ai_predictor = Mock()
        service.ai_predictor.generate_optimization_suggestions.return_value = [
            {
                "title": "压缩外协",
                "type": "PROCESS_IMPROVEMENT",
                "priority": "HIGH",
                "description": "优化外协成本",
                "current_situation": "外协偏高",
                "proposed_action": "重新议价",
                "implementation_steps": [{"step": 1, "action": "议价"}],
                "estimated_cost_saving": 1000,
                "implementation_cost": 200,
                "impact_on_schedule": "NEUTRAL",
                "impact_on_quality": "NEUTRAL",
                "implementation_risk": "LOW",
                "ai_confidence_score": 80,
                "ai_reasoning": "可行",
            }
        ]
        prediction = SimpleNamespace(
            id=1,
            project_id=2,
            project_code="P001",
            prediction_date=date(2026, 4, 12),
            created_by=9,
        )

        with patch(
            "app.services.cost.cost_prediction_service.CostOptimizationSuggestion",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            service._generate_optimization_suggestions(prediction, {}, {}, {})

        db.add.assert_called_once()
        db.commit.assert_called_once()
        added = db.add.call_args.args[0]
        assert added.suggestion_code == "OPT-P001-202604-001"
        assert added.net_benefit == Decimal("800")
        assert added.roi_percentage == Decimal("400")

    def test_generate_optimization_suggestions_swallows_errors(self):
        service = CostPredictionService(Mock(), glm_api_key=None)
        service.ai_predictor = Mock()
        service.ai_predictor.generate_optimization_suggestions.side_effect = RuntimeError("boom")

        service._generate_optimization_suggestions(
            SimpleNamespace(project_code="P001", prediction_date=date(2026, 4, 12), created_by=1),
            {},
            {},
            {},
        )

    def test_get_prediction_history_applies_limit(self):
        query = Mock()
        query.filter.return_value = query
        query.order_by.return_value = query
        limited = Mock()
        limited.all.return_value = [1, 2]
        query.limit.return_value = limited
        db = Mock()
        db.query.return_value = query
        service = CostPredictionService(db, glm_api_key=None)

        result = service.get_prediction_history(project_id=1, limit=2)

        assert result == [1, 2]
        query.limit.assert_called_once_with(2)
