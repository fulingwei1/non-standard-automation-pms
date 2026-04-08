# -*- coding: utf-8 -*-
"""user_sync_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.user_sync_service import UserSyncService

class TestUserSyncServiceInit:
    def test_init(self):
        service = UserSyncService(Mock())
        assert service is not None
