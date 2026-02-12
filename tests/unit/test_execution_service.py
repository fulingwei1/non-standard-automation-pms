# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from app.services.project.execution_service import ProjectExecutionService


class TestProjectExecutionService:
    @patch("app.services.project.execution_service.calculate_task_stats")
    @patch("app.services.project.execution_service.calculate_milestone_stats")
    @patch("app.services.project.execution_service.calculate_progress_stats")
    @patch("app.services.project.execution_service.ProjectCoreService")
    def test_empty_overview(self, mock_core_cls, mock_progress, mock_milestone, mock_task):
        db = MagicMock()
        mock_core = mock_core_cls.return_value
        query = MagicMock()
        query.order_by.return_value = query
        query.count.return_value = 0
        query.limit.return_value.all.return_value = []
        mock_core.get_scoped_query.return_value = query

        service = ProjectExecutionService(db)
        user = MagicMock()
        result = service.get_progress_overview(user)
        assert result["total_projects"] == 0
        assert result["projects"] == []

    @patch("app.services.project.execution_service.calculate_task_stats")
    @patch("app.services.project.execution_service.calculate_milestone_stats")
    @patch("app.services.project.execution_service.calculate_progress_stats")
    @patch("app.services.project.execution_service.ProjectCoreService")
    def test_with_projects(self, mock_core_cls, mock_progress, mock_milestone, mock_task):
        db = MagicMock()
        mock_core = mock_core_cls.return_value
        query = MagicMock()
        query.order_by.return_value = query
        query.count.return_value = 1
        p = MagicMock()
        p.id = 1; p.project_code = "P001"; p.project_name = "Test"
        p.stage = "S1"; p.status = "ST01"; p.pm_name = "PM"
        query.limit.return_value.all.return_value = [p]
        mock_core.get_scoped_query.return_value = query
        mock_progress.return_value = {"actual_progress": 50, "is_delayed": False}
        mock_milestone.return_value = {}
        mock_task.return_value = {}

        service = ProjectExecutionService(db)
        result = service.get_progress_overview(MagicMock())
        assert result["total_projects"] == 1
        assert len(result["projects"]) == 1
