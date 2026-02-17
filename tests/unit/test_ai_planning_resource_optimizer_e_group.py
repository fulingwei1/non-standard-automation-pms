# -*- coding: utf-8 -*-
"""
E组 - AI资源优化器 单元测试
覆盖: app/services/ai_planning/resource_optimizer.py
"""
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def glm_service():
    glm = MagicMock()
    glm.model = "glm-5"
    glm.is_available.return_value = True
    return glm


@pytest.fixture
def optimizer(db_session, glm_service):
    from app.services.ai_planning.resource_optimizer import AIResourceOptimizer
    return AIResourceOptimizer(db=db_session, glm_service=glm_service)


def _make_user(user_id=1, role="developer", is_active=True):
    user = MagicMock()
    user.id = user_id
    user.role = role
    user.is_active = is_active
    return user


def _make_wbs(wbs_id=1, project_id=10, required_skills=None, estimated_effort_hours=80,
              estimated_duration_days=10, task_type="DEV"):
    wbs = MagicMock()
    wbs.id = wbs_id
    wbs.project_id = project_id
    wbs.required_skills = json.dumps(required_skills) if required_skills else None
    wbs.estimated_effort_hours = estimated_effort_hours
    wbs.estimated_duration_days = estimated_duration_days
    wbs.task_type = task_type
    return wbs


# ─── _calculate_skill_match ──────────────────────────────────────────────────

class TestCalculateSkillMatch:

    def test_no_required_skills_returns_70(self, optimizer):
        user = _make_user(role="developer")
        wbs = _make_wbs(required_skills=None)
        result = optimizer._calculate_skill_match(user, wbs)
        assert result == 70.0

    def test_skill_match_in_role(self, optimizer):
        user = _make_user(role="python developer")
        wbs = _make_wbs(required_skills=[{"skill": "python", "level": "senior"}])
        result = optimizer._calculate_skill_match(user, wbs)
        assert result > 50.0

    def test_no_skill_match(self, optimizer):
        user = _make_user(role="marketing")
        wbs = _make_wbs(required_skills=[{"skill": "java", "level": "senior"}])
        result = optimizer._calculate_skill_match(user, wbs)
        assert result == 50.0  # base score, no match

    def test_max_capped_at_100(self, optimizer):
        user = _make_user(role="python java frontend backend")
        wbs = _make_wbs(required_skills=[
            {"skill": "python"}, {"skill": "java"}, {"skill": "frontend"}, {"skill": "backend"}
        ])
        result = optimizer._calculate_skill_match(user, wbs)
        assert result <= 100.0


# ─── _calculate_experience_match ─────────────────────────────────────────────

