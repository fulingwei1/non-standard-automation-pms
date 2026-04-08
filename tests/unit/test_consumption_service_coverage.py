# -*- coding: utf-8 -*-
"""consumption_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.material_tracking.consumption_service import ConsumptionService

class TestConsumptionServiceInit:
    def test_init(self):
        service = ConsumptionService(Mock())
        assert service is not None
