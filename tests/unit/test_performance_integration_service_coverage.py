# -*- coding: utf-8 -*-
"""performance_integration_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_integration_service import PerformanceIntegrationService

class TestPerformanceIntegrationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceIntegrationService(mock_db)
        assert hasattr(service, 'db')
