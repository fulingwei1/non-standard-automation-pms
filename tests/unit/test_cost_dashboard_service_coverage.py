# -*- coding: utf-8 -*-
"""cost_dashboard_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_dashboard_service import CostDashboardService

class TestCostDashboardServiceInit:
    def test_init(self):
        service = CostDashboardService(Mock())
        assert service is not None
