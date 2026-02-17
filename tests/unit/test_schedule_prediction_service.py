# -*- coding: utf-8 -*-
"""
进度预测服务单元测试
覆盖特征提取、线性预测、风险评级等核心逻辑
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from app.services.schedule_prediction_service import SchedulePredictionService


@pytest.fixture
def mock_db():
    db = MagicMock()
    # 默认返回空列表（无历史预测记录）
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def service(mock_db):
    with patch("app.services.schedule_prediction_service.AIClientService"):
        svc = SchedulePredictionService(db=mock_db)
    return svc


class TestExtractFeatures:
    """_extract_features 特征提取逻辑"""

    def test_progress_deviation_calculated_correctly(self, service):
        features = service._extract_features(
            project_id=1,
            current_progress=60.0,
            planned_progress=70.0,
            remaining_days=30,
            team_size=5,
        )
        assert features["progress_deviation"] == pytest.approx(-10.0, abs=0.01)

    def test_velocity_ratio_above_one_when_fast(self, service):
        # 历史日均进度 > 所需日均进度 → 比率 > 1
        features = service._extract_features(
            project_id=1,
            current_progress=80.0,
            planned_progress=50.0,
            remaining_days=5,
            team_size=10,
            project_data={"days_elapsed": 10},
        )
        # avg_daily = 80/10 = 8; required_daily = 20/5 = 4; ratio = 2.0
        assert features["velocity_ratio"] == pytest.approx(2.0, abs=0.01)

    def test_remaining_progress_complement(self, service):
        features = service._extract_features(
            project_id=1,
            current_progress=40.0,
            planned_progress=50.0,
            remaining_days=20,
            team_size=3,
        )
        assert features["remaining_progress"] == pytest.approx(60.0, abs=0.01)

    def test_zero_remaining_days_handled(self, service):
        """剩余天数为0时不应抛异常"""
        features = service._extract_features(
            project_id=1,
            current_progress=50.0,
            planned_progress=60.0,
            remaining_days=0,
            team_size=5,
        )
        # required_daily_progress 应为 0（避免除零）
        assert features["required_daily_progress"] == 0

    def test_complexity_default_medium(self, service):
        features = service._extract_features(
            project_id=1,
            current_progress=50.0,
            planned_progress=50.0,
            remaining_days=20,
            team_size=5,
        )
        assert features["complexity"] == "medium"

    def test_complexity_from_project_data(self, service):
        features = service._extract_features(
            project_id=1,
            current_progress=50.0,
            planned_progress=50.0,
            remaining_days=20,
            team_size=5,
            project_data={"complexity": "high"},
        )
        assert features["complexity"] == "high"


class TestPredictLinear:
    """_predict_linear 线性预测"""

    def test_on_track_predicts_no_delay(self, service):
        features = {
            "velocity_ratio": 1.0,
            "remaining_days": 30,
        }
        result = service._predict_linear(features)
        assert result["delay_days"] == 0
        assert result["confidence"] == 0.8

    def test_fast_project_predicts_no_delay(self, service):
        features = {
            "velocity_ratio": 1.5,
            "remaining_days": 30,
        }
        result = service._predict_linear(features)
        assert result["delay_days"] == 0

    def test_slow_project_calculates_delay(self, service):
        # velocity_ratio = 0.5 → delay = 30 * (2.0 - 1.0) = 30
        features = {
            "velocity_ratio": 0.5,
            "remaining_days": 30,
        }
        result = service._predict_linear(features)
        assert result["delay_days"] == 30
        assert result["confidence"] == 0.7

    def test_predicted_date_is_future(self, service):
        features = {
            "velocity_ratio": 1.0,
            "remaining_days": 20,
        }
        result = service._predict_linear(features)
        assert result["predicted_date"] >= date.today()

    def test_result_contains_method_key(self, service):
        features = {"velocity_ratio": 1.0, "remaining_days": 10}
        result = service._predict_linear(features)
        assert result["details"]["method"] == "linear"


class TestAssessRiskLevel:
    """_assess_risk_level 风险等级评估"""

    def test_negative_delay_is_low(self, service):
        assert service._assess_risk_level(-5) == "low"

    def test_zero_delay_is_low(self, service):
        assert service._assess_risk_level(0) == "low"

    def test_small_delay_is_low(self, service):
        assert service._assess_risk_level(3) == "low"

    def test_medium_delay_is_medium(self, service):
        assert service._assess_risk_level(7) == "medium"

    def test_large_delay_is_high(self, service):
        assert service._assess_risk_level(14) == "high"

    def test_critical_delay(self, service):
        assert service._assess_risk_level(20) == "critical"


class TestPredictCompletionDateLinear:
    """predict_completion_date 端到端（线性模式，mock DB）"""

    def test_linear_prediction_returns_expected_structure(self, mock_db):
        with patch("app.services.schedule_prediction_service.AIClientService"), \
             patch("app.services.schedule_prediction_service.save_obj"):
            svc = SchedulePredictionService(db=mock_db)
            # mock save_obj sets id
            mock_record = MagicMock()
            mock_record.id = 42
            with patch(
                "app.services.schedule_prediction_service.ProjectSchedulePrediction",
                return_value=mock_record,
            ):
                result = svc.predict_completion_date(
                    project_id=1,
                    current_progress=50.0,
                    planned_progress=50.0,
                    remaining_days=20,
                    team_size=5,
                    use_ai=False,
                )

        assert "prediction" in result
        assert "features" in result
        assert result["project_id"] == 1
        assert "risk_level" in result["prediction"]
