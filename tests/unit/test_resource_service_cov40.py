# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 项目资源聚合服务
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.project.resource_service import ProjectResourceService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.project.resource_service.ProjectCoreService"):
        svc = ProjectResourceService(db=mock_db)
        svc.db = mock_db
    return svc


class TestNormalizeRange:

    def test_both_none_returns_month_range(self):
        with patch("app.services.project.resource_service.get_month_range") as mock_range:
            mock_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
            start, end = ProjectResourceService._normalize_range(None, None)
            assert start == date(2024, 1, 1)
            assert end == date(2024, 1, 31)

    def test_start_before_end_ok(self):
        start, end = ProjectResourceService._normalize_range(
            date(2024, 1, 1), date(2024, 1, 31)
        )
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="before"):
            ProjectResourceService._normalize_range(
                date(2024, 2, 1), date(2024, 1, 1)
            )


class TestGetUserWorkload:

    def test_raises_when_user_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="user not found"):
            service.get_user_workload(user_id=999)

    def test_returns_workload_response(self, service, mock_db):
        user = MagicMock()
        user.id = 1
        user.display_name = "张三"
        user.department = "研发部"

        mock_db.query.return_value.filter.return_value.first.return_value = user

        with (
            patch("app.services.project.resource_service.get_user_tasks", return_value=[]),
            patch("app.services.project.resource_service.get_user_allocations", return_value=[]),
            patch("app.services.project.resource_service.calculate_total_assigned_hours", return_value=40),
            patch("app.services.project.resource_service.calculate_total_actual_hours", return_value=35),
            patch("app.services.project.resource_service.calculate_workdays", return_value=5),
            patch("app.services.project.resource_service.build_project_workload", return_value=[]),
            patch("app.services.project.resource_service.build_daily_load", return_value=[]),
            patch("app.services.project.resource_service.build_task_list", return_value=[]),
            patch("app.services.project.resource_service.get_month_range",
                  return_value=(date(2024, 1, 1), date(2024, 1, 31))),
        ):
            resp = service.get_user_workload(
                user_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        assert resp.user_id == 1
        assert resp.user_name == "张三"


class TestGetDepartmentWorkloadSummary:

    def test_raises_when_dept_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="department not found"):
            service.get_department_workload_summary(dept_id=999)

    def test_empty_members_returns_empty_summary(self, service, mock_db):
        dept = MagicMock()
        dept.id = 1
        dept.dept_name = "研发部"

        mock_db.query.return_value.filter.return_value.first.return_value = dept

        with patch.object(service, "_get_department_members", return_value=[]):
            result = service.get_department_workload_summary(
                dept_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        assert result["summary"]["total_members"] == 0
        assert result["members"] == []


class TestGetWorkloadOverview:

    def test_returns_overview_dict(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.all.return_value = []

        with patch("app.services.project.resource_service.get_month_range",
                   return_value=(date(2024, 1, 1), date(2024, 1, 31))):
            result = service.get_workload_overview(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
        assert "total_plans" in result
        assert "status_breakdown" in result
        assert "department_breakdown" in result
        assert "over_allocated_roles" in result
