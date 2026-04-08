# -*- coding: utf-8 -*-
"""pm_involvement_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pm_involvement_service import PMInvolvementService

class TestPMInvolvementServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PMInvolvementService(mock_db)
        assert hasattr(service, 'db')
