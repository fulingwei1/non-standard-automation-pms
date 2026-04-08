# -*- coding: utf-8 -*-
"""strategy单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.strategy import StrategyDashboardAdapter

class TestStrategyDashboardAdapterInit:
    def test_init(self):
        service = StrategyDashboardAdapter(Mock())
        assert service is not None
