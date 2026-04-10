# -*- coding: utf-8 -*-
"""smart_alert_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage.smart_alert_engine import SmartAlertEngine

class TestSmartAlertEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SmartAlertEngine(mock_db)
        assert hasattr(service, 'db')
