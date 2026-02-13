# -*- coding: utf-8 -*-
"""用户权限范围服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.data_scope.user_scope import UserScopeService


class TestUserScopeService:
    def setup_method(self):
        self.db = MagicMock()

    def test_superuser_gets_all_scope(self):
        user = MagicMock()
        user.is_superuser = True
        result = UserScopeService.get_user_data_scope(self.db, user)
        assert result == "ALL"

    def test_user_with_all_role(self):
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.is_active = True
        role.data_scope = "ALL"
        user_role = MagicMock()
        user_role.role = role
        user.roles = [user_role]
        result = UserScopeService.get_user_data_scope(self.db, user)
        assert result == "ALL"

    def test_user_with_dept_role(self):
        user = MagicMock()
        user.is_superuser = False
        role = MagicMock()
        role.is_active = True
        role.data_scope = "DEPT"
        user_role = MagicMock()
        user_role.role = role
        user.roles = [user_role]
        result = UserScopeService.get_user_data_scope(self.db, user)
        assert result == "DEPT"

    def test_user_with_no_roles(self):
        user = MagicMock()
        user.is_superuser = False
        user.roles = []
        result = UserScopeService.get_user_data_scope(self.db, user)
        assert result == "OWN"

    def test_get_user_project_ids(self):
        self.db.query.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,)]
        result = UserScopeService.get_user_project_ids(self.db, 1)
        assert result == {1, 2, 3}

    def test_get_subordinate_ids(self):
        self.db.query.return_value.filter.return_value.all.return_value = [(10,), (20,)]
        result = UserScopeService.get_subordinate_ids(self.db, 1)
        assert result == {10, 20}