class TestCalculateExperienceMatch:

    def test_zero_similar_tasks_returns_40(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 0
        result = optimizer._calculate_experience_match(user, wbs)
        assert result == 40.0

    def test_few_tasks_returns_60(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 2
        result = optimizer._calculate_experience_match(user, wbs)
        assert result == 60.0

    def test_many_tasks_returns_95(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 15
        result = optimizer._calculate_experience_match(user, wbs)
        assert result == 95.0

    def test_moderate_tasks_returns_80(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 5
        result = optimizer._calculate_experience_match(user, wbs)
        assert result == 80.0


# ─── _get_current_workload ────────────────────────────────────────────────────

class TestGetCurrentWorkload:

    def test_no_active_tasks_returns_0(self, optimizer, db_session):
        user = _make_user()
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = optimizer._get_current_workload(user)
        assert result == 0.0

    def test_5_tasks_100_percent(self, optimizer, db_session):
        user = _make_user()
        tasks = [MagicMock() for _ in range(5)]
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = tasks
        result = optimizer._get_current_workload(user)
        assert result == 100.0  # 5 * 20 = 100, capped

    def test_2_tasks_40_percent(self, optimizer, db_session):
        user = _make_user()
        tasks = [MagicMock(), MagicMock()]
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = tasks
        result = optimizer._get_current_workload(user)
        assert result == 40.0


# ─── _calculate_availability ─────────────────────────────────────────────────

class TestCalculateAvailability:

    def test_full_availability(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = optimizer._calculate_availability(user, wbs)
        assert result == 100.0

    def test_high_workload_low_availability(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        tasks = [MagicMock() for _ in range(5)]
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = tasks
        result = optimizer._calculate_availability(user, wbs)
        assert result == 0.0  # 100 - 100 = 0


# ─── _calculate_performance_score ────────────────────────────────────────────

class TestCalculatePerformanceScore:

    def test_no_completed_tasks_returns_70(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        db_session.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = []
        result = optimizer._calculate_performance_score(user, wbs)
        assert result == 70.0

    def test_all_on_time_returns_100(self, optimizer, db_session):
        user = _make_user()
        wbs = _make_wbs()
        from datetime import date
        task = MagicMock()
        task.planned_end_date = date(2025, 6, 1)
        task.actual_end_date = date(2025, 5, 28)  # before deadline
        db_session.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        result = optimizer._calculate_performance_score(user, wbs)
        assert result == 100.0


# ─── _get_hourly_rate ─────────────────────────────────────────────────────────

class TestGetHourlyRate:

    def test_senior_role(self, optimizer):
        user = _make_user(role="senior developer")
        assert optimizer._get_hourly_rate(user) == 200.0

    def test_middle_role(self, optimizer):
        user = _make_user(role="middle engineer")
        assert optimizer._get_hourly_rate(user) == 150.0

    def test_junior_role(self, optimizer):
        user = _make_user(role="junior developer")
        assert optimizer._get_hourly_rate(user) == 100.0

    def test_default_role(self, optimizer):
        user = _make_user(role="engineer")
        assert optimizer._get_hourly_rate(user) == 120.0

    def test_chinese_senior(self, optimizer):
        user = _make_user(role="高级工程师")
        assert optimizer._get_hourly_rate(user) == 200.0


# ─── _calculate_cost_efficiency ──────────────────────────────────────────────

class TestCalculateCostEfficiency:

    def test_zero_rate_returns_match_score(self, optimizer):
        result = optimizer._calculate_cost_efficiency(80.0, 0.0)
        assert result == 80.0

    def test_efficiency_capped_at_100(self, optimizer):
        result = optimizer._calculate_cost_efficiency(100.0, 100.0)
        assert result == 100.0

    def test_low_rate_high_efficiency(self, optimizer):
        result = optimizer._calculate_cost_efficiency(80.0, 50.0)
        # 80 / 0.5 = 160 -> capped at 100
        assert result == 100.0


# ─── _generate_recommendation_reason ─────────────────────────────────────────

class TestGenerateRecommendationReason:

    def test_high_skill_match(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        reason = optimizer._generate_recommendation_reason(user, wbs, 90, 80, 90, 90)
        assert "技能" in reason

    def test_high_availability(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        reason = optimizer._generate_recommendation_reason(user, wbs, 50, 50, 85, 70)
        assert "负载" in reason

    def test_no_strong_match_default_reason(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        reason = optimizer._generate_recommendation_reason(user, wbs, 50, 50, 50, 50)
        assert isinstance(reason, str) and len(reason) > 0


# ─── _analyze_strengths / _analyze_weaknesses ────────────────────────────────

class TestAnalyzeStrengthsWeaknesses:

    def test_high_skill_is_strength(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        strengths = optimizer._analyze_strengths(user, wbs, skill_match=85, performance=85)
        assert len(strengths) >= 1
        cats = [s["category"] for s in strengths]
        assert "技能" in cats

    def test_low_skill_is_weakness(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        weaknesses = optimizer._analyze_weaknesses(user, wbs, skill_match=40, availability=80)
        assert len(weaknesses) >= 1
        assert weaknesses[0]["impact"] == "HIGH"

    def test_low_availability_is_weakness(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        weaknesses = optimizer._analyze_weaknesses(user, wbs, skill_match=70, availability=30)
        cats = [w["category"] for w in weaknesses]
        assert "可用性" in cats


# ─── _optimize_allocations ───────────────────────────────────────────────────

class TestOptimizeAllocations:

    def test_empty_input_returns_empty(self, optimizer):
        result = optimizer._optimize_allocations([], MagicMock())
        assert result == []

    def test_first_allocation_is_primary(self, optimizer):
        allocs = [MagicMock(overall_match_score=90), MagicMock(overall_match_score=80)]
        wbs = _make_wbs()
        result = optimizer._optimize_allocations(allocs, wbs)
        assert result[0].allocation_type == "PRIMARY"
        assert result[0].priority == "HIGH"

    def test_max_5_returned(self, optimizer):
        allocs = [MagicMock(overall_match_score=i) for i in range(10)]
        result = optimizer._optimize_allocations(allocs, MagicMock())
        assert len(result) <= 5


# ─── allocate_resources (integration mock) ──────────────────────────────────

class TestAllocateResources:

    @pytest.mark.asyncio
    async def test_wbs_not_found_returns_empty(self, optimizer, db_session):
        db_session.query.return_value.get.return_value = None
        result = await optimizer.allocate_resources(999)
        assert result == []

    @pytest.mark.asyncio
    async def test_no_users_returns_empty(self, optimizer, db_session):
        wbs = _make_wbs()
        db_session.query.return_value.get.return_value = wbs
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = await optimizer.allocate_resources(1)
        assert result == []
