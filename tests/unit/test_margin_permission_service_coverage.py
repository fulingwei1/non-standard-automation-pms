# -*- coding: utf-8 -*-
"""margin_permission_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.margin_permission_service import MarginPermissionService

class TestMarginPermissionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MarginPermissionService(mock_db)
        assert hasattr(service, 'db')
