# -*- coding: utf-8 -*-
"""cpq_pricing_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.cpq_pricing_service import CpqPricingService

class TestCpqPricingServiceInit:
    def test_init(self):
        service = CpqPricingService(Mock())
        assert service is not None
