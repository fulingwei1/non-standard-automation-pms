# -*- coding: utf-8 -*-
"""progress_integration_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.progress_integration_service import ProgressIntegrationService

class TestProgressIntegrationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProgressIntegrationService(mock_db)
        assert hasattr(service, 'db')
