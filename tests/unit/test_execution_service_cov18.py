# -*- coding: utf-8 -*-
"""第十八批 - 项目执行服务单元测试"""
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.project.execution_service import ProjectExecutionService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    mock_core = MagicMock()
    svc = ProjectExecutionService(db, core_service=mock_core)
    return svc


def make_project(project_id=1, code="P001", name="项目一", pm="张三"):
    p = MagicMock()
    p.id = project_id
    p.project_code = code
    p.project_name = name
    p.stage = "S3"
    p.status = "ST01"
    p.pm_name = pm
    p.updated_at = None
    return p


class TestProjectExecutionServiceInit:
    def test_db_set(self, db, service):
        assert service.db is db

    def test_core_service_set(self, service):
        assert service.core_service is not None

    def test_creates_core_service_by_default(self, db):
        with patch("app.services.project.execution_service.ProjectCoreService") as MockCore:
            svc = ProjectExecutionService(db)
        MockCore.assert_called_once_with(db)


class TestGetProgressOverview:
    def test_returns_overview_dict(self, db, service):
        user = MagicMock()
        p1 = make_project(1, "P001", "项目A")
        p2 = make_project(2, "P002", "项目B")

        mock_query = MagicMock()
        mock_query.order_by.return_value.count.return_value = 2
        mock_query.order_by.return_value.limit.return_value.all.return_value = [p1, p2]
        service.core_service.get_scoped_query.return_value = mock_query

        progress_stats = {"actual_progress": 70.0, "is_delayed": False}
        milestone_stats = {"total": 5, "completed": 3}
        task_stats = {"total": 10, "done": 7}

        with patch("app.services.project.execution_service.calculate_progress_stats", return_value=progress_stats):
            with patch("app.services.project.execution_service.calculate_milestone_stats", return_value=milestone_stats):
                with patch("app.services.project.execution_service.calculate_task_stats", return_value=task_stats):
                    result = service.get_progress_overview(user)

        assert result["total_projects"] == 2
        assert result["sampled_projects"] == 2
        assert "average_progress" in result
        assert "delayed_projects" in result
        assert "projects" in result

    def test_average_progress_zero_when_no_projects(self, db, service):
        user = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value.count.return_value = 0
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        service.core_service.get_scoped_query.return_value = mock_query

        with patch("app.services.project.execution_service.calculate_progress_stats", return_value={"actual_progress": 0, "is_delayed": False}):
            with patch("app.services.project.execution_service.calculate_milestone_stats", return_value={}):
                with patch("app.services.project.execution_service.calculate_task_stats", return_value={}):
                    result = service.get_progress_overview(user)

        assert result["average_progress"] == 0.0

    def test_counts_delayed_projects(self, db, service):
        user = MagicMock()
        p1 = make_project(1)
        mock_query = MagicMock()
        mock_query.order_by.return_value.count.return_value = 1
        mock_query.order_by.return_value.limit.return_value.all.return_value = [p1]
        service.core_service.get_scoped_query.return_value = mock_query

        delayed_stats = {"actual_progress": 30.0, "is_delayed": True}
        with patch("app.services.project.execution_service.calculate_progress_stats", return_value=delayed_stats):
            with patch("app.services.project.execution_service.calculate_milestone_stats", return_value={}):
                with patch("app.services.project.execution_service.calculate_task_stats", return_value={}):
                    result = service.get_progress_overview(user)

        assert result["delayed_projects"] == 1

    def test_slowest_and_top_projects_included(self, db, service):
        user = MagicMock()
        projects = [make_project(i, f"P{i:03d}", f"项目{i}") for i in range(1, 4)]
        mock_query = MagicMock()
        mock_query.order_by.return_value.count.return_value = 3
        mock_query.order_by.return_value.limit.return_value.all.return_value = projects
        service.core_service.get_scoped_query.return_value = mock_query

        progress_values = [50.0, 70.0, 90.0]
        call_count = [0]
        def progress_side(project, today):
            v = progress_values[call_count[0] % 3]
            call_count[0] += 1
            return {"actual_progress": v, "is_delayed": False}

        with patch("app.services.project.execution_service.calculate_progress_stats", side_effect=progress_side):
            with patch("app.services.project.execution_service.calculate_milestone_stats", return_value={}):
                with patch("app.services.project.execution_service.calculate_task_stats", return_value={}):
                    result = service.get_progress_overview(user)

        assert "slowest_projects" in result
        assert "top_projects" in result
