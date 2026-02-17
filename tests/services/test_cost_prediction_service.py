# -*- coding: utf-8 -*-
"""成本预测服务单元测试 (CostPredictionService / GLM5CostPredictor)"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


def _make_evm(**kw):
    evm = MagicMock()
    defaults = dict(
        id=1,
        project_id=1,
        period_date=date(2024, 3, 31),
        budget_at_completion=Decimal("500000"),
        planned_value=Decimal("250000"),
        earned_value=Decimal("200000"),
        actual_cost=Decimal("220000"),
        cost_performance_index=Decimal("0.91"),
        schedule_performance_index=Decimal("0.80"),
        actual_percent_complete=Decimal("40"),
        is_verified=True,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(evm, k, v)
    return evm


def _make_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=1,
        project_name="比亚迪ADAS ICT测试系统",
        project_code="BYD-2024-001",
        planned_start_date=date(2024, 1, 1),
        planned_end_date=date(2024, 12, 31),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


class TestCostPredictionServiceInit:
    def test_init_without_api_key(self):
        """无API密钥时ai_predictor应为None"""
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        with patch.dict('os.environ', {}, clear=True):
            # 删除GLM_API_KEY确保无法初始化ai_predictor
            import os
            os.environ.pop('GLM_API_KEY', None)
            svc = CostPredictionService(db)
        assert svc.db is db
        assert svc.ai_predictor is None

    def test_init_with_api_key(self):
        """有API密钥时ai_predictor应被初始化"""
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        with patch('app.services.cost_prediction_service.GLM5CostPredictor') as mock_glm:
            mock_glm.return_value = MagicMock()
            svc = CostPredictionService(db, glm_api_key="test-key")
        assert svc.ai_predictor is not None


class TestTraditionalEACPrediction:
    def _make_svc(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        import os
        os.environ.pop('GLM_API_KEY', None)
        return CostPredictionService(db)

    def test_normal_cpi_eac(self):
        svc = self._make_svc()
        evm = _make_evm(
            budget_at_completion=Decimal("500000"),
            actual_cost=Decimal("220000"),
            earned_value=Decimal("200000"),
            cost_performance_index=Decimal("0.91"),
        )
        result = svc._traditional_eac_prediction(evm)
        assert "predicted_eac" in result
        assert result["predicted_eac"] > 0
        assert result["confidence"] == 70.0
        assert result["eac_lower_bound"] <= result["predicted_eac"]
        assert result["eac_upper_bound"] >= result["predicted_eac"]

    def test_zero_cpi_fallback(self):
        svc = self._make_svc()
        evm = _make_evm(
            budget_at_completion=Decimal("500000"),
            actual_cost=Decimal("220000"),
            earned_value=Decimal("200000"),
            cost_performance_index=Decimal("0"),
        )
        result = svc._traditional_eac_prediction(evm)
        # 应回退到 BAC * 1.2
        assert result["predicted_eac"] == pytest.approx(600000.0, rel=0.01)


class TestTraditionalRiskAnalysis:
    def _make_svc(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        import os
        os.environ.pop('GLM_API_KEY', None)
        return CostPredictionService(db)

    def test_high_cpi_low_risk(self):
        svc = self._make_svc()
        evm = _make_evm(cost_performance_index=Decimal("1.0"))
        result = svc._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "LOW"
        assert result["overrun_probability"] == 20.0

    def test_low_cpi_critical_risk(self):
        svc = self._make_svc()
        evm = _make_evm(cost_performance_index=Decimal("0.7"))
        result = svc._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "CRITICAL"
        assert result["overrun_probability"] == 90.0

    def test_medium_cpi_medium_risk(self):
        svc = self._make_svc()
        evm = _make_evm(cost_performance_index=Decimal("0.9"))
        result = svc._traditional_risk_analysis(evm, [evm])
        assert result["risk_level"] == "MEDIUM"


class TestCalculateDataQuality:
    def _make_svc(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        import os
        os.environ.pop('GLM_API_KEY', None)
        return CostPredictionService(db)

    def test_no_history_deducts_30(self):
        svc = self._make_svc()
        result = svc._calculate_data_quality([])
        assert result == Decimal("70")

    def test_sufficient_history_full_score(self):
        svc = self._make_svc()
        evms = [_make_evm(is_verified=True) for _ in range(6)]
        result = svc._calculate_data_quality(evms)
        assert result == Decimal("100")


class TestGetLatestPrediction:
    def test_returns_latest_prediction(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        mock_prediction = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prediction
        import os
        os.environ.pop('GLM_API_KEY', None)
        svc = CostPredictionService(db)
        result = svc.get_latest_prediction(project_id=1)
        assert result is mock_prediction

    def test_returns_none_when_no_prediction(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        import os
        os.environ.pop('GLM_API_KEY', None)
        svc = CostPredictionService(db)
        result = svc.get_latest_prediction(project_id=999)
        assert result is None


class TestCreatePredictionValidation:
    def test_project_not_found_raises(self):
        from app.services.cost_prediction_service import CostPredictionService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        import os
        os.environ.pop('GLM_API_KEY', None)
        svc = CostPredictionService(db)
        with pytest.raises(ValueError, match="项目不存在"):
            svc.create_prediction(project_id=999)
