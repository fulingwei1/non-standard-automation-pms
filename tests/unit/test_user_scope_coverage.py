# -*- coding: utf-8 -*-
"""user_scope单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_scope.user_scope import UserScopeService

class TestUserScopeServiceInit:
    def test_init(self):
        service = UserScopeService(Mock())
        assert service is not None
