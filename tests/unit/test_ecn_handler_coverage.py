# -*- coding: utf-8 -*-
"""ecn_handler单元测试"""
import pytest
from unittest.mock import Mock
from app.services.status_handlers.ecn_handler import ECNStatusHandler

class TestECNStatusHandlerInit:
    def test_init(self):
        service = ECNStatusHandler(Mock())
        assert service is not None
