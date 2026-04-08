# -*- coding: utf-8 -*-
"""two_factor_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.two_factor_service import TwoFactorService

class TestTwoFactorServiceInit:
    def test_init(self):
        service = TwoFactorService(Mock())
        assert service is not None
