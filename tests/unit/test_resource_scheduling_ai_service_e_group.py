# -*- coding: utf-8 -*-
"""
E组 - 资源调度AI服务 单元测试
覆盖: app/services/resource_scheduling_ai_service.py
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def service(db_session):
    from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
    with patch("app.services.resource_scheduling_ai_service.AIClientService"):
        svc = ResourceSchedulingAIService(db_session)
        svc.ai_client = MagicMock()
    return svc


# ─── _calculate_severity ────────────────────────────────────────────────────

class TestCalculateSeverity:

    def test_critical_by_over_allocation(self, service):
        result = service._calculate_severity(Decimal("55"), 5)
        assert result == "CRITICAL"

    def test_critical_by_overlap_days(self, service):
        result = service._calculate_severity(Decimal("5"), 35)
        assert result == "CRITICAL"

    def test_high_severity(self, service):
        result = service._calculate_severity(Decimal("35"), 5)
        assert result == "HIGH"

    def test_high_by_days(self, service):
        result = service._calculate_severity(Decimal("5"), 15)
        assert result == "HIGH"

    def test_medium_severity(self, service):
        result = service._calculate_severity(Decimal("15"), 8)
        assert result == "MEDIUM"

    def test_low_severity(self, service):
        result = service._calculate_severity(Decimal("5"), 3)
        assert result == "LOW"


# ─── _calculate_priority_score ──────────────────────────────────────────────

class TestCalculatePriorityScore:

    def test_critical_high_score(self, service):
        score = service._calculate_priority_score("CRITICAL", 20)
        assert score == 100  # capped at 100

    def test_low_severity_low_score(self, service):
        score = service._calculate_priority_score("LOW", 1)
        assert 30 <= score <= 60

    def test_time_bonus_applies(self, service):
        score_short = service._calculate_priority_score("MEDIUM", 1)
        score_long = service._calculate_priority_score("MEDIUM", 20)
        assert score_long > score_short

    def test_max_capped_at_100(self, service):
        score = service._calculate_priority_score("CRITICAL", 100)
        assert score == 100

    def test_unknown_severity_defaults_to_medium(self, service):
        score = service._calculate_priority_score("UNKNOWN", 5)
        assert 50 <= score <= 60


# ─── _determine_utilization_status ──────────────────────────────────────────

class TestDetermineUtilizationStatus:

    def test_underutilized(self, service):
        assert service._determine_utilization_status(Decimal("40")) == "UNDERUTILIZED"

    def test_normal(self, service):
        assert service._determine_utilization_status(Decimal("75")) == "NORMAL"

    def test_overutilized(self, service):
        assert service._determine_utilization_status(Decimal("100")) == "OVERUTILIZED"

    def test_critical(self, service):
        assert service._determine_utilization_status(Decimal("115")) == "CRITICAL"

    def test_boundary_50_is_normal(self, service):
        assert service._determine_utilization_status(Decimal("50")) == "NORMAL"

    def test_boundary_90_is_normal(self, service):
        assert service._determine_utilization_status(Decimal("90")) == "NORMAL"

    def test_boundary_91_is_overutilized(self, service):
        assert service._determine_utilization_status(Decimal("91")) == "OVERUTILIZED"


# ─── _ai_assess_conflict (mocked AI) ────────────────────────────────────────

class TestAiAssessConflict:

    def test_ai_success_returns_values(self, service):
        import json
        service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "risk_factors": ["风险1", "风险2"],
                "impact_analysis": {"schedule_impact": "可能延期"},
                "confidence": 0.85
            })
        }
        factors, impact, confidence = service._ai_assess_conflict(
            resource_id=1,
            project_a=MagicMock(project_name="项目A"),
            project_b=MagicMock(project_name="项目B"),
            over_allocation=Decimal("30"),
            overlap_days=10,
        )
        assert len(factors) >= 1
        assert confidence == Decimal("0.85")

    def test_ai_failure_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("AI error")
        factors, impact, confidence = service._ai_assess_conflict(
            resource_id=2,
            project_a=None,
            project_b=None,
            over_allocation=Decimal("20"),
            overlap_days=5,
        )
        assert isinstance(factors, list)
        assert confidence == Decimal("0.6")

    def test_ai_invalid_json_returns_defaults(self, service):
        service.ai_client.generate_solution.return_value = {"content": "not json {{"}
        factors, impact, confidence = service._ai_assess_conflict(
            resource_id=3,
            project_a=None,
            project_b=None,
            over_allocation=Decimal("10"),
            overlap_days=3,
        )
        assert isinstance(factors, list)


# ─── _ai_forecast_demand (mocked AI) ─────────────────────────────────────────

class TestAiForecastDemand:

    def test_successful_forecast(self, service):
        import json
        service.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "predicted_demand": 15,
                "demand_gap": 3,
                "gap_severity": "SHORTAGE",
                "predicted_utilization": 85,
                "ai_confidence": 0.78
            })
        }
        result = service._ai_forecast_demand(
            projects=[],
            forecast_period="3MONTH",
            resource_type="PERSON",
            skill_category=None,
        )
        assert result["predicted_demand"] == 15
        assert result["gap_severity"] == "SHORTAGE"

    def test_failed_forecast_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("timeout")
        result = service._ai_forecast_demand(
            projects=[],
            forecast_period="1MONTH",
            resource_type="PERSON",
            skill_category=None,
        )
        assert result["predicted_demand"] == 10
        assert result["gap_severity"] == "BALANCED"


# ─── _get_default_suggestions ────────────────────────────────────────────────

class TestGetDefaultSuggestions:

    def test_returns_one_suggestion(self, service):
        conflict = MagicMock()
        conflict.allocation_a_percent = 60
        conflict.project_b_id = 2
        result = service._get_default_suggestions(conflict)
        assert len(result) == 1
        assert result[0]["solution_type"] == "REALLOCATE"

    def test_suggestion_has_required_fields(self, service):
        conflict = MagicMock()
        conflict.allocation_a_percent = 70
        conflict.project_b_id = 5
        result = service._get_default_suggestions(conflict)
        sug = result[0]
        assert "pros" in sug
        assert "cons" in sug
        assert "execution_steps" in sug
        assert "feasibility_score" in sug


# ─── _ai_generate_solutions ──────────────────────────────────────────────────

class TestAiGenerateSolutions:

    def test_successful_generation(self, service):
        import json
        suggestions = [
            {
                "solution_type": "REALLOCATE",
                "strategy_name": "调整比例",
                "strategy_description": "降低B项目分配",
                "adjustments": {},
                "pros": ["快速"],
                "cons": ["影响B"],
                "risks": [],
                "affected_projects": [],
                "timeline_impact_days": 2,
                "cost_impact": 0,
                "quality_impact": "LOW",
                "execution_steps": ["沟通", "调整"],
                "estimated_duration_days": 2,
                "feasibility_score": 85,
                "impact_score": 20,
                "cost_score": 5,
                "risk_score": 15,
                "efficiency_score": 80,
                "ai_reasoning": "综合考虑最优"
            }
        ]
        service.ai_client.generate_solution.return_value = {
            "content": json.dumps(suggestions),
            "tokens_used": 100
        }
        conflict = MagicMock()
        conflict.resource_name = "张三"
        conflict.department_name = "研发部"
        conflict.project_a_name = "项目A"
        conflict.project_b_name = "项目B"
        conflict.allocation_a_percent = 60
        conflict.allocation_b_percent = 60
        conflict.start_date_a = date(2025, 1, 1)
        conflict.end_date_a = date(2025, 3, 31)
        conflict.start_date_b = date(2025, 2, 1)
        conflict.end_date_b = date(2025, 4, 30)
        conflict.overlap_start = date(2025, 2, 1)
        conflict.overlap_end = date(2025, 3, 31)
        conflict.overlap_days = 58
        conflict.over_allocation = Decimal("20")
        conflict.severity = "MEDIUM"
        conflict.project_b_id = 2

        result = service._ai_generate_solutions(conflict, 3)
        assert len(result) >= 1

    def test_ai_failure_returns_defaults(self, service):
        service.ai_client.generate_solution.side_effect = Exception("AI down")
        conflict = MagicMock()
        conflict.allocation_a_percent = 50
        conflict.project_b_id = 3
        result = service._ai_generate_solutions(conflict, 3)
        assert len(result) == 1  # default suggestion


# ─── detect_resource_conflicts ───────────────────────────────────────────────

class TestDetectResourceConflicts:

    def test_no_allocations_returns_empty(self, db_session):
        from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
        with patch("app.services.resource_scheduling_ai_service.AIClientService"):
            svc = ResourceSchedulingAIService(db_session)
            svc.ai_client = MagicMock()

        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db_session.query.return_value.filter.return_value.all.return_value = []

        result = svc.detect_resource_conflicts()
        assert isinstance(result, list)

    def test_no_overlap_returns_empty(self, db_session):
        from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
        with patch("app.services.resource_scheduling_ai_service.AIClientService"):
            svc = ResourceSchedulingAIService(db_session)
            svc.ai_client = MagicMock()

        # Two allocations for same resource, NO overlap
        alloc1 = MagicMock()
        alloc1.resource_id = 1
        alloc1.start_date = date(2025, 1, 1)
        alloc1.end_date = date(2025, 3, 31)
        alloc1.allocation_percent = 80

        alloc2 = MagicMock()
        alloc2.resource_id = 1
        alloc2.start_date = date(2025, 4, 1)
        alloc2.end_date = date(2025, 6, 30)
        alloc2.allocation_percent = 80

        db_session.query.return_value.filter.return_value.all.return_value = [alloc1, alloc2]

        result = svc.detect_resource_conflicts(resource_id=1)
        # No time overlap, no conflict
        assert result == []


# ─── forecast_resource_demand (mocked) ──────────────────────────────────────

class TestForecastResourceDemand:

    def test_creates_forecast_record(self, db_session):
        import json
        from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService
        with patch("app.services.resource_scheduling_ai_service.AIClientService"):
            svc = ResourceSchedulingAIService(db_session)
            svc.ai_client = MagicMock()

        svc.ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "predicted_demand": 8,
                "demand_gap": 2,
                "gap_severity": "SHORTAGE",
                "predicted_utilization": 80,
                "ai_confidence": 0.75
            })
        }
        db_session.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.resource_scheduling_ai_service.save_obj"):
            results = svc.forecast_resource_demand(forecast_period="1MONTH")
        assert len(results) == 1
