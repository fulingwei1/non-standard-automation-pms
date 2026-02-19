# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/generators/analysis.py
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.report_framework.generators.analysis")

from app.services.report_framework.generators.analysis import AnalysisReportGenerator


@pytest.fixture
def mock_db():
    return MagicMock()


class TestAnalysisReportGeneratorWorkload:
    def test_generate_workload_analysis_no_users(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = AnalysisReportGenerator.generate_workload_analysis(
            db=mock_db,
            department_id=None,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert "summary" in result
        assert "workload_details" in result
        assert result["summary"]["total_users"] == 0

    def test_generate_workload_analysis_with_defaults(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = AnalysisReportGenerator.generate_workload_analysis(db=mock_db)
        assert "load_distribution" in result
        assert "charts" in result

    def test_calculate_workload_load_levels(self, mock_db):
        users = [MagicMock(id=i, real_name=f"User{i}", username=f"user{i}", department="D") for i in range(4)]
        timesheets = [
            MagicMock(user_id=0, hours=200, project_id=1),  # OVERLOAD >22 days
            MagicMock(user_id=1, hours=150, project_id=2),  # HIGH
            MagicMock(user_id=2, hours=100, project_id=3),  # MEDIUM
            MagicMock(user_id=3, hours=50, project_id=4),   # LOW
        ]

        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            mock_db, users, timesheets
        )
        assert len(workload_list) == 4
        assert any(w["load_level"] == "OVERLOAD" for w in workload_list)
        assert any(w["load_level"] == "LOW" for w in workload_list)

    def test_get_user_scope_no_department(self, mock_db):
        mock_users = [MagicMock(id=1)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_users

        users, scope = AnalysisReportGenerator._get_user_scope(mock_db, None)
        assert scope == "全公司"
        assert users == mock_users

    def test_get_user_scope_with_department_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        users, scope = AnalysisReportGenerator._get_user_scope(mock_db, 999)
        assert users == []


class TestAnalysisReportGeneratorCost:
    def test_generate_cost_analysis_no_projects(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = AnalysisReportGenerator.generate_cost_analysis(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert "summary" in result
        assert result["summary"]["project_count"] == 0
        assert result["summary"]["total_budget"] == 0

    def test_get_projects_specific_project(self, mock_db):
        mock_project = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        projects = AnalysisReportGenerator._get_projects(mock_db, 1)
        assert len(projects) == 1

    def test_calculate_project_costs(self, mock_db):
        project = MagicMock(id=1, project_name="Test", budget_amount=10000)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            mock_db, [project], date(2024, 1, 1), date(2024, 1, 31)
        )
        assert len(summaries) == 1
        assert summaries[0]["project_name"] == "Test"
        assert total_budget == 10000.0
