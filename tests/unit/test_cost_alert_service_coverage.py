# -*- coding: utf-8 -*-
"""cost_alert_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_alert_service import CostAlertService

class TestCostAlertServiceInit:
    def test_init(self):
        service = CostAlertService(Mock())
        assert service is not None
