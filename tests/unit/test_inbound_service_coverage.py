# -*- coding: utf-8 -*-
"""inbound_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.inbound_service import InboundService

class TestInboundServiceInit:
    def test_init(self):
        service = InboundService(Mock())
        assert service is not None
