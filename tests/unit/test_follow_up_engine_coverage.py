# -*- coding: utf-8 -*-
"""follow_up_engine单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/engines/follow_up_engine import FollowUpEngine

class TestFollowUpEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = FollowUpEngine(mock_db)
        assert hasattr(service, 'db')
