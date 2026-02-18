# -*- coding: utf-8 -*-
"""第二十三批：delay_root_cause_service 单元测试"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.delay_root_cause_service")

from app.services.delay_root_cause_service import DelayRootCauseService


def _make_db():
    return MagicMock()


def _mock_task(task_id=1, plan_end=None, actual_end=None, delay_reason=None,
               plan_start=None, project_id=1, task_name="任务A"):
    t = MagicMock()
    t.id = task_id
    t.plan_end = plan_end or date(2025, 1, 10)
    t.actual_end = actual_end or date(2025, 1, 15)
    t.delay_reason = delay_reason
    t.plan_start = plan_start or date(2025, 1, 1)
    t.project_id = project_id
    t.task_name = task_name
    return t


def _mock_project(pid=1, status="IN_PROGRESS", plan_end_date=None, actual_end_date=None,
                  contract_amount=None, project_code="P001", project_name="项目1"):
    p = MagicMock()
    p.id = pid
    p.status = status
    p.plan_end_date = plan_end_date or date(2024, 12, 31)
    p.actual_end_date = actual_end_date
    p.contract_amount = contract_amount
    p.project_code = project_code
    p.project_name = project_name
    return p


class TestAnalyzeRootCause:
    def test_no_delayed_tasks_returns_empty(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = svc.analyze_root_cause()
        assert result["total_delayed_tasks"] == 0
        assert result["root_causes"] == []

    def test_delayed_tasks_grouped_by_reason(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        task1 = _mock_task(delay_reason="供应商延迟", plan_end=date(2025, 1, 10), actual_end=date(2025, 1, 15))
        task2 = _mock_task(delay_reason="供应商延迟", plan_end=date(2025, 1, 10), actual_end=date(2025, 1, 20))
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [task1, task2]
        db.query.return_value = q
        result = svc.analyze_root_cause()
        assert result["total_delayed_tasks"] == 2
        assert len(result["root_causes"]) == 1
        assert result["root_causes"][0]["reason"] == "供应商延迟"

    def test_project_id_filter_applied(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = svc.analyze_root_cause(project_id=42)
        assert result["total_delayed_tasks"] == 0

    def test_unknown_reason_used_when_none(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        task = _mock_task(delay_reason=None)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [task]
        db.query.return_value = q
        result = svc.analyze_root_cause()
        assert result["root_causes"][0]["reason"] == "UNKNOWN"


class TestAnalyzeImpact:
    def test_no_projects(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = svc.analyze_impact()
        assert result["cost_impact"]["total"] == 0.0

    def test_delayed_project_impacts_cost(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        proj = _mock_project(
            plan_end_date=date(2024, 6, 1),
            actual_end_date=date(2024, 6, 11),  # 10 days late
            contract_amount=100000
        )
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [proj]
        db.query.return_value = q
        result = svc.analyze_impact()
        assert result["cost_impact"]["total"] > 0


class TestAnalyzeTrends:
    def test_trend_returns_monthly_data(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = svc.analyze_trends(months=3)
        assert "trends" in result
        assert result["summary"]["average_delay_rate"] == 0


class TestHelpers:
    def test_calculate_delay_days_no_delay(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        task = _mock_task(plan_end=date(2025, 1, 15), actual_end=date(2025, 1, 10))
        # actual_end < plan_end → no delay
        assert svc._calculate_delay_days(task) == 0

    def test_calculate_trend_direction_stable(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        data = [{"delay_rate": 10.0}, {"delay_rate": 10.2}]
        assert svc._calculate_trend_direction(data) == "STABLE"

    def test_calculate_trend_direction_increasing(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        data = [{"delay_rate": 5.0}, {"delay_rate": 20.0}]
        assert svc._calculate_trend_direction(data) == "INCREASING"

    def test_is_project_delayed_with_no_dates(self):
        db = _make_db()
        svc = DelayRootCauseService(db)
        # Use a real-like mock with plan_end_date explicitly None
        proj = MagicMock()
        proj.plan_end_date = None
        proj.actual_end_date = None
        assert svc._is_project_delayed(proj) is False
