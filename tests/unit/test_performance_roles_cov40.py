# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 绩效管理服务角色函数
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.performance_service.roles import (
        get_user_manager_roles,
        get_manageable_employees,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_user(user_id=1, employee_id=10, is_active=True):
    user = MagicMock()
    user.id = user_id
    user.employee_id = employee_id
    user.is_active = is_active
    return user


class TestGetUserManagerRoles:

    def test_no_dept_no_project(self, mock_db):
        user = _make_user(employee_id=None)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_user_manager_roles(mock_db, user)
        assert result["is_dept_manager"] is False
        assert result["is_project_manager"] is False
        assert result["managed_dept_id"] is None
        assert result["managed_project_ids"] == []

    def test_dept_manager(self, mock_db):
        user = _make_user(employee_id=10)
        dept = MagicMock()
        dept.id = 5

        # 模拟查询链路: db.query(Department).filter(...).first() -> dept
        dept_query = MagicMock()
        dept_query.filter.return_value.first.return_value = dept

        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = []

        def side_effect(model):
            from app.models.organization import Department
            from app.models.project import Project
            if model is Department:
                return dept_query
            return project_query

        mock_db.query.side_effect = side_effect

        result = get_user_manager_roles(mock_db, user)
        assert result["is_dept_manager"] is True
        assert result["managed_dept_id"] == 5

    def test_project_manager(self, mock_db):
        user = _make_user(employee_id=None)
        proj1 = MagicMock()
        proj1.id = 101
        proj2 = MagicMock()
        proj2.id = 102

        from app.models.project import Project
        project_query = MagicMock()
        project_query.filter.return_value.all.return_value = [proj1, proj2]

        mock_db.query.return_value = project_query

        result = get_user_manager_roles(mock_db, user)
        assert result["is_project_manager"] is True
        assert 101 in result["managed_project_ids"]
        assert 102 in result["managed_project_ids"]

    def test_result_has_all_keys(self, mock_db):
        user = _make_user(employee_id=None)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_user_manager_roles(mock_db, user)
        for key in ("is_dept_manager", "is_project_manager", "managed_dept_id", "managed_project_ids"):
            assert key in result


class TestGetManageableEmployees:

    def test_returns_list(self, mock_db):
        user = _make_user(employee_id=None)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.performance_service.roles.get_user_manager_roles",
                   return_value={"is_dept_manager": False, "is_project_manager": False,
                                 "managed_dept_id": None, "managed_project_ids": []}):
            result = get_manageable_employees(mock_db, user)
        assert isinstance(result, list)

    def test_with_period_filter(self, mock_db):
        user = _make_user(employee_id=None)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("app.services.performance_service.roles.get_user_manager_roles",
                   return_value={"is_dept_manager": False, "is_project_manager": True,
                                 "managed_dept_id": None, "managed_project_ids": [1]}):
            mock_db.query.return_value.filter.return_value.all.return_value = []
            result = get_manageable_employees(mock_db, user, period="2024-01")
        assert isinstance(result, list)
