# -*- coding: utf-8 -*-
"""Tests for app.services.report_data_generation.analysis_reports"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.report_data_generation.analysis_reports import AnalysisReportMixin


class TestGenerateWorkloadAnalysis(unittest.TestCase):

    def test_no_department_all_users(self):
        db = MagicMock()
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        user.is_active = True
        user.department = "技术部"

        db.query.return_value.filter.return_value.all.side_effect = [
            [user],  # users
            [],      # timesheets
        ]

        result = AnalysisReportMixin.generate_workload_analysis(
            db, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["scope"], "全公司")
        self.assertEqual(result["summary"]["total_users"], 1)

    def test_with_department(self):
        db = MagicMock()
        dept = MagicMock()
        dept.dept_name = "技术部"

        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.department = "技术部"

        ts = MagicMock()
        ts.user_id = 1
        ts.hours = 160
        ts.project_id = 10

        db.query.return_value.filter.return_value.first.return_value = dept
        db.query.return_value.filter.return_value.all.side_effect = [
            [user],  # users
            [ts],    # timesheets
        ]
        # For user lookup in loop
        db.query.return_value.filter.return_value.first.return_value = user

        result = AnalysisReportMixin.generate_workload_analysis(
            db, department_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertIn("load_distribution", result)

    def test_empty_department(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        result = AnalysisReportMixin.generate_workload_analysis(
            db, department_id=999, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertEqual(result["summary"]["total_users"], 0)


class TestGenerateCostAnalysis(unittest.TestCase):

    def test_no_projects(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = AnalysisReportMixin.generate_cost_analysis(
            db, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertEqual(result["summary"]["project_count"], 0)
        self.assertEqual(result["summary"]["total_budget"], 0)

    def test_with_project(self):
        db = MagicMock()
        project = MagicMock()
        project.id = 1
        project.project_name = "项目A"
        project.budget_amount = 100000

        ts = MagicMock()
        ts.hours = 80

        db.query.return_value.filter.return_value.all.side_effect = [
            [project],  # projects
            [ts],       # timesheets
        ]

        result = AnalysisReportMixin.generate_cost_analysis(
            db, project_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        self.assertEqual(result["summary"]["project_count"], 1)
        self.assertGreater(result["summary"]["total_budget"], 0)

    def test_default_dates(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = AnalysisReportMixin.generate_cost_analysis(db)
        self.assertIn("summary", result)


if __name__ == "__main__":
    unittest.main()
