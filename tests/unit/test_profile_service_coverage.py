# -*- coding: utf-8 -*-
"""profile_service单元测试"""
import pytest
from unittest.mock import Mock
from services/engineer_performance/profile_service import ProfileService

class TestProfileServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProfileService(mock_db)
        assert hasattr(service, 'db')
