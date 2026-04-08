# -*- coding: utf-8 -*-
"""ecn_integration_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ecn.integration.ecn_integration_service import EcnIntegrationService

class TestEcnIntegrationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = EcnIntegrationService(mock_db)
        assert hasattr(service, 'db')
