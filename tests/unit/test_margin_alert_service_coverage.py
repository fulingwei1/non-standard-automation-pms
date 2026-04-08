# -*- coding: utf-8 -*-
"""margin_alert_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/margin_alert_service import MarginAlertService

class TestMarginAlertServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MarginAlertService(mock_db)
        assert hasattr(service, 'db')
