# -*- coding: utf-8 -*-
"""risk_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.engines.risk_engine import RiskEngine

class TestRiskEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RiskEngine(mock_db)
        assert hasattr(service, 'db')
