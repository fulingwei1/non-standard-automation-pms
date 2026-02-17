# -*- coding: utf-8 -*-
"""DelayRootCauseService 单元测试"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestDelayRootCauseService:

    def _make_service(self):
        from app.services.delay_root_cause_service import DelayRootCauseService
        db = MagicMock()
        return DelayRootCauseService(db), db

    # ---------- analyze_root_cause ----------

    def test_analyze_root_cause_empty(self):
        """无延期任务时返回空 root_causes"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.analyze_root_cause()
        assert result["total_delayed_tasks"] == 0
        assert result["root_causes"] == []
        assert result["summary"]["top_reason"] is None

    def test_analyze_root_cause_groups_by_reason(self):
        """按 delay_reason 分组统计"""
        svc, db = self._make_service()
        today = date.today()
        t1 = MagicMock(is_delayed=True, delay_reason="SUPPLIER", task_name="A", id=1, project_id=1,
                       plan_start_date=today, plan_end_date=today - timedelta(days=3),
                       actual_end_date=today)
        t2 = MagicMock(is_delayed=True, delay_reason="SUPPLIER", task_name="B", id=2, project_id=1,
                       plan_start_date=today, plan_end_date=today - timedelta(days=2),
                       actual_end_date=today)
        t3 = MagicMock(is_delayed=True, delay_reason="DESIGN", task_name="C", id=3, project_id=2,
                       plan_start_date=today, plan_end_date=today - timedelta(days=5),
                       actual_end_date=today)
        db.query.return_value.filter.return_value.all.return_value = [t1, t2, t3]
        result = svc.analyze_root_cause()
        assert result["total_delayed_tasks"] == 3
        reasons = {r["reason"] for r in result["root_causes"]}
        assert "SUPPLIER" in reasons
        assert "DESIGN" in reasons

    def test_analyze_root_cause_sorted_by_total_delay(self):
        """root_causes 按 total_delay_days 降序排列"""
        svc, db = self._make_service()
        today = date.today()
        t1 = MagicMock(is_delayed=True, delay_reason="A", task_name="T1", id=1, project_id=1,
                       plan_start_date=today, plan_end_date=today - timedelta(days=1), actual_end_date=today)
        t2 = MagicMock(is_delayed=True, delay_reason="B", task_name="T2", id=2, project_id=1,
                       plan_start_date=today, plan_end_date=today - timedelta(days=10), actual_end_date=today)
        db.query.return_value.filter.return_value.all.return_value = [t1, t2]
        result = svc.analyze_root_cause()
        assert result["root_causes"][0]["reason"] == "B"

    # ---------- _calculate_delay_days ----------

    def test_calculate_delay_days_with_actual(self):
        """实际结束日期晚于计划时计算差值"""
        svc, _ = self._make_service()
        plan = date(2025, 1, 1)
        actual = date(2025, 1, 11)
        task = MagicMock(is_delayed=True, plan_end_date=plan, actual_end_date=actual)
        assert svc._calculate_delay_days(task) == 10

    def test_calculate_delay_days_not_delayed(self):
        """未标记为延期时返回 0"""
        svc, _ = self._make_service()
        task = MagicMock(is_delayed=False)
        assert svc._calculate_delay_days(task) == 0

    # ---------- _calculate_trend_direction ----------

    def test_trend_increasing(self):
        svc, _ = self._make_service()
        data = [{"delay_rate": 5.0}, {"delay_rate": 10.0}, {"delay_rate": 15.0}]
        assert svc._calculate_trend_direction(data) == "INCREASING"

    def test_trend_decreasing(self):
        svc, _ = self._make_service()
        data = [{"delay_rate": 15.0}, {"delay_rate": 10.0}, {"delay_rate": 5.0}]
        assert svc._calculate_trend_direction(data) == "DECREASING"

    def test_trend_stable(self):
        svc, _ = self._make_service()
        data = [{"delay_rate": 10.0}, {"delay_rate": 10.0}, {"delay_rate": 10.0}]
        assert svc._calculate_trend_direction(data) == "STABLE"

    def test_trend_single_element(self):
        svc, _ = self._make_service()
        data = [{"delay_rate": 10.0}]
        assert svc._calculate_trend_direction(data) == "STABLE"

    # ---------- analyze_impact ----------

    def test_analyze_impact_no_delayed_projects(self):
        """无延期项目时成本影响为0"""
        svc, db = self._make_service()
        p = MagicMock(status="IN_PROGRESS", plan_end_date=date.today() + timedelta(days=30),
                      actual_end_date=None, contract_amount=None)
        db.query.return_value.filter.return_value.all.return_value = [p]
        result = svc.analyze_impact()
        assert result["cost_impact"]["total"] == 0.0
        assert result["affected_projects"] == []

    # ---------- analyze_trends ----------

    def test_analyze_trends_returns_structure(self):
        """analyze_trends 返回包含 trends 和 summary 的结构"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.analyze_trends(months=3)
        assert "trends" in result
        assert "summary" in result
        assert result["summary"]["average_delay_rate"] == 0
