# -*- coding: utf-8 -*-
"""outbound_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.inventory.outbound_service import OutboundService

class TestOutboundServiceInit:
    def test_init(self):
        service = OutboundService(Mock())
        assert service is not None
