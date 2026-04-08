# -*- coding: utf-8 -*-
"""hourly_rate_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.hourly_rate_service import HourlyRateService

class TestHourlyRateServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = HourlyRateService(mock_db)
        assert hasattr(service, 'db')
