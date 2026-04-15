# -*- coding: utf-8 -*-
"""Compatibility tests for the historical analysis generator test path."""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.report_framework.generators.analysis import AnalysisReportGenerator


class TestAnalysisReportGenerator(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()

    def test_get_projects_all(self):
        projects = [
            MagicMock(id=1, status="IN_PROGRESS"),
            MagicMock(id=2, status="ON_HOLD"),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = projects

        result = AnalysisReportGenerator._get_projects(self.db, None)

        self.assertEqual([project.id for project in result], [1, 2])

    def test_calculate_project_costs_budget_none(self):
        projects = [MagicMock(id=1, project_name="项目A", budget_amount=None)]
        self.db.query.return_value.filter.return_value.all.return_value = [MagicMock(hours=100)]

        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            self.db,
            projects,
            date(2024, 1, 1),
            date(2024, 1, 31),
        )

        self.assertEqual(total_budget, 0)
        self.assertEqual(total_actual, 10000)
        self.assertEqual(summaries[0]["budget"], 0)
        self.assertEqual(summaries[0]["actual_cost"], 10000)

    def test_generate_cost_analysis_default(self):
        projects = [MagicMock(id=1), MagicMock(id=2)]
        project_summaries = [
            {"project_id": 1, "project_name": "项目A", "budget": 100000, "actual_cost": 10000},
            {"project_id": 2, "project_name": "项目B", "budget": 50000, "actual_cost": 5000},
        ]

        with patch.object(AnalysisReportGenerator, "_get_projects", return_value=projects), patch.object(
            AnalysisReportGenerator,
            "_calculate_project_costs",
            return_value=(project_summaries, 150000, 15000),
        ):
            result = AnalysisReportGenerator.generate_cost_analysis(self.db)

        self.assertEqual(result["summary"]["project_count"], 2)
        self.assertEqual(result["summary"]["total_budget"], 150000)
        self.assertEqual(result["summary"]["total_actual"], 15000)
        self.assertEqual(result["project_breakdown"], project_summaries)

    def test_generate_cost_analysis_specific_project(self):
        project = MagicMock(id=9)
        project_summaries = [
            {"project_id": 9, "project_name": "指定项目", "budget": 200000, "actual_cost": 50000}
        ]

        with patch.object(AnalysisReportGenerator, "_get_projects", return_value=[project]) as mock_get_projects, patch.object(
            AnalysisReportGenerator,
            "_calculate_project_costs",
            return_value=(project_summaries, 200000, 50000),
        ):
            result = AnalysisReportGenerator.generate_cost_analysis(
                self.db,
                project_id=9,
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 29),
            )

        mock_get_projects.assert_called_once_with(self.db, 9)
        self.assertEqual(result["summary"]["project_count"], 1)
        self.assertEqual(result["summary"]["total_budget"], 200000)
        self.assertEqual(result["summary"]["total_actual"], 50000)

    def test_generate_workload_analysis_with_department(self):
        users = [
            MagicMock(id=1, real_name="张三", username="zhangsan", department="研发部"),
        ]
        timesheets = [MagicMock(user_id=1, hours=200, project_id=101)]
        self.db.query.return_value.filter.return_value.all.return_value = timesheets

        with patch.object(AnalysisReportGenerator, "_get_user_scope", return_value=(users, "研发部")):
            result = AnalysisReportGenerator.generate_workload_analysis(
                self.db,
                department_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )

        self.assertEqual(result["summary"]["scope"], "研发部")
        self.assertEqual(result["summary"]["total_users"], 1)
        self.assertEqual(result["load_distribution"]["OVERLOAD"], 1)
        self.assertEqual(result["workload_details"][0]["user_name"], "张三")

    def test_workload_details_sorted_by_days(self):
        users = [
            MagicMock(id=1, real_name="用户1", username="user1", department="部门1"),
            MagicMock(id=2, real_name="用户2", username="user2", department="部门2"),
            MagicMock(id=3, real_name="用户3", username="user3", department="部门3"),
        ]
        timesheets = [
            MagicMock(user_id=1, hours=80, project_id=1),
            MagicMock(user_id=2, hours=160, project_id=2),
            MagicMock(user_id=3, hours=120, project_id=3),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = timesheets

        with patch.object(AnalysisReportGenerator, "_get_user_scope", return_value=(users, "全公司")):
            result = AnalysisReportGenerator.generate_workload_analysis(self.db)

        self.assertEqual([item["user_id"] for item in result["workload_details"]], [2, 3, 1])
