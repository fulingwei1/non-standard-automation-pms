# -*- coding: utf-8 -*-
"""cost_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_service import CostService

class TestCostServiceInit:
    def test_init(self):
        service = CostService(Mock())
        assert service is not None
