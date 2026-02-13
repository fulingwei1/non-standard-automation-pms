# -*- coding: utf-8 -*-
"""Tests for performance_service/roles.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestGetUserManagerRoles:
    def test_no_employee_id(self):
        from app.services.performance_service.roles import get_user_manager_roles
        db = MagicMock()
        user = MagicMock(employee_id=None, id=1)
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_user_manager_roles(db, user)
        assert result['is_dept_manager'] is False
        assert result['is_project_manager'] is False

    def test_is_dept_manager(self):
        from app.services.performance_service.roles import get_user_manager_roles
        db = MagicMock()
        user = MagicMock(employee_id=10, id=1)
        dept = MagicMock(id=5)
        # First query for dept, second for projects
        db.query.return_value.filter.return_value.first.return_value = dept
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_user_manager_roles(db, user)
        assert result['is_dept_manager'] is True
        assert result['managed_dept_id'] == 5

    def test_is_project_manager(self):
        from app.services.performance_service.roles import get_user_manager_roles
        db = MagicMock()
        user = MagicMock(employee_id=10, id=1)
        db.query.return_value.filter.return_value.first.return_value = None
        project = MagicMock(id=100)
        db.query.return_value.filter.return_value.all.return_value = [project]
        result = get_user_manager_roles(db, user)
        assert result['is_project_manager'] is True


class TestGetManageableEmployees:
    def test_no_roles(self):
        from app.services.performance_service.roles import get_manageable_employees
        db = MagicMock()
        user = MagicMock(employee_id=None, id=1)
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_manageable_employees(db, user)
        assert isinstance(result, list)
