# -*- coding: utf-8 -*-
"""Tests for report_framework/generators/department.py"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestDeptReportGenerator:
    def setup_method(self):
        self.db = MagicMock()

    def test_generate_weekly_department_not_found(self):
        from app.services.report_framework.generators.department import DeptReportGenerator
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportGenerator.generate_weekly(self.db, 999, date(2024, 1, 1), date(2024, 1, 7))
        assert "error" in result

    @pytest.mark.skip(reason="User model lacks department_id attribute in test context")
    def test_generate_weekly_returns_dict(self):
        from app.services.report_framework.generators.department import DeptReportGenerator
        dept = MagicMock()
        dept.id = 1
        dept.dept_name = "测试部门"
        dept.dept_code = "D01"
        self.db.query.return_value.filter.return_value.first.return_value = dept
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = DeptReportGenerator.generate_weekly(self.db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert isinstance(result, dict)

    def test_generate_monthly_department_not_found(self):
        from app.services.report_framework.generators.department import DeptReportGenerator
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportGenerator.generate_monthly(self.db, 999, date(2024, 1, 1), date(2024, 1, 31))
        assert "error" in result


# ──────────────────────────────────────────────────────────────────────────────
# G4 补充测试 - DeptReportGenerator
# ──────────────────────────────────────────────────────────────────────────────

class TestDeptReportGeneratorG4:
    """G4 补充：DeptReportGenerator 额外覆盖"""

    def setup_method(self):
        self.db = MagicMock()

    def _make_dept(self, dept_id=1):
        dept = MagicMock()
        dept.id = dept_id
        dept.dept_name = "测试部门"
        dept.dept_code = "D001"
        return dept

    # ---- generate_weekly: 部门存在，返回正确结构 ----

    def test_generate_weekly_with_dept(self):
        """部门存在时 generate_weekly 返回包含 summary 的字典"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        dept = self._make_dept()
        # first() 返回 dept
        self.db.query.return_value.filter.return_value.first.return_value = dept
        # all() 返回空列表（无成员）
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        # 工时聚合返回 None
        self.db.query.return_value.filter.return_value.scalar.return_value = None

        result = DeptReportGenerator.generate_weekly(
            self.db, 1, date(2024, 1, 1), date(2024, 1, 7)
        )
        assert isinstance(result, dict)
        assert "summary" in result

    # ---- generate_weekly: 部门不存在 ----

    def test_generate_weekly_dept_missing(self):
        """部门不存在时返回 error 字典"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        self.db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportGenerator.generate_weekly(
            self.db, 999, date(2024, 1, 1), date(2024, 1, 7)
        )
        assert result.get("error") is not None

    # ---- generate_monthly: 部门不存在 ----

    def test_generate_monthly_dept_missing(self):
        """月报：部门不存在时返回 error"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        self.db.query.return_value.filter.return_value.first.return_value = None
        result = DeptReportGenerator.generate_monthly(
            self.db, 999, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert "error" in result

    # ---- generate_monthly: 部门存在，返回正确结构 ----

    def test_generate_monthly_with_dept(self):
        """月报：部门存在时返回包含 summary 的字典"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        dept = self._make_dept()
        self.db.query.return_value.filter.return_value.first.return_value = dept
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.scalar.return_value = None

        result = DeptReportGenerator.generate_monthly(
            self.db, 1, date(2024, 1, 1), date(2024, 1, 31)
        )
        assert isinstance(result, dict)
        assert "summary" in result

    # ---- department_id 传入 ----

    def test_weekly_report_includes_department_id(self):
        """周报 summary 中包含正确的 department_id"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        dept = self._make_dept(dept_id=42)
        self.db.query.return_value.filter.return_value.first.return_value = dept
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.scalar.return_value = None

        result = DeptReportGenerator.generate_weekly(
            self.db, 42, date(2024, 3, 1), date(2024, 3, 7)
        )
        assert result["summary"]["department_id"] == 42

    # ---- period_start / period_end 格式 ----

    def test_weekly_report_period_dates(self):
        """周报 summary 中 period_start/end 使用 ISO 格式"""
        from app.services.report_framework.generators.department import DeptReportGenerator

        dept = self._make_dept()
        self.db.query.return_value.filter.return_value.first.return_value = dept
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.scalar.return_value = None

        result = DeptReportGenerator.generate_weekly(
            self.db, 1, date(2024, 6, 3), date(2024, 6, 9)
        )
        assert result["summary"]["period_start"] == "2024-06-03"
        assert result["summary"]["period_end"] == "2024-06-09"
