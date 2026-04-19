# -*- coding: utf-8 -*-
"""user_scope单元测试"""
from app.services.data_scope.user_scope import UserScopeService


class TestUserScopeServiceInit:
    def test_init(self):
        assert hasattr(UserScopeService, "get_user_data_scope")
        assert hasattr(UserScopeService, "get_user_project_ids")
