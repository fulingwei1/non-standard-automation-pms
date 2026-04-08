# -*- coding: utf-8 -*-
"""technical_parameter_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.technical_parameter_service import TechnicalParameterService

class TestTechnicalParameterServiceInit:
    def test_init(self):
        service = TechnicalParameterService(Mock())
        assert service is not None
