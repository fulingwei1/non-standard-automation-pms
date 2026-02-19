# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/generators/analysis.py"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.generators.analysis import AnalysisReportGenerator
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.all.return_value = []
    return db


def test_generate_workload_analysis_no_department():
    db = _make_db()
    db.query.return_value.filter.return_value.all.return_value = []
    result = AnalysisReportGenerator.generate_workload_analysis(
        db, department_id=None, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
    )
    assert "summary" in result
    assert result["summary"]["scope"] == "全公司"
    assert "load_distribution" in result
    assert "workload_details" in result


def test_generate_workload_analysis_with_users():
    db = _make_db()
    user = MagicMock()
    user.id = 1
    user.real_name = "张三"
    user.username = "zhangsan"
    user.is_active = True
    db.query.return_value.filter.return_value.all.return_value = [user]
    result = AnalysisReportGenerator.generate_workload_analysis(
        db, department_id=None, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
    )
    assert result["summary"]["total_users"] == 1
    assert len(result["workload_details"]) == 1


def test_generate_cost_analysis_no_projects():
    db = _make_db()
    with patch.object(AnalysisReportGenerator, '_get_projects', return_value=[]):
        result = AnalysisReportGenerator.generate_cost_analysis(
            db, project_id=None, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
    assert result["summary"]["project_count"] == 0
    assert result["summary"]["total_budget"] == 0.0
    assert result["summary"]["total_actual"] == 0.0


def test_generate_cost_analysis_with_project():
    db = _make_db()
    project = MagicMock()
    project.id = 10
    project.project_name = "Cost项目"
    project.budget_amount = 100000
    db.query.return_value.filter.return_value.all.return_value = []
    with patch.object(AnalysisReportGenerator, '_get_projects', return_value=[project]):
        result = AnalysisReportGenerator.generate_cost_analysis(
            db, project_id=10, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
    assert result["summary"]["total_budget"] == 100000.0
    assert len(result["project_breakdown"]) == 1


def test_calculate_workload_overload():
    db = _make_db()
    user = MagicMock()
    user.id = 1
    user.real_name = "高负荷员工"
    user.username = "heavy"
    # 23 天 = 184 小时
    ts = MagicMock()
    ts.user_id = 1
    ts.hours = 184
    ts.project_id = 5
    workload_list, load_summary = AnalysisReportGenerator._calculate_workload(db, [user], [ts])
    assert workload_list[0]["load_level"] == "OVERLOAD"
    assert load_summary["OVERLOAD"] == 1


def test_calculate_workload_low():
    db = _make_db()
    user = MagicMock()
    user.id = 2
    user.real_name = "轻负荷员工"
    user.username = "light"
    workload_list, load_summary = AnalysisReportGenerator._calculate_workload(db, [user], [])
    assert workload_list[0]["load_level"] == "LOW"
    assert load_summary["LOW"] == 1


def test_get_user_scope_no_department():
    db = _make_db()
    users = [MagicMock()]
    db.query.return_value.filter.return_value.all.return_value = users
    result_users, scope_name = AnalysisReportGenerator._get_user_scope(db, None)
    assert scope_name == "全公司"
