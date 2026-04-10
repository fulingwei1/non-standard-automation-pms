# -*- coding: utf-8 -*-
"""status_transition_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_transition_service import StatusTransitionService

class TestStatusTransitionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = StatusTransitionService(mock_db)
        assert hasattr(service, 'db')
