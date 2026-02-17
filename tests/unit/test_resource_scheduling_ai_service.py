# -*- coding: utf-8 -*-
"""
I2组 - 资源调度AI服务 单元测试
覆盖: app/services/resource_scheduling_ai_service.py
"""
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.resource_scheduling_ai_service.AIClientService"):
        from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
        svc = ResourceSchedulingAIService(mock_db)
        svc.ai_client = MagicMock()
        return svc


# ─── _calculate_severity ─────────────────────────────────────────────────────

class TestCalculateSeverity:
    def test_critical_by_allocation(self, service):
        assert service._calculate_severity(Decimal("55"), 5) == "CRITICAL"

    def test_critical_by_days(self, service):
        assert service._calculate_severity(Decimal("5"), 35) == "CRITICAL"

    def test_high_by_allocation(self, service):
        assert service._calculate_severity(Decimal("35"), 5) == "HIGH"

    def test_high_by_days(self, service):
        assert service._calculate_severity(Decimal("5"), 15) == "HIGH"

    def test_medium_by_allocation(self, service):
        assert service._calculate_severity(Decimal("15"), 5) == "MEDIUM"

    def test_medium_by_days(self, service):
        assert service._calculate_severity(Decimal("5"), 8) == "MEDIUM"

    def test_low(self, service):
        assert service._calculate_severity(Decimal("5"), 3) == "LOW"


# ─── _calculate_priority_score ────────────────────────────────────────────────

class TestCalculatePriorityScore:
    def test_critical_base(self, service):
        score = service._calculate_priority_score("CRITICAL", 0)
        assert score == 95

    def test_low_base(self, service):
        score = service._calculate_priority_score("LOW", 0)
        assert score == 30

    def test_time_bonus(self, service):
        score_no_time = service._calculate_priority_score("MEDIUM", 0)
        score_with_time = service._calculate_priority_score("MEDIUM", 20)
        assert score_with_time > score_no_time

    def test_max_100(self, service):
        score = service._calculate_priority_score("CRITICAL", 100)
        assert score == 100

    def test_unknown_severity(self, service):
        score = service._calculate_priority_score("UNKNOWN", 0)
        assert score == 50  # 默认


# ─── _determine_utilization_status ───────────────────────────────────────────

class TestDetermineUtilizationStatus:
    def test_underutilized(self, service):
        assert service._determine_utilization_status(Decimal("40")) == "UNDERUTILIZED"

    def test_normal(self, service):
        assert service._determine_utilization_status(Decimal("80")) == "NORMAL"

    def test_overutilized(self, service):
        assert service._determine_utilization_status(Decimal("100")) == "OVERUTILIZED"

    def test_critical(self, service):
        assert service._determine_utilization_status(Decimal("120")) == "CRITICAL"

    def test_boundary_50(self, service):
        assert service._determine_utilization_status(Decimal("50")) == "NORMAL"

    def test_boundary_90(self, service):
        assert service._determine_utilization_status(Decimal("90")) == "NORMAL"

    def test_boundary_110(self, service):
        assert service._determine_utilization_status(Decimal("110")) == "OVERUTILIZED"


# ─── _get_default_suggestions ────────────────────────────────────────────────

class TestGetDefaultSuggestions:
    def test_returns_list(self, service):
        conflict = MagicMock()
        conflict.allocation_a_percent = 60
        conflict.project_b_id = 2
        result = service._get_default_suggestions(conflict)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_suggestion_structure(self, service):
        conflict = MagicMock()
        conflict.allocation_a_percent = 60
        conflict.project_b_id = 2
        suggestion = service._get_default_suggestions(conflict)[0]
        assert "solution_type" in suggestion
        assert "feasibility_score" in suggestion


# ─── _ai_assess_conflict (AI mock) ───────────────────────────────────────────

class TestAIAssessConflict:
    def test_success_path(self, service):
        fake_response = {
            "content": json.dumps({
                "risk_factors": ["超负荷"],
                "impact_analysis": {"schedule_impact": "延期"},
                "confidence": 0.85
            })
        }
        service.ai_client.generate_solution.return_value = fake_response

        project_a = MagicMock()
        project_a.project_name = "项目A"
        project_b = MagicMock()
        project_b.project_name = "项目B"

        risk_factors, impact, confidence = service._ai_assess_conflict(
            resource_id=1,
            project_a=project_a,
            project_b=project_b,
            over_allocation=Decimal("30"),
            overlap_days=10,
        )
        assert "超负荷" in risk_factors
        assert confidence == Decimal("0.85")

    def test_ai_failure_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("AI down")

        risk_factors, impact, confidence = service._ai_assess_conflict(
            resource_id=1,
            project_a=None,
            project_b=None,
            over_allocation=Decimal("20"),
            overlap_days=5,
        )
        assert isinstance(risk_factors, list)
        assert confidence == Decimal("0.6")

    def test_invalid_json_returns_defaults(self, service):
        service.ai_client.generate_solution.return_value = {"content": "不是JSON"}

        risk_factors, impact, confidence = service._ai_assess_conflict(
            resource_id=1,
            project_a=None,
            project_b=None,
            over_allocation=Decimal("10"),
            overlap_days=3,
        )
        assert isinstance(risk_factors, list)


