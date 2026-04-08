# -*- coding: utf-8 -*-
"""permission_service单元测试"""
import pytest
from unittest.mock import Mock
from services/permission_management/permission_service import PermissionService

class TestPermissionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PermissionService(mock_db)
        assert hasattr(service, 'db')
