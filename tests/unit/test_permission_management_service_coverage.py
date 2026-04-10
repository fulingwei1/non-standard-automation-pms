# -*- coding: utf-8 -*-
"""permission_management_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.permission_management.permission_management_service import PermissionManagementService

class TestPermissionManagementServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PermissionManagementService(mock_db)
        assert hasattr(service, 'db')
