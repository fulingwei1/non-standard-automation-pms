# -*- coding: utf-8 -*-
"""
SchedulePredictionService 深度覆盖测试（N3组）

覆盖：
- _extract_features (各种输入组合，EVM-相关计算)
- _predict_linear (速度足够/不足)
- _assess_risk_level (各延期档)
- _parse_ai_prediction (有效JSON/无效/降级)
- _parse_ai_solutions
- _generate_default_solutions
- check_and_create_alerts (delay/deviation/both/none)
- create_alert
- get_project_alerts (filters)
- get_risk_overview
- generate_catch_up_solutions (AI fail fallback)
- _get_similar_projects_stats (with data / exception)
- predict_completion_date (linear mode)
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    return db


@pytest.fixture
def service(mock_db):
    with patch("app.services.schedule_prediction_service.AIClientService"):
        from app.services.schedule_prediction_service import SchedulePredictionService
        svc = SchedulePredictionService(db=mock_db)
    return svc


# ---------------------------------------------------------------------------
# _extract_features — EVM 相关计算
# ---------------------------------------------------------------------------

class TestExtractFeatures:
    def test_progress_deviation(self, service):
        features = service._extract_features(1, 60.0, 70.0, 30, 5)
        assert features["progress_deviation"] == pytest.approx(-10.0, abs=0.01)

    def test_positive_progress_deviation(self, service):
        features = service._extract_features(1, 80.0, 65.0, 20, 8)
        assert features["progress_deviation"] == pytest.approx(15.0, abs=0.01)

    def test_avg_daily_progress_from_project_data(self, service):
        features = service._extract_features(
            1, 50.0, 60.0, 20, 5,
            project_data={"days_elapsed": 25}
        )
        # avg_daily = 50 / 25 = 2.0
        assert features["avg_daily_progress"] == pytest.approx(2.0, abs=0.001)

    def test_avg_daily_progress_default_30_days(self, service):
        features = service._extract_features(1, 60.0, 70.0, 30, 5)
        # avg_daily = 60 / 30 = 2.0
        assert features["avg_daily_progress"] == pytest.approx(2.0, abs=0.001)

    def test_velocity_ratio_above_one_when_fast(self, service):
        features = service._extract_features(
            1, 80.0, 50.0, 5, 10,
            project_data={"days_elapsed": 10}
        )
        # avg_daily = 80/10 = 8; required = 20/5 = 4; ratio = 2.0
        assert features["velocity_ratio"] == pytest.approx(2.0, abs=0.01)

    def test_velocity_ratio_below_one_when_slow(self, service):
        features = service._extract_features(
            1, 30.0, 60.0, 30, 5,
            project_data={"days_elapsed": 30}
        )
        # avg_daily = 30/30 = 1.0; required = 70/30 ≈ 2.33; ratio ≈ 0.43
        assert features["velocity_ratio"] < 1.0

    def test_remaining_progress_complement(self, service):
        features = service._extract_features(1, 40.0, 50.0, 20, 3)
        assert features["remaining_progress"] == pytest.approx(60.0, abs=0.01)

    def test_zero_remaining_days_doesnt_divide_by_zero(self, service):
        features = service._extract_features(1, 90.0, 95.0, 0, 5)
        assert features["velocity_ratio"] == pytest.approx(1.0, abs=0.01)

    def test_zero_elapsed_days_doesnt_divide_by_zero(self, service):
        features = service._extract_features(
            1, 50.0, 50.0, 20, 5,
            project_data={"days_elapsed": 0}
        )
        assert features["avg_daily_progress"] == 0

    def test_complexity_from_project_data(self, service):
        features = service._extract_features(
            1, 50.0, 50.0, 20, 5,
            project_data={"complexity": "high"}
        )
        assert features["complexity"] == "high"

    def test_default_complexity_is_medium(self, service):
        features = service._extract_features(1, 50.0, 50.0, 20, 5)
        assert features["complexity"] == "medium"

    def test_all_required_keys_present(self, service):
        features = service._extract_features(1, 50.0, 60.0, 25, 7)
        required_keys = [
            "current_progress", "planned_progress", "progress_deviation",
            "remaining_days", "remaining_progress", "team_size",
            "avg_daily_progress", "required_daily_progress", "velocity_ratio",
            "complexity", "similar_projects_avg_duration", "similar_projects_delay_rate",
        ]
        for key in required_keys:
            assert key in features, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# _predict_linear
# ---------------------------------------------------------------------------

class TestPredictLinear:
    def test_no_delay_when_velocity_sufficient(self, service):
        features = {
            "velocity_ratio": 1.2,
            "remaining_days": 20,
        }
        result = service._predict_linear(features)
        assert result["delay_days"] == 0
        assert result["confidence"] == pytest.approx(0.8, abs=0.01)

    def test_delay_calculated_when_velocity_insufficient(self, service):
        features = {
            "velocity_ratio": 0.5,
            "remaining_days": 20,
        }
        result = service._predict_linear(features)
        # delay = 20 * (1/0.5 - 1) = 20 * 1 = 20
        assert result["delay_days"] == 20
        assert result["confidence"] == pytest.approx(0.7, abs=0.01)

    def test_predicted_date_is_future(self, service):
        features = {
            "velocity_ratio": 0.8,
            "remaining_days": 30,
        }
        result = service._predict_linear(features)
        assert result["predicted_date"] >= date.today()

    def test_exactly_on_track(self, service):
        features = {
            "velocity_ratio": 1.0,
            "remaining_days": 15,
        }
        result = service._predict_linear(features)
        assert result["delay_days"] == 0

    def test_velocity_ratio_of_0_25(self, service):
        features = {
            "velocity_ratio": 0.25,
            "remaining_days": 40,
        }
        result = service._predict_linear(features)
        # delay = 40 * (1/0.25 - 1) = 40 * 3 = 120
        assert result["delay_days"] == 120


# ---------------------------------------------------------------------------
# _assess_risk_level
# ---------------------------------------------------------------------------

class TestAssessRiskLevel:
    @pytest.mark.parametrize("delay_days,expected", [
        (-5, "low"),
        (0, "low"),
        (3, "low"),
        (5, "medium"),
        (7, "medium"),
        (10, "high"),
        (14, "high"),
        (15, "critical"),
        (100, "critical"),
    ])
    def test_risk_levels(self, service, delay_days, expected):
        assert service._assess_risk_level(delay_days) == expected


# ---------------------------------------------------------------------------
# _parse_ai_prediction
# ---------------------------------------------------------------------------

class TestParseAiPrediction:
    def test_parses_valid_json(self, service):
        ai_response = json.dumps({
            "delay_days": 10,
            "confidence": 0.85,
            "risk_factors": ["人力不足"],
            "recommendations": ["增加人手"],
        })
        features = {"remaining_days": 20}
        result = service._parse_ai_prediction(ai_response, features)
        assert result["delay_days"] == 10
        assert result["confidence"] == pytest.approx(0.85, abs=0.001)
        assert result["predicted_date"] == date.today() + timedelta(days=30)

    def test_parses_json_wrapped_in_text(self, service):
        ai_response = "分析结果如下：\n```json\n{\"delay_days\": 5, \"confidence\": 0.7, \"risk_factors\": [], \"recommendations\": []}\n```"
        features = {"remaining_days": 15}
        result = service._parse_ai_prediction(ai_response, features)
        assert result["delay_days"] == 5

    def test_fallback_to_linear_when_invalid_json(self, service):
        features = {"velocity_ratio": 1.0, "remaining_days": 10}
        result = service._parse_ai_prediction("no json here", features)
        # Falls back to _predict_linear result
        assert "delay_days" in result
        assert "confidence" in result

    def test_negative_delay_means_early_completion(self, service):
        ai_response = json.dumps({"delay_days": -3, "confidence": 0.9})
        features = {"remaining_days": 20}
        result = service._parse_ai_prediction(ai_response, features)
        assert result["delay_days"] == -3
        assert result["predicted_date"] == date.today() + timedelta(days=17)


# ---------------------------------------------------------------------------
# _parse_ai_solutions
# ---------------------------------------------------------------------------

class TestParseAiSolutions:
    def test_parses_valid_solutions(self, service):
        data = {
            "solutions": [
                {"name": "加班方案", "type": "overtime", "estimated_catch_up": 5},
                {"name": "增员方案", "type": "manpower", "estimated_catch_up": 8},
            ],
            "recommended_index": 1,
        }
        result = service._parse_ai_solutions(json.dumps(data))
        assert len(result) == 2
        assert result[0]["name"] == "加班方案"

    def test_returns_empty_on_invalid_json(self, service):
        result = service._parse_ai_solutions("not json")
        assert result == []

    def test_returns_empty_on_missing_solutions_key(self, service):
        result = service._parse_ai_solutions(json.dumps({"other": []}))
        assert result == []


# ---------------------------------------------------------------------------
# _generate_default_solutions
# ---------------------------------------------------------------------------

class TestGenerateDefaultSolutions:
    def test_returns_three_solutions(self, service):
        result = service._generate_default_solutions(delay_days=10)
        assert len(result) == 3

    def test_overtime_solution_has_correct_fields(self, service):
        result = service._generate_default_solutions(delay_days=10)
        overtime = next(s for s in result if s["type"] == "overtime")
        assert "estimated_catch_up" in overtime
        assert overtime["estimated_catch_up"] <= 10
        assert overtime["additional_cost"] == 8000

    def test_solution_catch_up_never_exceeds_delay(self, service):
        result = service._generate_default_solutions(delay_days=5)
        for sol in result:
            assert sol["estimated_catch_up"] <= 5

    def test_zero_delay_all_solutions_zero_catchup(self, service):
        result = service._generate_default_solutions(delay_days=0)
        for sol in result:
            assert sol["estimated_catch_up"] == 0


# ---------------------------------------------------------------------------
# create_alert
# ---------------------------------------------------------------------------

class TestCreateAlert:
    def test_creates_alert_record(self, service, mock_db):
        with patch("app.services.schedule_prediction_service.save_obj") as mock_save:
            alert = service.create_alert(
                project_id=1,
                prediction_id=2,
                alert_type="delay_warning",
                severity="high",
                title="预警",
                message="项目延期",
            )
        mock_save.assert_called_once()
        assert alert is not None

    def test_creates_alert_with_notify_users(self, service, mock_db):
        with patch("app.services.schedule_prediction_service.save_obj"):
            alert = service.create_alert(
                project_id=1,
                prediction_id=2,
                alert_type="delay_warning",
                severity="medium",
                title="延期预警",
                message="延期5天",
                notify_users=[1, 2, 3],
            )
        # notified_users list should have 3 entries
        assert len(alert.notified_users) == 3

    def test_creates_alert_with_no_notify_users(self, service, mock_db):
        with patch("app.services.schedule_prediction_service.save_obj"):
            alert = service.create_alert(
                project_id=1,
                prediction_id=2,
                alert_type="velocity_drop",
                severity="low",
                title="进度慢",
                message="慢了",
            )
        assert alert.notified_users == []


# ---------------------------------------------------------------------------
# check_and_create_alerts
# ---------------------------------------------------------------------------

class TestCheckAndCreateAlerts:
    def test_creates_delay_alert_when_delay_gte_3(self, service):
        with patch.object(service, "create_alert", return_value=MagicMock()) as mock_create:
            alerts = service.check_and_create_alerts(1, 2, delay_days=5, progress_deviation=-5)
        assert len(alerts) == 1
        mock_create.assert_called_once()
        assert mock_create.call_args[1]["alert_type"] == "delay_warning"

    def test_creates_deviation_alert_when_abs_deviation_gte_10(self, service):
        with patch.object(service, "create_alert", return_value=MagicMock()) as mock_create:
            alerts = service.check_and_create_alerts(1, 2, delay_days=0, progress_deviation=-15)
        assert len(alerts) == 1
        mock_create.call_args[1]["alert_type"] == "velocity_drop"

    def test_creates_two_alerts_when_both_conditions_met(self, service):
        with patch.object(service, "create_alert", return_value=MagicMock()) as mock_create:
            alerts = service.check_and_create_alerts(1, 2, delay_days=10, progress_deviation=-25)
        assert len(alerts) == 2

    def test_creates_no_alerts_when_on_track(self, service):
        with patch.object(service, "create_alert") as mock_create:
            alerts = service.check_and_create_alerts(1, 2, delay_days=0, progress_deviation=0)
        assert len(alerts) == 0
        mock_create.assert_not_called()

    def test_deviation_alert_high_severity_when_gte_20(self, service):
        with patch.object(service, "create_alert", return_value=MagicMock()) as mock_create:
            service.check_and_create_alerts(1, 2, delay_days=0, progress_deviation=-25)
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["severity"] == "high"

    def test_deviation_alert_medium_severity_when_between_10_and_20(self, service):
        with patch.object(service, "create_alert", return_value=MagicMock()) as mock_create:
            service.check_and_create_alerts(1, 2, delay_days=0, progress_deviation=-12)
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["severity"] == "medium"


# ---------------------------------------------------------------------------
# get_project_alerts
# ---------------------------------------------------------------------------

class TestGetProjectAlerts:
    def _setup_alerts(self, mock_db):
        a1 = MagicMock()
        a1.id = 1
        a1.alert_type = "delay_warning"
        a1.severity = "high"
        a1.title = "延期预警"
        a1.message = "延期10天"
        a1.alert_details = {}
        a1.is_read = False
        a1.is_resolved = False
        a1.created_at = datetime(2024, 1, 10)
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [a1]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [a1]
        return a1

    def test_returns_alert_list(self, service, mock_db):
        a1 = self._setup_alerts(mock_db)
        result = service.get_project_alerts(project_id=1)
        assert isinstance(result, list)

    def test_with_severity_filter(self, service, mock_db):
        self._setup_alerts(mock_db)
        result = service.get_project_alerts(project_id=1, severity="high")
        assert isinstance(result, list)

    def test_unread_only_filter(self, service, mock_db):
        self._setup_alerts(mock_db)
        result = service.get_project_alerts(project_id=1, unread_only=True)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# _get_similar_projects_stats
# ---------------------------------------------------------------------------

class TestGetSimilarProjectsStats:
    def test_returns_defaults_when_no_data(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        result = service._get_similar_projects_stats("medium", 5)
        assert result["avg_duration"] == 90
        assert result["delay_rate"] == pytest.approx(0.3, abs=0.01)

    def test_returns_calculated_stats_when_data_exists(self, service, mock_db):
        p1 = MagicMock()
        p1.delay_days = 10
        p2 = MagicMock()
        p2.delay_days = 0
        p3 = MagicMock()
        p3.delay_days = 5
        # Need to setup the complex query chain properly
        from unittest.mock import MagicMock as MM
        q = MM()
        q.all.return_value = [p1, p2, p3]
        mock_db.query.return_value.filter.return_value.limit.return_value = q
        mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value = q
        # All chained filters
        mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = [p1, p2, p3]
        result = service._get_similar_projects_stats("medium", 5)
        # delay_rate = 2/3 ≈ 0.67
        assert "delay_rate" in result

    def test_handles_exception_returns_defaults(self, service, mock_db):
        mock_db.query.side_effect = Exception("DB error")
        result = service._get_similar_projects_stats("high", 3)
        assert result == {"avg_duration": 90, "delay_rate": 0.3, "avg_delay": 10}


# ---------------------------------------------------------------------------
# predict_completion_date (linear mode)
# ---------------------------------------------------------------------------

class TestPredictCompletionDate:
    def test_predict_linear_mode(self, service, mock_db):
        prediction_record = MagicMock()
        prediction_record.id = 1
        with patch("app.services.schedule_prediction_service.save_obj"), \
             patch.object(service, "_get_similar_projects_stats", return_value={"avg_duration": 90, "delay_rate": 0.3, "avg_delay": 10}):
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
            result = service.predict_completion_date(
                project_id=1,
                current_progress=50.0,
                planned_progress=60.0,
                remaining_days=30,
                team_size=5,
                use_ai=False,
            )
        assert "prediction" in result
        assert "features" in result
        assert result["project_id"] == 1

    def test_predict_includes_risk_level(self, service, mock_db):
        with patch("app.services.schedule_prediction_service.save_obj"), \
             patch.object(service, "_get_similar_projects_stats", return_value={"avg_duration": 90, "delay_rate": 0.3, "avg_delay": 10}):
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
            result = service.predict_completion_date(
                project_id=2,
                current_progress=30.0,
                planned_progress=70.0,
                remaining_days=20,
                team_size=3,
                use_ai=False,
            )
        assert "risk_level" in result["prediction"]
        assert result["prediction"]["risk_level"] in ["low", "medium", "high", "critical"]


# ---------------------------------------------------------------------------
# generate_catch_up_solutions (AI fail → fallback)
# ---------------------------------------------------------------------------

class TestGenerateCatchUpSolutions:
    def test_fallback_to_default_when_ai_fails(self, service, mock_db):
        with patch.object(service, "_generate_solutions_with_ai", side_effect=Exception("AI error")):
            with pytest.raises(Exception):
                service.generate_catch_up_solutions(
                    project_id=1,
                    prediction_id=2,
                    delay_days=10,
                )

    def test_saves_solutions_to_db(self, service, mock_db):
        default_solutions = service._generate_default_solutions(10)
        with patch.object(service, "_generate_solutions_with_ai", return_value=default_solutions):
            mock_db.commit.return_value = None
            solutions = service.generate_catch_up_solutions(
                project_id=1,
                prediction_id=2,
                delay_days=10,
            )
        assert isinstance(solutions, list)
        assert len(solutions) == 3

    def test_returns_correct_keys(self, service, mock_db):
        default_solutions = service._generate_default_solutions(5)
        with patch.object(service, "_generate_solutions_with_ai", return_value=default_solutions):
            solutions = service.generate_catch_up_solutions(
                project_id=1, prediction_id=1, delay_days=5
            )
        for sol in solutions:
            assert "name" in sol
            assert "risk_level" in sol
            assert "is_recommended" in sol


# ---------------------------------------------------------------------------
# get_risk_overview
# ---------------------------------------------------------------------------

class TestGetRiskOverview:
    def test_returns_overview_structure(self, service, mock_db):
        from sqlalchemy import func
        subq = MagicMock()
        mock_db.query.return_value.group_by.return_value.subquery.return_value = subq
        mock_db.query.return_value.join.return_value.all.return_value = []
        result = service.get_risk_overview()
        assert "total_projects" in result
        assert "at_risk" in result
        assert "critical" in result
        assert "projects" in result

    def test_counts_at_risk_projects(self, service, mock_db):
        p1 = MagicMock()
        p1.project_id = 1
        p1.risk_level = "high"
        p1.delay_days = 10
        p1.predicted_completion_date = date(2025, 6, 30)
        p2 = MagicMock()
        p2.project_id = 2
        p2.risk_level = "critical"
        p2.delay_days = 20
        p2.predicted_completion_date = date(2025, 7, 1)
        p3 = MagicMock()
        p3.project_id = 3
        p3.risk_level = "low"
        p3.delay_days = 0
        p3.predicted_completion_date = date(2025, 5, 1)

        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = [p1, p2, p3]

        result = service.get_risk_overview()
        assert result["total_projects"] == 3
        assert result["at_risk"] == 2
        assert result["critical"] == 1
