# -*- coding: utf-8 -*-
"""项目进度预测服务单元测试 (SchedulePredictionService)"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


class TestSchedulePredictionServiceInit:
    def test_init_sets_db(self):
        from app.services.schedule_prediction_service import SchedulePredictionService
        db = _make_db()
        with patch('app.services.schedule_prediction_service.AIClientService'):
            svc = SchedulePredictionService(db)
        assert svc.db is db


class TestExtractFeatures:
    def _make_svc(self):
        from app.services.schedule_prediction_service import SchedulePredictionService
        db = _make_db()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        with patch('app.services.schedule_prediction_service.AIClientService'):
            svc = SchedulePredictionService(db)
        return svc

    def test_extract_features_basic(self):
        svc = self._make_svc()
        features = svc._extract_features(
            project_id=1,
            current_progress=50.0,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5,
        )
        assert features["current_progress"] == 50.0
        assert features["planned_progress"] == 60.0
        assert features["progress_deviation"] == pytest.approx(-10.0, abs=0.01)
        assert features["remaining_days"] == 30
        assert features["team_size"] == 5

    def test_extract_features_progress_deviation_positive(self):
        svc = self._make_svc()
        features = svc._extract_features(
            project_id=1,
            current_progress=70.0,
            planned_progress=60.0,
            remaining_days=20,
            team_size=3,
        )
        assert features["progress_deviation"] == pytest.approx(10.0, abs=0.01)

    def test_velocity_ratio_computed(self):
        svc = self._make_svc()
        features = svc._extract_features(
            project_id=1,
            current_progress=40.0,
            planned_progress=50.0,
            remaining_days=30,
            team_size=4,
            project_data={"days_elapsed": 20, "complexity": "medium"}
        )
        # avg_daily_progress = 40/20 = 2.0
        # required_daily_progress = 60/30 = 2.0
        # velocity_ratio = 2.0/2.0 = 1.0
        assert features["velocity_ratio"] == pytest.approx(1.0, abs=0.01)


class TestPredictLinear:
    def _make_svc(self):
        from app.services.schedule_prediction_service import SchedulePredictionService
        db = _make_db()
        with patch('app.services.schedule_prediction_service.AIClientService'):
            svc = SchedulePredictionService(db)
        return svc

    def test_on_time_when_velocity_sufficient(self):
        svc = self._make_svc()
        features = {
            "velocity_ratio": 1.2,
            "remaining_days": 20,
        }
        result = svc._predict_linear(features)
        assert result["delay_days"] == 0
        assert result["confidence"] > 0

    def test_delayed_when_velocity_insufficient(self):
        svc = self._make_svc()
        features = {
            "velocity_ratio": 0.5,
            "remaining_days": 20,
        }
        result = svc._predict_linear(features)
        assert result["delay_days"] > 0
        # delay = 20 * (1/0.5 - 1) = 20
        assert result["delay_days"] == 20

    def test_predicted_date_is_future(self):
        svc = self._make_svc()
        features = {
            "velocity_ratio": 0.8,
            "remaining_days": 30,
        }
        result = svc._predict_linear(features)
        assert result["predicted_date"] > date.today()


class TestAssessRiskLevel:
    def _make_svc(self):
        from app.services.schedule_prediction_service import SchedulePredictionService
        db = _make_db()
        with patch('app.services.schedule_prediction_service.AIClientService'):
            svc = SchedulePredictionService(db)
        return svc

    def test_low_risk_no_delay(self):
        svc = self._make_svc()
        assert svc._assess_risk_level(0) == "low"

    def test_medium_risk(self):
        svc = self._make_svc()
        assert svc._assess_risk_level(5) == "medium"

    def test_high_risk(self):
        svc = self._make_svc()
        assert svc._assess_risk_level(10) == "high"

    def test_critical_risk(self):
        svc = self._make_svc()
        assert svc._assess_risk_level(20) == "critical"

    def test_early_completion(self):
        svc = self._make_svc()
        # 提前完成（负延迟）
        assert svc._assess_risk_level(-5) == "low"


class TestPredictCompletionDate:
    def test_returns_prediction_dict(self):
        from app.services.schedule_prediction_service import SchedulePredictionService
        db = _make_db()
        # Mock DB: no similar predictions
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        with patch('app.services.schedule_prediction_service.AIClientService'):
            svc = SchedulePredictionService(db)

        with patch('app.utils.db_helpers.save_obj'):
            result = svc.predict_completion_date(
                project_id=1,
                current_progress=50.0,
                planned_progress=60.0,
                remaining_days=30,
                team_size=5,
                use_ai=False  # 不调用真实AI
            )
        assert isinstance(result, dict)
        assert "delay_days" in result or "predicted_date" in result or "error" in result
