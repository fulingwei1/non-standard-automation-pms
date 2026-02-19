# -*- coding: utf-8 -*-
"""第四十六批 - 公司报表单元测试"""
import pytest
from datetime import date

pytest.importorskip("app.services.template_report.company_reports",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock
from app.services.template_report.company_reports import CompanyReportMixin


def _make_db(projects=None, departments=None):
    db = MagicMock()
    projects = projects or []
    departments = departments or []

    def query_side(model):
        q = MagicMock()
        name = getattr(model, '__name__', str(model))
        if 'Project' in name:
            q.filter.return_value.all.return_value = projects
        elif 'Department' in name:
            q.all.return_value = departments
        elif 'User' in name:
            q.filter.return_value.all.return_value = []
        elif 'Timesheet' in name:
            q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = query_side
    return db


class TestGenerateCompanyMonthly:
    def test_returns_summary_with_period(self):
        db = _make_db()
        result = CompanyReportMixin._generate_company_monthly(
            db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            sections_config={},
            metrics_config={}
        )

        assert "summary" in result
        assert result["summary"]["period_start"] == "2024-01-01"
        assert result["summary"]["period_end"] == "2024-01-31"

    def test_returns_sections(self):
        db = _make_db()
        result = CompanyReportMixin._generate_company_monthly(
            db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            sections_config={},
            metrics_config={}
        )
        assert "sections" in result
        assert "project_status" in result["sections"]
        assert "health_status" in result["sections"]

    def test_counts_projects(self):
        p1 = MagicMock()
        p1.status = "IN_PROGRESS"
        p2 = MagicMock()
        p2.status = "COMPLETED"
        db = _make_db(projects=[p1, p2])
        result = CompanyReportMixin._generate_company_monthly(
            db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            sections_config={},
            metrics_config={}
        )
        assert result["summary"]["total_projects"] == 2

    def test_metrics_present(self):
        db = _make_db()
        result = CompanyReportMixin._generate_company_monthly(
            db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            sections_config={},
            metrics_config={}
        )
        assert "metrics" in result
        assert "total_projects" in result["metrics"]

    def test_dept_hours_empty_when_no_timesheets(self):
        dept = MagicMock()
        dept.id = 1
        dept.name = "研发部"
        db = MagicMock()

        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            name = getattr(model, '__name__', str(model))
            if call_count[0] == 1:  # Project
                q.filter.return_value.all.return_value = []
            elif call_count[0] == 2:  # Department
                q.all.return_value = [dept]
            elif call_count[0] == 3:  # User
                q.filter.return_value.all.return_value = []
            else:  # Timesheet
                q.filter.return_value.all.return_value = []
            return q

        db.query.side_effect = query_side
        result = CompanyReportMixin._generate_company_monthly(
            db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            sections_config={},
            metrics_config={}
        )
        assert result["sections"]["department_hours"]["data"] == []