# ─── _ai_forecast_demand ─────────────────────────────────────────────────────

class TestAIForecastDemand:
    def test_success(self, service):
        fake = {
            "predicted_demand": 15,
            "demand_gap": 3,
            "gap_severity": "SHORTAGE",
            "ai_confidence": 0.78
        }
        service.ai_client.generate_solution.return_value = {"content": json.dumps(fake)}

        projects = []
        result = service._ai_forecast_demand(
            projects=projects,
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category=None,
        )
        assert result["predicted_demand"] == 15

    def test_ai_failure_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("error")
        result = service._ai_forecast_demand(
            projects=[], forecast_period="1MONTH",
            resource_type="PERSON", skill_category=None
        )
        assert "predicted_demand" in result
        assert result["ai_confidence"] == 0.5


# ─── _ai_analyze_utilization ─────────────────────────────────────────────────

class TestAIAnalyzeUtilization:
    def test_success(self, service):
        fake = {"key_insights": ["正常"], "optimization_suggestions": []}
        service.ai_client.generate_solution.return_value = {"content": json.dumps(fake)}

        result = service._ai_analyze_utilization(1, Decimal("80"), Decimal("128"), 20)
        assert "key_insights" in result

    def test_failure_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("err")
        result = service._ai_analyze_utilization(1, Decimal("50"), Decimal("80"), 10)
        assert "key_insights" in result


# ─── _create_forecast_record ─────────────────────────────────────────────────

class TestCreateForecastRecord:
    def test_creates_record(self, service, mock_db):
        ai_forecast = {
            "predicted_demand": 10,
            "demand_gap": 0,
            "gap_severity": "BALANCED",
            "predicted_total_hours": 800,
            "predicted_peak_hours": 240,
            "predicted_utilization": 75,
            "driving_projects": [],
            "recommendations": [],
            "hiring_suggestion": {},
            "estimated_cost": 0,
            "risk_level": "LOW",
            "ai_confidence": 0.7,
        }

        with patch("app.services.resource_scheduling_ai_service.save_obj") as mock_save:
            result = service._create_forecast_record(
                forecast_start=date.today(),
                forecast_end=date.today() + timedelta(days=90),
                forecast_period="3MONTH",
                resource_type="PERSON",
                skill_category=None,
                ai_forecast=ai_forecast,
            )
            assert mock_save.called

    def test_sets_forecast_code(self, service):
        ai_forecast = {
            "predicted_demand": 5,
            "demand_gap": 0,
            "gap_severity": "BALANCED",
            "ai_confidence": 0.6,
        }
        today = date(2024, 1, 15)

        with patch("app.services.resource_scheduling_ai_service.save_obj"):
            result = service._create_forecast_record(
                forecast_start=today,
                forecast_end=today + timedelta(days=30),
                forecast_period="1MONTH",
                resource_type="PERSON",
                skill_category=None,
                ai_forecast=ai_forecast,
            )
        assert result.forecast_code == "RF-1MONTH-20240115"


# ─── forecast_resource_demand ─────────────────────────────────────────────────

class TestForecastResourceDemand:
    def test_returns_list(self, service, mock_db):
        # Mock the entire DB query chain to avoid Project model attribute issues
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, "_ai_forecast_demand") as mock_ai, \
             patch.object(service, "_create_forecast_record") as mock_create, \
             patch("app.services.resource_scheduling_ai_service.and_"):
            mock_ai.return_value = {"predicted_demand": 5, "ai_confidence": 0.7}
            mock_create.return_value = MagicMock()

            # patch date().today() isn't needed; just ensure it runs
            result = service.forecast_resource_demand(forecast_period="3MONTH")
            assert isinstance(result, list)
            assert len(result) == 1


# ─── analyze_resource_utilization ────────────────────────────────────────────

class TestAnalyzeResourceUtilization:
    def _mock_timesheet_import(self, mock_db, timesheets):
        """Setup db mock to return timesheets without real import"""
        mock_db.query.return_value.filter.return_value.all.return_value = timesheets

    def test_basic(self, service, mock_db):
        mock_ts = MagicMock()
        mock_ts.hours = 8

        # Patch the Timesheet import inside the method
        mock_timesheet_class = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts] * 20

        with patch.dict("sys.modules", {"app.models.finance": MagicMock(Timesheet=MagicMock())}), \
             patch("app.services.resource_scheduling_ai_service.save_obj"), \
             patch.object(service, "_ai_analyze_utilization") as mock_ai:
            mock_ai.return_value = {"key_insights": ["正常"]}

            result = service.analyze_resource_utilization(
                resource_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
            assert result.analysis_code.startswith("RU-1-")

    def test_zero_hours(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.dict("sys.modules", {"app.models.finance": MagicMock(Timesheet=MagicMock())}), \
             patch("app.services.resource_scheduling_ai_service.save_obj"), \
             patch.object(service, "_ai_analyze_utilization") as mock_ai:
            mock_ai.return_value = {}

            result = service.analyze_resource_utilization(
                resource_id=2,
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 29),
            )
            assert result.total_actual_hours == Decimal("0")
