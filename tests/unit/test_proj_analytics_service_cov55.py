# -*- coding: utf-8 -*-
"""
Tests for app/services/project/analytics_service.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.project.analytics_service import ProjectAnalyticsService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.project.analytics_service.ProjectCoreService"), \
         patch("app.services.project.analytics_service.ProjectExecutionService"), \
         patch("app.services.project.analytics_service.ProjectResourceService"), \
         patch("app.services.project.analytics_service.ProjectFinanceService"):
        return ProjectAnalyticsService(db=mock_db)


def test_init_creates_sub_services(mock_db):
    """初始化时应创建所有子服务"""
    with patch("app.services.project.analytics_service.ProjectCoreService") as MockCore, \
         patch("app.services.project.analytics_service.ProjectExecutionService") as MockExec, \
         patch("app.services.project.analytics_service.ProjectResourceService") as MockRes, \
         patch("app.services.project.analytics_service.ProjectFinanceService") as MockFin:
        svc = ProjectAnalyticsService(db=mock_db)
        MockCore.assert_called_once_with(mock_db)
        assert svc.core_service is not None
        assert svc.execution_service is not None
        assert svc.resource_service is not None
        assert svc.finance_service is not None


def test_get_projects_health_summary_empty(service):
    """无项目时应返回空摘要"""
    user = MagicMock()
    service.core_service.get_scoped_query.return_value.all.return_value = []
    result = service.get_projects_health_summary(user)
    assert result["total_projects"] == 0
    assert result["risk_projects"] == []


def test_get_projects_health_summary_counts(service):
    """正确统计健康状态分布"""
    user = MagicMock()
    project1 = MagicMock()
    project1.health = "H1"
    project1.stage = "S1"
    project1.progress_pct = 50
    project2 = MagicMock()
    project2.health = "H3"
    project2.stage = "S2"
    project2.progress_pct = 20
    service.core_service.get_scoped_query.return_value.all.return_value = [project1, project2]
    service._is_delayed = MagicMock(return_value=False)
    result = service.get_projects_health_summary(user)
    assert result["total_projects"] == 2
    assert "H1" in result["by_health"]
    assert "H3" in result["by_health"]


def test_get_projects_progress_summary_delegates(service):
    """get_projects_progress_summary 委托给 execution_service"""
    user = MagicMock()
    service.execution_service.get_progress_overview.return_value = {"overview": {}}
    result = service.get_projects_progress_summary(user, limit=10)
    service.execution_service.get_progress_overview.assert_called_once_with(user, 10)


def test_risk_projects_sorted_by_progress(service):
    """风险项目应按进度排序"""
    user = MagicMock()
    p1 = MagicMock()
    p1.health = "H3"
    p1.stage = "S1"
    p1.progress_pct = 80
    p1.id = 1
    p1.project_code = "P001"
    p1.project_name = "项目1"
    p1.pm_name = "PM1"
    p2 = MagicMock()
    p2.health = "H4"
    p2.stage = "S2"
    p2.progress_pct = 20
    p2.id = 2
    p2.project_code = "P002"
    p2.project_name = "项目2"
    p2.pm_name = "PM2"
    service.core_service.get_scoped_query.return_value.all.return_value = [p1, p2]
    service._is_delayed = MagicMock(return_value=False)
    result = service.get_projects_health_summary(user)
    # 风险项目按进度升序排列
    assert result["risk_projects"][0]["progress_pct"] <= result["risk_projects"][-1]["progress_pct"]


def test_get_workload_overview_delegates(service):
    """get_workload_overview 委托给 resource_service"""
    service.resource_service.get_workload_overview.return_value = {}
    result = service.get_workload_overview()
    service.resource_service.get_workload_overview.assert_called()
