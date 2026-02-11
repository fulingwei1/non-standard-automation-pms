# -*- coding: utf-8 -*-
"""Tests for report_data_generation/dept_reports.py"""
from unittest.mock import MagicMock
from datetime import date

from app.services.report_data_generation.dept_reports import DeptReportMixin


class TestGenerateDeptWeeklyReport:
    def test_dept_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportMixin.generate_dept_weekly_report(db, 999, date(2025, 1, 6), date(2025, 1, 12))
        assert result == {"error": "部门不存在"}

    def test_basic_report(self):
        db = MagicMock()
        dept = MagicMock(dept_name="技术部", dept_code="TECH")
        user = MagicMock(id=1, real_name="张三", username="zhangsan", is_active=True)
        user.position = "工程师"
        ts = MagicMock(user_id=1, hours=8, project_id=1)

        db.query.return_value.filter.return_value.first.side_effect = [dept, MagicMock(project_name="项目A")]
        db.query.return_value.filter.return_value.all.side_effect = [
            [user],  # dept_members
            [ts],    # timesheets
        ]

        result = DeptReportMixin.generate_dept_weekly_report(db, 1, date(2025, 1, 6), date(2025, 1, 12))
        assert result['summary']['department_name'] == "技术部"
        assert result['timesheet']['total_hours'] == 8.0

    def test_empty_department(self):
        db = MagicMock()
        dept = MagicMock(dept_name="空部门", dept_code="EMPTY")
        db.query.return_value.filter.return_value.first.return_value = dept
        db.query.return_value.filter.return_value.all.side_effect = [
            [],  # no members
            [],  # no timesheets
        ]
        result = DeptReportMixin.generate_dept_weekly_report(db, 1, date(2025, 1, 6), date(2025, 1, 12))
        assert result['timesheet']['total_hours'] == 0


class TestGenerateDeptMonthlyReport:
    def test_dept_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportMixin.generate_dept_monthly_report(db, 999, date(2025, 1, 1), date(2025, 1, 31))
        assert result == {"error": "部门不存在"}

    def test_basic_monthly_report(self):
        db = MagicMock()
        dept = MagicMock(dept_name="技术部", dept_code="TECH")

        user = MagicMock(id=1, real_name="张三", username="zhangsan", department="技术部", is_active=True)
        user.position = "工程师"

        project = MagicMock(id=1, project_name="项目A", stage="S4", health="H1",
                            is_active=True, created_at=MagicMock(), updated_at=MagicMock())
        project.created_at.date.return_value = date(2025, 1, 15)
        project.updated_at.date.return_value = date(2025, 1, 20)

        ts = MagicMock(user_id=1, hours=160, project_id=1,
                       work_date=date(2025, 1, 15))
        pm = MagicMock(project_id=1, user_id=1)

        db.query.return_value.filter.return_value.first.side_effect = [
            dept,     # department
            project,  # project lookup
        ]
        db.query.return_value.filter.return_value.all.side_effect = [
            [user],   # dept_members
            [pm],     # project_memberships
            [project],  # projects
            [ts],     # timesheets
        ]

        result = DeptReportMixin.generate_dept_monthly_report(db, 1, date(2025, 1, 1), date(2025, 1, 31))
        assert result['summary']['department_name'] == "技术部"
        assert result['key_metrics']['total_members'] == 1
