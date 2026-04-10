# -*- coding: utf-8 -*-
"""shortage_management_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage.shortage_management_service import ShortageManagementService

class TestShortageManagementServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ShortageManagementService(mock_db)
        assert hasattr(service, 'db')
