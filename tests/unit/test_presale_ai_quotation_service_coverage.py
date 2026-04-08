# -*- coding: utf-8 -*-
"""presale_ai_quotation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService

class TestAIQuotationGeneratorServiceInit:
    def test_init(self):
        service = AIQuotationGeneratorService(Mock())
        assert service is not None
