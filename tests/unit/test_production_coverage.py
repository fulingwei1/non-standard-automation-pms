# -*- coding: utf-8 -*-
"""production单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.production import ProductionDashboardAdapter

class TestProductionDashboardAdapterInit:
    def test_init(self):
        service = ProductionDashboardAdapter(Mock())
        assert service is not None
