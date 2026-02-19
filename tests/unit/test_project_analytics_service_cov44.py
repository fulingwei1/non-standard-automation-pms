# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 项目分析聚合服务"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

try:
    from app.services.project.analytics_service import ProjectAnalyticsService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.project.analytics_service.ProjectCoreService"), \
         patch("app.services.project.analytics_service.ProjectExecutionService"), \
         patch("app.services.project.analytics_service.ProjectResourceService"), \
         patch("app.services.project.analytics_service.ProjectFinanceService"):
        svc = ProjectAnalyticsService(mock_db)
        return svc


class TestProjectAnalyticsService:

    def test_init_creates_sub_services(self, mock_db):
        with patch("app.services.project.analytics_service.ProjectCoreService") as MockCore, \
             patch("app.services.project.analytics_service.ProjectExecutionService") as MockExec, \
             patch("app.services.project.analytics_service.ProjectResourceService") as MockRes, \
             patch("app.services.project.analytics_service.ProjectFinanceService") as MockFin:
            svc = ProjectAnalyticsService(mock_db)
            MockCore.assert_called_once_with(mock_db)
            assert svc.db is mock_db

    def test_get_projects_health_summary_returns_dict(self, service):
        mock_user = MagicMock()
        service.core_service.get_scoped_query.return_value.all.return_value = []
        result = service.get_projects_health_summary(mock_user)
        assert isinstance(result, dict)
        assert "total_projects" in result
        assert result["total_projects"] == 0

    def test_health_summary_aggregates_by_health(self, service):
        mock_user = MagicMock()
        p1 = MagicMock(health="H1", stage="S1", pm_name="Alice",
                        project_code="P001", project_name="Proj1",
                        progress_pct=50, planned_end_date=None, id=1)
        p2 = MagicMock(health="H3", stage="S2", pm_name="Bob",
                        project_code="P002", project_name="Proj2",
                        progress_pct=30, planned_end_date=None, id=2)
        service.core_service.get_scoped_query.return_value.all.return_value = [p1, p2]
        result = service.get_projects_health_summary(mock_user)
        assert result["total_projects"] == 2
        assert result["by_health"].get("H1", 0) == 1
        assert result["by_health"].get("H3", 0) == 1

    def test_risk_projects_includes_h3_h4(self, service):
        mock_user = MagicMock()
        p = MagicMock(health="H4", stage="S3", pm_name="Carol",
                      project_code="P003", project_name="Proj3",
                      progress_pct=10, planned_end_date=None, id=3)
        service.core_service.get_scoped_query.return_value.all.return_value = [p]
        result = service.get_projects_health_summary(mock_user)
        assert len(result["risk_projects"]) == 1
        assert result["risk_projects"][0]["health"] == "H4"

    def test_get_projects_progress_summary_delegates(self, service):
        mock_user = MagicMock()
        service.execution_service.get_progress_overview.return_value = {"items": []}
        result = service.get_projects_progress_summary(mock_user, limit=10)
        service.execution_service.get_progress_overview.assert_called_once_with(mock_user, 10)
        assert result == {"items": []}

    def test_risk_projects_capped_at_ten(self, service):
        mock_user = MagicMock()
        projects = []
        for i in range(15):
            p = MagicMock(health="H3", stage="S1", pm_name=f"PM{i}",
                          project_code=f"P{i:03d}", project_name=f"Proj{i}",
                          progress_pct=i * 5, planned_end_date=None, id=i)
            projects.append(p)
        service.core_service.get_scoped_query.return_value.all.return_value = projects
        result = service.get_projects_health_summary(mock_user)
        assert len(result["risk_projects"]) <= 10
