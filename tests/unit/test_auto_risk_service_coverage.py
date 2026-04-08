# -*- coding: utf-8 -*-
"""auto_risk_service单元测试"""
import pytest
from unittest.mock import Mock
from services/project_risk/auto_risk_service import AutoRiskService

class TestAutoRiskServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AutoRiskService(mock_db)
        assert hasattr(service, 'db')
