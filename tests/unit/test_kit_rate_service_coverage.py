# -*- coding: utf-8 -*-
"""kit_rate_service单元测试"""
import pytest
from unittest.mock import Mock
from services/kit_rate/kit_rate_service import KitRateService

class TestKitRateServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = KitRateService(mock_db)
        assert hasattr(service, 'db')
