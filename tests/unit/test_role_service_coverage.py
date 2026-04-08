# -*- coding: utf-8 -*-
"""role_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.role_service import RoleService

class TestRoleServiceInit:
    def test_init(self):
        service = RoleService(Mock())
        assert service is not None
