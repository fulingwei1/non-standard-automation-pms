# -*- coding: utf-8 -*-
"""funnel_state_machine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.funnel_state_machine import FunnelStateMachine

class TestFunnelStateMachineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = FunnelStateMachine(mock_db)
        assert hasattr(service, 'db')
