# -*- coding: utf-8 -*-
"""status_update_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_update_service import StatusUpdateResult

class TestStatusUpdateResultInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = StatusUpdateResult(mock_db)
        assert hasattr(service, 'db')
