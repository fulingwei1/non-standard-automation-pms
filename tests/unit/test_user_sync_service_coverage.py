# -*- coding: utf-8 -*-
"""user_sync_service单元测试"""
from app.services.user_sync_service import UserSyncService


class TestUserSyncServiceInit:
    def test_init(self):
        assert hasattr(UserSyncService, "get_role_by_position")
        assert hasattr(UserSyncService, "create_user_from_employee")
