# -*- coding: utf-8 -*-
"""presale_ai_integration单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_integration import PresaleAIIntegrationService

class TestPresaleAIIntegrationServiceInit:
    def test_init(self):
        service = PresaleAIIntegrationService(Mock())
        assert service is not None
