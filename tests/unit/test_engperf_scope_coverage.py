# -*- coding: utf-8 -*-
"""engperf_scope单元测试"""
import pytest
from unittest.mock import Mock
from services/engineer_performance/engperf_scope import EngPerfScopeContext

class TestEngPerfScopeContextInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = EngPerfScopeContext(mock_db)
        assert hasattr(service, 'db')
