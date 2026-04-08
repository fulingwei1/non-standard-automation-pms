# -*- coding: utf-8 -*-
"""presale_mobile_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_mobile_service import PresaleMobileService

class TestPresaleMobileServiceInit:
    def test_init(self):
        service = PresaleMobileService(Mock())
        assert service is not None
