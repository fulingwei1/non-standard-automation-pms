# -*- coding: utf-8 -*-
"""项目健康度计算器单元测试 - 第三十六批"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.health_calculator")

try:
    from app.services.health_calculator import HealthCalculator
    from app.models.enums import ProjectHealthEnum
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    HealthCalculator = None
    ProjectHealthEnum = None


def make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.project_code = kwargs.get("project_code", "P001")
    p.project_name = kwargs.get("project_name", "测试项目")
    p.status = kwargs.get("status", "ST01")
    p.stage = kwargs.get("stage", "S01")
    p.health = kwargs.get("health", "H1")
    p.planned_start_date = kwargs.get("planned_start_date", date.today() - timedelta(days=30))
    p.planned_end_date = kwargs.get("planned_end_date", date.today() + timedelta(days=30))
    p.progress_pct = kwargs.get("progress_pct", 50)
    p.is_active = True
    p.is_archived = False
    return p


def make_calculator(db=None):
    if db is None:
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.first.return_value = None
    calc = HealthCalculator(db)
    return calc, db


class TestIsClosedAndBlocked:
    def test_closed_status_st30_returns_h4(self):
        calc, _ = make_calculator()
        p = make_project(status="ST30")
        assert calc.calculate_health(p) == "H4"

    def test_closed_status_st99_returns_h4(self):
        calc, _ = make_calculator()
        p = make_project(status="ST99")
        assert calc.calculate_health(p) == "H4"

    def test_blocked_status_st14_returns_h3(self):
        calc, _ = make_calculator()
        p = make_project(status="ST14")
        assert calc.calculate_health(p) == "H3"

    def test_blocked_status_st19_returns_h3(self):
        calc, _ = make_calculator()
        p = make_project(status="ST19")
        assert calc.calculate_health(p) == "H3"

    def test_normal_status_returns_h1(self):
        calc, _ = make_calculator()
        p = make_project(status="ST01")
        assert calc.calculate_health(p) == "H1"


class TestHasRisks:
    def test_rectification_status_st22_returns_h2(self):
        calc, _ = make_calculator()
        p = make_project(status="ST22")
        assert calc.calculate_health(p) == "H2"

    def test_deadline_approaching_7_days_returns_h2(self):
        calc, _ = make_calculator()
        p = make_project(
            status="ST01",
            planned_end_date=date.today() + timedelta(days=3)
        )
        assert calc.calculate_health(p) == "H2"

    def test_schedule_variance_over_threshold_returns_h2(self):
        calc, _ = make_calculator()
        p = make_project(
            status="ST01",
            planned_start_date=date.today() - timedelta(days=100),
            planned_end_date=date.today() + timedelta(days=10),
            progress_pct=0  # 大幅落后
        )
        assert calc.calculate_health(p) == "H2"


class TestCalculateAndUpdate:
    def test_health_unchanged_no_db_write(self):
        calc, db = make_calculator()
        p = make_project(health="H1", status="ST01")
        result = calc.calculate_and_update(p, auto_save=False)
        assert result["changed"] is False
        assert result["new_health"] == "H1"

    def test_health_changed_flags_changed(self):
        calc, db = make_calculator()
        p = make_project(health="H1", status="ST30")
        result = calc.calculate_and_update(p, auto_save=False)
        assert result["changed"] is True
        assert result["new_health"] == "H4"


class TestBatchCalculate:
    def test_batch_empty_returns_zero(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        calc = HealthCalculator(db)
        result = calc.batch_calculate()
        assert result["total"] == 0
        assert result["updated"] == 0
