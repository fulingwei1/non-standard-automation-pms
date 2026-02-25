# -*- coding: utf-8 -*-
"""Tests for app/schemas/performance.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.performance import (
    PersonalPerformanceResponse,
    PerformanceTrendResponse,
    TeamPerformanceResponse,
    DepartmentPerformanceResponse,
    PerformanceRankingResponse,
    ProjectPerformanceResponse,
    PerformanceCompareResponse,
    MonthlyWorkSummaryCreate,
    MonthlyWorkSummaryUpdate,
    MonthlyWorkSummaryResponse,
    PerformanceEvaluationRecordCreate,
    PerformanceEvaluationRecordUpdate,
    EvaluationTaskItem,
    EvaluationWeightConfigCreate,
    EvaluationWeightConfigResponse,
    MyPerformanceResult,
    MyPerformanceCurrentStatus,
)


class TestPersonalPerformanceResponse:
    def test_valid(self):
        p = PersonalPerformanceResponse(
            user_id=1, user_name="张三", period_id=1,
            period_name="2024Q1", period_type="QUARTERLY",
            start_date=date(2024, 1, 1), end_date=date(2024, 3, 31),
            total_score=Decimal("85.5"), level="B",
        )
        assert p.indicators == []
        assert p.project_contributions == []
        assert p.rank is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            PersonalPerformanceResponse()


class TestPerformanceTrendResponse:
    def test_valid(self):
        t = PerformanceTrendResponse(
            user_id=1, user_name="张三",
            periods=[{"period": "Q1", "score": 85}],
            trend_direction="UP",
            avg_score=Decimal("85"), max_score=Decimal("90"), min_score=Decimal("80"),
        )
        assert t.trend_direction == "UP"


class TestTeamPerformanceResponse:
    def test_valid(self):
        t = TeamPerformanceResponse(
            team_id=1, team_name="开发团队",
            period_id=1, period_name="Q1",
            member_count=10,
            avg_score=Decimal("82"), max_score=Decimal("95"), min_score=Decimal("70"),
            level_distribution={"A": 2, "B": 5, "C": 3},
            members=[],
        )
        assert t.member_count == 10


class TestMonthlyWorkSummaryCreate:
    def test_valid(self):
        s = MonthlyWorkSummaryCreate(
            period="2026-01",
            work_content="完成项目A的机械设计评审工作",
            self_evaluation="本月工作饱和按时完成任务",
        )
        assert s.highlights is None
        assert s.next_month_plan is None

    def test_short_period(self):
        with pytest.raises(ValidationError):
            MonthlyWorkSummaryCreate(
                period="2026",
                work_content="x" * 10,
                self_evaluation="y" * 10,
            )

    def test_short_content(self):
        with pytest.raises(ValidationError):
            MonthlyWorkSummaryCreate(
                period="2026-01",
                work_content="短",
                self_evaluation="y" * 10,
            )

    def test_short_eval(self):
        with pytest.raises(ValidationError):
            MonthlyWorkSummaryCreate(
                period="2026-01",
                work_content="x" * 10,
                self_evaluation="短",
            )

    def test_missing(self):
        with pytest.raises(ValidationError):
            MonthlyWorkSummaryCreate()


class TestMonthlyWorkSummaryUpdate:
    def test_all_none(self):
        u = MonthlyWorkSummaryUpdate()
        assert u.work_content is None

    def test_partial(self):
        u = MonthlyWorkSummaryUpdate(highlights="提前完成里程碑")
        assert u.highlights == "提前完成里程碑"


class TestPerformanceEvaluationRecordCreate:
    def test_valid(self):
        e = PerformanceEvaluationRecordCreate(
            score=92,
            comment="工作认真负责按时完成任务技术能力强",
        )
        assert e.project_id is None

    def test_score_too_low(self):
        with pytest.raises(ValidationError):
            PerformanceEvaluationRecordCreate(score=59, comment="x" * 10)

    def test_score_too_high(self):
        with pytest.raises(ValidationError):
            PerformanceEvaluationRecordCreate(score=101, comment="x" * 10)

    def test_short_comment(self):
        with pytest.raises(ValidationError):
            PerformanceEvaluationRecordCreate(score=80, comment="短")

    def test_boundary_scores(self):
        PerformanceEvaluationRecordCreate(score=60, comment="x" * 10)
        PerformanceEvaluationRecordCreate(score=100, comment="x" * 10)

    def test_with_project(self):
        e = PerformanceEvaluationRecordCreate(
            score=85, comment="x" * 10,
            project_id=1, project_weight=60,
        )
        assert e.project_weight == 60

    def test_weight_out_of_range(self):
        with pytest.raises(ValidationError):
            PerformanceEvaluationRecordCreate(
                score=85, comment="x" * 10, project_weight=101,
            )


class TestPerformanceEvaluationRecordUpdate:
    def test_all_none(self):
        u = PerformanceEvaluationRecordUpdate()
        assert u.score is None

    def test_score_bounds(self):
        PerformanceEvaluationRecordUpdate(score=60)
        PerformanceEvaluationRecordUpdate(score=100)

    def test_score_invalid(self):
        with pytest.raises(ValidationError):
            PerformanceEvaluationRecordUpdate(score=59)


class TestEvaluationWeightConfigCreate:
    def test_valid(self):
        c = EvaluationWeightConfigCreate(
            dept_manager_weight=60,
            project_manager_weight=40,
            effective_date=date(2026, 2, 1),
        )
        assert c.reason is None

    def test_out_of_range(self):
        with pytest.raises(ValidationError):
            EvaluationWeightConfigCreate(
                dept_manager_weight=101,
                project_manager_weight=40,
                effective_date=date(2026, 2, 1),
            )

    def test_missing(self):
        with pytest.raises(ValidationError):
            EvaluationWeightConfigCreate()


class TestMyPerformanceResult:
    def test_defaults(self):
        r = MyPerformanceResult(period="2026-01")
        assert r.final_score is None
        assert r.level is None
        assert r.score_breakdown == {}

    def test_with_data(self):
        r = MyPerformanceResult(
            period="2026-01", final_score=88.5, level="B",
            rank=3, dept_score=85, project_score=92.0,
        )
        assert r.final_score == 88.5


class TestMyPerformanceCurrentStatus:
    def test_valid(self):
        s = MyPerformanceCurrentStatus(
            period="2026-01",
            summary_status="SUBMITTED",
            dept_evaluation={"status": "PENDING"},
        )
        assert s.project_evaluations == []
