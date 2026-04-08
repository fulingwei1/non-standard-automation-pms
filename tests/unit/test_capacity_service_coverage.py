# -*- coding: utf-8 -*-
"""capacity_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.capacity.capacity_service import CapacityAnalysisService

class TestCapacityAnalysisServiceInit:
    def test_init(self):
        service = CapacityAnalysisService(Mock())
        assert service is not None
