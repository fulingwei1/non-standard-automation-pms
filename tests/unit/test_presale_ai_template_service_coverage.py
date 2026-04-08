# -*- coding: utf-8 -*-
"""presale_ai_template_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_template_service import PresaleAITemplateService

class TestPresaleAITemplateServiceInit:
    def test_init(self):
        service = PresaleAITemplateService(Mock())
        assert service is not None
