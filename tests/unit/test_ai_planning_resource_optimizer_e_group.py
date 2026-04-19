# -*- coding: utf-8 -*-
"""
E组 - AI资源优化器 单元测试
覆盖: app/services/ai_planning/resource_optimizer.py
"""
import json
from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def glm_service():
    glm = MagicMock()
    glm.model = "glm-5"
    glm.is_available.return_value = True
    return glm


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def optimizer(mock_db, glm_service):
    from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

    return AIResourceOptimizer(db=mock_db, glm_service=glm_service)


def _make_user(user_id=1, role="developer", is_active=True):
    user = MagicMock()
    user.id = user_id
    user.role = role
    user.is_active = is_active
    return user


def _make_wbs(
    wbs_id=1,
    project_id=10,
    required_skills=None,
    estimated_effort_hours=80,
    estimated_duration_days=10,
    task_type="DEV",
):
    wbs = MagicMock()
    wbs.id = wbs_id
    wbs.project_id = project_id
    wbs.required_skills = json.dumps(required_skills) if required_skills else None
    wbs.estimated_effort_hours = estimated_effort_hours
    wbs.estimated_duration_days = estimated_duration_days
    wbs.task_type = task_type
    return wbs


class TestCalculateSkillMatch:
    def test_no_required_skills_returns_70(self, optimizer):
        user = _make_user(role="developer")
        wbs = _make_wbs(required_skills=None)
        assert optimizer._calculate_skill_match(user, wbs) == 70.0

    def test_skill_match_in_role(self, optimizer):
        user = _make_user(role="python developer")
        wbs = _make_wbs(required_skills=[{"skill": "python", "level": "senior"}])
        assert optimizer._calculate_skill_match(user, wbs) > 50.0

    def test_no_skill_match(self, optimizer):
        user = _make_user(role="marketing")
        wbs = _make_wbs(required_skills=[{"skill": "java", "level": "senior"}])
        assert optimizer._calculate_skill_match(user, wbs) == 50.0

    def test_max_capped_at_100(self, optimizer):
        user = _make_user(role="python java frontend backend")
        wbs = _make_wbs(required_skills=[{"skill": "python"}, {"skill": "java"}, {"skill": "frontend"}, {"skill": "backend"}])
        assert optimizer._calculate_skill_match(user, wbs) <= 100.0


class TestCalculateExperienceMatch:
    def test_zero_similar_tasks_returns_40(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        assert optimizer._calculate_experience_match(user, wbs) == 40.0

    def test_few_tasks_returns_60(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2
        assert optimizer._calculate_experience_match(user, wbs) == 60.0

    def test_many_tasks_returns_95(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 15
        assert optimizer._calculate_experience_match(user, wbs) == 95.0

    def test_moderate_tasks_returns_80(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        assert optimizer._calculate_experience_match(user, wbs) == 80.0


class TestGetCurrentWorkload:
    def test_no_active_tasks_returns_0(self, optimizer, mock_db):
        user = _make_user()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        assert optimizer._get_current_workload(user) == 0.0

    def test_5_tasks_100_percent(self, optimizer, mock_db):
        user = _make_user()
        tasks = [MagicMock() for _ in range(5)]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        assert optimizer._get_current_workload(user) == 100.0

    def test_2_tasks_40_percent(self, optimizer, mock_db):
        user = _make_user()
        tasks = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        assert optimizer._get_current_workload(user) == 40.0


class TestCalculateAvailability:
    def test_full_availability(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        assert optimizer._calculate_availability(user, wbs) == 100.0

    def test_high_workload_low_availability(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        tasks = [MagicMock() for _ in range(5)]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        assert optimizer._calculate_availability(user, wbs) == 0.0


class TestCalculatePerformanceScore:
    def test_no_completed_tasks_returns_70(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        assert optimizer._calculate_performance_score(user, wbs) == 70.0

    def test_all_on_time_returns_100(self, optimizer, mock_db):
        user = _make_user()
        wbs = _make_wbs()
        task = MagicMock()
        task.planned_end_date = date(2025, 6, 1)
        task.actual_end_date = date(2025, 5, 28)
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        assert optimizer._calculate_performance_score(user, wbs) == 100.0


class TestGetHourlyRate:
    def test_senior_role(self, optimizer):
        assert optimizer._get_hourly_rate(_make_user(role="senior developer")) == 200.0

    def test_middle_role(self, optimizer):
        assert optimizer._get_hourly_rate(_make_user(role="middle engineer")) == 150.0

    def test_junior_role(self, optimizer):
        assert optimizer._get_hourly_rate(_make_user(role="junior developer")) == 100.0

    def test_default_role(self, optimizer):
        assert optimizer._get_hourly_rate(_make_user(role="engineer")) == 120.0

    def test_chinese_senior(self, optimizer):
        assert optimizer._get_hourly_rate(_make_user(role="高级工程师")) == 200.0


class TestCalculateCostEfficiency:
    def test_zero_rate_returns_match_score(self, optimizer):
        assert optimizer._calculate_cost_efficiency(80.0, 0.0) == 80.0

    def test_efficiency_capped_at_100(self, optimizer):
        assert optimizer._calculate_cost_efficiency(100.0, 100.0) == 100.0

    def test_low_rate_high_efficiency(self, optimizer):
        assert optimizer._calculate_cost_efficiency(80.0, 50.0) == 100.0


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


class TestAnalyzeStrengthsWeaknesses:
    def test_high_skill_is_strength(self, optimizer):
        user = _make_user()
        wbs = _make_wbs()
        strengths = optimizer._analyze_strengths(user, wbs, skill_match=85, performance=85)
        assert len(strengths) >= 1
        assert "技能" in [s["category"] for s in strengths]

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
        assert "可用性" in [w["category"] for w in weaknesses]


class TestOptimizeAllocations:
    def test_empty_input_returns_empty(self, optimizer):
        assert optimizer._optimize_allocations([], MagicMock()) == []

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


class TestAllocateResources:
    @pytest.mark.asyncio
    async def test_wbs_not_found_returns_empty(self, optimizer, mock_db):
        mock_db.query.return_value.get.return_value = None
        assert await optimizer.allocate_resources(999) == []

    @pytest.mark.asyncio
    async def test_no_users_returns_empty(self, optimizer, mock_db):
        wbs = _make_wbs()
        query1 = MagicMock()
        query1.get.return_value = wbs
        query2 = MagicMock()
        query2.filter.return_value.all.return_value = []
        mock_db.query.side_effect = [query1, query2]

        result = await optimizer.allocate_resources(1)
        assert result == []
